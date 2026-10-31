# SCST — VINAFCO 268 selective integration

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and execution

Owner asks assess then integrate supplied package if usable; initial assessment accepts illustrative use with explicit estimates. Source/acceptance: [SPEC](../specs/SCST_VINAFCO268.md). Root owns scope/gates/docs/commits; Terra6.1High backend/frontend worker; Sol-Medium browser verification, disjoint paths. Root independent review; root did not author supplied model. No permission to publish new real-source artifacts. Preserve package bytes.

Allowed worker paths: services/backend/**, apps/frontend/**, contracts/**, tests/backend/test_vinafco*.py, docs/reviews/SCST_VINAFCO268_EVIDENCE/** and docs/reviews/SCST_VINAFCO268_WORKER_RETURN.md. Root assigns Sol tests/browser/vinafco*.spec.ts only. No governance/core/archive/launcher/lockfile changes by workers. No new dependencies or external services. Read profile/GLB from sanitized app assets; no runtime dependency on incoming handoff. No raw PDF/personal URLs in copied data or API. Root .gitignore excludes incoming package from accidental publication.

Sequence: sanitize/profile adapter + server constraints → generated OpenAPI/types → vessel mode/viewer → backend/build/browser evidence → independent review. Keep existing default M1 tests. Evidence must check actual GLB/world matrices, case transitions/cargo limits, failures, stale/history, and mobile fallback. Root compares PDF principal values and supplied manifest independently. Do not claim naval safety or live CVF governance. Worker no commit/push; root dispatch marker before worker writes. 120min build +45min review ceiling, stop on boundary or repeated repair without new cause. Remainders tracked in SPEC; no automatic M2 work.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_VINAFCO268.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_VINAFCO268.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_VINAFCO268.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_VINAFCO268.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
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
    "path": "docs/specs/SCST_VINAFCO268.md",
    "heading": "## VIN acceptance",
    "sha256": "5b38911a2325311bdc140a101e823adacdad1e03ead651b63dabaaa692691143"
  },
  "milestone": {
    "id": "SCST-VINAFCO268",
    "consumer": "Owner SCST",
    "outcome": "Reference vessel view with synthetic cargo and explicit estimate/source boundaries",
    "checkpoint": {
      "trigger": "Six criteria evidenced or 165minute budget/scope boundary",
      "owner": "Root reviewer; owner business acceptance",
      "decision": "Review and repair within authority, or report remaining issue; no full M2 dispatch"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "VF-01",
      "VF-02",
      "VF-03",
      "VF-04",
      "VF-05",
      "VF-06"
    ],
    "owner": "Root independent reviewer",
    "output": "Selective vessel integration and docs/reviews/SCST_VINAFCO268_REVIEW.md",
    "budgetMinutes": 165,
    "stop": "Technical slice complete, no automatic remaining M2 or business acceptance",
    "next": "Owner views local VINAFCO268 mode and supplies business feedback; no remaining M2 functionality is dispatched."
  },
  "rows": [
    {
      "id": "VF-01",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business acceptance pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
          "sha256": "8bcd37d394ddcd489ccc73b84a2353f8d9ea1692663a24db14a2de95e0f8d34b"
        }
      ]
    },
    {
      "id": "VF-02",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business acceptance pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
          "sha256": "8bcd37d394ddcd489ccc73b84a2353f8d9ea1692663a24db14a2de95e0f8d34b"
        }
      ]
    },
    {
      "id": "VF-03",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business acceptance pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
          "sha256": "8bcd37d394ddcd489ccc73b84a2353f8d9ea1692663a24db14a2de95e0f8d34b"
        }
      ]
    },
    {
      "id": "VF-04",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business acceptance pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
          "sha256": "8bcd37d394ddcd489ccc73b84a2353f8d9ea1692663a24db14a2de95e0f8d34b"
        }
      ]
    },
    {
      "id": "VF-05",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business acceptance pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
          "sha256": "8bcd37d394ddcd489ccc73b84a2353f8d9ea1692663a24db14a2de95e0f8d34b"
        }
      ]
    },
    {
      "id": "VF-06",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; business acceptance pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
          "sha256": "8bcd37d394ddcd489ccc73b84a2353f8d9ea1692663a24db14a2de95e0f8d34b"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "Six technical criteria verified on reviewed source; owner acceptance remains separate",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_VINAFCO268_REVIEW.md",
        "sha256": "8bcd37d394ddcd489ccc73b84a2353f8d9ea1692663a24db14a2de95e0f8d34b"
      }
    ],
    "product": "PENDING",
    "productSummary": "No owner business acceptance; remaining M2/M3 stay separate",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```
