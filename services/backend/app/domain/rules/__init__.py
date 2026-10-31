"""Deterministic axis-aligned checks; face touching is allowed, no epsilon."""
from ..model import Evaluation, Issue, Plan, Summary
from ..geometry import bounds_um, contained_um, overlaps



def evaluate(plan: Plan) -> Evaluation:
    units = {u.id: u for u in plan.units}
    placed_ids = {p.unit_id for p in plan.placements}
    mass = sum(units[p.unit_id].mass_g for p in plan.placements)
    issues: list[Issue] = []
    pipe = plan.contract_version == "scst.pipe-list.v1"
    total = 0
    affected = set()
    has_geometry = False
    def add(code, ids, message):
        nonlocal total, has_geometry
        total += 1
        affected.update(ids)
        has_geometry |= code in {"OUT_OF_BOUNDS", "OVERLAP", "LAYER_UNSUPPORTED", "EMPTY_MANIFEST"}
        if not pipe or len(issues) < 200:
            issues.append(Issue(code=code,unit_ids=ids,message=message))
    if not plan.units:
        add("EMPTY_MANIFEST", [], "Chưa có bó hàng trong manifest.")
    hold = plan.hold
    capacity = plan.limits.voyage_cargo_limit_g - plan.limits.cargo_onboard_g
    if mass > capacity:
        add("OVERWEIGHT", [], f"Vượt giới hạn khối lượng hàng {mass - capacity:,} g.")
    boxes = []
    for p in plan.placements:
        low, high = bounds_um(units[p.unit_id], p)
        if not contained_um(low, high, hold):
            add("OUT_OF_BOUNDS", [p.unit_id], f"{p.unit_id} vượt biên hầm.")
        if p.z_mm != 0 or p.layer != 0 or p.supported_by:
            add("LAYER_UNSUPPORTED", [p.unit_id], f"{p.unit_id}: M1 chỉ kiểm bố trí một lớp trên đáy hầm (Z = 0).")
        boxes.append((p.unit_id, low, high))
    for i, (aid, alo, ahi) in enumerate(boxes):
        for bid, blo, bhi in boxes[i + 1:]:
            if overlaps(alo, ahi, blo, bhi):
                add("OVERLAP", [aid, bid], f"{aid} giao nhau với {bid}.")
    unplaced = [u.id for u in plan.units if u.id not in placed_ids and u.requirement != "excluded"]
    for u in plan.units:
        if u.requirement == "required" and u.id not in placed_ids:
            add("REQUIRED_UNPLACED", [u.id], f"{u.id} là hàng bắt buộc chưa được xếp.")
    return Evaluation(
        plan=plan,
        summary=Summary(manifest_mass_g=sum(u.mass_g for u in plan.units), placed_mass_g=mass,
                        remaining_capacity_g=capacity - mass, placed_count=len(placed_ids),
                        unplaced_ids=unplaced, excluded_ids=[u.id for u in plan.units if u.requirement == "excluded"]),
        status=("DRAFT" if has_geometry else "GEOMETRY_FEASIBLE" if total else "RULES_CHECKED"),
        basic_checks_passed=not total, issues=issues,
        total_issues=total if pipe else None, issues_truncated=(total > len(issues)) if pipe else None, affected_unit_ids=sorted(affected) if pipe else None,
        unchecked=["Kê, chèn và chằng buộc", "Chất xếp nhiều tầng", "Ổn định phương tiện", "Tải cục bộ đáy hầm", "Hàng cũ trong hầm mục tiêu"],
    )
