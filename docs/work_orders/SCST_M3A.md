# SCST — M3a multi-layer column stacking work order

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

On 05-11-2026 the owner confirmed the M2d XLSX opens without errors and restated the rule that the development team must deliver a usable Prototype/MVP before waiting for user feedback. The pre-M2d integration check showed the single-layer planner places only 167/1076 Baltimore bundles in the VINAFCO hold (floor area, not mass, is the limit). Root therefore selected M3a: multi-layer column stacking with support checks on the estimated hold, labelled unverified, while M3b (real cases, measured hold, stack load) stays with the owner. SPEC docs/specs/SCST_M3A.md binds D1-D5 and M3A-01..M3A-05 and records two root technical decisions (OD-only revisions stay CURRENT; provenance stays outside the revision hash). Merge authority is owner-delegated to root. Core pin c4c8767 and gate profile 1.2 unchanged. Baseline main 07c6e85: 679 backend tests, 52 browser cases, integration check 29/29.

Root (Claude local) is ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER, CLOSER, COMMIT_STEWARD and SESSION_SYNC_STEWARD. Claude Cloud is IMPLEMENTATION_WORKER on a non-main branch and returns through a pull request; it never merges or pushes to main. Roles are responsibilities, not provider requirements in the product. Reviewer is independent of the implementation session.

Worker ownership: services/backend/app/** (never services/backend/data/**), tests/backend/**, tests/browser/m3a.spec.ts (new), apps/frontend/src/**, contracts/openapi.json (regenerated with tooling/export_contract.py) and apps/frontend/src/api/generated/api.ts (regenerated with npm run contract), plus docs/reviews/SCST_M3A_EVIDENCE/worker-return.md and small screenshots under docs/reviews/SCST_M3A_EVIDENCE/. Root owns docs, CVF_SESSION, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, tooling, catalog, README and the merge decision.

Forbidden: services/backend/data/**, raw VINAFCO handoff folders, runtime-data and any user SQLite or profile file, .cvf/**, scripts/cvf_gates/**, .github/**, tooling/**, requirements files, package.json/package-lock.json, new dependencies, existing tests and browser specs (no edits), changes to stored data formats, revision hashing or existing contract fields (additions only), secrets/API keys, provider or network calls from the product, CVF core, deployment and edits to closed packets or historical evidence.

Apply SCST-DA01 (integer mm placement, exact um geometry and um2 support area), DA02 (legacy plans and snapshots byte-identical, isolated SCST_DATA_DIR tests), DA03 (unchecked stack load, tanktop load, lashing and stability stated in checks and report), DA04 (reuse Placement z/layer/supported_by, rules, planner flow, viewer and report) and DA05 (usable flow before owner feedback) explicitly in the worker return.

Implementation follows SPEC D1-D5. Write backend tests for each rule code (positive and negative), determinism and the Baltimore/VINAFCO placement count, and tests/browser/m3a.spec.ts for the M3A-05 flow at desktop and 390px.

Worker verification: full backend pytest, contract and type regeneration, npm run build, the new browser spec and the full existing browser suite, git status after the browser run, python tooling/integration_check_pre_m2d.py . (29/29), planner timing for 1076 bundles, and python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return. Never weaken, skip or edit a check.

Budget: worker 240 minutes, root review 90 minutes, no reset on repair. Commit and push reviewed work at every milestone. Stop dependent work and report if scope, paths, risk or dependencies must expand. No automatic M3b.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M3A.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M3A.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_M3A.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m3a.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m3a.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M3A.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | services/backend/app; tests/backend; tests/browser/m3a.spec.ts; apps/frontend/src; contracts/openapi.json; docs/reviews/SCST_M3A_EVIDENCE | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
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
    "path": "docs/specs/SCST_M3A.md",
    "heading": "## M3a acceptance",
    "sha256": "bdd445031d387858da491e50c34eabfedaf95d4666112cd7403fc3d4eaf4f6c8"
  },
  "milestone": {
    "id": "SCST-M3A",
    "consumer": "SCST owner and local tool user",
    "outcome": "Multi-layer column stacking with support checks, planner, viewer and report on the estimated hold as a usable MVP",
    "checkpoint": {
      "trigger": "Five criteria evidenced in a pull request or the 240/90 minute or scope boundary",
      "owner": "Root independent implementation reviewer with owner-delegated merge authority",
      "decision": "Accept, repair within authority or return to worker; M3b real cases and measured hold stay with the owner"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "M3A-01",
      "M3A-02",
      "M3A-03",
      "M3A-04",
      "M3A-05"
    ],
    "owner": "Root independent implementation reviewer",
    "output": "docs/reviews/SCST_M3A_REVIEW.md",
    "budgetMinutes": 240,
    "stop": "Five criteria evidenced or budget/scope boundary without reset",
    "next": "Root independent review; owner MVP feedback; M3b needs owner data"
  },
  "rows": [
    {
      "id": "M3A-01",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M3A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M3A_REVIEW.md",
          "sha256": "d8eb606af502679cf90b3c937dd8bee2fadd14107345a68b9a9e5b77eed6c33e"
        }
      ]
    },
    {
      "id": "M3A-02",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M3A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M3A_REVIEW.md",
          "sha256": "d8eb606af502679cf90b3c937dd8bee2fadd14107345a68b9a9e5b77eed6c33e"
        }
      ]
    },
    {
      "id": "M3A-03",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M3A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M3A_REVIEW.md",
          "sha256": "d8eb606af502679cf90b3c937dd8bee2fadd14107345a68b9a9e5b77eed6c33e"
        }
      ]
    },
    {
      "id": "M3A-04",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M3A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M3A_REVIEW.md",
          "sha256": "d8eb606af502679cf90b3c937dd8bee2fadd14107345a68b9a9e5b77eed6c33e"
        }
      ]
    },
    {
      "id": "M3A-05",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M3A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M3A_REVIEW.md",
          "sha256": "d8eb606af502679cf90b3c937dd8bee2fadd14107345a68b9a9e5b77eed6c33e"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "M3a five technical criteria reviewed after one repair round; merged as 9a98cb8 under owner-delegated merge authority",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_M3A_REVIEW.md",
        "sha256": "d8eb606af502679cf90b3c937dd8bee2fadd14107345a68b9a9e5b77eed6c33e"
      }
    ],
    "product": "PENDING",
    "productSummary": "M3b real cases, measured hold, stack and tanktop load, lashing, stability and business acceptance remain owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Technical disposition

Root independent implementation review accepts M3A-01..05 on PR #6 (round 0 head 8d205ef, repair round 1 head 1f8c26e: R1 pipe-list multi-layer default with five root-authorized one-line selects in existing specs, R2 case voyage limit on switch, R3 x-sweep overlap pass kept after review), merged to main as 9a98cb8 under the owner-delegated merge authority. Local Windows rerun at 1f8c26e: backend 734/734, contract additive only, build OK, full browser 55/55, clean git status, integration check 29/29, worker-return and reviewer-fast gates PASS. Baltimore/VINAFCO VR-SII columns-v1 places 1076/1076 (98 columns, 18 layers, 0 issues, 0.05 s). Root decisions: D2.1 level rule rounds the support top up to the mm grid; rebase cascades SUPPORT_LOST. Stack/tanktop load, lashing, stability, M3b and business acceptance remain owned work.
