"""M5a repair round 1: export error text carries no paths (R1); blocking backup work runs off the event loop (R2).

Every test uses a temporary SCST_DATA_DIR; no runtime data is touched.
"""
import asyncio
import hashlib
import sqlite3
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from app.adapters import backup_check, backup_export
from app.main import app

EXPORT_MESSAGE = 'Không tạo được bản sao lưu từ dữ liệu local.'


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    live = tmp_path / 'data'
    live.mkdir()
    monkeypatch.setenv('SCST_DATA_DIR', str(live))
    return live


# ------------------------------------------------------------------ R1: no paths in export errors
@pytest.mark.parametrize('exc', [
    OSError(2, 'No such file', '/very/secret/abs/path/scst.sqlite3'),
    sqlite3.OperationalError('unable to open database file /very/secret/x'),
    ValueError('bad input at /very/secret/y'),
])
def test_export_failure_message_is_fixed_and_path_free(exc, data, tmp_path, monkeypatch):
    def boom():
        raise exc
    monkeypatch.setattr(backup_export, 'export_bytes', boom)
    client = TestClient(app)

    response = client.get('/api/backup/export')

    assert response.status_code == 400
    assert response.json()['detail'] == {'message': EXPORT_MESSAGE, 'errors': []}
    assert '/very/secret' not in response.text
    assert str(data) not in response.text
    assert str(tmp_path) not in response.text


# ------------------------------------------------------------------ R2: preview/apply do not block the loop
def _valid_body() -> bytes:
    """A real scst.backup.v1 archive built from the empty temporary data directory."""
    return backup_export.export_bytes()[0]


def _gate_check(monkeypatch, entered: threading.Event, release: threading.Event):
    """Wrap the real check: signal when it starts, then hold it until released. The result stays the real one."""
    real_check = backup_check.check

    def gated(body, workdir):
        entered.set()
        assert release.wait(10), 'test did not release the blocked check'
        return real_check(body, workdir)
    monkeypatch.setattr(backup_check, 'check', gated)


async def _health_while_blocked(call, entered: threading.Event, release: threading.Event):
    """Run `call` on an ASGI client, then prove /api/health answers while `call` is blocked in its worker."""
    loop = asyncio.get_running_loop()
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            task = asyncio.create_task(call(client))
            deadline = loop.time() + 10
            while not entered.is_set():
                assert loop.time() < deadline, 'blocking step never started'
                await asyncio.sleep(0.01)
            health = await asyncio.wait_for(client.get('/api/health'), timeout=5)
            assert health.status_code == 200
            assert not task.done(), 'call finished before it was released'
            release.set()
            return await asyncio.wait_for(task, timeout=10)
    finally:
        release.set()


def test_preview_does_not_block_health(data, monkeypatch):
    body = _valid_body()
    entered, release = threading.Event(), threading.Event()
    _gate_check(monkeypatch, entered, release)

    async def call(client):
        return await client.post('/api/backup/restore/preview', content=body)

    response = asyncio.run(_health_while_blocked(call, entered, release))

    assert response.status_code == 200, response.text
    assert response.json()['backup_sha256'] == hashlib.sha256(body).hexdigest()


def test_apply_does_not_block_health(data, monkeypatch):
    body = _valid_body()
    confirm = hashlib.sha256(body).hexdigest()
    entered, release = threading.Event(), threading.Event()
    _gate_check(monkeypatch, entered, release)

    async def call(client):
        return await client.post('/api/backup/restore/apply', params={'confirm': confirm}, content=body)

    response = asyncio.run(_health_while_blocked(call, entered, release))

    assert response.status_code == 200, response.text
    assert set(response.json()) == {'counts', 'pre_restore_backup'}
