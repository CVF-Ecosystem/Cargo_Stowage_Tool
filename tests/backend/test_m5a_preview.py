"""M5a D2: restore preview validation. Hostile archives are built here from scratch; a valid source comes from the API."""
import base64
import hashlib
import json
import os
import sqlite3
import stat
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters import backup_check as bc
from app.adapters import storage
from app.domain import cargo_revisions as cr
from app.main import app
from glb_fixture import make_glb

client = TestClient(app)
SOURCE = {'kind': 'FACTORY', 'reference': 'PO-2026-11', 'received_date': '2026-11-02', 'note': 'cân thực tế'}
PROFILE_ID = 'TESTSHIP'
VIETNAMESE = 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------ a valid source built through the API
def _profile():
    corners = [(-5, -2, 0, 0), (5, -2, 10000, 0), (-5, 2, 0, 4000), (5, 2, 10000, 4000)]
    return {
        'contract_version': 'scst.vessel-profile.v1', 'id': PROFILE_ID, 'version': 1, 'name': 'Tàu thử', 'registration': 'T-1',
        'dimensions_m': {'length': 12, 'beam': 6, 'depth': 4},
        'hold': {'id': 'HOLD-T1', 'name': 'Hầm thử', 'length_mm': 10000, 'width_mm': 4000, 'height_mm': 3000, 'status': 'ESTIMATED'},
        'cases': [{'id': 'T-C1', 'cargo_mass_g': 5_000_000_000, 'draft_m': 2.0}],
        'notes': [], 'provenance': {'source_documents': [{'title': 'Tài liệu thử'}],
                                   'field_status': {'dimensions_m': 'ESTIMATED', 'hold': 'ESTIMATED', 'cases': 'ESTIMATED'}},
        'transform': {'translation_m': [0, 0, 0], 'yaw_deg': 0},
        'landmarks': [{'name': f'Góc {i}', 'glb_m': [x, 0, z], 'hold_mm': [hx, hy, 0]} for i, (x, z, hx, hy) in enumerate(corners)]}


@pytest.fixture(scope='module')
def good_parts(tmp_path_factory):
    """{archive name: bytes} of a valid backup content: 2 plans, 2 revisions, 1 vessel profile version."""
    source = tmp_path_factory.mktemp('source')
    patch = pytest.MonkeyPatch()
    patch.setenv('SCST_DATA_DIR', str(source))
    try:
        plan = client.get('/api/demo').json()['plan']
        for name in ('Phương án A', 'Phương án B'):
            r = client.post('/api/snapshots', json={'name': name, 'plan': plan})
            assert r.status_code == 200, r.text
        for mass in (500000, 500001):
            latest = client.get('/api/cargo-revisions').json()['latest_revision_id']
            group = {'bundle_count': 2, 'pieces_per_bundle': 10, 'dimensions_um': [6000000, 300000, 300000], 'mass_g': mass,
                     'outside_diameter_mm': '60.3', 'wall_thickness_mm': '3.91', 'dimension_warning': False}
            r = client.post('/api/cargo-revisions', json={'parent_revision_id': latest, 'source': SOURCE, 'changes': [
                {'type': 'ADD_GROUP', 'confirmation': 'UNVERIFIED', 'group': group}]})
            assert r.status_code == 200, r.text
        glb = make_glb([((-6, 0, -3), (6, 4, 3))])
        r = client.post('/api/vessel-profiles', json={'profile': _profile(), 'glb_base64': base64.b64encode(glb).decode()})
        assert r.status_code == 200, r.text
    finally:
        patch.undo()
    parts = {bc.DATABASE: (source / bc.DATABASE).read_bytes()}
    for path in sorted((source / 'vessels').rglob('*')):
        if path.is_file():
            parts[path.relative_to(source).as_posix()] = path.read_bytes()
    assert sorted(parts) == [bc.DATABASE, f'vessels/{PROFILE_ID}/v1/manifest.json', f'vessels/{PROFILE_ID}/v1/model.glb',
                             f'vessels/{PROFILE_ID}/v1/profile.json']
    return parts


@pytest.fixture
def data(tmp_path, monkeypatch):
    live = tmp_path / 'live'
    live.mkdir()
    monkeypatch.setenv('SCST_DATA_DIR', str(live))
    return live


@pytest.fixture
def parts(good_parts):
    return dict(good_parts)


# ------------------------------------------------------------------ archive builders
def manifest_for(parts, **override):
    files = [{'path': n, 'size': len(b), 'sha256': sha(b)} for n, b in sorted(parts.items()) if n != bc.MANIFEST]
    versions = len({n.rsplit('/', 1)[0] for n in parts if n.startswith('vessels/')})
    value = {'format': bc.FORMAT, 'created_utc': datetime.now(timezone.utc).isoformat(),
             'counts': {'plans': 2, 'revisions': 2, 'vessel_profile_versions': versions}, 'files': files}
    value.update(override)
    return value


def build(parts, manifest=None, *, with_manifest=True, extra=(), compression=zipfile.ZIP_DEFLATED):
    """Zip `parts` (+ a manifest computed from them unless given). `extra` = ZipInfo/bytes pairs appended raw."""
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression) as zf:
        if with_manifest:
            m = manifest if manifest is not None else manifest_for(parts)
            zf.writestr(bc.MANIFEST, m if isinstance(m, bytes) else json.dumps(m, sort_keys=True, ensure_ascii=False))
        for name, data in parts.items():
            zf.writestr(name, data)
        for info, data in extra:
            zf.writestr(info, data)
    return buf.getvalue()


def reject(body, tmp_path, fragment=None):
    import shutil
    work = tmp_path / 'work'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    with pytest.raises(bc.BackupRejected) as caught:
        bc.check(body, work)
    exc = caught.value
    assert exc.message and exc.errors and all(e['field'] and e['message'] for e in exc.errors)
    assert any(c in VIETNAMESE for c in exc.message.lower()) or 'ZIP' in exc.message or 'sha256' in exc.message
    assert str(tmp_path) not in exc.message and str(tmp_path) not in json.dumps(exc.errors)
    if fragment:
        assert fragment in exc.message, exc.message
    return exc


def with_db(parts, mutate):
    """Copy of parts whose SQLite file was altered by mutate(connection)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'x.sqlite3'
        path.write_bytes(parts[bc.DATABASE])
        con = sqlite3.connect(path)
        mutate(con)
        con.commit()
        con.close()
        out = dict(parts)
        out[bc.DATABASE] = path.read_bytes()
    return out


def tree_hash(root: Path):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}


# ------------------------------------------------------------------ accepting case
def test_valid_archive_accepted_and_preview_writes_nothing(parts, data, tmp_path):
    body = build(parts)
    # Live data with content of its own: one plan + the pre-existing vessels dir. It must stay byte-identical.
    plan = client.get('/api/demo').json()['plan']
    assert client.post('/api/snapshots', json={'name': 'Hiện có', 'plan': plan}).status_code == 200
    (data / 'vessels').mkdir()
    before = tree_hash(data)
    entries_before = sorted(p.relative_to(data).as_posix() for p in data.rglob('*'))
    result = bc.preview(body)
    assert tree_hash(data) == before
    assert sorted(p.relative_to(data).as_posix() for p in data.rglob('*')) == entries_before
    assert result['format'] == bc.FORMAT
    assert result['backup_sha256'] == sha(body)
    assert datetime.fromisoformat(result['created_utc']).utcoffset().total_seconds() == 0
    assert result['counts'] == {'plans': 2, 'revisions': 2, 'vessel_profile_versions': 1}
    assert result['current'] == {'plans': 1, 'revisions': 0, 'vessel_profile_versions': 0}
    assert set(result) == {'format', 'created_utc', 'backup_sha256', 'counts', 'current'}


def test_check_leaves_verified_tree_in_workdir(parts, data, tmp_path):
    work = tmp_path / 'w'
    work.mkdir()
    result = bc.check(build(parts), work)
    assert set(result) == {'format', 'created_utc', 'backup_sha256', 'counts'}
    assert (work / bc.DATABASE).read_bytes() == parts[bc.DATABASE]
    assert (work / 'vessels' / PROFILE_ID / 'v1' / 'model.glb').read_bytes() == parts[f'vessels/{PROFILE_ID}/v1/model.glb']
    sqlite3.connect(work / bc.DATABASE).close()
    os.remove(work / bc.DATABASE)  # no connection left open (Windows would refuse)


def test_stored_compression_also_accepted(parts, data):
    assert bc.preview(build(parts, compression=zipfile.ZIP_STORED))['counts']['plans'] == 2


def test_empty_database_archive_accepted(data):
    con = sqlite3.connect(':memory:')
    con.execute(storage.SNAPSHOTS_DDL)
    con.execute(storage.REVISIONS_DDL)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'e.sqlite3'
        disk = sqlite3.connect(path)
        con.backup(disk)
        disk.close()
        con.close()
        raw = path.read_bytes()
    parts = {bc.DATABASE: raw}
    manifest = manifest_for(parts, counts={'plans': 0, 'revisions': 0, 'vessel_profile_versions': 0})
    assert bc.preview(build(parts, manifest))['counts'] == {'plans': 0, 'revisions': 0, 'vessel_profile_versions': 0}


def test_current_counts_never_creates_anything(data):
    assert bc.current_counts() == {'plans': 0, 'revisions': 0, 'vessel_profile_versions': 0}
    assert list(data.iterdir()) == []


def test_preview_does_not_use_live_data_dir(parts, data, monkeypatch, tmp_path):
    import tempfile
    seen = []
    real = tempfile.TemporaryDirectory

    def spy(*a, **k):
        d = real(*a, **k)
        seen.append(Path(d.name))
        return d
    monkeypatch.setattr(bc.tempfile, 'TemporaryDirectory', spy)
    bc.preview(build(parts))
    assert seen and all(data not in p.parents and p != data for p in seen)
    assert not any(p.exists() for p in seen)


# ------------------------------------------------------------------ D2.1
def test_not_a_zip(tmp_path, data):
    reject(b'this is not a zip file at all', tmp_path, 'ZIP')


def test_truncated_zip(parts, tmp_path, data):
    reject(build(parts)[:-30], tmp_path, 'ZIP')


def test_zip_slip_parent_directory(parts, tmp_path, data):
    body = build(parts, extra=[(zipfile.ZipInfo('../evil.txt'), b'x')])
    reject(body, tmp_path, '..')
    assert not (tmp_path / 'evil.txt').exists()


def test_zip_slip_nested_parent_directory(parts, tmp_path, data):
    reject(build(parts, extra=[(zipfile.ZipInfo('vessels/../../evil.txt'), b'x')]), tmp_path, '..')


def test_zip_slip_absolute_path(parts, tmp_path, data):
    reject(build(parts, extra=[(zipfile.ZipInfo('/etc/evil.txt'), b'x')]), tmp_path, 'tuyệt đối')


def test_backslash_path(parts, tmp_path, data):
    reject(build(parts, extra=[(zipfile.ZipInfo('vessels\\TESTSHIP\\v2\\profile.json'), b'x')]), tmp_path, 'gạch ngược')


def test_drive_letter_path(parts, tmp_path, data):
    reject(build(parts, extra=[(zipfile.ZipInfo('C:evil.txt'), b'x')]), tmp_path, 'ổ đĩa')


def test_symlink_entry(parts, tmp_path, data):
    link = zipfile.ZipInfo('vessels/TESTSHIP/v1/model.glb')
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    body = build({k: v for k, v in parts.items() if k != link.filename}, extra=[(link, b'/etc/passwd')])
    reject(body, tmp_path, 'symlink')


def test_duplicate_names(parts, tmp_path, data):
    import io
    import warnings
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(bc.MANIFEST, json.dumps(manifest_for(parts)))
        for name, data_ in parts.items():
            zf.writestr(name, data_)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            zf.writestr(bc.DATABASE, b'second copy')
    reject(buf.getvalue(), tmp_path, 'trùng')


def test_duplicate_names_differing_only_by_case(parts, tmp_path, data):
    reject(build(parts, extra=[(zipfile.ZipInfo('SCST.SQLITE3'), b'x')]), tmp_path)


def test_directory_entry(parts, tmp_path, data):
    reject(build(parts, extra=[(zipfile.ZipInfo('vessels/'), b'')]), tmp_path, 'thư mục')


def test_unlisted_file_in_archive_and_manifest(parts, tmp_path, data):
    parts['notes.txt'] = b'hello'
    reject(build(parts), tmp_path, 'danh sách được phép')


def test_unlisted_vessel_file_name(parts, tmp_path, data):
    parts[f'vessels/{PROFILE_ID}/v1/extra.bin'] = b'x'
    reject(build(parts), tmp_path, 'danh sách được phép')


def test_bad_vessel_id_and_version_dir(parts, tmp_path, data):
    reject(build({**parts, 'vessels/bad id/v1/profile.json': b'x'}), tmp_path, 'danh sách được phép')
    reject(build({**parts, 'vessels/TESTSHIP/v0/profile.json': b'x'}), tmp_path, 'danh sách được phép')
    reject(build({**parts, 'vessels/TESTSHIP/v1/.lock': b'x'}), tmp_path, 'danh sách được phép')


def test_too_many_entries(parts, tmp_path, data, monkeypatch):
    monkeypatch.setattr(bc, 'MAX_ENTRIES', 3)
    reject(build(parts), tmp_path, 'quá nhiều mục')


def test_declared_uncompressed_size_over_limit(parts, tmp_path, data, monkeypatch):
    monkeypatch.setattr(bc, 'MAX_UNCOMPRESSED', 1000)
    reject(build(parts), tmp_path, 'khai báo')


def test_zip_bomb_declared_size(tmp_path, data, monkeypatch):
    parts = {bc.DATABASE: b'\x00' * (4 * 1024 * 1024)}
    body = build(parts)
    assert len(body) < 100 * 1024  # compresses to almost nothing
    monkeypatch.setattr(bc, 'MAX_UNCOMPRESSED', 1024 * 1024)
    reject(body, tmp_path, 'khai báo')


def forge_sizes(body: bytes, new_size: int) -> bytes:
    """Rewrite every uncompressed-size field (local and central headers) so the header lies about the content."""
    data = bytearray(body)
    pos = 0
    while (pos := data.find(b'PK\x03\x04', pos)) != -1:
        struct.pack_into('<I', data, pos + 22, new_size)
        pos += 4
    pos = 0
    while (pos := data.find(b'PK\x01\x02', pos)) != -1:
        struct.pack_into('<I', data, pos + 24, new_size)
        pos += 4
    return bytes(data)


def test_zip_bomb_real_bytes_exceed_lying_header(tmp_path, data, monkeypatch):
    parts = {bc.DATABASE: b'\x00' * (4 * 1024 * 1024)}
    body = forge_sizes(build(parts), 10)
    monkeypatch.setattr(bc, 'MAX_UNCOMPRESSED', 1024 * 1024)
    reject(body, tmp_path)
    # Whatever stage rejects it, no more than the declared size was ever written out.
    extracted = tmp_path / 'work' / bc.DATABASE
    assert not extracted.exists() or extracted.stat().st_size <= 1024 * 1024


def test_real_bytes_counted_across_entries(parts, tmp_path, data, monkeypatch):
    # Every header is honest and each entry is small, but together they pass the (patched) total once counted.
    total = sum(len(v) for v in parts.values())
    monkeypatch.setattr(bc, 'MAX_UNCOMPRESSED', total + 500)
    body = build(parts)  # declared sum = total + manifest size > limit
    reject(body, tmp_path)


def test_body_too_big(parts, tmp_path, data, monkeypatch):
    body = build(parts)
    monkeypatch.setattr(bc, 'MAX_BODY_BYTES', len(body) - 1)
    reject(body, tmp_path, 'vượt giới hạn')
    monkeypatch.setattr(bc, 'MAX_BODY_BYTES', len(body))
    bc.preview(body)  # exactly at the limit is accepted


def test_limit_constants():
    assert bc.MAX_BODY_BYTES == 256 * 1024 * 1024 and bc.MAX_ENTRIES == 20000 and bc.MAX_UNCOMPRESSED == 1024 ** 3


# ------------------------------------------------------------------ D2.2
def test_missing_manifest(parts, tmp_path, data):
    reject(build(parts, with_manifest=False), tmp_path, 'manifest.json')


def test_manifest_not_json(parts, tmp_path, data):
    reject(build(parts, b'{not json'), tmp_path, 'JSON')


def test_manifest_not_object(parts, tmp_path, data):
    reject(build(parts, b'[1, 2]'), tmp_path, 'đối tượng')


def test_wrong_format(parts, tmp_path, data):
    reject(build(parts, manifest_for(parts, format='scst.backup.v2')), tmp_path, 'Định dạng')


def test_manifest_lists_file_not_in_archive(parts, tmp_path, data):
    manifest = manifest_for(parts)
    manifest['files'].append({'path': f'vessels/{PROFILE_ID}/v2/profile.json', 'size': 1, 'sha256': '0' * 64})
    reject(build(parts, manifest), tmp_path, 'không khớp')


def test_archive_has_file_manifest_does_not_list(parts, tmp_path, data):
    manifest = manifest_for(parts)
    manifest['files'] = [f for f in manifest['files'] if f['path'] != f'vessels/{PROFILE_ID}/v1/model.glb']
    reject(build(parts, manifest), tmp_path, 'không khớp')


def test_manifest_lists_file_twice(parts, tmp_path, data):
    manifest = manifest_for(parts)
    manifest['files'].append(dict(manifest['files'][0]))
    reject(build(parts, manifest), tmp_path, 'nhiều lần')


def test_sha256_mismatch(parts, tmp_path, data):
    manifest = manifest_for(parts)
    manifest['files'][0]['sha256'] = '0' * 64
    reject(build(parts, manifest), tmp_path, 'sha256')


def test_sha256_mismatch_when_content_altered_after_manifest(parts, tmp_path, data):
    manifest = manifest_for(parts)
    glb = f'vessels/{PROFILE_ID}/v1/model.glb'
    altered = dict(parts)
    altered[glb] = parts[glb][:-1] + bytes([parts[glb][-1] ^ 1])
    reject(build(altered, manifest), tmp_path, 'sha256')


def test_size_mismatch(parts, tmp_path, data):
    manifest = manifest_for(parts)
    manifest['files'][0]['size'] += 1
    reject(build(parts, manifest), tmp_path, 'Kích thước')


def test_malformed_files_entry(parts, tmp_path, data):
    manifest = manifest_for(parts)
    manifest['files'][0]['size'] = '5'
    reject(build(parts, manifest), tmp_path, 'sai cấu trúc')


def test_counts_mismatch(parts, tmp_path, data):
    reject(build(parts, manifest_for(parts, counts={'plans': 3, 'revisions': 2, 'vessel_profile_versions': 1})), tmp_path, 'Số lượng')
    reject(build(parts, manifest_for(parts, counts={'plans': 2, 'revisions': 1, 'vessel_profile_versions': 1})), tmp_path, 'Số lượng')
    reject(build(parts, manifest_for(parts, counts={'plans': 2, 'revisions': 2, 'vessel_profile_versions': 0})), tmp_path, 'Số lượng')


def test_counts_malformed(parts, tmp_path, data):
    reject(build(parts, manifest_for(parts, counts={'plans': 2, 'revisions': 2})), tmp_path, 'counts')


def test_missing_database(parts, tmp_path, data):
    only_vessels = {k: v for k, v in parts.items() if k != bc.DATABASE}
    reject(build(only_vessels, manifest_for(only_vessels)), tmp_path, 'scst.sqlite3')


def test_bad_created_utc(parts, tmp_path, data):
    reject(build(parts, manifest_for(parts, created_utc='2026-11-02T10:00:00')), tmp_path, 'created_utc')


# ------------------------------------------------------------------ D2.3
def test_corrupt_sqlite(parts, tmp_path, data):
    parts[bc.DATABASE] = b'SQLite format 3\x00' + b'\xff' * 5000
    reject(build(parts), tmp_path, 'Cơ sở dữ liệu')


def test_sqlite_integrity_check_failure(parts, tmp_path, data):
    raw = bytearray(parts[bc.DATABASE])
    page = 4096
    assert len(raw) >= 3 * page
    for i in range(page, len(raw)):  # wreck every page after the schema page
        raw[i] = (raw[i] * 7 + 13) & 0xFF
    parts[bc.DATABASE] = bytes(raw)
    reject(build(parts), tmp_path, 'Cơ sở dữ liệu')


def test_wrong_snapshots_schema(parts, tmp_path, data):
    def mutate(con):
        con.execute('DROP TABLE snapshots')
        con.execute('CREATE TABLE snapshots (id TEXT PRIMARY KEY, name TEXT, plan_json TEXT)')
    reject(build(with_db(parts, mutate)), tmp_path, 'snapshots')


def test_wrong_revisions_schema(parts, tmp_path, data):
    def mutate(con):
        con.execute('DROP TABLE cargo_revisions')
        con.execute('CREATE TABLE cargo_revisions (revision_id TEXT PRIMARY KEY, dataset_id TEXT)')
    reject(build(with_db(parts, mutate)), tmp_path, 'cargo_revisions')


def test_revisions_table_required(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute('DROP TABLE cargo_revisions'))), tmp_path, 'cargo_revisions')


def test_snapshots_table_required(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute('DROP TABLE snapshots'))), tmp_path, 'snapshots')


def test_extra_user_table_rejected(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute('CREATE TABLE secrets (a TEXT)'))), tmp_path, 'secrets')


def test_trigger_and_view_rejected(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute('CREATE VIEW v AS SELECT id FROM snapshots'))), tmp_path)
    reject(build(with_db(parts, lambda con: con.execute(
        'CREATE TRIGGER t AFTER INSERT ON snapshots BEGIN DELETE FROM snapshots; END'))), tmp_path)


# ------------------------------------------------------------------ D2.4
def test_invalid_plan(parts, tmp_path, data):
    def mutate(con):
        plan_id = con.execute('SELECT id FROM snapshots LIMIT 1').fetchone()[0]
        con.execute('UPDATE snapshots SET plan_json=? WHERE id=?', ('{"contract_version": "nope"}', plan_id))
    reject(build(with_db(parts, mutate)), tmp_path, 'Phương án')


def test_plan_json_not_json(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute("UPDATE snapshots SET plan_json='{broken'"))), tmp_path, 'Phương án')


def test_wrong_snapshot_schema_version(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute("UPDATE snapshots SET schema_version='scst.saved-plan.v0'"))), tmp_path, 'phiên bản')


def test_naive_snapshot_timestamp(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute("UPDATE snapshots SET created_utc='2026-11-02T10:00:00'"))), tmp_path, 'thời gian')


def test_non_utc_snapshot_timestamp(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute("UPDATE snapshots SET created_utc='2026-11-02T10:00:00+07:00'"))), tmp_path, 'thời gian')


def test_snapshot_id_not_uuid(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute("UPDATE snapshots SET id='not-a-uuid' WHERE rowid=1"))), tmp_path, 'ID')


def test_broken_revision_chain(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute(
        "UPDATE cargo_revisions SET parent_revision_id='BALTIMORE-PIPE-V1-1@R0007' WHERE sequence=2"))), tmp_path, 'revision')


def test_revision_missing_from_chain(parts, tmp_path, data):
    def mutate(con):
        con.execute('DELETE FROM cargo_revisions WHERE sequence=1')
    reject(build(with_db(parts, mutate)), tmp_path, 'Revision')


def test_revision_content_sha256_mismatch(parts, tmp_path, data):
    exc = reject(build(with_db(parts, lambda con: con.execute(
        "UPDATE cargo_revisions SET content_sha256=? WHERE sequence=2", ('0' * 64,)))), tmp_path)
    assert 'R0002' in exc.message


def test_revision_changes_tampered(parts, tmp_path, data):
    def mutate(con):
        con.execute("UPDATE cargo_revisions SET changes_json='[]' WHERE sequence=1")
    reject(build(with_db(parts, mutate)), tmp_path, 'revision')


def test_revision_json_not_json(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute("UPDATE cargo_revisions SET source_json='{bad' WHERE sequence=1"))), tmp_path, 'JSON')


def test_revision_other_dataset_rejected(parts, tmp_path, data):
    exc = reject(build(with_db(parts, lambda con: con.execute("UPDATE cargo_revisions SET dataset_id='OTHER-DATASET' WHERE sequence=2"))),
                 tmp_path)
    assert 'OTHER-DATASET' in exc.message


def test_revision_sequence_gap_rejected(parts, tmp_path, data):
    reject(build(with_db(parts, lambda con: con.execute("UPDATE cargo_revisions SET sequence=5 WHERE sequence=2"))), tmp_path, 'số thứ tự')


# ------------------------------------------------------------------ D2.5
def vessel_name(leaf):
    return f'vessels/{PROFILE_ID}/v1/{leaf}'


def test_corrupt_vessel_profile_json(parts, tmp_path, data):
    parts[vessel_name('profile.json')] = parts[vessel_name('profile.json')] + b' '
    reject(build(parts), tmp_path, 'sha256')


def test_corrupt_vessel_glb(parts, tmp_path, data):
    glb = parts[vessel_name('model.glb')]
    parts[vessel_name('model.glb')] = glb[:-1] + bytes([glb[-1] ^ 1])
    reject(build(parts), tmp_path, 'model.glb')


def test_vessel_manifest_bad(parts, tmp_path, data):
    parts[vessel_name('manifest.json')] = b'{"schema": "x"}'
    reject(build(parts), tmp_path, 'manifest.json')


def test_vessel_version_missing_a_file(parts, tmp_path, data):
    del parts[vessel_name('model.glb')]
    reject(build(parts, manifest_for(parts)), tmp_path, 'model.glb')


def test_vessel_manifest_missing(parts, tmp_path, data):
    del parts[vessel_name('manifest.json')]
    reject(build(parts, manifest_for(parts)), tmp_path, 'manifest.json')


def test_vessel_profile_consistently_forged_but_invalid(parts, tmp_path, data):
    """profile.json hash matches its manifest, but the profile itself no longer validates (the _load rule)."""
    profile = json.loads(parts[vessel_name('profile.json')])
    profile['hold']['length_mm'] = -1
    raw = json.dumps(profile, sort_keys=True, ensure_ascii=False).encode()
    manifest = json.loads(parts[vessel_name('manifest.json')])
    manifest['profile_sha256'] = sha(raw)
    parts[vessel_name('profile.json')] = raw
    parts[vessel_name('manifest.json')] = json.dumps(manifest, sort_keys=True).encode()
    reject(build(parts), tmp_path, 'profile.json')


def test_vessel_profile_wrong_id_rejected(parts, tmp_path, data):
    renamed = {}
    for name, value in parts.items():
        renamed[name.replace(PROFILE_ID, 'OTHERSHIP')] = value
    reject(build(renamed), tmp_path, 'manifest.json')


# ------------------------------------------------------------------ read-only API guarantees
def test_rejection_writes_nothing_to_live_data(parts, data, tmp_path):
    plan = client.get('/api/demo').json()['plan']
    assert client.post('/api/snapshots', json={'name': 'Hiện có', 'plan': plan}).status_code == 200
    before = tree_hash(data)
    for body in (b'junk', build(parts, with_manifest=False), build(with_db(parts, lambda c: c.execute('DROP TABLE snapshots')))):
        with pytest.raises(bc.BackupRejected):
            bc.preview(body)
    assert tree_hash(data) == before


def test_preview_leaves_live_sqlite_untouched_when_missing(parts, data):
    assert not (data / bc.DATABASE).exists()
    bc.preview(build(parts))
    assert list(data.iterdir()) == []


def test_current_counts_reads_live_data(data):
    plan = client.get('/api/demo').json()['plan']
    client.post('/api/snapshots', json={'name': 'A', 'plan': plan})
    client.post('/api/snapshots', json={'name': 'B', 'plan': plan})
    assert bc.current_counts() == {'plans': 2, 'revisions': 0, 'vessel_profile_versions': 0}
    before = tree_hash(data)
    bc.current_counts()
    assert tree_hash(data) == before


def test_vessel_store_read_accepts_alternative_base(parts, tmp_path, data):
    """Additive `base` keyword of vessel_profile_store.read; default behaviour is the live data dir."""
    from app.adapters import vessel_profile_store as store
    work = tmp_path / 'w'
    bc.check(build(parts), work)
    got = store.read(PROFILE_ID, 1, base=work / 'vessels')
    assert got['profile_bytes'] == parts[vessel_name('profile.json')]
    with pytest.raises(LookupError):
        store.read(PROFILE_ID, 1)  # live data dir has no such profile
