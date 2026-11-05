"""M3a D3: columns-v1 planner (deterministic stacking suggestion; writes nothing)."""
import json
import time
from collections import Counter
from fastapi.testclient import TestClient
from app.main import app
from app.domain.model import Plan
from app.domain.planner import preview

client = TestClient(app)
GEOMETRY_CODES = {'OUT_OF_BOUNDS', 'OVERLAP', 'LAYER_UNSUPPORTED', 'EMPTY_MANIFEST', 'LAYER_INDEX_INVALID'}


def baltimore_vinafco():
    vin = client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan']
    r = client.post('/api/pipe-list/preview', json=vin)
    assert r.status_code == 200
    return r.json()['plan']


def geometry_issues(evaluation):
    return [i for i in evaluation['issues'] if i['code'] in GEOMETRY_CODES or i['code'].startswith('SUPPORT_')]


def unit(i, h=100, mass=1000, req='optional', length=500, width=500):
    return dict(id=f'U{i:03d}', name=f'Unit {i}', kind='BAR_BUNDLE', length_mm=length, width_mm=width, height_mm=h,
                mass_g=mass, requirement=req)


def synthetic_plan(units, hold=(500, 500, 300), limit_g=10**9):
    plan = client.get('/api/demo').json()['plan']
    plan['placements'] = []
    plan['hold'].update(length_mm=hold[0], width_mm=hold[1], height_mm=hold[2])
    plan['limits'].update(certificate_cargo_limit_g=limit_g, voyage_cargo_limit_g=limit_g, cargo_onboard_g=0)
    base = plan['units'][0]
    plan['units'] = [{**base, **u} for u in units]
    return Plan.model_validate(plan)


def test_default_algorithm_unchanged_and_explicit_param_identical():
    plan = baltimore_vinafco()
    a = client.post('/api/planner/preview', json=plan)
    b = client.post('/api/planner/preview?algorithm=guillotine-single-layer-v1', json=plan)
    assert a.status_code == b.status_code == 200
    assert a.text == b.text
    body = a.json()
    assert body['algorithm'] == 'guillotine-single-layer-v1'
    assert 'stacking' not in body['evaluation']['plan']
    assert all(p['z_mm'] == 0 and p['layer'] == 0 for p in body['evaluation']['plan']['placements'])


def test_unknown_algorithm_rejected():
    assert client.post('/api/planner/preview?algorithm=nope', json=baltimore_vinafco()).status_code == 422


def test_columns_v1_baltimore_deterministic_valid_and_fast():
    plan = baltimore_vinafco()
    r1 = client.post('/api/planner/preview?algorithm=columns-v1', json=plan)
    r2 = client.post('/api/planner/preview?algorithm=columns-v1', json=plan)
    assert r1.status_code == 200 and r1.text == r2.text
    body = r1.json(); cand = body['evaluation']['plan']
    assert body['algorithm'] == 'columns-v1' and cand['stacking'] == 'COLUMNS_V1'
    assert not geometry_issues(body['evaluation'])
    placed = cand['placements']; unplaced = body['unplaced']
    assert len(placed) >= 900 and len(placed) + len(unplaced) == 1076
    assert all(u['code'] and u['message'] for u in unplaced)
    assert {u['unit_id'] for u in unplaced}.isdisjoint(p['unit_id'] for p in placed)
    columns = sum(1 for p in placed if p['layer'] == 0)
    print('baltimore columns-v1', len(placed), 'columns', columns, 'max_layer', max(p['layer'] for p in placed) + 1,
          dict(Counter(u['code'] for u in unplaced)))
    t = time.perf_counter(); preview(Plan.model_validate(plan), 'columns-v1'); assert time.perf_counter() - t < 2.0


def test_columns_v1_stacks_three_high_with_levels_and_supports():
    plan = synthetic_plan([unit(i) for i in range(4)], hold=(500, 500, 300))
    res = preview(plan, 'columns-v1')
    pl = {p.unit_id: p for p in res.evaluation.plan.placements}
    assert res.evaluation.plan.stacking == 'COLUMNS_V1'
    assert [(pl[f'U{i:03d}'].z_mm, pl[f'U{i:03d}'].layer, pl[f'U{i:03d}'].supported_by) for i in range(3)] == [
        (0, 0, []), (100, 1, ['U000']), (200, 2, ['U001'])]
    assert len({(p.x_mm, p.y_mm, p.yaw_deg) for p in pl.values()}) == 1
    assert [(u.unit_id, u.code) for u in res.unplaced] == [('U003', 'STACK_HEIGHT')]
    assert 'đủ chiều cao hầm' in res.unplaced[0].message
    assert preview(plan, 'columns-v1').model_dump_json() == res.model_dump_json()


def test_columns_v1_mass_limit_skips_unit_but_lighter_later_unit_goes():
    units = [unit(0, mass=1000), unit(1, mass=5000, length=400, width=400), unit(2, mass=500, length=300, width=300)]
    res = preview(synthetic_plan(units, hold=(1000, 1000, 100), limit_g=2000), 'columns-v1')
    placed = {p.unit_id for p in res.evaluation.plan.placements}
    assert placed == {'U000', 'U002'}
    assert [(u.unit_id, u.code) for u in res.unplaced] == [('U001', 'MASS_LIMIT')]


def test_columns_v1_no_floor_space_for_new_dims_is_heuristic_and_excluded_reasons():
    units = [unit(0, h=300), unit(1, h=200, length=400, width=400), unit(2, req='excluded')]
    res = preview(synthetic_plan(units, hold=(500, 500, 300)), 'columns-v1')
    codes = {u.unit_id: u.code for u in res.unplaced}
    assert codes == {'U001': 'HEURISTIC_NO_SPACE', 'U002': 'EXCLUDED'}


def test_default_planner_keeps_input_stacking_and_single_layer():
    plan = synthetic_plan([unit(i) for i in range(4)])
    res = preview(plan)
    assert res.algorithm == 'guillotine-single-layer-v1' and res.evaluation.plan.stacking is None
    assert len(res.evaluation.plan.placements) == 1
    assert {u.code for u in res.unplaced} == {'HEURISTIC_NO_SPACE'}
