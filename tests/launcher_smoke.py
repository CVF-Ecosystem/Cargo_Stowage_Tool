"""Run the real Windows launcher on a dedicated port, then stop its process tree."""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
port = 18765
command = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'tooling/start-local.ps1', '-Port', str(port), '-NoBrowser']
proc = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
try:
    base = f'http://127.0.0.1:{port}'
    deadline = time.monotonic() + 30
    while True:
        if proc.poll() is not None:
            raise RuntimeError(f'Launcher exited early: {proc.returncode}')
        try:
            with urllib.request.urlopen(base + '/api/health', timeout=1) as r:
                health = json.load(r)
            break
        except (urllib.error.URLError, TimeoutError):
            if time.monotonic() >= deadline:
                raise RuntimeError('Launcher health timeout')
            time.sleep(.2)
    with urllib.request.urlopen(base, timeout=3) as r:
        html = r.read().decode('utf-8')
    with urllib.request.urlopen(base + '/api/demo', timeout=3) as r:
        demo = json.load(r)
    assert health['ai'] == 'off' and health['status'] == 'ok'
    assert '<div id="root">' in html
    assert demo['plan']['contract_version'] == 'scst.m1.v1'
    print(json.dumps({'launcher':command, 'health':health, 'ui_html':'ok', 'demo_contract':demo['plan']['contract_version'], 'result':'PASS'}, ensure_ascii=False, indent=2))
finally:
    subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        output = proc.communicate(timeout=5)[0].decode('utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        proc.kill(); output = proc.communicate()[0].decode('utf-8', errors='replace')
    print('Launcher output:\n' + output)
