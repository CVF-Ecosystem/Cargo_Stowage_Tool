# SCST M2a — Nhập liệu/import/lưu-mở

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and worker scope

Owner requests continue agreed roadmap; SPEC SCST_M2A bounds the next slice. Root reviewed current M1/VINAFCO source and selects M2a; lifecycle DESIGN/SPEC/WORK_ORDER completed before BUILD. Worker Terra6.1High backend/frontend; Sol-Medium browser; root independent reviewer and commit owner. No business acceptance inferred.

Allowed worker paths: services/backend/**, apps/frontend/**, contracts/**, tests/backend/test_m2a*.py, tests/m2a_restart_smoke.py, tests/fixtures/m2a/**, docs/reviews/SCST_M2A_EVIDENCE/**, docs/reviews/SCST_M2A_WORKER_RETURN.md. Sol owns tests/browser/m2a*.spec.ts and browser evidence only. Existing browser tests remain untouched; generated screenshots restored to prior bytes by root after verification. Existing locks/launcher/runtime unchanged except env test-isolation configuration in Playwright allowed. No newdependencies, profileassets/archive/originalsource/CVFcore/governance edits by worker; no commit/push/deploy/provider. Root handles SPEC/authority/continuity/catalog/README/guide/.gitignore. SQLite in ignored runtime-data, server-config path only. Do not reuse oldruntimecache or infer cargo mass.

Sequence: backend versioned model/CSV/storage API and meaningful tests → regenerate contracts → frontend checked drafts/manual/preview/saveopen → browser+restart persistence proof → independent root review. Cross-role checkpoints; 180min implementation +60min review/support budget, no resets. Source truth starts d13392e. Worker waits root dispatch commit/BUILD acknowledgment before edits. Send endpoint names/response shapes to browser worker when ready. No planner/M2b, PDF/XLSX/M2d, multilayer/M3 or AI.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2A.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2A.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_M2A.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M2A.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
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
    "path": "docs/specs/SCST_M2A.md",
    "heading": "## M2a acceptance",
    "sha256": "f1e4853288090d9b9c3cb4517607dca42c6489e5df686d15f4c1b10723bdad05"
  },
  "milestone": {
    "id": "SCST-M2A",
    "consumer": "Owner SCST",
    "outcome": "Manual and CSV cargo/hold input with checked local saved snapshots reopened after restart",
    "checkpoint": {
      "trigger": "Seven M2a criteria evidenced or240minute budget/scope boundary",
      "owner": "Root reviewer; project owner business scope",
      "decision": "Review readiness, repair within scope, or return unresolved boundary; no automatic M2b"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "M2A-01",
      "M2A-02",
      "M2A-03",
      "M2A-04",
      "M2A-05",
      "M2A-06",
      "M2A-07"
    ],
    "owner": "Root independent reviewer",
    "output": "M2a app and docs/reviews/SCST_M2A_REVIEW.md",
    "budgetMinutes": 240,
    "stop": "Seven technical criteria verified; no automatic M2b or operational acceptance",
    "next": "Prepare bounded SPEC M2b for heuristic placement and unplaced reasons after owner feedback/checkpoint; M2b not dispatched in this tranche."
  },
  "rows": [
    {
      "id": "M2A-01",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business/real-data acceptance separate",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2A_REVIEW.md",
          "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
        }
      ]
    },
    {
      "id": "M2A-02",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business/real-data acceptance separate",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2A_REVIEW.md",
          "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
        }
      ]
    },
    {
      "id": "M2A-03",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business/real-data acceptance separate",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2A_REVIEW.md",
          "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
        }
      ]
    },
    {
      "id": "M2A-04",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business/real-data acceptance separate",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2A_REVIEW.md",
          "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
        }
      ]
    },
    {
      "id": "M2A-05",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business/real-data acceptance separate",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2A_REVIEW.md",
          "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
        }
      ]
    },
    {
      "id": "M2A-06",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business/real-data acceptance separate",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2A_REVIEW.md",
          "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
        }
      ]
    },
    {
      "id": "M2A-07",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business/real-data acceptance separate",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2A_REVIEW.md",
          "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "All seven M2a technical criteria verified; owner selected labelled fixtures, no M2b dispatch",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_M2A_REVIEW.md",
        "sha256": "4a1db0958dda75dbd48f4a81b4950d426a5cf4058960dd54679238b54f604358"
      }
    ],
    "product": "PENDING",
    "productSummary": "Remaining M2b-d/M3 and business acceptance separate",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```
