"""Shared service binding plans to cargo-data revisions (SUP-02A D5/D6).

Every entry point that receives a Plan calls bind(); legacy contracts never open the database here. The pure replay
and derivation rules live in domain.cargo_revisions; the append-only rows in adapters.revision_store.
Nothing in this module writes to snapshots; the only write is revision creation through revision_store.append.
"""
import copy
import hashlib
import json
import sqlite3
import threading
from collections import OrderedDict
from datetime import datetime, timezone

from ..domain import cargo_revisions as cr
from ..domain.comparison import compare
from ..domain.model import Plan
from ..domain.rules import evaluate
from . import revision_store
from .pipe_registry import REGISTRY

DATASET = cr.DATASET
BASE = cr.BASE_REVISION_ID
V1, V2 = 'scst.pipe-list.v1', 'scst.pipe-list.v2'


class PlanBindingError(ValueError):
    """Plan or revision reference cannot be served; message is Vietnamese."""


class RevisionUnavailable(PlanBindingError):
    """Stored revisions fail replay/integrity (or cannot be read); never auto-repaired."""

    def __init__(self, revision_id, message):
        super().__init__(message)
        self.revision_id = revision_id


# ------------------------------------------------------------------ reading revisions
# H3 replay cache: in-process LRU of replay results keyed by SHA-256 of the raw DB rows of the replayed prefix. Every
# request still reads the rows; replay is skipped only on an exact match, so any edit (also a manual one) misses and
# is replayed and integrity-checked as before. The key covers ALL selected columns, not only revision_id/source/
# changes/content_sha256: created_utc and parent_revision_id also reach the served view and must not be masked.
_CACHE_MAX = 8
_REPLAY_CACHE = OrderedDict()  # key -> ('ok', views) | ('err', revision_id, message); the cached views are never handed out
_CACHE_LOCK = threading.Lock()


def clear_replay_cache():
    with _CACHE_LOCK:
        _REPLAY_CACHE.clear()


def _replay(rows, records, pick=None, share=False):
    """cr.replay(REGISTRY, records) memoised on `rows` (the raw rows `records` were decoded from, same order).
    Returns a private deep copy (callers may mutate) of all views, or only of views[pick]; share=True returns the cached
    list itself for strictly read-only callers. Re-raises a cached RevisionIntegrityError."""
    key = hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(',', ':'), default=repr).encode()).hexdigest()
    with _CACHE_LOCK:
        hit = _REPLAY_CACHE.get(key)
        if hit is not None:
            _REPLAY_CACHE.move_to_end(key)
    if hit is None:
        try:
            hit = ('ok', cr.replay(REGISTRY, records))
        except cr.RevisionIntegrityError as exc:
            hit = ('err', exc.revision_id, exc.message)
        with _CACHE_LOCK:
            _REPLAY_CACHE[key] = hit
            _REPLAY_CACHE.move_to_end(key)
            while len(_REPLAY_CACHE) > _CACHE_MAX:
                _REPLAY_CACHE.popitem(last=False)
    if hit[0] == 'err':
        raise cr.RevisionIntegrityError(hit[1], hit[2])
    return hit[1] if share else copy.deepcopy(hit[1] if pick is None else hit[1][pick])


class _Records(list):
    """Decoded records plus the raw rows they came from (`rows[:n]` is the cache key material of `self[:n]`)."""
    rows = ()


def _records():
    try:
        rows = revision_store.read_rows(DATASET)
        records = _Records(revision_store.decode_rows(rows))
        records.rows = rows
        return records
    except (sqlite3.Error, OSError, ValueError, TypeError) as exc:
        raise RevisionUnavailable(None, f'Không đọc được dữ liệu revision hàng: {exc}') from exc


def latest_id(records):
    return records[-1]['revision_id'] if records else BASE


def _view_from(records, seq):
    """View of revision `seq` replaying only records[:seq] (a broken later record does not block it)."""
    if seq == 0:
        return _replay([], [], 0)
    if seq > len(records):
        raise LookupError(f'Không tìm thấy revision {cr.revision_id(seq)}.')
    try:
        return _replay(records.rows[:seq], records[:seq], seq)
    except cr.RevisionIntegrityError as exc:
        raise RevisionUnavailable(cr.revision_id(seq), exc.message) from exc


def view(revision_id):
    """Full view of one revision. LookupError if unknown; RevisionUnavailable if its replay fails integrity."""
    try:
        seq = cr.parse_sequence(revision_id)
    except ValueError:
        raise LookupError(f'Mã revision không hợp lệ: {revision_id!r}.')
    return _view_from([] if seq == 0 else _records(), seq)


def latest():
    records = _records()
    return _view_from(records, len(records))


def servable_views(share=False):
    """-> (records, views): views[k] is the view of Rk for every revision whose replay is intact (longest valid prefix).
    share=True hands out the cached views themselves: read-only use only."""
    records = _records()
    for n in range(len(records), -1, -1):
        try:
            return records, _replay(records.rows[:n], records[:n], share=share)
        except cr.RevisionIntegrityError:
            continue
    raise AssertionError('unreachable: R0000 always replays')


def unit_total_mass(groups):
    return sum(g['bundle_overrides'].get(b, {}).get('mass_g', g['mass_g']) for g in groups for b in g['bundle_ids'])


def summary_of_view(v):
    groups = v['groups']
    return {'revision_id': v['revision_id'], 'parent_revision_id': v['parent_revision_id'],
            'created_utc': v['created_utc'], 'source': v['source'], 'change_count': len(v['changes']),
            'content_sha256': v['content_sha256'], 'group_count': len(groups),
            'bundle_count': sum(len(g['bundle_ids']) for g in groups), 'total_mass_g': unit_total_mass(groups),
            'available': True, 'integrity_error': None}


def summary_of_record(rec, message):
    source = cr.normalize_source(rec.get('source'))[0]
    changes = rec.get('changes')
    return {'revision_id': rec['revision_id'], 'parent_revision_id': rec.get('parent_revision_id'),
            'created_utc': rec.get('created_utc'), 'source': source,
            'change_count': len(changes) if isinstance(changes, list) else 0,
            'content_sha256': rec.get('content_sha256') or '', 'group_count': None, 'bundle_count': None,
            'total_mass_g': None, 'available': False, 'integrity_error': message}


def list_revisions():
    """-> {dataset_id, latest_revision_id, revisions newest first incl. R0000}; unservable records are flagged."""
    records, views = servable_views(share=True)  # summary_of_view only reads
    items = [summary_of_view(v) for v in views]
    for rec in records[len(views) - 1:]:
        items.append(summary_of_record(rec, 'Revision này hoặc một revision trước đó không qua được kiểm phát lại; không phục vụ.'))
    items.reverse()
    return {'dataset_id': DATASET, 'latest_revision_id': latest_id(records), 'revisions': items}


def detail(v):
    prov, groups = v['provenance'], []
    for g in v['groups']:
        overrides = []
        for b in g['bundle_ids']:
            if b in g['bundle_overrides']:
                ov = g['bundle_overrides'][b]
                overrides.append({'bundle_id': b, 'mass_g': ov.get('mass_g'), 'dimensions_um': ov.get('dimensions_um'),
                                  'provenance': {f: s for f, s in prov['__bundles__'].get(b, {}).items() if f in cr.OVERRIDE_FIELDS}})
        groups.append({**{k: g[k] for k in ('group_id', 'source_row', 'origin', 'pieces_per_bundle', 'dimensions_um',
                                            'mass_g', 'outside_diameter_mm', 'wall_thickness_mm', 'dimension_warning',
                                            'source_line_t', 'source_cbm_m3', 'envelope_cbm_m3', 'issue_codes',
                                            'bundle_ids', 'next_bundle_index')},
                       'bundle_count': len(g['bundle_ids']), 'provenance': prov[g['group_id']], 'overrides': overrides})
    return {**summary_of_view(v), 'groups': groups, 'changes': v['changes']}


# ------------------------------------------------------------------ creating revisions
def preview_draft(parent_revision_id, source, changes):
    """Validate a draft against its parent revision without writing anything."""
    records = _records()
    latest = latest_id(records)
    out = {'valid': False, 'errors': [], 'latest_revision_id': latest, 'parent_is_latest': parent_revision_id == latest,
           'content_sha256': None, 'added_bundle_ids': [], 'removed_bundle_ids': [], 'changed_bundle_ids': [],
           'change_summaries': [], 'group_count': None, 'bundle_count': None, 'total_mass_g': None}
    try:
        parent = _view_from(records, cr.parse_sequence(parent_revision_id))
        next_id = cr.revision_id(cr.parse_sequence(parent_revision_id) + 1)
    except (LookupError, ValueError) as exc:
        if isinstance(exc, RevisionUnavailable):
            raise
        out['errors'] = [{'index': None, 'field': 'parent_revision_id',
                          'message': f'Không tìm thấy revision cha {parent_revision_id!r}.'}]
        return out
    errors = cr.validate_batch(parent['groups'], source, changes)
    if errors:
        out['errors'] = errors
        return out
    groups, _, effect = cr.apply_batch(parent['groups'], source, changes, next_id)
    out.update(valid=True, content_sha256=cr.content_sha256(groups), added_bundle_ids=effect['added_bundle_ids'],
               removed_bundle_ids=effect['removed_bundle_ids'], changed_bundle_ids=effect['changed_bundle_ids'],
               change_summaries=effect['summaries'], group_count=len(groups),
               bundle_count=sum(len(g['bundle_ids']) for g in groups), total_mass_g=unit_total_mass(groups))
    return out


def create_revision(parent_revision_id, source, changes):
    """Append R(n+1). Raises revision_store.ParentMismatch (nothing written), cr.BatchValidationError,
    RevisionUnavailable. The RAW source/changes are stored; replay re-validates them."""
    def build(records):
        try:
            views = cr.replay(REGISTRY, records)
        except cr.RevisionIntegrityError as exc:
            raise RevisionUnavailable(exc.revision_id, exc.message) from exc
        try:
            rid = cr.revision_id(len(records) + 1)
        except ValueError:
            raise cr.BatchValidationError([{'index': None, 'field': 'changes',
                                            'message': 'Đã đạt số lượng revision tối đa (9999).'}])
        groups, _, _ = cr.apply_batch(views[-1]['groups'], source, changes, rid)
        return {'revision_id': rid, 'sequence': len(records) + 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
                'source': source, 'changes': changes, 'content_sha256': cr.content_sha256(groups)}
    try:
        row = revision_store.append(DATASET, parent_revision_id, build)
    except (sqlite3.Error, OSError) as exc:
        raise RevisionUnavailable(None, f'Không ghi được revision hàng: {exc}') from exc
    return summary_of_view(view(row['revision_id']))


# ------------------------------------------------------------------ binding
def _ref_dict(v):
    return {'dataset_id': DATASET, 'revision_id': v['revision_id'], 'content_sha256': v['content_sha256']}


def bind(plan):
    """Return `plan` unchanged when it is consistent with its stored vessel profile and pinned revision.
    Legacy plans without a user vessel profile never touch the DB or the profile store."""
    from . import vessel_profile_service  # lazy: the service imports this module
    vessel_profile_service.check_reference(plan)
    if plan.contract_version != V2:
        return plan
    ref = plan.cargo_revision
    try:
        v = view(ref.revision_id)
    except LookupError:
        raise PlanBindingError(f'Revision dữ liệu hàng {ref.revision_id} không tồn tại.')
    if ref.content_sha256 != v['content_sha256']:
        raise PlanBindingError(f'Mã băm nội dung của phương án không khớp revision {ref.revision_id}.')
    actual = [u.model_dump(mode='json') for u in plan.units]
    expected = cr.derive_units(v)
    diff = cr.diff_units(expected, actual)
    if len(actual) != len(expected) or any(diff.values()):
        raise PlanBindingError(
            f'Danh sách bó của phương án không khớp revision {ref.revision_id}: '
            f'thiếu {len(diff["removed"])} bó, thừa {len(diff["added"])} bó, {len(diff["changed"])} bó khác dữ liệu.')
    return plan


def pinned_units(plan):
    if plan.contract_version == V1:
        return cr.derive_units(view(BASE))
    if plan.contract_version == V2:
        return cr.derive_units(view(plan.cargo_revision.revision_id))
    return None


class _Cache:
    """Per-call memo of derived units by revision id (an Exception value remembers a failure)."""

    def __init__(self):
        self.units, self.contract_hash = {}, {}

    def get(self, revision_id):
        if revision_id not in self.units:
            try:
                v = view(revision_id)
                self.units[revision_id], self.contract_hash[revision_id] = cr.derive_units(v), v['content_sha256']
            except (LookupError, PlanBindingError) as exc:
                self.units[revision_id] = exc
        if isinstance(self.units[revision_id], Exception):
            raise self.units[revision_id]
        return self.units[revision_id]


def _drop_reason(target_unit, pinned_unit):
    """Why rebase drops a placement of this unit (None = kept). The single rule shared by rebase and recheck (H2)."""
    if target_unit is None:
        return 'REMOVED'
    if (pinned_unit is None or target_unit['dimensions_um'] != pinned_unit['dimensions_um']
            or target_unit['mass_g'] != pinned_unit['mass_g']):
        return 'CHANGED'
    return None


def _dropped_count(pinned, target_units, placed_ids):
    pinned_by, target_by = {u['id']: u for u in pinned}, {u['id']: u for u in target_units}
    return sum(1 for uid in placed_ids if _drop_reason(target_by.get(uid), pinned_by.get(uid)))


def _recheck(contract_version, pinned_id, pinned_sha, placed_ids, latest_units, cache):
    if contract_version not in (V1, V2):
        return {'cargo_revision_id': None, 'status': 'NOT_APPLICABLE', 'added': 0, 'removed': 0, 'changed': 0,
                'placed_affected': 0, 'placed_dropped_on_rebase': 0}
    out = {'cargo_revision_id': pinned_id, 'status': 'REVISION_UNAVAILABLE', 'added': 0, 'removed': 0, 'changed': 0,
           'placed_affected': 0, 'placed_dropped_on_rebase': 0}
    if latest_units is None:
        return out
    try:
        pinned = cache.get(pinned_id)
    except (LookupError, PlanBindingError):
        return out
    if pinned_sha is not None and pinned_sha != cache.contract_hash[pinned_id]:
        return out
    diff = cr.diff_units(pinned, latest_units)
    affected = set(diff['removed']) | set(diff['changed'])
    out.update(status='NEEDS_RECHECK' if any(diff.values()) else 'CURRENT', added=len(diff['added']),
               removed=len(diff['removed']), changed=len(diff['changed']),
               placed_affected=len(affected & set(placed_ids)),
               placed_dropped_on_rebase=_dropped_count(pinned, latest_units, placed_ids))
    return out


def recheck(plan, latest_view):
    """Status of a Plan against `latest_view` (counts only; v1 is pinned to R0000)."""
    v2 = plan.contract_version == V2
    return _recheck(plan.contract_version, plan.cargo_revision.revision_id if v2 else BASE,
                    plan.cargo_revision.content_sha256 if v2 else None, [p.unit_id for p in plan.placements],
                    cr.derive_units(latest_view), _Cache())


def annotate_listing(rows):
    """rows = [(SavedSummary, plan_json)] -> list of dicts with SavedSummary fields + recheck fields (read-only)."""
    cache, state = _Cache(), {}

    def latest_units():
        if 'units' not in state:
            try:
                state['units'] = cr.derive_units(latest())
            except PlanBindingError:
                state['units'] = None
        return state['units']

    out = []
    for summary, plan_json in rows:
        item = summary.model_dump()
        try:
            data = json.loads(plan_json)
            cv = data.get('contract_version')
            placed = [p['unit_id'] for p in data.get('placements', [])]
            if cv == V2:
                ref = data['cargo_revision']
                pinned_id, sha = ref['revision_id'], ref['content_sha256']
            else:
                pinned_id, sha = BASE, None
        except (ValueError, KeyError, TypeError, AttributeError):
            cv, pinned_id, sha, placed = None, None, None, []
        status = _recheck(cv, pinned_id, sha, placed, latest_units() if cv in (V1, V2) else None, cache)
        out.append({**item, 'cargo_revision_id': status['cargo_revision_id'], 'recheck_status': status['status'],
                    'added_count': status['added'], 'removed_count': status['removed'],
                    'changed_count': status['changed'], 'placed_affected_count': status['placed_affected'],
                    'placed_dropped_on_rebase_count': status['placed_dropped_on_rebase']})
    return out


# ------------------------------------------------------------------ candidate plans
def candidate_plan(plan, target_view, placements):
    """Plan v2 pinned to target_view; requirement copied by unit id (new ids optional)."""
    requirement = {u.id: u.requirement for u in plan.units}
    units = [{**u, 'requirement': requirement.get(u['id'], 'optional')} for u in cr.derive_units(target_view)]
    data = plan.model_dump(mode='json')
    data.update(contract_version=V2, cargo_dataset=DATASET, cargo_source='DOCUMENT_CALCULATED',
                cargo_revision=_ref_dict(target_view), units=units, placements=placements)
    return Plan.model_validate(data)


def revision_plan_preview(plan, revision_id):
    """Candidate pinned to `revision_id`: all units optional, no placements."""
    return candidate_plan(plan.model_copy(update={'units': []}), view(revision_id), [])


def rebase(plan, target_view):
    """Candidate at target_view keeping placements of unchanged bundles; never writes."""
    pinned = pinned_units(plan)
    if pinned is None:
        raise PlanBindingError('Phương án không dùng list ống nên không thể tạo bản theo dữ liệu mới.')
    pinned_by = {u['id']: u for u in pinned}
    target_units = cr.derive_units(target_view)
    target_by = {u['id']: u for u in target_units}
    kept, dropped = [], []
    for p in plan.placements:
        t, o = target_by.get(p.unit_id), pinned_by.get(p.unit_id)
        reason = _drop_reason(t, o)
        if reason:
            dropped.append({'unit_id': p.unit_id, 'reason': reason, 'x_mm': p.x_mm, 'y_mm': p.y_mm, 'yaw_deg': p.yaw_deg})
        else:
            kept.append(p.model_dump(mode='json'))
    candidate = candidate_plan(plan, target_view, kept)
    diff = cr.diff_units(pinned, target_units)
    return {'source_revision_id': plan.cargo_revision.revision_id if plan.contract_version == V2 else BASE,
            'target_revision_id': target_view['revision_id'], 'candidate': evaluate(candidate),
            'kept_placement_count': len(kept), 'dropped_placements': dropped, 'added_unit_ids': diff['added'],
            'removed_unit_ids': diff['removed'], 'changed_unit_ids': diff['changed'],
            'comparison': compare(plan, candidate)}
