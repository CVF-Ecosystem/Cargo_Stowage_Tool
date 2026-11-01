# SCST — SUP-01 bounded viewer work order

Status: ACTIVE
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

Owner asks to apply the new CVF transfer and continue the agreed roadmap. Root has reconciled source/hash and prepared SPEC docs/specs/SCST_SUP_01.md with four criteria, after bounded CVF-DEV verification. Scoped continuation requires independent review of docs/reviews/SCST_CVF_DEV_APPLICATION_RECONCILIATION.md before BUILD; it does not close full CVF adoption or prove agent governance. Core pin c4c8767 and profile1.2 unchanged. Baseline6f8fa9f; preserve incoming owner additions captured in evidence/incoming-transfer.json. No historical acceptance edits.

Root ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR admits packet and continuity, independently reviews worker implementation, owns docs/source manifest/final commit. Terra IMPLEMENTATION_WORKER owns apps/frontend/src/viewer-3d/** and apps/frontend/src/styles.css only, plus docs/reviews/SCST_SUP_01_EVIDENCE/worker-return.md. Sol BROWSER_WORKER owns tests/browser/** and apps/frontend/playwright.config.ts, plus evidence/browser/** and browser-return.md. Both use normal worker-return phase; roles are responsibilities, not provider requirements. No worker edits outside ownership or commits; coordinate build/server on port8766, never run suites in parallel.

Apply SCST-DA01/DA04/DA05 explicitly in worker returns: preserve exact data and practical units, reuse native viewer/kit and real invocation receipts, show usable product flow rather than test count. DA02 limits DB tests to isolated SCST_DATA_DIR; no persistence changes. DA03 keeps current source/profile/GLB transformation and uncertainty; no domain rule added. No external provider/API, secrets, new dependencies, engine, backend/contracts/schemaDB/source/GLB changes, core/profile/policy/CI/hook changes, deployment or push. UI 2D fallback/history/selection/source warnings stay usable. Root may update only current docs/catalog/continuity and artifact bindings; protected roadmap acceptance sections/closed packets remain unchanged.

Implementation: follow SPEC D1-D4, stable scene/asset lifecycle with incremental cargo and callback refs, fitting/presets/focus, selective owned material modes and explicit query diagnostics opt-in. Browser worker updates existing geometry tests to request diagnostics without weakening numerical assertions and routes screenshots/geometry receipts into SUP-01 evidence, preserving old evidence. New focused tests cover default-off, pose/canvas/asset persistence, context/profile races and failure, framing/mobile, material restoration, exact geometry/picking and retained save/reopen on isolated DB. Record baseline before new frontend build; Terra may edit/typecheck but coordinate the first build with Sol after baseline capture. Measure synthetic and actual1076 source with actual placed count, same environment, timing sample/range/resource observations; no unsupported FPS claim.

120minute total prep/worker/browser/review budget, no reset on repair. One full browser suite after candidate freeze; targeted rerun only for named failures/new changes; backend suite reused if unchanged. Build/contract checks appropriate to changed paths. Worker returns paths, commands/results, failed attempts, evidence/version, DA controls, limitations and remaining owner. Root verifies internal end-to-end consumer flow before feedback; business acceptance/public action separate. Stop dependent work if source/permission/risk/paths expand. No automatic SUP-02.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_SUP_01.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_SUP_01.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_SUP_01.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend/src/viewer-3d; apps/frontend/src/styles.css; tests/browser; apps/frontend/playwright.config.ts | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend/src/viewer-3d; apps/frontend/src/styles.css; tests/browser; apps/frontend/playwright.config.ts | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_SUP_01.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | apps/frontend/src/viewer-3d; apps/frontend/src/styles.css; tests/browser; apps/frontend/playwright.config.ts | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
| reviewer_fast | REVIEW | reviewer | REVIEW | apps/frontend/src/viewer-3d; apps/frontend/src/styles.css; tests/browser; apps/frontend/playwright.config.ts; README.md | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | worker_return_fast |
| pre_commit | PRE_MATERIAL_COMMIT | commit-steward | PRE_MATERIAL_COMMIT | docs; CVF_SESSION; IMPLEMENTATION_STATUS.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | reviewer_fast |
| terminal_completion_review | POST_MATERIAL | reviewer | REVIEW | docs/work_orders | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | pre_commit |
| continuity | CONTINUITY_COMMIT | session-sync-steward | CONTINUITY_COMMIT | CVF_SESSION; CVF_SESSION_MEMORY.md; IMPLEMENTATION_STATUS.json; docs/catalog | BOUNDED_PATH_FAMILIES | session-sync-steward | CONTINUITY_COMMIT | terminal_completion_review |
| committed_range_closure | POST_MATERIAL_CLOSURE | commit-steward | POST_MATERIAL_CLOSURE | docs/work_orders; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | CORRECTIVE_MATERIAL_COMMIT | continuity |





## Milestone coverage

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/specs/SCST_SUP_01.md",
    "heading": "## SUP-01 acceptance",
    "sha256": "6ce66bc1537a2e1fb8593d388029ab97d9dfb4d9c967b60b068d40034171e789"
  },
  "milestone": {
    "id": "SCST-SUP-01",
    "consumer": "SCST owner and local tool user",
    "outcome": "Readable persistent viewer with camera presets, selective ghost and bounded diagnostics",
    "checkpoint": {
      "trigger": "Four criteria evidenced or120minute/scope boundary",
      "owner": "Root independent implementation reviewer; owner business feedback separate",
      "decision": "Accept scoped technical flow, repair within authority or preserve owned remainder; no automatic SUP-02"
    }
  },
  "phase": "DISPATCH",
  "action": {
    "kind": "IMPLEMENT",
    "selected": [
      "S1-01",
      "S1-02",
      "S1-03",
      "S1-04"
    ],
    "owner": "Terra implementation and Sol browser workers; root review/commit",
    "output": "SUP-01 viewer and docs/reviews/SCST_SUP_01_EVIDENCE/",
    "budgetMinutes": 120,
    "stop": "Four criteria evidenced or budget/scope boundary without reset",
    "next": "Independent implementation review and usable local flow; SUP-02 requires its own SPEC/WORK_ORDER"
  },
  "rows": [
    {
      "id": "S1-01",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for S1-01",
      "owner": "Assigned workers and root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_01_REVIEW.md",
      "evidence": []
    },
    {
      "id": "S1-02",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for S1-02",
      "owner": "Assigned workers and root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_01_REVIEW.md",
      "evidence": []
    },
    {
      "id": "S1-03",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for S1-03",
      "owner": "Assigned workers and root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_01_REVIEW.md",
      "evidence": []
    },
    {
      "id": "S1-04",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for S1-04",
      "owner": "Assigned workers and root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_01_REVIEW.md",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Four SUP-01 criteria admitted for bounded implementation only",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "SUP-02/03, M2d/M3, live governance proof and business acceptance remain separate owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```
