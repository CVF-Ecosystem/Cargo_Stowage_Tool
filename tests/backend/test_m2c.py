from copy import deepcopy
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def demo(): return client.get('/api/demo').json()['plan']
def compare(a,b):
    r=client.post('/api/plans/compare',json={'before':a,'after':b});assert r.status_code==200,r.text;return r.json()

def test_reordered_units_and_placements_no_change():
    a=demo();b=deepcopy(a);b['units'].reverse();b['placements'].reverse();before=deepcopy(a)
    r=compare(a,b); assert a==before and r['counts']=={'ADDED':0,'REMOVED':0,'CHANGED':0,'UNCHANGED':len(a['units'])}
    assert not r['context_changes'] and all(not x['changes'] for x in r['rows'])
    assert all(v==0 for v in r['delta'].values())

def test_exact_differences_added_removed_context_and_defaults():
    a=demo();b=deepcopy(a);u=b['units'][0];u['mass_g']+=1;b['placements'][0]['x_mm']+=1
    b['units'][1]['name']='Changed';b['units'][2]['id']='NEW-003';b['placements'][2]['unit_id']='NEW-003'
    b['limits']['voyage_cargo_limit_g']-=1
    r=compare(a,b); assert r['delta']['manifest_mass_g']==1 and r['delta']['placed_mass_g']==1
    byid={row['unit_id']:row for row in r['rows']};assert byid[u['id']]['status']=='CHANGED'
    f={d['field']:d for d in byid[u['id']]['changes']};assert f['mass_g']['after']-f['mass_g']['before']==1 and f['placement.x_mm']['after']-f['placement.x_mm']['before']==1
    assert byid['NEW-003']['status']=='ADDED' and byid['NEW-003']['changes'] and byid[a['units'][2]['id']]['status']=='REMOVED' and not byid[a['units'][2]['id']]['in_after']
    assert any(c['field']=='limits.voyage_cargo_limit_g' for c in r['context_changes'])
    c=deepcopy(a);del c['placements'][0]['z_mm'];del c['placements'][0]['layer'];del c['placements'][0]['supported_by'];assert compare(a,c)['counts']['CHANGED']==0

def test_independent_evaluation_and_issue_count():
    a=demo();b=deepcopy(a);b['placements'][0]['x_mm']=-1
    r=compare(a,b);assert r['before']['basic_checks_passed'] and not r['after']['basic_checks_passed']
    assert r['delta']['issue_count']>0 and not r['before']['operational_eligible'] and not r['after']['operational_eligible']

def test_vessel_context_null_to_reference():
    a=demo();b=client.get('/api/vessels/vinafco268/cases/VR-SI/plan').json()['plan'];r=compare(a,b)
    context={x['field']:x for x in r['context_changes']}
    assert context['vessel.vessel_id']['before'] is None and context['vessel.vessel_id']['after']=='VINAFCO268'
    assert context['vessel.case_id']['before'] is None and context['vessel.case_id']['after']=='VR-SI'

def test_source1076_full_issue_count_and_identity_warning():
    a=client.post('/api/pipe-list/preview',json=demo()).json()['plan'];b=deepcopy(a)
    b['placements']=[dict(unit_id=u['id'],x_mm=0,y_mm=0,yaw_deg=0) for u in b['units']]
    started=time.monotonic();r=compare(a,b); assert time.monotonic()-started<15
    assert r['after']['issue_count']==1076*1075//2+1 and r['counts']['CHANGED']==1076
    assert r['counts']['ADDED']==0 and all(len(row['changes'])<10 for row in r['rows'])
    first=a['units'][0];generic=demo(); generic['contract_version']='scst.m2a.v1';generic['cargo_source']='USER_ENTERED';generic['units']=[{'id':first['id'],'name':'OTHER','kind':'PIPE_BUNDLE','requirement':'optional','length_mm':1,'width_mm':1,'height_mm':1,'mass_g':1}];generic['placements']=[]
    r=compare(generic,a);row=next(x for x in r['rows'] if x['unit_id']==first['id']);assert row['source_identity_warning']

def test_reject_unknown_fields_and_bad_plan():
    p=demo();assert client.post('/api/plans/compare',json={'before':p,'after':p,'extra':True}).status_code==422
    bad=deepcopy(p);bad['units'][0]['mass_g']=0;assert client.post('/api/plans/compare',json={'before':bad,'after':p}).status_code==422
