from pathlib import Path
import sys,json,copy,random,os,tempfile,time,hashlib
sys.path.insert(0,str(Path('services/backend').resolve()))
from fastapi.testclient import TestClient
from app.main import app
checks=0

def ck(value):
 global checks
 assert value
 checks+=1

def flatten(value,path=''):
 stack=[(path,value)];out={}
 while stack:
  prefix,item=stack.pop()
  if isinstance(item,dict):stack.extend(((prefix+'.' if prefix else '')+str(k),v) for k,v in item.items())
  else:out[prefix]=item
 return out

def changes(a,b):
 return [dict(field=k,before=a.get(k),after=b.get(k)) for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)]

def context(p):
 d={k:v for k,v in p.items() if k not in ['units','placements']};v=d['vessel'];d['vessel']={'vessel_id':v['vessel_id'] if v else None,'case_id':v['case_id'] if v else None};return flatten(d)

def summary(p):
 units={u['id']:u for u in p['units']};placed={q['unit_id'] for q in p['placements']};mass=sum(units[i]['mass_g'] for i in placed);cap=p['limits']['voyage_cargo_limit_g']-p['limits']['cargo_onboard_g'];n=int(not units)+int(mass>cap);geometry=not units;boxes=[]
 for q in p['placements']:
  u=units[q['unit_id']];d=u['dimensions_um'] or [u[k]*1000 for k in ['length_mm','width_mm','height_mm']];dx,dy=(d[1],d[0]) if q['yaw_deg']%180 else d[:2];lo=(q['x_mm']*1000,q['y_mm']*1000,q['z_mm']*1000);hi=(lo[0]+dx,lo[1]+dy,lo[2]+d[2]);oob=any(x<0 for x in lo) or any(x>y*1000 for x,y in zip(hi,[p['hold'][k] for k in ['length_mm','width_mm','height_mm']]));layer=q['z_mm']!=0 or q['layer']!=0 or bool(q['supported_by']);n+=int(oob)+int(layer);geometry|=oob or layer;boxes.append((lo,hi))
 for i,(lo,hi) in enumerate(boxes):
  for l2,h2 in boxes[i+1:]:
   overlap=all(max(a,b)<min(c,d) for a,b,c,d in zip(lo,l2,hi,h2));n+=overlap;geometry|=overlap
 n+=sum(u['requirement']=='required' and u['id'] not in placed for u in p['units'])
 return dict(manifest_mass_g=sum(u['mass_g'] for u in p['units']),placed_mass_g=mass,remaining_capacity_g=cap-mass,placed_count=len(placed),unplaced_count=sum(u['requirement']!='excluded' and u['id'] not in placed for u in p['units']),excluded_count=sum(u['requirement']=='excluded' for u in p['units']),issue_count=n,status='DRAFT' if geometry else 'GEOMETRY_FEASIBLE' if n else 'RULES_CHECKED',basic_checks_passed=n==0,operational_eligible=False)

def run(c,a,b):
 aa=copy.deepcopy(a);bb=copy.deepcopy(b);r=c.post('/api/plans/compare',json={'before':a,'after':b});ck(r.status_code==200);data=r.json();ck(a==aa and b==bb);sa=summary(a);sb=summary(b)
 for label,s in [('before',sa),('after',sb)]:ck(all(data[label][k]==v for k,v in s.items()))
 numeric=[k for k in sa if k not in ['status','basic_checks_passed','operational_eligible']];ck(data['delta']=={k:sb[k]-sa[k] for k in numeric});ck(data['context_changes']==changes(context(a),context(b)))
 ua={u['id']:u for u in a['units']};ub={u['id']:u for u in b['units']};pa={q['unit_id']:q for q in a['placements']};pb={q['unit_id']:q for q in b['placements']};counts={k:0 for k in ['ADDED','REMOVED','CHANGED','UNCHANGED']};expected=[]
 def detail(u,p):
  if u is None:return {}
  d={k:v for k,v in u.items() if k!='id'};d['placement']={k:v for k,v in p.items() if k!='unit_id'} if p else None;return flatten(d)
 for id in sorted(ua.keys()|ub.keys()):
  left=ua.get(id);right=ub.get(id);diff=changes(detail(left,pa.get(id)),detail(right,pb.get(id)));status='ADDED' if left is None else 'REMOVED' if right is None else 'CHANGED' if diff else 'UNCHANGED';counts[status]+=1;expected.append(dict(unit_id=id,status=status,changes=diff,source_identity_warning=bool(left and right and left['source_ref']!=right['source_ref']),in_after=right is not None))
 ck(data['counts']==counts);ck(data['rows']==expected);ck(sum(data['counts'].values())==len(ua.keys()|ub.keys()));ck(not data['before']['operational_eligible'] and not data['after']['operational_eligible']);return data,r

def canon(c,p):
 r=c.post('/api/validate',json=p);assert r.status_code==200,r.text;return r.json()['plan']

def fixture(c,rng,n):
 p=c.get('/api/demo').json()['plan'];p.update(contract_version='scst.m2a.v1',source='USER_ENTERED',cargo_source='USER_ENTERED',vessel=None,cargo_dataset=None,units=[],placements=[]);p['hold'].update(length_mm=20,width_mm=20,height_mm=20);p['limits'].update(certificate_cargo_limit_g=100000,voyage_cargo_limit_g=5000,cargo_onboard_g=100)
 for i in range(n):
  req=rng.choice(['required','optional','excluded']);id=f'U-{i:03}';p['units'].append(dict(id=id,name=id,kind='PIPE_BUNDLE',requirement=req,length_mm=rng.randint(1,12),width_mm=rng.randint(1,12),height_mm=rng.randint(1,12),mass_g=rng.randint(1,1000)))
  if req!='excluded' and rng.random()<.7:p['placements'].append(dict(unit_id=id,x_mm=rng.randint(-2,20),y_mm=rng.randint(-2,20),z_mm=rng.choice([0,0,1]),layer=rng.choice([0,0,1]),supported_by=[],yaw_deg=rng.choice([0,90,180,270])))
 return canon(c,p)

with tempfile.TemporaryDirectory(prefix='scst-m2c-root-') as temp:
 os.environ['SCST_DATA_DIR']=temp
 with TestClient(app) as c:
  rng=random.Random(20261101)
  for _ in range(40):
   a=fixture(c,rng,rng.randint(0,35));b=copy.deepcopy(a)
   if b['units']:
    b['units'][0]['mass_g']+=1;b['units'][0]['length_mm']+=1;b['units'][0]['name']='Edited name';drop=b['units'].pop()['id'];b['placements']=[q for q in b['placements'] if q['unit_id']!=drop]
   b['units'].append(dict(id='NEW-UNIT',name='New',kind='BAR_BUNDLE',requirement='optional',length_mm=3,width_mm=2,height_mm=1,mass_g=7));b['hold']['height_mm']=18;b['hold']['name']='Changed hold';b['limits']['voyage_cargo_limit_g']=4999;b=canon(c,b);d,_=run(c,a,b);ar=copy.deepcopy(a);br=copy.deepcopy(b);rng.shuffle(ar['units']);rng.shuffle(ar['placements']);rng.shuffle(br['units']);rng.shuffle(br['placements']);ck(run(c,ar,br)[0]==d)
  a=c.get('/api/demo').json()['plan'];b=copy.deepcopy(a);b['units'][0]['mass_g']+=1;d,_=run(c,a,b);ck(d['delta']['manifest_mass_g']==1 and d['delta']['placed_mass_g']==1);ck(any(x['field']=='mass_g' and x['after']-x['before']==1 for x in next(row for row in d['rows'] if row['unit_id']==a['units'][0]['id'])['changes']))
  ref=c.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan'];source=c.post('/api/pipe-list/preview',json=ref).json()['plan'];b=copy.deepcopy(source);b['units'][0]['requirement']='required';d,r=run(c,source,b);ck(d['counts']==dict(ADDED=0,REMOVED=0,CHANGED=1,UNCHANGED=1075));ck(d['delta']['issue_count']==1);ck(len(r.content)<250000)
  generic=fixture(c,rng,0);u=copy.deepcopy(source['units'][0]);u.update(dimensions_um=None,source_ref=None);generic['units']=[u];generic=canon(c,generic);d,_=run(c,generic,source);ck(d['rows'][0]['source_identity_warning'])
  stress=copy.deepcopy(source);stress['limits']['voyage_cargo_limit_g']=32000000;stress['placements']=[dict(unit_id=u['id'],x_mm=0,y_mm=0,z_mm=0,layer=0,supported_by=[],yaw_deg=0) for u in source['units']];start=time.perf_counter();d,r=run(c,stress,source);elapsed=time.perf_counter()-start;ck(elapsed<15);ck(d['before']['issue_count']==578351 and d['after']['issue_count']==0 and d['delta']['issue_count']==-578351)
  record=c.post('/api/snapshots',json={'name':'Root compare A','plan':source}).json();path=Path(temp,'scst.sqlite3');prior=hashlib.sha256(path.read_bytes()).hexdigest();run(c,source,b);ck(hashlib.sha256(path.read_bytes()).hexdigest()==prior);ck(c.get('/api/snapshots/'+record['id']).json()['plan']==source)
  tamper=copy.deepcopy(source);tamper['units'][0]['mass_g']+=1;ck(c.post('/api/plans/compare',json={'before':source,'after':tamper}).status_code==422);ck(c.post('/api/plans/compare',json={'before':source,'after':source,'status':'APPROVED'}).status_code==422)
 os.environ.pop('SCST_DATA_DIR',None)
result={'status':'PASS','assertions':checks,'random_plan_pairs':40,'order_shuffle_repeats':40,'oracle':'Separate dict/set and integer-µm geometry/mass/issue oracle; no application comparison/evaluate helpers','source_units':1076,'one_changed_unchanged':1075,'full_issue_count_not_truncated':578351,'stress_compare_seconds':round(elapsed,3),'comparison_no_db_mutation':True,'one_gram_delta_preserved':True}
Path('docs/reviews/SCST_M2C_EVIDENCE/root-independent.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2))
