"""D1 backup export (scst.backup.v1): consistent SQLite copy plus vessel profile versions in one ZIP archive.

Stdlib only. Never creates or modifies anything under SCST_DATA_DIR: the source database is opened read-only,
and every temporary file lives in a private temp directory that is removed before returning.
"""
import contextlib
import hashlib
import io
import json
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import storage
from . import vessel_profile_store as store

FORMAT = 'scst.backup.v1'
EXTENSION = '.scstbak'
DB_NAME = 'scst.sqlite3'
MANIFEST_NAME = 'manifest.json'
VESSEL_FILES = ('profile.json', 'model.glb', 'manifest.json')
_CHUNK = 1024 * 1024
_UNSUPPORTED_DB = 'Cấu trúc cơ sở dữ liệu không được hỗ trợ.'
_UNSUPPORTED_REVISIONS = 'Cấu trúc bảng revision dữ liệu hàng không được hỗ trợ.'
_INCOMPLETE_VESSEL = 'Hồ sơ tàu thiếu tệp, không thể xuất sao lưu.'


def _data_dir() -> Path:
    return Path(os.environ.get('SCST_DATA_DIR', str(storage.ROOT / 'runtime-data')))


def _snapshot_database(target: Path) -> None:
    """Write a consistent copy of the live database to target; the source is only ever opened read-only."""
    source = _data_dir() / DB_NAME
    if not source.exists():
        with contextlib.closing(sqlite3.connect(target)) as db:
            db.execute(storage.SNAPSHOTS_DDL)
            db.execute(storage.REVISIONS_DDL)
            db.commit()
        return
    src = sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
    try:
        columns = [row[1] for row in src.execute('PRAGMA table_info(snapshots)')]
        if columns != storage.SNAPSHOT_COLUMNS:
            raise ValueError(_UNSUPPORTED_DB)
        revisions = [(row[1], (row[2] or '').upper()) for row in src.execute('PRAGMA table_info(cargo_revisions)')]
        if revisions and revisions != storage.REVISIONS_COLUMNS:
            raise ValueError(_UNSUPPORTED_REVISIONS)
        # Single-step backup: the whole copy is taken under one read transaction, so it is one consistent state.
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    if not revisions:
        # Only the temporary copy gets the missing table; the source database is never altered.
        with contextlib.closing(sqlite3.connect(target)) as db:
            db.execute(storage.REVISIONS_DDL)
            db.commit()


def _count(db_path: Path, table: str) -> int:
    with contextlib.closing(sqlite3.connect(db_path)) as db:
        return db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]


def _vessel_entries() -> tuple[list[tuple[str, Path]], int]:
    """Only versions listed by the store, and only their three files. Must be called under the vessel lock."""
    base = store.data_dir()
    entries = []
    version_count = 0
    if not base.is_dir():
        return entries, version_count
    for folder in sorted(base.iterdir()):
        if not folder.is_dir() or not store.ID_PATTERN.fullmatch(folder.name):
            continue
        for version in store.versions(folder.name):
            directory = folder / f'v{version}'
            for name in VESSEL_FILES:
                path = directory / name
                if not path.is_file():
                    raise ValueError(_INCOMPLETE_VESSEL)
                entries.append((f'vessels/{folder.name}/v{version}/{name}', path))
            version_count += 1
    return entries, version_count


def _add_file(zf: zipfile.ZipFile, path: Path, arcname: str) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as source, zf.open(arcname, 'w', force_zip64=True) as target:
        for chunk in iter(lambda: source.read(_CHUNK), b''):
            digest.update(chunk)
            size += len(chunk)
            target.write(chunk)
    return {'path': arcname, 'size': size, 'sha256': digest.hexdigest()}


def _export_vessels(fileobj, db_path: Path, db_counts: dict) -> dict:
    entries, version_count = _vessel_entries()
    counts = {**db_counts, 'vessel_profile_versions': version_count}
    with zipfile.ZipFile(fileobj, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        files = [_add_file(zf, db_path, DB_NAME)]
        files += [_add_file(zf, path, arcname) for arcname, path in entries]
        files.sort(key=lambda item: item['path'])
        manifest = {'format': FORMAT, 'created_utc': datetime.now(timezone.utc).isoformat(),
                    'counts': counts, 'files': files}
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode('utf-8'))
    return manifest


def write_archive(fileobj, *, lock_held: bool = False) -> dict:
    """Write the scst.backup.v1 archive to fileobj and return its manifest.

    lock_held=True means the caller already holds vessel_profile_store._LOCK and the process lock; nothing is taken here.
    """
    with tempfile.TemporaryDirectory(prefix='scst-export-') as work:
        db_path = Path(work) / DB_NAME
        _snapshot_database(db_path)
        db_counts = {'plans': _count(db_path, 'snapshots'), 'revisions': _count(db_path, 'cargo_revisions')}
        if lock_held:
            return _export_vessels(fileobj, db_path, db_counts)
        with store._LOCK:
            if store.data_dir().is_dir():
                with store._process_lock(store.data_dir()):
                    return _export_vessels(fileobj, db_path, db_counts)
            return _export_vessels(fileobj, db_path, db_counts)


def export_bytes() -> tuple[bytes, str]:
    """Return (archive bytes, filename scst-backup-YYYYMMDD-HHMMSS.scstbak in UTC)."""
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    buffer = io.BytesIO()
    write_archive(buffer)
    return buffer.getvalue(), f'scst-backup-{stamp}{EXTENSION}'
