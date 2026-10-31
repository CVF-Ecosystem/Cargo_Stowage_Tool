from ..model import CargoUnit, Placement


def footprint(unit: CargoUnit, placement: Placement) -> tuple[int, int, int]:
    if placement.yaw_deg % 180:
        return unit.width_mm, unit.length_mm, unit.height_mm
    return unit.length_mm, unit.width_mm, unit.height_mm




def bounds(unit, placement):
    low = (placement.x_mm, placement.y_mm, placement.z_mm)
    return low, tuple(a + b for a, b in zip(low, footprint(unit, placement)))


def contained(low, high, hold):
    return all(v >= 0 for v in low) and all(a <= b for a, b in zip(high, (hold.length_mm, hold.width_mm, hold.height_mm)))


def overlaps(alo, ahi, blo, bhi):
    return all(max(a, b) < min(c, d) for a, b, c, d in zip(alo, blo, ahi, bhi))
