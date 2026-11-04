"""Typed request/response models for the cargo-revision API (SUP-02A). Pure pydantic, no logic."""
from typing import Any, Literal

from pydantic import BaseModel

from ..adapters.storage import SavedSummary
from ..domain.comparison import CompareResult
from ..domain.model import Evaluation

Confirmation = Literal['WORKBOOK', 'UNVERIFIED', 'CONFIRMED']
RecheckStatus = Literal['CURRENT', 'NEEDS_RECHECK', 'NOT_APPLICABLE', 'REVISION_UNAVAILABLE']


class BatchError(BaseModel):
    index: int | None
    field: str
    message: str


class RevisionSource(BaseModel):
    kind: str
    reference: str
    received_date: str
    note: str


class ProvenanceStamp(BaseModel):
    revision_id: str
    source: RevisionSource | None
    confirmation: Confirmation


class RevisionSummary(BaseModel):
    revision_id: str
    parent_revision_id: str | None
    created_utc: str | None
    source: RevisionSource | None
    change_count: int
    content_sha256: str
    group_count: int | None
    bundle_count: int | None
    total_mass_g: int | None
    available: bool = True
    integrity_error: str | None = None


class RevisionList(BaseModel):
    dataset_id: str
    latest_revision_id: str
    revisions: list[RevisionSummary]


class BundleOverrideInfo(BaseModel):
    bundle_id: str
    mass_g: int | None
    dimensions_um: list[int] | None
    provenance: dict[str, ProvenanceStamp]


class RevisionGroup(BaseModel):
    group_id: str
    source_row: int | None
    origin: Literal['WORKBOOK', 'ADDED']
    bundle_count: int
    pieces_per_bundle: int
    dimensions_um: list[int]
    mass_g: int
    outside_diameter_mm: str
    wall_thickness_mm: str
    dimension_warning: bool
    source_line_t: str | None
    source_cbm_m3: str | None
    envelope_cbm_m3: str | None
    issue_codes: list[str]
    bundle_ids: list[str]
    next_bundle_index: int
    provenance: dict[str, ProvenanceStamp]
    overrides: list[BundleOverrideInfo]


class RevisionDetail(RevisionSummary):
    groups: list[RevisionGroup]
    changes: list[dict[str, Any]]


class RevisionDraft(BaseModel):
    parent_revision_id: str
    source: dict[str, Any]
    changes: list[dict[str, Any]]


class ChangeSummary(BaseModel):
    index: int
    type: str
    target: str
    text: str


class RevisionPreview(BaseModel):
    valid: bool
    errors: list[BatchError]
    latest_revision_id: str
    parent_is_latest: bool
    content_sha256: str | None
    added_bundle_ids: list[str]
    removed_bundle_ids: list[str]
    changed_bundle_ids: list[str]
    change_summaries: list[ChangeSummary]
    group_count: int | None
    bundle_count: int | None
    total_mass_g: int | None


class RevisionRejected(BaseModel):
    """HTTP 400 detail for a draft that cannot be stored."""
    message: str
    errors: list[BatchError]


class ParentConflict(BaseModel):
    """HTTP 409 detail: the draft's parent is no longer the latest revision (nothing was written)."""
    message: str
    latest_revision_id: str


class SnapshotListItem(SavedSummary):
    cargo_revision_id: str | None
    recheck_status: RecheckStatus
    added_count: int
    removed_count: int
    changed_count: int
    placed_affected_count: int


class DroppedPlacement(BaseModel):
    unit_id: str
    reason: Literal['REMOVED', 'CHANGED']
    x_mm: int
    y_mm: int
    yaw_deg: int


class RebaseResult(BaseModel):
    source_revision_id: str
    target_revision_id: str
    candidate: Evaluation
    kept_placement_count: int
    dropped_placements: list[DroppedPlacement]
    added_unit_ids: list[str]
    removed_unit_ids: list[str]
    changed_unit_ids: list[str]
    comparison: CompareResult
