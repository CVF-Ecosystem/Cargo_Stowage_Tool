from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.demo import demo_plan
from app.domain.model import Plan
from app.domain.rules import evaluate
from app.main import app

client = TestClient(app)


def payload():
    return demo_plan().model_dump()


def codes(plan):
    return {i.code for i in evaluate(Plan.model_validate(plan)).issues}


def test_real_api_demo_accounts_for_every_unit():
    result = client.get('/api/demo').json()
    assert result['plan']['source'] == 'SYNTHETIC'
    assert result['summary'] == dict(manifest_mass_g=27_950_000, placed_mass_g=26_100_000,
                                     remaining_capacity_g=5_900_000, placed_count=12,
                                     unplaced_ids=['PP-013'], excluded_ids=[])
    assert result['basic_checks_passed'] and not result['operational_eligible']
    assert len(result['unchecked']) == 5
    assert client.get('/api/health').json()['ai'] == 'off'


@pytest.mark.parametrize('delta,passes', [(0, True), (1, False)])
def test_weight_boundary_exact_gram(delta, passes):
    p = payload(); p['limits']['voyage_cargo_limit_g'] = 27_100_000 - delta; p['limits']['cargo_onboard_g'] = 1_000_000
    assert ('OVERWEIGHT' not in codes(p)) == passes


@pytest.mark.parametrize('delta,passes', [(0, True), (1, False)])
def test_hold_boundary_exact_mm(delta, passes):
    p = payload(); p['placements'] = [p['placements'][0]]
    p['placements'][0]['x_mm'] = 8000 + delta
    assert ('OUT_OF_BOUNDS' not in codes(p)) == passes


@pytest.mark.parametrize('gap,overlap', [(0, False), (-1, True), (1, False)])
def test_face_touch_and_positive_overlap(gap, overlap):
    p = payload(); p['placements'] = p['placements'][:2]
    p['placements'][1].update(x_mm=6500 + gap, y_mm=550)
    assert ('OVERLAP' in codes(p)) == overlap


def test_rotation_and_height_are_not_ignored():
    p = payload(); p['placements'][0].update(yaw_deg=90, x_mm=0, y_mm=0)
    assert 'OUT_OF_BOUNDS' not in codes(p)
    p['placements'][0]['y_mm'] = 2501
    assert 'OUT_OF_BOUNDS' in codes(p)
    p['placements'][0].update(y_mm=0, z_mm=3351)
    assert {'LAYER_UNSUPPORTED', 'OUT_OF_BOUNDS'} <= codes(p)


def test_required_optional_and_excluded_partition():
    p = payload(); p['placements'] = p['placements'][1:]
    result = evaluate(Plan.model_validate(p))
    assert [i.unit_ids for i in result.issues if i.code == 'REQUIRED_UNPLACED'] == [['ST-001']]
    p['units'][0]['requirement'] = 'excluded'
    result = evaluate(Plan.model_validate(p))
    assert result.summary.excluded_ids == ['ST-001']
    assert result.summary.unplaced_ids == ['PP-013']
    assert result.basic_checks_passed


@pytest.mark.parametrize('bad', [2.5, True, '2500', 0, -1, 10**13])
def test_bad_mass_rejected_without_coercion(bad):
    p = payload(); p['units'][0]['mass_g'] = bad
    assert client.post('/api/validate', json=p).status_code == 422


@pytest.mark.parametrize('kind', ['duplicate_unit', 'duplicate_placement', 'unknown_id', 'excluded', 'unknown_field', 'bad_yaw', 'fractional_mm', 'oversized', 'real_source'])
def test_structural_errors_rejected(kind):
    p = payload()
    if kind == 'duplicate_unit': p['units'].append(deepcopy(p['units'][0]))
    if kind == 'duplicate_placement': p['placements'].append(deepcopy(p['placements'][0]))
    if kind == 'unknown_id': p['placements'][0]['unit_id'] = 'UNKNOWN'
    if kind == 'excluded': p['units'][0]['requirement'] = 'excluded'
    if kind == 'unknown_field': p['hold']['gross_tonnage'] = 5000
    if kind == 'bad_yaw': p['placements'][0]['yaw_deg'] = 45
    if kind == 'fractional_mm': p['placements'][0]['x_mm'] = 1.5
    if kind == 'oversized': p['units'] = p['units'] * 16
    if kind == 'real_source': p['source'] = 'REAL'
    assert client.post('/api/validate', json=p).status_code == 422


def test_invalid_geometry_is_returned_for_correction_and_demo_is_stateless():
    p = payload(); p['placements'][0]['x_mm'] = -1
    response = client.post('/api/validate', json=p)
    assert response.status_code == 200
    assert not response.json()['basic_checks_passed']
    assert response.json()['plan']['placements'][0]['x_mm'] == -1
    assert client.get('/api/demo').json()['basic_checks_passed']


def test_evaluation_is_deterministic_without_mutating_input():
    p = demo_plan(); before = p.model_dump()
    assert evaluate(p) == evaluate(p)
    assert p.model_dump() == before

@pytest.mark.parametrize('field,bad', [(f, b) for f in ['certificate_cargo_limit_g','voyage_cargo_limit_g'] for b in [0,-1,1.5,True,'1',10**12+1]] + [('cargo_onboard_g',b) for b in [-1,1.5,True,'1',10**12+1]])
def test_limit_domains(field,bad):
    p=payload(); p['limits'][field]=bad
    assert client.post('/api/validate',json=p).status_code == 422

@pytest.mark.parametrize('limits', [dict(certificate_cargo_limit_g=1,voyage_cargo_limit_g=2,cargo_onboard_g=0),dict(certificate_cargo_limit_g=2,voyage_cargo_limit_g=2,cargo_onboard_g=3)])
def test_limit_relations(limits):
    p=payload(); p['limits']=limits
    assert client.post('/api/validate',json=p).status_code == 422

@pytest.mark.parametrize('field,value', [('z_mm',1),('layer',1),('layer',1_000_001),('supported_by',['ST-002'])])
def test_each_unsupported_layer_field(field,value):
    p=payload(); p['placements'][0][field]=value
    response=client.post('/api/validate',json=p)
    assert response.status_code == 200
    assert 'LAYER_UNSUPPORTED' in {x['code'] for x in response.json()['issues']}
    assert response.json()['status']=='DRAFT'

def test_status_priority_and_zero_onboard():
    p=payload(); assert p['limits']['cargo_onboard_g']==0
    assert client.post('/api/validate',json=p).json()['status']=='RULES_CHECKED'
    p['limits']['voyage_cargo_limit_g']=1
    assert client.post('/api/validate',json=p).json()['status']=='GEOMETRY_FEASIBLE'
    p['placements'][0]['x_mm']=-1
    result=client.post('/api/validate',json=p).json()
    assert result['status']=='DRAFT' and not result['operational_eligible'] and len(result['unchecked'])==5
    assert {'OVERWEIGHT','OUT_OF_BOUNDS'} <= {i['code'] for i in result['issues']}
