"""M5a D1 backup export: archive layout, manifest, row and byte equality, exclusions and consistency.

Every test uses a temporary SCST_DATA_DIR; no runtime data is touched. Archive databases are extracted outside it.
"""
import contextlib
import hashlib
import io
import json
import re
import sqlite3
import threading
import time
import zipfile
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.adapters import backup_export
from app.adapters import storage
from app.adapters import vessel_profile_store as store

VER = {'result': 'PASS', 'tolerance_mm': 1}
NAME_PATTERN = re.compile(r'^scst-backup-\d{8}-\d{6}\.scstbak$')
ALLOWED = re.compile(r'^(manifest\.json|scst\.sqlite3|vessels/[A-Z0-9][A-Z0-9-]{1,31}/v[1-9][0-9]{0,8}/(profile\.json|model\.glb|manifest\.json))$')
REVISION_SQL = ('INSERT INTO cargo_revisions (revision_id,dataset_id,sequence,parent_revision_id,created_utc,'
                'source_json,changes_json,content_sha256) VALUES (?,?,?,?,?,?,?,?)')
SNAPSHOT_SQL = 'INSERT INTO snapshots (id,name,created_utc,schema_version,plan_json) VALUES (?,?,?,?,?)'


@pytest.fixture
def data(tmp_path, monkeypatch):
    root = tmp_path / 'data'
    root.mkdir()
    monkeypatch.setenv('SCST_DATA_DIR', str(root))
    return root


@pytest.fixture
def out(tmp_path):
    path = tmp_path / 'out'
    path.mkdir()
    return path


def seed_db(plans=3, revisions=2):
    with storage.connection() as db:
        for i in range(plans):
            db.execute(SNAPSHOT_SQL, (str(uuid4()), f'P{i}', f'2026-11-0{i + 1}T08:00:00+00:00',
                                      'scst.saved-plan.v1', f'{{"i":{i}}}'))
        for i in range(revisions):
            db.execute(REVISION_SQL, (f'rev-{i}', 'DS', i + 1, f'rev-{i - 1}' if i else 'BASE',
                                      '2026-11-02T08:00:00+00:00', '{"s":1}', '[]', 'ab' * 32))


def seed_vessels():
    store.append('TAU-A', 1, b'{"p":1}', b'glb-A1', VER)
    store.append('TAU-A', 2, b'{"p":2}\xff\x00', b'glb-A2' * 100, VER)
    store.append('TAU-B', 1, b'profile-b', b'\x00\x01\x02', VER)


def archive():
    buffer = io.BytesIO()
    manifest = backup_export.write_archive(buffer)
    return buffer.getvalue(), manifest


def members(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        return {info.filename: zf.read(info.filename) for info in zf.infolist()}


def archive_db(raw, out):
    path = out / 'archive.sqlite3'
    path.write_bytes(members(raw)['scst.sqlite3'])
    return path


def rows(path, table):
    with contextlib.closing(sqlite3.connect(path)) as db:
        return db.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall()


def schema(path):
    with contextlib.closing(sqlite3.connect(path)) as db:
        return db.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()


def count_snapshots(data):
    with contextlib.closing(sqlite3.connect(data / 'scst.sqlite3', timeout=5)) as db:
        return db.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0]


def test_manifest_matches_archive(data):
    seed_db()
    seed_vessels()
    raw, returned = archive()
    entries = members(raw)
    manifest = json.loads(entries['manifest.json'].decode('utf-8'))
    assert manifest == returned
    assert manifest['format'] == 'scst.backup.v1'
    created = datetime.fromisoformat(manifest['created_utc'])
    assert created.utcoffset() == timezone.utc.utcoffset(created)
    assert manifest['counts'] == {'plans': 3, 'revisions': 2, 'vessel_profile_versions': 3}
    listed = manifest['files']
    assert [f['path'] for f in listed] == sorted(f['path'] for f in listed)
    assert {f['path'] for f in listed} == set(entries) - {'manifest.json'}
    for item in listed:
        assert set(item) == {'path', 'size', 'sha256'}
        content = entries[item['path']]
        assert item['size'] == len(content)
        assert item['sha256'] == hashlib.sha256(content).hexdigest()


def test_archive_is_valid_zip_with_allow_listed_names(data):
    seed_db()
    seed_vessels()
    raw, _ = archive()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        assert zf.testzip() is None
        names = [info.filename for info in zf.infolist()]
    assert all(ALLOWED.fullmatch(name) for name in names), names
    assert all(not name.startswith('/') and '\\' not in name and '..' not in name.split('/') for name in names)


def test_no_absolute_paths_in_manifest(data):
    seed_db()
    seed_vessels()
    raw, _ = archive()
    manifest_text = members(raw)['manifest.json'].decode('utf-8')
    assert str(data) not in manifest_text
    assert str(data.parent) not in manifest_text


def test_db_rows_equal_source(data, out):
    seed_db()
    raw, _ = archive()
    path = archive_db(raw, out)
    assert rows(path, 'snapshots') == rows(data / 'scst.sqlite3', 'snapshots')
    assert rows(path, 'cargo_revisions') == rows(data / 'scst.sqlite3', 'cargo_revisions')
    assert len(rows(path, 'cargo_revisions')) == 2
    assert schema(path) == schema(data / 'scst.sqlite3')


def test_vessel_files_byte_identical(data):
    seed_vessels()
    raw, _ = archive()
    base = data / 'vessels'
    on_disk = {f'vessels/{p.relative_to(base).as_posix()}': p.read_bytes()
               for p in base.rglob('*') if p.is_file() and p.relative_to(base).as_posix() != '.lock'}  # Windows lock file
    in_archive = {name: content for name, content in members(raw).items() if name.startswith('vessels/')}
    assert len(on_disk) == 9
    assert in_archive == on_disk


def test_temp_lock_and_bak_files_excluded(data):
    seed_db()
    seed_vessels()
    (data / 'scst.sqlite3.pre-sup02a.bak').write_bytes(b'old')
    (data / 'scst.sqlite3.pre-sup02a.bak.tmp').write_bytes(b'old')
    base = data / 'vessels'
    (base / '.lock').write_bytes(b'')
    stray = base / 'TAU-A' / '.tmp-abc'
    stray.mkdir()
    (stray / 'profile.json').write_bytes(b'x')
    partial = base / 'TAU-A' / 'v3'
    partial.mkdir()
    (partial / 'profile.json').write_bytes(b'partial')  # no manifest.json: not a listed version
    raw, manifest = archive()
    names = list(members(raw))
    assert not any(marker in name for name in names for marker in ('.tmp', '.lock', '.bak', 'v3/'))
    assert manifest['counts']['vessel_profile_versions'] == 3


@pytest.mark.parametrize('present', [True, False])
def test_empty_data_dir_exports_valid_empty_archive(data, out, present):
    if not present:
        data.rmdir()
    raw, manifest = archive()
    assert manifest['counts'] == {'plans': 0, 'revisions': 0, 'vessel_profile_versions': 0}
    assert [f['path'] for f in manifest['files']] == ['scst.sqlite3']
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        assert zf.testzip() is None
    path = archive_db(raw, out)
    assert [name for name, _ in schema(path)] == ['cargo_revisions', 'snapshots']
    assert rows(path, 'snapshots') == []
    assert rows(path, 'cargo_revisions') == []
    if present:
        assert list(data.iterdir()) == []
    else:
        assert not data.exists()


def test_missing_revisions_table_added_only_in_copy(data, out):
    with contextlib.closing(sqlite3.connect(data / 'scst.sqlite3')) as db:
        db.execute(storage.SNAPSHOTS_DDL)
        db.execute("INSERT INTO snapshots VALUES ('a','n','2026-11-01T00:00:00+00:00','scst.saved-plan.v1','{}')")
        db.commit()
    before = (data / 'scst.sqlite3').read_bytes()
    raw, manifest = archive()
    assert (data / 'scst.sqlite3').read_bytes() == before
    assert manifest['counts'] == {'plans': 1, 'revisions': 0, 'vessel_profile_versions': 0}
    path = archive_db(raw, out)
    assert [name for name, _ in schema(path)] == ['cargo_revisions', 'snapshots']


def test_unsupported_schema_is_rejected_and_source_untouched(data):
    with contextlib.closing(sqlite3.connect(data / 'scst.sqlite3')) as db:
        db.execute('CREATE TABLE snapshots (id TEXT PRIMARY KEY)')
        db.commit()
    before = (data / 'scst.sqlite3').read_bytes()
    with pytest.raises(ValueError, match='Cấu trúc cơ sở dữ liệu'):
        archive()
    assert (data / 'scst.sqlite3').read_bytes() == before


def test_export_bytes_filename_and_archive(data):
    seed_db(plans=1, revisions=0)
    raw, name = backup_export.export_bytes()
    assert NAME_PATTERN.fullmatch(name), name
    stamp = name[len('scst-backup-'):-len('.scstbak')]
    parsed = datetime.strptime(stamp, '%Y%m%d-%H%M%S')
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs((now - parsed).total_seconds()) < 300
    assert zipfile.is_zipfile(io.BytesIO(raw))


def test_lock_held_true_does_not_reacquire(data):
    seed_vessels()
    buffer = io.BytesIO()
    with store._LOCK:
        with store._process_lock(store.data_dir()):
            manifest = backup_export.write_archive(buffer, lock_held=True)
    assert manifest['counts']['vessel_profile_versions'] == 3
    assert len(members(buffer.getvalue())) == 11  # scst.sqlite3 + 9 vessel files + manifest.json


def test_consistent_under_concurrent_writer(data, out):
    seed_db(plans=5, revisions=0)
    stop = threading.Event()
    errors = []

    def writer():
        index = 0
        try:
            while not stop.is_set() and index < 5000:
                with storage.connection() as db:
                    db.execute(SNAPSHOT_SQL, (str(uuid4()), f'W{index}', '2026-11-03T00:00:00+00:00',
                                              'scst.saved-plan.v1', '{}'))
                index += 1
        except BaseException as exc:  # reported by the test below
            errors.append(exc)

    before = count_snapshots(data)
    thread = threading.Thread(target=writer)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while count_snapshots(data) == before and time.monotonic() < deadline:
            time.sleep(0.005)
        raw, manifest = archive()
    finally:
        stop.set()
        thread.join(timeout=60)
    after = count_snapshots(data)
    assert not thread.is_alive()
    assert errors == []
    path = archive_db(raw, out)
    with contextlib.closing(sqlite3.connect(path)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    archived = len(rows(path, 'snapshots'))
    assert before < archived <= after
    assert manifest['counts']['plans'] == archived
