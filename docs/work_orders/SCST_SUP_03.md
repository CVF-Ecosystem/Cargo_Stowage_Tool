# SCST — SUP-03 derived bundle and pipe views work order

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

Owner on 04-11-2026 asked root to prepare a longer-horizon spec so the cloud worker continues overnight, with owner review on 05-11 before any merge. Root selected SUP-03, the last item of the supplemental roadmap (envelope, simplified bundle and detailed pipe views of one entity; derived packing with source status; envelope fallback with warnings). SPEC docs/specs/SCST_SUP_03.md binds D1-D6 and S3-01..S3-05. SUP-03 is stacked on SUP-02B: the worker branches from the head of claude/sup-02b-vessel-profile and opens its pull request against that branch; merge order is SUP-02B then SUP-03 after owner review. Core pin c4c8767 and gate profile 1.2 unchanged.

Root (Claude local) is ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, independent REVIEWER, CLOSER, COMMIT_STEWARD and SESSION_SYNC_STEWARD. Claude Cloud is IMPLEMENTATION_WORKER on a non-main branch and returns through a pull request; it never merges or pushes to main or to the SUP-02B branch. Roles are responsibilities, not provider requirements in the product. Reviewer is independent of the implementation session.

Worker ownership: services/backend/app/** (never services/backend/data/**), tests/backend/**, tests/browser/sup03.spec.ts (new), apps/frontend/src/**, contracts/openapi.json (regenerated with tooling/export_contract.py) and apps/frontend/src/api/generated/api.ts (regenerated with npm run contract), plus docs/reviews/SCST_SUP_03_EVIDENCE/worker-return.md and small screenshots under docs/reviews/SCST_SUP_03_EVIDENCE/browser. Root owns docs, CVF_SESSION, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, catalog, README and the merge decision.

Forbidden: services/backend/data/**, raw VINAFCO handoff folders, runtime-data and any user SQLite or profile file, .cvf/**, scripts/cvf_gates/**, .github/**, requirements files, package.json/package-lock.json, new dependencies, existing browser specs (no edits), changes to SUP-02A revision change types or hashed group fields, secrets/API keys, provider or network calls from the product, CVF core, deployment and edits to closed packets or historical evidence.

Apply SCST-DA01 (exact integer µm/mm, OD decimal string converted exactly, practical cm display), DA02 (no persistence change), DA03 (derived packing labelled DERIVED with reasons, never presented as measured), DA04 (reuse revisions, derive_units, Scene lifecycle, InstancedMesh, display modes and tables; add only missing parts) and DA05 (usable internal flow before owner feedback) explicitly in the worker return.

Implementation follows SPEC D1-D6. Packing is a read-only view keyed by revision and group; Plan and snapshot JSON stay byte-identical. Write backend tests for each S3 criterion and reason code, and tests/browser/sup03.spec.ts for the S3-05 flow at desktop and 390px, including picking in detailed view and the 60 000 instance budget message.

Worker verification: full backend pytest, contract and type regeneration, npm run build, the new browser spec and the full existing browser suite when a browser is available, git status after the full browser run (no committed file under docs/reviews changed), and python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return. If the cloud environment cannot run browsers or gates, record the exact command and error; never weaken, skip or edit a check. Worker return lists changed paths, commands with results, the 31-group Baltimore packing table, build timing for 1076 bundles, failed attempts, DA application, limitations and remaining owned work.

Budget: worker 240 minutes, root review 90 minutes, no reset on repair. Stop dependent work and report if scope, paths, risk, data sources or dependencies must expand. No automatic M2d or M3.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_SUP_03.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_SUP_03.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_SUP_02B.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/sup03.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/sup03.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_SUP_03.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | services/backend/app; tests/backend; tests/browser/sup03.spec.ts; apps/frontend/src; contracts/openapi.json; docs/reviews/SCST_SUP_03_EVIDENCE | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
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
    "path": "docs/specs/SCST_SUP_03.md",
    "heading": "## SUP-03 acceptance",
    "sha256": "47b0a53461fe47f9c1d033b2290c4dc26354825e2d33cebf3a7dfd6d751b3a7b"
  },
  "milestone": {
    "id": "SCST-SUP-03",
    "consumer": "SCST owner and local tool user",
    "outcome": "Envelope, simplified bundle and detailed pipe views of one entity with derived packing, checks and envelope fallback",
    "checkpoint": {
      "trigger": "Five criteria evidenced in a pull request or the 240/90 minute or scope boundary",
      "owner": "Root independent implementation reviewer; owner business feedback and merge decision separate",
      "decision": "Accept scoped technical flow, repair within authority or return to worker; then integration check before M2d"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "S3-01",
      "S3-02",
      "S3-03",
      "S3-04",
      "S3-05"
    ],
    "owner": "Root independent implementation reviewer",
    "output": "docs/reviews/SCST_SUP_03_REVIEW.md",
    "budgetMinutes": 240,
    "stop": "Five criteria evidenced or budget/scope boundary without reset",
    "next": "Root independent review, then integration check before M2d; M2d requires its own SPEC/WORK_ORDER"
  },
  "rows": [
    {
      "id": "S3-01",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_03_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_03_REVIEW.md",
          "sha256": "3d47c00630bebcd774e933b5e45c674db990c9feb36705fbe75ec6ee416cd8f1"
        }
      ]
    },
    {
      "id": "S3-02",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_03_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_03_REVIEW.md",
          "sha256": "3d47c00630bebcd774e933b5e45c674db990c9feb36705fbe75ec6ee416cd8f1"
        }
      ]
    },
    {
      "id": "S3-03",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_03_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_03_REVIEW.md",
          "sha256": "3d47c00630bebcd774e933b5e45c674db990c9feb36705fbe75ec6ee416cd8f1"
        }
      ]
    },
    {
      "id": "S3-04",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_03_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_03_REVIEW.md",
          "sha256": "3d47c00630bebcd774e933b5e45c674db990c9feb36705fbe75ec6ee416cd8f1"
        }
      ]
    },
    {
      "id": "S3-05",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business/domain acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_SUP_03_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_SUP_03_REVIEW.md",
          "sha256": "3d47c00630bebcd774e933b5e45c674db990c9feb36705fbe75ec6ee416cd8f1"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "SUP-03 five technical criteria and usable local flow reviewed; merged as 164dce5 by owner decision",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_SUP_03_REVIEW.md",
        "sha256": "3d47c00630bebcd774e933b5e45c674db990c9feb36705fbe75ec6ee416cd8f1"
      }
    ],
    "product": "PENDING",
    "productSummary": "M2d/M3, measured packing and hold, live governance proof and business acceptance remain separate owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Technical disposition

Root independent implementation review accepts S3-01..05 on PR #3 (head 0d8bdff, stacked on SUP-02B, retargeted to main with merged tree equal to the tested tree e66c2cc), merged to main as 164dce5 by owner decision on 05-11. Local Windows rerun: backend 597/597, contract identical, build OK, full browser 46/46 on isolated port 8766 with clean git status, worker-return and reviewer-fast PASS. R0000: 28/31 groups DETAILED, 3 groups (16 bundles) ENVELOPE_ONLY exactly matching the source-flagged envelope conflicts. OD-only revisions not triggering recheck accepted as SPEC interpretation; O8-O9 recorded. No business acceptance, measured packing or M2d.
