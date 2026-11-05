"""scst.plan-report.v1 (M2d D1): a pure report model derived from an already loaded saved plan.

No I/O, no env, no clock: the caller supplies every input (including generated_utc). Exact ints only (g, mm, um).
build_report derives totals and units from the stored plan alone; reconcile() re-checks them against evaluate(plan).
"""
import hashlib
import json

SCHEMA = 'scst.plan-report.v1'
SAVED_SCHEMA = 'scst.saved-plan.v1'
PIPE_CONTRACTS = ('scst.pipe-list.v1', 'scst.pipe-list.v2')
STATUS_LABEL = {'ESTIMATED': 'ước tính', 'SOURCED': 'lấy từ hồ sơ', 'UNCONFIRMED': 'chưa xác nhận'}
REASONS = {'EXCLUDED': 'Bó được loại trừ khỏi xếp.', 'REQUIRED_UNPLACED': 'Hàng bắt buộc chưa được xếp.',
           'OPTIONAL_UNPLACED': 'Tùy chọn, chưa xếp trong phương án đã lưu (lý do của bộ xếp thử không lưu cùng phương án).'}
UM3_PER_MM3 = 10 ** 9


class ReportReconciliationError(Exception):
    """The report disagrees with evaluate(plan) or with itself; `what` is a Vietnamese description."""

    def __init__(self, what):
        super().__init__(what)
        self.what = what


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def report_hash(report: dict) -> str:
    """sha256 of the canonical model without report_sha256 and header.generated_utc."""
    body = {k: v for k, v in report.items() if k != 'report_sha256'}
    body['header'] = {k: v for k, v in report['header'].items() if k != 'generated_utc'}
    return hashlib.sha256(canonical(body)).hexdigest()


def mm3_text(um3: int) -> str:
    """Exact decimal text of um^3 / 10**9 (no trailing zeros)."""
    whole, rest = divmod(um3, UM3_PER_MM3)
    frac = f'{rest:09d}'.rstrip('0')
    return f'{whole}.{frac}' if frac else str(whole)


def _volume(um3: int):
    return um3 // UM3_PER_MM3 if um3 % UM3_PER_MM3 == 0 else None


def _packing_index(packing):
    groups = {g['group_id']: g for g in (packing or {}).get('groups', [])}
    bundles = {b['bundle_id']: b for g in groups.values() for b in g['bundle_packings']}
    return groups, bundles


def _packing(unit, ref, groups, bundles):
    core = bundles.get(unit.id) or (groups.get(ref.group_id) if ref is not None else None)
    if unit.kind != 'PIPE_BUNDLE' or core is None:
        return None
    return {'status': core['status'], 'layout': core['layout'], 'columns': core['columns'], 'rows': core['rows'],
            'pieces_placed': core['pieces_placed'], 'pieces_source': core['pieces_source'],
            'reason_codes': [r['code'] for r in core['reasons']]}


def _vessel(plan, profile):
    ref = plan.vessel
    if ref is None:
        return None
    return {'vessel_id': ref.vessel_id, 'name': profile['profile']['name'], 'case_id': ref.case_id,
            'builtin': profile['builtin'], 'profile_version': ref.profile_version, 'profile_sha256': ref.profile_sha256,
            'field_status': {k: profile['profile']['provenance']['field_status'][k] for k in ('dimensions_m', 'hold', 'cases')}}


MULTI_LAYER_NOTICE = 'Phương án nhiều tầng: chưa kiểm tải chồng, tải sàn, chằng buộc và ổn định.'


def _notices(hold_status, recheck, units, unchecked, multi_layer=False):
    out = []
    if hold_status != 'MEASURED':
        out.append(('GEOMETRY_UNVERIFIED', f'Chưa xác minh hình học: kích thước hầm là {STATUS_LABEL[hold_status]} (chưa đo thực tế).'))
    if multi_layer:  # M3a D4.4: replaces the single-layer notice for COLUMNS_V1 plans
        out.append(('MULTI_LAYER', MULTI_LAYER_NOTICE))
    else:
        out.append(('SINGLE_LAYER', 'Phương án một tầng (xếp sơ bộ, chưa tối ưu).'))
    if any(u['group_id'] is not None for u in units):  # pipe list only (synthetic PIPE_BUNDLE units carry no packing)
        out.append(('PACKING_DERIVED', 'Packing là dẫn xuất, không phải số đo thực.'))
    if recheck['status'] == 'NEEDS_RECHECK':
        out.append(('NEEDS_RECHECK', f'Phương án cần kiểm lại theo dữ liệu mới: {recheck["latest_revision_id"]} '
                    f'(thêm {recheck["added"]}, bỏ {recheck["removed"]}, đổi {recheck["changed"]} bó; '
                    f'{recheck["placed_affected"]} bó đã đặt bị ảnh hưởng).'))
    if recheck['status'] == 'REVISION_UNAVAILABLE':
        out.append(('REVISION_UNAVAILABLE', 'Không kiểm lại được theo revision mới nhất; dữ liệu revision không phục vụ được.'))
    warned = sorted({u['group_id'] for u in units if u['dimension_warning']})
    if warned:
        out.append(('SOURCE_WARNING', f'Cảnh báo dữ liệu nguồn: các nhóm {", ".join(warned)} có cảnh báo kích thước nguồn.'))
    out.append(('NOT_OPERATIONAL', f'Chưa đủ điều kiện vận hành; các mục chưa kiểm: {" · ".join(unchecked)}.'))
    return [{'code': c, 'message': m} for c, m in out]


def build_report(*, snapshot_id, name, saved_utc, plan_json, plan, evaluation, profile, recheck, packing,
                 revision, generated_utc):
    """Assemble the report from loaded inputs.

    plan_json: stored text verbatim; plan: validated Plan; evaluation: evaluate(plan); profile: vessel_profile_service.detail()
    dict or None; recheck: the cargo.recheck dict; packing: pack_revision() of the pinned revision or None;
    revision: {'revision_id', 'content_sha256'} of the pinned revision or None.
    """
    placed = {p.unit_id: p for p in plan.placements}
    # M3a: multi-layer keys are added only for COLUMNS_V1 plans so legacy report bytes and report_sha256 stay unchanged.
    multi = plan.stacking == 'COLUMNS_V1'
    groups, bundles = _packing_index(packing)
    units, unplaced, mass = [], [], [0, 0]
    volume = {'manifest': 0, 'placed': 0}
    for u in plan.units:
        ref = u.source_ref
        dims = list(u.dimensions_um) if u.dimensions_um is not None else [u.length_mm * 1000, u.width_mm * 1000, u.height_mm * 1000]
        status = 'PLACED' if u.id in placed else 'EXCLUDED' if u.requirement == 'excluded' else 'UNPLACED'
        p = placed.get(u.id)
        cells = dims[0] * dims[1] * dims[2]
        volume['manifest'] += cells
        if p is not None:
            volume['placed'] += cells
        units.append({
            'id': u.id, 'name': u.name, 'kind': u.kind, 'requirement': u.requirement,
            'group_id': ref.group_id if ref else None, 'source_row': ref.source_row if ref else None,
            'revision_id': getattr(ref, 'revision_id', None), 'confirmation': getattr(ref, 'confirmation', None),
            'dimension_warning': bool(ref.dimension_warning) if ref else False,
            'length_mm': u.length_mm, 'width_mm': u.width_mm, 'height_mm': u.height_mm, 'dimensions_um': dims,
            'mass_g': u.mass_g, 'status': status,
            'placement': None if p is None else {'x_mm': p.x_mm, 'y_mm': p.y_mm, 'z_mm': p.z_mm, 'layer': p.layer, 'yaw_deg': p.yaw_deg},
            'packing': _packing(u, ref, groups, bundles)})
        if multi and p is not None:
            units[-1]['placement']['supported_by'] = list(p.supported_by)
        mass[0] += u.mass_g
        if p is not None:
            mass[1] += u.mass_g
        else:
            code = 'EXCLUDED' if u.requirement == 'excluded' else 'REQUIRED_UNPLACED' if u.requirement == 'required' else 'OPTIONAL_UNPLACED'
            unplaced.append({'id': u.id, 'name': u.name, 'status': status, 'requirement': u.requirement, 'mass_g': u.mass_g,
                             'dimensions_um': dims, 'reason_code': code, 'reason': REASONS[code]})
    count = {s: sum(1 for x in units if x['status'] == s) for s in ('PLACED', 'UNPLACED', 'EXCLUDED')}
    limits = plan.limits
    available = limits.voyage_cargo_limit_g - limits.cargo_onboard_g
    field = profile['profile']['provenance']['field_status']['hold'] if profile else 'UNCONFIRMED'
    hold = plan.hold
    cargo_revision = plan.cargo_revision
    report = {
        'schema_version': SCHEMA,
        'report_sha256': '',
        'header': {'plan_name': name, 'snapshot_id': snapshot_id, 'saved_utc': saved_utc, 'schema_version': SAVED_SCHEMA,
                   'contract_version': plan.contract_version, 'plan_sha256': hashlib.sha256(plan_json.encode('utf-8')).hexdigest(),
                   'generated_utc': generated_utc},
        'vessel': _vessel(plan, profile),
        'hold': {'id': hold.id, 'name': hold.name, 'length_mm': hold.length_mm, 'width_mm': hold.width_mm,
                 'height_mm': hold.height_mm, 'status': field},
        'limits': {'certificate_cargo_limit_g': limits.certificate_cargo_limit_g, 'voyage_cargo_limit_g': limits.voyage_cargo_limit_g,
                   'cargo_onboard_g': limits.cargo_onboard_g, 'available_capacity_g': available},
        'cargo': {'plan_source': plan.source, 'cargo_source': plan.cargo_source, 'dataset_id': plan.cargo_dataset,
                  'revision_id': revision['revision_id'] if revision else None,
                  'content_sha256': revision['content_sha256'] if revision else None,
                  'recheck': {k: recheck[k] for k in ('status', 'latest_revision_id', 'added', 'removed', 'changed', 'placed_affected')}},
        'totals': {'unit_count': len(units), 'placed_count': count['PLACED'], 'unplaced_count': count['UNPLACED'],
                   'excluded_count': count['EXCLUDED'], 'manifest_mass_g': mass[0], 'placed_mass_g': mass[1],
                   'remaining_capacity_g': available - mass[1],
                   'manifest_envelope_volume_mm3': _volume(volume['manifest']), 'placed_envelope_volume_mm3': _volume(volume['placed']),
                   'manifest_envelope_volume_mm3_text': mm3_text(volume['manifest']),
                   'placed_envelope_volume_mm3_text': mm3_text(volume['placed'])},
        'units': units,
        'unplaced': unplaced,
        'issues': {'status': evaluation.status, 'basic_checks_passed': evaluation.basic_checks_passed,
                   'total_issues': evaluation.total_issues if evaluation.total_issues is not None else len(evaluation.issues),
                   'issues_truncated': bool(evaluation.issues_truncated),
                   'items': [{'code': i.code, 'unit_ids': list(i.unit_ids), 'message': i.message} for i in evaluation.issues],
                   'unchecked': list(evaluation.unchecked), 'operational_eligible': False},
        'notices': None,
    }
    if multi:
        report['stacking'] = 'COLUMNS_V1'
        report['totals']['layer_count'] = max((p.layer for p in plan.placements), default=-1) + 1
        report['totals']['column_count'] = sum(1 for p in plan.placements if p.z_mm == 0)
    report['notices'] = _notices(field, report['cargo']['recheck'], units, evaluation.unchecked, multi)
    report['report_sha256'] = report_hash(report)
    return report


def reconcile(report: dict, evaluation) -> None:
    """D1.5 internal reconciliation; raises ReportReconciliationError describing the first mismatch."""
    t, s = report['totals'], evaluation.summary
    units = report['units']

    def fail(what):
        raise ReportReconciliationError(what)

    by_status = {x: sum(1 for u in units if u['status'] == x) for x in ('PLACED', 'UNPLACED', 'EXCLUDED')}
    if len(units) != t['unit_count']:
        fail(f'số dòng hàng {len(units)} khác tổng số đơn vị {t["unit_count"]}')
    if t['placed_count'] + t['unplaced_count'] + t['excluded_count'] != t['unit_count']:
        fail(f'đã xếp {t["placed_count"]} + chưa xếp {t["unplaced_count"]} + loại trừ {t["excluded_count"]} khác tổng số đơn vị {t["unit_count"]}')
    if (t['placed_count'], t['unplaced_count'], t['excluded_count']) != (by_status['PLACED'], by_status['UNPLACED'], by_status['EXCLUDED']):
        fail('số đơn vị theo trạng thái khác các dòng hàng')
    placed_mass = sum(u['mass_g'] for u in units if u['status'] == 'PLACED')
    if t['placed_mass_g'] != placed_mass:
        fail(f'khối lượng đã xếp {t["placed_mass_g"]} g khác tổng khối lượng các đơn vị đã xếp {placed_mass} g')
    if t['manifest_mass_g'] != sum(u['mass_g'] for u in units):
        fail('khối lượng manifest khác tổng khối lượng các đơn vị')
    for label, got, want in (
            ('khối lượng manifest', t['manifest_mass_g'], s.manifest_mass_g), ('khối lượng đã xếp', t['placed_mass_g'], s.placed_mass_g),
            ('sức chứa còn lại', t['remaining_capacity_g'], s.remaining_capacity_g), ('số bó đã xếp', t['placed_count'], s.placed_count),
            ('số bó chưa xếp', t['unplaced_count'], len(s.unplaced_ids)), ('số bó loại trừ', t['excluded_count'], len(s.excluded_ids))):
        if got != want:
            fail(f'{label} {got} khác kết quả kiểm {want}')
    if sorted(u['id'] for u in report['unplaced']) != sorted([*s.unplaced_ids, *s.excluded_ids]):
        fail('danh sách chưa xếp khác kết quả kiểm')
    expected = {'status': evaluation.status, 'basic_checks_passed': evaluation.basic_checks_passed, 'operational_eligible': False,
                'total_issues': evaluation.total_issues if evaluation.total_issues is not None else len(evaluation.issues),
                'issues_truncated': bool(evaluation.issues_truncated), 'unchecked': list(evaluation.unchecked),
                'items': [{'code': i.code, 'unit_ids': list(i.unit_ids), 'message': i.message} for i in evaluation.issues]}
    for key, want in expected.items():
        if report['issues'][key] != want:
            fail(f'mục kiểm "{key}" khác kết quả kiểm')
    if report.get('stacking') == 'COLUMNS_V1':
        layers = [u['placement']['layer'] for u in units if u['placement'] is not None]
        if t['layer_count'] != max(layers, default=-1) + 1:
            fail(f'tổng số tầng {t["layer_count"]} khác tầng cao nhất của các bó đã xếp')
    if report['report_sha256'] != report_hash(report):
        fail('report_sha256 không khớp nội dung báo cáo')
