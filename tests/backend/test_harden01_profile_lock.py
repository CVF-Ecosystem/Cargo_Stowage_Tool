"""HARDEN-01 H5: append() takes a cross-process file lock (flock on POSIX, msvcrt.locking on <vessels>/.lock on Windows)."""
import multiprocessing
import os
import time
import types
import pytest
from app.adapters import vessel_profile_store as store

VER = {'result': 'PASS', 'tolerance_mm': 1}
JOIN_S = 60


def _append_worker(data_dir, pid, ready, go, out):
    """Child process (top level so spawn can import it): wait for the start signal, append v1, report plain data."""
    os.environ['SCST_DATA_DIR'] = data_dir
    ready.set()
    go.wait(JOIN_S)
    try:
        manifest = store.append(pid, 1, b'{"p":1}', b'glTF-' + str(os.getpid()).encode(), VER)
        out.put(('ok', manifest['version']))
    except store.VersionConflict as err:
        out.put(('conflict', err.latest))
    except BaseException as err:  # report anything else so the parent fails with a message instead of hanging
        out.put(('error', repr(err)))


def _spawn(ctx, data_dir, pid, go, out):
    ready = ctx.Event()
    proc = ctx.Process(target=_append_worker, args=(str(data_dir), pid, ready, go, out))
    proc.start()
    return proc, ready


def _stop(procs):
    for proc in procs:
        if proc.is_alive():
            proc.terminate()
        proc.join(5)


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def test_two_processes_same_version_exactly_one_wins(data):
    ctx = multiprocessing.get_context('spawn')
    for n in range(5):
        pid = f'RACE-{n}'
        go, out = ctx.Event(), ctx.Queue()
        procs = [_spawn(ctx, data, pid, go, out) for _ in range(2)]
        try:
            for _, ready in procs:
                assert ready.wait(JOIN_S)
            go.set()
            results = [out.get(timeout=JOIN_S) for _ in range(2)]
            for proc, _ in procs:
                proc.join(JOIN_S)
                assert not proc.is_alive() and proc.exitcode == 0
        finally:
            _stop([p for p, _ in procs])
        assert sorted(r[0] for r in results) == ['conflict', 'ok'], results
        assert ('ok', 1) in results and ('conflict', 1) in results
        folder = data / 'vessels' / pid
        assert sorted(p.name for p in folder.iterdir()) == ['v1']
        assert store.versions(pid) == [1] and store.read(pid, 1)['manifest']['id'] == pid
    assert store.list_ids() == [f'RACE-{n}' for n in range(5)]


def test_held_process_lock_blocks_other_process_until_released(data):
    ctx = multiprocessing.get_context('spawn')
    base = store.data_dir()
    base.mkdir(parents=True)
    go, out = ctx.Event(), ctx.Queue()
    go.set()
    proc, ready = _spawn(ctx, data, 'HELD-1', go, out)
    try:
        with store._process_lock(base):
            assert ready.wait(JOIN_S)
            proc.join(1.5)
            assert proc.is_alive(), 'child finished while the parent held the process lock'
            assert out.empty() and store.versions('HELD-1') == []
        proc.join(JOIN_S)
        assert not proc.is_alive() and proc.exitcode == 0
        assert out.get(timeout=JOIN_S) == ('ok', 1)
    finally:
        _stop([proc])
    assert store.versions('HELD-1') == [1]
    assert not [p for p in (base / 'HELD-1').iterdir() if p.name.startswith('.tmp-')]


class FakeMsvcrt:
    LK_LOCK, LK_UNLCK = 1, 0

    def __init__(self, fail_first=0, always_fail=False):
        self.calls, self.fail_first, self.always_fail = [], fail_first, always_fail

    def locking(self, fd, mode, nbytes):
        os.fstat(fd)  # fd must be open
        self.calls.append((fd, mode, nbytes, os.lseek(fd, 0, os.SEEK_CUR)))
        if mode == self.LK_LOCK and (self.always_fail or self.fail_first > 0):
            self.fail_first -= 1
            raise OSError(36, 'Resource deadlock avoided')  # what LK_LOCK raises after its ~10 s of retries


def test_windows_branch_with_fake_msvcrt(data, monkeypatch):
    fake = FakeMsvcrt(fail_first=2)
    monkeypatch.setattr(store, 'fcntl', None)
    monkeypatch.setattr(store, 'msvcrt', fake)
    manifest = store.append('WIN-1', 1, b'{"p":1}', b'glb', VER)
    base = store.data_dir()
    assert manifest['version'] == 1 and (base / '.lock').is_file()
    # two failed LK_LOCK attempts are retried, then one success, then exactly one unlock; all on byte 0, length 1
    modes = [c[1] for c in fake.calls]
    assert modes == [fake.LK_LOCK] * 3 + [fake.LK_UNLCK]
    assert {(c[2], c[3]) for c in fake.calls} == {(1, 0)}
    fd = fake.calls[0][0]
    assert {c[0] for c in fake.calls} == {fd}
    with pytest.raises(OSError):
        os.fstat(fd)  # closed after the unlock
    # '.lock' is never a profile id and the stored layout is unchanged
    assert store.list_ids() == ['WIN-1'] and not store.ID_PATTERN.fullmatch('.lock')
    assert sorted(p.name for p in base.iterdir()) == ['.lock', 'WIN-1']
    assert sorted(p.name for p in (base / 'WIN-1').iterdir()) == ['v1']
    # a second append reuses the lock file and conflicts cleanly, still unlocking and closing
    fake.calls.clear()
    with pytest.raises(store.VersionConflict):
        store.append('WIN-1', 1, b'{"p":1}', b'glb', VER)
    assert [c[1] for c in fake.calls] == [fake.LK_LOCK, fake.LK_UNLCK]


def test_windows_branch_gives_up_after_bounded_wait_without_unlock(data, monkeypatch):
    fake = FakeMsvcrt(always_fail=True)
    monkeypatch.setattr(store, 'fcntl', None)
    monkeypatch.setattr(store, 'msvcrt', fake)
    monkeypatch.setattr(store, 'LOCK_WAIT_SECONDS', 0.05)
    start = time.monotonic()
    with pytest.raises(store.StoreError) as err:
        store.append('WIN-2', 1, b'{"p":1}', b'glb', VER)
    assert time.monotonic() - start < 10 and 'bận' in str(err.value)
    assert len(fake.calls) >= 1 and all(c[1] == fake.LK_LOCK for c in fake.calls)  # never locked, so never unlocked
    with pytest.raises(OSError):
        os.fstat(fake.calls[0][0])
    assert store.versions('WIN-2') == [] and not (store.data_dir() / 'WIN-2').exists()


def test_windows_branch_unlocks_when_body_raises(data, monkeypatch):
    fake = FakeMsvcrt()
    monkeypatch.setattr(store, 'fcntl', None)
    monkeypatch.setattr(store, 'msvcrt', fake)
    base = store.data_dir()
    base.mkdir(parents=True)
    with pytest.raises(RuntimeError):
        with store._process_lock(base):
            raise RuntimeError('boom')
    assert [c[1] for c in fake.calls] == [fake.LK_LOCK, fake.LK_UNLCK]
    with pytest.raises(OSError):
        os.fstat(fake.calls[0][0])
