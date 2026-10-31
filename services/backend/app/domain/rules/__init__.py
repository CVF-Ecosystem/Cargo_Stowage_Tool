"""Deterministic axis-aligned checks; face touching is allowed, no epsilon."""
from ..model import Evaluation, Issue, Plan, Summary
from ..geometry import bounds, contained, overlaps



def evaluate(plan: Plan) -> Evaluation:
    units = {u.id: u for u in plan.units}
    placed_ids = {p.unit_id for p in plan.placements}
    mass = sum(units[p.unit_id].mass_g for p in plan.placements)
    issues: list[Issue] = []
    hold = plan.hold
    capacity = plan.limits.voyage_cargo_limit_g - plan.limits.cargo_onboard_g
    if mass > capacity:
        issues.append(Issue(code="OVERWEIGHT", unit_ids=[], message=f"Vượt giới hạn khối lượng hàng {mass - capacity:,} g."))
    boxes = []
    for p in plan.placements:
        low, high = bounds(units[p.unit_id], p)
        if not contained(low, high, hold):
            issues.append(Issue(code="OUT_OF_BOUNDS", unit_ids=[p.unit_id], message=f"{p.unit_id} vượt biên hầm."))
        if p.z_mm != 0 or p.layer != 0 or p.supported_by:
            issues.append(Issue(code="LAYER_UNSUPPORTED", unit_ids=[p.unit_id], message=f"{p.unit_id}: M1 chỉ kiểm bố trí một lớp trên đáy hầm (Z = 0)."))
        boxes.append((p.unit_id, low, high))
    for i, (aid, alo, ahi) in enumerate(boxes):
        for bid, blo, bhi in boxes[i + 1:]:
            if overlaps(alo, ahi, blo, bhi):
                issues.append(Issue(code="OVERLAP", unit_ids=[aid, bid], message=f"{aid} giao nhau với {bid}."))
    unplaced = [u.id for u in plan.units if u.id not in placed_ids and u.requirement != "excluded"]
    for u in plan.units:
        if u.requirement == "required" and u.id not in placed_ids:
            issues.append(Issue(code="REQUIRED_UNPLACED", unit_ids=[u.id], message=f"{u.id} là hàng bắt buộc chưa được xếp."))
    return Evaluation(
        plan=plan,
        summary=Summary(manifest_mass_g=sum(u.mass_g for u in plan.units), placed_mass_g=mass,
                        remaining_capacity_g=capacity - mass, placed_count=len(placed_ids),
                        unplaced_ids=unplaced, excluded_ids=[u.id for u in plan.units if u.requirement == "excluded"]),
        status=("DRAFT" if any(i.code in {"OUT_OF_BOUNDS", "OVERLAP", "LAYER_UNSUPPORTED"} for i in issues) else "GEOMETRY_FEASIBLE" if issues else "RULES_CHECKED"),
        basic_checks_passed=not issues, issues=issues,
        unchecked=["Kê, chèn và chằng buộc", "Chất xếp nhiều tầng", "Ổn định phương tiện", "Tải cục bộ đáy hầm", "Hàng cũ trong hầm mục tiêu"],
    )
