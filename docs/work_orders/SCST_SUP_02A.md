# SCST — SUP-02A cargo revision work order

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

Owner on 04-11-2026 selected SUP-02 from the supplemental roadmap, made the GitHub repository private, authorized pushing the local main (573d7fb) and assigned implementation to Claude Cloud with Claude local as quality controller. Root split SUP-02 into SUP-02A (this order: cargo source revisions, provenance, plan revision pinning, recheck and rebase) and SUP-02B (generic vessel/profile contract, retained in the roadmap). SPEC docs/specs/SCST_SUP_02A.md binds D1-D8 and S2-01..S2-06. Core pin c4c8767 and gate profile 1.2 unchanged. Baseline 573d7fb: 104/104 backend tests; 36 browser cases per SUP-01 review.

Root (Claude local) is ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER, CLOSER, COMMIT_STEWARD and SESSION_SYNC_STEWARD. Claude Cloud is IMPLEMENTATION_WORKER on a non-main branch and returns through a pull request; it never merges or pushes to main. Roles are responsibilities, not provider requirements in the product. Reviewer is independent of the implementation session.

Worker ownership: services/backend/app/** (never services/backend/data/**), tests/backend/**, tests/browser/sup02a.spec.ts (new), apps/frontend/src/**, contracts/openapi.json (regenerated with tooling/export_contract.py) and apps/frontend/src/api/generated/api.ts (regenerated with npm run contract), plus docs/reviews/SCST_SUP_02A_EVIDENCE/worker-return.md. Root owns docs, CVF_SESSION, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, catalog, README and the merge decision.

Forbidden: services/backend/data/** (baltimore.json, profile.json, model.glb), raw VINAFCO handoff folders, runtime-data and any user SQLite file, .cvf/**, scripts/cvf_gates/**, .github/**, requirements files, package.json/package-lock.json, new dependencies, existing browser specs except an import or selector fix needed for regression and disclosed, secrets/API keys, provider or network calls from the product, CVF core, deployment and edits to closed packets or historical evidence.

Apply SCST-DA01 (exact µm/g, practical kg/cm/m display), DA02 (persistence change with isolated SCST_DATA_DIR tests, one-time backup, no reset on unknown schema), DA03 (sourced versus unconfirmed values, revision provenance), DA04 (reuse Plan, pipe registry, comparison, storage and frontend panels; add only missing parts) and DA05 (usable internal flow before owner feedback) explicitly in the worker return.

Implementation follows SPEC D1-D8. Validate revision binding in one shared service used by every Plan entry point (validate, save, open snapshot, compare, planner preview, pipe-list preview). Keep legacy contracts and stored snapshots byte-compatible. Write backend tests for each S2 criterion and limit, migration tests on a temporary SCST_DATA_DIR copy of a snapshots-only database, and tests/browser/sup02a.spec.ts for the S2-06 flow at desktop and 390px.

Worker verification: full backend pytest, contract and type regeneration, npm run build, the new browser spec and the existing browser suite when a browser is available, and python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return when the hidden core is available. If the cloud environment cannot run browsers or gates, record the exact command and error; never weaken, skip or edit a check. Worker return lists changed paths, commands with results, failed attempts, DA application, limitations and remaining owned work.

Budget: worker 240 minutes, root review 90 minutes, no reset on repair. Stop dependent work and report if scope, paths, risk, data sources or dependencies must expand. No automatic SUP-02B, SUP-03 or M2d.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_SUP_02A.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_SUP_02A.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_SUP_02A.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/sup02a.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/sup02a.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_SUP_02A.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | services/backend/app; tests/backend; tests/browser/sup02a.spec.ts; apps/frontend/src; contracts/openapi.json; docs/reviews/SCST_SUP_02A_EVIDENCE | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
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
    "path": "docs/specs/SCST_SUP_02A.md",
    "heading": "## SUP-02A acceptance",
    "sha256": "6b358a36f814dab611d459090d5ac23f632e7e6af33a6b4be5cee6a736003ff5"
  },
  "milestone": {
    "id": "SCST-SUP-02A",
    "consumer": "SCST owner and local tool user",
    "outcome": "Cargo data revisions with provenance, revision-pinned plans and visible recheck/rebase of affected plans",
    "checkpoint": {
      "trigger": "Six criteria evidenced in a pull request or the 240/90 minute or scope boundary",
      "owner": "Root independent implementation reviewer; owner business feedback and merge decision separate",
      "decision": "Accept scoped technical flow, repair within authority or return to worker; no automatic SUP-02B/SUP-03/M2d"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "S2-01",
      "S2-02",
      "S2-03",
      "S2-04",
      "S2-05",
      "S2-06"
    ],
    "owner": "Root independent implementation reviewer",
    "output": "docs/reviews/SCST_SUP_02A_REVIEW.md",
    "budgetMinutes": 240,
    "stop": "Six criteria evidenced or budget/scope boundary without reset",
    "next": "SUP-02A technical handoff; SUP-02B requires its own SPEC/WORK_ORDER; business acceptance separate"
  },
  "rows": [
    {
      "id": "S2-01",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_02A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_02A_REVIEW.md",
          "sha256": "b263150554cda7ba933086f81627d0565dfefee933c5a3bbe6b8a4b299a4a468"
        }
      ]
    },
    {
      "id": "S2-02",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_02A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_02A_REVIEW.md",
          "sha256": "b263150554cda7ba933086f81627d0565dfefee933c5a3bbe6b8a4b299a4a468"
        }
      ]
    },
    {
      "id": "S2-03",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_02A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_02A_REVIEW.md",
          "sha256": "b263150554cda7ba933086f81627d0565dfefee933c5a3bbe6b8a4b299a4a468"
        }
      ]
    },
    {
      "id": "S2-04",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_02A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_02A_REVIEW.md",
          "sha256": "b263150554cda7ba933086f81627d0565dfefee933c5a3bbe6b8a4b299a4a468"
        }
      ]
    },
    {
      "id": "S2-05",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_02A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_02A_REVIEW.md",
          "sha256": "b263150554cda7ba933086f81627d0565dfefee933c5a3bbe6b8a4b299a4a468"
        }
      ]
    },
    {
      "id": "S2-06",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_02A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_02A_REVIEW.md",
          "sha256": "b263150554cda7ba933086f81627d0565dfefee933c5a3bbe6b8a4b299a4a468"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "SUP-02A six technical criteria and usable local flow reviewed; merged as 569c7ee by owner decision",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_SUP_02A_REVIEW.md",
        "sha256": "b263150554cda7ba933086f81627d0565dfefee933c5a3bbe6b8a4b299a4a468"
      }
    ],
    "product": "PENDING",
    "productSummary": "SUP-02B, SUP-03, M2d/M3, live governance proof and business acceptance remain separate owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Technical disposition

Root independent implementation review accepts S2-01..06 on PR #1 head 4f91202, merged to main as 569c7ee by owner decision. Local rerun: backend 222/222, contract regeneration identical, build OK, full browser 39/39 on isolated port 8766, worker-return 7/7 and reviewer-fast 8/8 PASS. No blocking finding and no root repair. REVISION_UNAVAILABLE, conservative placed_affected and created provenance stamp accepted; observations O1-O5 recorded in the review as owned follow-up. No business acceptance, SUP-02B, SUP-03 or M2d.
