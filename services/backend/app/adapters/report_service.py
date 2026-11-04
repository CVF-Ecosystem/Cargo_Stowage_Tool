"""Plan report for one saved snapshot (M2d D1/D2). Strictly read-only: the only database access is a SELECT.

Loads the stored row, binds the plan (revision and vessel-profile integrity), evaluates it, rechecks against the latest
cargo revision, derives packing of the pinned revision, then builds and reconciles the pure report model.
"""
import json
from datetime import datetime, timezone
from uuid import UUID

from ..domain.model import Plan
from ..domain.packing import pack_revision
from ..domain.report import build_report, reconcile
from ..domain.rules import evaluate
from . import plan_binding, storage, vessel_profile_service
from .vessel_profile_store import ProfileUnavailable

PIPE = (plan_binding.V1, plan_binding.V2)


class SnapshotError(ValueError):
    """The stored snapshot cannot be served; message is Vietnamese."""


def load_snapshot(identifier):
    """-> (id, name, created_utc, plan_json text verbatim, Plan). SnapshotError (bad id/version/data), LookupError (unknown)."""
    try:
        if str(UUID(identifier)) != identifier:
            raise ValueError()
    except (ValueError, AttributeError):
        raise SnapshotError('ID phương án không hợp lệ.')
    with storage.connection() as db:
        row = db.execute('SELECT id,name,created_utc,schema_version,plan_json FROM snapshots WHERE id=?', (identifier,)).fetchone()
    if row is None:
        raise LookupError('Không tìm thấy phương án đã lưu.')
    if row[3] != 'scst.saved-plan.v1':
        raise SnapshotError('Phiên bản phương án đã lưu không được hỗ trợ.')
    try:
        plan = Plan.model_validate(json.loads(row[4]))
    except ValueError:
        raise SnapshotError('Dữ liệu phương án đã lưu không hợp lệ.') from None
    return row[0], row[1], row[2], row[4], plan


def _recheck(plan):
    if plan.contract_version not in PIPE:
        return {'status': 'NOT_APPLICABLE', 'latest_revision_id': None, 'added': 0, 'removed': 0, 'changed': 0, 'placed_affected': 0}
    try:
        latest = plan_binding.latest()
    except plan_binding.PlanBindingError:
        return {'status': 'REVISION_UNAVAILABLE', 'latest_revision_id': None, 'added': 0, 'removed': 0, 'changed': 0, 'placed_affected': 0}
    r = plan_binding.recheck(plan, latest)
    return {'status': r['status'], 'latest_revision_id': latest['revision_id'], 'added': r['added'], 'removed': r['removed'],
            'changed': r['changed'], 'placed_affected': r['placed_affected']}


def snapshot_report(identifier, now=None):
    """The scst.plan-report.v1 dict of a saved snapshot. Raises LookupError (unknown), PlanBindingError/ValueError
    (cannot be served) or ReportReconciliationError (report disagrees with evaluate(plan); nothing is returned)."""
    sid, name, saved_utc, plan_json, plan = load_snapshot(identifier)
    plan_binding.bind(plan)
    evaluation = evaluate(plan)
    try:
        profile = None
        if plan.vessel is not None:
            profile = vessel_profile_service.detail(plan.vessel.vessel_id, plan.vessel.profile_version or 1)
        revision = packing = None
        if plan.contract_version in PIPE:
            pinned = plan_binding.view(plan.cargo_revision.revision_id if plan.contract_version == plan_binding.V2 else plan_binding.BASE)
            revision = {'revision_id': pinned['revision_id'], 'content_sha256': pinned['content_sha256']}
            packing = pack_revision(pinned)
    except (LookupError, ProfileUnavailable) as exc:
        raise plan_binding.PlanBindingError(str(exc)) from None
    report = build_report(snapshot_id=sid, name=name, saved_utc=saved_utc, plan_json=plan_json, plan=plan, evaluation=evaluation,
                          profile=profile, recheck=_recheck(plan), packing=packing, revision=revision,
                          generated_utc=(now or datetime.now(timezone.utc)).isoformat())
    reconcile(report, evaluation)
    return report
