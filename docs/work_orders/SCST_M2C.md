# SCST M2c — Giữ gốc và so sánh phương án

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and scope

Owner says “tiếp”01-11-2026 after M2b handoff. SPEC docs/specs/SCST_M2C.md bounds nextroadmap M2c, six criteria. Base e5a8b74b86ae5dc2530ca45a276cbb72ae354524. Root ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER and commitowner; Terra6.1High runtime/backend tests, Sol-Medium browser. No edits before admission commit and BUILD acknowledgment.

Terra allowed: services/backend/app/domain/comparison/** (new); services/backend/app/api/**; apps/frontend/src/**; contracts/**; tests/backend/test_m2c*.py; tests/m2c_restart_smoke.py; docs/reviews/SCST_M2C_WORKER_RETURN.md; docs/reviews/SCST_M2C_EVIDENCE/** except browser/**, browser-return.md and root-* files. Reuse immutable storage API unchanged. Sol owns tests/browser/m2c*.spec.ts and evidence browser/**, browser-return.md only. Existing tests/runtime guards unchanged, historical generated evidence restored byroot. Read-only data/vessel/registry/geometry/model/rules/planner/storage/sourceworkbooks/GLB/archive/locks/launcher/core/governance. No newdeps/DBschema/commit/push/provider/network/export/multilayer. Root owns docs/continuity/catalog/roadmap and finalreview; reviewer-local repairs only within existing boundedcontract with disclosure.

Backendtyped compare validates/re-evaluates A/B separately and computes exact complete context/unit/placement diffs; UI preserves B when setting/loading A, explicit compare/filter/page/detail/select/restore, STALE and revision guards. Save uses existing immutableUUID snapshots. Do not show rawJSON as UI, do not infer optimality/physicalidentity from matchingID. Existing rounded overview stays2decimaltonnes; comparisondetail reveals1g/1mm/µm. APIvalues preserve exact units. No secondThree scene/overlay. Old arrayunit/placement order doesnot create changes; source/shape/limits changes reported, not normalized away.

Read-only Sol preflight agrees native reuse and gives8boundary/workflow cases. Main gap: history20 alone cannot identify a baseline or explain changes. Preparation includes doctor28checks+boundedsource/preflight, elapsed/billing partlyUNKNOWN.180min build+60min review/support ceiling240min, no reset on repair. PriorM2b/PIPE-LIST evidence reused; root final fullregression once frozen, focusedrechecks only for meaningful changes/failures. Worker return covers all six criteria, failures/sourceboundaries/openlimits; root owns final usability and business-acceptance boundary. No automaticM2d after closure.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2C.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2C.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_M2C.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M2C.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
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
    "path": "docs/specs/SCST_M2C.md",
    "heading": "## M2c acceptance",
    "sha256": "1497e594cd500793d61052fc206e2d4b87156d5ec81cb9a08d951ee9eaf57bea"
  },
  "milestone": {
    "id": "SCST-M2C",
    "consumer": "Owner SCST",
    "outcome": "Keep a baseline, edit/check current plan, compare full exact changes and restore without losing saved versions",
    "checkpoint": {
      "trigger": "Six criteria evidenced or240minute/scope boundary",
      "owner": "Root reviewer; project owner business decision",
      "decision": "Review usableflow, repair within scope or return unresolved boundary; no automatic M2d"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "M2C-01",
      "M2C-02",
      "M2C-03",
      "M2C-04",
      "M2C-05",
      "M2C-06"
    ],
    "owner": "Root independent reviewer",
    "output": "M2c app and docs/reviews/SCST_M2C_REVIEW.md",
    "budgetMinutes": 240,
    "stop": "Six criteria proof or budget/scope boundary",
    "next": "Owner reviews technically delivered M2c; next roadmap slice M2d requires separate SPEC/WORK_ORDER when selected, no automatic implementation."
  },
  "rows": [
    {
      "id": "M2C-01",
      "state": "VERIFIED",
      "gap": "Technical criterion and developer-owned usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2C_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2C_REVIEW.md",
          "sha256": "849dc11dcb3f2036d3fc23ae53d53d1593eed5497f45c41ce9313ed70adcf97c"
        }
      ]
    },
    {
      "id": "M2C-02",
      "state": "VERIFIED",
      "gap": "Technical criterion and developer-owned usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2C_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2C_REVIEW.md",
          "sha256": "849dc11dcb3f2036d3fc23ae53d53d1593eed5497f45c41ce9313ed70adcf97c"
        }
      ]
    },
    {
      "id": "M2C-03",
      "state": "VERIFIED",
      "gap": "Technical criterion and developer-owned usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2C_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2C_REVIEW.md",
          "sha256": "849dc11dcb3f2036d3fc23ae53d53d1593eed5497f45c41ce9313ed70adcf97c"
        }
      ]
    },
    {
      "id": "M2C-04",
      "state": "VERIFIED",
      "gap": "Technical criterion and developer-owned usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2C_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2C_REVIEW.md",
          "sha256": "849dc11dcb3f2036d3fc23ae53d53d1593eed5497f45c41ce9313ed70adcf97c"
        }
      ]
    },
    {
      "id": "M2C-05",
      "state": "VERIFIED",
      "gap": "Technical criterion and developer-owned usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2C_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2C_REVIEW.md",
          "sha256": "849dc11dcb3f2036d3fc23ae53d53d1593eed5497f45c41ce9313ed70adcf97c"
        }
      ]
    },
    {
      "id": "M2C-06",
      "state": "VERIFIED",
      "gap": "Technical criterion and developer-owned usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M2C_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M2C_REVIEW.md",
          "sha256": "849dc11dcb3f2036d3fc23ae53d53d1593eed5497f45c41ce9313ed70adcf97c"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "Six technical criteria and integrated usable flow independently verified.",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_M2C_REVIEW.md",
        "sha256": "849dc11dcb3f2036d3fc23ae53d53d1593eed5497f45c41ce9313ed70adcf97c"
      }
    ],
    "product": "PENDING",
    "productSummary": "M2d/M3 and business/operational acceptance pending; local delivery only.",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Technical disposition

Six criteria verified by root independent REVIEW, 104 backend/28 browser/902 checks and packaged flow; see review and exact-version manifest. Technical order CLOSED, business/operational acceptance PENDING. No automatic M2d. Admission closeability checked before BUILD; final CLOSED packet skips that check as not applicable, never used to bypass initial dispatch. Local material commit required before closure claim.
