"""Deterministic axis-aligned checks; face touching is allowed, no epsilon."""
from ..model import Evaluation, Issue, Plan, Summary
from ..geometry import bounds_um, contained_um


GEOMETRY_CODES = {"OUT_OF_BOUNDS", "OVERLAP", "LAYER_UNSUPPORTED", "EMPTY_MANIFEST", "SUPPORT_MISSING",
                  "SUPPORT_LEVEL_MISMATCH", "SUPPORT_AREA_LOW", "SUPPORT_CENTRE_UNSUPPORTED", "LAYER_INDEX_INVALID"}
UNCHECKED_SINGLE = ["Kê, chèn và chằng buộc", "Chất xếp nhiều tầng", "Ổn định phương tiện", "Tải cục bộ đáy hầm", "Hàng cũ trong hầm mục tiêu"]
UNCHECKED_COLUMNS = ["Kê, chèn và chằng buộc", "Tải chồng cho phép trên bó (chưa có dữ liệu)", "Ổn định phương tiện",
                     "Tải cục bộ đáy hầm", "Hàng cũ trong hầm mục tiêu"]


def _mm(um: int) -> str:
    """Micrometres as millimetres with a Vietnamese decimal comma, without trailing zeros."""
    whole, frac = divmod(um, 1000)
    return f"{whole},{frac:03d}".rstrip("0").rstrip(",")


def _union_area(rects) -> int:
    """Exact area of the union of axis-aligned (x0, y0, x1, y1) integer rectangles (coordinate compression)."""
    rects = [r for r in rects if r[2] > r[0] and r[3] > r[1]]
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    area = 0
    for x0, x1 in zip(xs, xs[1:]):
        spans = sorted((r[1], r[3]) for r in rects if r[0] <= x0 and r[2] >= x1)
        covered = 0
        end = None
        for lo, hi in spans:
            if end is None or lo > end:
                covered += hi - lo
                end = hi
            elif hi > end:
                covered += hi - end
                end = hi
        area += covered * (x1 - x0)
    return area


def _check_columns(plan, boxes, add):
    """COLUMNS_V1 support rules (SPEC M3a D2) for every placement, exact integer micrometres.

    Level decision: heights are exact um but z_mm is an integer mm, so a supporter's top
    must round UP to the mm grid to equal z_mm: (top_um + 999) // 1000 == z_mm (exact for integer-mm units).
    Layer is checked whenever the supporter ids are valid (also after a level/area/centre failure)."""
    by_id = {pid: (lo, hi) for pid, lo, hi in boxes}
    layers = {p.unit_id: p.layer for p in plan.placements}
    for p in plan.placements:
        pid = p.unit_id
        if p.z_mm < 0:
            continue  # already OUT_OF_BOUNDS
        if p.z_mm == 0:
            if p.supported_by:
                add("SUPPORT_LEVEL_MISMATCH", [pid, *p.supported_by], f"{pid}: đặt trên đáy hầm (Z = 0) nhưng khai báo bó đỡ {', '.join(p.supported_by)}.")
            if p.layer != 0:
                add("LAYER_INDEX_INVALID", [pid], f"{pid}: đặt trên đáy hầm (Z = 0) phải ở tầng 0, đang khai báo tầng {p.layer}.")
            continue
        seen = set()
        bad = []
        for s in p.supported_by:
            if (s == pid or s not in by_id or s in seen) and s not in bad:
                bad.append(s)
            seen.add(s)
        if not p.supported_by or bad:
            if not p.supported_by:
                add("SUPPORT_MISSING", [pid], f"{pid}: đặt ở cao độ {p.z_mm} mm nhưng chưa khai báo bó đỡ.")
            else:
                add("SUPPORT_MISSING", [pid, *bad], f"{pid}: bó đỡ không hợp lệ (chưa đặt, trùng lặp hoặc là chính nó): {', '.join(bad)}.")
            continue
        (plo, phi) = by_id[pid]
        level_ok = True
        for s in p.supported_by:
            top = by_id[s][1][2]
            if (top + 999) // 1000 != p.z_mm:
                level_ok = False
                add("SUPPORT_LEVEL_MISMATCH", [pid, s], f"{pid}: bó đỡ {s} có mặt trên {_mm(top)} mm, không khớp cao độ đặt {p.z_mm} mm.")
        if level_ok:
            base = (phi[0] - plo[0]) * (phi[1] - plo[1])
            clipped = []
            for s in p.supported_by:
                slo, shi = by_id[s]
                clipped.append((max(slo[0], plo[0]), max(slo[1], plo[1]), min(shi[0], phi[0]), min(shi[1], phi[1])))
            cover = _union_area(clipped)
            if cover * 10 < base * 9:
                pct = cover * 1000 // base if base > 0 else 0
                add("SUPPORT_AREA_LOW", [pid, *p.supported_by],
                    f"{pid}: bó đỡ {', '.join(p.supported_by)} chỉ phủ {pct // 10},{pct % 10}% diện tích đáy, cần tối thiểu 90%.")
            cx, cy = plo[0] + phi[0], plo[1] + phi[1]  # doubled centre keeps integers
            if not any(2 * by_id[s][0][0] <= cx <= 2 * by_id[s][1][0] and 2 * by_id[s][0][1] <= cy <= 2 * by_id[s][1][1] for s in p.supported_by):
                add("SUPPORT_CENTRE_UNSUPPORTED", [pid, *p.supported_by], f"{pid}: tâm đáy không nằm trên mặt trên của bó đỡ {', '.join(p.supported_by)}.")
        expected = max(layers[s] for s in p.supported_by) + 1
        if p.layer != expected:
            add("LAYER_INDEX_INVALID", [pid, *p.supported_by], f"{pid}: khai báo tầng {p.layer}, cần tầng {expected} theo bó đỡ {', '.join(p.supported_by)}.")


def _overlap_pairs(boxes):
    """Index pairs (i, j), i < j, of boxes whose volumes overlap (strict, face touching allowed).

    Same result and order as the all-pairs loop `for i: for j > i: if overlaps(...)`, but an x sweep:
    only boxes whose x interval overlaps the current one are compared on y and z."""
    order = sorted(range(len(boxes)), key=lambda k: boxes[k][1][0])
    active = []  # (index, x1, y0, y1, z0, z1) of boxes seen earlier (x0 <= current x0)
    pairs = []
    for k in order:
        _, (x0, y0, z0), (x1, y1, z1) = boxes[k]
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            continue  # empty volume never overlaps (strict comparisons)
        live = [a for a in active if a[1] > x0]  # drop boxes ending at or before this x0
        for idx, _ax1, ay0, ay1, az0, az1 in live:
            if ay0 < y1 and y0 < ay1 and az0 < z1 and z0 < az1:
                pairs.append((idx, k) if idx < k else (k, idx))
        live.append((k, x1, y0, y1, z0, z1))
        active = live
    pairs.sort()
    return pairs


def evaluate(plan: Plan) -> Evaluation:
    units = {u.id: u for u in plan.units}
    placed_ids = {p.unit_id for p in plan.placements}
    mass = sum(units[p.unit_id].mass_g for p in plan.placements)
    issues: list[Issue] = []
    pipe = plan.contract_version in ("scst.pipe-list.v1", "scst.pipe-list.v2")
    total = 0
    affected = set()
    has_geometry = False
    def add(code, ids, message):
        nonlocal total, has_geometry
        total += 1
        affected.update(ids)
        has_geometry |= code in GEOMETRY_CODES
        if not pipe or len(issues) < 200:
            issues.append(Issue(code=code,unit_ids=ids,message=message))
    if not plan.units:
        add("EMPTY_MANIFEST", [], "Chưa có bó hàng trong manifest.")
    hold = plan.hold
    capacity = plan.limits.voyage_cargo_limit_g - plan.limits.cargo_onboard_g
    if mass > capacity:
        add("OVERWEIGHT", [], f"Vượt giới hạn khối lượng hàng {mass - capacity:,} g.")
    columns = plan.stacking == "COLUMNS_V1"
    boxes = []
    for p in plan.placements:
        low, high = bounds_um(units[p.unit_id], p)
        if not contained_um(low, high, hold):
            add("OUT_OF_BOUNDS", [p.unit_id], f"{p.unit_id} vượt biên hầm.")
        if not columns and (p.z_mm != 0 or p.layer != 0 or p.supported_by):
            add("LAYER_UNSUPPORTED", [p.unit_id], f"{p.unit_id}: M1 chỉ kiểm bố trí một lớp trên đáy hầm (Z = 0).")
        boxes.append((p.unit_id, low, high))
    for i, j in _overlap_pairs(boxes):
        aid, bid = boxes[i][0], boxes[j][0]
        add("OVERLAP", [aid, bid], f"{aid} giao nhau với {bid}.")
    if columns:
        _check_columns(plan, boxes, add)
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
        unchecked=list(UNCHECKED_COLUMNS if columns else UNCHECKED_SINGLE),
    )
