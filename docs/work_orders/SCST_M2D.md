# SCST — M2d plan report export work order

Status: ACTIVE
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

M2d is the last part of M2 in the main roadmap (export PDF/XLSX; table, 3D and report data agree). The pre-M2d integration checkpoint docs/reviews/SCST_INTEGRATION_CHECK_PRE_M2D.md passed 29/29 on 05-11-2026 with no blocker. The owner instructed root to continue the roadmap without waiting for questions and reviews before every merge. SPEC docs/specs/SCST_M2D.md binds D1-D5 and M2D-01..M2D-05. Core pin c4c8767 and gate profile 1.2 unchanged. Baseline main e73c876: 597 backend tests, 46 browser cases.

Root (Claude local) is ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER, CLOSER, COMMIT_STEWARD and SESSION_SYNC_STEWARD. Claude Cloud is IMPLEMENTATION_WORKER on a non-main branch and returns through a pull request; it never merges or pushes to main. Roles are responsibilities, not provider requirements in the product. Reviewer is independent of the implementation session.

Worker ownership: services/backend/app/** (never services/backend/data/**), tests/backend/**, tests/browser/m2d.spec.ts (new), apps/frontend/src/**, contracts/openapi.json (regenerated with tooling/export_contract.py) and apps/frontend/src/api/generated/api.ts (regenerated with npm run contract), plus docs/reviews/SCST_M2D_EVIDENCE/worker-return.md and small evidence files (screenshots, one sample XLSX and one sample PDF from the test database) under docs/reviews/SCST_M2D_EVIDENCE/. Root owns docs, CVF_SESSION, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, catalog, README and the merge decision.

Forbidden: services/backend/data/**, raw VINAFCO handoff folders, runtime-data and any user SQLite or profile file, .cvf/**, scripts/cvf_gates/**, .github/**, requirements files, package.json/package-lock.json, new dependencies (no openpyxl, xlsxwriter, reportlab, jsPDF or similar), server-side PDF generation, existing browser specs (no edits), changes to stored snapshot JSON, revision hashing or Plan contracts, secrets/API keys, provider or network calls from the product, CVF core, deployment and edits to closed packets or historical evidence.

Apply SCST-DA01 (exact integer g/mm/um columns beside practical kg/cm/m/t display), DA02 (read-only export, isolated SCST_DATA_DIR tests), DA03 (mandatory notices: geometry not verified, single-layer plan, derived packing, recheck needed, source warnings), DA04 (reuse Evaluation, rules, recheck, packing and the existing viewer for the 3D image; add only missing parts) and DA05 (usable internal flow before owner feedback) explicitly in the worker return.

Implementation follows SPEC D1-D5. One shared report model feeds the JSON endpoint, the XLSX writer and the printable page; the frontend never recomputes report numbers. XLSX is deterministic and written with zipfile and XML from the standard library. Write backend tests for each M2D criterion, and tests/browser/m2d.spec.ts for the M2D-05 flow including page.pdf() on Chromium.

Worker verification: full backend pytest, contract and type regeneration, npm run build, the new browser spec and the full existing browser suite when a browser is available, git status after the full browser run (no committed file under docs/reviews changed), and python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return. If the cloud environment cannot run browsers or gates, record the exact command and error; never weaken, skip or edit a check. Worker return lists changed paths, commands with results, XLSX/PDF evidence, timing for 1076 and 2000 units, failed attempts, DA application, limitations and remaining owned work.

Budget: worker 240 minutes, root review 90 minutes, no reset on repair. Commit and push reviewed work at every milestone. Stop dependent work and report if scope, paths, risk, data sources or dependencies must expand. No automatic M3.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2D.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M2D.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_M2D.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m2d.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m2d.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M2D.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | services/backend/app; tests/backend; tests/browser/m2d.spec.ts; apps/frontend/src; contracts/openapi.json; docs/reviews/SCST_M2D_EVIDENCE | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
| reviewer_fast | REVIEW | reviewer | REVIEW | services/backend/app; tests/backend; tests/browser; apps/frontend/src; contracts/openapi.json; README.md | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | worker_return_fast |
| pre_commit | PRE_MATERIAL_COMMIT | commit-steward | PRE_MATERIAL_COMMIT | docs; CVF_SESSION; IMPLEMENTATION_STATUS.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | reviewer_fast |
| terminal_completion_review | POST_MATERIAL | reviewer | REVIEW | docs/work_orders | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | pre_commit |
| continuity | CONTINUITY_COMMIT | session-sync-steward | CONTINUITY_COMMIT | CVF_SESSION; CVF_SESSION_MEMORY.md; IMPLEMENTATION_STATUS.json; docs/catalog | BOUNDED_PATH_FAMILIES | session-sync-steward | CONTINUITY_COMMIT | terminal_completion_review |
| committed_range_closure | POST_MATERIAL_CLOSURE | commit-steward | POST_MATERIAL_CLOSURE | docs/work_orders; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | CORRECTIVE_MATERIAL_COMMIT | continuity |

## Milestone coverage

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/specs/SCST_M2D.md",
    "heading": "## M2d acceptance",
    "sha256": "76def98aa07e6d6c3dc00d993e6358610cd447ca9f23a986dc1b4b9d084b0b18"
  },
  "milestone": {
    "id": "SCST-M2D",
    "consumer": "SCST owner and local tool user",
    "outcome": "Saved plans export to a shared report model, deterministic XLSX and a printable A4 page with mandatory data-status notices",
    "checkpoint": {
      "trigger": "Five criteria evidenced in a pull request or the 240/90 minute or scope boundary",
      "owner": "Root independent implementation reviewer; owner business feedback and merge decision separate",
      "decision": "Accept scoped technical flow, repair within authority or return to worker; M3 needs owner data and its own SPEC"
    }
  },
  "phase": "DISPATCH",
  "action": {
    "kind": "IMPLEMENT",
    "selected": [
      "M2D-01",
      "M2D-02",
      "M2D-03",
      "M2D-04",
      "M2D-05"
    ],
    "owner": "Claude Cloud implementation worker on a branch; root independent review and commit steward",
    "output": "M2d source, tests, regenerated contract and docs/reviews/SCST_M2D_EVIDENCE/worker-return.md in a pull request",
    "budgetMinutes": 240,
    "stop": "Five criteria evidenced or budget/scope boundary without reset",
    "next": "Root independent review; M3 requires owner hold measurements, real cases and its own SPEC/WORK_ORDER"
  },
  "rows": [
    {
      "id": "M2D-01",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for M2D-01",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_M2D_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2D-02",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for M2D-02",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_M2D_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2D-03",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for M2D-03",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_M2D_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2D-04",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for M2D-04",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_M2D_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M2D-05",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for M2D-05",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_M2D_REVIEW.md",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Five M2d criteria admitted for bounded implementation only",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "M3 multi-layer and real cases, measured hold/packing, live governance proof and business acceptance remain separate owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```
