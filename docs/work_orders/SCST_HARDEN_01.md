# SCST — HARDEN-01 hardening work order

Status: ACTIVE
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

On 05-11-2026 (~02:50 +7) the owner delegated GitHub merge authority to root as orchestrator after independent review and asked root to coordinate the next session. M3 needs owner hold measurements and real cases, so root selected a data-independent hardening tranche from observations recorded in the SUP-02A, SUP-02B and SUP-03 reviews. SPEC docs/specs/SCST_HARDEN_01.md binds H1-H6 and H-01..H-05. Core pin c4c8767 and gate profile 1.2 unchanged. Baseline main 268ff35 (after M2d): 650 backend tests, 50 browser cases, integration check 29/29.

Root (Claude local) is ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER, CLOSER, COMMIT_STEWARD and SESSION_SYNC_STEWARD. Claude Cloud is IMPLEMENTATION_WORKER on a non-main branch and returns through a pull request; it never merges or pushes to main. Roles are responsibilities, not provider requirements in the product. Reviewer is independent of the implementation session.

Worker ownership: services/backend/app/** (never services/backend/data/**), tests/backend/**, tests/browser/harden01.spec.ts (new), apps/frontend/src/**, contracts/openapi.json (regenerated with tooling/export_contract.py) and apps/frontend/src/api/generated/api.ts (regenerated with npm run contract), plus docs/reviews/SCST_HARDEN_01_EVIDENCE/worker-return.md. Root owns docs, CVF_SESSION, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, tooling, catalog, README and the merge decision.

Forbidden: services/backend/data/**, raw VINAFCO handoff folders, runtime-data and any user SQLite or profile file, .cvf/**, scripts/cvf_gates/**, .github/**, requirements files, package.json/package-lock.json, new dependencies, existing browser specs and existing tests (no edits; integrity tests must pass unchanged), changes to stored data formats, revision hashing or existing contract fields (additions only), secrets/API keys, provider or network calls from the product, CVF core, deployment and edits to closed packets or historical evidence.

Apply SCST-DA01 (exact integers), DA02 (no storage format change, isolated SCST_DATA_DIR tests, no reset), DA03 (labels match data meaning), DA04 (local fixes, no rewrites) and DA05 (usable flow) explicitly in the worker return.

Implementation follows SPEC H1-H6. Write backend tests for H-02..H-05 including a two-process lock test, and tests/browser/harden01.spec.ts for H-01 and the H-02 labels at desktop and 390px.

Worker verification: full backend pytest, contract and type regeneration, npm run build, the new browser spec and the full existing browser suite, git status after the browser run, python tooling/integration_check_pre_m2d.py . (must stay 29/29), and python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return. Record timing before/after for H3. Never weaken, skip or edit a check.

Budget: worker 180 minutes, root review 60 minutes, no reset on repair. Commit and push reviewed work at every milestone. Stop dependent work and report if scope, paths, risk or dependencies must expand. No automatic M3.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_HARDEN_01.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_HARDEN_01.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_HARDEN_01.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/harden01.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/harden01.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_HARDEN_01.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | services/backend/app; tests/backend; tests/browser/harden01.spec.ts; apps/frontend/src; contracts/openapi.json; docs/reviews/SCST_HARDEN_01_EVIDENCE | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
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
    "path": "docs/specs/SCST_HARDEN_01.md",
    "heading": "## HARDEN-01 acceptance",
    "sha256": "e2adaffe33dfcb8badddf784129858e098a0bba94bc49669687d2d3660e2aa5d"
  },
  "milestone": {
    "id": "SCST-HARDEN-01",
    "consumer": "SCST owner and local tool user",
    "outcome": "Paged rebase drops, clear recheck counts, cached replay, pre-parse size limits and cross-process profile locking",
    "checkpoint": {
      "trigger": "Five criteria evidenced in a pull request or the 180/60 minute or scope boundary",
      "owner": "Root independent implementation reviewer with owner-delegated merge authority",
      "decision": "Accept, repair within authority or return to worker; M3 needs owner data"
    }
  },
  "phase": "DISPATCH",
  "action": {
    "kind": "IMPLEMENT",
    "selected": [
      "H-01",
      "H-02",
      "H-03",
      "H-04",
      "H-05"
    ],
    "owner": "Claude Cloud implementation worker on a branch; root independent review and commit steward",
    "output": "HARDEN-01 source, tests, regenerated contract and docs/reviews/SCST_HARDEN_01_EVIDENCE/worker-return.md in a pull request",
    "budgetMinutes": 180,
    "stop": "Five criteria evidenced or budget/scope boundary without reset",
    "next": "Root independent review; M3 requires owner hold measurements, real cases and its own SPEC/WORK_ORDER"
  },
  "rows": [
    {
      "id": "H-01",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for H-01",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_HARDEN_01_REVIEW.md",
      "evidence": []
    },
    {
      "id": "H-02",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for H-02",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_HARDEN_01_REVIEW.md",
      "evidence": []
    },
    {
      "id": "H-03",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for H-03",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_HARDEN_01_REVIEW.md",
      "evidence": []
    },
    {
      "id": "H-04",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for H-04",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_HARDEN_01_REVIEW.md",
      "evidence": []
    },
    {
      "id": "H-05",
      "state": "NOT_STARTED",
      "gap": "Implementation and exact-version product flow evidence required for H-05",
      "owner": "Claude Cloud implementation worker and root independent reviewer",
      "destination": "docs/reviews/SCST_HARDEN_01_REVIEW.md",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Five HARDEN-01 criteria admitted for bounded implementation only",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "M3 multi-layer and real cases, measured hold/packing and business acceptance remain separate owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```
