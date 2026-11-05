"""Response models of scst.plan-report.v1 (M2d D1/D2); they only document and validate what domain.report builds."""
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, model_serializer

Status = Literal["ESTIMATED", "SOURCED", "MEASURED"]
Dims = tuple[int, int, int]


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Optional(_M):
    """M3a: fields in _OMIT are present only for multi-layer (COLUMNS_V1) reports; omitted when None so legacy JSON is byte-identical."""
    _OMIT: ClassVar[tuple] = ()

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler):
        data = handler(self)
        if isinstance(data, dict):
            for key in self._OMIT:
                if data.get(key) is None:
                    data.pop(key, None)
        return data


class ReportHeader(_M):
    plan_name: str
    snapshot_id: str
    saved_utc: str
    schema_version: Literal["scst.saved-plan.v1"]
    contract_version: str
    plan_sha256: str
    generated_utc: str


class ReportFieldStatus(_M):
    dimensions_m: Status
    hold: Status
    cases: Status


class ReportVessel(_M):
    vessel_id: str
    name: str
    case_id: str
    builtin: bool
    profile_version: int | None
    profile_sha256: str | None
    field_status: ReportFieldStatus


class ReportHold(_M):
    id: str
    name: str
    length_mm: int
    width_mm: int
    height_mm: int
    status: Literal["ESTIMATED", "SOURCED", "MEASURED", "UNCONFIRMED"]


class ReportLimits(_M):
    certificate_cargo_limit_g: int
    voyage_cargo_limit_g: int
    cargo_onboard_g: int
    available_capacity_g: int


class ReportRecheck(_M):
    status: Literal["CURRENT", "NEEDS_RECHECK", "NOT_APPLICABLE", "REVISION_UNAVAILABLE"]
    latest_revision_id: str | None
    added: int
    removed: int
    changed: int
    placed_affected: int


class ReportCargo(_M):
    plan_source: str
    cargo_source: str | None
    dataset_id: str | None
    revision_id: str | None
    content_sha256: str | None
    recheck: ReportRecheck


class ReportTotals(_Optional):
    _OMIT: ClassVar[tuple] = ("layer_count", "column_count")
    unit_count: int
    placed_count: int
    unplaced_count: int
    excluded_count: int
    manifest_mass_g: int
    placed_mass_g: int
    remaining_capacity_g: int
    manifest_envelope_volume_mm3: int | None
    placed_envelope_volume_mm3: int | None
    manifest_envelope_volume_mm3_text: str
    placed_envelope_volume_mm3_text: str
    layer_count: int | None = None
    column_count: int | None = None


class ReportPlacement(_Optional):
    _OMIT: ClassVar[tuple] = ("supported_by",)
    x_mm: int
    y_mm: int
    z_mm: int
    layer: int
    yaw_deg: int
    supported_by: list[str] | None = None


class ReportPacking(_M):
    status: Literal["DETAILED", "ENVELOPE_ONLY"]
    layout: Literal["RECT", "HEX"] | None
    columns: int
    rows: int
    pieces_placed: int
    pieces_source: int
    reason_codes: list[str]


class ReportUnit(_M):
    id: str
    name: str
    kind: Literal["BAR_BUNDLE", "PIPE_BUNDLE"]
    requirement: Literal["required", "optional", "excluded"]
    group_id: str | None
    source_row: int | None
    revision_id: str | None
    confirmation: str | None
    dimension_warning: bool
    length_mm: int
    width_mm: int
    height_mm: int
    dimensions_um: Dims
    mass_g: int
    status: Literal["PLACED", "UNPLACED", "EXCLUDED"]
    placement: ReportPlacement | None
    packing: ReportPacking | None


class ReportUnplaced(_M):
    id: str
    name: str
    status: Literal["UNPLACED", "EXCLUDED"]
    requirement: Literal["required", "optional", "excluded"]
    mass_g: int
    dimensions_um: Dims
    reason_code: Literal["EXCLUDED", "REQUIRED_UNPLACED", "OPTIONAL_UNPLACED"]
    reason: str


class ReportIssue(_M):
    code: str
    unit_ids: list[str]
    message: str


class ReportIssues(_M):
    status: str
    basic_checks_passed: bool
    total_issues: int
    issues_truncated: bool
    items: list[ReportIssue]
    unchecked: list[str]
    operational_eligible: Literal[False]


class ReportNotice(_M):
    code: str
    message: str


class PlanReport(_Optional):
    _OMIT: ClassVar[tuple] = ("stacking",)
    schema_version: Literal["scst.plan-report.v1"]
    report_sha256: str
    header: ReportHeader
    vessel: ReportVessel | None
    hold: ReportHold
    limits: ReportLimits
    cargo: ReportCargo
    totals: ReportTotals
    units: list[ReportUnit]
    unplaced: list[ReportUnplaced]
    issues: ReportIssues
    notices: list[ReportNotice]
    stacking: Literal["COLUMNS_V1"] | None = None
