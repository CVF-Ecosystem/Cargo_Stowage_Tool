"""M5b D1: automatic backups. Data is built through the API (helpers of the M5a restore tests)."""
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters import backup_auto, backup_check, backup_export, backup_restore
from app.main import app
from test_m5a_restore import add_profile, add_revision, fingerprint, populate, rows, save_plan, sha

T0 = datetime(2026, 11, 5, 10, 0, 0, 123456, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    live = tmp_path / 'live'
    live.mkdir()
    monkeypatch.setenv('SCST_DATA_DIR', str(live))
    monkeypatch.delenv('SCST_AUTO_BACKUP', raising=False)
    monkeypatch.setattr(backup_auto, '_state', {'last_error': None})
    return live


def clock(monkeypatch, moment):
    box = {'now': moment}
    monkeypatch.setattr(backup_auto, '_now', lambda: box['now'])
    return box


def tree(root: Path):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob('*'))


def auto_files(data):
    folder = data / 'backups' / 'auto'
    return sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []


def stamp_name(moment, suffix=''):
    return f'auto-{moment.strftime("%Y%m%dT%H%M%S%fZ")}{suffix}.scstbak'


def seed_old(data, count, newest_age_hours=30):
    folder = data / 'backups' / 'auto'
    folder.mkdir(parents=True, exist_ok=True)
    names = []
    for i in range(count):
        name = stamp_name(T0 - timedelta(hours=newest_age_hours + i))
        (folder / name).write_bytes(b'old-%d' % i)
        names.append(name)
    return names


# ------------------------------------------------------------------ due / not due
def test_due_creates_one_valid_file(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(1, 1)
    entry = backup_auto.run_if_due()
    assert entry is not None and backup_auto.NAME_PATTERN.fullmatch(entry['name'])
    assert auto_files(data) == [entry['name']]
    assert entry['created_utc'] == T0.isoformat() and entry['size_bytes'] > 0
    assert backup_auto.list_files() == [entry]
    assert ':' not in entry['name']
    assert backup_auto.last_error() is None


def test_not_due_under_20_hours_then_due_after(data, monkeypatch):
    box = clock(monkeypatch, T0)
    populate(1, 0)
    first = backup_auto.run_if_due()
    box['now'] = T0 + timedelta(hours=19, minutes=59)
    assert backup_auto.run_if_due() is None
    assert auto_files(data) == [first['name']]
    box['now'] = T0 + timedelta(hours=20)
    second = backup_auto.run_if_due()
    assert second is not None and second['name'] != first['name']
    assert [e['name'] for e in backup_auto.list_files()] == [second['name'], first['name']]


def test_vessel_profile_alone_is_data(data, monkeypatch):
    clock(monkeypatch, T0)
    assert not backup_auto.has_data()
    add_profile()
    assert backup_auto.has_data()
    assert backup_auto.run_if_due() is not None


# ------------------------------------------------------------------ no data creates nothing
def test_no_data_creates_nothing(data):
    before = tree(data)
    assert backup_auto.has_data() is False
    assert backup_auto.run_if_due() is None
    with pytest.raises(backup_auto.NoData) as caught:
        backup_auto.run_now()
    assert caught.value.message == 'Chưa có dữ liệu để sao lưu.'
    assert backup_auto.list_files() == []
    backup_auto.start_background()
    assert tree(data) == before == []
    assert not (data / 'backups').exists() and not (data / 'scst.sqlite3').exists()


def test_empty_vessels_lock_file_alone_is_no_data(data):
    (data / 'vessels').mkdir()
    (data / 'vessels' / '.lock').write_bytes(b'')
    before = tree(data)
    assert backup_auto.has_data() is False
    assert backup_auto.run_if_due() is None
    assert tree(data) == before and not (data / 'backups').exists()


def test_existing_empty_database_is_no_data_and_not_modified(data):
    import sqlite3
    from app.adapters import storage
    con = sqlite3.connect(data / 'scst.sqlite3')
    con.execute(storage.SNAPSHOTS_DDL)
    con.commit()
    con.close()
    before = (data / 'scst.sqlite3').read_bytes()
    assert backup_auto.has_data() is False
    assert backup_auto.run_if_due() is None
    assert (data / 'scst.sqlite3').read_bytes() == before and not (data / 'backups').exists()


# ------------------------------------------------------------------ disabled
def test_disabled_by_env_but_run_now_works(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(1, 0)
    monkeypatch.setenv('SCST_AUTO_BACKUP', '0')
    assert backup_auto.enabled() is False
    assert backup_auto.run_if_due() is None
    backup_auto.start_background()
    assert auto_files(data) == []
    entry = backup_auto.run_now()
    assert auto_files(data) == [entry['name']]
    monkeypatch.setenv('SCST_AUTO_BACKUP', '1')
    assert backup_auto.enabled() is True


# ------------------------------------------------------------------ retention
def test_retention_keeps_10_and_deletes_the_oldest(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(1, 0)
    old = seed_old(data, 10)  # old[0] newest ... old[9] oldest
    entry = backup_auto.run_now()
    names = auto_files(data)
    assert len(names) == backup_auto.KEEP == 10
    assert entry['name'] in names
    assert old[9] not in names and set(old[:9]) <= set(names)
    assert [e['name'] for e in backup_auto.list_files()][0] == entry['name']


def test_retention_never_touches_other_files(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(1, 0)
    backups = data / 'backups'
    backups.mkdir()
    others = {
        backups / 'pre-restore-20260101T000000000000Z.scstbak': b'pre',
        backups / 'scst-backup-20260101-000000.scstbak': b'manual',
        backups / 'auto-note.txt': b'x',
    }
    seed_old(data, 12)
    folder = backups / 'auto'
    others.update({
        folder / 'pre-restore-20250101T000000000000Z.scstbak': b'pre2',
        folder / 'scst-backup-20250101-000000.scstbak': b'manual2',
        folder / 'random.bin': b'r',
        folder / 'auto-2020.scstbak': b'bad-pattern',
        folder / 'auto-20200101T000000000000Z.scstbak.bak': b'bad2',
    })
    for path, content in others.items():
        path.write_bytes(content)
    backup_auto.run_now()
    for path, content in others.items():
        assert path.read_bytes() == content
    assert len(backup_auto.list_files()) == 10
    assert all(backup_auto.NAME_PATTERN.fullmatch(e['name']) for e in backup_auto.list_files())


# ------------------------------------------------------------------ failure
def test_failed_new_backup_removes_only_the_new_file(data, monkeypatch):
    box = clock(monkeypatch, T0)
    populate(1, 0)
    old = seed_old(data, 10)
    before = {n: (data / 'backups' / 'auto' / n).read_bytes() for n in old}

    def boom(body, workdir):
        raise backup_check.BackupRejected(f'hỏng {data}')
    real_check = backup_check.check
    monkeypatch.setattr(backup_check, 'check', boom)
    box['now'] = T0 + timedelta(days=3)
    with pytest.raises(backup_auto.AutoBackupFailed) as caught:
        backup_auto.run_now()
    assert str(data) not in caught.value.message
    assert auto_files(data) == sorted(old)  # nothing added, nothing pruned
    assert {n: (data / 'backups' / 'auto' / n).read_bytes() for n in old} == before
    error = backup_auto.last_error()
    assert error and str(data) not in error and '/' not in error and '\\' not in error
    monkeypatch.setattr(backup_check, 'check', real_check)  # a later success clears the error
    backup_auto.run_now()
    assert backup_auto.last_error() is None


def test_run_if_due_swallows_failure_with_fixed_message(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(1, 0)

    def boom(fileobj, **kwargs):
        raise RuntimeError(f'đường dẫn {data}')
    monkeypatch.setattr(backup_export, 'write_archive', boom)
    assert backup_auto.run_if_due() is None
    error = backup_auto.last_error()
    assert error and str(data) not in error
    assert auto_files(data) == []  # temp file removed too


# ------------------------------------------------------------------ no overwrite
def test_never_overwrites_same_timestamp(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(1, 0)
    first = backup_auto.run_now()
    first_bytes = (data / 'backups' / 'auto' / first['name']).read_bytes()
    second = backup_auto.run_now()
    third = backup_auto.run_now()
    assert second['name'] == first['name'].replace('.scstbak', '-1.scstbak')
    assert third['name'] == first['name'].replace('.scstbak', '-2.scstbak')
    assert (data / 'backups' / 'auto' / first['name']).read_bytes() == first_bytes
    assert all(backup_auto.NAME_PATTERN.fullmatch(n) for n in auto_files(data))
    assert backup_auto.list_files()[0]['name'] == third['name']


# ------------------------------------------------------------------ concurrency
def test_two_concurrent_run_if_due_create_one_file(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(1, 0)
    barrier = threading.Barrier(2)
    results = []

    def work():
        barrier.wait()
        results.append(backup_auto.run_if_due())
    threads = [threading.Thread(target=work) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    assert len(auto_files(data)) == 1
    assert sorted(r is None for r in results) == [False, True]


# ------------------------------------------------------------------ startup
def test_startup_survives_injected_faults(data, monkeypatch):
    populate(1, 0)
    def boom(*a, **k):
        raise RuntimeError('tiêm lỗi')
    for target, name in ((backup_auto, 'run_if_due'), (backup_export, 'write_archive'), (backup_auto, 'start_background')):
        with monkeypatch.context() as local:
            local.setattr(target, name, boom)
            with TestClient(app) as test_client:
                assert test_client.get('/api/health').status_code == 200


def test_startup_without_data_creates_nothing(data):
    with TestClient(app) as test_client:
        assert test_client.get('/api/health').status_code == 200
    assert tree(data) == []


# ------------------------------------------------------------------ check + round trip
def test_every_auto_file_passes_check(data, monkeypatch, tmp_path):
    box = clock(monkeypatch, T0)
    populate(2, 2)
    for i in range(3):
        box['now'] = T0 + timedelta(days=i)
        backup_auto.run_now()
    for entry in backup_auto.list_files():
        work = tmp_path / f'check-{entry["name"]}'
        work.mkdir()
        body = (data / 'backups' / 'auto' / entry['name']).read_bytes()
        assert backup_check.check(body, work)['counts']['plans'] == 2


def test_round_trip_restores_byte_identical(data, monkeypatch):
    clock(monkeypatch, T0)
    populate(2, 2)
    snap_rows, rev_rows = rows(data, 'snapshots'), rows(data, 'cargo_revisions')
    vessels = {k: v for k, v in fingerprint(data).items() if k.startswith('vessels')}
    assert any(k.endswith('profile.json') for k in vessels)
    entry = backup_auto.run_now()
    body = (data / 'backups' / 'auto' / entry['name']).read_bytes()
    save_plan('Phương án thêm')
    add_revision(777777)
    add_profile(version=2)
    assert rows(data, 'snapshots') != snap_rows
    backup_restore.apply(body, sha(body))
    assert rows(data, 'snapshots') == snap_rows
    assert rows(data, 'cargo_revisions') == rev_rows
    assert {k: v for k, v in fingerprint(data).items() if k.startswith('vessels')} == vessels
    assert (data / 'backups' / 'auto' / entry['name']).read_bytes() == body  # auto backup survives restore


# ------------------------------------------------------------------ unusual path
def test_data_dir_with_spaces_and_vietnamese(tmp_path, monkeypatch):
    odd = tmp_path / 'thư mục dữ liệu' / 'dữ liệu SCST'
    odd.mkdir(parents=True)
    monkeypatch.setenv('SCST_DATA_DIR', str(odd))
    clock(monkeypatch, T0)
    populate(1, 1)
    entry = backup_auto.run_now()
    assert backup_auto.auto_dir() == odd / 'backups' / 'auto'
    assert (odd / 'backups' / 'auto' / entry['name']).is_file()
    assert backup_auto.list_files() == [entry]
