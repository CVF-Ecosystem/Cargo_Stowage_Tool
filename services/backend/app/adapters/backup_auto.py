"""M5b D1: automatic local backups (scst.backup.v1) under <SCST_DATA_DIR>/backups/auto.

Stdlib only. Nothing is created unless data exists; every failure becomes a fixed Vietnamese message without a path.

Concurrency: one module-level blocking lock guards the whole run. A second caller waits, then (run_if_due) re-checks
the 20 hour rule inside the lock, so two concurrent run_if_due calls create exactly one file. run_now always creates
one file per call (it ignores the 20 hour rule) but never in parallel with another run. The vessel store locks are
taken only inside backup_export.write_archive, never held across the rest of the run.
"""
import contextlib
import os
import re
import shutil
import sqlite3
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import backup_check, backup_export, storage
from . import vessel_profile_store as vstore

INTERVAL_HOURS = 20
KEEP = 10
EXTENSION = backup_export.EXTENSION
NAME_PATTERN = re.compile(r'^auto-\d{8}T\d{6}\d{6}Z(-\d+)?\.scstbak$')
_STAMP = re.compile(r'^auto-(\d{8}T\d{6}\d{6}Z)(?:-(\d+))?\.scstbak$')
_STAMP_FORMAT = '%Y%m%dT%H%M%S%fZ'
_NO_DATA = 'Chưa có dữ liệu để sao lưu.'
_FAILED = 'Sao lưu tự động thất bại; dữ liệu hiện tại không bị thay đổi.'
_LOCK = threading.Lock()
_state = {'last_error': None}


class NoData(Exception):
    message = _NO_DATA

    def __init__(self):
        super().__init__(self.message)


class AutoBackupFailed(Exception):
    message = _FAILED

    def __init__(self):
        super().__init__(self.message)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _data_dir() -> Path:
    return Path(os.environ.get('SCST_DATA_DIR', str(storage.ROOT / 'runtime-data')))


def auto_dir() -> Path:
    return _data_dir() / 'backups' / 'auto'


def enabled() -> bool:
    return os.environ.get('SCST_AUTO_BACKUP') != '0'


def last_error() -> str | None:
    return _state['last_error']


def _db_has_rows() -> bool:
    db_path = _data_dir() / backup_export.DB_NAME
    if not db_path.is_file():
        return False
    try:
        with contextlib.closing(sqlite3.connect(db_path.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)) as db:
            for table in ('snapshots', 'cargo_revisions'):
                try:
                    if db.execute(f'SELECT 1 FROM {table} LIMIT 1').fetchone() is not None:
                        return True
                except sqlite3.Error:
                    continue  # table missing (cargo_revisions may be absent)
    except (sqlite3.Error, OSError):
        return False
    return False


def has_data() -> bool:
    """Read-only: creates no database, directory or file."""
    if _db_has_rows():
        return True
    try:
        return bool(vstore.list_ids())  # iterdir only; an empty vessels/.lock is not a profile folder
    except OSError:
        return False


def _parse(name: str):
    match = _STAMP.fullmatch(name)
    if not match:
        return None
    moment = datetime.strptime(match.group(1), _STAMP_FORMAT).replace(tzinfo=timezone.utc)
    return moment, int(match.group(2) or 0)


def _entries() -> list[tuple[tuple, Path]]:
    """Matching regular files, newest first."""
    directory = auto_dir()
    try:
        children = list(directory.iterdir())
    except OSError:
        return []
    found = []
    for path in children:
        key = _parse(path.name) if NAME_PATTERN.fullmatch(path.name) else None
        if key is not None and path.is_file() and not path.is_symlink():
            found.append((key, path))
    found.sort(key=lambda item: item[0], reverse=True)
    return found


def _describe(key, path: Path) -> dict:
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return {'name': path.name, 'created_utc': key[0].isoformat(), 'size_bytes': size}


def list_files() -> list[dict]:
    return [_describe(key, path) for key, path in _entries()]


def _write_new(directory: Path) -> Path:
    """Temp file + fsync + link to the final name; an existing file is never overwritten (-1, -2 ... suffix)."""
    stamp = _now().strftime(_STAMP_FORMAT)
    fd, temp_name = tempfile.mkstemp(prefix='.auto-', suffix='.tmp', dir=directory)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            backup_export.write_archive(handle)
            handle.flush()
            os.fsync(handle.fileno())
        attempt = 0
        while True:
            final = directory / f'auto-{stamp}{"" if attempt == 0 else f"-{attempt}"}{EXTENSION}'
            try:
                os.link(temp, final)
                return final
            except FileExistsError:
                attempt += 1
            except OSError:  # hard links unsupported: exclusive create + copy
                try:
                    with open(final, 'xb') as out, open(temp, 'rb') as source:
                        shutil.copyfileobj(source, out)
                        out.flush()
                        os.fsync(out.fileno())
                    return final
                except FileExistsError:
                    attempt += 1
                except BaseException:
                    final.unlink(missing_ok=True)
                    raise
    finally:
        temp.unlink(missing_ok=True)


def _prune(new: Path) -> None:
    """Delete matching auto files beyond the newest KEEP; the file just created is never deleted (clock moved back)."""
    for _, path in _entries()[KEEP:]:
        if path.name == new.name:
            continue
        try:
            path.unlink()
        except OSError:
            pass


def _run_locked() -> dict:
    if not has_data():
        raise NoData()
    new = None
    try:
        directory = auto_dir()
        directory.mkdir(parents=True, exist_ok=True)
        new = _write_new(directory)
        body = new.read_bytes()
        with tempfile.TemporaryDirectory(prefix='scst-autocheck-') as work:
            backup_check.check(body, Path(work))
        key = _parse(new.name)
    except BaseException as exc:
        if new is not None:
            with contextlib.suppress(OSError):
                new.unlink()
        if isinstance(exc, Exception):
            _state['last_error'] = _FAILED
            raise AutoBackupFailed() from exc
        raise
    _state['last_error'] = None
    _prune(new)
    return _describe(key, new)


def run_now() -> dict:
    """Back up now, ignoring the 20 hour rule. Raises NoData or AutoBackupFailed."""
    with _LOCK:
        return _run_locked()


def _due() -> bool:
    entries = _entries()
    if not entries:
        return True
    return _now() - entries[0][0][0] >= timedelta(hours=INTERVAL_HOURS)


def run_if_due() -> dict | None:
    """Never raises. None when disabled, without data, not yet due, or when the run failed (see last_error)."""
    try:
        if not enabled():
            return None
        with _LOCK:
            if not has_data() or not _due():
                return None
            return _run_locked()
    except Exception:
        _state['last_error'] = _FAILED
        return None


def _background() -> None:
    try:
        run_if_due()
    except BaseException:
        pass


def start_background() -> None:
    """Start run_if_due in a daemon thread when enabled; never raises, never blocks."""
    try:
        if enabled():
            threading.Thread(target=_background, name='scst-auto-backup', daemon=True).start()
    except Exception:
        pass
