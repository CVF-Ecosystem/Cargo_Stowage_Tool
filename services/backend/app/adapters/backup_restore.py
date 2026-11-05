"""M5a D3: replace-all restore of a scst.backup.v1 archive, atomic with rollback.

Order of one apply() (everything between 'checked' and 'cache_cleared' is undone on any failure):
  confirm check -> lock (vessel _LOCK + process lock) -> extract+verify into <data>/.restore-* (full D2) -> pre-restore backup
  -> move live DB (and -journal/-wal/-shm) aside, move the verified DB in -> move every child of vessels/ (except '.lock')
  aside, move the verified <ID> directories in -> clear the HARDEN-01 replay cache -> remove the work directory.

The Windows lock file <vessels>/.lock is held open while locked, so the vessels directory itself is never renamed:
only its children move. Every move is recorded in a journal *before* it is attempted; rollback reverses the journal in
reverse order and reverses an entry only when its destination exists and its source does not, so a move that failed
(or was interrupted) is skipped and a move that completed is undone. The pre-restore backup is kept on success and failure.
"""
import hashlib
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import backup_check, backup_export, plan_binding, storage
from . import vessel_profile_store as vstore
from .backup_check import BackupRejected

PREFIX = 'pre-restore-'
BACKUPS_DIR = 'backups'
WORKDIR_PREFIX = '.restore-'
DATABASE = 'scst.sqlite3'
SIDECARS = ('-journal', '-wal', '-shm')
_FAILED = ('Khôi phục thất bại; dữ liệu hiện tại đã được giữ nguyên. '
           'Bản sao lưu trước khôi phục (nếu đã tạo) vẫn nằm trong thư mục backups.')
_STEPS = ('checked', 'pre_backup_written', 'db_moved_aside', 'db_replaced', 'vessel_moved_aside', 'vessels_old_aside',
          'vessel_moved_in', 'vessels_replaced', 'cache_cleared')


class ConfirmMismatch(BackupRejected):
    """`confirm` is not the sha256 of the request body. Raised before anything is written."""


def _step(name: str) -> None:
    """Fault-injection hook, called after each completed step. A no-op in production; tests replace it."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _data_dir() -> Path:
    return Path(os.environ.get('SCST_DATA_DIR', str(storage.ROOT / 'runtime-data')))


class _Journal:
    """Moves done (or in progress), reversed in reverse order on rollback."""

    def __init__(self):
        self.entries: list[tuple[Path, Path]] = []

    def move(self, src: Path, dst: Path) -> None:
        self.entries.append((src, dst))  # recorded first: an interrupted move is resolved by existence checks in undo()
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.replace(src, dst)

    def undo(self) -> None:
        for src, dst in reversed(self.entries):
            try:
                if os.path.lexists(dst) and not os.path.lexists(src):
                    os.replace(dst, src)
            except OSError:
                continue  # keep restoring the remaining entries; nothing else can be done for this one
        self.entries.clear()


def _write_pre_restore_backup(backups: Path) -> str:
    """Write <backups>/pre-restore-<UTC>.scstbak via a temp file; an existing file is never overwritten (-1, -2 ... suffix)."""
    backups.mkdir(parents=True, exist_ok=True)
    stamp = _now().strftime('%Y%m%dT%H%M%S%fZ')
    fd, temp_name = tempfile.mkstemp(prefix='.pre-restore-', suffix='.tmp', dir=backups)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            backup_export.write_archive(handle, lock_held=True)
            handle.flush()
            os.fsync(handle.fileno())
        attempt = 0
        while True:
            name = f'{PREFIX}{stamp}{"" if attempt == 0 else f"-{attempt}"}{backup_export.EXTENSION}'
            final = backups / name
            try:
                os.link(temp, final)
                return name
            except FileExistsError:
                attempt += 1
            except OSError:  # hard links unsupported on this file system: exclusive create + copy
                try:
                    with open(final, 'xb') as out, open(temp, 'rb') as source:
                        shutil.copyfileobj(source, out)
                        out.flush()
                        os.fsync(out.fileno())
                    return name
                except FileExistsError:
                    attempt += 1
                except BaseException:
                    final.unlink(missing_ok=True)
                    raise
    finally:
        temp.unlink(missing_ok=True)


def _swap_database(live: Path, new_db: Path, old_dir: Path, journal: _Journal) -> None:
    for suffix in ('',) + SIDECARS:
        source = live.with_name(live.name + suffix)
        if os.path.lexists(source):
            journal.move(source, old_dir / source.name)
    _step('db_moved_aside')
    journal.move(new_db, live)
    _step('db_replaced')


def _swap_vessels(base: Path, new_vessels: Path, old_dir: Path, journal: _Journal) -> None:
    for entry in sorted(base.iterdir(), key=lambda p: p.name):
        if entry.name == '.lock':
            continue
        journal.move(entry, old_dir / entry.name)
        _step('vessel_moved_aside')
    _step('vessels_old_aside')
    if new_vessels.is_dir():
        for entry in sorted(new_vessels.iterdir(), key=lambda p: p.name):
            journal.move(entry, base / entry.name)
            _step('vessel_moved_in')
    _step('vessels_replaced')


def _remove_created_base(base: Path) -> None:
    """Remove the vessels dir that apply() created, once it holds nothing but the Windows lock file (an empty regular .lock).
    Call only after the process lock is released; a directory with any other content is left as it is."""
    try:
        names = [p.name for p in base.iterdir()]
    except OSError:
        return
    try:
        if names == ['.lock']:
            lock = base / '.lock'
            if lock.is_file() and not lock.is_symlink() and lock.stat().st_size == 0:
                lock.unlink()
        base.rmdir()
    except OSError:
        pass


def apply(body: bytes, confirm: str) -> dict:
    """Replace all local data with the backup `body`. Returns {"counts", "pre_restore_backup"} (a file name, never a path)."""
    if not isinstance(confirm, str) or confirm != hashlib.sha256(body).hexdigest():
        raise ConfirmMismatch('Mã xác nhận không khớp tệp sao lưu gửi lên; chưa thay đổi gì.', 'confirm')
    data = _data_dir()
    data.mkdir(parents=True, exist_ok=True)
    base = vstore.data_dir()
    with vstore._LOCK:
        base_created = not base.exists()
        base.mkdir(parents=True, exist_ok=True)
        workdir = Path(tempfile.mkdtemp(prefix=WORKDIR_PREFIX, dir=data))
        journal = _Journal()
        committed = False
        try:
            with vstore._process_lock(base):
                new_dir = workdir / 'new'
                new_dir.mkdir()
                result = backup_check.check(body, new_dir)  # full D2 again
                _step('checked')
                pre_restore = _write_pre_restore_backup(data / BACKUPS_DIR)
                _step('pre_backup_written')
                # No SQLite connection of this module is open here; every request opens and closes its own.
                _swap_database(data / DATABASE, new_dir / DATABASE, workdir / 'old', journal)
                _swap_vessels(base, new_dir / 'vessels', workdir / 'old-vessels', journal)
                plan_binding.clear_replay_cache()
                _step('cache_cleared')
                committed = True
        except BaseException as exc:
            if not committed:
                journal.undo()
                plan_binding.clear_replay_cache()
            shutil.rmtree(workdir, ignore_errors=True)
            if not committed and base_created:
                _remove_created_base(base)  # outside the process lock; only when this call created it
            if isinstance(exc, BackupRejected) or not isinstance(exc, Exception):
                raise  # a rejected archive keeps its own message; KeyboardInterrupt/SystemExit stay what they are
            raise BackupRejected(_FAILED, 'restore') from exc
        # Committed: a cleanup problem must not undo the restore.
        shutil.rmtree(workdir, ignore_errors=True)
        if base_created:
            _remove_created_base(base)  # outside the process lock; only when this call created it
    return {'counts': result['counts'], 'pre_restore_backup': pre_restore}
