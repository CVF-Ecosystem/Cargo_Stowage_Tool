# SCST — Practical display units repair

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

Owner requests practical kg/cm presentation01-11-2026. SPEC docs/specs/SCST_DISPLAY_UNITS.md binds four criteria; no historical SPEC acceptance changes. Base232807d. Root ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER and commit owner. Terra IMPLEMENTATION_WORKER owns apps/frontend/src/{features/model.ts,features/Workspace.tsx,features/ComparisonPanel.tsx,viewer-3d/Viewer.tsx,styles.css}, evidence worker-return.md. Sol owns tests/browser/*.spec.ts and evidence browser/**/browser-return.md; update existing expectations only for display/new input units while preserving exact API/geometry/transaction assertions. Add tests/browser/display-units.spec.ts for unchanged-field preservation, practical presentation, precise explicit conversion, compare small-delta label and recovery. Root owns docs/catalog/continuity/review/commit. No edits before admission and BUILD ack.

Allowed evidence docs/reviews/SCST_DISPLAY_UNITS_EVIDENCE/** by owner. Read-only backend/API/model/geometry/rules/planner/storage/registry/data/GLB/source/contracts/dependencies/launcher/archive/core and governance controls. No DB writes in user runtime for tests, use isolated browser suite DB; no push/provider/dependency/network additions. Reuse precise dimensions/footprint for mesh; add display helpers only. All draft changes need field tracking so rounded defaults never rewrite untouched values. cm/kg exact decimal conversion, defaults1cm/1kg, existing representable fractions accepted. CSV explicit format unchanged. 100min ceiling includes preparation/focusedchecks/finalreview, no reset on repair. Four criteria mandatory, checkpoint separate from overall roadmap/product. Worker return includes changed paths/checks/errors/limits; root proves developer-owned packaged flow before feedback. Mechanical gates do not prove AI governance. Reviewer-local repair within same contract disclosed; material expansion follows existing REWORK boundary.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_DISPLAY_UNITS.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_DISPLAY_UNITS.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_DISPLAY_UNITS.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_DISPLAY_UNITS.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
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
    "path": "docs/specs/SCST_DISPLAY_UNITS.md",
    "heading": "## Display acceptance",
    "sha256": "71153d80508b9c98274c2820a37e5455636674e04c83d94f56d48117105e42ba"
  },
  "milestone": {
    "id": "SCST-DISPLAY-UNITS",
    "consumer": "Owner SCST",
    "outcome": "Practical kg/cm/m presentation with exact underlying data preserved",
    "checkpoint": {
      "trigger": "Four criteria evidenced or100minute boundary",
      "owner": "Root reviewer / project owner business feedback",
      "decision": "Technical review and bounded repair; no M2d"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "DU-01",
      "DU-02",
      "DU-03",
      "DU-04"
    ],
    "owner": "Root independent reviewer",
    "output": "Practical units UI and docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
    "budgetMinutes": 100,
    "stop": "Four criteria proof or scope/time boundary",
    "next": "Owner reviews practical kg/cm/m display repair; next roadmap slice M2d needs separate SPEC/WORK_ORDER when selected, no automatic implementation."
  },
  "rows": [
    {
      "id": "DU-01",
      "state": "VERIFIED",
      "gap": "Technical criterion and usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
          "sha256": "de275460eb34dd2e8732f5a49b1373108dcf422aaf19ea575e53c8fac9a30cdc"
        }
      ]
    },
    {
      "id": "DU-02",
      "state": "VERIFIED",
      "gap": "Technical criterion and usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
          "sha256": "de275460eb34dd2e8732f5a49b1373108dcf422aaf19ea575e53c8fac9a30cdc"
        }
      ]
    },
    {
      "id": "DU-03",
      "state": "VERIFIED",
      "gap": "Technical criterion and usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
          "sha256": "de275460eb34dd2e8732f5a49b1373108dcf422aaf19ea575e53c8fac9a30cdc"
        }
      ]
    },
    {
      "id": "DU-04",
      "state": "VERIFIED",
      "gap": "Technical criterion and usable flow verified; business/operational acceptance separate.",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
          "sha256": "de275460eb34dd2e8732f5a49b1373108dcf422aaf19ea575e53c8fac9a30cdc"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "Four practical display criteria and packaged user flow independently verified.",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md",
        "sha256": "de275460eb34dd2e8732f5a49b1373108dcf422aaf19ea575e53c8fac9a30cdc"
      }
    ],
    "product": "PENDING",
    "productSummary": "Business/operational acceptance and M2d separate",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Technical closure

Four criteria verified; no active app order remains. Local material commit before closure claim. Product/business/operational acceptance pending. Closed applicability skips closeability; initial dispatch did check it, not bypassed. Default kg/cm means rounded display resolution, not new spinner/HTML step constraints.
