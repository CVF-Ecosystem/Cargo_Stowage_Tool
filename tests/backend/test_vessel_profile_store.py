import hashlib
import os
import threading
import pytest
from app.adapters import vessel_profile_store as store

VER = {'result': 'PASS', 'tolerance_mm': 1}


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def put(pid='TAU-A', version=1, profile=b'{"p":1}', glb=b'glTF-bytes'):
    return store.append(pid, version, profile, glb, VER)


def tree(root):
    return sorted(str(p.relative_to(root)) for p in root.rglob('*'))


def snapshot_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_constants_and_data_dir(data):
    assert store.MAX_IDS == 50 and store.MAX_VERSIONS == 50
    assert store.data_dir() == data / 'vessels'


def test_first_version_must_be_one(data):
    with pytest.raises(store.VersionConflict) as err:
        put(version=2)
    assert err.value.latest == 0
    assert not (data / 'vessels').exists() or not any((data / 'vessels').rglob('v*'))
    manifest = put(version=1, profile=b'abc', glb=b'xyz')
    assert manifest['schema'] == 'scst.vessel-profile-manifest.v1'
    assert manifest['id'] == 'TAU-A' and manifest['version'] == 1
    assert manifest['profile_sha256'] == hashlib.sha256(b'abc').hexdigest()
    assert manifest['glb_sha256'] == hashlib.sha256(b'xyz').hexdigest()
    assert manifest['glb_bytes'] == 3 and manifest['verification'] == VER
    assert manifest['created_utc'].endswith('+00:00')
    folder = data / 'vessels' / 'TAU-A' / 'v1'
    assert sorted(p.name for p in folder.iterdir()) == ['manifest.json', 'model.glb', 'profile.json']
    assert (folder / 'profile.json').read_bytes() == b'abc' and (folder / 'model.glb').read_bytes() == b'xyz'


def test_second_version_after_first_and_read_roundtrip(data):
    put(version=1, profile=b'one')
    put(version=2, profile=b'two', glb=b'g2')
    assert store.versions('TAU-A') == [1, 2] and store.latest_version('TAU-A') == 2
    assert store.list_ids() == ['TAU-A']
    got = store.read('TAU-A', 2)
    assert got['profile_bytes'] == b'two' and got['glb_path'].read_bytes() == b'g2'
    assert got['manifest']['version'] == 2
    assert store.read('TAU-A', 1)['profile_bytes'] == b'one'


@pytest.mark.parametrize('version', [4, 5, 1, 2, 0, -1])
def test_wrong_version_conflicts_and_writes_nothing(data, version):
    put(version=1)
    put(version=2)
    before = tree(data)
    bytes_before = snapshot_bytes(data)
    with pytest.raises((store.VersionConflict, store.StoreError)) as err:
        put(version=version, profile=b'other')
    if isinstance(err.value, store.VersionConflict):
        assert err.value.latest == 2
    assert tree(data) == before and snapshot_bytes(data) == bytes_before


def test_non_int_version_rejected(data):
    for bad in (True, 1.0, '1', None):
        with pytest.raises(store.StoreError):
            put(version=bad)
    assert not (data / 'vessels').exists()


def test_no_overwrite_same_version(data):
    put(version=1, profile=b'orig')
    before = snapshot_bytes(data)
    with pytest.raises(store.VersionConflict):
        put(version=1, profile=b'changed', glb=b'changed')
    assert snapshot_bytes(data) == before


def test_race_target_exists_removes_temp(data, monkeypatch):
    put(version=1)
    real_latest = store.latest_version
    calls = {'n': 0}

    def stale(pid):  # first call (inside append) claims v1 is latest even after another writer made v2
        calls['n'] += 1
        return 1 if calls['n'] == 1 else real_latest(pid)
    put(version=2)
    before = snapshot_bytes(data)
    with monkeypatch.context() as m:
        m.setattr(store, 'latest_version', stale)
        with pytest.raises(store.VersionConflict) as err:
            put(version=2, profile=b'racer')
    assert err.value.latest == 2
    assert snapshot_bytes(data) == before
    assert not [p for p in (data / 'vessels' / 'TAU-A').iterdir() if p.name.startswith('.tmp-')]


def test_failure_during_rename_leaves_no_version(data, monkeypatch):
    put(version=1)
    before = snapshot_bytes(data)

    def boom(*args, **kwargs):
        raise OSError('disk full')
    with monkeypatch.context() as m:
        m.setattr(os, 'rename', boom)
        with pytest.raises(OSError):
            put(version=2)
    assert store.versions('TAU-A') == [1]
    assert snapshot_bytes(data) == before
    assert not [p for p in (data / 'vessels' / 'TAU-A').iterdir() if p.name != 'v1']


def test_failure_during_write_leaves_nothing_for_new_id(data, monkeypatch):
    def boom(path, data_):
        raise OSError('io error')
    with monkeypatch.context() as m:
        m.setattr(store, '_write', boom)
        with pytest.raises(OSError):
            put(pid='TAU-NEW', version=1)
    assert store.list_ids() == [] and store.versions('TAU-NEW') == []
    assert not (data / 'vessels' / 'TAU-NEW').exists()


@pytest.mark.parametrize('victim', ['profile.json', 'model.glb'])
def test_tampered_file_is_unavailable_and_untouched(data, victim):
    put(version=1)
    path = data / 'vessels' / 'TAU-A' / 'v1' / victim
    path.write_bytes(path.read_bytes() + b'X')
    before = snapshot_bytes(data)
    with pytest.raises(store.ProfileUnavailable) as err:
        store.read('TAU-A', 1)
    assert err.value.profile_id == 'TAU-A' and err.value.version == 1
    assert snapshot_bytes(data) == before


@pytest.mark.parametrize('content', [b'not json', b'[]', b'{}', b'\xff\xfe',
                                     b'{"schema":"x"}'])
def test_bad_manifest_is_unavailable_and_untouched(data, content):
    put(version=1)
    (data / 'vessels' / 'TAU-A' / 'v1' / 'manifest.json').write_bytes(content)
    before = snapshot_bytes(data)
    with pytest.raises(store.ProfileUnavailable):
        store.read('TAU-A', 1)
    assert snapshot_bytes(data) == before


def test_manifest_id_or_version_mismatch(data):
    import json
    put(version=1)
    path = data / 'vessels' / 'TAU-A' / 'v1' / 'manifest.json'
    manifest = json.loads(path.read_text('utf-8'))
    for field, value in (('id', 'TAU-B'), ('version', 2), ('schema', 'other'), ('verification', []), ('glb_bytes', 99)):
        path.write_text(json.dumps({**manifest, field: value}), 'utf-8')
        with pytest.raises(store.ProfileUnavailable):
            store.read('TAU-A', 1)
    path.write_text(json.dumps({k: v for k, v in manifest.items() if k != 'glb_sha256'}), 'utf-8')
    with pytest.raises(store.ProfileUnavailable):
        store.read('TAU-A', 1)


@pytest.mark.parametrize('missing', ['profile.json', 'model.glb'])
def test_missing_file_is_unavailable(data, missing):
    put(version=1)
    (data / 'vessels' / 'TAU-A' / 'v1' / missing).unlink()
    with pytest.raises(store.ProfileUnavailable):
        store.read('TAU-A', 1)


def test_absent_raises_lookup_error(data):
    with pytest.raises(LookupError):
        store.read('TAU-A', 1)
    put(version=1)
    with pytest.raises(LookupError):
        store.read('TAU-A', 2)
    with pytest.raises(LookupError):
        store.read('../x', 1)
    assert store.versions('NOPE') == [] and store.latest_version('NOPE') == 0 and store.list_ids() == ['TAU-A']


def test_version_limit(data, monkeypatch):
    monkeypatch.setattr(store, 'MAX_VERSIONS', 3)
    for v in (1, 2, 3):
        put(version=v)
    before = tree(data)
    with pytest.raises(store.StoreLimit):
        put(version=4)
    assert tree(data) == before and store.latest_version('TAU-A') == 3


def test_id_limit(data, monkeypatch):
    monkeypatch.setattr(store, 'MAX_IDS', 3)
    for n in range(3):
        put(pid=f'TAU-{n}')
    before = tree(data)
    with pytest.raises(store.StoreLimit):
        put(pid='TAU-9')
    assert tree(data) == before
    put(pid='TAU-0', version=2)  # an existing id may still grow
    assert store.list_ids() == ['TAU-0', 'TAU-1', 'TAU-2']


def test_real_limits_of_fifty(data):
    for v in range(1, 51):
        put(version=v, profile=b'p', glb=b'g')
    assert store.versions('TAU-A') == list(range(1, 51))
    with pytest.raises(store.StoreLimit):
        put(version=51)
    for n in range(49):
        put(pid=f'ID-{n:02d}')
    assert len(store.list_ids()) == 50
    with pytest.raises(store.StoreLimit):
        put(pid='ONE-TOO-MANY')
    assert len(store.list_ids()) == 50


@pytest.mark.parametrize('pid', ['', 'a', 'tau-a', 'A', '-AB', 'A_B', '../X', 'A/B', 'A\\B', '..', '.', 'A' * 33,
                                 'TAU A', 'TÀU', None, 5])
def test_invalid_id_rejected(data, pid):
    with pytest.raises(store.StoreError):
        store.append(pid, 1, b'p', b'g', VER)
    assert not (data / 'vessels').exists() and not (data.parent / 'X').exists()
    assert store.versions(pid) == [] and store.latest_version(pid) == 0


def test_temp_dirs_and_junk_ignored(data):
    put(version=1)
    folder = data / 'vessels' / 'TAU-A'
    (folder / '.tmp-crash').mkdir()
    (folder / '.tmp-crash' / 'manifest.json').write_text('{}')
    (folder / 'v2').mkdir()  # no manifest
    (folder / 'v03').mkdir()
    (folder / 'vx').mkdir()
    (folder / 'notes.txt').write_text('x')
    (data / 'vessels' / '.tmp-root').mkdir()
    (data / 'vessels' / 'EMPTY-ID').mkdir()
    (data / 'vessels' / '.lock').write_text('')
    assert store.versions('TAU-A') == [1]
    assert store.list_ids() == ['TAU-A']
    put(version=2)  # v2 dir without manifest does not count as latest; rename onto the empty dir is not attempted as safe
    assert store.versions('TAU-A') == [1, 2]


def test_non_empty_leftover_version_dir_is_conflict_and_untouched(data):
    put(version=1)
    leftover = data / 'vessels' / 'TAU-A' / 'v2'
    leftover.mkdir()
    (leftover / 'keep.bin').write_bytes(b'x')
    with pytest.raises(store.VersionConflict):
        put(version=2)
    assert (leftover / 'keep.bin').read_bytes() == b'x'
    assert store.versions('TAU-A') == [1]


def test_concurrent_same_version_exactly_one_wins(data):
    results = []
    barrier = threading.Barrier(8)

    def worker(n):
        barrier.wait()
        try:
            put(version=1, profile=f'p{n}'.encode(), glb=f'g{n}'.encode())
            results.append('ok')
        except store.VersionConflict as exc:
            results.append(exc.latest)
    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count('ok') == 1 and results.count(1) == 7
    assert store.versions('TAU-A') == [1]
    assert store.read('TAU-A', 1)['manifest']['version'] == 1
    assert not [p for p in (data / 'vessels' / 'TAU-A').iterdir() if p.name.startswith('.tmp-')]
