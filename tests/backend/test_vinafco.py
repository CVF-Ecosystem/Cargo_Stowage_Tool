from copy import deepcopy
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.vessel import DATA

client = TestClient(app)


def plan(case='VR-SII'):
    r = client.get(f'/api/vessels/vinafco268/cases/{case}/plan')
    assert r.status_code == 200
    return r.json()['plan']


def test_profile_source_geometry_and_asset():
    p = client.get('/api/vessels/vinafco268').json()
    assert [p['dimensions_m'][x] for x in ('length', 'beam', 'depth')] == [77.8,13.24,5.2]
    assert p['hold']['status'] == 'ESTIMATED' and p['hold']['width_mm'] == 10343
    assert p['geometry']['width_inset_each_side_mm'] == .375
    assert p['lightship_mass_t'] is None and p['tanktop_load_limit_t_per_m2'] is None
    assert '4,17' in p['container_note'] and '12 mm' in p['provenance']['freeboard_note']
    assert 'http' not in json.dumps(p).lower()
    asset = client.get(p['asset_url'])
    assert asset.status_code == 200 and asset.content[:4] == b'glTF'
    assert hashlib.sha256(asset.content).hexdigest() == p['provenance']['source_glb_sha256']
    assert not list(DATA.glob('*.pdf'))


@pytest.mark.parametrize('case,limit,dwt,draft', [('VR-SI',3282500000,3301,4.6),('VR-SII',3517500000,3536,4.85)])
def test_case_profile_and_plan(case,limit,dwt,draft):
    p=client.get('/api/vessels/vinafco268').json()
    c=next(c for c in p['cases'] if c['id']==case)
    assert (c['cargo_mass_g'],c['deadweight_t'],c['draft_m']) == (limit,dwt,draft)
    v=plan(case)
    assert v['source']=='MIXED_REFERENCE' and v['vessel']['case_id']==case
    assert (v['hold']['length_mm'],v['hold']['width_mm'],v['hold']['height_mm'])==(56405,10343,5408)
    assert v['limits']['certificate_cargo_limit_g']==limit
    assert not client.post('/api/validate',json=v).json()['operational_eligible']
    assert client.get('/api/vessels/vinafco268/cases/unknown/plan').status_code==404


@pytest.mark.parametrize('field', ['source','vessel','case','hold','name','limit'])
def test_profile_tamper_rejected(field):
    p=plan()
    if field=='source': p['source']='SYNTHETIC'
    if field=='vessel': p['vessel']['vessel_id']='OTHER'
    if field=='case': p['vessel']['case_id']='OTHER'
    if field=='hold': p['hold']['width_mm']=10344
    if field=='name': p['hold']['name']='other'
    if field=='limit': p['limits']['certificate_cargo_limit_g']+=1
    assert client.post('/api/validate',json=p).status_code==422


@pytest.mark.parametrize('case,mass,excess',[('VR-SII',3520000000,2500000),('VR-SI',3300000000,17500000)])
def test_cargo_reference_capacity_cases(case,mass,excess):
    p=plan(case)
    p['units']=p['units'][:1]; p['placements']=p['placements'][:1]
    p['units'][0]['mass_g']=mass
    response=client.post('/api/validate',json=p)
    assert response.status_code==200
    result=response.json()
    assert result['summary']['remaining_capacity_g']==-excess
    assert any(i['code']=='OVERWEIGHT' for i in result['issues'])


def test_boundary_width_and_existing_synthetic():
    p=plan(); p['units']=p['units'][:1]; p['placements']=p['placements'][:1]
    p['placements'][0]['y_mm']=10343-p['units'][0]['width_mm']
    assert all(i['code']!='OUT_OF_BOUNDS' for i in client.post('/api/validate',json=p).json()['issues'])
    p['placements'][0]['y_mm']+=1
    assert any(i['code']=='OUT_OF_BOUNDS' for i in client.post('/api/validate',json=p).json()['issues'])
    assert client.get('/api/demo').json()['plan']['source']=='SYNTHETIC'
