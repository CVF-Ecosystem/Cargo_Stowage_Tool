# SCST — Pipe list source integration

Status: APPROVED_FOR_EXECUTION
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and worker scope

Current owner V1.1 request and SPEC SCST_PIPE_LIST authorize bounded source-list integration, not a new ship model or planner. Base a3bbcd0. Root SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER and commit owner. Terra6.1High owns backend/frontend; Sol-Medium owns new browser tests. No implementation before dispatch commit and BUILD acknowledgment.

Allowed Terra paths: services/backend/** except data/vessels/** and vessel.py; apps/frontend/src/**; contracts/**; tests/backend/test_pipe_list*.py; tests/pipe_list_restart_smoke.py; tooling/import_pipe_list.py; docs/reviews/SCST_PIPE_LIST_WORKER_RETURN.md; docs/reviews/SCST_PIPE_LIST_EVIDENCE/**. Source package read-only VINAFCO268_LOCAL_HANDOFF_V1_1/**. Sol owns tests/browser/pipe-list*.spec.ts and new evidence browser files only. Existing tests unchanged, historical generated screenshots restored by root. No dependency, lock, launcher, core, archived, profile/GLB, workbook, governance, commit/push/deploy/provider changes by workers. Root owns documentation/continuity/catalog/.gitignore and calculation receipt.

Deliver all six criteria. Use fixed registry derivative with sourcehash, not runtime XLSX parser or inferred bundle mass. Browser contract coordinated after backend route shapes settle. Budget180min build+60min review/support, no reset. Existing domain/workspace/snapshots reused. Any incompatible source fact returns before dependent effects. Independent root tests source, API, exactµm, adversarial payload, UI/counters/persistence, and review all evidence before local closure. No GitHub push of this source data.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_PIPE_LIST.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_PIPE_LIST.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_PIPE_LIST.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_PIPE_LIST.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
| reviewer_fast | REVIEW | reviewer | REVIEW | apps/frontend; services/backend; contracts; tests; tooling; README.md | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | worker_return_fast |
| pre_commit | PRE_MATERIAL_COMMIT | commit-steward | PRE_MATERIAL_COMMIT | docs; CVF_SESSION; IMPLEMENTATION_STATUS.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | reviewer_fast |
| terminal_completion_review | POST_MATERIAL | reviewer | REVIEW | docs/work_orders | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | pre_commit |
| continuity | CONTINUITY_COMMIT | session-sync-steward | CONTINUITY_COMMIT | CVF_SESSION; CVF_SESSION_MEMORY.md; IMPLEMENTATION_STATUS.json; docs/catalog | BOUNDED_PATH_FAMILIES | session-sync-steward | CONTINUITY_COMMIT | terminal_completion_review |
| committed_range_closure | POST_MATERIAL_CLOSURE | commit-steward | POST_MATERIAL_CLOSURE | docs/work_orders; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | CORRECTIVE_MATERIAL_COMMIT | continuity |





## Milestone coverage

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/specs/SCST_PIPE_LIST.md",
    "heading": "## Pipe list acceptance",
    "sha256": "dd83fed71b42a74294556bf21f6f9655bedee2d1953fee3ec9e87bbbf87fc9f6"
  },
  "milestone": {
    "id": "SCST-PIPE-LIST",
    "consumer": "Owner SCST",
    "outcome": "Load actual31group pipe list and place individual bundles with exact calculated totals and preserved hull",
    "checkpoint": {
      "trigger": "Six criteria evidenced or240min/scope boundary",
      "owner": "Root reviewer; owner business acceptance",
      "decision": "Review technical usability, repair within scope, hold unresolved boundary; no automatic M2b"
    }
  },
  "phase": "DISPATCH",
  "action": {
    "kind": "IMPLEMENT",
    "selected": [
      "PIPE-01",
      "PIPE-02",
      "PIPE-03",
      "PIPE-04",
      "PIPE-05",
      "PIPE-06"
    ],
    "owner": "Terra implementation; Sol browser; root review",
    "output": "Local app plus docs/reviews/SCST_PIPE_LIST_REVIEW.md",
    "budgetMinutes": 240,
    "stop": "Six criteria proof or scope/budget boundary",
    "next": "Independent review then owner product feedback; M2b not dispatched"
  },
  "rows": [
    {
      "id": "PIPE-01",
      "state": "NOT_STARTED",
      "gap": "New list source adapter and focused proof not yet implemented",
      "owner": "Terra/Sol then root reviewer",
      "destination": "docs/reviews/SCST_PIPE_LIST_REVIEW.md",
      "evidence": []
    },
    {
      "id": "PIPE-02",
      "state": "NOT_STARTED",
      "gap": "New list source adapter and focused proof not yet implemented",
      "owner": "Terra/Sol then root reviewer",
      "destination": "docs/reviews/SCST_PIPE_LIST_REVIEW.md",
      "evidence": []
    },
    {
      "id": "PIPE-03",
      "state": "NOT_STARTED",
      "gap": "New list source adapter and focused proof not yet implemented",
      "owner": "Terra/Sol then root reviewer",
      "destination": "docs/reviews/SCST_PIPE_LIST_REVIEW.md",
      "evidence": []
    },
    {
      "id": "PIPE-04",
      "state": "NOT_STARTED",
      "gap": "New list source adapter and focused proof not yet implemented",
      "owner": "Terra/Sol then root reviewer",
      "destination": "docs/reviews/SCST_PIPE_LIST_REVIEW.md",
      "evidence": []
    },
    {
      "id": "PIPE-05",
      "state": "NOT_STARTED",
      "gap": "New list source adapter and focused proof not yet implemented",
      "owner": "Terra/Sol then root reviewer",
      "destination": "docs/reviews/SCST_PIPE_LIST_REVIEW.md",
      "evidence": []
    },
    {
      "id": "PIPE-06",
      "state": "NOT_STARTED",
      "gap": "New list source adapter and focused proof not yet implemented",
      "owner": "Terra/Sol then root reviewer",
      "destination": "docs/reviews/SCST_PIPE_LIST_REVIEW.md",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Admitted local source integration only",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "Measuredhold/business acceptance and M2b-d/M3 separate",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```
