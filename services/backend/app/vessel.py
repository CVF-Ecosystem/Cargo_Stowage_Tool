from pathlib import Path
import json

DATA = Path(__file__).resolve().parents[1] / 'data' / 'vessels' / 'vinafco268'
PROFILE = json.loads((DATA / 'profile.json').read_text(encoding='utf-8'))
CASES = {case['id']: case for case in PROFILE['cases']}


def builtin_vinafco_profile() -> dict:
    """VINAFCO268 v1 as a scst.vessel-profile.v1 dict, derived read-only from PROFILE (see SPEC D1.4/D2.5)."""
    from .domain.vessel_profiles import validate_profile  # lazy: domain.model imports this module
    p, g, h, prov = PROFILE, PROFILE['geometry'], PROFILE['hold'], PROFILE['provenance']
    half = p['dimensions_m']['length'] / 2
    # hold frame: x 0 at source x min (aft end, source X points to the bow); y 0 at the port side (source y max); z 0 at the floor
    landmarks = [{
        'name': f'Góc sàn hầm {xname}-{yname}',
        'glb_m': [x - half, g['source_floor_z_m'], -y],
        'hold_mm': [0 if x == g['source_hold_x_min_m'] else h['length_mm'],
                    0 if y == g['source_hold_y_max_m'] else h['width_mm'], 0]}
        for xname, x in (('lái', g['source_hold_x_min_m']), ('mũi', g['source_hold_x_max_m']))
        for yname, y in (('trái', g['source_hold_y_max_m']), ('phải', g['source_hold_y_min_m']))]
    profile = {
        'contract_version': 'scst.vessel-profile.v1', 'id': p['id'], 'version': 1, 'name': p['name'],
        'registration': p['registration'], 'dimensions_m': dict(p['dimensions_m']),
        'hold': {k: h[k] for k in ('id', 'name', 'length_mm', 'width_mm', 'height_mm', 'status')},
        'cases': [{k: c[k] for k in ('id', 'cargo_mass_g', 'draft_m', 'deadweight_t', 'freeboard_mm')} for c in p['cases']],
        'notes': [p['capacity_note'], p['container_note'], p['estimate_note'], prov['freeboard_note']],
        'provenance': {
            'source_documents': [
                {'title': 'Hồ sơ tàu VINAFCO 268 (PDF, trang 1, 4, 5, 6)', 'sha256': prov['source_pdf_sha256']},
                {'title': 'Dữ liệu nguồn JSON của VINAFCO 268', 'sha256': prov['source_json_sha256']},
                {'title': 'Mô hình 3D nguồn GLB của VINAFCO 268', 'sha256': prov['source_glb_sha256']}],
            'field_status': {'dimensions_m': 'SOURCED', 'hold': 'ESTIMATED', 'cases': 'SOURCED'}},
        'transform': {'translation_m': list(g['glb_to_hold_translation_m']), 'yaw_deg': 0},
        'landmarks': landmarks,
        'hull_mesh_names': ['Than_tau_duoi_duong_nuoc', 'Than_tau_tren_duong_nuoc', 'Day_ngoai_than_tau',
                            'Vach_trong_ham_hang_uoc_tinh', 'Thanh_quay_ham_uoc_tinh'],
    }
    model, errors = validate_profile(profile)
    if errors:
        raise ValueError(f'VINAFCO268 built-in profile invalid: {errors}')
    return model.model_dump(mode='json')
