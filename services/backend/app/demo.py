from .domain.model import CargoUnit, Hold, Limits, Placement, Plan


def demo_plan() -> Plan:
    """Hand-authored synthetic units, not inferred weights from a manifest total."""
    units = [CargoUnit(id=f"{'ST' if i < 6 else 'PP'}-{i+1:03}",
                       name="Bó thép thanh" if i < 6 else "Bó thép ống",
                       kind="BAR_BUNDLE" if i < 6 else "PIPE_BUNDLE",
                       requirement="required", length_mm=6000, width_mm=900, height_mm=650,
                       mass_g=2_500_000 if i < 6 else 1_850_000) for i in range(12)]
    units.append(CargoUnit(id="PP-013", name="Bó thép ống dự phòng", kind="PIPE_BUNDLE",
                           requirement="optional", length_mm=6000, width_mm=900, height_mm=650, mass_g=1_850_000))
    return Plan(hold=Hold(id="HOLD-01", name="Hầm mẫu 01", length_mm=14000, width_mm=8500,
                          height_mm=4000), limits=Limits(certificate_cargo_limit_g=32_000_000, voyage_cargo_limit_g=32_000_000), units=units,
                placements=[Placement(unit_id=u.id, x_mm=500 if i < 6 else 7500,
                                      y_mm=550 + (i % 6) * 1200, yaw_deg=0) for i, u in enumerate(units[:12])])
