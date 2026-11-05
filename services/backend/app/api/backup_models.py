"""Response models of the local backup/restore API (M5a). Additions only; no existing contract field changes."""
from pydantic import BaseModel


class BackupCounts(BaseModel):
    plans: int
    revisions: int
    vessel_profile_versions: int


class BackupPreview(BaseModel):
    format: str
    created_utc: str
    backup_sha256: str
    counts: BackupCounts
    current: BackupCounts


class RestoreResult(BaseModel):
    counts: BackupCounts
    pre_restore_backup: str


class BackupFieldError(BaseModel):
    field: str
    message: str


class BackupRejectedDetail(BaseModel):
    message: str
    errors: list[BackupFieldError]
