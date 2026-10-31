from copy import deepcopy
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def base():
    p=client.get('/api/demo').json()['plan'];p.update(contract_version='scst.m2a.v1',source='USER_ENTERED',cargo_source='USER_ENTERED',vessel=None,units=[],placements=[])
    p['hold'].update(length_mm=10,width_mm=10,height_mm=10);p['limits'].update(certificate_cargo_limit_g=10000,voyage_cargo_limit_g=10000,cargo_onboard_g=0)
    return p

def unit(id,l,w,h=1,mass=100,req='optional'):
    return dict(id=id,name=id,kind='PIPE_BUNDLE',requirement=req,length_mm=l,width_mm=w,height_mm=h,mass_g=mass)

def run(p):
    r=client.post('/api/planner/preview',json=p);assert r.status_code==200,r.text;return r.json()

def test_empty_and_input_unchanged():
    p=base();before=deepcopy(p);r=run(p);assert p==before and r['evaluation']['plan']['units']==[] and r['evaluation']['status']=='DRAFT' and not r['unplaced']

def test_priority_rotation_and_touch():
    p=base();p['hold'].update(length_mm=8,width_mm=5);p['units']=[unit('OPTIONAL',8,5),unit('REQUIRED',5,8,req='required')]
    r=run(p);placed=r['evaluation']['plan']['placements'];assert len(placed)==1 and placed[0]['unit_id']=='REQUIRED' and placed[0]['yaw_deg']==90
    assert r['unplaced'][0]['code']=='HEURISTIC_NO_SPACE' and r['evaluation']['basic_checks_passed']
    assert r==run(p)

def test_reason_priority_and_mass_exact():
    p=base();p['limits'].update(certificate_cargo_limit_g=100,voyage_cargo_limit_g=100,cargo_onboard_g=0)
    p['units']=[unit('EX',100,100,100,200,'excluded'),unit('HIGH',100,100,11,200),unit('BIG',11,11,1,200),unit('EXACT',1,1,1,100,'required'),unit('MASS',1,1,1,1)]
    r=run(p);reasons={x['unit_id']:x['code'] for x in r['unplaced']}
    assert reasons=={'EX':'EXCLUDED','HIGH':'TOO_HIGH','BIG':'FOOTPRINT_TOO_LARGE','MASS':'MASS_LIMIT'}
    assert r['evaluation']['summary']['placed_mass_g']==100

def test_required_unplaced_does_not_hide_rule_failure():
    p=base();p['units']=[unit('A',11,11,req='required')];r=run(p)
    assert r['unplaced'][0]['code']=='FOOTPRINT_TOO_LARGE' and not r['evaluation']['basic_checks_passed']
    assert any(i['code']=='REQUIRED_UNPLACED' for i in r['evaluation']['issues'])

def test_determinism_independent_of_input_order():
    p=base();p['units']=[unit('A',4,3),unit('C',4,3),unit('B',4,3)]
    a=run(p);p['units'].reverse();b=run(p)
    assert a['evaluation']['plan']['placements']==b['evaluation']['plan']['placements'] and a['unplaced']==b['unplaced']

def test_full_source_conservative_and_performance():
    b=client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan']
    p=client.post('/api/pipe-list/preview',json=b).json()['plan'];p['limits']['voyage_cargo_limit_g']=p['limits']['certificate_cargo_limit_g']
    before=deepcopy(p);start=time.monotonic();r=run(p);elapsed=time.monotonic()-start
    candidate=r['evaluation']['plan'];placed={x['unit_id'] for x in candidate['placements']};unplaced={x['unit_id'] for x in r['unplaced']}
    assert elapsed<15 and len(placed|unplaced)==1076 and not placed&unplaced
    assert candidate['units']==before['units'] and candidate['hold']==before['hold'] and candidate['limits']==before['limits'] and p==before
    assert not any(i['code'] in ('OUT_OF_BOUNDS','OVERLAP','OVERWEIGHT','LAYER_UNSUPPORTED') for i in r['evaluation']['issues'])
    print('source preview seconds',elapsed,'placed',len(placed),'remaining',len(unplaced))
