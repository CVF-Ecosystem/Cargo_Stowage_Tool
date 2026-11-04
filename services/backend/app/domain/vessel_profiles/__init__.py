"""scst.vessel-profile.v1: pydantic contract, Vietnamese field errors, canonical hash, pure frame transform, verification."""
import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError, field_validator

CONTRACT = "scst.vessel-profile.v1"
MAX_PROFILE_BYTES = 256 * 1024
TOLERANCE_MM = 1
STATUS = Literal["ESTIMATED", "SOURCED", "MEASURED"]

Metres = Annotated[float, Field(strict=True, gt=0, le=500, allow_inf_nan=False)]
Millimetres = Annotated[StrictInt, Field(gt=0, le=500_000)]
Coordinate = Annotated[float, Field(strict=True, ge=-1000, le=1000, allow_inf_nan=False)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Dimensions(_Model):
    length: Metres
    beam: Metres
    depth: Metres


class Hold(_Model):
    id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{0,31}$")
    name: str = Field(min_length=1, max_length=100)
    length_mm: Millimetres
    width_mm: Millimetres
    height_mm: Millimetres
    status: STATUS


class Case(_Model):
    id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9-]{0,31}$")
    cargo_mass_g: Annotated[StrictInt, Field(gt=0, le=1_000_000_000_000)]
    draft_m: Annotated[float, Field(strict=True, gt=0, le=500, allow_inf_nan=False)]
    deadweight_t: Annotated[StrictInt, Field(gt=0, le=10_000_000)] | None = None
    freeboard_mm: Annotated[StrictInt, Field(ge=0, le=500_000)] | None = None


class SourceDocument(_Model):
    title: str = Field(min_length=1, max_length=300)
    sha256: Sha256 | None = None


class FieldStatus(_Model):
    dimensions_m: STATUS
    hold: STATUS
    cases: STATUS


class Provenance(_Model):
    source_documents: list[SourceDocument] = Field(min_length=1, max_length=10)
    field_status: FieldStatus


class Transform(_Model):
    translation_m: Annotated[list[Coordinate], Field(min_length=3, max_length=3)]
    yaw_deg: Literal[0, 90, 180, 270]


class Landmark(_Model):
    name: str = Field(min_length=1, max_length=100)
    glb_m: Annotated[list[Coordinate], Field(min_length=3, max_length=3)]
    hold_mm: Annotated[list[Annotated[StrictInt, Field(ge=-1_000_000, le=1_000_000)]], Field(min_length=3, max_length=3)]


class VesselProfileV1(_Model):
    contract_version: Literal["scst.vessel-profile.v1"]
    id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9-]{1,31}$")
    version: Annotated[StrictInt, Field(ge=1)]
    name: str = Field(min_length=1, max_length=100)
    registration: str = Field(max_length=50)
    dimensions_m: Dimensions
    hold: Hold
    cases: list[Case] = Field(min_length=1, max_length=20)
    notes: list[Annotated[str, Field(max_length=500)]] = Field(max_length=10)
    provenance: Provenance
    transform: Transform
    landmarks: list[Landmark] = Field(min_length=3, max_length=20)
    hull_mesh_names: list[Annotated[str, Field(min_length=1, max_length=100)]] | None = Field(default=None, max_length=50)

    @field_validator("cases")
    @classmethod
    def _unique_case_ids(cls, cases):
        seen = set()
        for case in cases:
            if case.id in seen:
                raise ValueError(f"Mã trường hợp tải '{case.id}' bị trùng; mỗi trường hợp phải có mã riêng.")
            seen.add(case.id)
        return cases


# ---- validation with Vietnamese per-field errors ------------------------------------------------

def _field(loc) -> str:
    out = ""
    for part in loc:
        out += f"[{part}]" if isinstance(part, int) else (("." if out else "") + str(part))
    return out or "profile"


def _message(err: dict) -> str:
    kind, ctx = err["type"], err.get("ctx") or {}
    table = {
        "missing": "Thiếu trường bắt buộc.",
        "extra_forbidden": "Trường không được phép có trong hồ sơ.",
        "int_type": "Giá trị phải là số nguyên (không nhận số thập phân, chuỗi hay true/false).",
        "int_parsing": "Giá trị phải là số nguyên.",
        "int_from_float": "Giá trị phải là số nguyên, không phải số thập phân.",
        "float_type": "Giá trị phải là số thực hợp lệ (không nhận chuỗi hay true/false).",
        "float_parsing": "Giá trị phải là số thực.",
        "finite_number": "Giá trị phải là số hữu hạn (không nhận NaN hoặc vô cực).",
        "string_type": "Giá trị phải là chuỗi ký tự.",
        "list_type": "Giá trị phải là một danh sách.",
        "model_type": "Giá trị phải là một đối tượng JSON.",
        "dict_type": "Giá trị phải là một đối tượng JSON.",
        "greater_than": f"Giá trị phải lớn hơn {ctx.get('gt')}.",
        "greater_than_equal": f"Giá trị phải lớn hơn hoặc bằng {ctx.get('ge')}.",
        "less_than": f"Giá trị phải nhỏ hơn {ctx.get('lt')}.",
        "less_than_equal": f"Giá trị phải nhỏ hơn hoặc bằng {ctx.get('le')}.",
        "string_pattern_mismatch": f"Giá trị sai định dạng, cần khớp mẫu {ctx.get('pattern')}.",
        "string_too_short": f"Chuỗi quá ngắn, tối thiểu {ctx.get('min_length')} ký tự.",
        "string_too_long": f"Chuỗi quá dài, tối đa {ctx.get('max_length')} ký tự.",
        "too_short": f"Danh sách quá ít phần tử, tối thiểu {ctx.get('min_length')}.",
        "too_long": f"Danh sách quá nhiều phần tử, tối đa {ctx.get('max_length')}.",
        "literal_error": f"Giá trị không thuộc tập cho phép: {str(ctx.get('expected')).replace(' or ', ' hoặc ')}.",
    }
    if kind == "value_error" and "error" in ctx:
        return str(ctx["error"])
    return table.get(kind, "Giá trị không hợp lệ.")


def validate_profile(data: object) -> tuple[VesselProfileV1 | None, list[dict]]:
    try:
        return VesselProfileV1.model_validate(data), []
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            errors.append({"field": _field(err["loc"]), "message": _message(err)})
        return None, errors


def check_profile_size(n_bytes: int) -> list[dict]:
    if n_bytes > MAX_PROFILE_BYTES:
        return [{"field": "profile", "message": f"Hồ sơ dài {n_bytes} byte, vượt giới hạn 256 KiB ({MAX_PROFILE_BYTES} byte)."}]
    return []


def canonical_bytes(profile: VesselProfileV1) -> bytes:
    return json.dumps(profile.model_dump(mode="json"), sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def profile_sha256(profile: VesselProfileV1) -> str:
    return hashlib.sha256(canonical_bytes(profile)).hexdigest()


# ---- pure frame transform (GLB -> scene -> hold) -----------------------------------------------

_YAW = {  # THREE.js object.rotation.y convention, exact (no trig)
    0: lambda x, y, z: (x, y, z),
    90: lambda x, y, z: (z, y, -x),
    180: lambda x, y, z: (-x, y, -z),
    270: lambda x, y, z: (-z, y, x),
}
_YAW_INVERSE = {0: 0, 90: 270, 180: 180, 270: 90}


def rotate_yaw(v, yaw: int) -> tuple:
    if yaw not in _YAW:
        raise ValueError("yaw_deg phải thuộc {0, 90, 180, 270}.")
    return _YAW[yaw](*v)


def _tf(transform) -> tuple:
    if isinstance(transform, dict):
        return transform["translation_m"], transform["yaw_deg"]
    return transform.translation_m, transform.yaw_deg


def _dim(hold, key: str):
    return hold[key] if isinstance(hold, dict) else getattr(hold, key)


def glb_to_scene(point, transform) -> tuple:
    t, yaw = _tf(transform)
    r = rotate_yaw(point, yaw)
    return (r[0] + t[0], r[1] + t[1], r[2] + t[2])


def scene_to_glb(point, transform) -> tuple:
    t, yaw = _tf(transform)
    return rotate_yaw((point[0] - t[0], point[1] - t[1], point[2] - t[2]), _YAW_INVERSE[yaw])


def scene_to_hold_mm(point, hold) -> tuple:
    """Scene (m) -> hold frame (mm): x along length, y across width, z up."""
    length, width = _dim(hold, "length_mm"), _dim(hold, "width_mm")
    return ((point[0] + length / 2000) * 1000, (point[2] + width / 2000) * 1000, point[1] * 1000)


def hold_mm_to_scene(point, hold) -> tuple:
    length, width = _dim(hold, "length_mm"), _dim(hold, "width_mm")
    return (point[0] / 1000 - length / 2000, point[2] / 1000, point[1] / 1000 - width / 2000)


def transform_box(bmin, bmax, transform) -> tuple[list, list]:
    pts = [glb_to_scene([(bmax if (i >> (2 - k)) & 1 else bmin)[k] for k in range(3)], transform) for i in range(8)]
    return [min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]


# ---- verification and viewer ------------------------------------------------------------------

def _r(values, digits=6) -> list:
    return [round(float(v), digits) for v in values]


def verify(profile: VesselProfileV1, gltf_bounds) -> dict:
    tf, hold = profile.transform, profile.hold
    landmarks = []
    for lm in profile.landmarks:
        actual = scene_to_hold_mm(glb_to_scene(lm.glb_m, tf), hold)
        error = _r(abs(a - e) for a, e in zip(actual, lm.hold_mm))
        landmarks.append({"name": lm.name, "glb_m": _r(lm.glb_m, 9), "expected_hold_mm": list(lm.hold_mm),
                          "actual_hold_mm": _r(actual), "error_mm": error, "pass": max(error) <= TOLERANCE_MM})
    gmin, gmax = gltf_bounds
    smin, smax = transform_box(gmin, gmax, tf)
    hmin = [-hold.length_mm / 2000, 0.0, -hold.width_mm / 2000]
    hmax = [hold.length_mm / 2000, hold.height_mm / 1000, hold.width_mm / 2000]
    contains = all(smin[k] <= hmin[k] + 1e-6 and smax[k] >= hmax[k] - 1e-6 for k in range(3))
    ok = contains and all(lm["pass"] for lm in landmarks)
    return {"result": "PASS" if ok else "FAIL", "tolerance_mm": TOLERANCE_MM, "landmarks": landmarks,
            "bounds": {"glb_min_m": _r(gmin), "glb_max_m": _r(gmax), "scene_min_m": _r(smin), "scene_max_m": _r(smax),
                       "hold_min_m": _r(hmin), "hold_max_m": _r(hmax), "contains_hold": contains}}


def viewer_block(profile: VesselProfileV1) -> dict:
    tf, dims = profile.transform, profile.dimensions_m
    sx, sz = (dims.length, dims.beam) if tf.yaw_deg in (0, 180) else (dims.beam, dims.length)
    return {"translation_m": list(tf.translation_m), "yaw_deg": tf.yaw_deg, "hull_box_m": [sx, 0.01, sz],
            "draft_markers": [{"case_id": c.id, "center_m": _r(glb_to_scene((0, c.draft_m, 0), tf))}
                              for c in profile.cases],
            "hull_mesh_names": list(profile.hull_mesh_names or [])}
