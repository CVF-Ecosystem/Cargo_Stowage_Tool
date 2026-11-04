"""Append-only file store of user vessel profiles (bytes in, bytes out). Deliberately has no update or delete function.

Layout: <SCST_DATA_DIR>/vessels/<id>/v<version>/{profile.json, model.glb, manifest.json}.
A version appears with one os.rename of a fully written temp directory ('.tmp-*', ignored by readers) and is never replaced.
"""
import hashlib
import json
import os
import re
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows: the rename-not-overwrite rule alone keeps a race safe
    fcntl = None

ROOT = Path(__file__).resolve().parents[4]
MAX_IDS = 50
MAX_VERSIONS = 50
ID_PATTERN = re.compile(r'^[A-Z0-9][A-Z0-9-]{1,31}$')
VERSION_DIR = re.compile(r'^v([1-9][0-9]{0,8})$')
MANIFEST_SCHEMA = 'scst.vessel-profile-manifest.v1'
MANIFEST_KEYS = {'schema', 'id', 'version', 'created_utc', 'profile_sha256', 'glb_sha256', 'glb_bytes', 'verification'}
_LOCK = threading.Lock()


class StoreError(ValueError):
    """Base class of store errors; messages are Vietnamese."""


class VersionConflict(StoreError):
    def __init__(self, latest: int):
        super().__init__(f'Phiên bản không hợp lệ: phiên bản mới nhất hiện là {latest}, phiên bản kế tiếp phải là {latest + 1}.')
        self.latest = latest


class StoreLimit(StoreError):
    pass


class ProfileUnavailable(StoreError):
    def __init__(self, profile_id: str, version: int, reason: str):
        super().__init__(f'Hồ sơ tàu {profile_id} phiên bản {version} không phục vụ được: {reason}')
        self.profile_id = profile_id
        self.version = version


def data_dir() -> Path:
    return Path(os.environ.get('SCST_DATA_DIR', str(ROOT / 'runtime-data'))) / 'vessels'


def _check(profile_id, version):
    if not isinstance(profile_id, str) or not ID_PATTERN.fullmatch(profile_id):
        raise StoreError('Mã hồ sơ tàu không hợp lệ.')
    if type(version) is not int or version < 1:
        raise StoreError('Phiên bản hồ sơ tàu phải là số nguyên từ 1 trở lên.')


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def versions(profile_id: str) -> list[int]:
    if not isinstance(profile_id, str) or not ID_PATTERN.fullmatch(profile_id):
        return []
    try:
        entries = list((data_dir() / profile_id).iterdir())
    except OSError:
        return []
    found = [int(m.group(1)) for e in entries if (m := VERSION_DIR.fullmatch(e.name)) and (e / 'manifest.json').is_file()]
    return sorted(found)


def latest_version(profile_id: str) -> int:
    found = versions(profile_id)
    return found[-1] if found else 0


def list_ids() -> list[str]:
    try:
        names = [e.name for e in data_dir().iterdir() if e.is_dir() and ID_PATTERN.fullmatch(e.name)]
    except OSError:
        return []
    return sorted(n for n in names if versions(n))


def _fsync_dir(path: Path):
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _write(path: Path, data: bytes):
    with open(path, 'xb') as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def append(profile_id: str, version: int, profile_bytes: bytes, glb_bytes: bytes, verification: dict) -> dict:
    """Add exactly version latest+1 of a profile; returns the manifest. Nothing is written on any error."""
    _check(profile_id, version)
    if not isinstance(profile_bytes, bytes) or not isinstance(glb_bytes, bytes) or not isinstance(verification, dict):
        raise StoreError('Dữ liệu hồ sơ tàu không hợp lệ.')
    base = data_dir()
    if not base.is_dir() and version != 1:
        raise VersionConflict(0)
    with _LOCK:
        base.mkdir(parents=True, exist_ok=True)
        lock_fd = os.open(base, os.O_RDONLY) if fcntl else None
        try:
            if lock_fd is not None:
                fcntl.flock(lock_fd, fcntl.LOCK_EX)
            return _append_locked(base, profile_id, version, profile_bytes, glb_bytes, verification)
        finally:
            if lock_fd is not None:
                os.close(lock_fd)


def _append_locked(base: Path, profile_id: str, version: int, profile_bytes: bytes, glb_bytes: bytes, verification: dict) -> dict:
    latest = latest_version(profile_id)
    if version != latest + 1:
        raise VersionConflict(latest)
    if latest >= MAX_VERSIONS:
        raise StoreLimit(f'Mỗi hồ sơ tàu chỉ được lưu tối đa {MAX_VERSIONS} phiên bản.')
    if latest == 0 and profile_id not in list_ids() and len(list_ids()) >= MAX_IDS:
        raise StoreLimit(f'Chỉ được lưu tối đa {MAX_IDS} mã hồ sơ tàu.')
    manifest = {'schema': MANIFEST_SCHEMA, 'id': profile_id, 'version': version,
                'created_utc': datetime.now(timezone.utc).isoformat(), 'profile_sha256': _sha(profile_bytes),
                'glb_sha256': _sha(glb_bytes), 'glb_bytes': len(glb_bytes), 'verification': verification}
    manifest_bytes = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode('utf-8')
    folder = base / profile_id
    folder_new = not folder.exists()
    folder.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.tmp-', dir=folder))
    try:
        _write(temp / 'profile.json', profile_bytes)
        _write(temp / 'model.glb', glb_bytes)
        _write(temp / 'manifest.json', manifest_bytes)
        _fsync_dir(temp)
        target = folder / f'v{version}'
        try:
            os.rename(temp, target)
        except OSError:
            if target.exists():
                raise VersionConflict(latest_version(profile_id)) from None
            raise
        _fsync_dir(folder)
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        if folder_new:
            try:
                folder.rmdir()
            except OSError:
                pass
        raise
    return manifest


def read(profile_id: str, version: int) -> dict:
    """Return {manifest, profile_bytes, glb_path, glb_bytes} (the exact verified bytes) after verifying both files against the manifest. Never repairs."""
    try:
        _check(profile_id, version)
    except StoreError:
        raise LookupError('Không tìm thấy hồ sơ tàu.') from None
    folder = data_dir() / profile_id / f'v{version}'
    if not folder.is_dir():
        raise LookupError(f'Không tìm thấy hồ sơ tàu {profile_id} phiên bản {version}.')

    def bad(reason):
        return ProfileUnavailable(profile_id, version, reason)

    try:
        manifest = json.loads((folder / 'manifest.json').read_bytes().decode('utf-8'))
    except (OSError, ValueError):
        raise bad('không đọc được manifest.json.') from None
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS or manifest['schema'] != MANIFEST_SCHEMA:
        raise bad('manifest.json sai cấu trúc.')
    if manifest['id'] != profile_id or manifest['version'] != version or type(manifest['version']) is not int:
        raise bad('manifest.json không khớp mã hoặc phiên bản.')
    if not isinstance(manifest['verification'], dict) or type(manifest['glb_bytes']) is not int:
        raise bad('manifest.json sai cấu trúc.')
    try:
        profile_bytes = (folder / 'profile.json').read_bytes()
    except OSError:
        raise bad('thiếu hoặc không đọc được profile.json.') from None
    if _sha(profile_bytes) != manifest['profile_sha256']:
        raise bad('profile.json không khớp sha256 trong manifest.')
    glb_path = folder / 'model.glb'
    try:
        glb_bytes = glb_path.read_bytes()
    except OSError:
        raise bad('thiếu hoặc không đọc được model.glb.') from None
    if _sha(glb_bytes) != manifest['glb_sha256'] or len(glb_bytes) != manifest['glb_bytes']:
        raise bad('model.glb không khớp sha256 trong manifest.')
    return {'manifest': manifest, 'profile_bytes': profile_bytes, 'glb_path': glb_path, 'glb_bytes': glb_bytes}
