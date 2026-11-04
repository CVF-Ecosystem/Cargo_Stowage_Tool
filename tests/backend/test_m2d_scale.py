"""M2D-03 scale: real (unmocked) report XLSX for 1076 units over the API and 2000 units through the pure domain path.
Read-only proof for the real writer: snapshot row and DB file bytes are unchanged by report/XLSX calls."""
import hashlib
import io
import sqlite3
import time
import zipfile
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from app.domain import cargo_revisions as cr
from app.domain.model import Plan
from app.domain.report import build_report, reconcile
from app.domain.report.xlsx import write_xlsx
from app.domain.rules import evaluate
from app.main import app

client = TestClient(app)
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def _exact_units(xlsx_bytes):
    """-> {unit id: (um x3, g)} from the 'Hàng' sheet exact columns (U..W µm, AA g)."""
    sheet = ET.fromstring(zipfile.ZipFile(io.BytesIO(xlsx_bytes)).read('xl/worksheets/sheet2.xml'))
    out = {}
    for row in sheet.find('m:sheetData', NS)[1:]:
        cells = {c.get('r').rstrip('0123456789'): c for c in row}
        uid = cells['A'].find('m:is/m:t', NS).text
        assert all(cells[k].get('t') is None for k in ('U', 'V', 'W', 'AA'))
        out[uid] = (tuple(int(cells[k].find('m:v', NS).text) for k in ('U', 'V', 'W')), int(cells['AA'].find('m:v', NS).text))
    return out


def test_real_xlsx_for_1076_unit_vinafco_plan_is_exact_fast_and_read_only(data):
    vin = client.get('/api/vessels/vinafco268/cases/VR-SII/plan').json()['plan']
    plan = client.post('/api/planner/preview', json=client.post('/api/pipe-list/preview', json=vin).json()['plan']).json()['evaluation']['plan']
    sid = client.post('/api/snapshots', json={'name': 'VINAFCO Baltimore — báo cáo', 'plan': plan}).json()['id']
    before = hashlib.sha256((data / 'scst.sqlite3').read_bytes()).hexdigest()
    started = time.perf_counter()
    first = client.get(f'/api/snapshots/{sid}/report.xlsx')
    elapsed = time.perf_counter() - started
    second = client.get(f'/api/snapshots/{sid}/report.xlsx')
    print(f'\nM2D real XLSX over HTTP for 1076 units: {elapsed:.3f} s, {len(first.content)} bytes')
    assert first.status_code == 200 and first.content == second.content and elapsed < 10
    assert hashlib.sha256((data / 'scst.sqlite3').read_bytes()).hexdigest() == before
    exact = _exact_units(first.content)
    assert len(exact) == 1076
    for u in plan['units']:
        assert exact[u['id']] == (tuple(u['dimensions_um']), u['mass_g'])


def test_2000_unit_report_and_xlsx_through_the_domain_path():
    units = [{'id': f'PIPE-X{i:04d}-B0001', 'name': f'Ống thử {i}', 'kind': 'PIPE_BUNDLE', 'requirement': 'optional',
              'length_mm': 6001, 'width_mm': 338, 'height_mm': 296, 'mass_g': 900_001 + i, 'dimensions_um': [6_000_123, 337_600, 295_400],
              'source_ref': {'dataset_id': cr.DATASET, 'workbook_sha256': '0' * 64, 'sheet': 'Sheet1', 'group_id': 'Sheet1-R002',
                             'source_row': 2, 'bundle_index': 1, 'pieces': 42, 'dimension_warning': False,
                             'revision_id': cr.revision_id(1), 'confirmation': 'CONFIRMED'}} for i in range(2000)]
    placements = [{'unit_id': units[i]['id'], 'x_mm': (i // 100) * 6100, 'y_mm': (i % 100) * 340, 'yaw_deg': 0} for i in range(500)]
    plan = Plan.model_validate({'contract_version': 'scst.pipe-list.v2', 'cargo_source': 'DOCUMENT_CALCULATED', 'cargo_dataset': cr.DATASET,
                                'cargo_revision': {'dataset_id': cr.DATASET, 'revision_id': cr.revision_id(1), 'content_sha256': 'a' * 64},
                                'hold': {'id': 'H1', 'name': 'Hầm thử 2000', 'length_mm': 130_000, 'width_mm': 34_000, 'height_mm': 3_000},
                                'limits': {'certificate_cargo_limit_g': 10 ** 12, 'voyage_cargo_limit_g': 10 ** 12},
                                'units': units, 'placements': placements})
    started = time.perf_counter()
    evaluation = evaluate(plan)
    report = build_report(snapshot_id='00000000-0000-4000-8000-000000000000', name='Thử 2000 bó', saved_utc='2026-11-04T10:00:00+00:00',
                          plan_json=plan.model_dump_json(), plan=plan, evaluation=evaluation, profile=None,
                          recheck={'status': 'CURRENT', 'latest_revision_id': cr.revision_id(1), 'added': 0, 'removed': 0, 'changed': 0, 'placed_affected': 0},
                          packing=None, revision={'revision_id': cr.revision_id(1), 'content_sha256': 'a' * 64}, generated_utc='2026-11-04T10:00:01+00:00')
    reconcile(report, evaluation)
    built = time.perf_counter() - started
    started = time.perf_counter()
    blob = write_xlsx(report)
    written = time.perf_counter() - started
    print(f'\nM2D 2000 units: evaluate+build+reconcile {built:.3f} s, XLSX {written:.3f} s, {len(blob)} bytes')
    assert built + written < 30 and report['totals']['placed_count'] == 500 and evaluation.basic_checks_passed
    exact = _exact_units(blob)
    assert len(exact) == 2000 and all(exact[u['id']] == (tuple(u['dimensions_um']), u['mass_g']) for u in units)
