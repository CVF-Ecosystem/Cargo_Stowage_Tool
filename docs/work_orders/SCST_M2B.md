# SCST M2b — Xếp thử tự động và hiển thị gọn

Status: APPROVED_FOR_EXECUTION
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and scope

Owner01-11-2026 asks mass displayrounding and explicitly chooses “Bắt đầu phần xếp thử tự động theo roadmap M2b”. SPEC docs/specs/SCST_M2B.md authorizes allsixcriteria. Base a596298d9140f66a580d845144692fc3865b396c. Root ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR and independent REVIEWER/commitowner; Terra6.1High runtime/tests, Sol-Medium browser. No worker edits before admitted dispatch commit + BUILD acknowledgment.

Allowed Terra: services/backend/app/domain/planner/** (new); services/backend/app/api/**; apps/frontend/src/**; contracts/**; tests/backend/test_m2b*.py; tests/m2b_restart_smoke.py; docs/reviews/SCST_M2B_WORKER_RETURN.md; docs/reviews/SCST_M2B_EVIDENCE/** except browser/** and root-* files. Small model/geometry adapter edits only if needed for typedresponse/reuse, preserve prior invariants. Sol owns tests/browser/m2b*.spec.ts plus minimal formatter expectations in tests/browser/workspace.spec.ts and tests/browser/pipe-list.spec.ts; must preserve integergram/async/geometry assertions and disclose every oldexpectation change. Sol evidence browser/** and browser-return.md. No existing backendtest changes. Runtime/source data read-only: services/backend/data/**, vessel.py, pipe_registry.py, normalized source and rawpackage, originalworkbooks/GLB, archive. No dependency/lock/launcher/storage/schemaDB/core/governance/provider/network/push/commit changes byworkers. Root owns continuity/catalog/SPEC/order/README/guide/roadmap.

Implement backend guillotine planner+boundedtypedresponse/tests → generateOpenAPI/types → UIpreview/apply/reasonpaging/rounding → Solbrowserproof → rootindependentreview/restart/performance. Root reuses sourcecalculation/sourcebindings; no Excelaudit. Inputmetadata/unitarray preserved, onlycandidateplacements replaced; deterministic repeatedpreviews and placement-order independent of unitinputorder via IDtiebreak. Exact sourceµm validation preserved; conservativeplanner grid and heuristiclimits documented. EmptyM2a preview clean/explicit; no inventedcargo.

Read-only preflight Sol verified rectangular split/disjointness and≤N+1free rectangles, capacityprecision and reasons/async risks. Priorelapsed prep partlyUNKNOWN; observed doctor28checks+boundedscan/preflight, billingUNKNOWN. Additional180min build+60min review/support total240min; no resetting on repair. Existingmanualplacement cannot close automaticplacementcriterion; smallestlocalheuristic chosen, no external solver. Stop at sixcriteria or budget/scopeboundary, no automaticM2c. Root finaldecision separates technical+developerusableflow from ownerbusinessacceptance. Localcommitonly, rawdata notpublished.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2B.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2B.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_M2B.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M2B.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
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
    "path": "docs/specs/SCST_M2B.md",
    "heading": "## M2b acceptance",
    "sha256": "2bf1d6752ebae9cc9bf6de301f5257d04a4604889d281bcaf4cbac452d3b075b"
  },
  "milestone": {
    "id": "SCST-M2B",
    "consumer": "Owner SCST",
    "outcome": "Automatically propose single-layer positions, display cargo on ship after explicitapply, explain remainingunits and rounddisplaymass",
    "checkpoint": {
      "trigger": "Sixcriteria proof or240minute/scope boundary",
      "owner": "Rootreviewer; projectowner businessdecision",
      "decision": "Review usableflow, repair within scope or hold unresolvedboundary; no automaticM2c"
    }
  },
  "phase": "DISPATCH",
  "action": {
    "kind": "IMPLEMENT",
    "selected": [
      "M2B-01",
      "M2B-02",
      "M2B-03",
      "M2B-04",
      "M2B-05",
      "M2B-06"
    ],
    "owner": "Terra implementation; Solbrowser; rootindependentreview",
    "output": "M2b app and docs/reviews/SCST_M2B_REVIEW.md",
    "budgetMinutes": 240,
    "stop": "Sixcriteria proof or boundary, no M2c",
    "next": "Independent source/oracle/browser review before ownerfeedback"
  },
  "rows": [
    {
      "id": "M2B-01",
      "state": "NOT_STARTED",
      "gap": "M2b heuristic/transactions/reasons/display proof not implemented",
      "owner": "Terra/Sol then rootreviewer",
      "destination": "docs/reviews/SCST_M2B_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2B-02",
      "state": "NOT_STARTED",
      "gap": "M2b heuristic/transactions/reasons/display proof not implemented",
      "owner": "Terra/Sol then rootreviewer",
      "destination": "docs/reviews/SCST_M2B_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2B-03",
      "state": "NOT_STARTED",
      "gap": "M2b heuristic/transactions/reasons/display proof not implemented",
      "owner": "Terra/Sol then rootreviewer",
      "destination": "docs/reviews/SCST_M2B_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2B-04",
      "state": "NOT_STARTED",
      "gap": "M2b heuristic/transactions/reasons/display proof not implemented",
      "owner": "Terra/Sol then rootreviewer",
      "destination": "docs/reviews/SCST_M2B_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2B-05",
      "state": "NOT_STARTED",
      "gap": "M2b heuristic/transactions/reasons/display proof not implemented",
      "owner": "Terra/Sol then rootreviewer",
      "destination": "docs/reviews/SCST_M2B_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2B-06",
      "state": "NOT_STARTED",
      "gap": "M2b heuristic/transactions/reasons/display proof not implemented",
      "owner": "Terra/Sol then rootreviewer",
      "destination": "docs/reviews/SCST_M2B_REVIEW.md",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "OwnerexplicitlyselectedM2b after PIPE-LIST feedback",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "M2c-d/M3 andbusinessacceptance remainseparate",
    "acceptance": [],
    "owner": "Projectowner"
  }
}
```
