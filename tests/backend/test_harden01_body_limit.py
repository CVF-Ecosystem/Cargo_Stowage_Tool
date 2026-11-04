"""HARDEN-01 H4 / O5: oversize request bodies are refused before FastAPI parses them.

Cargo revision POSTs refuse above cargo.MAX_PAYLOAD_BYTES (1 MiB); vessel-profile uploads refuse above 28 MiB.
Every test uses a temporary SCST_DATA_DIR; no runtime data is touched.
"""
import asyncio
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest

from app.adapters import vessel_profile_service as profiles
from app.domain import cargo_revisions as cr
from app.main import app

client = TestClient(app)
LIMIT = cr.MAX_PAYLOAD_BYTES
PATHS = ['/api/cargo-revisions', '/api/cargo-revisions/preview']
JSON = {'content-type': 'application/json'}
REJECT = {'message': 'Dữ liệu gửi lên quá lớn.',
          'errors': [{'index': None, 'field': 'payload', 'message': 'Dữ liệu gửi lên vượt quá 1048576 byte (1 MiB).'}]}
G2 = 'Sheet1-R002'
SOURCE = {'kind': 'FACTORY', 'reference': 'PO-2026-11 / chứng từ nhà máy', 'received_date': '2026-11-02', 'note': 'cân thực tế'}


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv('SCST_DATA_DIR', str(tmp_path))
    return tmp_path


def revision_rows(data):
    if not (data / 'scst.sqlite3').exists():
        return 0
    con = sqlite3.connect(data / 'scst.sqlite3')
    try:
        return con.execute('SELECT COUNT(*) FROM cargo_revisions').fetchone()[0]
    finally:
        con.close()


def latest_id():
    return client.get('/api/cargo-revisions').json()['latest_revision_id']


def valid_draft():
    change = {'type': 'UPDATE_GROUP', 'group_id': G2, 'confirmation': 'CONFIRMED', 'set': {'mass_g': 900000}}
    return {'parent_revision_id': latest_id(), 'source': SOURCE, 'changes': [change]}


def asgi_post(path, chunks):
    """Drives the ASGI app with a headerless chunked body; `pulled` counts the chunks the server actually received.

    TestClient materialises generator bodies up front, so it cannot show how far the server read; this can.
    """
    feed, pulled, sent = iter(chunks), [], []

    async def receive():
        chunk = next(feed, b'')
        if chunk:
            pulled.append(len(chunk))
        return {'type': 'http.request', 'body': chunk, 'more_body': bool(chunk)}

    async def send(message):
        sent.append(message)
    scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1', 'method': 'POST', 'scheme': 'http',
             'path': path, 'raw_path': path.encode(), 'root_path': '', 'query_string': b'', 'client': ('test', 1),
             'server': ('test', 80), 'headers': [(b'content-type', b'application/json')]}
    asyncio.run(app(scope, receive, send))
    status = next(m['status'] for m in sent if m['type'] == 'http.response.start')
    body = b''.join(m.get('body', b'') for m in sent if m['type'] == 'http.response.body')
    return status, json.loads(body), pulled


# 1. Invalid JSON over the limit with Content-Length: rejected pre-parse (today this is 422).
@pytest.mark.parametrize('path', PATHS)
def test_oversize_invalid_json_with_content_length_rejected_before_parse(data, path):
    r = client.post(path, content=b'x' * (LIMIT + 1), headers=JSON)
    assert r.request.headers['content-length'] == str(LIMIT + 1)
    assert r.status_code == 400 and r.json() == {'detail': REJECT}
    assert revision_rows(data) == 0


# 2. No Content-Length (chunked body): streamed and refused as soon as the running size exceeds the limit.
@pytest.mark.parametrize('path', PATHS)
def test_chunked_body_without_content_length_rejected_and_reading_stops_early(data, path):
    status, body, pulled = asgi_post(path, [b'x' * 65536] * 64)  # 4 MiB offered; a parse-first server would read it all
    assert status == 400 and body == {'detail': REJECT}
    assert len(pulled) == 17  # 16 chunks = exactly 1 MiB (allowed); the 17th crosses the limit
    assert revision_rows(data) == 0


# 3. Declared Content-Length over the limit with a small body: refused from the header, body never streamed.
@pytest.mark.parametrize('path', PATHS)
def test_declared_length_over_limit_rejected_without_reading_body(data, path, monkeypatch):
    streamed, sizes = [], []
    real_stream, real_check = StarletteRequest.stream, cr.check_payload_size
    monkeypatch.setattr(StarletteRequest, 'stream', lambda self: streamed.append(1) or real_stream(self))
    monkeypatch.setattr(cr, 'check_payload_size', lambda size: sizes.append(size) or real_check(size))
    r = client.post(path, content=b'{}', headers=dict(JSON, **{'content-length': str(LIMIT + 5000)}))
    assert r.status_code == 400 and r.json() == {'detail': REJECT}
    assert sizes == [LIMIT + 5000] and streamed == []
    assert revision_rows(data) == 0


# 4. Normal traffic is unchanged; rejected requests never write a revision row.
def test_valid_requests_unchanged_and_rejections_write_nothing(data):
    assert client.post('/api/cargo-revisions/preview', json=valid_draft()).json()['valid']
    assert client.post('/api/cargo-revisions/preview', json=valid_draft()).status_code == 200
    assert revision_rows(data) == 0

    created = client.post('/api/cargo-revisions', json=valid_draft())
    assert created.status_code == 200, created.text
    assert revision_rows(data) == 1

    assert client.post('/api/cargo-revisions/preview', content=b'{', headers=JSON).status_code == 422
    assert client.post('/api/cargo-revisions', content=b'{', headers=JSON).status_code == 422
    assert client.post('/api/cargo-revisions', content=b'x' * (LIMIT + 1), headers=JSON).status_code == 400
    assert revision_rows(data) == 1


# 5. Vessel-profile uploads already reject pre-parse (_upload_body, 28 MiB); pinned here, not changed.
@pytest.mark.parametrize('path', ['/api/vessel-profiles/preview', '/api/vessel-profiles'])
def test_vessel_upload_declared_over_28_mib_rejected_before_parse(path):
    declared = profiles.MAX_BODY_BYTES + 1
    r = client.post(path, content=b'{}', headers=dict(JSON, **{'content-length': str(declared)}))
    assert r.status_code == 413
    assert r.json() == {'detail': {'message': 'Thân yêu cầu quá lớn.', 'errors': profiles.body_size_errors(declared)}}


@pytest.mark.parametrize('path', ['/api/vessel-profiles/preview', '/api/vessel-profiles'])
def test_vessel_upload_chunked_over_28_mib_stops_reading_early(path):
    status, body, pulled = asgi_post(path, [b'x' * (1024 * 1024)] * 40)
    assert status == 413 and body['detail']['message'] == 'Thân yêu cầu quá lớn.'
    assert len(pulled) == 29  # 28 MiB exactly is allowed; the 29th MiB crosses the limit
