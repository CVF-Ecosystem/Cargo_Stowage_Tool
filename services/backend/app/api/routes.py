from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel
from typing import Literal

from ..vessel import PROFILE, CASES, DATA

from ..demo import demo_plan
from ..domain.model import Evaluation, Plan
from ..domain.rules import evaluate
from ..adapters import plan_binding
from ..adapters.plan_binding import PlanBindingError
from ..adapters import vessel_profile_service as profiles
from ..adapters.vessel_profile_store import ProfileUnavailable
from .vessel_profile_models import (ProfileDetail, ProfileListItem, ProfilePreview, ProfileVersionConflict,
                                    VesselProfileUpload)

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
    return profiles.case_plan(PROFILE['id'], 1, case_id)


_UPLOAD_BODY = {"required": True, "content": {"application/json": {"schema": VesselProfileUpload.model_json_schema()}}}
_REJECTED_UPLOAD = {400: {"model": ProfilePreview, "description": "Hồ sơ hoặc GLB không hợp lệ hay kiểm landmark FAIL; chưa ghi gì."},
                    413: {"description": "Thân yêu cầu vượt 28 MiB."}}


def _profile_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProfileUnavailable):
        return HTTPException(400, {"message": str(exc)})
    if isinstance(exc, profiles.ServiceError):
        return HTTPException(exc.status, exc.detail)
    return HTTPException(404, str(exc))


async def _upload_body(request: Request) -> bytes:
    """Read the body for the upload endpoints, refusing more than 28 MiB before (and while) reading it."""
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > profiles.MAX_BODY_BYTES:
        raise HTTPException(413, {"message": "Thân yêu cầu quá lớn.", "errors": profiles.body_size_errors(int(declared))})
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > profiles.MAX_BODY_BYTES:
            raise HTTPException(413, {"message": "Thân yêu cầu quá lớn.", "errors": profiles.body_size_errors(size)})
        chunks.append(chunk)
    return b"".join(chunks)


@router.get("/vessel-profiles", response_model=list[ProfileListItem])
def list_vessel_profiles():
    return profiles.list_profiles()


@router.post("/vessel-profiles/preview", response_model=ProfilePreview, openapi_extra={"requestBody": _UPLOAD_BODY},
             responses=_REJECTED_UPLOAD)
async def preview_vessel_profile(request: Request):
    return profiles.preview(await _upload_body(request))


@router.post("/vessel-profiles", response_model=ProfileListItem, openapi_extra={"requestBody": _UPLOAD_BODY},
             responses={**_REJECTED_UPLOAD, 409: {"model": ProfileVersionConflict, "description": "Trùng built-in, sai version kế tiếp hoặc đầy kho; chưa ghi gì."}})
async def create_vessel_profile(request: Request):
    try:
        return profiles.create(await _upload_body(request))
    except profiles.ServiceError as exc:
        raise _profile_error(exc)


@router.get("/vessel-profiles/{profile_id}/{version}", response_model=ProfileDetail,
            responses={400: {"description": "Hồ sơ không qua kiểm toàn vẹn."}, 404: {"description": "Không tìm thấy hồ sơ tàu."}})
def vessel_profile_detail(profile_id: str, version: int):
    try:
        return profiles.detail(profile_id, version)
    except (LookupError, ProfileUnavailable) as exc:
        raise _profile_error(exc)


@router.get("/vessel-profiles/{profile_id}/{version}/model", response_class=Response,
            responses={200: {"content": {"model/gltf-binary": {}}}, 400: {"description": "Hồ sơ không qua kiểm toàn vẹn."},
                       404: {"description": "Không tìm thấy hồ sơ tàu."}})
def vessel_profile_model(profile_id: str, version: int):
    try:
        return Response(profiles.model_bytes(profile_id, version), media_type="model/gltf-binary")
    except (LookupError, ProfileUnavailable) as exc:
        raise _profile_error(exc)


@router.get("/vessel-profiles/{profile_id}/{version}/cases/{case_id}/plan", response_model=Evaluation,
            responses={400: {"description": "Hồ sơ không qua kiểm toàn vẹn."}, 404: {"description": "Không tìm thấy hồ sơ hoặc trường hợp tải."}})
def vessel_profile_case_plan(profile_id: str, version: int, case_id: str):
    try:
        return profiles.case_plan(profile_id, version, case_id)
    except (LookupError, ProfileUnavailable, PlanBindingError) as exc:
        raise _profile_error(exc)


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
def suggest_placement(plan: Plan, algorithm: Literal['guillotine-single-layer-v1','columns-v1']='guillotine-single-layer-v1'):
    return planner_preview(_bound(plan),algorithm)


from ..domain.comparison import CompareRequest, CompareResult, compare

@router.post("/plans/compare", response_model=CompareResult)
def compare_plans(payload: CompareRequest):
    return compare(_bound(payload.before),_bound(payload.after))


from ..adapters import revision_store
from ..domain import cargo_revisions as cargo
from ..domain import packing as cargo_packing
from .cargo_models import (ParentConflict, RebaseResult, RevisionDetail, RevisionDraft, RevisionList, RevisionPacking,
                           RevisionPreview, RevisionRejected, RevisionSummary)

_REJECTED = {400: {"model": RevisionRejected, "description": "Lô cập nhật không hợp lệ hoặc revision không qua kiểm toàn vẹn."}}


def _plain_error(exc) -> HTTPException:
    return HTTPException(400, {"message": str(exc), "errors": []})


async def _check_size(request: Request):
    size = len(await request.body())
    if size > cargo.MAX_PAYLOAD_BYTES:
        raise HTTPException(400, {"message": "Dữ liệu gửi lên quá lớn.", "errors": cargo.check_payload_size(size)})


async def _cargo_body(request: Request) -> bytes:
    """H4 / O5: read the cargo body, refusing more than MAX_PAYLOAD_BYTES before FastAPI parses it (same shape as _upload_body)."""
    limit = cargo.MAX_PAYLOAD_BYTES
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > limit:
        raise HTTPException(400, {"message": "Dữ liệu gửi lên quá lớn.", "errors": cargo.check_payload_size(int(declared))})
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise HTTPException(400, {"message": "Dữ liệu gửi lên quá lớn.", "errors": cargo.check_payload_size(size)})
        chunks.append(chunk)
    return b"".join(chunks)


class _BoundedBodyRoute(APIRoute):
    """Stores the bounded body on the request so FastAPI's own request.body() read reuses it instead of parsing unbounded input."""
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def bounded(request: Request):
            request._body = await _cargo_body(request)
            return await handler(request)
        return bounded


@router.get("/cargo-revisions", response_model=RevisionList, responses={400: {"model": RevisionRejected}})
def list_cargo_revisions():
    try:
        return plan_binding.list_revisions()
    except PlanBindingError as exc:
        raise _plain_error(exc)


async def preview_cargo_revision(draft: RevisionDraft, request: Request):
    await _check_size(request)
    try:
        return plan_binding.preview_draft(draft.parent_revision_id, draft.source, draft.changes)
    except PlanBindingError as exc:
        raise _plain_error(exc)


router.add_api_route("/cargo-revisions/preview", preview_cargo_revision, methods=["POST"], response_model=RevisionPreview,
                     responses=_REJECTED, route_class_override=_BoundedBodyRoute)


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


router.add_api_route("/cargo-revisions", create_cargo_revision, methods=["POST"], response_model=RevisionSummary,
                     responses={**_REJECTED, 409: {"model": ParentConflict, "description": "Revision cha không còn là mới nhất; chưa ghi gì."}},
                     route_class_override=_BoundedBodyRoute)


@router.get("/cargo-revisions/{revision_id}", response_model=RevisionDetail,
            responses={**_REJECTED, 404: {"description": "Không tìm thấy revision."}})
def get_cargo_revision(revision_id: str):
    try:
        return plan_binding.detail(plan_binding.view(revision_id))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PlanBindingError as exc:
        raise _plain_error(exc)


@router.get("/cargo-revisions/{revision_id}/packing", response_model=RevisionPacking,
            responses={**_REJECTED, 404: {"description": "Không tìm thấy revision."}})
def get_cargo_revision_packing(revision_id: str):
    """SUP-03 D3: derived (not measured) packing of every group of one revision; read-only, never stored."""
    try:
        return cargo_packing.pack_revision(plan_binding.view(revision_id))
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


import re
import unicodedata
from urllib.parse import quote
from ..adapters import report_service
from ..domain.report import ReportReconciliationError, xlsx as report_xlsx
from .report_models import PlanReport

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_REPORT_ERRORS = {400: {"description": "ID, dữ liệu, phiên bản hoặc revision ghim/profile tàu không qua kiểm toàn vẹn."},
                  404: {"description": "Không tìm thấy phương án đã lưu."},
                  500: {"description": "Báo cáo không khớp đối soát nội bộ; không xuất báo cáo."}}


def _report(snapshot_id: str) -> dict:
    """Read-only report model of a saved snapshot, with the same refusals as the other snapshot entry points."""
    try:
        return report_service.snapshot_report(snapshot_id)
    except ReportReconciliationError as exc:
        raise HTTPException(500, f"Báo cáo không khớp đối soát nội bộ: {exc.what}; không xuất báo cáo.")
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except (PlanBindingError, report_service.SnapshotError) as exc:
        raise HTTPException(400, str(exc))
    except (sqlite3.Error, OSError, ValueError, TypeError, OverflowError):
        raise HTTPException(400, "Không thể tạo báo cáo; ID, dữ liệu hoặc phiên bản không hợp lệ.")


def _slug(name: str) -> str:
    text = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-")[:60].strip("-") or "phuong-an"


def _download_names(name: str, snapshot_id: str) -> tuple[str, str]:
    return f"SCST-bao-cao-{_slug(name)}-{snapshot_id[:8]}.xlsx", f"SCST báo cáo {name} {snapshot_id[:8]}.xlsx"


@router.get("/snapshots/{snapshot_id}/report", response_model=PlanReport, responses=_REPORT_ERRORS)
def snapshot_report(snapshot_id: str):
    return _report(snapshot_id)


@router.get("/snapshots/{snapshot_id}/report.xlsx", response_class=Response, responses={**_REPORT_ERRORS, 200: {"content": {XLSX_MIME: {}}}})
def snapshot_report_xlsx(snapshot_id: str):
    report = _report(snapshot_id)
    ascii_name, real_name = _download_names(report["header"]["plan_name"], snapshot_id)
    return Response(report_xlsx.write_xlsx(report), media_type=XLSX_MIME,
                    headers={"Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(real_name, safe='')}"})


# ------------------------------------------------------------------ M5a local backup and restore
from ..adapters import backup_check, backup_export
from .backup_models import BackupPreview, BackupRejectedDetail, RestoreResult
from starlette.concurrency import run_in_threadpool

_BACKUP_BODY = {"required": True, "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}}
_BACKUP_REJECTED = {400: {"model": BackupRejectedDetail, "description": "Tệp sao lưu không hợp lệ; dữ liệu hiện tại giữ nguyên."},
                    413: {"model": BackupRejectedDetail, "description": "Tệp sao lưu vượt 256 MiB; chưa đọc hết, chưa ghi gì."}}


def _backup_too_large(size: int) -> HTTPException:
    limit = backup_check.MAX_BODY_BYTES
    return HTTPException(413, {"message": "Tệp sao lưu quá lớn.",
                               "errors": [{"field": "body", "message": f"Tệp dài {size} byte, vượt giới hạn 256 MiB ({limit} byte)."}]})


async def _backup_body(request: Request) -> bytes:
    """Read a .scstbak body, refusing more than backup_check.MAX_BODY_BYTES before (and while) reading it."""
    limit = backup_check.MAX_BODY_BYTES
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > limit:
        raise _backup_too_large(int(declared))
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise _backup_too_large(size)
        chunks.append(chunk)
    return b"".join(chunks)


def _backup_rejected(exc: "backup_check.BackupRejected") -> HTTPException:
    return HTTPException(400, {"message": exc.message, "errors": exc.errors})


@router.get("/backup/export", response_class=Response,
            responses={200: {"content": {"application/octet-stream": {}}, "description": "Tệp sao lưu scst.backup.v1 (.scstbak)."},
                       400: {"model": BackupRejectedDetail, "description": "Không đọc được dữ liệu local để sao lưu."}})
def export_backup():
    try:
        data, filename = backup_export.export_bytes()
    except (sqlite3.Error, OSError, ValueError):  # D1.2: never echo the exception, it may carry a filesystem path
        raise HTTPException(400, {"message": "Không tạo được bản sao lưu từ dữ liệu local.", "errors": []})
    return Response(data, media_type="application/octet-stream",
                    headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})


@router.post("/backup/restore/preview", response_model=BackupPreview, openapi_extra={"requestBody": _BACKUP_BODY},
             responses=_BACKUP_REJECTED)
async def preview_backup_restore(request: Request):
    body = await _backup_body(request)
    try:
        return await run_in_threadpool(backup_check.preview, body)
    except backup_check.BackupRejected as exc:
        raise _backup_rejected(exc)


@router.post("/backup/restore/apply", response_model=RestoreResult, openapi_extra={"requestBody": _BACKUP_BODY},
             responses={**_BACKUP_REJECTED, 409: {"model": BackupRejectedDetail, "description": "Mã xác nhận không khớp tệp gửi lên; chưa ghi gì."}})
async def apply_backup_restore(request: Request, confirm: str):
    from ..adapters import backup_restore
    body = await _backup_body(request)
    try:
        return await run_in_threadpool(backup_restore.apply, body, confirm)
    except backup_restore.ConfirmMismatch as exc:
        raise HTTPException(409, {"message": exc.message, "errors": exc.errors})
    except backup_check.BackupRejected as exc:
        raise _backup_rejected(exc)
