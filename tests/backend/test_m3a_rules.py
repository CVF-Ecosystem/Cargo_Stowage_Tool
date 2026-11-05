"""M3a D2: COLUMNS_V1 stacking rules in domain/rules, and the same rule at every API entry point."""
import time
from copy import deepcopy
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.domain.model import CargoUnit, Limits, Placement, Plan
from app.domain import rules
from app.domain.rules import evaluate

client = TestClient(app)
NEW_CODES = {"SUPPORT_MISSING", "SUPPORT_LEVEL_MISMATCH", "SUPPORT_AREA_LOW", "SUPPORT_CENTRE_UNSUPPORTED", "LAYER_INDEX_INVALID"}
OLD_UNCHECKED = ["Kê, chèn và chằng buộc", "Chất xếp nhiều tầng", "Ổn định phương tiện", "Tải cục bộ đáy hầm", "Hàng cũ trong hầm mục tiêu"]
COLUMNS_UNCHECKED = ["Kê, chèn và chằng buộc", "Tải chồng cho phép trên bó (chưa có dữ liệu)", "Ổn định phương tiện",
                     "Tải cục bộ đáy hầm", "Hàng cũ trong hầm mục tiêu"]


def unit(uid, l=1000, w=1000, h=300):
    return dict(id=uid, name="Bó " + uid, kind="BAR_BUNDLE", requirement="optional", length_mm=l, width_mm=w, height_mm=h, mass_g=1000)


def put(uid, x=0, y=0, z=0, layer=0, by=(), yaw=0):
    return dict(unit_id=uid, x_mm=x, y_mm=y, z_mm=z, layer=layer, supported_by=list(by), yaw_deg=yaw)


def plan(units, placements, stacking="COLUMNS_V1"):
    p = client.get("/api/demo").json()["plan"]  # hold 14000 x 8500 x 4000 mm
    p.update(contract_version="scst.m2a.v1", source="USER_ENTERED", cargo_source="USER_ENTERED", vessel=None,
             units=units, placements=placements)
    if stacking is not None:
        p["stacking"] = stacking
    return p


def run(units, placements, stacking="COLUMNS_V1"):
    r = client.post("/api/validate", json=plan(units, placements, stacking))
    assert r.status_code == 200, r.text
    return r.json()


def codes(result):
    return [i["code"] for i in result["issues"]]


def evaluate_um(monkeypatch, plan_model):
    """evaluate() without re-validating the plan: legacy contracts cannot carry dimensions_um, but the rule must be exact in um."""
    monkeypatch.setattr(rules, "Evaluation", lambda **kw: SimpleNamespace(**kw))
    return evaluate(plan_model)


def stack3():
    """Valid three-layer column B001 <- B002 <- B003."""
    return ([unit("B001"), unit("B002"), unit("B003")],
            [put("B001"), put("B002", z=300, layer=1, by=["B001"]), put("B003", z=600, layer=2, by=["B002"])])


def test_valid_stack_passes_and_lists_unchecked():
    r = run(*stack3())
    assert r["issues"] == [] and r["basic_checks_passed"] is True and r["status"] == "RULES_CHECKED"
    assert r["unchecked"] == COLUMNS_UNCHECKED and r["plan"]["stacking"] == "COLUMNS_V1"


@pytest.mark.parametrize("by", [[], ["NOPE"], ["B002"], ["B001", "B001"], ["B001", "NOPE"]], ids=["empty", "unknown", "self", "duplicate", "mixed"])
def test_support_missing_raised(by):
    r = run([unit("B001"), unit("B002")], [put("B001"), put("B002", z=300, layer=1, by=by)])
    issue = next(i for i in r["issues"] if i["code"] == "SUPPORT_MISSING")
    assert issue["unit_ids"][0] == "B002" and "B002" in issue["message"]
    assert {c for c in codes(r)} <= {"SUPPORT_MISSING"} and r["status"] == "DRAFT" and not r["basic_checks_passed"]
    if by and by != ["B001", "B001"]:
        assert issue["unit_ids"][1:] == [b for b in dict.fromkeys(by) if b in {"NOPE", "B002"}]


def test_support_missing_unplaced_supporter_is_not_a_placed_unit():
    # B001 exists in the manifest but is not placed.
    r = run([unit("B001"), unit("B002")], [put("B002", z=300, layer=1, by=["B001"])])
    assert [i["unit_ids"] for i in r["issues"] if i["code"] == "SUPPORT_MISSING"] == [["B002", "B001"]]


def test_support_missing_negative():
    assert "SUPPORT_MISSING" not in codes(run(*stack3()))


def test_level_mismatch_raised_with_vietnamese_message():
    r = run([unit("B001"), unit("B002")], [put("B001"), put("B002", z=310, layer=1, by=["B001"])])
    issue = next(i for i in r["issues"] if i["code"] == "SUPPORT_LEVEL_MISMATCH")
    assert issue["unit_ids"] == ["B002", "B001"]
    assert issue["message"] == "B002: bó đỡ B001 có mặt trên 300 mm, không khớp cao độ đặt 310 mm."
    # Level mismatch skips the area and centre checks for that placement.
    assert set(codes(r)) == {"SUPPORT_LEVEL_MISMATCH"}


def test_level_mismatch_on_floor_with_supporter():
    r = run([unit("B001"), unit("B002")], [put("B001"), put("B002", x=2000, by=["B001"])])
    issue = next(i for i in r["issues"] if i["code"] == "SUPPORT_LEVEL_MISMATCH")
    assert issue["unit_ids"] == ["B002", "B001"]


def test_level_mismatch_one_issue_per_wrong_supporter():
    units = [unit("B001"), unit("B002", h=250), unit("B003")]
    pl = [put("B001"), put("B002", x=1000), put("B003", z=300, layer=1, by=["B001", "B002"])]
    r = run(units, pl)
    assert [i["unit_ids"] for i in r["issues"] if i["code"] == "SUPPORT_LEVEL_MISMATCH"] == [["B003", "B002"]]


def test_level_rounds_supporter_top_up_to_mm_grid(monkeypatch):
    base = Plan.model_validate(plan([unit("B001"), unit("B002")], []))

    def level(z):
        u = CargoUnit.model_construct(**{**unit("B001", 1000, 1000, 300), "dimensions_um": (1_000_000, 1_000_000, 300_400), "source_ref": None})
        top = CargoUnit.model_construct(**{**unit("B002", 1000, 1000, 300), "dimensions_um": (1_000_000, 1_000_000, 300_000), "source_ref": None})
        pl = [Placement(unit_id="B001", x_mm=0, y_mm=0, yaw_deg=0), Placement(unit_id="B002", x_mm=0, y_mm=0, z_mm=z, layer=1, supported_by=["B001"], yaw_deg=0)]
        return evaluate_um(monkeypatch, base.model_copy(update={"units": [u, top], "placements": pl}))
    assert level(301).basic_checks_passed
    for z in (300, 302):
        r = level(z)
        assert [i.code for i in r.issues if i.code != "OVERLAP"] == ["SUPPORT_LEVEL_MISMATCH"]   # z=300 also overlaps 300,4 mm
    assert "300,4 mm" in next(i for i in level(300).issues if i.code == "SUPPORT_LEVEL_MISMATCH").message


def test_area_exactly_90_percent_passes_and_below_fails_in_mm():
    ok = run([unit("B001", 1000, 900), unit("B002", 1000, 1000)], [put("B001"), put("B002", z=300, layer=1, by=["B001"])])
    assert ok["issues"] == []
    low = run([unit("B001", 1000, 899), unit("B002", 1000, 1000)], [put("B001"), put("B002", z=300, layer=1, by=["B001"])])
    issue = next(i for i in low["issues"] if i["code"] == "SUPPORT_AREA_LOW")
    assert issue["unit_ids"] == ["B002", "B001"] and "89,9%" in issue["message"] and "B001" in issue["message"]


def _um_case(monkeypatch, supporters, p_dims=(1000, 10, 100)):
    """P sits at z=300 mm over supporters stacked at the same mm origin; dimensions are exact micrometres."""
    base = Plan.model_validate(plan([unit("B001")], []))
    units = [CargoUnit.model_construct(**{**unit("P"), "dimensions_um": p_dims, "source_ref": None})]
    pl = [Placement(unit_id="P", x_mm=0, y_mm=0, z_mm=300, layer=1, supported_by=[f"S{i}" for i in range(len(supporters))], yaw_deg=0)]
    for i, dims in enumerate(supporters):
        units.append(CargoUnit.model_construct(**{**unit(f"S{i}"), "dimensions_um": dims, "source_ref": None}))
        pl.append(Placement(unit_id=f"S{i}", x_mm=0, y_mm=0, yaw_deg=0))
    return evaluate_um(monkeypatch, base.model_copy(update={"units": units, "placements": pl}))


def test_area_boundary_exact_in_um2(monkeypatch):
    # P base 1000 x 10 um = 10 000 um2; 90% = 9 000 um2 exactly.
    exact = _um_case(monkeypatch, [(1000, 9, 300_000)])
    assert [i.code for i in exact.issues] == []
    # Union of 1000x8 and 999x9 (overlapping supporters) = 8 000 + 999 = 8 999 um2: one um2 short.
    short = _um_case(monkeypatch, [(1000, 8, 300_000), (999, 9, 300_000)])
    assert [i.code for i in short.issues if i.code != "OVERLAP"] == ["SUPPORT_AREA_LOW"]
    assert "89,9%" in next(i for i in short.issues if i.code == "SUPPORT_AREA_LOW").message
    # Overlapping supporters count once: two identical 1000x9 supporters still cover exactly 90%.
    twice = _um_case(monkeypatch, [(1000, 9, 300_000), (1000, 9, 300_000)])
    assert [i.code for i in twice.issues if i.code != "OVERLAP"] == []


def test_area_counts_union_of_two_supporters():
    units = [unit("B001", 500, 1000), unit("B002", 500, 1000), unit("B003", 1000, 1000)]
    pl = [put("B001"), put("B002", x=500), put("B003", z=300, layer=1, by=["B001", "B002"])]
    assert run(units, pl)["issues"] == []


def test_centre_on_edge_passes_just_outside_fails():
    # P is 1001 mm long: centre at 500,5 mm. Supporters are 501 mm or 500 mm long, then a 1 mm gap-free/with-gap neighbour.
    def case(len1, x2):
        units = [unit("B001", len1, 1000), unit("B002", 500, 1000), unit("B003", 1001, 1000)]
        pl = [put("B001"), put("B002", x=x2), put("B003", z=300, layer=1, by=["B001", "B002"])]
        return run(units, pl)
    assert case(501, 501)["issues"] == []                        # [0,501] holds the centre 500,5; B002 [501,1001]
    out = case(500, 501)                                           # [0,500] and [501,1001] leave 500,5 uncovered
    assert codes(out) == ["SUPPORT_CENTRE_UNSUPPORTED"]
    assert out["issues"][0]["unit_ids"] == ["B003", "B001", "B002"]


def test_centre_exactly_on_closed_edge():
    # P 1000 mm long, centre 500 mm: supporter [0,500] contains it on its edge.
    units = [unit("B001", 500, 1000), unit("B002", 500, 1000), unit("B003", 1000, 1000)]
    assert run(units, [put("B001"), put("B002", x=501), put("B003", z=300, layer=1, by=["B001", "B002"])])["issues"] == []
    short = [unit("B001", 499, 1000), unit("B002", 500, 1000), unit("B003", 1000, 1000)]   # [0,499] and [501,1001]
    assert codes(run(short, [put("B001"), put("B002", x=501), put("B003", z=300, layer=1, by=["B001", "B002"])])) == ["SUPPORT_CENTRE_UNSUPPORTED"]


@pytest.mark.parametrize("pl", [
    [put("B001"), put("B002", z=300, layer=2, by=["B001"])],
    [put("B001"), put("B002", z=300, layer=0, by=["B001"])],
    [put("B001", layer=1), put("B002", z=300, layer=2, by=["B001"])],
], ids=["too-high", "zero", "floor-layer-nonzero"])
def test_layer_index_invalid_raised(pl):
    r = run([unit("B001"), unit("B002")], pl)
    assert "LAYER_INDEX_INVALID" in codes(r) and r["status"] == "DRAFT"
    assert all(c == "LAYER_INDEX_INVALID" for c in codes(r)) or pl[0]["layer"] == 1


def test_layer_is_max_of_supporters_plus_one():
    # B004 straddles two layer-0 supporters whose tops are both at 300 mm.
    units = [unit("B001"), unit("B002", 1000, 1000, 300), unit("B003", 1000, 1000, 300), unit("B004", 2000, 1000)]
    pl = [put("B001", z=0), put("B002", x=1000, z=0), put("B004", z=300, layer=1, by=["B001", "B002"])]
    assert run(units, pl)["issues"] == []
    pl_bad = [put("B001"), put("B002", x=1000), put("B004", z=300, layer=2, by=["B001", "B002"])]
    assert codes(run(units, pl_bad)) == ["LAYER_INDEX_INVALID"]


def test_layer_negative_valid_stack():
    assert "LAYER_INDEX_INVALID" not in codes(run(*stack3()))


def test_stack_over_hold_height_is_out_of_bounds():
    units = [unit("B001", h=2000), unit("B002", h=2000), unit("B003", h=2000)]
    pl = [put("B001"), put("B002", z=2000, layer=1, by=["B001"]), put("B003", z=4000, layer=2, by=["B002"])]
    r = run(units, pl)
    assert [(i["code"], i["unit_ids"]) for i in r["issues"]] == [("OUT_OF_BOUNDS", ["B003"])] and r["status"] == "DRAFT"


def test_overlap_between_layers_is_3d_overlap():
    units = [unit("B001"), unit("B002"), unit("B003")]
    pl = [put("B001"), put("B002", z=300, layer=1, by=["B001"]), put("B003", z=150, layer=1, by=["B001"])]
    r = run(units, pl)
    assert ("OVERLAP", ["B001", "B003"]) in [(i["code"], i["unit_ids"]) for i in r["issues"]]
    assert ("OVERLAP", ["B002", "B003"]) in [(i["code"], i["unit_ids"]) for i in r["issues"]]


def test_face_touching_between_layers_is_allowed():
    assert "OVERLAP" not in codes(run(*stack3()))


def test_new_codes_make_status_draft():
    r = run([unit("B001"), unit("B002")], [put("B001"), put("B002", z=300, layer=1)])
    assert codes(r) == ["SUPPORT_MISSING"] and r["status"] == "DRAFT" and r["basic_checks_passed"] is False


def test_overweight_and_required_unplaced_unchanged_with_stacking():
    units = [unit("B001"), {**unit("B002"), "requirement": "required"}]
    r = run(units, [put("B001")])
    assert codes(r) == ["REQUIRED_UNPLACED"] and r["status"] == "GEOMETRY_FEASIBLE"
    p = plan(units[:1], [put("B001")]); p["limits"]["voyage_cargo_limit_g"] = 999
    p["limits"]["certificate_cargo_limit_g"] = 999
    assert [i["code"] for i in client.post("/api/validate", json=p).json()["issues"]] == ["OVERWEIGHT"]


@pytest.mark.parametrize("stacking", [None, "SINGLE_LAYER"])
def test_single_layer_and_absent_keep_layer_unsupported(stacking):
    r = run(*stack3(), stacking=stacking)
    assert codes(r) == ["LAYER_UNSUPPORTED", "LAYER_UNSUPPORTED"]
    assert [i["unit_ids"] for i in r["issues"]] == [["B002"], ["B003"]]
    assert r["issues"][0]["message"] == "B002: M1 chỉ kiểm bố trí một lớp trên đáy hầm (Z = 0)."
    assert r["unchecked"] == OLD_UNCHECKED and r["status"] == "DRAFT"
    assert not NEW_CODES & set(codes(r))
    assert ("stacking" in r["plan"]) == (stacking is not None)


# --- Every API entry point applies the same rule ---

def test_snapshot_save_and_open_use_same_rule(tmp_path, monkeypatch):
    monkeypatch.setenv("SCST_DATA_DIR", str(tmp_path))
    good = plan(*stack3())
    saved = client.post("/api/snapshots", json={"name": "Synthetic stack", "plan": good}).json()
    opened = client.get("/api/snapshots/" + saved["id"])
    assert opened.status_code == 200
    j = opened.json()
    assert j["issues"] == [] and j["basic_checks_passed"] and j["unchecked"] == COLUMNS_UNCHECKED and j["plan"]["stacking"] == "COLUMNS_V1"
    bad = plan([unit("B001"), unit("B002")], [put("B001"), put("B002", z=310, layer=1, by=["B001"])])
    saved = client.post("/api/snapshots", json={"name": "Synthetic bad stack", "plan": bad}).json()
    j = client.get("/api/snapshots/" + saved["id"]).json()
    assert codes(j) == ["SUPPORT_LEVEL_MISMATCH"] and j["status"] == "DRAFT"
    assert j == client.post("/api/validate", json=bad).json()


def test_compare_evaluates_both_sides_with_the_rule():
    before = plan([unit("B001"), unit("B002")], [put("B001"), put("B002", z=310, layer=1, by=["B001"])])
    after = deepcopy(before); after["placements"][1]["z_mm"] = 300
    r = client.post("/api/plans/compare", json={"before": before, "after": after})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["before"]["issue_count"] == 1 and not j["before"]["basic_checks_passed"] and j["before"]["status"] == "DRAFT"
    assert j["after"]["issue_count"] == 0 and j["after"]["basic_checks_passed"] and j["after"]["unchecked"] == COLUMNS_UNCHECKED
    assert j["delta"]["issue_count"] == -1


# --- Real pipe-list data: exact um dimensions, rounded-up levels ---

def pipe_plan():
    base = client.get("/api/demo").json()["plan"]
    p = client.post("/api/pipe-list/preview", json=base).json()["plan"]
    p["stacking"] = "COLUMNS_V1"
    return p


def test_pipe_list_levels_use_exact_um_heights():
    p = pipe_plan()
    u1, u2 = p["units"][0], p["units"][1]
    assert u1["dimensions_um"] == [6401000, 337600, 295400] and u2["dimensions_um"] == u1["dimensions_um"]
    p["placements"] = [put(u1["id"]), put(u2["id"], z=296, layer=1, by=[u1["id"]])]   # ceil(295,4) = 296 mm
    r = client.post("/api/validate", json=p)
    assert r.status_code == 200, r.text
    assert r.json()["issues"] == []
    for z in (295, 297):
        p["placements"][1]["z_mm"] = z
        got = [i["code"] for i in client.post("/api/validate", json=p).json()["issues"] if i["code"] != "OVERLAP"]   # z=295 also overlaps
        assert got == ["SUPPORT_LEVEL_MISMATCH"]


def test_evaluate_1076_placements_is_fast():
    p = pipe_plan()
    # One column per unit would overflow the hold; geometry issues are fine here, only speed is measured.
    p["placements"] = [put(u["id"], x=(i % 2) * 6500, y=(i // 2 % 25) * 338, z=0 if i < 50 else 296, layer=0 if i < 50 else 1,
                           by=[] if i < 50 else [p["units"][i - 50]["id"]]) for i, u in enumerate(p["units"])]
    plan_model = Plan.model_validate(p)
    start = time.perf_counter()
    result = evaluate(plan_model)
    assert time.perf_counter() - start < 5 and result.total_issues is not None
