"""M5b D2 automatic backup API: status, run now, download; bad names are 404; no filesystem path in any response.

Every test uses a temporary SCST_DATA_DIR; no runtime data is touched.
"""
import pytest
from fastapi.testclient import TestClient

from app.adapters import backup_auto
from app.demo import demo_plan
from app.main import app

client = TestClient(app, raise_server_exceptions=False)
RUN = '/api/backup/auto/run'


@pytest.fixture
def data(tmp_path, monkeypatch):
    root = tmp_path / 'data'
    root.mkdir()
    monkeypatch.setenv('SCST_DATA_DIR', str(root))
    monkeypatch.delenv('SCST_AUTO_BACKUP', raising=False)
    return root


def save_plan(name):
    r = client.post('/api/snapshots', json={'name': name, 'plan': demo_plan().model_dump(mode='json')})
    assert r.status_code == 200, r.text
    return r.json()['id']


def test_status_empty(data):
    r = client.get('/api/backup/auto')
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['enabled'] is True
    assert body['interval_hours'] == 20
    assert body['keep'] == 10
    assert body['files'] == []
    assert str(data.parent) not in r.text


def test_run_without_data_is_409_and_creates_nothing(data):
    r = client.post(RUN)
    assert r.status_code == 409, r.text
    detail = r.json()['detail']
    assert detail['message'] == backup_auto.NoData.message
    assert detail['errors'] == [{'field': 'body', 'message': backup_auto.NoData.message}]
    assert any(ord(ch) > 127 for ch in detail['message'])
    assert str(data.parent) not in r.text
    assert not backup_auto.auto_dir().exists() or not any(backup_auto.auto_dir().iterdir())
    assert client.get('/api/backup/auto').json()['files'] == []


def test_run_failure_is_500_with_message_and_no_path(data, monkeypatch):
    save_plan('M5B fail')

    def boom():
        raise backup_auto.AutoBackupFailed()

    monkeypatch.setattr(backup_auto, 'run_now', boom)
    r = client.post(RUN)
    assert r.status_code == 500, r.text
    assert r.json()['detail']['message'] == backup_auto.AutoBackupFailed.message
    assert str(data.parent) not in r.text


def test_run_list_and_download_round_trip(data):
    save_plan('M5B one')
    r = client.post(RUN)
    assert r.status_code == 200, r.text
    entry = r.json()
    name = entry['name']
    assert backup_auto.NAME_PATTERN.fullmatch(name)
    assert isinstance(entry['size_bytes'], int) and entry['size_bytes'] > 0
    assert entry['created_utc']
    assert str(data.parent) not in r.text

    status = client.get('/api/backup/auto')
    assert status.status_code == 200, status.text
    listed = status.json()
    assert [f['name'] for f in listed['files']] == [name]
    assert listed['files'][0]['size_bytes'] == entry['size_bytes']
    assert str(data.parent) not in status.text

    download = client.get(f'/api/backup/auto/{name}')
    assert download.status_code == 200, download.text
    assert download.headers['content-type'].startswith('application/octet-stream')
    assert f'attachment; filename="{name}"' in download.headers['content-disposition']
    assert download.content == (backup_auto.auto_dir() / name).read_bytes()
    assert str(data.parent) not in download.text


def test_second_run_lists_newest_first(data):
    save_plan('M5B first')
    first = client.post(RUN).json()['name']
    save_plan('M5B second')
    second = client.post(RUN).json()['name']
    assert second != first
    names = [f['name'] for f in client.get('/api/backup/auto').json()['files']]
    assert names == sorted([first, second], reverse=True)


@pytest.mark.parametrize('name', [
    '%2E%2E',                                  # '..'
    '..%2F..%2Fscst.sqlite3',                  # escape the backup folder to the data file
    '%5C..%5Cscst.sqlite3',                    # backslash variant
    'auto-x.scstbak',                          # matches no pattern
    'pre-restore-20260101T000000000000Z.scstbak',  # manual/pre-restore backup name, not an auto name
    'auto-20260101T000000000000Z.scstbak',     # valid pattern, file does not exist
    'auto-20260101T000000000000Z.scstbak%0A',  # trailing newline
])
def test_bad_or_missing_names_are_404_without_path(data, name):
    (data / 'scst.sqlite3').write_bytes(b'SQLite format 3\x00')
    r = client.get(f'/api/backup/auto/{name}')
    assert r.status_code == 404, r.text
    assert r.headers['content-type'].startswith('application/json')
    assert r.json()['detail'] and any(ord(ch) > 127 for ch in r.json()['detail'])
    assert str(data.parent) not in r.text
    assert 'scst.sqlite3' not in r.text


def test_existing_auto_name_outside_folder_is_404(data):
    # a file that matches the auto pattern but sits next to the folder, not inside it
    name = 'auto-20260101T000000000000Z.scstbak'
    (data / name).write_bytes(b'not in the auto folder')
    r = client.get(f'/api/backup/auto/{name}')
    assert r.status_code == 404
    assert b'not in the auto folder' not in r.content
