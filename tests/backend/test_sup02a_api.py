"""SUP-02A API acceptance (S2-01..S2-05). Every test uses a temporary SCST_DATA_DIR; no runtime data is touched."""
import hashlib
import json
import re
import sqlite3
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.pipe_registry import PATH as BALTIMORE_PATH, REGISTRY
from app.demo import demo_plan
from app.domain import cargo_revisions as cr
from app.main import app

client = TestClient(app)
R0 = cr.BASE_REVISION_ID
R1, R2, R3 = cr.revision_id(1), cr.revision_id(2), cr.revision_id(3)
VIETNAMESE = re.compile('[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.I)
LEGACY_DDL = ('CREATE TABLE snapshots (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_utc TEXT NOT NULL, '
              'schema_version TEXT NOT NULL, plan_json TEXT NOT NULL)')
G2, G3, G4, G5 = 'Sheet1-R002', 'Sheet1-R003', 'Sheet1-R004', 'Sheet1-R005'
WARNED_GROUP = 'Sheet1-R022'
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
def db(data):
    return sqlite3.connect(data / 'scst.sqlite3')


def revision_rows(data):
    if not (data / 'scst.sqlite3').exists():
        return 0
    con = db(data)
    try:
        return con.execute('SELECT COUNT(*) FROM cargo_revisions').fetchone()[0]
    finally:
        con.close()


def snapshot_rows(data):
    con = db(data)
    try:
        return con.execute('SELECT * FROM snapshots ORDER BY id').fetchall()
    finally:
        con.close()


def latest_id():
    return client.get('/api/cargo-revisions').json()['latest_revision_id']


def draft(changes, source=None, parent=None):
    return {'parent_revision_id': parent or latest_id(), 'source': source or SOURCE, 'changes': changes}


def update(group, confirmation='CONFIRMED', **fields):
    return {'type': 'UPDATE_GROUP', 'group_id': group, 'confirmation': confirmation, 'set': fields}


def override(bundle, confirmation='UNVERIFIED', **fields):
    return {'type': 'BUNDLE_OVERRIDE', 'bundle_id': bundle, 'confirmation': confirmation, 'set': fields}


def add_group(count=3, confirmation='UNVERIFIED', **extra):
    group = {'bundle_count': count, 'pieces_per_bundle': 10, 'dimensions_um': [6000000, 300000, 300000], 'mass_g': 500000,
             'outside_diameter_mm': '60.3', 'wall_thickness_mm': '3.91', 'dimension_warning': False}
    group.update(extra)
    return {'type': 'ADD_GROUP', 'confirmation': confirmation, 'group': group}


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


def v1_plan():
    r = client.post('/api/pipe-list/preview', json=roomy(base_plan()))
    assert r.status_code == 200, r.text
    return r.json()['plan']


def v2_plan(revision=None):
    r = client.post(f'/api/cargo-revisions/{revision or latest_id()}/plan-preview', json=roomy(base_plan()))
    assert r.status_code == 200, r.text
    return r.json()['plan']


def place(plan, *pairs):
    plan['placements'] = [dict(unit_id=u, x_mm=0, y_mm=y, z_mm=0, layer=0, supported_by=[], yaw_deg=0) for u, y in pairs]
    return plan


def m2a_plan():
    text = 'id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\nA,Synthetic,BAR_BUNDLE,required,1000,500,300,12.5\n'
    r = client.post('/api/import/csv/preview', json={'plan': base_plan(), 'csv_text': text}).json()
    assert r['valid']
    return r['candidate']


def save(plan, name='Phương án thử'):
    r = client.post('/api/snapshots', json={'name': name, 'plan': plan})
    assert r.status_code == 200, r.text
    return r.json()['id']


def listing():
    r = client.get('/api/snapshots')
    assert r.status_code == 200, r.text
    return {i['id']: i for i in r.json()}


def stored_plan_json(data, snapshot_id):
    con = db(data)
    try:
        return con.execute('SELECT plan_json FROM snapshots WHERE id=?', (snapshot_id,)).fetchone()[0]
    finally:
        con.close()


def insert_raw_snapshot(data, snapshot_id, plan_json, created='2026-01-01T00:00:00+00:00'):
    con = db(data)
    try:
        con.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)', (snapshot_id, 'Hàng SQL', created, 'scst.saved-plan.v1', plan_json))
        con.commit()
    finally:
        con.close()


# ------------------------------------------------------------------ S2-01
def test_initial_list_shows_only_derived_base_with_stable_hash(data):
    first = client.get('/api/cargo-revisions').json()
    second = client.get('/api/cargo-revisions').json()
    assert first == second and first['dataset_id'] == cr.DATASET and first['latest_revision_id'] == R0
    (base,) = first['revisions']
    assert base['revision_id'] == R0 and base['parent_revision_id'] is None and base['change_count'] == 0
    assert base['content_sha256'] == cr.content_sha256(cr.base_groups(REGISTRY))
    assert (base['group_count'], base['bundle_count'], base['total_mass_g']) == (31, 1076, 1125551030)
    assert base['available'] and base['integrity_error'] is None
    assert revision_rows(data) == 0


def test_preview_reports_affected_ids_and_writes_nothing(data):
    changes = [update(G2, mass_g=900000), update(G3, bundle_count=18), add_group(2)]
    r = client.post('/api/cargo-revisions/preview', json=draft(changes))
    assert r.status_code == 200
    j = r.json()
    assert j['valid'] and j['errors'] == [] and j['parent_is_latest'] and j['latest_revision_id'] == R0
    assert len(j['changed_bundle_ids']) == 160 and j['removed_bundle_ids'] == ['PIPE-R003-B0019', 'PIPE-R003-B0020']
    assert j['added_bundle_ids'] == ['PIPE-A001-B0001', 'PIPE-A001-B0002']
    assert [s['index'] for s in j['change_summaries']] == [0, 1, 2] and all(s['text'] for s in j['change_summaries'])
    assert (j['group_count'], j['bundle_count']) == (32, 1076 - 2 + 2) and j['content_sha256']
    assert revision_rows(data) == 0
    assert client.get('/api/cargo-revisions').json()['latest_revision_id'] == R0
    bad = client.post('/api/cargo-revisions/preview', json=draft([update(G2, mass_g=0)])).json()
    assert not bad['valid'] and bad['errors'][0]['index'] == 0 and bad['content_sha256'] is None
    assert revision_rows(data) == 0


def test_create_list_read_chain(data):
    first = create([update(G2, mass_g=900000)])
    assert first['revision_id'] == R1 and first['parent_revision_id'] == R0 and first['change_count'] == 1
    assert first['source']['reference'] == SOURCE['reference'] and first['created_utc']
    second = create([override('PIPE-R003-B0001', mass_g=123457)], parent=R1)
    assert second['revision_id'] == R2 and second['parent_revision_id'] == R1
    listed = client.get('/api/cargo-revisions').json()
    assert listed['latest_revision_id'] == R2
    assert [r['revision_id'] for r in listed['revisions']] == [R2, R1, R0]
    assert listed['revisions'][0]['content_sha256'] != listed['revisions'][1]['content_sha256']
    assert revision_rows(data) == 2
    detail = client.get(f'/api/cargo-revisions/{R2}').json()
    assert detail['content_sha256'] == second['content_sha256'] and len(detail['changes']) == 1
    assert detail['total_mass_g'] == 1125551030 + 160 * (900000 - 911400) + (123457 - REGISTRY['groups'][1]['mass_g'])
    assert client.get(f'/api/cargo-revisions/{cr.DATASET}@R0009').status_code == 404
    assert client.get('/api/cargo-revisions/nonsense').status_code == 404


def test_stale_parent_returns_409_and_writes_nothing(data):
    create([update(G2, mass_g=900000)])
    r = client.post('/api/cargo-revisions', json=draft([update(G3, mass_g=1000)], parent=R0))
    assert r.status_code == 409
    assert r.json()['detail']['latest_revision_id'] == R1 and r.json()['detail']['message']
    assert revision_rows(data) == 1
    assert client.get('/api/cargo-revisions').json()['latest_revision_id'] == R1
    unknown = client.post('/api/cargo-revisions', json=draft([update(G3, mass_g=1000)], parent=cr.revision_id(7)))
    assert unknown.status_code == 409 and revision_rows(data) == 1


@pytest.mark.parametrize('path', ['/api/cargo-revisions', '/api/cargo-revisions/preview'])
def test_payload_over_one_mib_rejected(data, path):
    big = dict(SOURCE, reference='x' * 1_100_000)
    r = client.post(path, json=draft([update(G2, mass_g=900000)], source=big))
    assert r.status_code == 400
    errors = r.json()['detail']['errors']
    assert errors == [{'index': None, 'field': 'payload', 'message': errors[0]['message']}] and VIETNAMESE.search(errors[0]['message'])
    assert revision_rows(data) == 0


def _too_many_groups():
    return [add_group(1) for _ in range(171)]


LIMIT_CASES = [
    ('bundle_count_over_group_limit', [update(G3, bundle_count=2001)], 0, 'set.bundle_count'),
    ('pieces_zero', [update(G3, pieces_per_bundle=0)], 0, 'set.pieces_per_bundle'),
    ('pieces_over', [update(G3, pieces_per_bundle=10001)], 0, 'set.pieces_per_bundle'),
    ('mass_over', [update(G3, mass_g=10 ** 12 + 1)], 0, 'set.mass_g'),
    ('mass_float', [update(G3, mass_g=1.5)], 0, 'set.mass_g'),
    ('mass_bool', [update(G3, mass_g=True)], 0, 'set.mass_g'),
    ('dimension_over', [update(G2, mass_g=900000), update(G3, dimensions_um=[1, 2, 10 ** 9 + 1])], 1, 'set.dimensions_um.2'),
    ('dimension_zero', [update(G3, dimensions_um=[0, 2, 3])], 0, 'set.dimensions_um.0'),
    ('dimension_arity', [update(G3, dimensions_um=[1, 2])], 0, 'set.dimensions_um'),
    ('diameter_format', [update(G3, outside_diameter_mm='-3')], 0, 'set.outside_diameter_mm'),
    ('unknown_group', [update('Sheet1-R999', mass_g=5)], 0, 'group_id'),
    ('unknown_bundle', [override('PIPE-R003-B0999', mass_g=5)], 0, 'bundle_id'),
    ('bad_confirmation', [update(G3, confirmation='MAYBE', mass_g=5)], 0, 'confirmation'),
    ('warning_off_unverified', [update(WARNED_GROUP, confirmation='UNVERIFIED', dimension_warning=False)], 0, 'set.dimension_warning'),
    ('add_missing_field', [{'type': 'ADD_GROUP', 'confirmation': 'CONFIRMED', 'group': {'bundle_count': 1}}], 0, 'group.pieces_per_bundle'),
    ('total_bundles', [update(G2, bundle_count=2000)], None, 'changes'),
    ('group_count', _too_many_groups(), None, 'changes'),
    ('too_many_changes', [update(G3, mass_g=5)] * 501, None, 'changes'),
    ('no_changes', [], None, 'changes'),
]


@pytest.mark.parametrize('name,changes,index,field', LIMIT_CASES, ids=[c[0] for c in LIMIT_CASES])
def test_every_limit_returns_vietnamese_error_per_change_and_writes_nothing(data, name, changes, index, field):
    preview = client.post('/api/cargo-revisions/preview', json=draft(changes)).json()
    assert preview['valid'] is False
    r = client.post('/api/cargo-revisions', json=draft(changes))
    assert r.status_code == 400
    errors = r.json()['detail']['errors']
    assert errors == preview['errors']
    hit = [e for e in errors if e['field'] == field and e['index'] == index]
    assert hit, errors
    assert all(VIETNAMESE.search(e['message']) for e in errors)
    assert revision_rows(data) == 0


def test_source_errors_and_confirmed_warning_off(data):
    for source in (dict(SOURCE, reference='   '), dict(SOURCE, kind='MARS'), dict(SOURCE, received_date='2026-02-30'),
                   dict(SOURCE, note='n' * 501)):
        r = client.post('/api/cargo-revisions', json=draft([update(G3, mass_g=5)], source=source))
        assert r.status_code == 400
        assert r.json()['detail']['errors'][0]['index'] is None and r.json()['detail']['errors'][0]['field'].startswith('source')
    assert revision_rows(data) == 0
    ok = create([update(WARNED_GROUP, confirmation='CONFIRMED', dimension_warning=False)])
    assert ok['revision_id'] == R1


# ------------------------------------------------------------------ S2-02
def test_revision_detail_provenance_and_overrides():
    create([update(G2, mass_g=900000), override('PIPE-R003-B0001', mass_g=123457, dimensions_um=[6400001, 300001, 300001]),
            add_group(2)])
    d = client.get(f'/api/cargo-revisions/{R1}').json()
    groups = {g['group_id']: g for g in d['groups']}
    g2 = groups[G2]
    mass = g2['provenance']['mass_g']
    assert mass['revision_id'] == R1 and mass['confirmation'] == 'CONFIRMED' and mass['source']['reference'] == SOURCE['reference']
    for field in ('pieces_per_bundle', 'dimensions_um', 'bundle_count'):
        assert g2['provenance'][field] == {'revision_id': R0, 'source': None, 'confirmation': 'WORKBOOK'}
    assert groups[G4]['provenance']['mass_g']['revision_id'] == R0
    (ov,) = groups[G3]['overrides']
    assert ov['bundle_id'] == 'PIPE-R003-B0001' and ov['mass_g'] == 123457 and ov['dimensions_um'] == [6400001, 300001, 300001]
    assert ov['provenance']['mass_g'] == {'revision_id': R1, 'source': SOURCE, 'confirmation': 'UNVERIFIED'}
    assert groups[G3]['provenance']['mass_g']['revision_id'] == R0 and groups[G3]['mass_g'] == REGISTRY['groups'][1]['mass_g']
    added = groups['ADD-001']
    assert added['origin'] == 'ADDED' and added['source_row'] is None and added['bundle_ids'] == ['PIPE-A001-B0001', 'PIPE-A001-B0002']
    assert all(s['revision_id'] == R1 and s['confirmation'] == 'UNVERIFIED' for s in added['provenance'].values())
    base = client.get(f'/api/cargo-revisions/{R0}').json()
    assert all(s == {'revision_id': R0, 'source': None, 'confirmation': 'WORKBOOK'} for g in base['groups'] for s in g['provenance'].values())
    assert all(g['overrides'] == [] for g in base['groups']) and base['changes'] == []


def test_bundle_ids_stable_and_never_reissued():
    create([update(G3, bundle_count=18)])
    create([update(G3, bundle_count=19)])
    detail = {g['group_id']: g for g in client.get(f'/api/cargo-revisions/{R2}').json()['groups']}[G3]
    assert detail['bundle_ids'][-1] == 'PIPE-R003-B0021' and 'PIPE-R003-B0019' not in detail['bundle_ids']
    assert detail['bundle_ids'][:3] == ['PIPE-R003-B0001', 'PIPE-R003-B0002', 'PIPE-R003-B0003'] and detail['bundle_count'] == 19


def test_plan_preview_units_carry_revision_and_confirmation_with_exact_values():
    create([update(G2, mass_g=900001, dimensions_um=[6401001, 337601, 295401]),
            override('PIPE-R003-B0001', mass_g=123457), add_group(1, confirmation='CONFIRMED')])
    r = client.post(f'/api/cargo-revisions/{R1}/plan-preview', json=roomy(base_plan()))
    assert r.status_code == 200
    plan = r.json()['plan']
    assert plan['contract_version'] == 'scst.pipe-list.v2' and plan['placements'] == []
    assert plan['cargo_revision'] == {'dataset_id': cr.DATASET, 'revision_id': R1,
                                      'content_sha256': client.get(f'/api/cargo-revisions/{R1}').json()['content_sha256']}
    units = {u['id']: u for u in plan['units']}
    assert len(units) == 1077 and all(u['requirement'] == 'optional' for u in units.values())
    changed = units['PIPE-R002-B0001']
    assert (changed['mass_g'], changed['dimensions_um']) == (900001, [6401001, 337601, 295401])
    assert (changed['length_mm'], changed['width_mm'], changed['height_mm']) == (6402, 338, 296)
    assert changed['source_ref']['revision_id'] == R1 and changed['source_ref']['confirmation'] == 'CONFIRMED'
    over = units['PIPE-R003-B0001']
    assert over['mass_g'] == 123457 and over['source_ref']['revision_id'] == R1 and over['source_ref']['confirmation'] == 'UNVERIFIED'
    untouched = units['PIPE-R004-B0001']
    assert untouched['source_ref']['revision_id'] == R0 and untouched['source_ref']['confirmation'] == 'WORKBOOK'
    assert units['PIPE-R003-B0002']['source_ref']['revision_id'] == R0
    added = units['PIPE-A001-B0001']
    assert added['source_ref']['source_row'] is None and added['source_ref']['confirmation'] == 'CONFIRMED'
    # R0000 plan-preview carries exactly the legacy v1 data (ids, mass, µm) with workbook provenance.
    legacy = {u['id']: u for u in v1_plan()['units']}
    base = {u['id']: u for u in v2_plan(R0)['units']}
    assert legacy.keys() == base.keys()
    assert all((legacy[i]['mass_g'], legacy[i]['dimensions_um']) == (base[i]['mass_g'], base[i]['dimensions_um']) for i in legacy)
    assert client.post(f'/api/cargo-revisions/{cr.revision_id(5)}/plan-preview', json=base_plan()).status_code == 404


# ------------------------------------------------------------------ S2-03
def _tamper(plan, kind):
    plan = deepcopy(plan)
    if kind == 'mass':
        plan['units'][0]['mass_g'] += 1
    elif kind == 'missing':
        plan['units'].pop()
    elif kind == 'sha':
        plan['cargo_revision']['content_sha256'] = 'f' * 64
    elif kind == 'nonexistent':
        plan['cargo_revision']['revision_id'] = cr.revision_id(99)
    return plan


TAMPERS = ['mass', 'missing', 'sha', 'nonexistent']
CSV = 'id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\nA,Synthetic,BAR_BUNDLE,required,1,1,1,1\n'
ENTRY_POINTS = {
    'validate': lambda p: client.post('/api/validate', json=p),
    'save': lambda p: client.post('/api/snapshots', json={'name': 'x', 'plan': p}),
    'compare_before': lambda p: client.post('/api/plans/compare', json={'before': p, 'after': v1_plan()}),
    'compare_after': lambda p: client.post('/api/plans/compare', json={'before': v1_plan(), 'after': p}),
    'planner': lambda p: client.post('/api/planner/preview', json=p),
    'pipe_list': lambda p: client.post('/api/pipe-list/preview', json=p),
    'csv': lambda p: client.post('/api/import/csv/preview', json={'plan': p, 'csv_text': CSV}),
}


@pytest.fixture
def revised():
    create([update(G2, mass_g=900000), update(G3, bundle_count=18), add_group(2)])
    return v2_plan(R1)


def test_valid_v2_plan_accepted_at_every_entry_point(data, revised):
    plan = place(revised, ('PIPE-R004-B0001', 0), ('PIPE-A001-B0001', 400))
    for name, call in ENTRY_POINTS.items():
        r = call(plan)
        assert r.status_code == 200, (name, r.text)
    v = client.post('/api/validate', json=plan).json()
    assert v['plan'] == plan and v['summary']['placed_count'] == 2
    assert client.post('/api/pipe-list/preview', json=plan).json()['plan']['contract_version'] == 'scst.pipe-list.v1'
    c = client.post('/api/import/csv/preview', json={'plan': plan, 'csv_text': CSV}).json()
    assert c['valid'] and c['candidate']['contract_version'] == 'scst.m2a.v1' and 'cargo_revision' not in c['candidate']
    assert client.post('/api/plans/compare', json={'before': plan, 'after': plan}).json()['counts']['CHANGED'] == 0
    sid = save(plan)
    opened = client.get('/api/snapshots/' + sid)
    assert opened.status_code == 200 and opened.json()['plan'] == plan
    assert json.loads(stored_plan_json(data, sid))['cargo_revision']['revision_id'] == R1
    assert revision_rows(data) == 1


@pytest.mark.parametrize('kind', TAMPERS)
@pytest.mark.parametrize('entry', list(ENTRY_POINTS))
def test_tampered_v2_plan_rejected_at_every_entry_point(data, revised, entry, kind):
    r = ENTRY_POINTS[entry](_tamper(revised, kind))
    assert r.status_code == (400 if entry == 'save' else 422), r.text
    assert VIETNAMESE.search(str(r.json()['detail']))
    if entry == 'save':
        assert snapshot_rows(data) == []


@pytest.mark.parametrize('kind', TAMPERS)
def test_tampered_v2_snapshot_not_openable(data, revised, kind):
    sid = '22222222-2222-4222-8222-222222222222'
    insert_raw_snapshot(data, sid, json.dumps(_tamper(revised, kind)))
    r = client.get('/api/snapshots/' + sid)
    assert r.status_code == 400
    assert str(r.json()['detail'])


def test_v2_pinned_to_old_revision_still_valid_after_new_revision(revised):
    old = v2_plan(R0)
    create([update(G4, mass_g=1000)], parent=R1)
    assert client.post('/api/validate', json=old).status_code == 200
    assert client.post('/api/validate', json=revised).status_code == 200


def test_legacy_contracts_regression(data):
    # scst.m1.v1
    m1 = demo_plan().model_dump(mode='json')
    sid_m1 = save(m1)
    opened = client.get('/api/snapshots/' + sid_m1)
    assert client.post('/api/validate', json=m1).status_code == 200
    assert opened.status_code == 200 and opened.json()['plan'] == m1
    # scst.m2a.v1
    m2a = m2a_plan()
    assert client.post('/api/validate', json=m2a).status_code == 200
    sid_m2a = save(m2a)
    assert client.get('/api/snapshots/' + sid_m2a).json()['plan'] == m2a
    # scst.pipe-list.v1
    v1 = place(v1_plan(), ('PIPE-R002-B0001', 0))
    assert client.post('/api/validate', json=v1).status_code == 200
    sid_v1 = save(v1)
    assert client.get('/api/snapshots/' + sid_v1).json()['plan'] == client.post('/api/validate', json=v1).json()['plan']
    for sid in (sid_m1, sid_m2a, sid_v1):
        stored = json.loads(stored_plan_json(data, sid))
        assert 'cargo_revision' not in stored
    assert set(listing()) == {sid_m1, sid_m2a, sid_v1}
    # legacy contracts still work, unchanged, after revisions exist
    create([update(G2, mass_g=900000)])
    assert client.post('/api/validate', json=v1).status_code == 200
    assert client.get('/api/snapshots/' + sid_v1).status_code == 200
    # tampered v1 stays rejected by its own structural contract
    broken = deepcopy(v1)
    broken['units'][0]['mass_g'] += 1
    assert client.post('/api/validate', json=broken).status_code == 422


def test_legacy_snapshot_rows_inserted_directly_open_identically_and_are_listed(data):
    con = db(data)
    con.execute(LEGACY_DDL)
    con.commit()
    con.close()
    m1_json = json.dumps(demo_plan().model_dump(mode='json'))
    v1_json = json.dumps(v1_plan())
    ids = ['33333333-3333-4333-8333-333333333333', '44444444-4444-4444-8444-444444444444']
    insert_raw_snapshot(data, ids[0], m1_json, '2026-01-01T00:00:00+00:00')
    insert_raw_snapshot(data, ids[1], v1_json, '2026-01-02T00:00:00+00:00')
    before = snapshot_rows(data)
    for sid, raw in zip(ids, (m1_json, v1_json)):
        r = client.get('/api/snapshots/' + sid)
        assert r.status_code == 200 and r.json()['plan'] == json.loads(raw)
    items = listing()
    assert set(items) == set(ids)
    assert items[ids[0]]['recheck_status'] == 'NOT_APPLICABLE' and items[ids[1]]['recheck_status'] == 'CURRENT'
    assert snapshot_rows(data) == before and revision_rows(data) == 0


def test_exact_micrometre_and_gram_values_preserved(data):
    create([update(G2, mass_g=911401, dimensions_um=[6401001, 337601, 295401])])
    plan = v2_plan(R1)
    unit = plan['units'][0]
    assert (unit['mass_g'], unit['dimensions_um']) == (911401, [6401001, 337601, 295401])
    sid = save(plan)
    stored = json.loads(stored_plan_json(data, sid))['units'][0]
    assert (stored['mass_g'], stored['dimensions_um']) == (911401, [6401001, 337601, 295401])
    opened = client.get('/api/snapshots/' + sid).json()['plan']['units'][0]
    assert (opened['mass_g'], opened['dimensions_um']) == (911401, [6401001, 337601, 295401])


# ------------------------------------------------------------------ S2-04
def test_recheck_statuses_counts_and_rebase(data):
    required_unit = 'PIPE-R005-B0001'
    v1 = v1_plan()
    for u in v1['units']:
        if u['id'] == required_unit:
            u['requirement'] = 'required'
    v1 = place(v1, ('PIPE-R002-B0001', 0), ('PIPE-R003-B0019', 400), ('PIPE-R004-B0001', 800))
    sid_m1, sid_m2a, sid_v1 = save(base_plan(), 'm1'), save(m2a_plan(), 'm2a'), save(v1, 'v1')
    sid_v2_old = save(place(v2_plan(R0), ('PIPE-R004-B0001', 0)), 'v2 R0')
    items = listing()
    for sid in (sid_m1, sid_m2a):
        assert items[sid]['recheck_status'] == 'NOT_APPLICABLE' and items[sid]['cargo_revision_id'] is None
        assert (items[sid]['added_count'], items[sid]['removed_count'], items[sid]['changed_count']) == (0, 0, 0)
    for sid in (sid_v1, sid_v2_old):
        assert items[sid]['recheck_status'] == 'CURRENT' and items[sid]['cargo_revision_id'] == R0
        assert items[sid]['placed_affected_count'] == 0

    create([update(G2, mass_g=900000), update(G3, bundle_count=18), add_group(3)])
    before = snapshot_rows(data)
    items = listing()
    expected = {'recheck_status': 'NEEDS_RECHECK', 'cargo_revision_id': R0, 'added_count': 3, 'removed_count': 2,
                'changed_count': 160, 'placed_affected_count': 2}
    assert {k: items[sid_v1][k] for k in expected} == expected
    assert items[sid_v1]['name'] == 'v1' and items[sid_v1]['schema_version'] == 'scst.saved-plan.v1'
    assert items[sid_v2_old]['recheck_status'] == 'NEEDS_RECHECK' and items[sid_v2_old]['placed_affected_count'] == 0
    assert items[sid_m1]['recheck_status'] == 'NOT_APPLICABLE'

    sid_v2_new = save(v2_plan(R1), 'v2 R1')
    assert listing()[sid_v2_new]['recheck_status'] == 'CURRENT' and listing()[sid_v2_new]['cargo_revision_id'] == R1
    original_json = stored_plan_json(data, sid_v1)

    r = client.post(f'/api/snapshots/{sid_v1}/rebase')
    assert r.status_code == 200, r.text
    j = r.json()
    assert (j['source_revision_id'], j['target_revision_id']) == (R0, R1)
    assert j['kept_placement_count'] == 1
    dropped = {d['unit_id']: d for d in j['dropped_placements']}
    assert dropped == {'PIPE-R002-B0001': {'unit_id': 'PIPE-R002-B0001', 'reason': 'CHANGED', 'x_mm': 0, 'y_mm': 0, 'yaw_deg': 0},
                       'PIPE-R003-B0019': {'unit_id': 'PIPE-R003-B0019', 'reason': 'REMOVED', 'x_mm': 0, 'y_mm': 400, 'yaw_deg': 0}}
    assert len(j['changed_unit_ids']) == 160 and j['removed_unit_ids'] == ['PIPE-R003-B0019', 'PIPE-R003-B0020']
    assert j['added_unit_ids'] == ['PIPE-A001-B0001', 'PIPE-A001-B0002', 'PIPE-A001-B0003']
    cand = j['candidate']['plan']
    assert cand['contract_version'] == 'scst.pipe-list.v2' and cand['cargo_revision']['revision_id'] == R1
    assert [p['unit_id'] for p in cand['placements']] == ['PIPE-R004-B0001']
    assert cand['placements'][0] == {'unit_id': 'PIPE-R004-B0001', 'x_mm': 0, 'y_mm': 800, 'z_mm': 0, 'layer': 0,
                                     'supported_by': [], 'yaw_deg': 0}
    units = {u['id']: u for u in cand['units']}
    assert len(units) == 1076 - 2 + 3 and units[required_unit]['requirement'] == 'required'
    assert units['PIPE-A001-B0001']['requirement'] == 'optional' and units['PIPE-R002-B0001']['mass_g'] == 900000
    assert j['comparison']['counts']['ADDED'] == 3 and j['comparison']['counts']['REMOVED'] == 2
    assert j['comparison']['counts']['CHANGED'] >= 160 and j['comparison']['after']['placed_count'] == 1
    assert j['comparison']['before']['placed_count'] == 3
    # candidate is a normal plan: validates and saves as a new snapshot
    assert client.post('/api/validate', json=cand).status_code == 200
    new_id = save(cand, 'bản mới')
    assert listing()[new_id]['recheck_status'] == 'CURRENT' and new_id != sid_v1
    assert client.get('/api/snapshots/' + new_id).json()['plan'] == cand
    # saved snapshots are never modified
    assert stored_plan_json(data, sid_v1) == original_json
    after = {row[0]: row for row in snapshot_rows(data)}
    assert all(after[row[0]] == row for row in before)
    # rebasing a v2 snapshot pinned to an older revision works too; rebase of an up-to-date one keeps every placement
    again = client.post(f'/api/snapshots/{sid_v2_old}/rebase').json()
    assert again['source_revision_id'] == R0 and again['target_revision_id'] == R1 and again['kept_placement_count'] == 1
    same = client.post(f'/api/snapshots/{new_id}/rebase').json()
    assert same['kept_placement_count'] == 1 and same['dropped_placements'] == [] and same['changed_unit_ids'] == []
    assert stored_plan_json(data, sid_v1) == original_json


def test_rebase_rejections(data):
    sid_m1 = save(base_plan())
    r = client.post(f'/api/snapshots/{sid_m1}/rebase')
    assert r.status_code == 400 and VIETNAMESE.search(r.json()['detail'])
    assert client.post('/api/snapshots/not-a-uuid/rebase').status_code == 400
    assert client.post('/api/snapshots/55555555-5555-4555-8555-555555555555/rebase').status_code == 404
    assert revision_rows(data) == 0


def test_listing_read_only_and_cached_per_call(data):
    v1 = v1_plan()
    ids = [save(v1, f'v1 #{i}') for i in range(3)]
    create([update(G2, mass_g=900000)])
    before = snapshot_rows(data)
    items = listing()
    assert all(items[i]['recheck_status'] == 'NEEDS_RECHECK' and items[i]['changed_count'] == 160 for i in ids)
    assert snapshot_rows(data) == before


# ------------------------------------------------------------------ S2-05 (API level)
def test_tampered_stored_hash_refuses_that_revision_but_serves_base(data):
    create([update(G2, mass_g=900000)])
    sid_v2 = save(v2_plan(R1), 'pinned R1')
    sid_base = save(v2_plan(R0), 'pinned R0')
    sid_v1 = save(v1_plan(), 'v1')
    sid_m1 = save(base_plan(), 'm1')
    con = db(data)
    con.execute('UPDATE cargo_revisions SET content_sha256=? WHERE revision_id=?', ('0' * 64, R1))
    con.commit()
    con.close()
    rows_before = snapshot_rows(data)

    bad = client.get(f'/api/cargo-revisions/{R1}')
    assert bad.status_code == 400 and VIETNAMESE.search(bad.json()['detail']['message'])
    assert client.get(f'/api/cargo-revisions/{R0}').status_code == 200
    assert client.post(f'/api/cargo-revisions/{R1}/plan-preview', json=base_plan()).status_code == 400
    assert client.post(f'/api/cargo-revisions/{R0}/plan-preview', json=base_plan()).status_code == 200
    listed = client.get('/api/cargo-revisions')
    assert listed.status_code == 200
    by_id = {r['revision_id']: r for r in listed.json()['revisions']}
    assert by_id[R1]['available'] is False and by_id[R1]['integrity_error'] and by_id[R1]['group_count'] is None
    assert by_id[R0]['available'] is True and listed.json()['latest_revision_id'] == R1
    # new revisions cannot be built on a broken store; nothing is written
    assert client.post('/api/cargo-revisions', json=draft([update(G3, mass_g=5)], parent=R1)).status_code == 400
    assert client.post('/api/cargo-revisions/preview', json=draft([update(G3, mass_g=5)], parent=R1)).status_code == 400
    assert revision_rows(data) == 1

    items = listing()
    assert items[sid_v2]['recheck_status'] == 'REVISION_UNAVAILABLE' and items[sid_v2]['cargo_revision_id'] == R1
    assert items[sid_m1]['recheck_status'] == 'NOT_APPLICABLE'
    assert set(items) == {sid_v2, sid_base, sid_v1, sid_m1}
    assert client.get('/api/snapshots/' + sid_v2).status_code == 400
    assert client.post(f'/api/snapshots/{sid_v2}/rebase').status_code == 400
    assert client.post('/api/validate', json=json.loads(stored_plan_json(data, sid_v2))).status_code == 422
    # plans pinned to R0000 and legacy plans keep opening
    assert client.get('/api/snapshots/' + sid_base).status_code == 200
    assert client.get('/api/snapshots/' + sid_v1).status_code == 200
    assert snapshot_rows(data) == rows_before


def test_later_broken_revision_does_not_block_earlier_ones(data):
    create([update(G2, mass_g=900000)])
    create([update(G3, mass_g=1000)], parent=R1)
    sid_r1 = save(v2_plan(R1), 'pinned R1')
    con = db(data)
    con.execute('UPDATE cargo_revisions SET content_sha256=? WHERE revision_id=?', ('0' * 64, R2))
    con.commit()
    con.close()
    assert client.get(f'/api/cargo-revisions/{R1}').status_code == 200
    assert client.get(f'/api/cargo-revisions/{R2}').status_code == 400
    assert client.get('/api/snapshots/' + sid_r1).status_code == 200
    by_id = {r['revision_id']: r for r in client.get('/api/cargo-revisions').json()['revisions']}
    assert by_id[R1]['available'] and not by_id[R2]['available']
    assert listing()[sid_r1]['recheck_status'] == 'REVISION_UNAVAILABLE'


def test_unknown_pinned_revision_in_stored_snapshot_is_listed_unavailable(data, revised=None):
    create([update(G2, mass_g=900000)])
    plan = v2_plan(R1)
    plan['cargo_revision']['revision_id'] = cr.revision_id(99)
    sid = '66666666-6666-4666-8666-666666666666'
    insert_raw_snapshot(data, sid, json.dumps(plan))
    item = listing()[sid]
    assert item['recheck_status'] == 'REVISION_UNAVAILABLE' and item['cargo_revision_id'] == cr.revision_id(99)
