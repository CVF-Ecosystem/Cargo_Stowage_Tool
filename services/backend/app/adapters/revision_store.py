"""Append-only store of cargo data revisions. Deliberately has no update or delete function."""
import json
from . import storage

BASE_REVISION_ID = 'BALTIMORE-PIPE-V1-1@R0000'

_INSERT = ('INSERT INTO cargo_revisions (revision_id,dataset_id,sequence,parent_revision_id,created_utc,'
           'source_json,changes_json,content_sha256) VALUES (?,?,?,?,?,?,?,?)')
_SELECT = ('SELECT revision_id,dataset_id,sequence,parent_revision_id,created_utc,source_json,changes_json,'
           'content_sha256 FROM cargo_revisions WHERE dataset_id=? ORDER BY sequence')


class ParentMismatch(Exception):
    """The caller's parent revision is no longer the latest one."""

    def __init__(self, latest: str):
        super().__init__(latest)
        self.latest = latest


def _decode(rows):
    return [{'revision_id': r[0], 'dataset_id': r[1], 'sequence': r[2], 'parent_revision_id': r[3],
             'created_utc': r[4], 'source': json.loads(r[5]), 'changes': json.loads(r[6]),
             'content_sha256': r[7]} for r in rows]


def _latest(records):
    return records[-1]['revision_id'] if records else BASE_REVISION_ID


def read_rows(dataset: str) -> list[tuple]:
    """Raw selected columns of every revision row in sequence order (source_json/changes_json undecoded)."""
    with storage.connection() as db:
        return [tuple(r) for r in db.execute(_SELECT, (dataset,)).fetchall()]


def decode_rows(rows) -> list[dict]:
    return _decode(rows)


def read_records(dataset: str) -> list[dict]:
    return _decode(read_rows(dataset))


def latest_revision_id(dataset: str) -> str:
    return _latest(read_records(dataset))


def append(dataset: str, parent_revision_id: str, build) -> dict:
    """Append one revision atomically. build(records) returns the row dict to insert and may raise to abort."""
    db = storage.open_migrated(isolation_level=None)
    try:
        db.execute('BEGIN IMMEDIATE')
        try:
            records = _decode(db.execute(_SELECT, (dataset,)).fetchall())
            latest = _latest(records)
            if parent_revision_id != latest:
                raise ParentMismatch(latest)
            row = build(records)
            db.execute(_INSERT, (row['revision_id'], dataset, row['sequence'], parent_revision_id,
                                 row['created_utc'], json.dumps(row['source'], ensure_ascii=False, sort_keys=True),
                                 json.dumps(row['changes'], ensure_ascii=False, sort_keys=True),
                                 row['content_sha256']))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:
                db.execute('ROLLBACK')
            raise
        return {**row, 'dataset_id': dataset, 'parent_revision_id': parent_revision_id}
    finally:
        db.close()
