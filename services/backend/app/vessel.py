from pathlib import Path
import json

DATA = Path(__file__).resolve().parents[1] / 'data' / 'vessels' / 'vinafco268'
PROFILE = json.loads((DATA / 'profile.json').read_text(encoding='utf-8'))
CASES = {case['id']: case for case in PROFILE['cases']}

