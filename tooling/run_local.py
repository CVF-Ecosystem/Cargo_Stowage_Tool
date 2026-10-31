"""Single-process local server; open browser only once the API is ready."""
import argparse
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'services' / 'backend'))


def open_when_ready(port: int):
    url = f'http://127.0.0.1:{port}'
    for _ in range(60):
        try:
            with urllib.request.urlopen(url + '/api/health', timeout=0.5) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except OSError:
            time.sleep(0.25)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('port must be in 1024..65535')
    if not args.no_browser:
        threading.Thread(target=open_when_ready, args=(args.port,), daemon=True).start()
    uvicorn.run('app.main:app', host='127.0.0.1', port=args.port)
