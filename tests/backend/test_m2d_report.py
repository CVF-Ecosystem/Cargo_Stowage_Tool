"""M2d backend acceptance (M2D-01, M2D-02): the plan report model and its read-only API.
Every test uses a temporary SCST_DATA_DIR; the XLSX writer itself is covered elsewhere (only headers are checked here)."""
import base64
import hashlib
import json
import re
import sqlite3
import time
from copy import deepcopy
from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

from app.adapters import report_service
from app.adapters.storage import open_migrated
from app.domain import cargo_revisions as cr
from app.domain.model import Plan
from app.domain.report import ReportReconciliationError, mm3_text, reconcile, report_hash, xlsx
from app.domain.rules import evaluate
from app.main import app
from glb_fixture import make_glb

client = TestClient(app)
R0 = cr.BASE_REVISION_ID
R1, R2 = cr.revision_id(1), cr.revision_id(2)
BASE_SHA = '9392efc3fd93d9b56e2bfddb2cf45c73d04755d7fe1003092b09fca5250449a4'
VIETNAMESE = re.compile('[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.I)
G2 = 'Sheet1-R002'
SOURCE = {'kind': 'FACTORY', 'reference': 'PO-2026-11 / chứng từ nhà máy', 'received_date': '2026-11-02', 'note': 'cân thực tế'}
NOTICE_TEXT = {
    'SINGLE_LAYER': 'Phương án một tầng (xếp sơ bộ, chưa tối ưu).',
    'PACKING_DERIVED': 'Packing là dẫn xuất, không phải số đo thực.',
    'GEOMETRY_ESTIMATED': 'Chưa xác minh hình học: kích thước hầm là ước tính (chưa đo thực tế).',
    'GEOMETRY_UNCONFIRMED': 'Chưa xác minh hình học: kích thước hầm là chưa xác nhận (chưa đo thực tế).',
    'SOURCE_WARNING': 'Cảnh báo dữ liệu nguồn: các nhóm Sheet1-R022, Sheet1-R031, Sheet1-R032 có cảnh báo kích thước nguồn.',
    'NOT_OPERATIONAL': 'Chưa đủ điều kiện vận hành; các mục chưa kiểm: Kê, chèn và chằng buộc · Chất xếp nhiều tầng · '
                       'Ổn định phương tiện · Tải cục bộ đáy hầm · Hàng cũ trong hầm mục tiêu.',
    'REVISION_UNAVAILABLE': 'Không kiểm lại được theo revision mới nhất; dữ liệu revision không phục vụ được.',
}


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


# ------------------------------------------------------------------ helpers
def db(data):
    return sqlite3.connect(data / 'scst.sqlite3')


def stored_json(data, sid):
    con = db(data)
    try:
        return con.execute('SELECT plan_json FROM snapshots WHERE id=?', (sid,)).fetchone()[0]
    finally:
        con.close()


def tree(data):
    return {str(p.relative_to(data)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(data.rglob('*')) if p.is_file()}


def insert_raw(data, sid, plan_json, schema='scst.saved-plan.v1', name='Hàng SQL'):
    con = open_migrated()
    try:
        con.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)', (sid, name, '2026-01-01T00:00:00+00:00', schema, plan_json))
        con.commit()
    finally:
        con.close()


def base_plan():
    return client.get('/api/demo').json()['plan']


def roomy(plan):
    plan['hold'].update(length_mm=20000, width_mm=9000, height_mm=4000)
    plan['limits'].update(certificate_cargo_limit_g=10 ** 10, voyage_cargo_limit_g=10 ** 10, cargo_onboard_g=0)
    return plan


def place(plan, *pairs):
    plan['placements'] = [dict(unit_id=u, x_mm=0, y_mm=y, z_mm=0, layer=0, supported_by=[], yaw_deg=0) for u, y in pairs]
    return plan


def save(plan, name='Phương án thử'):
    r = client.post('/api/snapshots', json={'name': name, 'plan': plan})
    assert r.status_code == 200, r.text
    return r.json()['id']


def report(sid):
    r = client.get(f'/api/snapshots/{sid}/report')
    assert r.status_code == 200, r.text
    return r.json()


def latest_id():
    return client.get('/api/cargo-revisions').json()['latest_revision_id']


def create_revision(changes, parent=None):
    r = client.post('/api/cargo-revisions', json={'parent_revision_id': parent or latest_id(), 'source': SOURCE, 'changes': changes})
    assert r.status_code == 200, r.text


def update(group, confirmation='CONFIRMED', **fields):
    return {'type': 'UPDATE_GROUP', 'group_id': group, 'confirmation': confirmation, 'set': fields}


def add_group(count=2):
    return {'type': 'ADD_GROUP', 'confirmation': 'UNVERIFIED',
            'group': {'bundle_count': count, 'pieces_per_bundle': 10, 'dimensions_um': [6000000, 300000, 300000], 'mass_g': 500000,
                      'outside_diameter_mm': '60.3', 'wall_thickness_mm': '3.91', 'dimension_warning': False}}


def v2_plan(revision, *pairs):
    r = client.post(f'/api/cargo-revisions/{revision}/plan-preview', json=roomy(base_plan()))
    assert r.status_code == 200, r.text
    return place(r.json()['plan'], *pairs)


def vinafco_pipe_plan():
    """Pipe list v1 in the VINAFCO hold, placed by the suggestion planner (167 of 1076 bundles)."""
    plan = client.get('/api/vessels/vinafco268/cases/VR-SI/plan').json()['plan']
    plan = client.post('/api/pipe-list/preview', json=plan).json()['plan']
    r = client.post('/api/planner/preview', json=plan)
    assert r.status_code == 200, r.text
    return r.json()['evaluation']['plan']


def m2a_plan():
    text = ('id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\n'
            'A,Bó đặt,BAR_BUNDLE,required,1000,500,300,12.5\nB,Bó tùy chọn,BAR_BUNDLE,optional,2000,500,300,20\n'
            'C,Bó loại,BAR_BUNDLE,excluded,1000,400,300,5\nD,Bó bắt buộc chưa đặt,BAR_BUNDLE,required,900,400,300,7.25\n')
    r = client.post('/api/import/csv/preview', json={'plan': base_plan(), 'csv_text': text}).json()
    assert r['valid'], r
    return place(r['candidate'], ('A', 0))


def glb():
    return make_glb([((-6, 0, -3), (6, 4, 3))])


def ship_profile(version=1, hold_status='ESTIMATED'):
    corners = [(-5, -2, 0, 0), (5, -2, 10000, 0), (-5, 2, 0, 4000), (5, 2, 10000, 4000)]
    return {
        'contract_version': 'scst.vessel-profile.v1', 'id': 'TESTSHIP', 'version': version, 'name': 'Tàu thử', 'registration': 'T-1',
        'dimensions_m': {'length': 12, 'beam': 6, 'depth': 4},
        'hold': {'id': 'HOLD-T1', 'name': 'Hầm thử', 'length_mm': 10000, 'width_mm': 4000, 'height_mm': 3000, 'status': hold_status},
        'cases': [{'id': 'T-C1', 'cargo_mass_g': 5_000_000_000, 'draft_m': 2.0}],
        'notes': [], 'provenance': {'source_documents': [{'title': 'Tài liệu thử'}],
                                   'field_status': {'dimensions_m': 'SOURCED', 'hold': hold_status, 'cases': 'ESTIMATED'}},
        'transform': {'translation_m': [0, 0, 0], 'yaw_deg': 0},
        'landmarks': [{'name': f'Góc {i}', 'glb_m': [x, 0, z], 'hold_mm': [hx, hy, 0]} for i, (x, z, hx, hy) in enumerate(corners)]}


def user_ship_plan(hold_status='ESTIMATED'):
    body = {'profile': ship_profile(hold_status=hold_status), 'glb_base64': base64.b64encode(glb()).decode()}
    assert client.post('/api/vessel-profiles', json=body).status_code == 200
    r = client.get('/api/vessel-profiles/TESTSHIP/1/cases/T-C1/plan')
    assert r.status_code == 200, r.text
    return r.json()['plan']


def expected_hash(r):
    body = {k: v for k, v in r.items() if k != 'report_sha256'}
    body['header'] = {k: v for k, v in r['header'].items() if k != 'generated_utc'}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def no_floats(value):
    if isinstance(value, dict):
        return all(no_floats(v) for v in value.values())
    if isinstance(value, list):
        return all(no_floats(v) for v in value)
    return not isinstance(value, float)


def codes(r):
    return [n['code'] for n in r['notices']]


def assert_units_match_stored(r, stored):
    """D1.2 'units': every exact value equals the stored plan (mm, um, g, placement), same order."""
    plan = json.loads(stored)
    placed = {p['unit_id']: p for p in plan['placements']}
    assert [u['id'] for u in r['units']] == [u['id'] for u in plan['units']]
    for got, want in zip(r['units'], plan['units']):
        ref = want.get('source_ref')
        assert (got['name'], got['kind'], got['requirement']) == (want['name'], want['kind'], want['requirement'])
        assert (got['length_mm'], got['width_mm'], got['height_mm'], got['mass_g']) == (want['length_mm'], want['width_mm'], want['height_mm'], want['mass_g'])
        assert got['dimensions_um'] == (want.get('dimensions_um') or [want['length_mm'] * 1000, want['width_mm'] * 1000, want['height_mm'] * 1000])
        assert got['group_id'] == (ref['group_id'] if ref else None) and got['source_row'] == (ref['source_row'] if ref else None)
        assert got['revision_id'] == (ref.get('revision_id') if ref else None) and got['confirmation'] == (ref.get('confirmation') if ref else None)
        assert got['dimension_warning'] is bool(ref and ref['dimension_warning'])
        p = placed.get(want['id'])
        if p is None:
            assert got['placement'] is None and got['status'] == ('EXCLUDED' if want['requirement'] == 'excluded' else 'UNPLACED')
        else:
            assert got['status'] == 'PLACED'
            assert got['placement'] == {k: p[k] for k in ('x_mm', 'y_mm', 'z_mm', 'layer', 'yaw_deg')}
        assert (got['packing'] is not None) == bool(ref and want['kind'] == 'PIPE_BUNDLE')


# ------------------------------------------------------------------ (a) M1 demo
def test_m1_demo_report(data):
    plan = base_plan()
    sid = save(plan, 'Demo M1')
    r = report(sid)
    assert r['schema_version'] == 'scst.plan-report.v1' and list(r)[:3] == ['schema_version', 'report_sha256', 'header']
    assert r['header']['plan_name'] == 'Demo M1' and r['header']['snapshot_id'] == sid
    assert r['header']['schema_version'] == 'scst.saved-plan.v1' and r['header']['contract_version'] == 'scst.m1.v1'
    assert r['vessel'] is None and r['hold']['status'] == 'UNCONFIRMED' and r['hold']['id'] == plan['hold']['id']
    assert r['cargo']['revision_id'] is None and r['cargo']['content_sha256'] is None and r['cargo']['dataset_id'] is None
    assert r['cargo']['recheck'] == {'status': 'NOT_APPLICABLE', 'latest_revision_id': None, 'added': 0, 'removed': 0, 'changed': 0, 'placed_affected': 0}
    # PACKING_DERIVED is keyed on a pipe list (units with a source group); synthetic PIPE_BUNDLE demo units carry none
    assert codes(r) == ['GEOMETRY_UNVERIFIED', 'SINGLE_LAYER', 'NOT_OPERATIONAL']
    assert r['notices'][0]['message'] == NOTICE_TEXT['GEOMETRY_UNCONFIRMED'] and all(u['packing'] is None for u in r['units'])
    ev = client.get('/api/demo').json()
    t = r['totals']
    assert (t['manifest_mass_g'], t['placed_mass_g'], t['remaining_capacity_g'], t['placed_count']) == \
        tuple(ev['summary'][k] for k in ('manifest_mass_g', 'placed_mass_g', 'remaining_capacity_g', 'placed_count'))
    assert t['unit_count'] == t['placed_count'] + t['unplaced_count'] + t['excluded_count'] == len(plan['units'])
    assert r['limits']['available_capacity_g'] == plan['limits']['voyage_cargo_limit_g'] - plan['limits']['cargo_onboard_g']
    assert r['issues']['status'] == ev['status'] and r['issues']['operational_eligible'] is False
    assert [i['code'] for i in r['issues']['items']] == [i['code'] for i in ev['issues']]
    assert_units_match_stored(r, stored_json(data, sid))
    assert no_floats(r)


# ------------------------------------------------------------------ (b) M2a user-entered
def test_m2a_report_statuses_reasons_and_exact_volume(data):
    sid = save(m2a_plan(), 'Nhập tay')
    r = report(sid)
    assert r['header']['contract_version'] == 'scst.m2a.v1' and r['cargo']['plan_source'] == m2a_plan()['source']
    assert r['cargo']['cargo_source'] == 'USER_ENTERED' and r['vessel'] is None
    assert [u['status'] for u in r['units']] == ['PLACED', 'UNPLACED', 'EXCLUDED', 'UNPLACED']
    assert r['units'][0]['placement'] == {'x_mm': 0, 'y_mm': 0, 'z_mm': 0, 'layer': 0, 'yaw_deg': 0}
    assert [(u['id'], u['status'], u['reason_code'], u['requirement']) for u in r['unplaced']] == [
        ('B', 'UNPLACED', 'OPTIONAL_UNPLACED', 'optional'), ('C', 'EXCLUDED', 'EXCLUDED', 'excluded'), ('D', 'UNPLACED', 'REQUIRED_UNPLACED', 'required')]
    assert r['unplaced'][0]['reason'].startswith('Tùy chọn, chưa xếp') and r['unplaced'][1]['reason'] == 'Bó được loại trừ khỏi xếp.'
    assert r['unplaced'][2]['reason'] == 'Hàng bắt buộc chưa được xếp.'
    t = r['totals']
    assert (t['unit_count'], t['placed_count'], t['unplaced_count'], t['excluded_count']) == (4, 1, 2, 1)
    assert (t['manifest_mass_g'], t['placed_mass_g']) == (12500 + 20000 + 5000 + 7250, 12500)
    assert t['placed_envelope_volume_mm3'] == 1000 * 500 * 300 and t['placed_envelope_volume_mm3_text'] == '150000000'
    assert t['manifest_envelope_volume_mm3'] == 1000 * 500 * 300 + 2000 * 500 * 300 + 1000 * 400 * 300 + 900 * 400 * 300
    assert [i['code'] for i in r['issues']['items']] == ['REQUIRED_UNPLACED'] and r['issues']['items'][0]['unit_ids'] == ['D']
    assert r['issues']['total_issues'] == 1 and r['issues']['issues_truncated'] is False
    assert 'PACKING_DERIVED' not in codes(r) and all(u['packing'] is None for u in r['units'])
    assert_units_match_stored(r, stored_json(data, sid))


def test_volume_text_is_exact_decimal():
    assert mm3_text(0) == '0' and mm3_text(10 ** 9) == '1' and mm3_text(638350934400000000) == '638350934.4'
    assert mm3_text(1) == '0.000000001' and mm3_text(123 * 10 ** 9 + 450_000_000) == '123.45'


# ------------------------------------------------------------------ (c)+(e) pipe list v1 in the VINAFCO hold
def test_pipe_v1_vinafco_report_notices_and_packing(data):
    plan = vinafco_pipe_plan()
    sid = save(plan, 'Ống VINAFCO')
    r = report(sid)
    stored = stored_json(data, sid)
    assert r['header']['contract_version'] == 'scst.pipe-list.v1' and r['header']['plan_sha256'] == hashlib.sha256(stored.encode()).hexdigest()
    assert r['vessel'] == {'vessel_id': 'VINAFCO268', 'name': 'VINAFCO 268', 'case_id': 'VR-SI', 'builtin': True, 'profile_version': None,
                           'profile_sha256': None, 'field_status': {'dimensions_m': 'SOURCED', 'hold': 'ESTIMATED', 'cases': 'SOURCED'}}
    assert r['hold']['status'] == 'ESTIMATED' and r['hold']['length_mm'] == 56405
    assert r['cargo']['dataset_id'] == 'BALTIMORE-PIPE-V1-1' and r['cargo']['revision_id'] == R0 and r['cargo']['content_sha256'] == BASE_SHA
    assert r['cargo']['recheck'] == {'status': 'CURRENT', 'latest_revision_id': R0, 'added': 0, 'removed': 0, 'changed': 0, 'placed_affected': 0}
    assert [(n['code'], n['message']) for n in r['notices']] == [
        ('GEOMETRY_UNVERIFIED', NOTICE_TEXT['GEOMETRY_ESTIMATED']), ('SINGLE_LAYER', NOTICE_TEXT['SINGLE_LAYER']),
        ('PACKING_DERIVED', NOTICE_TEXT['PACKING_DERIVED']), ('SOURCE_WARNING', NOTICE_TEXT['SOURCE_WARNING']),
        ('NOT_OPERATIONAL', NOTICE_TEXT['NOT_OPERATIONAL'])]
    t = r['totals']
    assert t['unit_count'] == 1076 and t['placed_count'] == len(plan['placements']) > 0
    assert t['unplaced_count'] == 1076 - t['placed_count'] and t['excluded_count'] == 0 and len(r['unplaced']) == t['unplaced_count']
    assert t['manifest_mass_g'] == sum(u['mass_g'] for u in plan['units'])
    assert t['manifest_envelope_volume_mm3'] is None or isinstance(t['manifest_envelope_volume_mm3'], int)
    assert '.' in t['manifest_envelope_volume_mm3_text'] or t['manifest_envelope_volume_mm3'] is not None
    pk = client.get(f'/api/cargo-revisions/{R0}/packing').json()
    by_group = {g['group_id']: g for g in pk['groups']}
    for u in r['units']:
        g = by_group[u['group_id']]
        assert u['packing'] == {'status': g['status'], 'layout': g['layout'], 'columns': g['columns'], 'rows': g['rows'],
                                'pieces_placed': g['pieces_placed'], 'pieces_source': g['pieces_source'],
                                'reason_codes': [x['code'] for x in g['reasons']]}
    assert {u['packing']['status'] for u in r['units']} == {'DETAILED', 'ENVELOPE_ONLY'}
    assert_units_match_stored(r, stored)
    assert no_floats(r)


def test_vinafco_case_plan_has_no_packing_and_no_pipe_revision():
    sid = save(client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan'], 'Case SII')
    r = report(sid)
    assert r['vessel']['builtin'] and r['vessel']['profile_version'] is None and r['vessel']['case_id'] == 'VR-SII'
    assert 'PACKING_DERIVED' not in codes(r) and r['hold']['status'] == 'ESTIMATED' and all(u['packing'] is None for u in r['units'])


# ------------------------------------------------------------------ (d) pinned v2 and recheck
def test_v2_pinned_old_revision_needs_recheck_after_new_revision(data):
    sid = save(v2_plan(R0, ('PIPE-R002-B0001', 0), ('PIPE-R004-B0001', 400)), 'Ghim R0')
    before = report(sid)
    assert before['cargo']['revision_id'] == R0 and before['cargo']['recheck']['status'] == 'CURRENT'
    assert 'NEEDS_RECHECK' not in codes(before)
    create_revision([update(G2, mass_g=900000), add_group(2)])
    after = report(sid)
    listing = next(i for i in client.get('/api/snapshots').json() if i['id'] == sid)
    c = after['cargo']['recheck']
    assert c['status'] == 'NEEDS_RECHECK' == listing['recheck_status'] and c['latest_revision_id'] == R1
    assert (c['added'], c['removed'], c['changed'], c['placed_affected']) == \
        (listing['added_count'], listing['removed_count'], listing['changed_count'], listing['placed_affected_count'])
    assert c['added'] == 2 and c['changed'] > 0 and c['placed_affected'] == 1
    notice = next(n for n in after['notices'] if n['code'] == 'NEEDS_RECHECK')
    assert notice['message'] == (f'Phương án cần kiểm lại theo dữ liệu mới: {R1} '
                                 f'(thêm {c["added"]}, bỏ {c["removed"]}, đổi {c["changed"]} bó; {c["placed_affected"]} bó đã đặt bị ảnh hưởng).')
    assert codes(after).index('PACKING_DERIVED') < codes(after).index('NEEDS_RECHECK') < codes(after).index('NOT_OPERATIONAL')
    assert after['cargo']['revision_id'] == R0 and after['cargo']['content_sha256'] == BASE_SHA
    assert after['header']['plan_sha256'] == before['header']['plan_sha256']
    assert_units_match_stored(after, stored_json(data, sid))
    # a plan pinned to the new revision is CURRENT and its units carry revision and confirmation
    sid1 = save(v2_plan(R1, ('PIPE-R002-B0001', 0)), 'Ghim R1')
    r1 = report(sid1)
    assert r1['cargo']['revision_id'] == R1 and r1['cargo']['recheck']['status'] == 'CURRENT' and r1['cargo']['recheck']['latest_revision_id'] == R1
    changed = next(u for u in r1['units'] if u['group_id'] == G2)
    assert (changed['revision_id'], changed['confirmation']) == (R1, 'CONFIRMED') and changed['mass_g'] == 900000
    assert_units_match_stored(r1, stored_json(data, sid1))


def test_bundle_override_packing_follows_pinned_revision():
    create_revision([{'type': 'BUNDLE_OVERRIDE', 'bundle_id': 'PIPE-R002-B0001', 'confirmation': 'CONFIRMED',
                      'set': {'dimensions_um': [6401000, 90000, 90000]}}])
    r = report(save(v2_plan(R1, ('PIPE-R002-B0001', 0)), 'Override'))
    pk = client.get(f'/api/cargo-revisions/{R1}/packing').json()
    group = next(g for g in pk['groups'] if g['group_id'] == G2)
    own = group['bundle_packings'][0]
    assert own['bundle_id'] == 'PIPE-R002-B0001'
    first, second = (next(u for u in r['units'] if u['id'] == i) for i in ('PIPE-R002-B0001', 'PIPE-R002-B0002'))
    assert first['dimensions_um'] == [6401000, 90000, 90000] and first['packing']['status'] == own['status'] == 'ENVELOPE_ONLY'
    assert first['packing']['reason_codes'] == [x['code'] for x in own['reasons']]
    assert second['packing']['status'] == group['status'] == 'DETAILED' and second['packing']['pieces_placed'] == group['pieces_placed']


def test_revision_unavailable_when_latest_revision_is_broken(data):
    sid = save(v2_plan(R0, ('PIPE-R002-B0001', 0)), 'Ghim R0')
    create_revision([update(G2, mass_g=900000)])
    con = db(data)
    con.execute('UPDATE cargo_revisions SET content_sha256=? WHERE revision_id=?', ('0' * 64, R1))
    con.commit()
    con.close()
    r = report(sid)
    assert r['cargo']['recheck'] == {'status': 'REVISION_UNAVAILABLE', 'latest_revision_id': None, 'added': 0, 'removed': 0, 'changed': 0, 'placed_affected': 0}
    assert [n['message'] for n in r['notices'] if n['code'] == 'REVISION_UNAVAILABLE'] == [NOTICE_TEXT['REVISION_UNAVAILABLE']]
    assert 'NEEDS_RECHECK' not in codes(r)


# ------------------------------------------------------------------ (f) user vessel profile
def test_user_vessel_profile_report():
    plan = user_ship_plan()
    detail = client.get('/api/vessel-profiles/TESTSHIP/1').json()
    r = report(save(plan, 'Tàu người dùng'))
    assert r['vessel'] == {'vessel_id': 'TESTSHIP', 'name': 'Tàu thử', 'case_id': 'T-C1', 'builtin': False, 'profile_version': 1,
                           'profile_sha256': detail['profile_sha256'], 'field_status': {'dimensions_m': 'SOURCED', 'hold': 'ESTIMATED', 'cases': 'ESTIMATED'}}
    assert r['hold'] == {'id': 'HOLD-T1', 'name': 'Hầm thử', 'length_mm': 10000, 'width_mm': 4000, 'height_mm': 3000, 'status': 'ESTIMATED'}
    assert r['limits']['certificate_cargo_limit_g'] == 5_000_000_000 and 'GEOMETRY_UNVERIFIED' in codes(r)


def test_measured_hold_has_no_geometry_notice():
    r = report(save(user_ship_plan('MEASURED'), 'Đã đo'))
    assert r['hold']['status'] == 'MEASURED' and r['vessel']['field_status']['hold'] == 'MEASURED'
    assert 'GEOMETRY_UNVERIFIED' not in codes(r) and codes(r)[0] == 'SINGLE_LAYER' and codes(r)[-1] == 'NOT_OPERATIONAL'


# ------------------------------------------------------------------ (g) hash
def test_report_sha256_is_stable_and_excludes_generated_utc():
    sid = save(vinafco_pipe_plan())
    a, b = report(sid), report(sid)
    assert a['report_sha256'] == b['report_sha256'] == expected_hash(a) == report_hash(a)
    assert a['header']['generated_utc'] and a['header']['generated_utc'].endswith('+00:00')
    b['header']['generated_utc'] = 'x'
    assert expected_hash(b) == a['report_sha256']
    assert len(a['report_sha256']) == 64 and no_floats(a)


def test_report_sha256_changes_with_latest_revision_but_not_without():
    sid = save(v2_plan(R0, ('PIPE-R002-B0001', 0)))
    first = report(sid)['report_sha256']
    assert report(sid)['report_sha256'] == first
    create_revision([update(G2, mass_g=900000)])
    second = report(sid)
    assert second['report_sha256'] != first and second['report_sha256'] == expected_hash(second)


# ------------------------------------------------------------------ (h) read-only
def test_reports_never_change_snapshot_rows_or_database_bytes(data, monkeypatch):
    monkeypatch.setattr(xlsx, 'write_xlsx', lambda r: b'PK')
    ids = [save(base_plan(), 'm1'), save(m2a_plan(), 'm2a'), save(vinafco_pipe_plan(), 'v1'), save(v2_plan(R0, ('PIPE-R002-B0001', 0)), 'v2')]
    create_revision([update(G2, mass_g=900000)])
    con = db(data)
    rows = con.execute('SELECT * FROM snapshots ORDER BY id').fetchall()
    revs = con.execute('SELECT * FROM cargo_revisions ORDER BY rowid').fetchall()
    con.close()
    files = tree(data)
    for sid in ids:
        assert client.get(f'/api/snapshots/{sid}/report').status_code == 200
        assert client.get(f'/api/snapshots/{sid}/report.xlsx').status_code == 200
    con = db(data)
    assert con.execute('SELECT * FROM snapshots ORDER BY id').fetchall() == rows
    assert con.execute('SELECT * FROM cargo_revisions ORDER BY rowid').fetchall() == revs
    con.close()
    assert tree(data) == files  # includes the sqlite file bytes; no journal or other file appears


# ------------------------------------------------------------------ (i) refusals
def test_invalid_unknown_and_unsupported_snapshots(data):
    for path in ('report', 'report.xlsx'):
        bad = client.get(f'/api/snapshots/not-a-uuid/{path}')
        assert bad.status_code == 400 and VIETNAMESE.search(bad.json()['detail'])
        assert client.get(f'/api/snapshots/AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA/{path}').status_code == 400  # not the canonical lower-case form
        unknown = client.get(f'/api/snapshots/11111111-1111-4111-8111-111111111111/{path}')
        assert unknown.status_code == 404 and VIETNAMESE.search(unknown.json()['detail'])
    insert_raw(data, '22222222-2222-4222-8222-222222222222', json.dumps(base_plan()), schema='unknown')
    insert_raw(data, '33333333-3333-4333-8333-333333333333', '{"not":"a plan"}')
    insert_raw(data, '44444444-4444-4444-8444-444444444444', 'not json')
    for sid in ('22222222-2222-4222-8222-222222222222', '33333333-3333-4333-8333-333333333333', '44444444-4444-4444-8444-444444444444'):
        r = client.get(f'/api/snapshots/{sid}/report')
        assert r.status_code == 400 and VIETNAMESE.search(r.json()['detail']), r.text


def test_pinned_revision_integrity_failure_is_refused(data):
    create_revision([update(G2, mass_g=900000)])
    sid = save(v2_plan(R1, ('PIPE-R002-B0001', 0)), 'Ghim R1')
    con = db(data)
    con.execute('UPDATE cargo_revisions SET content_sha256=? WHERE revision_id=?', ('0' * 64, R1))
    con.commit()
    con.close()
    before = tree(data)
    for path in ('report', 'report.xlsx'):
        r = client.get(f'/api/snapshots/{sid}/{path}')
        assert r.status_code == 400 and VIETNAMESE.search(r.json()['detail']), r.text
    assert tree(data) == before


def test_unknown_pinned_revision_and_tampered_plan_are_refused(data):
    create_revision([update(G2, mass_g=900000)])
    plan = v2_plan(R1, ('PIPE-R002-B0001', 0))
    plan['units'][0]['mass_g'] += 1  # stored list no longer matches the pinned revision
    insert_raw(data, '55555555-5555-4555-8555-555555555555', json.dumps(plan))
    r = client.get('/api/snapshots/55555555-5555-4555-8555-555555555555/report')
    assert r.status_code == 400 and VIETNAMESE.search(r.json()['detail'])


def test_tampered_user_profile_sha_and_profile_file_are_refused(data):
    plan = user_ship_plan()
    bad = deepcopy(plan)
    bad['vessel']['profile_sha256'] = '0' * 64
    insert_raw(data, '66666666-6666-4666-8666-666666666666', json.dumps(bad))
    sid = save(plan, 'Tàu người dùng')
    assert client.get(f'/api/snapshots/{sid}/report').status_code == 200
    for path in ('report', 'report.xlsx'):
        r = client.get(f'/api/snapshots/66666666-6666-4666-8666-666666666666/{path}')
        assert r.status_code == 400 and VIETNAMESE.search(r.json()['detail'])
    profile_file = data / 'vessels' / 'TESTSHIP' / 'v1' / 'profile.json'
    profile_file.write_bytes(profile_file.read_bytes() + b' ')
    r = client.get(f'/api/snapshots/{sid}/report')
    assert r.status_code == 400 and VIETNAMESE.search(r.json()['detail'])


# ------------------------------------------------------------------ (j) reconciliation
def _loaded(sid, data):
    plan = Plan.model_validate(json.loads(stored_json(data, sid)))
    return deepcopy(report(sid)), evaluate(plan)


MUTATIONS = {
    'placed_mass': lambda r: r['totals'].__setitem__('placed_mass_g', r['totals']['placed_mass_g'] + 1),
    'manifest_mass': lambda r: r['totals'].__setitem__('manifest_mass_g', r['totals']['manifest_mass_g'] - 1),
    'remaining': lambda r: r['totals'].__setitem__('remaining_capacity_g', r['totals']['remaining_capacity_g'] + 1),
    'counts_sum': lambda r: r['totals'].__setitem__('excluded_count', r['totals']['excluded_count'] + 1),
    'placed_count': lambda r: r['totals'].update(placed_count=r['totals']['placed_count'] + 1, unplaced_count=r['totals']['unplaced_count'] - 1),
    'unit_count': lambda r: r['totals'].__setitem__('unit_count', r['totals']['unit_count'] + 1),
    'unit_mass': lambda r: r['units'][0].__setitem__('mass_g', r['units'][0]['mass_g'] + 1),
    'unit_status': lambda r: r['units'][0].__setitem__('status', 'EXCLUDED' if r['units'][0]['status'] != 'EXCLUDED' else 'PLACED'),
    'unplaced_list': lambda r: r['unplaced'].pop(),
    'issues_dropped': lambda r: r['issues']['items'].pop(),
    'issues_status': lambda r: r['issues'].__setitem__('status', 'DRAFT'),
    'hash': lambda r: r.__setitem__('report_sha256', '0' * 64),
}


def test_reconcile_accepts_a_good_report_and_rejects_every_tamper(data):
    sid = save(m2a_plan(), 'Đối soát')
    good, ev = _loaded(sid, data)
    assert reconcile(good, ev) is None
    for name, mutate in MUTATIONS.items():
        bad = deepcopy(good)
        mutate(bad)
        with pytest.raises(ReportReconciliationError) as info:
            reconcile(bad, ev)
        assert VIETNAMESE.search(info.value.what), name


def test_reconcile_message_names_the_mismatch(data):
    good, ev = _loaded(save(m2a_plan(), 'Đối soát'), data)
    good['totals']['placed_mass_g'] += 7
    with pytest.raises(ReportReconciliationError, match='khối lượng đã xếp'):
        reconcile(good, ev)


@pytest.mark.parametrize('path', ['report', 'report.xlsx'])
def test_api_returns_500_and_no_report_on_reconciliation_mismatch(data, monkeypatch, path):
    sid = save(m2a_plan(), 'Đối soát API')
    real = report_service.build_report

    def skewed(**kw):
        out = real(**kw)
        out['totals']['placed_mass_g'] += 1
        return out

    sent = []
    monkeypatch.setattr(report_service, 'build_report', skewed)
    monkeypatch.setattr(xlsx, 'write_xlsx', lambda r: sent.append(r) or b'PK')
    r = client.get(f'/api/snapshots/{sid}/{path}')
    assert r.status_code == 500 and r.headers['content-type'].startswith('application/json')
    detail = r.json()['detail']
    assert detail.startswith('Báo cáo không khớp đối soát nội bộ: ') and detail.endswith('; không xuất báo cáo.') and 'khối lượng đã xếp' in detail
    assert 'totals' not in r.text and sent == [] and r.content.count(b'PK') == 0


# ------------------------------------------------------------------ (k) exact values
def test_every_unit_value_equals_the_stored_plan(data):
    plan = vinafco_pipe_plan()
    sid = save(plan)
    r = report(sid)
    assert_units_match_stored(r, stored_json(data, sid))
    assert [u['dimensions_um'] for u in r['units']] == [u['dimensions_um'] for u in plan['units']]
    placed_ids = {p['unit_id'] for p in plan['placements']}
    assert {u['id'] for u in r['units'] if u['status'] == 'PLACED'} == placed_ids
    assert all(isinstance(v, int) for u in r['units'] for v in (u['length_mm'], u['mass_g'], *u['dimensions_um']))


# ------------------------------------------------------------------ (l) download headers and routing
def _names(header):
    m = re.fullmatch(r'attachment; filename="([^"]+)"; filename\*=UTF-8\'\'(\S+)', header)
    assert m, header
    return m.group(1), unquote(m.group(2))


def test_xlsx_headers_and_route_is_not_swallowed(monkeypatch):
    calls = []
    monkeypatch.setattr(xlsx, 'write_xlsx', lambda r: calls.append(r) or b'PK')
    name = 'Ống thép Đặng / "x"'
    sid = save(base_plan(), name)
    r = client.get(f'/api/snapshots/{sid}/report.xlsx')
    assert r.status_code == 200 and r.content == b'PK'
    assert r.headers['content-type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ascii_name, real_name = _names(r.headers['content-disposition'])
    assert ascii_name == f'SCST-bao-cao-Ong-thep-Dang-x-{sid[:8]}.xlsx' and ascii_name.isascii()
    assert real_name == f'SCST báo cáo {name} {sid[:8]}.xlsx'
    assert calls[0]['schema_version'] == 'scst.plan-report.v1' and calls[0]['header']['snapshot_id'] == sid
    # neighbouring routes keep their own meaning
    assert client.get(f'/api/snapshots/{sid}/report').headers['content-type'] == 'application/json'
    assert client.get(f'/api/snapshots/{sid}').json()['plan']['hold']['id']


@pytest.mark.parametrize('name,slug', [('日本語', 'phuong-an'), ('a' * 100, 'a' * 60), ('Đường  Ống__A-1', 'Duong-Ong__A-1'),
                                       ('x' * 59 + ' y', 'x' * 59)])
def test_filename_slug_rules(monkeypatch, name, slug):
    monkeypatch.setattr(xlsx, 'write_xlsx', lambda r: b'PK')
    sid = save(base_plan(), name)
    ascii_name, real_name = _names(client.get(f'/api/snapshots/{sid}/report.xlsx').headers['content-disposition'])
    assert ascii_name == f'SCST-bao-cao-{slug}-{sid[:8]}.xlsx' and real_name == f'SCST báo cáo {name.strip()} {sid[:8]}.xlsx'


def test_openapi_documents_the_report_routes():
    spec = app.openapi()
    got = spec['paths']['/api/snapshots/{snapshot_id}/report']['get']
    assert got['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/PlanReport')
    assert {'400', '404', '500'} <= set(got['responses'])
    xl = spec['paths']['/api/snapshots/{snapshot_id}/report.xlsx']['get']['responses']['200']['content']
    assert list(xl) == ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    assert spec['components']['schemas']['PlanReport']['additionalProperties'] is False


# ------------------------------------------------------------------ timing
def test_report_of_the_1076_unit_pipe_plan_is_fast(data):
    sid = save(vinafco_pipe_plan(), 'Thời gian')
    started = time.perf_counter()
    r = client.get(f'/api/snapshots/{sid}/report')
    elapsed = time.perf_counter() - started
    print(f'\nM2D report build+serialize for 1076 units (HTTP): {elapsed:.3f} s')
    started = time.perf_counter()
    report_service.snapshot_report(sid)
    print(f'M2D report build only: {time.perf_counter() - started:.3f} s')
    assert r.status_code == 200 and len(r.json()['units']) == 1076 and elapsed < 10
