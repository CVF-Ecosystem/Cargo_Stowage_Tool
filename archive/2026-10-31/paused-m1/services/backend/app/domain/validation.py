"""Deterministic axis-aligned checks; face touching is allowed, no epsilon."""
from .models import CargoUnit, Evaluation, Issue, Placement, Plan, Summary


def footprint(unit: CargoUnit, placement: Placement) -> tuple[int, int, int]:
    if placement.yaw_deg % 180:
        return unit.width_mm, unit.length_mm, unit.height_mm
    return unit.length_mm, unit.width_mm, unit.height_mm


def evaluate(plan: Plan) -> Evaluation:
    units = {u.id: u for u in plan.units}
    placed_ids = {p.unit_id for p in plan.placements}
    mass = sum(units[p.unit_id].mass_g for p in plan.placements)
    issues: list[Issue] = []
    hold = plan.hold
    if mass > hold.cargo_limit_g:
        issues.append(Issue(code="OVERWEIGHT", unit_ids=[], message=f"Vượt giới hạn khối lượng hàng {mass - hold.cargo_limit_g:,} g."))
    boxes = []
    for p in plan.placements:
        dims = footprint(units[p.unit_id], p)
        low = (p.x_mm, p.y_mm, p.z_mm)
        high = tuple(a + b for a, b in zip(low, dims))
        if any(v < 0 for v in low) or any(a > b for a, b in zip(high, (hold.length_mm, hold.width_mm, hold.height_mm))):
            issues.append(Issue(code="OUT_OF_BOUNDS", unit_ids=[p.unit_id], message=f"{p.unit_id} vượt biên hầm."))
        if p.z_mm != 0:
            issues.append(Issue(code="LAYER_UNSUPPORTED", unit_ids=[p.unit_id], message=f"{p.unit_id}: M1 chỉ kiểm bố trí một lớp trên đáy hầm (Z = 0)."))
        boxes.append((p.unit_id, low, high))
    for i, (aid, alo, ahi) in enumerate(boxes):
        for bid, blo, bhi in boxes[i + 1:]:
            if all(max(a, b) < min(c, d) for a, b, c, d in zip(alo, blo, ahi, bhi)):
                issues.append(Issue(code="OVERLAP", unit_ids=[aid, bid], message=f"{aid} giao nhau với {bid}."))
    unplaced = [u.id for u in plan.units if u.id not in placed_ids and u.requirement != "excluded"]
    for u in plan.units:
        if u.requirement == "required" and u.id not in placed_ids:
            issues.append(Issue(code="REQUIRED_UNPLACED", unit_ids=[u.id], message=f"{u.id} là hàng bắt buộc chưa được xếp."))
    return Evaluation(
        plan=plan,
        summary=Summary(manifest_mass_g=sum(u.mass_g for u in plan.units), placed_mass_g=mass,
                        remaining_capacity_g=hold.cargo_limit_g - mass, placed_count=len(placed_ids),
                        unplaced_ids=unplaced, excluded_ids=[u.id for u in plan.units if u.requirement == "excluded"]),
        basic_checks_passed=not issues, issues=issues,
        unchecked=["Kê, chèn và chằng buộc", "Chất xếp nhiều tầng", "Ổn định phương tiện", "Tải cục bộ đáy hầm"],
    )
