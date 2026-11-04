from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Literal

from ..vessel import PROFILE, CASES, DATA

from ..demo import demo_plan
from ..domain.model import Evaluation, Plan
from ..domain.rules import evaluate
from ..adapters import plan_binding
from ..adapters.plan_binding import PlanBindingError

router = APIRouter(prefix="/api")


def _bound(plan: Plan, status: int = 422) -> Plan:
    """Shared revision-binding gate for every entry point that receives a Plan (D5)."""
    try:
        return plan_binding.bind(plan)
    except PlanBindingError as exc:
        raise HTTPException(status, str(exc))


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0", "mode": "synthetic-demo", "ai": "off"}


@router.get("/demo", response_model=Evaluation)
def demo() -> Evaluation:
    return evaluate(demo_plan())


@router.post("/validate", response_model=Evaluation)
def validate(plan: Plan) -> Evaluation:
    return evaluate(_bound(plan))


class Dimensions(BaseModel):
    length: float
    beam: float
    depth: float


class ReferenceHold(BaseModel):
    id: str
    name: str
    length_mm: int
    width_mm: int
    height_mm: int
    source_width_m: float
    floor_z_m: float
    status: Literal["ESTIMATED"]


class OperatingCase(BaseModel):
    id: Literal["VR-SI", "VR-SII"]
    cargo_mass_g: int
    deadweight_t: float
    draft_m: float
    freeboard_mm: int


class Provenance(BaseModel):
    source_pdf_sha256: str
    source_json_sha256: str
    source_glb_sha256: str
    source_pages: list[int]
    freeboard_note: str


class ReferenceGeometry(BaseModel):
    source_hold_x_min_m: float
    source_hold_x_max_m: float
    source_hold_y_min_m: float
    source_hold_y_max_m: float
    source_floor_z_m: float
    glb_to_hold_translation_m: list[float]
    width_inset_each_side_mm: float
    axis_note: str


class VesselProfile(BaseModel):
    id: Literal["VINAFCO268"]
    name: str
    registration: str
    dimensions_m: Dimensions
    hold: ReferenceHold
    lightship_mass_t: float | None
    tanktop_load_limit_t_per_m2: float | None
    cases: list[OperatingCase]
    capacity_note: str
    container_note: str
    estimate_note: str
    asset_url: str
    provenance: Provenance
    geometry: ReferenceGeometry


@router.get("/vessels/vinafco268", response_model=VesselProfile)
def vessel_profile():
    return PROFILE


@router.get("/vessels/vinafco268/model", response_class=FileResponse)
def vessel_model():
    return FileResponse(DATA / 'model.glb', media_type='model/gltf-binary')


@router.get("/vessels/vinafco268/cases/{case_id}/plan", response_model=Evaluation)
def vessel_plan(case_id: str):
    if case_id not in CASES:
        raise HTTPException(404, "Unknown operating case")
    payload = demo_plan().model_dump()
    hold = PROFILE['hold']
    payload.update(source='MIXED_REFERENCE', vessel={'vessel_id': PROFILE['id'], 'case_id': case_id},
                   hold={k: hold[k] for k in ('id', 'name', 'length_mm', 'width_mm', 'height_mm')})
    payload['limits']['certificate_cargo_limit_g'] = CASES[case_id]['cargo_mass_g']
    payload['limits']['voyage_cargo_limit_g'] = CASES[case_id]['cargo_mass_g']
    return evaluate(Plan.model_validate(payload))


from ..adapters.csv_import import CsvRequest, CsvPreview, preview
from ..adapters.storage import SaveRequest, SavedSummary, save, fetch_plan, listing_rows
from .cargo_models import SnapshotListItem
import sqlite3


@router.post("/import/csv/preview", response_model=CsvPreview)
def csv_preview(payload: CsvRequest):
    _bound(payload.plan)
    return preview(payload)


@router.post("/snapshots", response_model=SavedSummary)
def save_snapshot(payload: SaveRequest):
    _bound(payload.plan, 400)
    try:
        return save(payload)
    except (sqlite3.Error, OSError, ValueError, TypeError, OverflowError):
        raise HTTPException(400, "Không thể lưu phương án local; kiểm tra tên và dữ liệu lưu trữ.")


@router.get("/snapshots", response_model=list[SnapshotListItem])
def list_snapshots():
    try:
        return plan_binding.annotate_listing(listing_rows())
    except (sqlite3.Error, OSError, ValueError, TypeError, OverflowError):
        raise HTTPException(400, "Không thể đọc danh sách phương án local.")


@router.get("/snapshots/{snapshot_id}", response_model=Evaluation)
def get_snapshot(snapshot_id: str):
    try:
        return evaluate(_bound(fetch_plan(snapshot_id), 400))
    except (sqlite3.Error, OSError, ValueError, LookupError, TypeError, OverflowError):
        raise HTTPException(400, "Không thể mở phương án; ID, dữ liệu hoặc phiên bản không hợp lệ.")


from ..adapters.pipe_registry import REGISTRY as PIPE_REGISTRY, DATASET as PIPE_DATASET, units as pipe_units

class PipeGroup(BaseModel):
    group_id: str
    source_row: int
    bundle_count: int
    pieces_per_bundle: int
    dimensions_um: tuple[int,int,int]
    mass_g: int
    source_line_t: str
    source_cbm_m3: str
    envelope_cbm_m3: str
    dimension_warning: bool
    issue_codes: list[str]
    outside_diameter_mm: str
    wall_thickness_mm: str

class PipeLibrary(BaseModel):
    dataset_id: str
    workbook_sha256: str
    sheet: str
    assigned_vessel: None
    mass_basis: str
    groups: list[PipeGroup]
    source_mass_t: str
    calculated_mass_t: str
    source_cbm_m3: str
    envelope_cbm_m3: str

@router.get("/pipe-list", response_model=PipeLibrary)
def pipe_list():
    return PIPE_REGISTRY

@router.post("/pipe-list/preview", response_model=Evaluation)
def pipe_list_preview(plan: Plan):
    candidate=_bound(plan).model_dump(mode="json")
    candidate.pop("cargo_revision",None)
    candidate.update(contract_version="scst.pipe-list.v1",cargo_dataset=PIPE_DATASET,cargo_source="DOCUMENT_CALCULATED",units=pipe_units(),placements=[])
    return evaluate(Plan.model_validate(candidate))


from ..domain.planner import PlannerPreview, preview as planner_preview

@router.post("/planner/preview", response_model=PlannerPreview)
def suggest_placement(plan: Plan):
    return planner_preview(_bound(plan))


from ..domain.comparison import CompareRequest, CompareResult, compare

@router.post("/plans/compare", response_model=CompareResult)
def compare_plans(payload: CompareRequest):
    return compare(_bound(payload.before),_bound(payload.after))


from ..adapters import revision_store
from ..domain import cargo_revisions as cargo
from .cargo_models import (ParentConflict, RebaseResult, RevisionDetail, RevisionDraft, RevisionList, RevisionPreview,
                           RevisionRejected, RevisionSummary)

_REJECTED = {400: {"model": RevisionRejected, "description": "Lô cập nhật không hợp lệ hoặc revision không qua kiểm toàn vẹn."}}


def _plain_error(exc) -> HTTPException:
    return HTTPException(400, {"message": str(exc), "errors": []})


async def _check_size(request: Request):
    size = len(await request.body())
    if size > cargo.MAX_PAYLOAD_BYTES:
        raise HTTPException(400, {"message": "Dữ liệu gửi lên quá lớn.", "errors": cargo.check_payload_size(size)})


@router.get("/cargo-revisions", response_model=RevisionList, responses={400: {"model": RevisionRejected}})
def list_cargo_revisions():
    try:
        return plan_binding.list_revisions()
    except PlanBindingError as exc:
        raise _plain_error(exc)


@router.post("/cargo-revisions/preview", response_model=RevisionPreview, responses=_REJECTED)
async def preview_cargo_revision(draft: RevisionDraft, request: Request):
    await _check_size(request)
    try:
        return plan_binding.preview_draft(draft.parent_revision_id, draft.source, draft.changes)
    except PlanBindingError as exc:
        raise _plain_error(exc)


@router.post("/cargo-revisions", response_model=RevisionSummary,
             responses={**_REJECTED, 409: {"model": ParentConflict, "description": "Revision cha không còn là mới nhất; chưa ghi gì."}})
async def create_cargo_revision(draft: RevisionDraft, request: Request):
    await _check_size(request)
    try:
        return plan_binding.create_revision(draft.parent_revision_id, draft.source, draft.changes)
    except revision_store.ParentMismatch as exc:
        raise HTTPException(409, {"message": "Revision cha không còn là mới nhất; hãy tải lại và tạo lô cập nhật mới.",
                                  "latest_revision_id": exc.latest})
    except cargo.BatchValidationError as exc:
        raise HTTPException(400, {"message": "Lô cập nhật không hợp lệ; chưa ghi gì.", "errors": exc.errors})
    except PlanBindingError as exc:
        raise _plain_error(exc)


@router.get("/cargo-revisions/{revision_id}", response_model=RevisionDetail,
            responses={**_REJECTED, 404: {"description": "Không tìm thấy revision."}})
def get_cargo_revision(revision_id: str):
    try:
        return plan_binding.detail(plan_binding.view(revision_id))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PlanBindingError as exc:
        raise _plain_error(exc)


@router.post("/cargo-revisions/{revision_id}/plan-preview", response_model=Evaluation,
             responses={**_REJECTED, 404: {"description": "Không tìm thấy revision."}, 422: {"description": "Plan không hợp lệ."}})
def cargo_revision_plan_preview(revision_id: str, plan: Plan):
    _bound(plan)
    try:
        return evaluate(plan_binding.revision_plan_preview(plan, revision_id))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PlanBindingError as exc:
        raise _plain_error(exc)


@router.post("/snapshots/{snapshot_id}/rebase", response_model=RebaseResult,
             responses={400: {"description": "Phương án không dùng list ống, dữ liệu lỗi hoặc revision không phục vụ được."},
                        404: {"description": "Không tìm thấy phương án."}})
def rebase_snapshot(snapshot_id: str):
    try:
        plan = _bound(fetch_plan(snapshot_id), 400)
        return plan_binding.rebase(plan, plan_binding.latest())
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except (PlanBindingError, sqlite3.Error, OSError, ValueError, TypeError, OverflowError) as exc:
        raise HTTPException(400, str(exc) if isinstance(exc, PlanBindingError)
                            else "Không thể tạo bản theo dữ liệu mới; ID, dữ liệu hoặc phiên bản không hợp lệ.")
