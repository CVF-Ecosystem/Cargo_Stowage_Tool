"""Pure cargo-data revision domain (SUP-02A D1-D4). No sqlite, no env, no file I/O.

A revision is the full list of group states after applying an ordered change batch to its parent. R0000 is derived
from the registry; later revisions are replayed from stored change records and checked against stored hashes.
Error dicts are {index:int|None, field:str, message:str(vi)}; field is a dotted path ('set.mass_g',
'set.dimensions_um.1', 'group.bundle_count'); index None means batch-level (source.*, changes, payload).
"""
import copy
import hashlib
import json
import re
from datetime import date

from ...adapters.pipe_registry import REGISTRY

DATASET = 'BALTIMORE-PIPE-V1-1'
BASE_REVISION_ID = DATASET + '@R0000'
MAX_PAYLOAD_BYTES = 1_048_576
MAX_CHANGES = 500
MAX_GROUPS = 200
MAX_TOTAL_BUNDLES = 2000
MAX_GROUP_BUNDLES = 2000
MAX_PIECES = 10_000
MAX_DIMENSION_UM = 10 ** 9
MAX_MASS_G = 10 ** 12
GROUP_FIELDS = ('bundle_count', 'pieces_per_bundle', 'dimensions_um', 'mass_g',
                'outside_diameter_mm', 'wall_thickness_mm', 'dimension_warning')
OVERRIDE_FIELDS = ('mass_g', 'dimensions_um')
SOURCE_KINDS = ('USER', 'FACTORY', 'CUSTOMER', 'OTHER')
CONFIRMATIONS = ('UNVERIFIED', 'CONFIRMED')
_CHANGE_KEYS = {'UPDATE_GROUP': ('group_id', 'set'), 'ADD_GROUP': ('group',), 'BUNDLE_OVERRIDE': ('bundle_id', 'set')}
_DECIMAL = re.compile(r'^[0-9]{1,6}(\.[0-9]{1,4})?$')
_DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
_REVISION = re.compile('^' + re.escape(DATASET) + '@R([0-9]{4})$')


class RevisionIntegrityError(Exception):
    def __init__(self, revision_id, message):
        super().__init__(message)
        self.revision_id, self.message = revision_id, message


class BatchValidationError(ValueError):
    def __init__(self, errors):
        super().__init__('Lô cập nhật không hợp lệ: ' + '; '.join(e['message'] for e in errors[:3]))
        self.errors = errors


def revision_id(seq):
    if type(seq) is not int or not 0 <= seq <= 9999:
        raise ValueError('Số thứ tự revision phải từ 0 đến 9999.')
    return f'{DATASET}@R{seq:04d}'


def parse_sequence(rev):
    m = _REVISION.match(rev) if isinstance(rev, str) else None
    if not m:
        raise ValueError(f'Mã revision không hợp lệ: {rev!r}.')
    return int(m.group(1))


def content_sha256(groups):
    text = json.dumps(groups, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _prefix(g):
    return f"PIPE-R{g['source_row']:03d}" if g['source_row'] is not None else f"PIPE-A{int(g['group_id'][4:]):03d}"


def base_groups(registry):
    out = []
    for r in registry['groups']:
        g = {k: copy.deepcopy(r[k]) for k in GROUP_FIELDS if k != 'bundle_count'}
        g.update(group_id=r['group_id'], source_row=r['source_row'], bundle_count=r['bundle_count'],
                 source_line_t=r['source_line_t'], source_cbm_m3=r['source_cbm_m3'], envelope_cbm_m3=r['envelope_cbm_m3'],
                 issue_codes=list(r['issue_codes']), origin='WORKBOOK', next_bundle_index=r['bundle_count'] + 1,
                 bundle_overrides={})
        g['bundle_ids'] = [f"{_prefix(g)}-B{i:04d}" for i in range(1, r['bundle_count'] + 1)]
        out.append(g)
    return out


def _stamp(rev, source, confirmation):
    return {'revision_id': rev, 'source': copy.deepcopy(source), 'confirmation': confirmation}


def base_provenance(groups):
    prov = {g['group_id']: {f: _stamp(BASE_REVISION_ID, None, 'WORKBOOK') for f in GROUP_FIELDS} for g in groups}
    prov['__bundles__'] = {}
    return prov


def apply_provenance(prov, delta, groups):
    """New provenance = prov + delta; bundle entries of bundles no longer active are dropped."""
    out = copy.deepcopy(prov)
    for key, fields in delta.items():
        if key == '__bundles__':
            for bid, bf in fields.items():
                out['__bundles__'].setdefault(bid, {}).update(copy.deepcopy(bf))
        else:
            out.setdefault(key, {}).update(copy.deepcopy(fields))
    active = {b for g in groups for b in g['bundle_ids']}
    out['__bundles__'] = {b: v for b, v in out['__bundles__'].items() if b in active}
    return out


# ---------------------------------------------------------------- validation of single values
def _int_error(label, v, lo, hi):
    if type(v) is not int:
        return f'{label} phải là số nguyên (không nhận số thực hoặc true/false).'
    if not lo <= v <= hi:
        return f'{label} phải nằm trong khoảng {lo} đến {hi}.'


def _field_errors(field, v, min_bundles=0):
    """-> list of (suffix, message) for one group/override field value."""
    if field == 'bundle_count':
        m = _int_error('Số bó của nhóm', v, min_bundles, MAX_GROUP_BUNDLES)
    elif field == 'pieces_per_bundle':
        m = _int_error('Số ống mỗi bó', v, 1, MAX_PIECES)
    elif field == 'mass_g':
        m = _int_error('Khối lượng bó (g)', v, 1, MAX_MASS_G)
    elif field == 'dimensions_um':
        if not isinstance(v, (list, tuple)) or len(v) != 3:
            return [('', 'Kích thước phải gồm đúng 3 số nguyên [dài, rộng, cao] tính bằng µm.')]
        return [(f'.{i}', e) for i, x in enumerate(v) if (e := _int_error('Kích thước (µm)', x, 1, MAX_DIMENSION_UM))]
    elif field in ('outside_diameter_mm', 'wall_thickness_mm'):
        label = 'Đường kính ngoài (mm)' if field == 'outside_diameter_mm' else 'Độ dày thành (mm)'
        ok = isinstance(v, str) and _DECIMAL.match(v) and float(v) > 0
        m = None if ok else f'{label} phải là chuỗi số thập phân dương (tối đa 6 chữ số nguyên, 4 chữ số thập phân).'
    else:  # dimension_warning
        m = None if type(v) is bool else 'Cờ cảnh báo kích thước phải là true hoặc false.'
    return [('', m)] if m else []


def check_payload_size(size):
    if size > MAX_PAYLOAD_BYTES:
        return [{'index': None, 'field': 'payload', 'message': f'Dữ liệu gửi lên vượt quá {MAX_PAYLOAD_BYTES} byte (1 MiB).'}]
    return []


def normalize_source(source):
    """-> (normalized source dict | None, errors)."""
    errs = []

    def e(field, msg):
        errs.append({'index': None, 'field': f'source.{field}' if field else 'source', 'message': msg})
    if not isinstance(source, dict):
        e('', 'Nguồn dữ liệu phải là một đối tượng.')
        return None, errs
    for k in source:
        if k not in ('kind', 'reference', 'received_date', 'note'):
            e(k, 'Trường không được hỗ trợ.')
    kind, ref, day, note = source.get('kind'), source.get('reference'), source.get('received_date'), source.get('note', '')
    if not isinstance(kind, str) or kind not in SOURCE_KINDS:
        e('kind', 'Loại nguồn phải là một trong: ' + ', '.join(SOURCE_KINDS) + '.')
    ref = ref.strip() if isinstance(ref, str) else None
    if ref is None or not 1 <= len(ref) <= 200:
        e('reference', 'Tham chiếu nguồn phải có từ 1 đến 200 ký tự (không chỉ gồm khoảng trắng).')
    valid_day = False
    if isinstance(day, str) and _DATE.match(day):
        try:
            date.fromisoformat(day)
            valid_day = True
        except ValueError:
            pass
    if not valid_day:
        e('received_date', 'Ngày nhận phải là ngày hợp lệ theo dạng YYYY-MM-DD.')
    if not isinstance(note, str) or len(note) > 500:
        e('note', 'Ghi chú phải là chuỗi tối đa 500 ký tự.')
    if errs:
        return None, errs
    return {'kind': kind, 'reference': ref, 'received_date': day, 'note': note}, []


# ---------------------------------------------------------------- batch engine
def _values(groups):
    out = {}
    for g in groups:
        for b in g['bundle_ids']:
            ov = g['bundle_overrides'].get(b, {})
            out[b] = (ov.get('mass_g', g['mass_g']), tuple(ov.get('dimensions_um', g['dimensions_um'])),
                      g['pieces_per_bundle'], g['dimension_warning'])
    return out


def _run(groups, source, changes, rev):
    """Validate and apply together on a private copy. -> (errors, new_groups, provenance_delta, effect)."""
    errs = []

    def e(index, field, msg):
        errs.append({'index': index, 'field': field, 'message': msg})
    norm, src_errs = normalize_source(source)
    errs += src_errs
    if not isinstance(changes, list):
        e(None, 'changes', 'Danh sách thay đổi phải là một mảng.')
        return errs, None, None, None
    if not changes:
        e(None, 'changes', 'Lô cập nhật phải có ít nhất 1 thay đổi.')
        return errs, None, None, None
    if len(changes) > MAX_CHANGES:
        e(None, 'changes', f'Lô cập nhật có tối đa {MAX_CHANGES} thay đổi (nhận {len(changes)}).')
        return errs, None, None, None

    new = copy.deepcopy(groups)
    by_id = {g['group_id']: g for g in new}
    owner = {b: g for g in new for b in g['bundle_ids']}
    delta = {'__bundles__': {}}
    summaries = []

    def resize(g, n, stamp, created):
        ids = g['bundle_ids']
        if n < len(ids):
            for b in ids[n:]:
                owner.pop(b)
                g['bundle_overrides'].pop(b, None)
            del ids[n:]
        while len(ids) < n:
            b = f"{_prefix(g)}-B{g['next_bundle_index']:04d}"
            g['next_bundle_index'] += 1
            ids.append(b)
            owner[b] = g
            if created:
                delta['__bundles__'].setdefault(b, {})['created'] = stamp
        g['bundle_count'] = n

    def fields_ok(i, data, label, allowed, min_bundles=0, require_all=False):
        if not isinstance(data, dict):
            e(i, label, 'Phải là một đối tượng.')
            return
        if not data:
            e(i, label, 'Phải có ít nhất một trường cần thay đổi.')
        for k, v in data.items():
            if k not in allowed:
                e(i, f'{label}.{k}', 'Trường không được hỗ trợ.')
            else:
                for suffix, msg in _field_errors(k, v, min_bundles):
                    e(i, f'{label}.{k}{suffix}', msg)
        if require_all:
            for k in allowed:
                if k not in data:
                    e(i, f'{label}.{k}', 'Thiếu trường bắt buộc.')

    for i, ch in enumerate(changes):
        before = len(errs)
        if not isinstance(ch, dict):
            e(i, 'change', 'Mỗi thay đổi phải là một đối tượng.')
            continue
        kind = ch.get('type')
        if not isinstance(kind, str) or kind not in _CHANGE_KEYS:
            e(i, 'type', 'Loại thay đổi phải là UPDATE_GROUP, ADD_GROUP hoặc BUNDLE_OVERRIDE.')
            continue
        for k in ch:
            if k not in ('type', 'confirmation') + _CHANGE_KEYS[kind]:
                e(i, k, 'Trường không được hỗ trợ.')
        conf = ch.get('confirmation')
        if not isinstance(conf, str) or conf not in CONFIRMATIONS:
            e(i, 'confirmation', 'Trạng thái xác nhận phải là UNVERIFIED hoặc CONFIRMED.')
        for k in _CHANGE_KEYS[kind]:
            if k not in ch:
                e(i, k, 'Thiếu trường bắt buộc.')
        if len(errs) > before:
            continue
        stamp = _stamp(rev, norm, conf) if norm else None
        if kind == 'ADD_GROUP':
            fields_ok(i, ch['group'], 'group', GROUP_FIELDS, 1, True)
            if len(errs) > before:
                continue
            s = ch['group']
            n = sum(1 for g in new if g['origin'] == 'ADDED') + 1
            g = {'group_id': f'ADD-{n:03d}', 'source_row': None, 'bundle_count': 0, 'source_line_t': None,
                 'source_cbm_m3': None, 'envelope_cbm_m3': None, 'issue_codes': [], 'origin': 'ADDED',
                 'bundle_ids': [], 'next_bundle_index': 1, 'bundle_overrides': {}}
            for f in GROUP_FIELDS:
                if f != 'bundle_count':
                    g[f] = list(s[f]) if f == 'dimensions_um' else s[f]
            new.append(g)
            by_id[g['group_id']] = g
            resize(g, s['bundle_count'], stamp, False)
            delta[g['group_id']] = {f: copy.deepcopy(stamp) for f in GROUP_FIELDS}
            summaries.append({'index': i, 'type': kind, 'target': g['group_id'],
                              'text': f"Thêm nhóm {g['group_id']} ({s['bundle_count']} bó)."})
            continue
        gid = ch.get('group_id')
        g = by_id.get(gid) if isinstance(gid, str) else None
        if kind == 'UPDATE_GROUP':
            if g is None:
                e(i, 'group_id', f'Không tìm thấy nhóm {gid!r}.')
            fields_ok(i, ch['set'], 'set', GROUP_FIELDS)
            s = ch['set']
            if (g is not None and isinstance(s, dict) and s.get('dimension_warning') is False
                    and g['dimension_warning'] and conf != 'CONFIRMED'):
                e(i, 'set.dimension_warning', 'Chỉ được tắt cảnh báo kích thước khi thay đổi được xác nhận (CONFIRMED).')
            if len(errs) > before:
                continue
            for f, v in s.items():
                if f == 'bundle_count':
                    resize(g, v, stamp, True)
                else:
                    g[f] = list(v) if f == 'dimensions_um' else v
            delta.setdefault(gid, {}).update({f: copy.deepcopy(stamp) for f in s})
            summaries.append({'index': i, 'type': kind, 'target': gid,
                              'text': f"Sửa nhóm {gid}: {', '.join(s)}."})
        else:  # BUNDLE_OVERRIDE
            bid = ch.get('bundle_id')
            g = owner.get(bid) if isinstance(bid, str) else None
            if g is None:
                e(i, 'bundle_id', f'Không tìm thấy bó {bid!r} (không tồn tại hoặc đã bị bỏ).')
            fields_ok(i, ch['set'], 'set', OVERRIDE_FIELDS)
            if len(errs) > before:
                continue
            s = ch['set']
            ov = g['bundle_overrides'].setdefault(bid, {})
            bp = delta['__bundles__'].setdefault(bid, {})
            for f, v in s.items():
                ov[f] = list(v) if f == 'dimensions_um' else v
                bp[f] = copy.deepcopy(stamp)
            summaries.append({'index': i, 'type': kind, 'target': bid,
                              'text': f"Ghi đè bó {bid}: {', '.join(s)}."})
    if not errs:
        if len(new) > MAX_GROUPS:
            e(None, 'changes', f'Sau lô cập nhật có {len(new)} nhóm, vượt giới hạn {MAX_GROUPS} nhóm.')
        total = len(owner)
        if total > MAX_TOTAL_BUNDLES:
            e(None, 'changes', f'Sau lô cập nhật có {total} bó, vượt giới hạn {MAX_TOTAL_BUNDLES} bó toàn dataset.')
    if errs:
        return errs, None, None, None
    old_v, new_v = _values(groups), _values(new)
    effect = {'added_bundle_ids': [b for b in new_v if b not in old_v],
              'removed_bundle_ids': [b for b in old_v if b not in new_v],
              'changed_bundle_ids': [b for b in new_v if b in old_v and new_v[b] != old_v[b]],
              'summaries': summaries}
    return [], new, delta, effect


def validate_batch(groups, source, changes):
    return _run(groups, source, changes, None)[0]


def apply_batch(groups, source, changes, rev_id):
    """-> (new_groups, provenance_delta, effect); raises BatchValidationError (a ValueError) if invalid."""
    parse_sequence(rev_id)
    errs, new, delta, effect = _run(groups, source, changes, rev_id)
    if errs:
        raise BatchValidationError(errs)
    return new, delta, effect


# ---------------------------------------------------------------- replay and derivation
def _view(rev, parent, created, source, changes, groups, prov, sha=None):
    return {'revision_id': rev, 'parent_revision_id': parent, 'created_utc': created, 'source': source,
            'changes': changes, 'content_sha256': sha or content_sha256(groups), 'groups': groups, 'provenance': prov}


def replay(registry, records):
    groups = base_groups(registry)
    prov = base_provenance(groups)
    views = [_view(BASE_REVISION_ID, None, None, None, [], groups, prov)]
    for n, rec in enumerate(records, 1):
        rid = revision_id(n)
        got = rec.get('revision_id') if isinstance(rec, dict) else None
        if got != rid or rec.get('parent_revision_id') != views[-1]['revision_id']:
            raise RevisionIntegrityError(str(got), f'Revision {got} không đúng thứ tự hoặc sai revision cha (mong đợi {rid}).')
        errs, new, delta, _ = _run(groups, rec.get('source'), rec.get('changes'), rid)
        if errs:
            raise RevisionIntegrityError(rid, f'Revision {rid} có danh sách thay đổi không hợp lệ khi phát lại: {errs[0]["message"]}')
        if content_sha256(new) != rec.get('content_sha256'):
            raise RevisionIntegrityError(rid, f'Revision {rid} có mã băm nội dung không khớp khi phát lại; không phục vụ revision này.')
        groups, prov = new, apply_provenance(prov, delta, new)
        views.append(_view(rid, views[-1]['revision_id'], rec.get('created_utc'), normalize_source(rec['source'])[0],
                           copy.deepcopy(rec['changes']), groups, prov, rec['content_sha256']))
    return views


def _unit_provenance(gp, bp, ov):
    feeds = [gp['pieces_per_bundle'], gp['dimension_warning'],
             bp['mass_g'] if 'mass_g' in ov else gp['mass_g'],
             bp['dimensions_um'] if 'dimensions_um' in ov else gp['dimensions_um']]
    if 'created' in bp:
        feeds.append(bp['created'])
    states = {f['confirmation'] for f in feeds}
    conf = 'UNVERIFIED' if 'UNVERIFIED' in states else 'CONFIRMED' if 'CONFIRMED' in states else 'WORKBOOK'
    return max((f['revision_id'] for f in feeds), key=parse_sequence), conf


def derive_units(view, registry=None):
    registry = registry or REGISTRY
    prov, units = view['provenance'], []
    for g in view['groups']:
        gp, bundles = prov[g['group_id']], prov['__bundles__']
        label = f"{g['source_row']:03d}" if g['source_row'] is not None else f"A{int(g['group_id'][4:]):03d}"
        for b in g['bundle_ids']:
            ov = g['bundle_overrides'].get(b, {})
            dims = list(ov.get('dimensions_um', g['dimensions_um']))
            rev, conf = _unit_provenance(gp, bundles.get(b, {}), ov)
            units.append({
                'id': b, 'name': f'Ống thép nhóm {label}', 'kind': 'PIPE_BUNDLE', 'requirement': 'optional',
                'length_mm': (dims[0] + 999) // 1000, 'width_mm': (dims[1] + 999) // 1000,
                'height_mm': (dims[2] + 999) // 1000, 'mass_g': ov.get('mass_g', g['mass_g']), 'dimensions_um': dims,
                'source_ref': {'dataset_id': DATASET, 'workbook_sha256': registry['workbook_sha256'],
                               'sheet': registry['sheet'], 'group_id': g['group_id'], 'source_row': g['source_row'],
                               'bundle_index': int(b.rsplit('-B', 1)[1]), 'pieces': g['pieces_per_bundle'],
                               'dimension_warning': g['dimension_warning'], 'revision_id': rev, 'confirmation': conf}})
    return units


def diff_units(old_units, new_units):
    old, new = {u['id']: u for u in old_units}, {u['id']: u for u in new_units}
    strip = lambda u: {k: v for k, v in u.items() if k != 'requirement'}
    return {'added': [i for i in new if i not in old], 'removed': [i for i in old if i not in new],
            'changed': [i for i in new if i in old and strip(new[i]) != strip(old[i])]}
