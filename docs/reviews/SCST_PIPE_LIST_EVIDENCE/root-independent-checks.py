from pathlib import Path
import sys,json,random,copy,os,tempfile,time,hashlib
sys.path.insert(0,str(Path('services/backend').resolve()))
from fastapi.testclient import TestClient
from app.main import app
receipt=json.loads(Path('docs/reviews/SCST_PIPE_LIST_EVIDENCE/calculation-receipt.json').read_text(encoding='utf8'))
checks=0
def check(v):
 global checks
 assert v;checks+=1
with tempfile.TemporaryDirectory(prefix='scst-pipe-root-') as tmp:
 os.environ['SCST_DATA_DIR']=tmp
 with TestClient(app) as c:
  original=c.get('/api/vessels/vinafco268/cases/VR-SI/plan').json()['plan']
  response=c.post('/api/pipe-list/preview',json=original);check(response.status_code==200)
  e=response.json();p=e['plan'];units=p['units'];check(len(units)==1076 and len({u['id'] for u in units})==1076);check(not p['placements']);check(e['summary']['manifest_mass_g']==1125551030);check(p['vessel']==original['vessel'] and p['hold']==original['hold'] and p['limits']==original['limits'])
  for row in receipt['rows']:
   group=[u for u in units if u['source_ref']['source_row']==row['row']]
   check(len(group)==row['bundles']);check(all(u['mass_g']==row['bundle_mass_g'] and u['dimensions_um']==row['dimensions_um'] and u['source_ref']['pieces']==row['pipes_per_bundle'] for u in group))
  check(sum(u['source_ref']['pieces'] for u in units)==21226);check(sum(u['source_ref']['dimension_warning'] for u in units)==16)
  for field,val in [('mass_g',1),('length_mm',6400),('dimensions_um',[6401000,337601,295400]),('source_ref',None),('name','changed'),('kind','BAR_BUNDLE'),('id','OTHER')]:
   bad=copy.deepcopy(p);bad['units'][0][field]=val;check(c.post('/api/validate',json=bad).status_code==422);check(c.post('/api/snapshots',json={'name':'invalid','plan':bad}).status_code==422)
  for field,val in [('workbook_sha256','0'*64),('group_id','Sheet1-R003'),('bundle_index',2),('source_row',3),('pieces',1),('dimension_warning',True)]:
   bad=copy.deepcopy(p);bad['units'][0]['source_ref'][field]=val;check(c.post('/api/validate',json=bad).status_code==422)
  for mode in ['scst.m1.v1','scst.m2a.v1']:
   bad=copy.deepcopy(p);bad['contract_version']=mode;check(c.post('/api/validate',json=bad).status_code==422)
  rng=random.Random(268)
  for run in range(30):
   trial=copy.deepcopy(p);sample=rng.sample(units,18);rects=[];placements=[];out=0;overlap=0
   for u in sample:
    x=rng.randint(-10,55)*1000;y=rng.randint(-1,10)*1000;yaw=rng.choice([0,90,180,270]);dims=u['dimensions_um'];dx,dy=(dims[1],dims[0]) if yaw%180 else dims[:2]
    low=(x*1000,y*1000,0);high=(low[0]+dx,low[1]+dy,dims[2]);rects.append((u['id'],low,high));out+=any(v<0 for v in low) or any(a>b*1000 for a,b in zip(high,[56405,10343,5408]));placements.append({'unit_id':u['id'],'x_mm':x,'y_mm':y,'yaw_deg':yaw})
   for i,(_,lo,hi) in enumerate(rects):
    for _,l2,h2 in rects[i+1:]:overlap+=all(max(a,b)<min(d,f) for a,b,d,f in zip(lo,l2,hi,h2))
   trial['placements']=placements;ans=c.post('/api/validate',json=trial).json();check(ans['total_issues']==out+overlap);check(ans['summary']['placed_mass_g']==sum(u['mass_g'] for u in sample));check(ans['summary']['placed_count']==18);check(ans['status']==('DRAFT' if out+overlap else 'RULES_CHECKED'))
  stress=copy.deepcopy(p);stress['placements']=[{'unit_id':u['id'],'x_mm':0,'y_mm':0,'yaw_deg':0} for u in units]
  start=time.perf_counter();rr=c.post('/api/validate',json=stress);elapsed=time.perf_counter()-start;s=rr.json();check(s['total_issues']==578350);check(len(s['issues'])==200 and s['issues_truncated']);check(len(s['affected_unit_ids'])==1076 and s['status']=='DRAFT' and not s['basic_checks_passed']);check(len(rr.content)<2000000);check(elapsed<15)
  p['placements']=[{'unit_id':units[0]['id'],'x_mm':0,'y_mm':0,'yaw_deg':90}];record=c.post('/api/snapshots',json={'name':'Root isolated pipe snapshot','plan':p});check(record.status_code==200);opened=c.get('/api/snapshots/'+record.json()['id']);check(opened.status_code==200);check(opened.json()['plan']==c.post('/api/validate',json=p).json()['plan']);check(not opened.json()['operational_eligible'])
  saved_bytes=hashlib.sha256(Path(tmp,'scst.sqlite3').read_bytes()).hexdigest();bad=copy.deepcopy(p);bad['units'][0]['mass_g']+=1;check(c.post('/api/snapshots',json={'name':'bad','plan':bad}).status_code==422);check(hashlib.sha256(Path(tmp,'scst.sqlite3').read_bytes()).hexdigest()==saved_bytes)
 os.environ.pop('SCST_DATA_DIR',None)
out={'status':'PASS','assertions':checks,'random_layouts':30,'random_placed_per_layout':18,'oracle':'Independent raw source receipt and integer-micrometre rectangle comparison, not app helpers','all_overlap_pairs':578350,'stress_seconds':round(elapsed,3),'stress_response_bytes':len(rr.content),'issues_returned':200,'all_affected_units':1076,'isolated_snapshot_roundtrip':True,'tamper_validation_and_db_unchanged':True,'scope':'Current backend source at receipt time; final source manifest/review establishes version boundary'}
Path('docs/reviews/SCST_PIPE_LIST_EVIDENCE/root-independent-checks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
