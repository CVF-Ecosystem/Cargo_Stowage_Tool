"""Exercise first-run setup and launcher from an isolated source copy."""
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

root = Path(__file__).resolve().parents[1]
# A fresh, uniquely named copy avoids deleting or disturbing other sessions.
cold = root / '.cvf' / 'runtime' / ('m1-cold-' + str(time.time_ns()))
cold.mkdir(parents=True)
for directory in ('tooling', 'services/backend', 'apps/frontend'):
    shutil.copytree(root / directory, cold / directory, ignore=shutil.ignore_patterns('node_modules', 'dist', '__pycache__', '*.pyc', 'test-results'))
for name in ('requirements-lock.txt','requirements-dev.txt','Start-SCST.cmd'):
    shutil.copy2(root / name, cold / name)
port=18766
command=['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File','tooling/start-local.ps1','-Port',str(port),'-NoBrowser']
log = cold / 'launcher.log'
with log.open('w', encoding='utf-8') as output:
    proc=subprocess.Popen(command,cwd=cold,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        deadline=time.monotonic()+180
        while True:
            if proc.poll() is not None:
                raise RuntimeError(f'first run exited {proc.returncode}; see {log}')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/demo',timeout=1) as r:
                    data=json.load(r)
                break
            except (urllib.error.URLError, TimeoutError):
                if time.monotonic()>deadline: raise RuntimeError(f'first run timeout; see {log}')
                time.sleep(.5)
        assert data['plan']['contract_version']=='scst.m1.v1'
        assert (cold/'.venv/Scripts/python.exe').is_file() and (cold/'apps/frontend/dist/index.html').is_file()
        print(json.dumps({'result':'PASS','firstRun':'fresh venv + npm ci + build + local demo','contract':data['plan']['contract_version'],'log':str(log)},indent=2))
    finally:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        proc.wait(timeout=10)
print('Cold launcher log:')
print(log.read_text(encoding='utf-8',errors='replace'))
