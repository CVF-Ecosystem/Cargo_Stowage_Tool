from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Literal

from ..vessel import PROFILE, CASES, DATA

from ..demo import demo_plan
from ..domain.model import Evaluation, Plan
from ..domain.rules import evaluate

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0", "mode": "synthetic-demo", "ai": "off"}


@router.get("/demo", response_model=Evaluation)
def demo() -> Evaluation:
    return evaluate(demo_plan())


@router.post("/validate", response_model=Evaluation)
def validate(plan: Plan) -> Evaluation:
    return evaluate(plan)


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
