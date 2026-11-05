"""M5a D3: replace-all restore. Data is built through the API; faults are injected at every step of the swap."""
import base64
import hashlib
import io
import os
import sqlite3
import threading
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters import backup_check, backup_export, backup_restore, plan_binding
from app.adapters import vessel_profile_store as vstore
from app.demo import demo_plan
from app.main import app
from glb_fixture import make_glb
from test_m5a_preview import PROFILE_ID, SOURCE, _profile

client = TestClient(app, raise_server_exceptions=False)

STEPS = ['checked', 'pre_backup_written', 'db_moved_aside', 'db_replaced', 'vessel_moved_aside', 'vessels_old_aside',
         'vessel_moved_in', 'vessels_replaced', 'cache_cleared']


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    live = tmp_path / 'live'
    live.mkdir()
    monkeypatch.setenv('SCST_DATA_DIR', str(live))
    return live


# ------------------------------------------------------------------ helpers
def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(root: Path):
    """{relative path: sha256} of every file under the data dir except backups/; empty dirs are listed as well."""
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root).as_posix()
        if relative == 'backups' or relative.startswith('backups/'):
            continue
        result[relative] = sha(path.read_bytes()) if path.is_file() else 'DIR'
    return result


def save_plan(name):
    r = client.post('/api/snapshots', json={'name': name, 'plan': demo_plan().model_dump(mode='json')})
    assert r.status_code == 200, r.text
    return r.json()['id']


def add_revision(mass):
    latest = client.get('/api/cargo-revisions').json()['latest_revision_id']
    group = {'bundle_count': 2, 'pieces_per_bundle': 10, 'dimensions_um': [6000000, 300000, 300000], 'mass_g': mass,
             'outside_diameter_mm': '60.3', 'wall_thickness_mm': '3.91', 'dimension_warning': False}
    r = client.post('/api/cargo-revisions', json={'parent_revision_id': latest, 'source': SOURCE, 'changes': [
        {'type': 'ADD_GROUP', 'confirmation': 'UNVERIFIED', 'group': group}]})
    assert r.status_code == 200, r.text


def add_profile(version=1):
    profile = {**_profile(), 'version': version}
    glb = make_glb([((-6, 0, -3), (6, 4, 3))])
    r = client.post('/api/vessel-profiles', json={'profile': profile, 'glb_base64': base64.b64encode(glb).decode()})
    assert r.status_code == 200, r.text


def populate(plans=2, revisions=2):
    ids = [save_plan(f'Phương án {i + 1}') for i in range(plans)]
    for i in range(revisions):
        add_revision(500000 + i)
    add_profile()
    return ids


def export():
    r = client.get('/api/backup/export')
    assert r.status_code == 200
    return r.content


def restore(body, confirm=None):
    return client.post('/api/backup/restore/apply', params={'confirm': confirm or sha(body)}, content=body,
                       headers={'content-type': 'application/octet-stream'})


def rows(data, table):
    con = sqlite3.connect(data / 'scst.sqlite3')
    try:
        return con.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall()
    finally:
        con.close()


def no_workdir(data):
    assert [p.name for p in data.iterdir() if p.name.startswith('.restore-')] == []


def fault(monkeypatch, name, occurrence=1, error=RuntimeError):
    """Make the `occurrence`-th call of _step(name) raise."""
    seen = {'n': 0}

    def hook(step):
        if step == name:
            seen['n'] += 1
            if seen['n'] == occurrence:
                raise error(f'tiêm lỗi {name} #{occurrence}')
    monkeypatch.setattr(backup_restore, '_step', hook)
    return seen


# ------------------------------------------------------------------ 1. confirm
def test_wrong_confirm_is_409_and_writes_nothing(data):
    populate()
    body = export()
    add_revision(999999)
    before = fingerprint(data)
    for confirm in ('0' * 64, sha(body)[:-1], sha(body).upper(), ''):
        r = client.post('/api/backup/restore/apply', params={'confirm': confirm}, content=body,
                        headers={'content-type': 'application/octet-stream'})
        assert r.status_code == 409, r.text
        assert r.json()['detail']['errors']
    assert fingerprint(data) == before
    assert not (data / 'backups').exists()
    no_workdir(data)


def test_confirm_of_other_bytes_is_409(data):
    populate()
    body = export()
    assert restore(body, sha(body + b'x')).status_code == 409
    assert not (data / 'backups').exists()


def test_rejected_archive_is_400_and_writes_nothing(data):
    populate()
    before = fingerprint(data)
    body = b'khong phai zip'
    r = restore(body)
    assert r.status_code == 400
    assert fingerprint(data) == before
    assert not (data / 'backups').exists()
    no_workdir(data)


# ------------------------------------------------------------------ 2. round trip
def test_round_trip_replaces_everything_and_keeps_pre_restore_backup(data):
    ids = populate()
    body = export()
    at_export = fingerprint(data)
    snapshots = rows(data, 'snapshots')
    revisions = rows(data, 'cargo_revisions')
    assert len(snapshots) == 2 and len(revisions) == 2
    third = save_plan('Phương án 3')
    add_revision(777777)
    add_profile(version=2)
    assert len(client.get('/api/snapshots').json()) == 3
    assert vstore.versions(PROFILE_ID) == [1, 2]

    r = restore(body)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['counts'] == {'plans': 2, 'revisions': 2, 'vessel_profile_versions': 1}
    name = result['pre_restore_backup']
    assert name.startswith('pre-restore-') and name.endswith('.scstbak') and '/' not in name and '\\' not in name

    assert rows(data, 'snapshots') == snapshots
    assert rows(data, 'cargo_revisions') == revisions
    # vessels/** byte for byte; the DB file is the backup's copy of the database, so it is compared by rows above
    assert {k: v for k, v in fingerprint(data).items() if k != 'scst.sqlite3'} == {k: v for k, v in at_export.items() if k != 'scst.sqlite3'}
    no_workdir(data)

    listing = client.get('/api/snapshots').json()
    assert sorted(item['id'] for item in listing) == sorted(ids)
    assert third not in [item['id'] for item in listing]
    for snapshot_id in ids:
        assert client.get(f'/api/snapshots/{snapshot_id}').status_code == 200
    assert client.get(f'/api/snapshots/{third}').status_code == 400
    chain = client.get('/api/cargo-revisions').json()
    assert len(chain['revisions']) == 3  # base + the 2 restored revisions
    assert [client.get(f"/api/cargo-revisions/{item['revision_id']}").status_code for item in chain['revisions']] == [200, 200, 200]
    assert vstore.versions(PROFILE_ID) == [1]
    assert client.get(f'/api/vessel-profiles/{PROFILE_ID}/1').status_code == 200
    assert client.get(f'/api/vessel-profiles/{PROFILE_ID}/2').status_code in (400, 404)

    pre = (data / 'backups' / name).read_bytes()
    work = data / 'verify-pre'
    work.mkdir()
    checked = backup_check.check(pre, work)
    assert checked['counts'] == {'plans': 3, 'revisions': 3, 'vessel_profile_versions': 2}
    # the pre-restore backup is a normal D1 archive and can itself be restored
    assert zipfile.ZipFile(io.BytesIO(pre)).testzip() is None


def test_restore_into_empty_data_dir_and_back(data):
    populate()
    body = export()
    for child in list(data.iterdir()):
        if child.is_dir():
            import shutil
            shutil.rmtree(child)
        else:
            child.unlink()
    r = restore(body)
    assert r.status_code == 200, r.text
    assert len(client.get('/api/snapshots').json()) == 2
    pre = (data / 'backups' / r.json()['pre_restore_backup']).read_bytes()
    assert backup_check.check(pre, data / 'verify-empty')['counts'] == {'plans': 0, 'revisions': 0, 'vessel_profile_versions': 0}


def test_restore_without_vessels_removes_live_vessels(data):
    save_plan('Một')
    body = export()  # no vessels in it
    add_profile()
    assert vstore.versions(PROFILE_ID) == [1]
    r = restore(body)
    assert r.status_code == 200, r.text
    assert vstore.versions(PROFILE_ID) == []
    assert not any(p for p in (data / 'vessels').iterdir() if p.name != '.lock')


def test_other_children_of_vessels_are_replaced_too(data):
    populate()
    body = export()
    (data / 'vessels' / 'stray.txt').write_bytes(b'x')
    (data / 'vessels' / 'OLD-ONE' / 'v1').mkdir(parents=True)
    (data / 'vessels' / '.lock').write_bytes(b'')
    assert restore(body).status_code == 200
    assert sorted(p.name for p in (data / 'vessels').iterdir() if p.name != '.lock') == [PROFILE_ID]


# ------------------------------------------------------------------ 3. fault injection at every step
@pytest.mark.parametrize('step', STEPS)
@pytest.mark.parametrize('error', [RuntimeError, OSError])
def test_fault_at_every_step_leaves_data_byte_identical(data, monkeypatch, step, error):
    populate()
    body = export()
    save_plan('Thứ ba')
    add_revision(123456)
    add_profile(version=2)
    (data / 'vessels' / 'EXTRA' / 'v1').mkdir(parents=True)  # a second vessel-side entry so repeated steps repeat
    before = fingerprint(data)
    seen = fault(monkeypatch, step, error=error)
    r = restore(body)
    assert seen['n'] >= 1, 'bước chưa từng được gọi'
    assert r.status_code == 400, r.text
    assert 'giữ nguyên' in r.json()['detail']['message']
    assert fingerprint(data) == before
    no_workdir(data)
    # the live data still works
    assert len(client.get('/api/snapshots').json()) == 3
    assert vstore.versions(PROFILE_ID) == [1, 2]


@pytest.mark.parametrize('step,occurrence', [('vessel_moved_aside', 1), ('vessel_moved_aside', 2), ('vessel_moved_aside', 3),
                                              ('vessel_moved_in', 1), ('vessel_moved_in', 2)])
def test_fault_at_kth_repeated_step(data, monkeypatch, step, occurrence):
    populate()
    add_profile(version=2)
    other = {**_profile(), 'id': 'OTHERSHIP', 'version': 1}
    glb = make_glb([((-6, 0, -3), (6, 4, 3))])
    assert client.post('/api/vessel-profiles', json={'profile': other, 'glb_base64': base64.b64encode(glb).decode()}).status_code == 200
    (data / 'vessels' / 'STRAY').mkdir()
    body = export()
    # new tree has 2 ids (PROFILE_ID, OTHERSHIP); live has 3 children besides .lock (+ one more added below)
    (data / 'vessels' / 'STRAY2').mkdir()
    before = fingerprint(data)
    seen = fault(monkeypatch, step, occurrence)
    r = restore(body)
    assert seen['n'] == occurrence
    assert r.status_code == 400, r.text
    assert fingerprint(data) == before
    no_workdir(data)


def test_fault_when_vessels_dir_did_not_exist_removes_it_again(data, monkeypatch):
    save_plan('Một')
    body = export()
    assert not (data / 'vessels').exists()
    before = fingerprint(data)
    fault(monkeypatch, 'vessels_replaced')
    assert restore(body).status_code == 400
    assert not (data / 'vessels').exists()
    assert fingerprint(data) == before


def test_fault_when_no_live_database_existed(data, monkeypatch):
    save_plan('Nguồn')
    body = export()
    (data / 'scst.sqlite3').unlink()
    before = fingerprint(data)
    assert before == {}
    fault(monkeypatch, 'db_replaced')
    assert restore(body).status_code == 400
    assert fingerprint(data) == before


def test_os_replace_failure_on_database_move(data, monkeypatch):
    populate()
    body = export()
    save_plan('Thứ ba')
    before = fingerprint(data)
    real = os.replace

    def failing(src, dst, *args, **kwargs):
        if Path(src).name == 'scst.sqlite3':
            raise PermissionError('khóa tệp')
        return real(src, dst, *args, **kwargs)
    monkeypatch.setattr(os, 'replace', failing)
    r = restore(body)
    assert r.status_code == 400
    assert fingerprint(data) == before
    no_workdir(data)


def test_os_replace_failure_on_installing_the_new_database(data, monkeypatch):
    populate()
    body = export()
    save_plan('Thứ ba')
    before = fingerprint(data)
    real = os.replace

    def failing(src, dst, *args, **kwargs):
        if Path(src).name == 'scst.sqlite3' and Path(src).parent.name == 'new':
            raise PermissionError('khóa tệp')
        return real(src, dst, *args, **kwargs)
    monkeypatch.setattr(os, 'replace', failing)
    assert restore(body).status_code == 400
    assert fingerprint(data) == before
    no_workdir(data)


def test_os_replace_failure_while_moving_vessels_in(data, monkeypatch):
    populate()
    body = export()
    add_profile(version=2)
    before = fingerprint(data)
    real = os.replace

    def failing(src, dst, *args, **kwargs):
        if Path(src).parent.name == 'vessels' and Path(src).parent.parent.name == 'new':
            raise PermissionError('khóa thư mục')
        return real(src, dst, *args, **kwargs)
    monkeypatch.setattr(os, 'replace', failing)
    assert restore(body).status_code == 400
    assert fingerprint(data) == before
    no_workdir(data)


def test_keyboard_interrupt_rolls_back_and_propagates(data, monkeypatch):
    populate()
    body = export()
    save_plan('Thứ ba')
    before = fingerprint(data)
    fault(monkeypatch, 'vessels_replaced', error=KeyboardInterrupt)
    with pytest.raises(KeyboardInterrupt):
        backup_restore.apply(body, sha(body))
    assert fingerprint(data) == before
    no_workdir(data)


def test_exception_is_wrapped_as_backup_rejected(data, monkeypatch):
    populate()
    body = export()
    fault(monkeypatch, 'db_replaced')
    with pytest.raises(backup_check.BackupRejected) as info:
        backup_restore.apply(body, sha(body))
    assert not isinstance(info.value, backup_restore.ConfirmMismatch)
    assert info.value.message.startswith('Khôi phục thất bại; dữ liệu hiện tại đã được giữ nguyên.')
    assert str(data) not in info.value.message


def test_pre_restore_backup_stays_after_failure(data, monkeypatch):
    populate()
    body = export()
    fault(monkeypatch, 'vessels_replaced')
    assert restore(body).status_code == 400
    files = list((data / 'backups').iterdir())
    assert len(files) == 1 and files[0].name.startswith('pre-restore-')
    assert backup_check.check(files[0].read_bytes(), data / 'verify')['counts']['plans'] == 2


def test_failure_in_pre_backup_leaves_no_partial_file(data, monkeypatch):
    populate()
    body = export()
    before = fingerprint(data)

    def broken(handle, *, lock_held=False):
        handle.write(b'dang ghi')
        raise OSError('đầy ổ đĩa')
    monkeypatch.setattr(backup_export, 'write_archive', broken)
    assert restore(body).status_code == 400
    assert fingerprint(data) == before
    assert list((data / 'backups').iterdir()) == []


def test_corrupt_replay_cache_cleared_even_when_rolled_back(data, monkeypatch):
    populate()
    body = export()
    calls = []
    real = plan_binding.clear_replay_cache
    monkeypatch.setattr(plan_binding, 'clear_replay_cache', lambda: (calls.append(1), real())[1])
    fault(monkeypatch, 'cache_cleared')
    assert restore(body).status_code == 400
    assert len(calls) == 2  # once at the step, once after rollback


# ------------------------------------------------------------------ 4. cache freshness
def test_replay_cache_does_not_serve_data_from_before_the_restore(data):
    add_revision(500000)
    body = export()  # 1 revision
    at_export = client.get('/api/cargo-revisions').json()
    for i in range(1, 4):
        add_revision(500000 + i)
    warm = client.get('/api/cargo-revisions').json()
    assert len(warm['revisions']) == 5
    for item in warm['revisions']:
        assert client.get(f"/api/cargo-revisions/{item['revision_id']}").status_code == 200
    assert restore(body).status_code == 200
    after = client.get('/api/cargo-revisions').json()
    assert len(after['revisions']) == 2
    assert after == at_export
    dropped = warm['latest_revision_id']
    assert dropped != after['latest_revision_id']
    assert client.get(f'/api/cargo-revisions/{dropped}').status_code in (400, 404)
    assert client.get(f"/api/cargo-revisions/{after['latest_revision_id']}").status_code == 200


# ------------------------------------------------------------------ 5. concurrency
def test_profile_append_blocks_until_restore_finishes(data, monkeypatch):
    populate()
    body = export()
    entered = threading.Event()
    release = threading.Event()
    real_step = backup_restore._step

    def hook(step):
        real_step(step)
        if step == 'db_replaced':
            entered.set()
            assert release.wait(30)
    monkeypatch.setattr(backup_restore, '_step', hook)
    outcome = {}

    def do_restore():
        try:
            outcome['result'] = backup_restore.apply(body, sha(body))
        except BaseException as exc:  # pragma: no cover - reported by the assertions
            outcome['error'] = exc

    finished = threading.Event()

    def do_append():
        try:
            vstore.append('NEWSHIP', 1, b'{}', b'glb', {})
        except BaseException as exc:  # pragma: no cover
            outcome['append_error'] = exc
        finally:
            finished.set()

    restorer = threading.Thread(target=do_restore)
    restorer.start()
    assert entered.wait(30)
    appender = threading.Thread(target=do_append)
    appender.start()
    assert not finished.wait(0.5), 'append đã chạy khi khôi phục đang giữ khóa'
    release.set()
    restorer.join(30)
    appender.join(30)
    assert finished.is_set() and 'error' not in outcome and 'append_error' not in outcome
    # append ran strictly after the swap: the restored tree plus the new id
    assert sorted(vstore.list_ids()) == sorted([PROFILE_ID, 'NEWSHIP'])


def test_profile_append_blocks_while_pre_restore_backup_is_taken(data, monkeypatch):
    populate()
    body = export()
    entered = threading.Event()
    release = threading.Event()

    def hook(step):
        if step == 'checked':
            entered.set()
            assert release.wait(30)
    monkeypatch.setattr(backup_restore, '_step', hook)
    t = threading.Thread(target=lambda: backup_restore.apply(body, sha(body)))
    t.start()
    assert entered.wait(30)
    finished = threading.Event()

    def append():
        vstore.append('LATE-ONE', 1, b'{}', b'glb', {})
        finished.set()
    a = threading.Thread(target=append)
    a.start()
    assert not finished.wait(0.5)
    release.set()
    t.join(30)
    a.join(30)
    assert finished.is_set()


# ------------------------------------------------------------------ 6. pre-restore backup never overwrites
def test_pre_restore_backup_never_overwrites_existing_file(data, monkeypatch):
    populate()
    body = export()
    frozen = datetime(2026, 11, 5, 1, 2, 3, 456789, tzinfo=timezone.utc)
    monkeypatch.setattr(backup_restore, '_now', lambda: frozen)
    backups = data / 'backups'
    backups.mkdir()
    taken = backups / 'pre-restore-20261105T010203456789Z.scstbak'
    taken.write_bytes('dữ liệu có sẵn'.encode())
    first = restore(body)
    assert first.status_code == 200, first.text
    assert first.json()['pre_restore_backup'] == 'pre-restore-20261105T010203456789Z-1.scstbak'
    second = restore(body)
    assert second.json()['pre_restore_backup'] == 'pre-restore-20261105T010203456789Z-2.scstbak'
    assert taken.read_bytes() == 'dữ liệu có sẵn'.encode()
    assert sorted(p.name for p in backups.iterdir()) == sorted([taken.name, 'pre-restore-20261105T010203456789Z-1.scstbak',
                                                                'pre-restore-20261105T010203456789Z-2.scstbak'])
    for name in ('-1', '-2'):
        content = (backups / f'pre-restore-20261105T010203456789Z{name}.scstbak').read_bytes()
        assert backup_check.check(content, data / f'v{name}')['counts']['plans'] == 2


def test_pre_restore_backup_name_format(data):
    populate()
    body = export()
    name = restore(body).json()['pre_restore_backup']
    stamp = name[len('pre-restore-'):-len('.scstbak')]
    assert len(stamp) == len('20261105T010203456789Z') and stamp.endswith('Z')
    datetime.strptime(stamp, '%Y%m%dT%H%M%S%fZ')
    assert [p.name for p in (data / 'backups').iterdir() if p.name.startswith('.')] == []  # no temp file left


def test_workdir_removed_on_success(data):
    populate()
    assert restore(export()).status_code == 200
    no_workdir(data)
