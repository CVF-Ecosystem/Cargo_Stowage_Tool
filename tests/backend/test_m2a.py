import json
import sqlite3
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADER='id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\n'
ROW='B-1,"Synthetic, bundle",BAR_BUNDLE,required,6000,900,650,2500.001\n'

def m2():
    p=client.get('/api/demo').json()['plan']
    p.update(contract_version='scst.m2a.v1',source='USER_ENTERED',cargo_source='USER_ENTERED',vessel=None,units=[],placements=[])
    return p

def test_empty_versions_and_existing_reference():
    p=m2();r=client.post('/api/validate',json=p)
    assert r.status_code==200
    j=r.json(); assert j['status']=='DRAFT' and j['summary']['manifest_mass_g']==0 and j['issues'][0]['code']=='EMPTY_MANIFEST'
    p['contract_version']='scst.m1.v1';assert client.post('/api/validate',json=p).status_code==422
    p=client.get('/api/vessels/vinafco268/cases/VR-SI/plan').json()['plan'];p.update(contract_version='scst.m2a.v1',cargo_source='USER_ENTERED',units=[],placements=[])
    assert client.post('/api/validate',json=p).status_code==200
    p['hold']['width_mm']+=1;assert client.post('/api/validate',json=p).status_code==422

def csv(text): return client.post('/api/import/csv/preview',json={'plan':m2(),'csv_text':text}).json()

def test_csv_bom_quote_precision_and_no_partial():
    p=csv('\ufeff'+HEADER+ROW)
    assert p['valid'] and p['count']==1 and p['total_mass_g']==2500001
    assert p['candidate']['units'][0]['name']=='Synthetic, bundle' and not p['candidate']['placements']
    r=csv(HEADER+ROW+ROW)
    assert not r['valid'] and r['candidate'] is None and any(e['row']==3 and e['field']=='id' for e in r['errors'])

@pytest.mark.parametrize('text,field',[(HEADER.replace('mass_kg','mass_g')+ROW,'header'),(HEADER+'x,bad,NO,wrong,0,-2,x,1.2345\n','length_mm'),(HEADER+'x,bad,NO,wrong,0,-2,x,1.2345\n','kind'),(HEADER+'x,bad,NO,wrong,0,-2,x,1.2345\n','mass_kg'),(HEADER+'x,a,BAR_BUNDLE,required,1,2,3,1,extra\n','row'),(HEADER+'"unterminated','csv'),(HEADER+('x'*1048576),'file'),(HEADER+''.join(f'X-{i},A,BAR_BUNDLE,required,1,1,1,1\n' for i in range(201)),'row')], ids=['header','bounds','kind','precision','extra','quote','size','rows'])
def test_csv_rejects_invalid_with_location(text,field):
    r=csv(text);assert not r['valid'] and r['candidate'] is None and any(e['field']==field for e in r['errors'])

def test_storage_immutable_reopen_and_corrupt_record(tmp_path,monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR',str(tmp_path)); p=m2()
    first=client.post('/api/snapshots',json={'name':'Synthetic empty','plan':p}).json()
    second=client.post('/api/snapshots',json={'name':'Synthetic empty','plan':p}).json()
    assert first['id']!=second['id']; assert len(client.get('/api/snapshots').json())==2
    r=client.get('/api/snapshots/'+first['id']); assert r.status_code==200 and r.json()['plan']==p and r.json()['status']=='DRAFT'
    with sqlite3.connect(tmp_path/'scst.sqlite3') as db:
        db.execute('UPDATE snapshots SET schema_version=? WHERE id=?',('unknown',first['id']))
    assert client.get('/api/snapshots/'+first['id']).status_code==400
    assert client.get('/api/snapshots/'+second['id']).status_code==200
    assert client.get('/api/snapshots/not-a-uuid').status_code==400
    assert client.post('/api/snapshots',json={'name':'   ','plan':p}).status_code==400

def test_storage_corrupt_db_not_reset(tmp_path,monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR',str(tmp_path)); path=tmp_path/'scst.sqlite3';path.write_bytes(b'broken db')
    assert client.get('/api/snapshots').status_code==400
    assert path.read_bytes()==b'broken db'


def test_header_only_and_multiline_csv_errors():
    empty=csv(HEADER); assert not empty['valid'] and empty['errors'][0]['field']=='row'
    data=HEADER+'A,"two\nlines",BAR_BUNDLE,required,1,1,1,1\nB,bad,NO,required,1,1,1,1\n'
    result=csv(data)
    assert not result['valid'] and any(e['row']==4 and e['field']=='kind' for e in result['errors'])


def test_v1_rejects_v2_provenance():
    p=client.get('/api/demo').json()['plan']; p['cargo_source']='USER_ENTERED'
    assert client.post('/api/validate',json=p).status_code==422


def test_existing_unrelated_database_is_not_repaired(tmp_path,monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR',str(tmp_path)); path=tmp_path/'scst.sqlite3'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE unrelated (data TEXT)')
    before=path.read_bytes()
    assert client.get('/api/snapshots').status_code==400
    assert path.read_bytes()==before


def test_corrupt_snapshot_time_reports_error_without_losing_good_snapshot(tmp_path,monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR',str(tmp_path)); p=m2()
    good=client.post('/api/snapshots',json={'name':'Good synthetic fixture','plan':p}).json()
    bad=client.post('/api/snapshots',json={'name':'Corrupt synthetic fixture','plan':p}).json()
    with sqlite3.connect(tmp_path/'scst.sqlite3') as db:
        db.execute('UPDATE snapshots SET created_utc=? WHERE id=?',('not-a-date',bad['id']))
    response=client.get('/api/snapshots')
    assert response.status_code==400 and 'Không thể đọc' in response.json()['detail']
    reopened=client.get('/api/snapshots/'+good['id'])
    assert reopened.status_code==200 and reopened.json()['plan']==p
    with sqlite3.connect(tmp_path/'scst.sqlite3') as db:
        assert db.execute('SELECT created_utc FROM snapshots WHERE id=?',(bad['id'],)).fetchone()[0]=='not-a-date'
