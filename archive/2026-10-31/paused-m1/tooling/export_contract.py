"""Run with project venv; generated schema is the source for frontend types."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'services' / 'backend'))
from app.main import app  # noqa: E402

target = root / 'contracts' / 'openapi.json'
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(target)
