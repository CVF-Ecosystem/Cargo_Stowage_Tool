"""SUP-03 API acceptance (S3-03 and the API parts of S3-02). Every test uses a temporary SCST_DATA_DIR; no runtime data is touched."""
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.pipe_registry import PATH as BALTIMORE_PATH, REGISTRY
from app.domain import cargo_revisions as cr
from app.main import app

client = TestClient(app)
R0 = cr.BASE_REVISION_ID
R1, R2, R5 = cr.revision_id(1), cr.revision_id(2), cr.revision_id(5)
# Golden R0000 content hash, as pinned in tests/backend/test_cargo_revisions_domain.py (BASE_SHA).
BASE_SHA = '9392efc3fd93d9b56e2bfddb2cf45c73d04755d7fe1003092b09fca5250449a4'
VIETNAMESE = re.compile('[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.I)
G2, G5 = 'Sheet1-R002', 'Sheet1-R005'
WARNED_GROUP = 'Sheet1-R022'
ENVELOPE_AT_R0 = [WARNED_GROUP, 'Sheet1-R031', 'Sheet1-R032']
SOURCE = {'kind': 'FACTORY', 'reference': 'PO-2026-11 / chứng từ nhà máy', 'received_date': '2026-11-02', 'note': 'cân thực tế'}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope='module', autouse=True)
def source_data_unchanged():
    before = sha(BALTIMORE_PATH)
    yield
    assert sha(BALTIMORE_PATH) == before


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


# ------------------------------------------------------------------ helpers
def store_state(data):
    """None when no database file exists; otherwise every table's rows in rowid order (read-only)."""
    path = data / 'scst.sqlite3'
    if not path.exists():
        return None
    con = sqlite3.connect(path)
    try:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {t: con.execute(f'SELECT * FROM "{t}" ORDER BY rowid').fetchall() for t in tables}
    finally:
        con.close()


def stored_plan_json(data, snapshot_id):
    con = sqlite3.connect(data / 'scst.sqlite3')
    try:
        return con.execute('SELECT plan_json FROM snapshots WHERE id=?', (snapshot_id,)).fetchone()[0]
    finally:
        con.close()


def latest_id():
    return client.get('/api/cargo-revisions').json()['latest_revision_id']


def draft(changes, source=None, parent=None):
    return {'parent_revision_id': parent or latest_id(), 'source': source or SOURCE, 'changes': changes}


def update(group, confirmation='CONFIRMED', **fields):
    return {'type': 'UPDATE_GROUP', 'group_id': group, 'confirmation': confirmation, 'set': fields}


def create(changes, **kw):
    r = client.post('/api/cargo-revisions', json=draft(changes, **kw))
    assert r.status_code == 200, r.text
    return r.json()


def base_plan():
    return client.get('/api/demo').json()['plan']


def roomy(plan):
    plan['hold'].update(length_mm=20000, width_mm=9000, height_mm=4000)
    plan['limits'].update(certificate_cargo_limit_g=10 ** 10, voyage_cargo_limit_g=10 ** 10, cargo_onboard_g=0)
    return plan


def v2_plan(revision):
    r = client.post(f'/api/cargo-revisions/{revision}/plan-preview', json=roomy(base_plan()))
    assert r.status_code == 200, r.text
    return r.json()['plan']


def place(plan, *pairs):
    plan['placements'] = [dict(unit_id=u, x_mm=0, y_mm=y, z_mm=0, layer=0, supported_by=[], yaw_deg=0) for u, y in pairs]
    return plan


def save(plan, name='Phương án thử'):
    r = client.post('/api/snapshots', json={'name': name, 'plan': plan})
    assert r.status_code == 200, r.text
    return r.json()['id']


def packing_response(revision):
    r = client.get(f'/api/cargo-revisions/{revision}/packing')
    assert r.status_code == 200, r.text
    return r


def packing(revision):
    return packing_response(revision).json()


def group(pk, group_id):
    return next(g for g in pk['groups'] if g['group_id'] == group_id)


def other_groups(pk, group_id):
    return [g for g in pk['groups'] if g['group_id'] != group_id]


def codes(g):
    return [r['code'] for r in g['reasons']]


def keys_of(v):
    if isinstance(v, dict):
        return set(v).union(*(keys_of(x) for x in v.values()))
    if isinstance(v, list):
        return set().union(*(keys_of(x) for x in v))
    return set()


# ------------------------------------------------------------------ S3-03 / S3-02: R0000 packing
def test_r0000_packing_totals_and_status_counts():
    pk = packing(R0)
    assert pk['dataset_id'] == cr.DATASET and pk['revision_id'] == R0 and pk['basis'] == 'DERIVED'
    assert pk['content_sha256'] == BASE_SHA
    stats = pk['stats']
    assert len(pk['groups']) == stats['group_count'] == 31
    assert stats['bundle_count'] == 1076 and stats['source_pieces'] == 21226
    assert stats['groups_by_status']['DETAILED'] + stats['groups_by_status']['ENVELOPE_ONLY'] == 31
    assert stats['groups_by_status'] == {'DETAILED': 28, 'ENVELOPE_ONLY': 3}
    assert sorted(g['group_id'] for g in pk['groups'] if g['status'] == 'ENVELOPE_ONLY') == sorted(ENVELOPE_AT_R0)
    # derived pieces = placed pieces x bundles per group (R0000 has no bundle overrides)
    assert stats['derived_pieces'] == sum(g['pieces_placed'] * g['bundle_count'] for g in pk['groups'])
    # every source piece is either derived or belongs to an ENVELOPE_ONLY group
    envelope_source = sum(g['pieces_source'] * g['bundle_count'] for g in pk['groups'] if g['status'] == 'ENVELOPE_ONLY')
    assert stats['source_pieces'] - stats['derived_pieces'] == envelope_source
    assert stats['bundles_by_status']['DETAILED'] + stats['bundles_by_status']['ENVELOPE_ONLY'] == 1076


def test_packing_numbers_are_exact_integers_and_centres_fit_their_section():
    pk = packing(R0)

    def no_floats(v):
        assert type(v) is not float, v
        if isinstance(v, dict):
            for x in v.values():
                no_floats(x)
        elif isinstance(v, list):
            for x in v:
                no_floats(x)

    no_floats(pk)
    for g in pk['groups']:
        for centre in g['pipe_centres_um']:
            assert len(centre) == 2 and all(type(v) is int for v in centre), (g['group_id'], centre)
        if g['status'] == 'DETAILED':
            assert len(g['pipe_centres_um']) == g['pieces_placed'] == g['pieces_source']
            w, h = g['section_um'][0], g['section_um'][1]
            od = g['od_um']
            for y, z in g['pipe_centres_um']:
                assert 2 * y - od >= 0 and 2 * y + od <= 2 * w and 2 * z - od >= 0 and 2 * z + od <= 2 * h, g['group_id']
        else:
            assert g['pipe_centres_um'] == [] and g['pieces_placed'] == 0


# ------------------------------------------------------------------ S3-03: read-only
def test_packing_is_read_only_and_writes_no_rows(data):
    assert store_state(data) is None
    packing(R0)
    assert store_state(data) is None or all(not rows for t, rows in store_state(data).items()
                                             if t in ('cargo_revisions', 'snapshots'))
    create([update(G2, mass_g=900000)])
    before = store_state(data)
    assert len(before['cargo_revisions']) == 1 and before.get('snapshots', []) == []
    packing(R0)
    packing(R1)
    assert store_state(data) == before


@pytest.mark.parametrize('revision_id', [R5, 'nonsense', cr.DATASET + '@R00X'], ids=['unknown', 'malformed', 'malformed-suffix'])
def test_unknown_or_malformed_revision_returns_404(revision_id):
    r = client.get(f'/api/cargo-revisions/{revision_id}/packing')
    assert r.status_code == 404, r.text


def test_integrity_failure_is_refused_like_sup02a(data):
    create([update(G2, mass_g=900000)])
    con = sqlite3.connect(data / 'scst.sqlite3')
    con.execute('UPDATE cargo_revisions SET content_sha256=? WHERE revision_id=?', ('0' * 64, R1))
    con.commit()
    con.close()
    bad = client.get(f'/api/cargo-revisions/{R1}/packing')
    assert bad.status_code == 400
    detail = bad.json()['detail']
    assert set(detail) == {'message', 'errors'} and detail['errors'] == []
    assert isinstance(detail['message'], str) and VIETNAMESE.search(detail['message'])
    assert detail == client.get(f'/api/cargo-revisions/{R1}').json()['detail']
    # the intact base revision is still served
    assert packing(R0)['content_sha256'] == BASE_SHA


# ------------------------------------------------------------------ S3-03: byte regression
def test_r0000_hash_and_revision_bytes_unchanged_by_packing():
    assert cr.content_sha256(cr.base_groups(REGISTRY)) == BASE_SHA
    rev_before = client.get(f'/api/cargo-revisions/{R0}')
    assert rev_before.status_code == 200 and rev_before.json()['content_sha256'] == BASE_SHA
    first = packing_response(R0)
    assert first.json()['content_sha256'] == rev_before.json()['content_sha256'] == BASE_SHA
    assert packing_response(R0).content == first.content
    assert client.get(f'/api/cargo-revisions/{R0}').content == rev_before.content


def test_v2_snapshot_bytes_unchanged_by_packing(data):
    sid = save(place(v2_plan(R0), ('PIPE-R004-B0001', 0)), 'pinned R0')
    raw_before = stored_plan_json(data, sid)
    snap_before = client.get('/api/snapshots/' + sid)
    rev_before = client.get(f'/api/cargo-revisions/{R0}').content
    packing_response(R0)
    assert stored_plan_json(data, sid) == raw_before
    assert client.get('/api/snapshots/' + sid).content == snap_before.content
    assert client.get(f'/api/cargo-revisions/{R0}').content == rev_before
    stored = json.loads(raw_before)
    assert stored['contract_version'] == 'scst.pipe-list.v2' and stored['cargo_revision']['revision_id'] == R0
    assert 'packing' not in keys_of(stored) and 'pipe_centres_um' not in keys_of(stored)
    assert 'pipe_centres_um' not in raw_before and '"packing"' not in raw_before
    assert 'packing' not in keys_of(snap_before.json()) and 'pipe_centres_um' not in keys_of(snap_before.json())


# ------------------------------------------------------------------ S3-03: revision changes reach packing
def test_od_edit_changes_only_that_group_and_leaves_r0000_untouched():
    r0_before = packing_response(R0).content
    create([update(G5, confirmation='UNVERIFIED', outside_diameter_mm='120')])
    assert packing_response(R0).content == r0_before
    pk0, pk1 = packing(R0), packing(R1)
    assert pk1['revision_id'] == R1 and pk1['content_sha256'] != BASE_SHA
    g0, g1 = group(pk0, G5), group(pk1, G5)
    assert g0['od_um'] == 60300 and g1['od_um'] == 120000
    # 26 pipes of 120 mm do not fit the 361.8 mm square: RECT holds 3 x 3 = 9, HEX holds 8
    assert g1['status'] == 'ENVELOPE_ONLY' and codes(g1) == ['PIECES_DO_NOT_FIT'] and g1['max_fit'] == 9
    assert other_groups(pk1, G5) == other_groups(pk0, G5)
    s0, s1 = pk0['stats'], pk1['stats']
    assert s1['groups_by_status'] == {'DETAILED': 27, 'ENVELOPE_ONLY': 4}
    assert s1['bundle_count'] == s0['bundle_count'] and s1['source_pieces'] == s0['source_pieces']
    assert s1['bundles_by_status']['ENVELOPE_ONLY'] == s0['bundles_by_status']['ENVELOPE_ONLY'] + g0['bundle_count']
    assert s1['derived_pieces'] == s0['derived_pieces'] - g0['pieces_placed'] * g0['bundle_count']


def test_od_larger_than_section_is_envelope_only_with_reason():
    create([update(G5, confirmation='UNVERIFIED', outside_diameter_mm='120')])
    create([update(G5, confirmation='UNVERIFIED', outside_diameter_mm='400')], parent=R1)
    pk0, pk2 = packing(R0), packing(R2)
    g2 = group(pk2, G5)
    assert g2['status'] == 'ENVELOPE_ONLY' and g2['od_um'] == 400000
    assert codes(g2) == ['OD_EXCEEDS_SECTION'] and g2['checks']['od_fit'] is False
    assert g2['pieces_placed'] == 0 and g2['pipe_centres_um'] == [] and g2['bundle_packings'] == []
    assert VIETNAMESE.search(g2['reasons'][0]['message'])
    assert other_groups(pk2, G5) == other_groups(pk0, G5)
    s0, s2 = pk0['stats'], pk2['stats']
    assert s2['groups_by_status'] == {'DETAILED': 27, 'ENVELOPE_ONLY': 4}
    assert s2['bundles_by_status']['ENVELOPE_ONLY'] == s0['bundles_by_status']['ENVELOPE_ONLY'] + group(pk0, G5)['bundle_count']
    assert s2['derived_pieces'] == s0['derived_pieces'] - group(pk0, G5)['pieces_placed'] * group(pk0, G5)['bundle_count']
    assert s2['source_pieces'] == s0['source_pieces']


# ------------------------------------------------------------------ S3-02: source warning reason
def test_source_warning_group_keeps_source_warning_reason():
    g = group(packing(R0), WARNED_GROUP)
    assert g['status'] == 'ENVELOPE_ONLY' and codes(g) == ['PIECES_DO_NOT_FIT', 'SOURCE_WARNING']
    source_reason = next(r for r in g['reasons'] if r['code'] == 'SOURCE_WARNING')
    assert VIETNAMESE.search(source_reason['message']) and g['bundle_packings'] == []
    create([update(G5, confirmation='UNVERIFIED', outside_diameter_mm='120')])
    assert codes(group(packing(R1), WARNED_GROUP)) == ['PIECES_DO_NOT_FIT', 'SOURCE_WARNING']
