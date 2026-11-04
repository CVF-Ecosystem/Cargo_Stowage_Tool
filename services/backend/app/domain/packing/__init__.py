"""Pure derived pipe packing (SUP-03 D1-D3). No I/O, no env, no floats anywhere in the returned data.

Geometry is exact integer µm. Section origin = bottom-left corner; y runs across the width, z runs up the height.
A pipe centre (y, z) with outside diameter OD fits the W x H section when 2y-OD>=0, 2y+OD<=2W, 2z-OD>=0, 2z+OD<=2H
(doubled integers, so odd OD needs no rounding in the check). r = ceil(OD/2) is the first centre offset.
RECT: square grid, pitch OD, placed row by row bottom-up. HEX: row pitch floor(OD*sqrt(3)/2), odd rows shifted by
ceil(OD/2); because of integer rounding adjacent-row pipes may overlap by less than 1 µm (never checked or reported).
Reported columns/rows are the ones actually used: the widest placed row and the number of rows reached.
"""
import re
from math import isqrt

from ..cargo_revisions import DATASET

MAX_PIECES = 10_000
_MAX_REPORTED_FIT = 2 ** 53 - 1  # keep max_fit exactly representable by JS numbers
_DECIMAL = re.compile(r'[0-9]{1,6}(\.[0-9]{1,4})?')
_GUIDE = ' Kiểm lại OD, số ống mỗi bó hoặc kích thước bó trong revision.'
STATUSES = ('DETAILED', 'ENVELOPE_ONLY')


def mm_to_um(s):
    """Exact 'mm' decimal string -> int µm; None when invalid, <= 0 or not a whole number of µm. Never uses float."""
    if not isinstance(s, str):
        return None
    m = _DECIMAL.fullmatch(s)
    if not m:
        return None
    whole, _, frac = s.partition('.')
    tenth_um = int(whole) * 10_000 + int(frac.ljust(4, '0'))
    if tenth_um % 10 or tenth_um <= 0:
        return None
    return tenth_um // 10


def _mm_text(um):
    frac = f'{um % 1000:03d}'.rstrip('0')
    return f'{um // 1000}.{frac}' if frac else str(um // 1000)


def _is_int(v):
    return type(v) is int


def _reason(code, message):
    return {'code': code, 'message': message}


def _axis_count(length, od, start, step):
    """Pipes along one axis with first centre at `start` and spacing `step` that stay inside [0, length]."""
    room = 2 * length - 2 * start - od
    return 0 if room < 0 else room // (2 * step) + 1


def _capacities(w, h, od):
    r = (od + 1) // 2
    cols, rows = _axis_count(w, od, r, od), _axis_count(h, od, r, od)
    pitch = max(1, isqrt(3 * od * od) // 2)
    hex_rows = _axis_count(h, od, r, pitch)
    shift = (od + 1) // 2
    n_even, n_odd = _axis_count(w, od, r, od), _axis_count(w, od, r + shift, od)
    return {'r': r, 'cols': cols, 'rows': rows, 'rect': cols * rows, 'pitch': pitch, 'hex_rows': hex_rows,
            'n_even': n_even, 'n_odd': n_odd, 'shift': shift,
            'hex': ((hex_rows + 1) // 2) * n_even + (hex_rows // 2) * n_odd}


def _place_rect(pieces, c):
    r, cols, od = c['r'], c['cols'], c['od']
    centres = []
    for k in range(pieces):
        i, j = divmod(k, cols)
        centres.append([r + j * od, r + i * od])
    return centres, min(cols, pieces), -(-pieces // cols)


def _place_hex(pieces, c):
    r, od, left, centres, widest, last = c['r'], c['od'], pieces, [], 0, -1
    for i in range(c['hex_rows']):
        if left == 0:
            break
        odd = i % 2 == 1
        n = min(c['n_odd'] if odd else c['n_even'], left)
        start, z = (r + c['shift'] if odd else r), r + i * c['pitch']
        centres.extend([start + j * od, z] for j in range(n))
        if n:
            widest, last = max(widest, n), i
        left -= n
    return centres, widest, last + 1


def _inside(centres, w, h, od):
    return all(2 * y - od >= 0 and 2 * y + od <= 2 * w and 2 * z - od >= 0 and 2 * z + od <= 2 * h for y, z in centres)


def _valid_dims(d):
    return isinstance(d, (list, tuple)) and len(d) == 3 and all(_is_int(x) and x > 0 for x in d)


def pack_section(pieces, od_mm, wall_mm, dimensions_um, source_warning):
    """Pack one cross-section -> PackingCore dict (no ids). Total function: invalid input yields ENVELOPE_ONLY."""
    dims_ok = _valid_dims(dimensions_um)
    pieces_ok = _is_int(pieces) and 1 <= pieces <= MAX_PIECES
    raw = list(dimensions_um) if isinstance(dimensions_um, (list, tuple)) and len(dimensions_um) == 3 else [0, 0, 0]
    length, w, h = [x if _is_int(x) and x > 0 else 0 for x in raw]
    od = mm_to_um(od_mm)
    out = {'status': 'ENVELOPE_ONLY', 'basis': 'DERIVED', 'layout': None, 'columns': 0, 'rows': 0, 'od_um': od,
           'wall_thickness_um': mm_to_um(wall_mm), 'length_um': length, 'section_um': [w, h],
           'pieces_source': pieces if _is_int(pieces) and pieces > 0 else 0, 'pieces_placed': 0, 'max_fit': 0,
           'pipe_centres_um': [], 'slack_um': None,
           'checks': {'count': False, 'od_fit': False, 'envelope_fit': False, 'slack_loose': False}, 'reasons': []}
    reasons = out['reasons']
    if not (dims_ok and pieces_ok):
        reasons.append(_reason('INPUT_INVALID', 'Số ống mỗi bó phải là số nguyên từ 1 đến 10000 và kích thước bó phải gồm '
                               '3 số nguyên dương (µm); chưa thể xếp ống chi tiết, hiển thị khối bao.' + _GUIDE))
    if od is None:
        reasons.append(_reason('OD_MISSING', 'Thiếu hoặc không hợp lệ đường kính ngoài (OD) của ống nên không thể xếp '
                               'ống chi tiết; hiển thị khối bao.' + _GUIDE))
    if dims_ok and pieces_ok and od is not None:
        out['checks']['od_fit'] = od <= w and od <= h
        if not out['checks']['od_fit']:
            reasons.append(_reason('OD_EXCEEDS_SECTION', f'OD {_mm_text(od)} mm lớn hơn mặt cắt bó {_mm_text(w)} × '
                                   f'{_mm_text(h)} mm nên không xếp được ống; hiển thị khối bao.' + _GUIDE))
        else:
            c = _capacities(w, h, od)
            c['od'] = od
            out['max_fit'] = min(max(c['rect'], c['hex']), _MAX_REPORTED_FIT)
            if c['rect'] >= pieces:
                layout, (centres, cols, rows) = 'RECT', _place_rect(pieces, c)
            elif c['hex'] >= pieces:
                layout, (centres, cols, rows) = 'HEX', _place_hex(pieces, c)
            else:
                layout = None
                reasons.append(_reason('PIECES_DO_NOT_FIT', f'Không xếp vừa {pieces} ống OD {_mm_text(od)} mm vào mặt cắt '
                                       f'{_mm_text(w)} × {_mm_text(h)} mm; tối đa xếp được {out["max_fit"]} ống; '
                                       'hiển thị khối bao.' + _GUIDE))
            if layout:
                fits = _inside(centres, w, h, od)
                counted = len(centres) == pieces
                out['checks'].update(count=counted, envelope_fit=fits)
                if counted and fits:
                    ext_w = max((2 * y + od + 1) // 2 for y, _ in centres)
                    ext_h = max((2 * z + od + 1) // 2 for _, z in centres)
                    slack = [w - ext_w, h - ext_h]
                    loose = slack[0] >= od or slack[1] >= od
                    out.update(status='DETAILED', layout=layout, columns=cols, rows=rows, pieces_placed=len(centres),
                               pipe_centres_um=centres, slack_um=slack)
                    out['checks']['slack_loose'] = loose
                    if loose:
                        reasons.append(_reason('ENVELOPE_LOOSE', f'Khối bao rộng hơn cách xếp: dư {_mm_text(slack[0])} mm '
                                               f'theo chiều rộng và {_mm_text(slack[1])} mm theo chiều cao (thông tin).'))
                else:  # defensive: construction must never get here
                    reasons.append(_reason('PIECES_DO_NOT_FIT', 'Cách xếp dẫn xuất không qua được kiểm tra khối bao; '
                                           'hiển thị khối bao.' + _GUIDE))
    if source_warning:
        reasons.append(_reason('SOURCE_WARNING', 'Dữ liệu nguồn của nhóm có cảnh báo kích thước hoặc mã vấn đề; cách xếp '
                               'chỉ để tham khảo cho đến khi dữ liệu được xác nhận.'))
    return out


def _group_core(group, dims):
    warn = bool(group.get('dimension_warning')) or bool(group.get('issue_codes'))
    return pack_section(group.get('pieces_per_bundle'), group.get('outside_diameter_mm'),
                        group.get('wall_thickness_mm'), dims, warn)


def pack_group(group):
    """-> GroupPacking. Bundles whose override has dimensions_um get their own BundlePacking; others inherit the group."""
    core = _group_core(group, group.get('dimensions_um'))
    ids = list(group.get('bundle_ids') or [])
    overrides = group.get('bundle_overrides') or {}
    bundles = []
    for b in ids:
        ov = overrides.get(b)
        if isinstance(ov, dict) and 'dimensions_um' in ov:
            bundles.append({**_group_core(group, ov['dimensions_um']), 'bundle_id': b})
    return {**core, 'group_id': group.get('group_id'), 'bundle_count': len(ids), 'bundle_packings': bundles}


def pack_revision(view):
    """-> RevisionPacking for a cargo revision view (revision_id, content_sha256, groups). Input is not mutated."""
    groups = [pack_group(g) for g in view['groups']]
    gstat, bstat = dict.fromkeys(STATUSES, 0), dict.fromkeys(STATUSES, 0)
    bundle_count = derived = source = 0
    for gp in groups:
        gstat[gp['status']] += 1
        own = gp['bundle_packings']  # every bundle id is either an override packing or inherits the group
        n = gp['bundle_count']
        bundle_count += n
        for b in own:
            bstat[b['status']] += 1
            derived += b['pieces_placed']
            source += b['pieces_source']
        inherit = n - len(own)
        bstat[gp['status']] += inherit
        derived += inherit * gp['pieces_placed']
        source += inherit * gp['pieces_source']
    return {'dataset_id': DATASET, 'revision_id': view['revision_id'], 'content_sha256': view['content_sha256'],
            'basis': 'DERIVED', 'groups': groups,
            'stats': {'group_count': len(groups), 'groups_by_status': gstat, 'bundle_count': bundle_count,
                      'bundles_by_status': bstat, 'derived_pieces': derived, 'source_pieces': source}}
