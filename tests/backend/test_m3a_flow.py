"""M3a M3A-05 backend flow: Baltimore list in VINAFCO VR-SII -> columns-v1 -> apply/validate -> save -> open -> report/XLSX
-> new cargo revision -> recheck -> rebase. Rebase choice: placements resting on a dropped placement are dropped too
(reason SUPPORT_LOST, transitively), so the candidate keeps valid support geometry; recheck counts the same drops.
Every test uses a temporary SCST_DATA_DIR."""
import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SOURCE = {'kind': 'FACTORY', 'reference': 'M3A flow', 'received_date': '2026-11-05', 'note': 'kiểm nhiều tầng'}
GEOMETRY = {'OUT_OF_BOUNDS', 'OVERLAP', 'LAYER_UNSUPPORTED', 'EMPTY_MANIFEST', 'SUPPORT_MISSING', 'SUPPORT_LEVEL_MISMATCH',
            'SUPPORT_AREA_LOW', 'SUPPORT_CENTRE_UNSUPPORTED', 'LAYER_INDEX_INVALID'}


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def ok(r):
    assert r.status_code == 200, r.text
    return r.json()


def geometry(evaluation):
    return [i for i in evaluation['issues'] if i['code'] in GEOMETRY]


def planned():
    vin = ok(client.get('/api/vessels/vinafco268/cases/VR-SII/plan'))['plan']
    plan = ok(client.post('/api/pipe-list/preview', json=vin))['plan']
    preview = ok(client.post('/api/planner/preview', params={'algorithm': 'columns-v1'}, json=plan))
    return plan, preview


def test_multi_layer_flow_save_open_report_revision_rebase():
    plan, preview = planned()
    assert preview['algorithm'] == 'columns-v1'
    candidate = preview['evaluation']['plan']
    assert candidate['stacking'] == 'COLUMNS_V1' and len(candidate['placements']) >= 900
    applied = ok(client.post('/api/validate', json=candidate))
    assert geometry(applied) == [] and applied['plan']['placements'] == candidate['placements']
    assert 'Tải chồng cho phép trên bó (chưa có dữ liệu)' in applied['unchecked']
    assert max(p['layer'] for p in candidate['placements']) >= 1

    sid = ok(client.post('/api/snapshots', json={'name': 'Nhiều tầng', 'plan': applied['plan']}))['id']
    opened = ok(client.get(f'/api/snapshots/{sid}'))
    opened_plan = opened.get('plan') or opened['evaluation']['plan']
    assert opened_plan['placements'] == candidate['placements'] and opened_plan['stacking'] == 'COLUMNS_V1'

    report = ok(client.get(f'/api/snapshots/{sid}/report'))
    codes = [n['code'] for n in report['notices']]
    assert 'MULTI_LAYER' in codes and 'SINGLE_LAYER' not in codes
    assert report['stacking'] == 'COLUMNS_V1'
    assert report['totals']['layer_count'] == max(p['layer'] for p in candidate['placements']) + 1
    assert report['totals']['column_count'] == sum(1 for p in candidate['placements'] if p['z_mm'] == 0)
    stacked = next(u for u in report['units'] if u['placement'] and u['placement']['layer'] > 0)
    assert stacked['placement']['supported_by'] and stacked['placement']['z_mm'] > 0
    xlsx = client.get(f'/api/snapshots/{sid}/report.xlsx')
    assert xlsx.status_code == 200
    sheets = ''.join(zipfile.ZipFile(io.BytesIO(xlsx.content)).read(n).decode() for n in zipfile.ZipFile(io.BytesIO(xlsx.content)).namelist() if n.endswith('.xml'))
    assert 'Tầng' in sheets and 'Bó đỡ' in sheets and 'Tổng số tầng' in sheets

    # A group whose bundles carry bundles of other groups: changing its mass drops it and, by support, the bundles above.
    group_of = {u['id']: u['source_ref']['group_id'] for u in plan['units']}
    mass_of = {u['id']: u['mass_g'] for u in plan['units']}
    by_id = {p['unit_id']: p for p in candidate['placements']}
    group = next(group_of[p['supported_by'][0]] for p in candidate['placements']
                 if p['supported_by'] and group_of[p['supported_by'][0]] != group_of[p['unit_id']])
    member = next(u for u in by_id if group_of[u] == group)
    parent = ok(client.get('/api/cargo-revisions'))['latest_revision_id']
    ok(client.post('/api/cargo-revisions', json={'parent_revision_id': parent, 'source': SOURCE, 'changes': [
        {'type': 'UPDATE_GROUP', 'group_id': group, 'confirmation': 'CONFIRMED', 'set': {'mass_g': mass_of[member] - 1000}}]}))

    listing = next(i for i in ok(client.get('/api/snapshots')) if i['id'] == sid)
    assert listing['recheck_status'] == 'NEEDS_RECHECK'
    rebased = ok(client.post(f'/api/snapshots/{sid}/rebase'))
    dropped = rebased['dropped_placements']
    reasons = {d['unit_id']: d['reason'] for d in dropped}
    assert listing['placed_dropped_on_rebase_count'] == len(dropped)
    assert {u for u, r in reasons.items() if r == 'CHANGED'} == {u for u in by_id if group_of[u] == group}
    lost = {u for u, r in reasons.items() if r == 'SUPPORT_LOST'}
    assert lost and all(group_of[u] != group for u in lost)
    for u in lost:  # each lost bundle rests on a dropped bundle
        assert any(s in reasons for s in by_id[u]['supported_by'])
    kept = rebased['candidate']['plan']['placements']
    assert len(kept) == rebased['kept_placement_count'] == len(by_id) - len(dropped)
    assert rebased['candidate']['plan']['stacking'] == 'COLUMNS_V1'
    assert geometry(rebased['candidate']) == []
    # The rebase candidate is saved as a new current plan and reopens unchanged.
    sid_b = ok(client.post('/api/snapshots', json={'name': 'Nhiều tầng B', 'plan': rebased['candidate']['plan']}))['id']
    again = ok(client.get(f'/api/snapshots/{sid_b}'))
    assert (again.get('plan') or again['evaluation']['plan'])['placements'] == kept
    assert next(i for i in ok(client.get('/api/snapshots')) if i['id'] == sid_b)['recheck_status'] == 'CURRENT'


def test_planner_columns_is_deterministic_and_single_layer_report_unchanged():
    plan, first = planned()
    _, second = planned()
    assert first == second
    single = ok(client.post('/api/planner/preview', json=plan))
    assert single['algorithm'] == 'guillotine-single-layer-v1' and 'stacking' not in single['evaluation']['plan']
    sid = ok(client.post('/api/snapshots', json={'name': 'Một tầng', 'plan': single['evaluation']['plan']}))['id']
    report = ok(client.get(f'/api/snapshots/{sid}/report'))
    assert 'stacking' not in report and 'layer_count' not in report['totals']
    assert all('supported_by' not in u['placement'] for u in report['units'] if u['placement'])
    assert 'SINGLE_LAYER' in [n['code'] for n in report['notices']]
