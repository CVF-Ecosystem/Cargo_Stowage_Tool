"""M3a R3: the sweep-based OVERLAP detection is byte-identical to the original all-pairs loop, and fast."""
import random
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domain import rules
from app.domain.model import Plan
from app.domain.planner import preview
from app.domain.geometry import overlaps

client = TestClient(app)


def reference_overlap_pairs(boxes):
    """Frozen copy of the ORIGINAL logic: for i in placement order, for j > i in placement order."""
    out = []
    for i, (_aid, alo, ahi) in enumerate(boxes):
        for j in range(i + 1, len(boxes)):
            _bid, blo, bhi = boxes[j]
            if overlaps(alo, ahi, blo, bhi):
                out.append((i, j))
    return out


def baltimore():
    vin = client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan']
    r = client.post('/api/pipe-list/preview', json=vin)
    assert r.status_code == 200
    return r.json()['plan']


@pytest.fixture(scope='module')
def plan_dict():
    return baltimore()


def with_placements(d, placements, stacking=None):
    d = dict(d)
    d['placements'] = placements
    if stacking:
        d['stacking'] = stacking
    return Plan.model_validate(d)


def pl(uid, x, y, z=0, layer=0, supported_by=(), yaw=0):
    return dict(unit_id=uid, x_mm=x, y_mm=y, z_mm=z, layer=layer, supported_by=list(supported_by), yaw_deg=yaw)


def assert_same_as_reference(plan, monkeypatch):
    new = rules.evaluate(plan)
    with monkeypatch.context() as m:
        m.setattr(rules, '_overlap_pairs', reference_overlap_pairs)
        ref = rules.evaluate(plan)
    assert new.model_dump_json() == ref.model_dump_json()
    return new


def test_random_boxes_match_reference_pairs():
    rng = random.Random(20261105)
    for _ in range(300):
        n = rng.randint(0, 40)
        boxes = []
        for k in range(n):
            lo = tuple(rng.randint(0, 6) for _ in range(3))
            hi = tuple(a + rng.randint(0, 4) for a in lo)  # zero-size and face-touching included
            boxes.append((f'B{k}', lo, hi))
        assert rules._overlap_pairs(boxes) == reference_overlap_pairs(boxes)


def test_baltimore_single_layer_candidate_identical(plan_dict, monkeypatch):
    cand = preview(Plan.model_validate(plan_dict)).evaluation.plan
    ev = assert_same_as_reference(cand, monkeypatch)
    assert len(cand.placements) > 100 and not [i for i in ev.issues if i.code == 'OVERLAP']


def test_baltimore_columns_candidate_identical(plan_dict, monkeypatch):
    cand = preview(Plan.model_validate(plan_dict), 'columns-v1').evaluation.plan
    ev = assert_same_as_reference(cand, monkeypatch)
    assert len(cand.placements) > 900 and not [i for i in ev.issues if i.code == 'OVERLAP']


def test_pipe_plan_with_many_overlaps_truncates_identically(plan_dict, monkeypatch):
    ids = [u['id'] for u in plan_dict['units']][:40]
    plan = with_placements(plan_dict, [pl(uid, 0, 0) for uid in ids])  # identical origin: 780 overlapping pairs
    ev = assert_same_as_reference(plan, monkeypatch)
    assert ev.total_issues >= 780 and len(ev.issues) == 200 and ev.issues_truncated is True
    assert [i.code for i in ev.issues][:1] == ['OVERLAP']


def test_pipe_plan_scattered_overlaps_mixed_codes_identical(plan_dict, monkeypatch):
    rng = random.Random(7)
    ids = [u['id'] for u in plan_dict['units']][:120]
    placements = []
    for uid in ids:  # dense cluster, some z > 0 without supports, some yaw 90, some out of bounds
        placements.append(pl(uid, rng.randint(-200, 6000), rng.randint(-200, 3000), rng.choice([0, 0, 100, 250]), 0, (), rng.choice([0, 90])))
    for stacking in (None, 'COLUMNS_V1'):
        ev = assert_same_as_reference(with_placements(plan_dict, placements, stacking), monkeypatch)
        assert ev.issues_truncated is True and len(ev.issues) == 200


def test_pipe_plan_touching_faces_not_overlap(plan_dict, monkeypatch):
    exact = [u for u in plan_dict['units'] if u['dimensions_um'][0] % 1000 == 0 and u['dimensions_um'][1] % 1000 == 0][:3]
    assert len(exact) == 3
    a, b, c = exact
    # b starts exactly where a ends on X; c starts exactly where a ends on Y: face contact only.
    plan = with_placements(plan_dict, [pl(a['id'], 0, 0), pl(b['id'], a['dimensions_um'][0] // 1000, 0),
                                       pl(c['id'], 0, a['dimensions_um'][1] // 1000)])
    ev = assert_same_as_reference(plan, monkeypatch)
    assert 'OVERLAP' not in {i.code for i in ev.issues}
    nudged = with_placements(plan_dict, [pl(a['id'], 0, 0), pl(b['id'], a['dimensions_um'][0] // 1000 - 1, 0),
                                         pl(c['id'], 0, a['dimensions_um'][1] // 1000)])
    ev = assert_same_as_reference(nudged, monkeypatch)
    assert [i.unit_ids for i in ev.issues if i.code == 'OVERLAP'] == [[a['id'], b['id']]]


def synthetic(units, placements, hold=(2000, 2000, 1000)):
    base = client.get('/api/demo').json()['plan']
    base['hold'].update(length_mm=hold[0], width_mm=hold[1], height_mm=hold[2])
    base['limits'].update(certificate_cargo_limit_g=10**9, voyage_cargo_limit_g=10**9, cargo_onboard_g=0)
    tmpl = base['units'][0]
    base['units'] = [{**tmpl, **u} for u in units]
    base['placements'] = placements
    return Plan.model_validate(base)


def su(i, length=500, width=500, height=100):
    return dict(id=f'U{i:03d}', name=f'Unit {i}', kind='BAR_BUNDLE', length_mm=length, width_mm=width, height_mm=height,
                mass_g=1000, requirement='optional')


def test_synthetic_touching_identical_and_partial_overlap(monkeypatch):
    units = [su(i) for i in range(6)]
    placements = [pl('U000', 0, 0), pl('U001', 500, 0), pl('U002', 0, 500), pl('U003', 0, 0, 100, 1, ['U000']),
                  pl('U004', 0, 0), pl('U005', 250, 250)]
    ev = assert_same_as_reference(synthetic(units, placements), monkeypatch)
    pairs = [tuple(i.unit_ids) for i in ev.issues if i.code == 'OVERLAP']
    assert ('U000', 'U001') not in pairs and ('U000', 'U002') not in pairs and ('U000', 'U003') not in pairs
    assert ('U000', 'U004') in pairs and ('U000', 'U005') in pairs
    assert_same_as_reference(synthetic(units, placements).model_copy(update={'stacking': 'COLUMNS_V1'}), monkeypatch)


def test_preview_columns_v1_is_fast(plan_dict):
    plan = Plan.model_validate(plan_dict)
    for algorithm in ('guillotine-single-layer-v1', 'columns-v1'):
        t = time.perf_counter()
        preview(plan, algorithm)
        assert time.perf_counter() - t < 2.0
    t = time.perf_counter()
    r = client.post('/api/planner/preview?algorithm=columns-v1', json=plan_dict)
    assert r.status_code == 200 and time.perf_counter() - t < 2.0
