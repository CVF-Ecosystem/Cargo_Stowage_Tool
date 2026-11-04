"""Immutable local snapshots; never expose a filesystem path through the API."""
import json
import os
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from ..domain.model import Plan
from ..domain.rules import evaluate

ROOT = Path(__file__).resolve().parents[4]

class SaveRequest(BaseModel):
    name: str = Field(min_length=1,max_length=100)
    plan: Plan

class SavedSummary(BaseModel):
    id: str
    name: str
    created_utc: str
    schema_version: str


SNAPSHOT_COLUMNS = ['id', 'name', 'created_utc', 'schema_version', 'plan_json']
SNAPSHOTS_DDL = 'CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_utc TEXT NOT NULL, schema_version TEXT NOT NULL, plan_json TEXT NOT NULL)'
REVISIONS_DDL = ('CREATE TABLE IF NOT EXISTS cargo_revisions (revision_id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, '
                 'sequence INTEGER NOT NULL, parent_revision_id TEXT NOT NULL, created_utc TEXT NOT NULL, '
                 'source_json TEXT NOT NULL, changes_json TEXT NOT NULL, content_sha256 TEXT NOT NULL, '
                 'UNIQUE(dataset_id, sequence))')
REVISIONS_COLUMNS = [('revision_id', 'TEXT'), ('dataset_id', 'TEXT'), ('sequence', 'INTEGER'),
                     ('parent_revision_id', 'TEXT'), ('created_utc', 'TEXT'), ('source_json', 'TEXT'),
                     ('changes_json', 'TEXT'), ('content_sha256', 'TEXT')]
BACKUP_NAME = 'scst.sqlite3.pre-sup02a.bak'


def _backup_once(db, directory: Path):
    """One-time copy of the pre-SUP-02A database; an existing backup is never overwritten."""
    target = directory / BACKUP_NAME
    if target.exists():
        return
    temporary = directory / (BACKUP_NAME + '.tmp')
    temporary.unlink(missing_ok=True)
    copy = sqlite3.connect(temporary)
    try:
        db.backup(copy)
    finally:
        copy.close()
    if target.exists():
        temporary.unlink(missing_ok=True)
    else:
        os.replace(temporary, target)


def _prepare(db, directory: Path, existed: bool):
    """Create or verify both tables; never drops, resets or alters existing data."""
    if not existed:
        db.execute(SNAPSHOTS_DDL)
        db.execute(REVISIONS_DDL)
        return
    columns = [row[1] for row in db.execute('PRAGMA table_info(snapshots)')]
    if columns != SNAPSHOT_COLUMNS:
        raise ValueError('Cấu trúc cơ sở dữ liệu không được hỗ trợ.')
    info = [(row[1], (row[2] or '').upper()) for row in db.execute('PRAGMA table_info(cargo_revisions)')]
    if not info:
        _backup_once(db, directory)
        db.execute(REVISIONS_DDL)
    elif info != REVISIONS_COLUMNS:
        raise ValueError('Cấu trúc bảng revision dữ liệu hàng không được hỗ trợ.')


def open_migrated(isolation_level: str | None = ''):
    """Open the local database with the schema verified/migrated. The caller closes it."""
    directory = Path(os.environ.get('SCST_DATA_DIR', str(ROOT / 'runtime-data')))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'scst.sqlite3'
    existed = path.exists()
    db = sqlite3.connect(path, timeout=5, isolation_level=isolation_level)
    try:
        _prepare(db, directory, existed)
    except BaseException:
        db.close()
        raise
    return db


@contextmanager
def connection():
    db = open_migrated()
    try:
        with db:
            yield db
    finally:
        db.close()


def save(req: SaveRequest):
    name=req.name.strip()
    if not name: raise ValueError('Tên phương án không được trống.')
    evaluate(req.plan)  # Re-evaluate the validated snapshot before persistence.
    record=SavedSummary(id=str(uuid4()),name=name,created_utc=datetime.now(timezone.utc).isoformat(),schema_version='scst.saved-plan.v1')
    with connection() as db:
        db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)', (record.id,record.name,record.created_utc,record.schema_version,req.plan.model_dump_json()))
    return record


def listing():
    with connection() as db:
        rows = db.execute('SELECT id,name,created_utc,schema_version FROM snapshots ORDER BY created_utc DESC,id DESC LIMIT 100').fetchall()
        items = []
        for row in rows:
            timestamp = datetime.fromisoformat(row[2])
            if timestamp.tzinfo is None or timestamp.utcoffset() != timezone.utc.utcoffset(timestamp):
                raise ValueError('Thời gian phương án không hợp lệ.')
            items.append(SavedSummary(id=row[0],name=row[1],created_utc=row[2],schema_version=row[3]))
        return items


def fetch_plan(identifier):
    """Load and structurally validate a saved plan without evaluating it (no revision binding)."""
    try:
        if str(UUID(identifier)) != identifier: raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError('ID phương án không hợp lệ.')
    with connection() as db:
        row=db.execute('SELECT schema_version,plan_json FROM snapshots WHERE id=?',(identifier,)).fetchone()
    if row is None: raise LookupError('Không tìm thấy phương án đã lưu.')
    if row[0]!='scst.saved-plan.v1': raise ValueError('Phiên bản phương án đã lưu không được hỗ trợ.')
    return Plan.model_validate(json.loads(row[1]))


def open_snapshot(identifier):
    return evaluate(fetch_plan(identifier))


def listing_rows():
    """Same rows, order and checks as listing(), but with the stored plan JSON (read-only)."""
    with connection() as db:
        rows = db.execute('SELECT id,name,created_utc,schema_version,plan_json FROM snapshots ORDER BY created_utc DESC,id DESC LIMIT 100').fetchall()
    items = []
    for row in rows:
        timestamp = datetime.fromisoformat(row[2])
        if timestamp.tzinfo is None or timestamp.utcoffset() != timezone.utc.utcoffset(timestamp):
            raise ValueError('Thời gian phương án không hợp lệ.')
        items.append((SavedSummary(id=row[0],name=row[1],created_utc=row[2],schema_version=row[3]), row[4]))
    return items
