"""Verification of a scst.backup.v1 archive before it may be restored (M5a D2). Nothing here touches live data.

check() extracts the allow-listed entries of an untrusted ZIP into a caller-provided empty directory (streamed, real
bytes counted, headers never trusted) and validates manifest, hashes, SQLite and every stored record. Messages are
Vietnamese and never contain an absolute path. current_counts() and preview() are strictly read-only.
"""
import hashlib
import io
import json
import os
import re
import sqlite3
import stat
import tempfile
import zipfile
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from ..domain import cargo_revisions as cr
from ..domain.model import Plan
from ..domain.vessel_profiles import profile_sha256, validate_profile
from . import revision_store, storage
from . import vessel_profile_store as vstore
from .pipe_registry import REGISTRY

FORMAT = 'scst.backup.v1'
MAX_BODY_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 20000
MAX_UNCOMPRESSED = 1024 ** 3
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MANIFEST = 'manifest.json'
DATABASE = 'scst.sqlite3'
_CHUNK = 64 * 1024
_SHA = re.compile(r'^[0-9a-f]{64}$')
_VESSEL_FILE = re.compile(r'^vessels/([^/]+)/([^/]+)/(profile\.json|model\.glb|manifest\.json)$')
_COUNT_KEYS = ('plans', 'revisions', 'vessel_profile_versions')
_REVISIONS_SELECT = ('SELECT revision_id,dataset_id,sequence,parent_revision_id,created_utc,source_json,changes_json,'
                     'content_sha256 FROM cargo_revisions ORDER BY sequence')


class BackupRejected(ValueError):
    """The archive may not be restored. `message` is Vietnamese; `errors` is [{"field","message"}]."""

    def __init__(self, message: str, field: str = 'body', errors: list | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors if errors is not None else [{'field': field, 'message': message}]


def _short(name) -> str:
    text = repr(name)
    return text if len(text) <= 80 else text[:77] + '...'


def _megabytes(n: int) -> str:
    return f'{n / (1024 * 1024):.0f} MiB'


# ------------------------------------------------------------------ D2.1 names and ZIP
def _name_problem(name: str) -> str | None:
    """None if `name` is on the allow-list, else a Vietnamese reason."""
    if not name or '\x00' in name:
        return 'tên mục rỗng hoặc chứa ký tự không hợp lệ'
    if '\\' in name:
        return 'đường dẫn chứa dấu gạch ngược'
    if name.startswith('/'):
        return 'đường dẫn tuyệt đối'
    if re.match(r'^[A-Za-z]:', name):
        return 'đường dẫn chứa ký tự ổ đĩa'
    if '..' in name.split('/'):
        return 'đường dẫn chứa ".."'
    if name.endswith('/'):
        return 'mục là thư mục (tệp sao lưu không chứa mục thư mục)'
    if name in (MANIFEST, DATABASE):
        return None
    m = _VESSEL_FILE.fullmatch(name)
    if m and vstore.ID_PATTERN.fullmatch(m.group(1)) and vstore.VERSION_DIR.fullmatch(m.group(2)):
        return None
    return 'tệp không nằm trong danh sách được phép'


def _entry_problem(info: zipfile.ZipInfo) -> str | None:
    problem = _name_problem(info.filename)
    if problem:
        return problem
    mode = info.external_attr >> 16
    if mode and stat.S_IFMT(mode) == stat.S_IFLNK:
        return 'mục là liên kết tượng trưng (symlink)'
    if mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG):
        return 'mục không phải tệp thường'
    if info.flag_bits & 0x1:
        return 'mục bị mã hóa'
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        return 'phương thức nén không được hỗ trợ'
    if info.file_size < 0 or info.compress_size < 0:
        return 'kích thước mục không hợp lệ'
    return None


def _open_zip(body: bytes) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(io.BytesIO(body))
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, EOFError, ValueError, NotImplementedError, RuntimeError):
        raise BackupRejected('Tệp không phải bản sao lưu hợp lệ: không đọc được như tệp ZIP.') from None


def _validate_entries(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    infos = zf.infolist()
    if len(infos) > MAX_ENTRIES:
        raise BackupRejected(f'Tệp sao lưu có quá nhiều mục ({len(infos)}); tối đa {MAX_ENTRIES}.')
    seen = set()
    declared = 0
    for info in infos:
        problem = _entry_problem(info)
        if problem:
            raise BackupRejected(f'Tệp sao lưu bị từ chối: mục {_short(info.filename)} không được phép ({problem}).')
        key = info.filename.casefold()
        if key in seen:
            raise BackupRejected(f'Tệp sao lưu bị từ chối: tên mục {_short(info.filename)} bị trùng.')
        seen.add(key)
        declared += info.file_size
        if declared > MAX_UNCOMPRESSED:
            raise BackupRejected(f'Tệp sao lưu bị từ chối: tổng kích thước giải nén khai báo vượt giới hạn {_megabytes(MAX_UNCOMPRESSED)}.')
    return infos


def _extract(zf: zipfile.ZipFile, infos: list[zipfile.ZipInfo], workdir: Path) -> dict:
    """Write every entry under workdir, counting the bytes really produced. -> {name: (size, sha256)}."""
    measured = {}
    total = 0
    for info in infos:
        target = workdir / info.filename
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        try:
            with zf.open(info) as source, open(target, 'xb') as out:
                while True:
                    chunk = source.read(_CHUNK)
                    if not chunk:
                        break
                    size += len(chunk)
                    total += len(chunk)
                    if size > info.file_size or total > MAX_UNCOMPRESSED:
                        raise BackupRejected(
                            f'Tệp sao lưu bị từ chối: dữ liệu giải nén thực tế vượt kích thước khai báo hoặc giới hạn {_megabytes(MAX_UNCOMPRESSED)}.')
                    digest.update(chunk)
                    out.write(chunk)
        except BackupRejected:
            raise
        except (zipfile.BadZipFile, zlib.error, EOFError, OSError, NotImplementedError, RuntimeError, ValueError):
            raise BackupRejected(f'Tệp sao lưu bị hỏng: không giải nén được mục {_short(info.filename)}.') from None
        measured[info.filename] = (size, digest.hexdigest())
    return measured


# ------------------------------------------------------------------ D2.2 manifest
def _aware_utc(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError:
        return False
    return stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0)


def _read_manifest(workdir: Path, measured: dict) -> dict:
    if MANIFEST not in measured:
        raise BackupRejected('Tệp sao lưu thiếu manifest.json.')
    path = workdir / MANIFEST
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        raise BackupRejected('manifest.json quá lớn.')
    try:
        manifest = json.loads(path.read_bytes().decode('utf-8'))
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise BackupRejected('manifest.json không phải JSON hợp lệ.', 'manifest.json') from None
    if not isinstance(manifest, dict):
        raise BackupRejected('manifest.json phải là một đối tượng JSON.', 'manifest.json')
    if manifest.get('format') != FORMAT:
        raise BackupRejected(f'Định dạng sao lưu không được hỗ trợ; cần "{FORMAT}".', 'manifest.format')
    if not _aware_utc(manifest.get('created_utc')):
        raise BackupRejected('manifest.json có created_utc không hợp lệ (cần thời điểm UTC có múi giờ).', 'manifest.created_utc')
    files = manifest.get('files')
    if not isinstance(files, list):
        raise BackupRejected('manifest.json thiếu danh sách tệp "files".', 'manifest.files')
    listed = {}
    for item in files:
        if (not isinstance(item, dict) or not isinstance(item.get('path'), str) or type(item.get('size')) is not int
                or not isinstance(item.get('sha256'), str) or not _SHA.fullmatch(item['sha256'])):
            raise BackupRejected('manifest.json có mục "files" sai cấu trúc (cần path, size, sha256).', 'manifest.files')
        if item['path'] in listed:
            raise BackupRejected(f'manifest.json liệt kê tệp {_short(item["path"])} nhiều lần.', 'manifest.files')
        listed[item['path']] = item
    actual = set(measured) - {MANIFEST}
    if set(listed) != actual:
        raise BackupRejected('Danh sách tệp trong manifest.json không khớp các tệp thực tế trong bản sao lưu.', 'manifest.files')
    for name, item in listed.items():
        size, digest = measured[name]
        if item['size'] != size:
            raise BackupRejected(f'Kích thước tệp {_short(name)} không khớp manifest.json.', 'manifest.files')
        if item['sha256'] != digest:
            raise BackupRejected(f'sha256 của tệp {_short(name)} không khớp manifest.json.', 'manifest.files')
    counts = manifest.get('counts')
    if (not isinstance(counts, dict) or set(counts) != set(_COUNT_KEYS)
            or any(type(counts[k]) is not int or counts[k] < 0 for k in _COUNT_KEYS)):
        raise BackupRejected('manifest.json có "counts" sai cấu trúc.', 'manifest.counts')
    return manifest


# ------------------------------------------------------------------ D2.3 / D2.4 SQLite
def _ro_uri(path: Path) -> str:
    return path.absolute().as_uri() + '?mode=ro'


def _check_database(path: Path) -> tuple[int, int]:
    """Validate scst.sqlite3 read-only -> (plans, revisions). Every connection is closed before returning."""
    try:
        db = sqlite3.connect(_ro_uri(path), uri=True, timeout=5)
    except sqlite3.Error:
        raise BackupRejected('Cơ sở dữ liệu trong bản sao lưu không mở được.', DATABASE) from None
    try:
        try:
            result = [row[0] for row in db.execute('PRAGMA integrity_check')]
            if result != ['ok']:
                raise BackupRejected('Cơ sở dữ liệu trong bản sao lưu không qua kiểm tra toàn vẹn (integrity_check).', DATABASE)
            objects = db.execute('SELECT type,name FROM sqlite_master').fetchall()
            for kind, name in objects:
                if kind == 'table' and name in ('snapshots', 'cargo_revisions'):
                    continue
                if kind == 'index' and name.startswith('sqlite_autoindex_'):
                    continue
                raise BackupRejected(f'Cơ sở dữ liệu trong bản sao lưu chứa đối tượng không được phép: {_short(name)}.', DATABASE)
            columns = [row[1] for row in db.execute('PRAGMA table_info(snapshots)')]
            if columns != storage.SNAPSHOT_COLUMNS:
                raise BackupRejected('Cấu trúc bảng phương án (snapshots) trong bản sao lưu không được hỗ trợ.', DATABASE)
            info = [(row[1], (row[2] or '').upper()) for row in db.execute('PRAGMA table_info(cargo_revisions)')]
            if info != storage.REVISIONS_COLUMNS:
                raise BackupRejected('Cấu trúc bảng revision (cargo_revisions) trong bản sao lưu không được hỗ trợ.', DATABASE)
            plans = _check_plans(db.execute('SELECT id,name,created_utc,schema_version,plan_json FROM snapshots ORDER BY id').fetchall())
            revisions = _check_revisions(db.execute(_REVISIONS_SELECT).fetchall())
            return plans, revisions
        except sqlite3.Error:
            raise BackupRejected('Cơ sở dữ liệu trong bản sao lưu bị hỏng hoặc không đọc được.', DATABASE) from None
    finally:
        db.close()


def _check_plans(rows) -> int:
    for plan_id, name, created, schema, plan_json in rows:
        label = f'Phương án {_short(plan_id)}'
        if not all(isinstance(v, str) for v in (plan_id, name, created, schema, plan_json)) or not name.strip():
            raise BackupRejected(f'{label} có dữ liệu cột sai kiểu.', 'snapshots')
        try:
            if str(UUID(plan_id)) != plan_id:
                raise ValueError()
        except ValueError:
            raise BackupRejected(f'{label} có ID không hợp lệ.', 'snapshots') from None
        if schema != 'scst.saved-plan.v1':
            raise BackupRejected(f'{label} có phiên bản lưu không được hỗ trợ.', 'snapshots')
        if not _aware_utc(created):
            raise BackupRejected(f'{label} có thời gian lưu không hợp lệ (cần UTC có múi giờ).', 'snapshots')
        try:
            Plan.model_validate(json.loads(plan_json))
        except Exception:  # pydantic ValidationError, bad JSON, recursion: all mean the stored plan is unusable
            raise BackupRejected(f'{label} không qua kiểm tra cấu trúc phương án.', 'snapshots') from None
    return len(rows)


def _check_revisions(rows) -> int:
    if len(rows) > 9999:
        raise BackupRejected('Số revision dữ liệu hàng vượt giới hạn 9999.', 'cargo_revisions')
    for position, row in enumerate(rows, 1):
        if row[1] != cr.DATASET:
            raise BackupRejected(f'Revision {_short(row[0])} thuộc bộ dữ liệu {_short(row[1])}, không phải {cr.DATASET}.', 'cargo_revisions')
        if type(row[2]) is not int or row[2] != position:
            raise BackupRejected(f'Revision {_short(row[0])} có số thứ tự không liên tục.', 'cargo_revisions')
    try:
        records = revision_store.decode_rows(rows)
    except Exception:
        raise BackupRejected('Một revision dữ liệu hàng có source/changes không phải JSON hợp lệ.', 'cargo_revisions') from None
    try:
        cr.replay(REGISTRY, records)
    except cr.RevisionIntegrityError as exc:
        raise BackupRejected(f'Chuỗi revision dữ liệu hàng không qua kiểm phát lại: {exc.message}', 'cargo_revisions') from None
    except Exception:
        raise BackupRejected('Chuỗi revision dữ liệu hàng không qua kiểm phát lại.', 'cargo_revisions') from None
    return len(rows)


# ------------------------------------------------------------------ D2.5 vessel profiles
def _check_vessels(names, workdir: Path) -> int:
    """Existing read check of the store (manifest, profile/glb sha256) on the extracted tree, then the profile
    validation of vessel_profile_service._load, re-stated here because _load is bound to the live data directory."""
    found: dict[str, set[int]] = {}
    for name in names:
        m = _VESSEL_FILE.fullmatch(name)
        if m:
            found.setdefault(m.group(1), set()).add(int(vstore.VERSION_DIR.fullmatch(m.group(2)).group(1)))
    if len(found) > vstore.MAX_IDS or any(len(v) > vstore.MAX_VERSIONS for v in found.values()):
        raise BackupRejected('Số hồ sơ tàu hoặc số phiên bản trong bản sao lưu vượt giới hạn của kho hồ sơ.', 'vessels')
    base = workdir / 'vessels'
    for profile_id in sorted(found):
        for version in sorted(found[profile_id]):
            label = f'Hồ sơ tàu {profile_id} phiên bản {version}'
            try:
                stored = vstore.read(profile_id, version, base=base)
            except (vstore.StoreError, LookupError) as exc:
                raise BackupRejected(f'{label} không qua kiểm tra: {exc}', 'vessels') from None
            try:
                model, errors = validate_profile(json.loads(stored['profile_bytes'].decode('utf-8')))
            except (UnicodeDecodeError, ValueError, RecursionError):
                raise BackupRejected(f'{label}: profile.json không phải JSON hợp lệ.', 'vessels') from None
            if (errors or model is None or model.id != profile_id or model.version != version
                    or profile_sha256(model) != stored['manifest']['profile_sha256']):
                raise BackupRejected(f'{label}: profile.json không còn hợp lệ hoặc không khớp mã, phiên bản, sha256.', 'vessels')
    return sum(len(v) for v in found.values())


# ------------------------------------------------------------------ public API
def check(body: bytes, workdir: Path) -> dict:
    """Extract into `workdir` (empty, caller-owned) and validate D2.1-D2.5. Raises BackupRejected."""
    if len(body) > MAX_BODY_BYTES:
        raise BackupRejected(f'Tệp sao lưu dài {_megabytes(len(body))}, vượt giới hạn {_megabytes(MAX_BODY_BYTES)}.')
    workdir = Path(workdir)
    with _open_zip(body) as zf:
        infos = _validate_entries(zf)
        measured = _extract(zf, infos, workdir)
    manifest = _read_manifest(workdir, measured)
    if DATABASE not in measured:
        raise BackupRejected('Bản sao lưu thiếu cơ sở dữ liệu scst.sqlite3.', DATABASE)
    plans, revisions = _check_database(workdir / DATABASE)
    vessels = _check_vessels(measured, workdir)
    actual = {'plans': plans, 'revisions': revisions, 'vessel_profile_versions': vessels}
    if manifest['counts'] != actual:
        raise BackupRejected('Số lượng ghi trong manifest.json không khớp dữ liệu thực tế trong bản sao lưu.', 'manifest.counts')
    return {'format': FORMAT, 'created_utc': manifest['created_utc'], 'backup_sha256': hashlib.sha256(body).hexdigest(),
            'counts': actual}


def _count(db: sqlite3.Connection, table: str) -> int:
    try:
        return int(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0])
    except sqlite3.Error:
        return 0


def current_counts() -> dict:
    """Counts of the live data. Strictly read-only: never creates the database or the vessels directory."""
    plans = revisions = 0
    path = Path(os.environ.get('SCST_DATA_DIR', str(storage.ROOT / 'runtime-data'))) / DATABASE
    if path.is_file():
        try:
            db = sqlite3.connect(_ro_uri(path), uri=True, timeout=5)
        except sqlite3.Error:
            db = None
        if db is not None:
            try:
                plans, revisions = _count(db, 'snapshots'), _count(db, 'cargo_revisions')
            finally:
                db.close()
    vessels = sum(len(vstore.versions(profile_id)) for profile_id in vstore.list_ids())
    return {'plans': plans, 'revisions': revisions, 'vessel_profile_versions': vessels}


def preview(body: bytes) -> dict:
    """check() in a temporary directory outside the data directory, plus the live counts. Writes nothing to live data."""
    with tempfile.TemporaryDirectory(prefix='scst-preview-', ignore_cleanup_errors=True) as tmp:
        result = check(body, Path(tmp))
    return {**result, 'current': current_counts()}
