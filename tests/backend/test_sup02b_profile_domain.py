"""SUP-02B domain layer: contract limits, canonical hash, frame transform, GLB bounds, verification. Offline."""
import copy
import hashlib
import json
import math
import re

import pytest

from app.domain.vessel_profiles import (MAX_PROFILE_BYTES, VesselProfileV1, canonical_bytes, check_profile_size,
                                        glb_to_scene, hold_mm_to_scene, profile_sha256, rotate_yaw, scene_to_glb,
                                        scene_to_hold_mm, transform_box, validate_profile, verify, viewer_block)
from app.domain.vessel_profiles.glb import MAX_GLB_BYTES, GlbError, glb_bounds, parse_glb
from app.vessel import CASES, DATA, PROFILE, builtin_vinafco_profile
import glb_fixture as fx

DIACRITICS = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.I)
FILES = [DATA / "profile.json", DATA / "model.glb"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def source_files_unchanged():
    before = [sha(p) for p in FILES]
    yield
    assert [sha(p) for p in FILES] == before


def good():
    return copy.deepcopy(builtin_vinafco_profile())


def errors_of(mutate):
    data = good()
    mutate(data)
    model, errors = validate_profile(data)
    assert model is None and errors
    assert all(DIACRITICS.search(e["message"]) for e in errors), errors
    return {e["field"]: e["message"] for e in errors}


def box_profile(**overrides):
    """Synthetic 10x4x3 m hold; GLB frame == scene frame shifted by translation."""
    data = good()
    data["hold"].update(length_mm=10000, width_mm=4000, height_mm=3000)
    data["transform"] = {"translation_m": [0.0, 0.0, 0.0], "yaw_deg": 0}
    data["landmarks"] = [{"name": n, "glb_m": g, "hold_mm": h} for n, g, h in [
        ("A", [-5.0, 0.0, -2.0], [0, 0, 0]), ("B", [5.0, 0.0, -2.0], [10000, 0, 0]),
        ("C", [5.0, 3.0, 2.0], [10000, 4000, 3000])]]
    data.update(overrides)
    model, errors = validate_profile(data)
    assert not errors, errors
    return model


HULL = fx.make_glb([((-6.0, -0.5, -3.0), (6.0, 4.0, 3.0))])


# ---- transform ---------------------------------------------------------------------------------

@pytest.mark.parametrize("yaw,expected", [(0, (1, 2, 3)), (90, (3, 2, -1)), (180, (-1, 2, -3)), (270, (-3, 2, 1))])
def test_rotate_matches_three_convention(yaw, expected):
    assert rotate_yaw((1, 2, 3), yaw) == expected
    a = math.radians(yaw)  # THREE rotation.y: x' = x cos + z sin ; z' = -x sin + z cos
    x, y, z = 1, 2, 3
    ref = (x * math.cos(a) + z * math.sin(a), y, -x * math.sin(a) + z * math.cos(a))
    assert all(abs(r - e) < 1e-12 for r, e in zip(ref, expected))


def test_rotate_rejects_other_yaw():
    with pytest.raises(ValueError):
        rotate_yaw((1, 2, 3), 45)


@pytest.mark.parametrize("yaw", [0, 90, 180, 270])
@pytest.mark.parametrize("t", [[0.0, 0.0, 0.0], [-0.9725, -0.832, 0.0], [12.5, 3.25, -7.75]])
def test_transform_round_trips(yaw, t):
    tf = {"translation_m": t, "yaw_deg": yaw}
    for p in [(0.0, 0.0, 0.0), (1.5, -2.0, 3.25), (-38.9, 5.2, 6.62)]:
        scene = glb_to_scene(p, tf)
        assert scene == tuple(a + b for a, b in zip(rotate_yaw(p, yaw), t))
        assert scene_to_glb(scene, tf) == pytest.approx(p, abs=1e-12)
    hold = {"length_mm": 56405, "width_mm": 10343}
    for p in [(0, 0, 0), (56405, 10343, 5408), (1234, 567, 89)]:
        assert scene_to_hold_mm(hold_mm_to_scene(p, hold), hold) == pytest.approx(p, abs=1e-9)
    # four quarter turns are the identity
    q = (1.0, 2.0, 3.0)
    for _ in range(4):
        q = rotate_yaw(q, 90)
    assert q == (1.0, 2.0, 3.0)


@pytest.mark.parametrize("yaw", [0, 90, 180, 270])
def test_transform_box_is_exact_aabb(yaw):
    tf = {"translation_m": [1.0, -2.0, 0.5], "yaw_deg": yaw}
    lo, hi = transform_box((-4, 0, -1), (6, 3, 2), tf)
    corners = [glb_to_scene((x, y, z), tf) for x in (-4, 6) for y in (0, 3) for z in (-1, 2)]
    assert lo == [min(c[k] for c in corners) for k in range(3)]
    assert hi == [max(c[k] for c in corners) for k in range(3)]
    if yaw in (90, 270):  # length and width swap
        assert hi[0] - lo[0] == 3 and hi[2] - lo[2] == 10


def test_scene_to_hold_mm_matches_scene_ts_convention():
    hold = {"length_mm": 56405, "width_mm": 10343}
    # cargo at hold (x,y,z) mm is drawn at scene (x/1000-L/2, z/1000, y/1000-W/2)
    assert scene_to_hold_mm((-28.2025, 1.0, -5.1715), hold) == pytest.approx((0, 0, 1000))
    assert scene_to_hold_mm((28.2025, 0.0, 5.1715), hold) == pytest.approx((56405, 10343, 0))


# ---- VINAFCO268 derivation ---------------------------------------------------------------------

def test_vinafco_derivation_is_verbatim_and_valid():
    data = builtin_vinafco_profile()
    model, errors = validate_profile(data)
    assert not errors and isinstance(model, VesselProfileV1)
    assert (data["id"], data["name"], data["registration"], data["version"]) == ("VINAFCO268", "VINAFCO 268", "HN-2642", 1)
    assert data["dimensions_m"] == PROFILE["dimensions_m"]
    assert {k: v for k, v in data["hold"].items() if k != "status"} == {
        k: PROFILE["hold"][k] for k in ("id", "name", "length_mm", "width_mm", "height_mm")}
    assert data["hold"]["status"] == "ESTIMATED"
    assert data["cases"] == [{k: c[k] for k in ("id", "cargo_mass_g", "draft_m", "deadweight_t", "freeboard_mm")}
                             for c in PROFILE["cases"]]
    assert {c["id"]: c["cargo_mass_g"] for c in data["cases"]} == {k: v["cargo_mass_g"] for k, v in CASES.items()}
    prov = PROFILE["provenance"]
    assert data["notes"] == [PROFILE["capacity_note"], PROFILE["container_note"], PROFILE["estimate_note"],
                             prov["freeboard_note"]]
    assert [d["sha256"] for d in data["provenance"]["source_documents"]] == [
        prov["source_pdf_sha256"], prov["source_json_sha256"], prov["source_glb_sha256"]]
    assert data["provenance"]["source_documents"][2]["sha256"] == sha(DATA / "model.glb")
    assert data["provenance"]["field_status"] == {"dimensions_m": "SOURCED", "hold": "ESTIMATED", "cases": "SOURCED"}
    assert data["transform"] == {"translation_m": [-0.9725, -0.832, 0.0], "yaw_deg": 0}
    assert data["hull_mesh_names"][0] == "Than_tau_duoi_duong_nuoc" and len(data["hull_mesh_names"]) == 5
    assert len(data["landmarks"]) == 4
    # derivation is deterministic and independent of earlier calls
    assert canonical_bytes(model) == canonical_bytes(validate_profile(builtin_vinafco_profile())[0])


def test_vinafco_verifies_against_real_glb():
    model, _ = validate_profile(builtin_vinafco_profile())
    bounds = glb_bounds(parse_glb((DATA / "model.glb").read_bytes()))
    assert bounds[0] == pytest.approx([-38.9, 0.0, -6.62], abs=1e-5)
    assert bounds[1] == pytest.approx([38.9, 9.4, 6.62], abs=1e-5)
    result = verify(model, bounds)
    assert result["result"] == "PASS" and result["tolerance_mm"] == 1
    assert result["bounds"]["contains_hold"] is True
    assert len(result["landmarks"]) == 4
    for lm in result["landmarks"]:
        assert lm["pass"] and max(lm["error_mm"]) <= 1
        assert lm["error_mm"] == pytest.approx([0.0, 0.375, 0.0], abs=1e-6)  # 0.375 mm width inset each side
        assert lm["actual_hold_mm"][0] == pytest.approx(lm["expected_hold_mm"][0], abs=1e-6)
        assert lm["actual_hold_mm"][2] == pytest.approx(0.0, abs=1e-6)
    assert result["landmarks"][0]["glb_m"] == [-27.23, 0.832, -5.171875]
    assert result["landmarks"][3]["glb_m"] == [29.175, 0.832, 5.171875]
    json.dumps(result)


def test_vinafco_viewer_block_matches_current_scene():
    model, _ = validate_profile(builtin_vinafco_profile())
    block = viewer_block(model)
    assert block["translation_m"] == [-0.9725, -0.832, 0.0] and block["yaw_deg"] == 0
    assert block["hull_box_m"] == [77.8, 0.01, 13.24]
    assert block["draft_markers"] == [{"case_id": "VR-SI", "center_m": [-0.9725, 3.768, 0.0]},
                                      {"case_id": "VR-SII", "center_m": [-0.9725, 4.018, 0.0]}]
    assert "Day_ngoai_than_tau" in block["hull_mesh_names"]


def test_viewer_block_swaps_hull_box_for_quarter_turns():
    for yaw, box in ((90, [13.24, 0.01, 77.8]), (180, [77.8, 0.01, 13.24]), (270, [13.24, 0.01, 77.8])):
        data = good()
        data["transform"]["yaw_deg"] = yaw
        assert viewer_block(validate_profile(data)[0])["hull_box_m"] == box


def test_canonical_bytes_and_hash():
    model, _ = validate_profile(builtin_vinafco_profile())
    raw = canonical_bytes(model)
    assert raw == json.dumps(json.loads(raw), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert "Hầm ước tính".encode("utf-8") in raw  # not ASCII-escaped
    assert profile_sha256(model) == hashlib.sha256(raw).hexdigest()
    reparsed, errors = validate_profile(json.loads(raw))  # a stored profile round-trips to the same hash
    assert not errors and profile_sha256(reparsed) == profile_sha256(model)
    shuffled = dict(reversed(list(builtin_vinafco_profile().items())))
    assert profile_sha256(validate_profile(shuffled)[0]) == profile_sha256(model)


# ---- synthetic GLB verification ----------------------------------------------------------------

def test_synthetic_pass():
    result = verify(box_profile(), glb_bounds(parse_glb(HULL)))
    assert result["result"] == "PASS"
    assert all(lm["error_mm"] == [0.0, 0.0, 0.0] for lm in result["landmarks"])
    assert result["bounds"]["hold_min_m"] == [-5.0, 0.0, -2.0] and result["bounds"]["hold_max_m"] == [5.0, 3.0, 2.0]


def test_landmark_off_by_two_mm_fails():
    data = box_profile().model_dump(mode="json")
    data["landmarks"][1]["glb_m"][0] += 0.002
    model, _ = validate_profile(data)
    result = verify(model, glb_bounds(parse_glb(HULL)))
    assert result["result"] == "FAIL"
    assert [lm["pass"] for lm in result["landmarks"]] == [True, False, True]
    assert result["landmarks"][1]["error_mm"][0] == pytest.approx(2.0, abs=1e-6)


def test_landmark_within_tolerance_passes():
    data = box_profile().model_dump(mode="json")
    data["landmarks"][1]["glb_m"][0] += 0.0009
    assert verify(validate_profile(data)[0], glb_bounds(parse_glb(HULL)))["result"] == "PASS"


@pytest.mark.parametrize("box", [((-4.9, -0.5, -3.0), (6.0, 4.0, 3.0)), ((-6.0, -0.5, -3.0), (6.0, 2.9, 3.0)),
                                 ((-6.0, -0.5, -1.9), (6.0, 4.0, 3.0))])
def test_hold_outside_glb_bounds_fails(box):
    result = verify(box_profile(), glb_bounds(parse_glb(fx.make_glb([box]))))
    assert result["bounds"]["contains_hold"] is False and result["result"] == "FAIL"
    assert all(lm["pass"] for lm in result["landmarks"])


def test_node_translation_and_rotation_affect_bounds():
    box = ((-1.0, 0.0, -2.0), (3.0, 1.0, 2.0))
    assert glb_bounds(parse_glb(fx.make_glb([box]))) == ([-1.0, 0.0, -2.0], [3.0, 1.0, 2.0])
    lo, hi = glb_bounds(parse_glb(fx.make_glb([box], node_translation=[10.0, 5.0, -1.0])))
    assert (lo, hi) == ([9.0, 5.0, -3.0], [13.0, 6.0, 1.0])
    s = math.sqrt(0.5)  # +90 deg about Y: (x, y, z) -> (z, y, -x)
    lo, hi = glb_bounds(parse_glb(fx.make_glb([box], node_rotation=[0, s, 0, s])))
    assert lo == pytest.approx([-2.0, 0.0, -3.0], abs=1e-9) and hi == pytest.approx([2.0, 1.0, 1.0], abs=1e-9)
    lo, hi = glb_bounds(parse_glb(fx.make_glb([box], node_scale=[2.0, 1.0, 1.0], node_translation=[1.0, 0, 0])))
    assert (lo, hi) == pytest.approx(([-1.0, 0.0, -2.0], [7.0, 1.0, 2.0]))
    matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 4, 0, 0, 1]  # column-major translate x by 4
    assert glb_bounds(parse_glb(fx.make_glb([box], node_matrix=matrix)))[0] == [3.0, 0.0, -2.0]


def test_multiple_primitives_union_and_node_tree():
    assert glb_bounds(parse_glb(fx.make_glb([((0, 0, 0), (1, 1, 1)), ((5, 5, 5), (6, 7, 8))]))) == ([0, 0, 0], [6, 7, 8])
    gltf = {"asset": {"version": "2.0"}, "scenes": [{"nodes": [0]}], "nodes": [
        {"translation": [10, 0, 0], "children": [1]}, {"translation": [0, 2, 0], "mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "accessors": [{"componentType": 5126, "type": "VEC3", "count": 8, "min": [0, 0, 0], "max": [1, 1, 1]}]}
    assert glb_bounds(gltf) == ([10, 2, 0], [11, 3, 1])
    del gltf["scenes"]  # no scenes: all root nodes
    assert glb_bounds(gltf) == ([10, 2, 0], [11, 3, 1])


@pytest.mark.parametrize("mutate", [
    lambda g: g["nodes"][0].update(children=[0]),                       # cycle
    lambda g: g["nodes"][0].update(children=[9]),                       # child out of range
    lambda g: g["nodes"][0].update(mesh=5),                             # mesh out of range
    lambda g: g.update(scene=3),                                        # scene out of range
    lambda g: g["accessors"][0].pop("min"),                             # missing min
    lambda g: g["accessors"][0].pop("max"),                             # missing max
    lambda g: g["accessors"][0].update(componentType=5123),             # not float32
    lambda g: g["meshes"][0]["primitives"][0]["attributes"].pop("POSITION"),
    lambda g: g.update(meshes=[]),
    lambda g: g["nodes"][0].update(matrix=[1] * 15),
])
def test_glb_bounds_errors(mutate):
    gltf = parse_glb(fx.make_glb([((0, 0, 0), (1, 1, 1))]))
    mutate(gltf)
    with pytest.raises(GlbError) as exc:
        glb_bounds(gltf)
    assert DIACRITICS.search(str(exc.value))


def test_missing_minmax_from_fixture():
    with pytest.raises(GlbError, match="min/max"):
        glb_bounds(parse_glb(fx.make_glb([((0, 0, 0), (1, 1, 1))], include_minmax=False)))
    with pytest.raises(GlbError, match="float32"):
        glb_bounds(parse_glb(fx.make_glb([((0, 0, 0), (1, 1, 1))], component_type=5123)))


def test_fixture_has_real_bin_chunk():
    glb = fx.make_glb([((0, 0, 0), (1, 2, 3))])
    json_len = int.from_bytes(glb[12:16], "little")
    assert int.from_bytes(glb[20 + json_len + 4:20 + json_len + 8], "little") == 0x004E4942
    assert len(glb) == int.from_bytes(glb[8:12], "little")
    assert parse_glb(glb)["buffers"][0]["byteLength"] == 8 * 12 + 36 * 2 + 0  # 96 + 72 bytes
    assert parse_glb(glb)["buffers"][0]["byteLength"] == 96 + 72


# ---- GLB format errors -------------------------------------------------------------------------

GOOD = fx.make_glb([((0, 0, 0), (1, 1, 1))])


@pytest.mark.parametrize("data", [
    b"", b"glTF\x02\x00", fx.bad_magic(GOOD), fx.bad_version(GOOD), fx.bad_version(GOOD, 3), fx.bad_total_length(GOOD),
    GOOD[:19], fx.non_json_first_chunk(GOOD), fx.bad_chunk_length(GOOD),
    fx.with_json_bytes(b"{not json"), fx.with_json_bytes(b"\xff\xfe\x00"), fx.with_json_bytes(b"[1, 2]"),
    fx.with_json_bytes(b"{}"), fx.with_json_bytes(b'{"asset": {"version": "1.0"}}'),
    fx.with_json_bytes(b'{"asset": {"version": 2}}'), fx.make_glb([((0, 0, 0), (1, 1, 1))], asset_version="1.0"),
])
def test_parse_glb_rejects_bad_files(data):
    with pytest.raises(GlbError) as exc:
        parse_glb(data)
    assert DIACRITICS.search(str(exc.value))


def test_parse_glb_size_limit_checked_first():
    assert MAX_GLB_BYTES == 20 * 1024 * 1024
    with pytest.raises(GlbError, match="20 MiB"):
        parse_glb(b"\0" * (MAX_GLB_BYTES + 1))  # would also fail the magic check, size is reported first
    padded = GOOD + b"\0" * (MAX_GLB_BYTES - len(GOOD))
    with pytest.raises(GlbError, match="không khớp"):  # at the limit: passes the size check, fails the length check
        parse_glb(padded)


def test_parse_glb_accepts_valid_file_and_real_model():
    assert parse_glb(GOOD)["asset"]["version"] == "2.0"
    assert parse_glb((DATA / "model.glb").read_bytes())["asset"]["version"] == "2.0"


# ---- D1 limits: every limit -> Vietnamese error on the right field ------------------------------

def test_good_profile_has_no_errors():
    assert validate_profile(good())[1] == []


@pytest.mark.parametrize("value", ["vinafco", "-AB", "A", "A" * 33, "AB_C", ""])
def test_id_pattern(value):
    assert "id" in errors_of(lambda d: d.update(id=value))


def test_id_boundaries_ok():
    for value in ("AB", "A" * 32, "0A-1"):
        data = good()
        data["id"] = value
        assert validate_profile(data)[1] == []


@pytest.mark.parametrize("value", [0, -1, 1.0, "1", True, None])
def test_version(value):
    assert "version" in errors_of(lambda d: d.update(version=value))


def test_name_and_registration_limits():
    assert "name" in errors_of(lambda d: d.update(name=""))
    assert "name" in errors_of(lambda d: d.update(name="x" * 101))
    assert "registration" in errors_of(lambda d: d.update(registration="x" * 51))
    data = good()
    data.update(name="x" * 100, registration="")
    assert validate_profile(data)[1] == []
    data["registration"] = "x" * 50
    assert validate_profile(data)[1] == []


@pytest.mark.parametrize("key", ["length", "beam", "depth"])
@pytest.mark.parametrize("value", [0, -1.0, 500.001, float("nan"), float("inf"), "5", True, None])
def test_dimensions(key, value):
    assert f"dimensions_m.{key}" in errors_of(lambda d: d["dimensions_m"].update({key: value}))


def test_dimension_boundary_and_integer_input_ok():
    data = good()
    data["dimensions_m"] = {"length": 500, "beam": 0.001, "depth": 500.0}
    assert validate_profile(data)[1] == []


@pytest.mark.parametrize("key", ["length_mm", "width_mm", "height_mm"])
@pytest.mark.parametrize("value", [0, -5, 500001, 10.5, 10.0, "10", True, None])
def test_hold_mm(key, value):
    assert f"hold.{key}" in errors_of(lambda d: d["hold"].update({key: value}))


def test_hold_mm_boundary_ok():
    data = good()
    data["hold"].update(length_mm=500000, width_mm=1, height_mm=500000)
    assert validate_profile(data)[1] == []


def test_hold_id_name_status():
    assert "hold.id" in errors_of(lambda d: d["hold"].update(id="hold-1"))
    assert "hold.id" in errors_of(lambda d: d["hold"].update(id="A" * 33))
    assert "hold.name" in errors_of(lambda d: d["hold"].update(name=""))
    assert "hold.name" in errors_of(lambda d: d["hold"].update(name="x" * 101))
    assert "hold.status" in errors_of(lambda d: d["hold"].update(status="GUESSED"))
    assert "hold.status" in errors_of(lambda d: d["hold"].pop("status"))
    for status in ("ESTIMATED", "SOURCED", "MEASURED"):
        data = good()
        data["hold"]["status"] = status
        assert validate_profile(data)[1] == []


def test_cases_count():
    assert "cases" in errors_of(lambda d: d.update(cases=[]))
    extra = lambda n: [{"id": f"C{i}", "cargo_mass_g": 1, "draft_m": 1.0} for i in range(n)]
    assert "cases" in errors_of(lambda d: d.update(cases=extra(21)))
    data = good()
    data["cases"] = extra(20)
    assert validate_profile(data)[1] == []


def test_case_fields():
    assert "cases[0].id" in errors_of(lambda d: d["cases"][0].update(id="vr-si"))
    assert "cases[0].id" in errors_of(lambda d: d["cases"][0].update(id="A" * 33))
    for value in (0, -1, 1.5, "3", True):
        assert "cases[0].cargo_mass_g" in errors_of(lambda d: d["cases"][0].update(cargo_mass_g=value))
    for value in (0, -0.1, float("nan"), "4.6", True):
        assert "cases[1].draft_m" in errors_of(lambda d: d["cases"][1].update(draft_m=value))
    assert "cases[0].deadweight_t" in errors_of(lambda d: d["cases"][0].update(deadweight_t=0))
    assert "cases[0].freeboard_mm" in errors_of(lambda d: d["cases"][0].update(freeboard_mm=-1))
    data = good()
    data["cases"][0].update(deadweight_t=None, freeboard_mm=None)
    assert validate_profile(data)[1] == []
    data["cases"][0] = {"id": "ONLY", "cargo_mass_g": 1, "draft_m": 2}
    assert validate_profile(data)[1] == []


def test_duplicate_case_ids():
    errors = errors_of(lambda d: d["cases"][1].update(id=d["cases"][0]["id"]))
    assert "cases" in errors and "VR-SI" in errors["cases"] and "trùng" in errors["cases"]


def test_notes_limits():
    assert "notes" in errors_of(lambda d: d.update(notes=["x"] * 11))
    assert "notes[2]" in errors_of(lambda d: d.update(notes=["a", "b", "x" * 501]))
    assert "notes[0]" in errors_of(lambda d: d.update(notes=[5]))
    data = good()
    data["notes"] = ["x" * 500] * 10
    assert validate_profile(data)[1] == []
    data["notes"] = []
    assert validate_profile(data)[1] == []


def test_source_documents_limits():
    assert "provenance.source_documents" in errors_of(lambda d: d["provenance"].update(source_documents=[]))
    doc = {"title": "Tài liệu"}
    assert "provenance.source_documents" in errors_of(lambda d: d["provenance"].update(source_documents=[doc] * 11))
    assert "provenance.source_documents[0].title" in errors_of(lambda d: d["provenance"].update(source_documents=[{"title": ""}]))
    assert "provenance.source_documents[0].sha256" in errors_of(
        lambda d: d["provenance"].update(source_documents=[{"title": "x", "sha256": "ABC"}]))
    data = good()
    data["provenance"]["source_documents"] = [doc] * 10
    assert validate_profile(data)[1] == []


def test_field_status_values():
    for key in ("dimensions_m", "hold", "cases"):
        assert f"provenance.field_status.{key}" in errors_of(lambda d: d["provenance"]["field_status"].update({key: "UNKNOWN"}))
        assert f"provenance.field_status.{key}" in errors_of(lambda d: d["provenance"]["field_status"].pop(key))
    assert "provenance.field_status.other" in errors_of(lambda d: d["provenance"]["field_status"].update(other="SOURCED"))


def test_landmark_count_and_fields():
    assert "landmarks" in errors_of(lambda d: d.update(landmarks=d["landmarks"][:2]))
    lm = {"name": "L", "glb_m": [0, 0, 0], "hold_mm": [0, 0, 0]}
    assert "landmarks" in errors_of(lambda d: d.update(landmarks=[lm] * 21))
    data = good()
    data["landmarks"] = [lm] * 20
    assert validate_profile(data)[1] == []
    assert "landmarks[0].name" in errors_of(lambda d: d["landmarks"][0].update(name=""))
    assert "landmarks[0].hold_mm[1]" in errors_of(lambda d: d["landmarks"][0].update(hold_mm=[0, 1.5, 0]))
    assert "landmarks[0].hold_mm" in errors_of(lambda d: d["landmarks"][0].update(hold_mm=[0, 0]))
    assert "landmarks[0].glb_m[2]" in errors_of(lambda d: d["landmarks"][0].update(glb_m=[0, 0, float("nan")]))
    assert "landmarks[0].glb_m[0]" in errors_of(lambda d: d["landmarks"][0].update(glb_m=[1000.5, 0, 0]))
    assert "landmarks[0].glb_m" in errors_of(lambda d: d["landmarks"][0].update(glb_m=[0, 0, 0, 0]))


def test_transform_limits():
    for yaw in (45, -90, 360, 91.5, "90", True, None):
        assert "transform.yaw_deg" in errors_of(lambda d: d["transform"].update(yaw_deg=yaw))
    for yaw in (0, 90, 180, 270):
        data = good()
        data["transform"]["yaw_deg"] = yaw
        assert validate_profile(data)[1] == []
    assert "transform.translation_m" in errors_of(lambda d: d["transform"].update(translation_m=[0, 0]))
    assert "transform.translation_m[0]" in errors_of(lambda d: d["transform"].update(translation_m=[1001, 0, 0]))
    assert "transform.translation_m[1]" in errors_of(lambda d: d["transform"].update(translation_m=[0, float("inf"), 0]))
    assert "hoặc" in errors_of(lambda d: d["transform"].update(yaw_deg=45))["transform.yaw_deg"]
    assert "transform.scale" in errors_of(lambda d: d["transform"].update(scale=2))


def test_contract_extra_and_missing_fields():
    assert "contract_version" in errors_of(lambda d: d.update(contract_version="scst.vessel-profile.v2"))
    assert "contract_version" in errors_of(lambda d: d.pop("contract_version"))
    assert "surprise" in errors_of(lambda d: d.update(surprise=1))
    assert "hold" in errors_of(lambda d: d.pop("hold"))
    assert "hull_mesh_names" in errors_of(lambda d: d.update(hull_mesh_names=["x"] * 51))
    assert "hull_mesh_names[0]" in errors_of(lambda d: d.update(hull_mesh_names=["x" * 101]))
    data = good()
    data.pop("hull_mesh_names")
    assert validate_profile(data)[1] == []


@pytest.mark.parametrize("data", [None, [], "profile", 5])
def test_non_object_input(data):
    model, errors = validate_profile(data)
    assert model is None and errors[0]["field"] == "profile" and DIACRITICS.search(errors[0]["message"])


def test_size_limit_256_kib():
    assert MAX_PROFILE_BYTES == 256 * 1024
    assert check_profile_size(MAX_PROFILE_BYTES) == []
    errors = check_profile_size(MAX_PROFILE_BYTES + 1)
    assert errors[0]["field"] == "profile" and "256 KiB" in errors[0]["message"] and DIACRITICS.search(errors[0]["message"])
