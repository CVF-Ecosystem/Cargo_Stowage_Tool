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

with tempfile.TemporaryDirectory(prefix='scst-m2a-') as tmp:
    first,base=launch(tmp)
    try:
        p=call(base,'/api/vessels/vinafco268/cases/VR-SI/plan')['plan']
        p.update(contract_version='scst.m2a.v1',cargo_source='USER_ENTERED')
        p['units'][0]['name']='Synthetic restart fixture'
        result=call(base,'/api/validate',p)
        record=call(base,'/api/snapshots',{'name':'Synthetic restart fixture','plan':result['plan']})
    finally: stop(first)
    second,base=launch(tmp)
    try:
        reopened=call(base,'/api/snapshots/'+record['id'])
        assert reopened['plan']==result['plan'] and reopened['summary']==result['summary']
        assert any(x['id']==record['id'] for x in call(base,'/api/snapshots'))
        print('PASS: separate server processes preserve reference case, cargo, placements and evaluated summary')
    finally: stop(second)
