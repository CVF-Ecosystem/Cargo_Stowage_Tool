"""HARDEN-01 H-02: placed_dropped_on_rebase_count equals what rebase really drops; old fields unchanged.
Every test uses a temporary SCST_DATA_DIR; no runtime data is touched."""
import pytest
from fastapi.testclient import TestClient

from app.domain import cargo_revisions as cr
from app.main import app

client = TestClient(app)
R0 = cr.BASE_REVISION_ID
SOURCE = {'kind': 'FACTORY', 'reference': 'HARDEN-01 H2', 'received_date': '2026-11-04', 'note': 'kiểm số đếm'}
G2, G3, G4 = 'Sheet1-R002', 'Sheet1-R003', 'Sheet1-R004'
OLD_FIELDS = ('cargo_revision_id', 'recheck_status', 'added_count', 'removed_count', 'changed_count', 'placed_affected_count')


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def latest_id():
    return client.get('/api/cargo-revisions').json()['latest_revision_id']


def create(changes):
    r = client.post('/api/cargo-revisions', json={'parent_revision_id': latest_id(), 'source': SOURCE, 'changes': changes})
    assert r.status_code == 200, r.text


def update(group, confirmation='CONFIRMED', **fields):
    return {'type': 'UPDATE_GROUP', 'group_id': group, 'confirmation': confirmation, 'set': fields}


def roomy():
    plan = client.get('/api/demo').json()['plan']
    plan['hold'].update(length_mm=20000, width_mm=9000, height_mm=4000)
    plan['limits'].update(certificate_cargo_limit_g=10 ** 10, voyage_cargo_limit_g=10 ** 10, cargo_onboard_g=0)
    return plan


def v1_plan():
    r = client.post('/api/pipe-list/preview', json=roomy())
    assert r.status_code == 200, r.text
    return r.json()['plan']


def v2_plan():
    r = client.post(f'/api/cargo-revisions/{latest_id()}/plan-preview', json=roomy())
    assert r.status_code == 200, r.text
    return r.json()['plan']


def place(plan, *units):
    plan['placements'] = [dict(unit_id=u, x_mm=0, y_mm=400 * i, z_mm=0, layer=0, supported_by=[], yaw_deg=0)
                          for i, u in enumerate(units)]
    return plan


def save(plan, name):
    r = client.post('/api/snapshots', json={'name': name, 'plan': plan})
    assert r.status_code == 200, r.text
    return r.json()['id']


def item(sid):
    r = client.get('/api/snapshots')
    assert r.status_code == 200, r.text
    return next(i for i in r.json() if i['id'] == sid)


def rebase_dropped(sid):
    r = client.post(f'/api/snapshots/{sid}/rebase')
    assert r.status_code == 200, r.text
    return r.json()['dropped_placements']


def assert_matches_rebase(sid, expected_dropped, expected_affected):
    it = item(sid)
    dropped = rebase_dropped(sid)
    assert it['placed_dropped_on_rebase_count'] == len(dropped) == expected_dropped
    assert it['placed_affected_count'] == expected_affected
    return it, dropped


PLACED = ('PIPE-R002-B0001', 'PIPE-R003-B0019', 'PIPE-R004-B0001')


def test_new_field_is_zero_when_current_and_not_applicable():
    sid_v1 = save(place(v1_plan(), *PLACED), 'v1')
    sid_m1 = save(client.get('/api/demo').json()['plan'], 'm1')
    assert item(sid_v1)['recheck_status'] == 'CURRENT' and item(sid_v1)['placed_dropped_on_rebase_count'] == 0
    assert item(sid_m1)['recheck_status'] == 'NOT_APPLICABLE' and item(sid_m1)['placed_dropped_on_rebase_count'] == 0


def test_removed_bundles_v1_plan():
    """v1 plan pinned to R0000: shrinking a group removes a placed bundle -> dropped as REMOVED."""
    sid = save(place(v1_plan(), *PLACED), 'v1')
    create([update(G3, bundle_count=18)])
    it, dropped = assert_matches_rebase(sid, 1, 1)
    assert [(d['unit_id'], d['reason']) for d in dropped] == [('PIPE-R003-B0019', 'REMOVED')]
    assert it['removed_count'] == 2 and it['recheck_status'] == 'NEEDS_RECHECK'


def test_mass_change_v2_plan():
    create([update(G4, 'UNVERIFIED', pieces_per_bundle=9)])  # make the plan v2 at R0001
    sid = save(place(v2_plan(), *PLACED), 'v2')
    create([update(G2, mass_g=900000)])
    _, dropped = assert_matches_rebase(sid, 1, 1)
    assert [(d['unit_id'], d['reason']) for d in dropped] == [('PIPE-R002-B0001', 'CHANGED')]


def test_confirmation_or_pipe_count_only_changes_drop_nothing():
    """Changes that keep dimensions and mass: placed bundles count as affected but rebase keeps them all (0)."""
    sid = save(place(v1_plan(), *PLACED), 'v1')
    create([update(G2, 'CONFIRMED', dimension_warning=False)])
    create([update(G4, 'CONFIRMED', pieces_per_bundle=9)])
    it, dropped = assert_matches_rebase(sid, 0, item(sid)['placed_affected_count'])
    assert it['recheck_status'] == 'NEEDS_RECHECK' and it['placed_affected_count'] >= 1 and dropped == []


def test_mixed_batch_counts_equal_rebase_and_old_fields_unchanged():
    sid = save(place(v1_plan(), *PLACED), 'v1')
    create([update(G2, mass_g=900000), update(G3, bundle_count=18), update(G4, 'CONFIRMED', pieces_per_bundle=9)])
    it, dropped = assert_matches_rebase(sid, 2, 3)
    assert sorted((d['unit_id'], d['reason']) for d in dropped) == [('PIPE-R002-B0001', 'CHANGED'),
                                                                  ('PIPE-R003-B0019', 'REMOVED')]
    assert set(OLD_FIELDS) <= set(it)


def test_revision_unavailable_reports_zero(data):
    import sqlite3
    sid = save(place(v1_plan(), *PLACED), 'v1')
    create([update(G2, mass_g=900000)])
    con = sqlite3.connect(data / 'scst.sqlite3')
    con.execute("UPDATE cargo_revisions SET content_sha256='0'")
    con.commit()
    con.close()
    it = item(sid)
    assert it['recheck_status'] == 'REVISION_UNAVAILABLE' and it['placed_dropped_on_rebase_count'] == 0
