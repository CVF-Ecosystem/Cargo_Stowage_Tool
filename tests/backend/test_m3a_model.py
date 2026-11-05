"""M3a D1 / M3A-01: optional Plan.stacking, omitted from JSON when absent; legacy bytes unchanged."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.domain.model import Issue, Plan
from app.main import app

client = TestClient(app)
NEW_CODES = ("SUPPORT_MISSING", "SUPPORT_LEVEL_MISMATCH", "SUPPORT_AREA_LOW", "SUPPORT_CENTRE_UNSUPPORTED", "LAYER_INDEX_INVALID")


def demo_plan():
    return client.get('/api/demo').json()['plan']


def test_absent_stacking_is_omitted_and_round_trips_byte_identical():
    raw = demo_plan()
    assert 'stacking' not in raw
    plan = Plan.model_validate(raw)
    assert plan.stacking is None
    dumped = plan.model_dump(mode='json')
    assert 'stacking' not in dumped and dumped == raw
    assert Plan.model_validate_json(plan.model_dump_json()).model_dump_json() == plan.model_dump_json()
    assert '"stacking"' not in client.get('/api/demo').text
    assert '"stacking"' not in client.get('/api/vessels/vinafco268/cases/VR-SII/plan').text


@pytest.mark.parametrize('mode', ['SINGLE_LAYER', 'COLUMNS_V1'])
def test_explicit_stacking_is_kept(mode):
    plan = Plan.model_validate({**demo_plan(), 'stacking': mode})
    assert plan.model_dump(mode='json')['stacking'] == mode
    assert Plan.model_validate_json(plan.model_dump_json()).stacking == mode


def test_unknown_stacking_rejected():
    with pytest.raises(ValidationError):
        Plan.model_validate({**demo_plan(), 'stacking': 'FOO'})
    assert client.post('/api/validate', json={**demo_plan(), 'stacking': 'FOO'}).status_code == 422


def test_schema_lists_stacking_and_new_issue_codes():
    assert set(Plan.model_json_schema()['properties']['stacking']['anyOf'][0]['enum']) == {'SINGLE_LAYER', 'COLUMNS_V1'}
    for code in NEW_CODES:
        Issue(code=code, unit_ids=[], message='x')
