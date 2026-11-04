"""HARDEN-01 H3: in-process replay cache keyed by the raw DB rows. Integrity checks must stay as strict as uncached."""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.adapters import plan_binding
from app.domain import cargo_revisions as cr
from app.main import app

client = TestClient(app)
R0 = cr.BASE_REVISION_ID
R1, R2, R3 = cr.revision_id(1), cr.revision_id(2), cr.revision_id(3)
SOURCE = {'kind': 'FACTORY', 'reference': 'PO-2026-11 / chứng từ nhà máy', 'received_date': '2026-11-02', 'note': 'cân thực tế'}


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def latest_id():
    return client.get('/api/cargo-revisions').json()['latest_revision_id']


def add(count=2, mass=500000):
    group = {'bundle_count': count, 'pieces_per_bundle': 10, 'dimensions_um': [6000000, 300000, 300000], 'mass_g': mass,
             'outside_diameter_mm': '60.3', 'wall_thickness_mm': '3.91', 'dimension_warning': False}
    r = client.post('/api/cargo-revisions', json={
        'parent_revision_id': latest_id(), 'source': SOURCE,
        'changes': [{'type': 'ADD_GROUP', 'confirmation': 'UNVERIFIED', 'group': group}]})
    assert r.status_code == 200, r.text


def make(n=3):
    for i in range(n):
        add(mass=500000 + i)


def warm():
    assert client.get('/api/cargo-revisions').status_code == 200
    for rid in (R1, R2, R3)[:len(by_id()) - 1]:
        assert client.get(f'/api/cargo-revisions/{rid}').status_code == 200


def edit(data, sql, *args):
    con = sqlite3.connect(data / 'scst.sqlite3')
    con.execute(sql, args)
    con.commit()
    con.close()


def by_id():
    return {r['revision_id']: r for r in client.get('/api/cargo-revisions').json()['revisions']}


@pytest.fixture
def replays(monkeypatch):
    calls = []
    real = cr.replay

    def spy(registry, records):
        calls.append(len(records))
        return real(registry, records)
    monkeypatch.setattr(plan_binding.cr, 'replay', spy)
    return calls


def test_hand_edited_hash_after_warm_cache_is_refused(data):
    make()
    warm()
    assert all(r['available'] for r in by_id().values())
    edit(data, 'UPDATE cargo_revisions SET content_sha256=? WHERE revision_id=?', '0' * 64, R2)
    items = by_id()
    assert items[R1]['available'] and not items[R2]['available'] and not items[R3]['available']
    assert items[R2]['integrity_error']
    assert client.get(f'/api/cargo-revisions/{R1}').status_code == 200
    bad = client.get(f'/api/cargo-revisions/{R2}')
    assert bad.status_code == 400 and bad.json()['detail']['message']


def test_hand_edited_changes_json_after_warm_cache_is_refused(data):
    make(2)
    warm()
    other = '[{"type":"ADD_GROUP","confirmation":"UNVERIFIED","group":{"bundle_count":5,"pieces_per_bundle":10,' \
            '"dimensions_um":[6000000,300000,300000],"mass_g":1,"outside_diameter_mm":"60.3","wall_thickness_mm":"3.91",' \
            '"dimension_warning":false}}]'
    edit(data, 'UPDATE cargo_revisions SET changes_json=? WHERE revision_id=?', other, R1)
    assert client.get(f'/api/cargo-revisions/{R1}').status_code == 400
    assert not by_id()[R1]['available']


def test_hand_edited_created_utc_is_reflected_not_masked(data):
    make(2)
    warm()
    before = client.get(f'/api/cargo-revisions/{R1}').json()['created_utc']
    edit(data, 'UPDATE cargo_revisions SET created_utc=? WHERE revision_id=?', '2001-01-01T00:00:00+00:00', R1)
    after = client.get(f'/api/cargo-revisions/{R1}').json()['created_utc']
    assert before != after == '2001-01-01T00:00:00+00:00'
    assert by_id()[R2]['available']


def test_second_identical_read_skips_replay_and_new_revision_misses(replays):
    make(2)
    plan_binding.clear_replay_cache()
    assert client.get(f'/api/cargo-revisions/{R2}').status_code == 200
    first = len(replays)
    assert first >= 1
    replays.clear()
    for _ in range(2):
        assert client.get(f'/api/cargo-revisions/{R2}').status_code == 200
        assert client.get('/api/cargo-revisions').status_code == 200
    assert replays == []
    keys = set(plan_binding._REPLAY_CACHE)
    add(mass=7)  # R3: a different prefix, so a different key (and a real replay while it is created)
    assert replays and set(plan_binding._REPLAY_CACHE) > keys
    replays.clear()
    assert client.get(f'/api/cargo-revisions/{R3}').status_code == 200
    assert client.get('/api/cargo-revisions').status_code == 200
    assert replays == []
    plan_binding.clear_replay_cache()  # cold again -> replays exactly the R0003 prefix
    assert client.get(f'/api/cargo-revisions/{R3}').status_code == 200
    assert replays == [3]


def test_mutating_a_returned_view_cannot_corrupt_the_cache():
    make(2)
    plan_binding.clear_replay_cache()
    first = plan_binding.view(R2)
    groups, changes = len(first['groups']), len(first['changes'])
    assert groups > 0
    first['groups'].clear()
    first['changes'].clear()
    first['groups_extra'] = 1
    again = plan_binding.view(R2)
    assert len(again['groups']) == groups and len(again['changes']) == changes and 'groups_extra' not in again
    _, views = plan_binding.servable_views()
    views[-1]['groups'].clear()
    assert len(plan_binding.view(R2)['groups']) == groups


def test_cache_is_bounded():
    make(3)
    plan_binding.clear_replay_cache()
    for _ in range(3):
        add()
        for rid in (R1, R2, R3):
            client.get(f'/api/cargo-revisions/{rid}')
        client.get('/api/cargo-revisions')
        assert len(plan_binding._REPLAY_CACHE) <= 8
    for i in range(20):
        plan_binding._replay([('x', i)], [])
        assert len(plan_binding._REPLAY_CACHE) <= 8
    assert len(plan_binding._REPLAY_CACHE) == 8


def test_failed_entry_reraises_same_error_on_hit(data, replays):
    make(2)
    edit(data, 'UPDATE cargo_revisions SET content_sha256=? WHERE revision_id=?', '0' * 64, R2)
    plan_binding.clear_replay_cache()
    with pytest.raises(plan_binding.RevisionUnavailable) as first:
        plan_binding.view(R2)
    n = len(replays)
    assert n >= 1
    with pytest.raises(plan_binding.RevisionUnavailable) as second:
        plan_binding.view(R2)
    assert len(replays) == n
    assert (second.value.revision_id, str(second.value)) == (first.value.revision_id, str(first.value)) == (R2, str(first.value))
    assert client.get(f'/api/cargo-revisions/{R2}').status_code == 400
