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


@contextmanager
def connection():
    directory = Path(os.environ.get('SCST_DATA_DIR', str(ROOT / 'runtime-data')))
    directory.mkdir(parents=True,exist_ok=True)
    path = directory / 'scst.sqlite3'
    existed = path.exists()
    db = sqlite3.connect(path, timeout=5)
    try:
        if existed:
            columns = [row[1] for row in db.execute('PRAGMA table_info(snapshots)')]
            if columns != ['id', 'name', 'created_utc', 'schema_version', 'plan_json']:
                raise ValueError('Cấu trúc cơ sở dữ liệu không được hỗ trợ.')
        else:
            db.execute('CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_utc TEXT NOT NULL, schema_version TEXT NOT NULL, plan_json TEXT NOT NULL)')
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


def open_snapshot(identifier):
    try:
        if str(UUID(identifier)) != identifier: raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError('ID phương án không hợp lệ.')
    with connection() as db:
        row=db.execute('SELECT schema_version,plan_json FROM snapshots WHERE id=?',(identifier,)).fetchone()
    if row is None: raise LookupError('Không tìm thấy phương án đã lưu.')
    if row[0]!='scst.saved-plan.v1': raise ValueError('Phiên bản phương án đã lưu không được hỗ trợ.')
    return evaluate(Plan.model_validate(json.loads(row[1])))
