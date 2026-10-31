from copy import deepcopy
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def preview():
    base=client.get('/api/demo').json()['plan']
    r=client.post('/api/pipe-list/preview',json=base); assert r.status_code==200
    return r.json()

def test_library_and_candidate():
    lib=client.get('/api/pipe-list').json(); groups=lib['groups']
    assert len(groups)==31 and sum(g['bundle_count'] for g in groups)==1076
    assert sum(g['bundle_count']*g['pieces_per_bundle'] for g in groups)==21226
    assert sum(g['bundle_count']*g['mass_g'] for g in groups)==1125551030
    assert sum(g['bundle_count'] for g in groups if g['dimension_warning'])==16
    assert groups[0]['group_id']=='Sheet1-R002' and lib['assigned_vessel'] is None
    assert any('manual_kg_per_m_difference' in g['issue_codes'] for g in groups)
    result=preview();p=result['plan']; assert len(p['units'])==1076 and not p['placements']
    assert result['summary']['manifest_mass_g']==1125551030 and all(u['requirement']=='optional' for u in p['units'])
    first=p['units'][0];assert first['id']=='PIPE-R002-B0001' and first['dimensions_um']==[6401000,337600,295400]
    assert (first['length_mm'],first['width_mm'],first['height_mm'],first['mass_g'])==(6401,338,296,911400)

@pytest.mark.parametrize('field',['mass','size','legacy','row','hash','name','missing','duplicate','legacy_version'])
def test_tampering_rejected(field):
    p=preview()['plan'];u=p['units'][0]
    if field=='mass':u['mass_g']+=1
    if field=='size':u['dimensions_um'][1]+=1
    if field=='legacy':u['width_mm']-=1
    if field=='row':u['source_ref']['source_row']+=1
    if field=='hash':u['source_ref']['workbook_sha256']='other'
    if field=='name':u['name']='other'
    if field=='missing':p['units'].pop()
    if field=='duplicate':p['units'][1]=deepcopy(p['units'][0])
    if field=='legacy_version':p['contract_version']='scst.m2a.v1'
    assert client.post('/api/validate',json=p).status_code==422

def test_exact_um_bounds_rotation_and_touch():
    p=preview()['plan'];p['hold'].update(length_mm=12802,width_mm=338,height_mm=296)
    a,b=p['units'][:2];p['placements']=[dict(unit_id=a['id'],x_mm=0,y_mm=0,yaw_deg=0),dict(unit_id=b['id'],x_mm=6401,y_mm=0,yaw_deg=0)]
    j=client.post('/api/validate',json=p).json();assert not any(i['code'] in ('OUT_OF_BOUNDS','OVERLAP') for i in j['issues'])
    p['placements'][1]['x_mm']=6400;j=client.post('/api/validate',json=p).json();assert any(i['code']=='OVERLAP' for i in j['issues'])
    p['placements']=p['placements'][:1];p['hold'].update(length_mm=338,width_mm=6401);p['placements'][0]['yaw_deg']=90
    assert not any(i['code']=='OUT_OF_BOUNDS' for i in client.post('/api/validate',json=p).json()['issues'])
    p['hold']['length_mm']=337; assert any(i['code']=='OUT_OF_BOUNDS' for i in client.post('/api/validate',json=p).json()['issues'])

def test_large_overlap_is_bounded_and_exact():
    p=preview()['plan'];p['placements']=[dict(unit_id=u['id'],x_mm=0,y_mm=0,yaw_deg=0) for u in p['units']]
    started=time.monotonic();r=client.post('/api/validate',json=p);elapsed=time.monotonic()-started;j=r.json()
    assert r.status_code==200 and elapsed<15 and len(j['issues'])==200
    # Original demo voyage ceiling creates one overweight issue in addition to every pair overlap.
    assert j['total_issues']==1076*1075//2+1 and j['issues_truncated'] and len(j['affected_unit_ids'])==1076
    assert j['status']=='DRAFT' and not j['basic_checks_passed'] and len(r.content)<1_000_000

def test_snapshot_and_csv_switch_keep_or_clear_context(tmp_path,monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR',str(tmp_path));p=preview()['plan'];p['placements']=[dict(unit_id=p['units'][0]['id'],x_mm=0,y_mm=0,yaw_deg=0)]
    p=client.post('/api/validate',json=p).json()['plan']
    created=client.post('/api/snapshots',json={'name':'Source calculation fixture','plan':p});assert created.status_code==200
    r=client.get('/api/snapshots/'+created.json()['id']);assert r.status_code==200 and r.json()['plan']==p
    text='id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\nA,Synthetic,BAR_BUNDLE,required,1,1,1,1\n'
    c=client.post('/api/import/csv/preview',json={'plan':p,'csv_text':text}).json()
    assert c['valid'] and c['candidate']['contract_version']=='scst.m2a.v1' and c['candidate']['cargo_dataset'] is None and c['candidate']['placements']==[]
