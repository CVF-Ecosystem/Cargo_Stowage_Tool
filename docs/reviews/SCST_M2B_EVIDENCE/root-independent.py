from pathlib import Path
import sys,json,copy,random,time,tempfile,os
sys.path.insert(0,str(Path('services/backend').resolve()))
from fastapi.testclient import TestClient
from app.main import app
checks=0

def check(condition):
 global checks
 assert condition
 checks+=1

def unit(id,l,w,h=1,m=1,r='optional'):
 return dict(id=id,name=id,kind='PIPE_BUNDLE',requirement=r,length_mm=l,width_mm=w,height_mm=h,mass_g=m)

def fixture(c,units,hold=(10,10,10),capacity=1000000,onboard=0):
 p=c.get('/api/demo').json()['plan'];p.update(contract_version='scst.m2a.v1',source='USER_ENTERED',cargo_source='USER_ENTERED',cargo_dataset=None,vessel=None,units=units,placements=[]);p['hold'].update(length_mm=hold[0],width_mm=hold[1],height_mm=hold[2]);p['limits'].update(certificate_cargo_limit_g=capacity,voyage_cargo_limit_g=capacity,cargo_onboard_g=onboard)
 return c.post('/api/validate',json=p).json()['plan']

def run(c,p):
 untouched=copy.deepcopy(p);r=c.post('/api/planner/preview',json=p);check(r.status_code==200);check(p==untouched);result=r.json();e=result['evaluation'];plan=e['plan'];byid={u['id']:u for u in plan['units']}
 check(all(plan[k]==p[k] for k in p if k!='placements'))
 ids=[q['unit_id'] for q in plan['placements']];missing=[q['unit_id'] for q in result['unplaced']]
 check(len(ids)==len(set(ids)) and len(missing)==len(set(missing)));check(set(ids).isdisjoint(missing) and set(ids)|set(missing)==set(byid))
 boxes=[]
 for q in plan['placements']:
  u=byid[q['unit_id']];d=u.get('dimensions_um') or [u[k]*1000 for k in ['length_mm','width_mm','height_mm']];dx,dy=(d[1],d[0]) if q['yaw_deg']==90 else d[:2]
  low=(q['x_mm']*1000,q['y_mm']*1000,0);high=(low[0]+dx,low[1]+dy,d[2]);boxes.append((low,high))
  check(q['yaw_deg'] in [0,90] and q['z_mm']==0 and q['layer']==0 and not q['supported_by']);check(all(a>=0 for a in low) and all(a<=b*1000 for a,b in zip(high,[plan['hold'][k] for k in ['length_mm','width_mm','height_mm']])));check(u['requirement']!='excluded')
 check(all(not all(max(a,b)<min(d,f) for a,b,d,f in zip(lo,l2,hi,h2)) for n,(lo,hi) in enumerate(boxes) for l2,h2 in boxes[n+1:]))
 placed_mass=sum(byid[id]['mass_g'] for id in ids);check(placed_mass==e['summary']['placed_mass_g']);check(placed_mass<=plan['limits']['voyage_cargo_limit_g']-plan['limits']['cargo_onboard_g']);check(not e['operational_eligible']);check(not any(i['code'] in ['OVERWEIGHT','OVERLAP','OUT_OF_BOUNDS','LAYER_UNSUPPORTED'] for i in e['issues']))
 for reason in result['unplaced']:
  u=byid[reason['unit_id']];d=u.get('dimensions_um') or [u[k]*1000 for k in ['length_mm','width_mm','height_mm']];h=plan['hold'];code=reason['code']
  if code=='EXCLUDED':check(u['requirement']=='excluded')
  elif code=='TOO_HIGH':check(d[2]>h['height_mm']*1000)
  elif code=='FOOTPRINT_TOO_LARGE':check(not (d[0]<=h['length_mm']*1000 and d[1]<=h['width_mm']*1000) and not(d[1]<=h['length_mm']*1000 and d[0]<=h['width_mm']*1000))
  elif code=='MASS_LIMIT':check(placed_mass+u['mass_g']>h.get('unused',plan['limits']['voyage_cargo_limit_g']-plan['limits']['cargo_onboard_g']))
  else:check(code=='HEURISTIC_NO_SPACE' and 'khác' in reason['message'])
 return result

with tempfile.TemporaryDirectory(prefix='scst-m2b-root-') as tmp:
 os.environ['SCST_DATA_DIR']=tmp
 with TestClient(app) as c:
  empty=run(c,fixture(c,[]));check(empty['evaluation']['status']=='DRAFT')
  q=run(c,fixture(c,[unit('A',3,6)],hold=(6,3,1)));check(q['evaluation']['plan']['placements'][0]['yaw_deg']==90)
  q=run(c,fixture(c,[unit('A',2,2),unit('B',2,2),unit('C',2,2),unit('D',2,2)],hold=(4,4,1),capacity=4));check(len(q['evaluation']['plan']['placements'])==4)
  q=run(c,fixture(c,[unit('A-OPTION',2,2),unit('Z-REQ',2,2,r='required'),unit('EX',1,1,r='excluded')],hold=(2,2,1),capacity=1));check([u['unit_id'] for u in q['evaluation']['plan']['placements']]==['Z-REQ']);check({r['unit_id']:r['code'] for r in q['unplaced']}=={'A-OPTION':'MASS_LIMIT','EX':'EXCLUDED'})
  for cap,count in [(2500000,0),(2500001,1)]:
   q=run(c,fixture(c,[unit('PRECISE',1,1,m=2500001)],capacity=cap));check(len(q['evaluation']['plan']['placements'])==count)
  q=run(c,fixture(c,[unit('A',1,1)],capacity=100,onboard=100));check(q['unplaced'][0]['code']=='MASS_LIMIT')
  q=run(c,fixture(c,[unit('HIGH',11,11,h=11),unit('BIG',11,11),unit('FIT-A',10,10),unit('FIT-B',10,10)],capacity=100));check({r['unit_id']:r['code'] for r in q['unplaced']}=={'HIGH':'TOO_HIGH','BIG':'FOOTPRINT_TOO_LARGE','FIT-B':'HEURISTIC_NO_SPACE'})
  rng=random.Random(20261101)
  for case in range(40):
   units=[unit(f'U-{i:03}',rng.randint(1,50),rng.randint(1,50),h=rng.randint(1,15),m=rng.randint(1,12000),r=rng.choice(['required','optional','excluded'])) for i in range(rng.randint(1,60))]
   p=fixture(c,units,hold=(rng.randint(8,100),rng.randint(8,100),10),capacity=50000,onboard=5000);a=run(c,p);b=run(c,p);check(a==b);rng.shuffle(p['units']);b=run(c,p);check(a['evaluation']['plan']['placements']==b['evaluation']['plan']['placements'] and a['unplaced']==b['unplaced'])
  ref=c.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan'];source=c.post('/api/pipe-list/preview',json=ref).json()['plan'];source['limits']['voyage_cargo_limit_g']=source['limits']['certificate_cargo_limit_g'];start=time.perf_counter();full=run(c,source);elapsed=time.perf_counter()-start;check(elapsed<15);check(0<len(full['evaluation']['plan']['placements'])<1076);check(sum(u['source_ref']['dimension_warning'] for u in full['evaluation']['plan']['units'])==16)
  limited=copy.deepcopy(source);limited['limits']['voyage_cargo_limit_g']=32000000;small=run(c,limited);check(small['evaluation']['summary']['placed_mass_g']<=32000000);check(any(r['code']=='MASS_LIMIT' for r in small['unplaced']))
  bad=copy.deepcopy(source);bad['units'][0]['mass_g']+=1;check(c.post('/api/planner/preview',json=bad).status_code==422)
  saved=c.post('/api/snapshots',json={'name':'Root M2b isolated','plan':full['evaluation']['plan']});check(saved.status_code==200);opened=c.get('/api/snapshots/'+saved.json()['id']).json();check(opened['plan']==full['evaluation']['plan'])
 os.environ.pop('SCST_DATA_DIR',None)
result={'status':'PASS','assertions':checks,'random_manifests':40,'runs_each':3,'oracle':'Independent integer-µm bounds/overlap/mass/identity/accounting, cause checks and fixed boundary cases; no optimality claim','source_bundles':1076,'source_placed':len(full['evaluation']['plan']['placements']),'source_unplaced':len(full['unplaced']),'source_placed_mass_g':full['evaluation']['summary']['placed_mass_g'],'full_source_seconds':round(elapsed,3),'mass_limit_32t_placed':len(small['evaluation']['plan']['placements']),'snapshot_roundtrip':True}
Path('docs/reviews/SCST_M2B_EVIDENCE/root-independent.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2))
