"""Request/response models of the vessel-profile API (SUP-02B D5). Profile content itself stays a plain object."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class VesselProfileUpload(BaseModel):
    """Body of POST /api/vessel-profiles[/preview]: the profile object and the GLB as strict base64."""
    profile: dict[str, Any]
    glb_base64: str


class ProfileError(BaseModel):
    field: str
    message: str


class LandmarkCheck(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    glb_m: list[float]
    expected_hold_mm: list[int]
    actual_hold_mm: list[float]
    error_mm: list[float]
    passed: bool = Field(alias="pass")


class BoundsCheck(BaseModel):
    glb_min_m: list[float]
    glb_max_m: list[float]
    scene_min_m: list[float]
    scene_max_m: list[float]
    hold_min_m: list[float]
    hold_max_m: list[float]
    contains_hold: bool


class Verification(BaseModel):
    result: Literal["PASS", "FAIL"]
    tolerance_mm: int
    landmarks: list[LandmarkCheck]
    bounds: BoundsCheck


class DraftMarker(BaseModel):
    case_id: str
    center_m: list[float]


class ViewerBlock(BaseModel):
    translation_m: list[float]
    yaw_deg: int
    hull_box_m: list[float]
    draft_markers: list[DraftMarker]
    hull_mesh_names: list[str]


class ProfileFieldStatus(BaseModel):
    dimensions_m: str
    hold: str
    cases: str


class ProfileSourceDocument(BaseModel):
    title: str
    sha256: str | None = None


class ProfileListItem(BaseModel):
    id: str
    version: int
    name: str
    registration: str | None
    builtin: bool
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    integrity_error: str | None
    verification: Literal["PASS", "FAIL"] | None
    field_status: ProfileFieldStatus | None
    source_documents: list[ProfileSourceDocument]
    profile_sha256: str | None
    created_utc: str | None


class ProfileDetail(BaseModel):
    id: str
    version: int
    builtin: bool
    status: Literal["AVAILABLE"]
    profile: dict[str, Any]
    profile_sha256: str
    glb_sha256: str
    asset_url: str
    verification: Verification
    viewer: ViewerBlock
    created_utc: str | None


class ProfilePreview(BaseModel):
    valid: bool
    errors: list[ProfileError]
    verification: Verification | None
    profile_sha256: str | None
    glb_sha256: str | None
    glb_bytes: int | None
    id: str | None
    version: int | None
    latest_version: int | None
    version_ok: bool
    builtin_conflict: bool


class ProfileVersionConflict(BaseModel):
    message: str
    latest_version: int | None = None
