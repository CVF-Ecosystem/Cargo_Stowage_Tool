"""Two isolated server processes prove SQLite snapshot survives restart."""
import json, os, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def call(base,path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'} if data else {})
    with urllib.request.urlopen(req,timeout=3) as r: return json.load(r)

def launch(directory):
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    env=os.environ.copy();env['SCST_DATA_DIR']=directory
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--app-dir',str(ROOT/'services'/'backend'),'--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    base=f'http://127.0.0.1:{port}'
    for _ in range(100):
        if proc.poll() is not None: raise RuntimeError('server failed to start')
        try: call(base,'/api/health'); return proc,base
        except OSError: time.sleep(.05)
    proc.terminate();raise RuntimeError('server timeout')

def stop(proc):
    proc.terminate();proc.wait(timeout=10)

with tempfile.TemporaryDirectory(prefix='scst-m2c-') as tmp:
    first,base=launch(tmp)
    try:
        a=call(base,'/api/demo')['plan']
        b=json.loads(json.dumps(a)); b['units'][0]['mass_g']+=1; b['placements'][0]['x_mm']+=1
        a=call(base,'/api/validate',a)['plan'];b=call(base,'/api/validate',b)['plan']
        saved_a=call(base,'/api/snapshots',{'name':'Comparison A fixture','plan':a})
        saved_b=call(base,'/api/snapshots',{'name':'Comparison B fixture','plan':b})
    finally: stop(first)
    second,base=launch(tmp)
    try:
        a2=call(base,'/api/snapshots/'+saved_a['id'])['plan'];b2=call(base,'/api/snapshots/'+saved_b['id'])['plan']
        assert a2==a and b2==b
        db=Path(tmp)/'scst.sqlite3'; before=db.read_bytes()
        result=call(base,'/api/plans/compare',{'before':a2,'after':b2})
        assert result['delta']['manifest_mass_g']==1 and result['counts']['CHANGED']==1
        assert db.read_bytes()==before
        print('PASS: two-process saved A/B comparison preserves exact 1g/1mm and SQLite bytes')
    finally: stop(second)
