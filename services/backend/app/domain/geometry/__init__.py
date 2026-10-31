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


def bounds_um(unit, placement):
    """Exact geometry in integer micrometres; placement input stays integer mm."""
    dims = unit.dimensions_um or (unit.length_mm*1000,unit.width_mm*1000,unit.height_mm*1000)
    if placement.yaw_deg % 180:
        dims = (dims[1],dims[0],dims[2])
    low = (placement.x_mm*1000,placement.y_mm*1000,placement.z_mm*1000)
    return low, tuple(a+b for a,b in zip(low,dims))


def contained_um(low, high, hold):
    return all(v >= 0 for v in low) and all(a <= b*1000 for a,b in zip(high,(hold.length_mm,hold.width_mm,hold.height_mm)))
