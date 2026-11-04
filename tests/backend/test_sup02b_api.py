"""SUP-02B API acceptance (S2B-03, S2B-04): vessel-profile store endpoints and user-profile plan references.
Every test uses a temporary SCST_DATA_DIR and a synthetic GLB built at run time; built-in data is never written."""
import base64
import hashlib
import json
import re
import sqlite3
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters import vessel_profile_service as service
from app.domain.vessel_profiles.glb import MAX_GLB_BYTES
from app.domain.vessel_profiles import MAX_PROFILE_BYTES
from app.main import app
from app.vessel import DATA
from glb_fixture import bad_magic, bad_total_length, bad_version, make_glb, non_json_first_chunk

client = TestClient(app)
VIETNAMESE = re.compile('[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.I)
GOLDEN = {
    '/api/vessels/vinafco268': 'e7840ff9496b281e984e1dc6e6deb561fdd83155cd2ce2e6d89feaeb36f9b78f',
    '/api/vessels/vinafco268/model': '684cb4d4c7351aaba50ff4c7d23b3766656cf1e7b2b652f36357b167d83b1a5d',
    '/api/vessels/vinafco268/cases/VR-SI/plan': '788f5cceeeff7dfcd648a4fb6e3788e04f565ce87725adda801a8a75f9dcbee8',
    '/api/vessels/vinafco268/cases/VR-SII/plan': '34014c4ded9058d76cb540e787d59782c1f34d4cb28ce0ef246c8380363ea89c',
}
SII_SHA = GOLDEN['/api/vessels/vinafco268/cases/VR-SII/plan']
SNAPSHOT_SHA = 'b1a51101ea4bce2a6d84dee7c3cb5a8072214fc28c69c64878029250aba3ab41'
CSV = 'id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\nA,Synthetic,BAR_BUNDLE,required,1,1,1,1\n'
LEGACY_DDL = ('CREATE TABLE snapshots (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_utc TEXT NOT NULL, '
              'schema_version TEXT NOT NULL, plan_json TEXT NOT NULL)')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree(path: Path) -> dict:
    return {str(p.relative_to(path)): sha(p.read_bytes()) for p in sorted(path.rglob('*')) if p.is_file()}


@pytest.fixture(scope='module', autouse=True)
def builtin_data_unchanged():
    before = tree(DATA.parent)
    yield
    assert tree(DATA.parent) == before


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


# ------------------------------------------------------------------ synthetic ship
def glb(hull=((-6, 0, -3), (6, 4, 3))):
    return make_glb([hull])


def profile(version=1, ship='TESTSHIP', **override):
    corners = [(-5, -2, 0, 0), (5, -2, 10000, 0), (-5, 2, 0, 4000), (5, 2, 10000, 4000)]
    data = {
        'contract_version': 'scst.vessel-profile.v1', 'id': ship, 'version': version, 'name': 'Tàu thử', 'registration': 'T-1',
        'dimensions_m': {'length': 12, 'beam': 6, 'depth': 4},
        'hold': {'id': 'HOLD-T1', 'name': 'Hầm thử', 'length_mm': 10000, 'width_mm': 4000, 'height_mm': 3000, 'status': 'ESTIMATED'},
        'cases': [{'id': 'T-C1', 'cargo_mass_g': 5_000_000_000, 'draft_m': 2.0},
                  {'id': 'T-C2', 'cargo_mass_g': 4_000_000_000, 'draft_m': 1.5}],
        'notes': [], 'provenance': {'source_documents': [{'title': 'Tài liệu thử'}],
                                   'field_status': {'dimensions_m': 'ESTIMATED', 'hold': 'ESTIMATED', 'cases': 'ESTIMATED'}},
        'transform': {'translation_m': [0, 0, 0], 'yaw_deg': 0},
        'landmarks': [{'name': f'Góc {i}', 'glb_m': [x, 0, z], 'hold_mm': [hx, hy, 0]} for i, (x, z, hx, hy) in enumerate(corners)]}
    data.update(override)
    return data


def body(prof=None, glb_bytes=None, **extra):
    return {'profile': profile() if prof is None else prof,
            'glb_base64': base64.b64encode(glb() if glb_bytes is None else glb_bytes).decode(), **extra}


def preview(**kwargs):
    return client.post('/api/vessel-profiles/preview', json=body(**kwargs))


def create(**kwargs):
    return client.post('/api/vessel-profiles', json=body(**kwargs))


def user_plan(version=1, case='T-C1', ship='TESTSHIP'):
    r = client.get(f'/api/vessel-profiles/{ship}/{version}/cases/{case}/plan')
    assert r.status_code == 200, r.text
    return r.json()['plan']


# ------------------------------------------------------------------ byte identity (S2B-04)
@pytest.mark.parametrize('url', list(GOLDEN))
def test_vinafco_routes_byte_identical_to_base_commit(url):
    assert sha(client.get(url).content) == GOLDEN[url]


def test_vinafco_plan_validate_snapshot_and_new_route_byte_identical(data):
    plan = client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan']
    assert 'profile_version' not in plan['vessel'] and 'profile_sha256' not in plan['vessel']
    assert sha(client.post('/api/validate', json=plan).content) == SII_SHA
    sid = client.post('/api/snapshots', json={'name': 'VINAFCO', 'plan': plan}).json()['id']
    with sqlite3.connect(data / 'scst.sqlite3') as con:
        stored = con.execute('SELECT plan_json FROM snapshots WHERE id=?', (sid,)).fetchone()[0]
    assert sha(stored.encode()) == SNAPSHOT_SHA and 'profile_' not in stored
    assert sha(client.get('/api/snapshots/' + sid).content) == SII_SHA
    assert sha(client.get('/api/vessel-profiles/VINAFCO268/1/cases/VR-SII/plan').content) == SII_SHA
    assert not (data / 'vessels').exists()


def test_legacy_snapshot_row_opens_and_is_never_modified(data):
    plan = client.get('/api/vessels/vinafco268/cases/VR-SI/plan').json()['plan']
    legacy = json.dumps(plan, ensure_ascii=False)
    con = sqlite3.connect(data / 'scst.sqlite3')
    con.execute(LEGACY_DDL)
    con.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)', ('7b1d9e2a-0c3f-4f6e-8a55-1c2d3e4f5a6b', 'Cũ', '2026-01-01T00:00:00+00:00', 'scst.saved-plan.v1', legacy))
    con.commit()
    con.close()
    sid = '7b1d9e2a-0c3f-4f6e-8a55-1c2d3e4f5a6b'

    def row():
        with sqlite3.connect(data / 'scst.sqlite3') as c:
            return c.execute('SELECT * FROM snapshots').fetchall()
    before = row()
    assert client.get('/api/snapshots/' + sid).json()['plan'] == plan
    assert client.get('/api/snapshots').status_code == 200
    assert client.post(f'/api/snapshots/{sid}/rebase').status_code == 400  # not a pipe-list plan
    assert row() == before


# ------------------------------------------------------------------ model (D4)
def test_model_profile_fields_rules():
    plan = client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan']
    for fields in ({'profile_version': 1}, {'profile_sha256': 'a' * 64}, {'profile_version': 1, 'profile_sha256': 'a' * 64}):
        bad = deepcopy(plan)
        bad['vessel'].update(fields)
        assert client.post('/api/validate', json=bad).status_code == 422, fields
    other = deepcopy(plan)
    other['vessel']['vessel_id'] = 'OTHER-SHIP'
    assert client.post('/api/validate', json=other).status_code == 422
    unknown_case = deepcopy(plan)
    unknown_case['vessel']['case_id'] = 'VR-SIII'
    assert client.post('/api/validate', json=unknown_case).status_code == 422
    assert create().status_code == 200
    mine = user_plan()
    assert mine['vessel']['profile_version'] == 1 and len(mine['vessel']['profile_sha256']) == 64
    for key in ('profile_version', 'profile_sha256'):
        half = deepcopy(mine)
        del half['vessel'][key]
        assert client.post('/api/validate', json=half).status_code == 422
    bool_version = deepcopy(mine)
    bool_version['vessel']['profile_version'] = True
    assert client.post('/api/validate', json=bool_version).status_code == 422


# ------------------------------------------------------------------ store endpoints (S2B-03)
def test_preview_writes_nothing_and_reports_verification(data):
    before = sorted(data.rglob('*'))
    r = preview()
    assert r.status_code == 200
    out = r.json()
    assert out['valid'] and out['errors'] == [] and out['verification']['result'] == 'PASS'
    assert out['id'] == 'TESTSHIP' and out['latest_version'] == 0 and out['version_ok'] and not out['builtin_conflict']
    assert out['glb_bytes'] == len(glb()) and out['glb_sha256'] == sha(glb())
    assert len(out['verification']['landmarks']) == 4 and out['verification']['bounds']['contains_hold']
    assert sorted(data.rglob('*')) == before


def test_create_versions_list_detail_model(data):
    r = create()
    assert r.status_code == 200 and r.json()['version'] == 1 and r.json()['verification'] == 'PASS' and not r.json()['builtin']
    assert create(prof=profile(2, name='Tàu thử bản 2')).status_code == 200
    items = client.get('/api/vessel-profiles').json()
    assert [(i['id'], i['version'], i['builtin']) for i in items] == [('TESTSHIP', 2, False), ('TESTSHIP', 1, False), ('VINAFCO268', 1, True)]
    assert all(i['status'] == 'AVAILABLE' and i['verification'] == 'PASS' for i in items)
    d = client.get('/api/vessel-profiles/TESTSHIP/2').json()
    assert d['profile']['name'] == 'Tàu thử bản 2' and d['glb_sha256'] == sha(glb()) and d['asset_url'] == '/api/vessel-profiles/TESTSHIP/2/model'
    assert d['viewer']['hull_box_m'] == [12, 0.01, 6] and d['viewer']['draft_markers'][0]['case_id'] == 'T-C1'
    assert d['profile_sha256'] == sha((data / 'vessels/TESTSHIP/v2/profile.json').read_bytes())
    model = client.get(d['asset_url'])
    assert model.content == glb() and model.headers['content-type'] == 'model/gltf-binary'
    built = client.get('/api/vessel-profiles/VINAFCO268/1').json()
    assert built['builtin'] and built['asset_url'] == '/api/vessels/vinafco268/model' and built['verification']['result'] == 'PASS'
    assert client.get(built['asset_url']).content == client.get('/api/vessel-profiles/VINAFCO268/1/model').content
    assert client.get('/api/vessel-profiles/TESTSHIP/3').status_code == 404
    assert client.get('/api/vessel-profiles/VINAFCO268/2').status_code == 404
    assert client.get('/api/vessel-profiles/nope/1').status_code == 404
    assert client.get('/api/vessel-profiles/TESTSHIP/1/cases/NOPE/plan').status_code == 404


def test_wrong_version_and_builtin_id_conflict_write_nothing(data):
    r = create(prof=profile(2))
    assert r.status_code == 409 and r.json()['detail']['latest_version'] == 0 and VIETNAMESE.search(r.json()['detail']['message'])
    assert not (data / 'vessels').exists()
    assert create().status_code == 200
    snapshot = tree(data)
    for v in (1, 3):
        r = create(prof=profile(v))
        assert r.status_code == 409 and r.json()['detail']['latest_version'] == 1
    r = create(prof=profile(ship='VINAFCO268'))
    assert r.status_code == 409 and VIETNAMESE.search(r.json()['detail']['message'])
    assert preview(prof=profile(ship='VINAFCO268')).json()['builtin_conflict'] is True
    assert tree(data) == snapshot


def test_store_limit_returns_409(data, monkeypatch):
    monkeypatch.setattr('app.adapters.vessel_profile_store.MAX_VERSIONS', 1)
    assert create().status_code == 200
    r = create(prof=profile(2))
    assert r.status_code == 409 and VIETNAMESE.search(r.json()['detail']['message'])


def test_verification_fail_is_rejected_and_nothing_written(data):
    off = profile()
    off['landmarks'][0]['hold_mm'][0] = 2  # 2 mm off, tolerance is 1 mm
    for call in (preview, create):
        r = call(prof=off)
        out = r.json() if call is preview else r.json()['detail']
        assert (r.status_code == 200) == (call is preview)
        assert out['verification']['result'] == 'FAIL' and not out['valid'] and not out['verification']['landmarks'][0]['pass']
        assert 1.5 < out['verification']['landmarks'][0]['error_mm'][0] < 2.5
    assert create(prof=off).status_code == 400
    outside = glb(((-4, 0, -3), (4, 4, 3)))  # hold spans x +-5 m
    r = create(glb_bytes=outside)
    assert r.status_code == 400 and r.json()['detail']['verification']['bounds']['contains_hold'] is False
    assert not (data / 'vessels').exists()


def test_tampered_stored_files_become_unavailable_and_are_not_repaired(data):
    assert create().status_code == 200 and create(prof=profile(2)).status_code == 200
    plan = user_plan(2)
    p1, g2 = data / 'vessels/TESTSHIP/v1/profile.json', data / 'vessels/TESTSHIP/v2/model.glb'
    p1.write_bytes(p1.read_bytes() + b' ')
    g2.write_bytes(g2.read_bytes() + b'\0')
    tampered = tree(data)
    items = {i['version']: i for i in client.get('/api/vessel-profiles').json() if not i['builtin']}
    assert all(i['status'] == 'UNAVAILABLE' and VIETNAMESE.search(i['integrity_error']) and i['verification'] is None for i in items.values())
    for v in (1, 2):
        base = f'/api/vessel-profiles/TESTSHIP/{v}'
        assert client.get(base).status_code == 400 and client.get(base + '/model').status_code == 400
        assert client.get(base + '/cases/T-C1/plan').status_code == 400
    r = client.post('/api/validate', json=plan)
    assert r.status_code == 422 and VIETNAMESE.search(r.json()['detail'])
    assert tree(data) == tampered
    assert create(prof=profile(3)).status_code == 200  # a new version is still appended, the broken ones stay as they are


@pytest.mark.parametrize('mutate', [bad_magic, bad_version, bad_total_length, non_json_first_chunk, lambda g: g[:30], lambda g: g[:8], lambda g: b''])
def test_malformed_glb_rejected(data, mutate):
    r = preview(glb_bytes=mutate(glb()))
    out = r.json()
    assert r.status_code == 200 and not out['valid'] and out['verification'] is None
    assert out['errors'][0]['field'] == 'glb' and VIETNAMESE.search(out['errors'][0]['message'])
    assert create(glb_bytes=mutate(glb())).status_code == 400
    assert not (data / 'vessels').exists()


def test_body_shape_errors_are_vietnamese_field_errors(data):
    cases = [
        ({'profile': profile(), 'glb_base64': '!!not base64!!'}, 'glb_base64'),
        ({'profile': profile(), 'glb_base64': 12}, 'glb_base64'),
        ({'profile': profile()}, 'glb_base64'),
        ({'glb_base64': ''}, 'profile'),
        ({'profile': [], 'glb_base64': ''}, 'profile'),
        (body(extra_field=1), 'extra_field'),
        (body(prof=profile(hold={**profile()['hold'], 'length_mm': 10000.5})), 'profile.hold.length_mm'),
        (body(prof={**profile(), 'surprise': 1}), 'profile.surprise'),
    ]
    for payload, field in cases:
        out = client.post('/api/vessel-profiles/preview', json=payload).json()
        assert not out['valid'] and field in [e['field'] for e in out['errors']], (field, out['errors'])
        assert all(VIETNAMESE.search(e['message']) for e in out['errors'])
        assert client.post('/api/vessel-profiles', json=payload).status_code == 400
    for raw in (b'not json', b'[]', b'"x"'):
        out = client.post('/api/vessel-profiles/preview', content=raw).json()
        assert out['errors'][0]['field'] == 'body' and not out['valid']
    assert not (data / 'vessels').exists()


def test_size_limits(data, monkeypatch):
    assert (service.MAX_BODY_BYTES, MAX_GLB_BYTES, MAX_PROFILE_BYTES) == (28 * 1024 * 1024, 20 * 1024 * 1024, 256 * 1024)
    # profile larger than 256 KiB
    big = profile(registration='x' * 49)
    big['notes'] = ['y' * 500] * 10
    big['extra'] = 'z' * MAX_PROFILE_BYTES
    out = preview(prof=big).json()
    assert [e['field'] for e in out['errors']] == ['profile'] and '256 KiB' in out['errors'][0]['message']
    # GLB larger than 20 MiB (valid header, so only the size rule can reject it)
    out = preview(glb_bytes=glb() + b'\0' * MAX_GLB_BYTES).json()
    assert out['errors'] == [{'field': 'glb', 'message': 'Tệp GLB vượt quá giới hạn 20 MiB.'}]
    # body larger than 28 MiB: by Content-Length header (small real body) and by actual length
    for call in (client.post,):
        r = call('/api/vessel-profiles/preview', content=b'{}', headers={'Content-Length': str(service.MAX_BODY_BYTES + 1)})
        assert r.status_code == 413 and r.json()['detail']['errors'][0]['field'] == 'body'
        r = call('/api/vessel-profiles', content=b' ' * (service.MAX_BODY_BYTES + 1))
        assert r.status_code == 413
    assert service.body_size_errors(service.MAX_BODY_BYTES) == [] and service.body_size_errors(service.MAX_BODY_BYTES + 1)
    assert service.preview(b' ' * (service.MAX_BODY_BYTES + 1))['errors'][0]['field'] == 'body'
    assert not (data / 'vessels').exists()


# ------------------------------------------------------------------ plan references at every entry point (D4.3)
def v1_plan_from(plan):
    r = client.post('/api/pipe-list/preview', json=plan)
    assert r.status_code == 200, r.text
    return r.json()['plan']


ENTRY_POINTS = {
    'validate': (lambda p: client.post('/api/validate', json=p), 422),
    'save': (lambda p: client.post('/api/snapshots', json={'name': 'x', 'plan': p}), 400),
    'compare_before': (lambda p: client.post('/api/plans/compare', json={'before': p, 'after': client.get('/api/demo').json()['plan']}), 422),
    'compare_after': (lambda p: client.post('/api/plans/compare', json={'before': client.get('/api/demo').json()['plan'], 'after': p}), 422),
    'planner': (lambda p: client.post('/api/planner/preview', json=p), 422),
    'pipe_list': (lambda p: client.post('/api/pipe-list/preview', json=p), 422),
    'csv': (lambda p: client.post('/api/import/csv/preview', json={'plan': p, 'csv_text': CSV}), 422),
    'plan_preview': (lambda p: client.post('/api/cargo-revisions/BALTIMORE-PIPE-V1-1@R0000/plan-preview', json=p), 422),
}


def _break(plan, kind):
    plan = deepcopy(plan)
    if kind == 'unknown_profile':
        plan['vessel']['vessel_id'] = 'NOSUCHSHIP'
    elif kind == 'unknown_version':
        plan['vessel']['profile_version'] = 9
    elif kind == 'wrong_sha':
        plan['vessel']['profile_sha256'] = 'f' * 64
    elif kind == 'wrong_hold':
        plan['hold']['length_mm'] += 1
    elif kind == 'wrong_hold_name':
        plan['hold']['name'] = 'Hầm khác'
    elif kind == 'unknown_case':
        plan['vessel']['case_id'] = 'T-C9'
    elif kind == 'wrong_limit':
        plan['limits']['certificate_cargo_limit_g'] += 1
    elif kind == 'other_case_limit':
        plan['limits']['certificate_cargo_limit_g'] = 4_000_000_000  # belongs to T-C2, not T-C1
        plan['limits']['voyage_cargo_limit_g'] = 4_000_000_000
    return plan


BREAKS = ['unknown_profile', 'unknown_version', 'wrong_sha', 'wrong_hold', 'wrong_hold_name', 'unknown_case', 'wrong_limit', 'other_case_limit']


@pytest.fixture
def mine(data):
    assert create().status_code == 200
    return user_plan()


def test_correct_user_profile_plan_accepted_everywhere(data, mine):
    for name, (call, _) in ENTRY_POINTS.items():
        assert call(mine).status_code == 200, name
    other_case = user_plan(case='T-C2')
    assert other_case['limits']['certificate_cargo_limit_g'] == 4_000_000_000
    assert client.post('/api/validate', json=other_case).status_code == 200
    sid = client.post('/api/snapshots', json={'name': 'Tàu thử', 'plan': mine}).json()['id']
    opened = client.get('/api/snapshots/' + sid)
    assert opened.status_code == 200 and opened.json()['plan'] == mine
    with sqlite3.connect(data / 'scst.sqlite3') as con:
        assert json.loads(con.execute('SELECT plan_json FROM snapshots WHERE id=?', (sid,)).fetchone()[0])['vessel'] == mine['vessel']


@pytest.mark.parametrize('kind', BREAKS)
@pytest.mark.parametrize('entry', list(ENTRY_POINTS))
def test_bad_user_profile_reference_rejected_at_every_entry_point(data, mine, entry, kind):
    call, status = ENTRY_POINTS[entry]
    before = tree(data)
    r = call(_break(mine, kind))
    assert r.status_code == status, r.text
    assert VIETNAMESE.search(str(r.json()['detail']))
    assert tree(data) == before
    if entry == 'save':
        assert not (data / 'scst.sqlite3').exists() or not sqlite3.connect(data / 'scst.sqlite3').execute('SELECT 1 FROM snapshots').fetchall()


def test_snapshot_open_and_rebase_check_profile_and_never_modify_snapshot(data, mine):
    plan = v1_plan_from(mine)
    sid = client.post('/api/snapshots', json={'name': 'Danh sách ống', 'plan': plan}).json()['id']

    def stored():
        with sqlite3.connect(data / 'scst.sqlite3') as con:
            return con.execute('SELECT plan_json FROM snapshots WHERE id=?', (sid,)).fetchone()[0]
    saved = stored()
    assert client.get('/api/snapshots/' + sid).status_code == 200
    assert client.post(f'/api/snapshots/{sid}/rebase').status_code == 200
    assert stored() == saved
    path = data / 'vessels/TESTSHIP/v1/profile.json'
    path.write_bytes(path.read_bytes() + b' ')
    for r in (client.get('/api/snapshots/' + sid), client.post(f'/api/snapshots/{sid}/rebase')):
        assert r.status_code == 400 and VIETNAMESE.search(r.json()['detail'])
    assert client.get('/api/snapshots').status_code == 200  # listing never binds
    assert stored() == saved


def test_compare_context_has_profile_leaves_only_for_user_profiles(mine):
    vin = client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan']
    r = client.post('/api/plans/compare', json={'before': vin, 'after': vin}).json()
    assert r['context_changes'] == []
    r = client.post('/api/plans/compare', json={'before': mine, 'after': _break(mine, 'wrong_sha')})
    assert r.status_code == 422
    other = user_plan(case='T-C2')
    fields = {c['field'] for c in client.post('/api/plans/compare', json={'before': mine, 'after': other}).json()['context_changes']}
    assert 'vessel.case_id' in fields and 'vessel.profile_sha256' not in fields
    changes = client.post('/api/plans/compare', json={'before': vin, 'after': mine}).json()['context_changes']
    assert {'vessel.profile_version', 'vessel.profile_sha256'} <= {c['field'] for c in changes}
