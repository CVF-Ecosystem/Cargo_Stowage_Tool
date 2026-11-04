import sqlite3
import pytest
from app.adapters import revision_store, storage

DS = 'BALTIMORE-PIPE-V1-1'
BAK = 'scst.sqlite3.pre-sup02a.bak'
LEGACY_DDL = 'CREATE TABLE snapshots (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_utc TEXT NOT NULL, schema_version TEXT NOT NULL, plan_json TEXT NOT NULL)'
ROW = ('11111111-1111-4111-8111-111111111111', 'Legacy', '2026-01-01T00:00:00+00:00', 'scst.saved-plan.v1', '{"legacy":true}')


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def legacy_db(directory):
    path = directory / 'scst.sqlite3'
    db = sqlite3.connect(path)
    db.execute(LEGACY_DDL)
    db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)', ROW)
    db.commit()
    db.close()
    return path


def tables(path):
    db = sqlite3.connect(path)
    try:
        return sorted(r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
    finally:
        db.close()


def snapshot_rows(path):
    db = sqlite3.connect(path)
    try:
        return db.execute('SELECT * FROM snapshots ORDER BY id').fetchall()
    finally:
        db.close()


def row(seq, parent, sha='a' * 64):
    return {'revision_id': f'{DS}@R{seq:04d}', 'sequence': seq, 'created_utc': '2026-02-01T00:00:00+00:00',
            'source': {'kind': 'USER', 'reference': 'r', 'received_date': '2026-02-01', 'note': ''},
            'changes': [{'type': 'UPDATE_GROUP', 'group_id': 'x', 'confirmation': 'CONFIRMED', 'set': {'mass_g': 1}}],
            'content_sha256': sha}


def test_legacy_db_backed_up_once_and_snapshot_bytes_kept(data):
    path = legacy_db(data)
    with storage.connection() as db:
        db.execute('SELECT 1')
    bak = data / BAK
    assert bak.exists()
    assert tables(bak) == ['snapshots'] and snapshot_rows(bak) == [ROW]
    assert tables(path) == ['cargo_revisions', 'snapshots'] and snapshot_rows(path) == [ROW]
    # second open must not rewrite the backup, even when it was modified externally
    b = sqlite3.connect(bak)
    b.execute("UPDATE snapshots SET name='edited'")
    b.commit()
    b.close()
    before, mtime = bak.read_bytes(), bak.stat().st_mtime_ns
    storage.listing()
    storage.listing()
    assert bak.read_bytes() == before and bak.stat().st_mtime_ns == mtime
    assert not (data / (BAK + '.tmp')).exists()


def test_backup_never_overwritten_after_undo_and_remigration(data):
    path = legacy_db(data)
    storage.listing()
    (data / BAK).write_bytes(b'user kept this')
    db = sqlite3.connect(path)
    db.execute('DROP TABLE cargo_revisions')
    db.commit()
    db.close()
    storage.listing()
    assert (data / BAK).read_bytes() == b'user kept this'
    assert 'cargo_revisions' in tables(path)


def test_fresh_directory_creates_both_tables_without_backup(data):
    storage.listing()
    assert tables(data / 'scst.sqlite3') == ['cargo_revisions', 'snapshots']
    assert not (data / BAK).exists()


@pytest.mark.parametrize('ddl', [
    'CREATE TABLE cargo_revisions (revision_id TEXT PRIMARY KEY, extra TEXT)',
    'CREATE TABLE cargo_revisions (revision_id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, sequence TEXT NOT NULL, parent_revision_id TEXT NOT NULL, created_utc TEXT NOT NULL, source_json TEXT NOT NULL, changes_json TEXT NOT NULL, content_sha256 TEXT NOT NULL)',
])
def test_malformed_revision_table_rejected_and_untouched(data, ddl):
    path = legacy_db(data)
    db = sqlite3.connect(path)
    db.execute(ddl)
    cols = [r[1] for r in db.execute('PRAGMA table_info(cargo_revisions)')]
    db.execute('INSERT INTO cargo_revisions (%s) VALUES (%s)' % (','.join(cols), ','.join('?' * len(cols))), ['keep'] * len(cols))
    db.commit()
    db.close()
    before = path.read_bytes()
    with pytest.raises(ValueError, match='revision dữ liệu hàng'):
        storage.listing()
    with pytest.raises(ValueError, match='revision dữ liệu hàng'):
        revision_store.read_records(DS)
    with pytest.raises(ValueError):
        revision_store.append(DS, revision_store.BASE_REVISION_ID, lambda rec: row(1, None))
    assert path.read_bytes() == before
    assert snapshot_rows(path) == [ROW] and not (data / BAK).exists()


def test_unknown_snapshots_structure_still_rejected_without_backup(data):
    path = data / 'scst.sqlite3'
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE snapshots (id TEXT, other TEXT)')
    db.commit()
    db.close()
    before = path.read_bytes()
    with pytest.raises(ValueError, match='Cấu trúc cơ sở dữ liệu không được hỗ trợ'):
        storage.listing()
    assert path.read_bytes() == before and not (data / BAK).exists()


def test_append_read_and_latest(data):
    assert revision_store.read_records(DS) == []
    assert revision_store.latest_revision_id(DS) == revision_store.BASE_REVISION_ID
    out = revision_store.append(DS, revision_store.BASE_REVISION_ID, lambda rec: row(len(rec) + 1, None))
    assert out['revision_id'] == f'{DS}@R0001' and out['parent_revision_id'] == revision_store.BASE_REVISION_ID
    revision_store.append(DS, f'{DS}@R0001', lambda rec: row(len(rec) + 1, None))
    records = revision_store.read_records(DS)
    assert [r['revision_id'] for r in records] == [f'{DS}@R0001', f'{DS}@R0002']
    assert records[1]['parent_revision_id'] == f'{DS}@R0001'
    assert records[0]['source']['kind'] == 'USER' and records[0]['changes'][0]['set'] == {'mass_g': 1}
    assert revision_store.latest_revision_id(DS) == f'{DS}@R0002'


def test_parent_mismatch_writes_nothing_and_build_not_called(data):
    revision_store.append(DS, revision_store.BASE_REVISION_ID, lambda rec: row(1, None))
    called = []
    with pytest.raises(revision_store.ParentMismatch) as e:
        revision_store.append(DS, revision_store.BASE_REVISION_ID, lambda rec: called.append(1) or row(2, None))
    assert e.value.latest == f'{DS}@R0001' and not called
    assert len(revision_store.read_records(DS)) == 1


def test_build_failure_aborts_and_writes_nothing(data):
    def boom(records):
        raise RuntimeError('abort')
    with pytest.raises(RuntimeError):
        revision_store.append(DS, revision_store.BASE_REVISION_ID, boom)
    assert revision_store.read_records(DS) == []
    revision_store.append(DS, revision_store.BASE_REVISION_ID, lambda rec: row(1, None))
    assert len(revision_store.read_records(DS)) == 1


def test_sequence_is_unique_and_failed_insert_rolls_back(data):
    revision_store.append(DS, revision_store.BASE_REVISION_ID, lambda rec: row(1, None))
    dup = row(1, None)
    dup['revision_id'] = f'{DS}@R0009'
    with pytest.raises(sqlite3.IntegrityError):
        revision_store.append(DS, f'{DS}@R0001', lambda rec: dup)
    records = revision_store.read_records(DS)
    assert [r['revision_id'] for r in records] == [f'{DS}@R0001']
    revision_store.append(DS, f'{DS}@R0001', lambda rec: row(2, None))
    assert len(revision_store.read_records(DS)) == 2


def test_store_has_no_mutation_api():
    public = {n for n in dir(revision_store) if not n.startswith('_') and callable(getattr(revision_store, n))}
    assert not {n for n in public if n.startswith(('update', 'delete', 'remove', 'drop'))}


def test_dropping_revision_table_leaves_snapshots_listed(data):
    path = legacy_db(data)
    revision_store.append(DS, revision_store.BASE_REVISION_ID, lambda rec: row(1, None))
    db = sqlite3.connect(path)
    db.execute('DROP TABLE cargo_revisions')
    db.commit()
    db.close()
    assert snapshot_rows(path) == [ROW]
    items = storage.listing()
    assert [i.id for i in items] == [ROW[0]]
    assert revision_store.read_records(DS) == []
