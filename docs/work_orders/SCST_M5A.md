# SCST — M5a local backup and restore work order

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

M3a closed on 05-11-2026 (review docs/reviews/SCST_M3A_REVIEW.md, merge 9a98cb8, closure f982225), and the multi-layer MVP goes to the owner for trial. Before the owner stores real work locally, root selects the data-independent M5 slice under the owner-delegated authority.

The slice has two parts:
- export a verified `scst.backup.v1` file (a consistent SQLite copy plus user vessel profiles);
- replace-all restore with full validation, an automatic pre-restore backup and atomic rollback on any failure.

SPEC docs/specs/SCST_M5A.md binds D1-D5 and M5A-01..M5A-05. Merge authority is owner-delegated to root. Core pin c4c8767 and gate profile 1.2 are unchanged. Baseline is main after the M3a closure: 734 backend tests, 55 browser cases, integration check 29/29.

Roles:
- Root (Claude local) is ORCHESTRATOR, SPEC_AUTHOR, WORK_ORDER_AUTHOR, independent REVIEWER, CLOSER, COMMIT_STEWARD and SESSION_SYNC_STEWARD.
- Claude Cloud is IMPLEMENTATION_WORKER on a non-main branch and returns through a pull request. It never merges or pushes to main.
- Roles are responsibilities, not provider requirements in the product. The reviewer is independent of the implementation session.

Worker ownership:
- services/backend/app/** (never services/backend/data/**);
- tests/backend/**;
- tests/browser/m5a.spec.ts (new);
- apps/frontend/src/**;
- contracts/openapi.json, regenerated with tooling/export_contract.py;
- apps/frontend/src/api/generated/api.ts, regenerated with npm run contract;
- docs/reviews/SCST_M5A_EVIDENCE/worker-return.md and small screenshots under docs/reviews/SCST_M5A_EVIDENCE/.

Root owns docs, CVF_SESSION, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, tooling, catalog, README and the merge decision.

Forbidden:
- data and local files: services/backend/data/**, raw VINAFCO handoff folders, runtime-data and any user SQLite or profile file;
- repository machinery: .cvf/**, scripts/cvf_gates/**, .github/**, tooling/**, requirements files, package.json/package-lock.json, new dependencies;
- existing tests and browser specs (no edits);
- changes to stored data formats, schemas, revision hashing or existing contract fields (additions only);
- secrets/API keys, provider or network calls from the product, CVF core, deployment;
- edits to closed packets or historical evidence.

Tests use a temporary SCST_DATA_DIR only.

The worker return must state explicitly how each DA control was applied:
- DA02: existing data is never lost or changed on failure, the round trip is byte-identical, and formats are unchanged.
- DA03: no scheduled backup, encryption or merge restore, stated in the UI and the worker return.
- DA04: reuse the storage schema check, Plan validation, the revision replay check, the vessel profile read checks and the profile store lock.
- DA05: a usable export/restore flow in the UI.

Implementation follows SPEC D1-D5. Required tests:
- backend tests for every D2 rejection case, the byte-identical round trip, fault injection at each D3.4 step, the pre-restore backup and cache freshness after restore;
- tests/browser/m5a.spec.ts for the M5A-05 flow at desktop and 390px.

Worker verification, never weakening, skipping or editing a check:
- full backend pytest;
- contract and type regeneration, then npm run build;
- the new browser spec and the full existing browser suite, then git status after the browser run;
- python tooling/integration_check_pre_m2d.py . (29/29);
- python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return.

Budget: worker 150 minutes, root review 60 minutes, no reset on repair. Commit and push reviewed work at every milestone. Stop dependent work and report if scope, paths, risk or dependencies must expand. No automatic M5b (installer) or scheduled backup.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M5A.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M5A.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_M5A.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m5a.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m5a.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M5A.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | services/backend/app; tests/backend; tests/browser/m5a.spec.ts; apps/frontend/src; contracts/openapi.json; docs/reviews/SCST_M5A_EVIDENCE | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
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
    "path": "docs/specs/SCST_M5A.md",
    "heading": "## M5a acceptance",
    "sha256": "e63b0e7d38f7d1fc474d20def81b969598acbc6de6bd07816201e22b07f245c6"
  },
  "milestone": {
    "id": "SCST-M5A",
    "consumer": "SCST owner and local tool user",
    "outcome": "Verified local backup export and replace-all restore with pre-restore backup and atomic rollback, usable from the UI",
    "checkpoint": {
      "trigger": "Five criteria evidenced in a pull request or the 150/60 minute or scope boundary",
      "owner": "Root independent implementation reviewer with owner-delegated merge authority",
      "decision": "Accept, repair within authority or return to worker; installer and scheduled backup stay separate"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "M5A-01",
      "M5A-02",
      "M5A-03",
      "M5A-04",
      "M5A-05"
    ],
    "owner": "Root independent implementation reviewer",
    "output": "docs/reviews/SCST_M5A_REVIEW.md",
    "budgetMinutes": 150,
    "stop": "Five criteria evidenced or budget/scope boundary without reset",
    "next": "Root independent review; owner MVP trial and feedback; installer M5b separate"
  },
  "rows": [
    {
      "id": "M5A-01",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5A_REVIEW.md",
          "sha256": "4bc545d375728697ba1245f3263dbbf0fcc96731afe0fa0b09609d0a2e39b5a8"
        }
      ]
    },
    {
      "id": "M5A-02",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5A_REVIEW.md",
          "sha256": "4bc545d375728697ba1245f3263dbbf0fcc96731afe0fa0b09609d0a2e39b5a8"
        }
      ]
    },
    {
      "id": "M5A-03",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5A_REVIEW.md",
          "sha256": "4bc545d375728697ba1245f3263dbbf0fcc96731afe0fa0b09609d0a2e39b5a8"
        }
      ]
    },
    {
      "id": "M5A-04",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5A_REVIEW.md",
          "sha256": "4bc545d375728697ba1245f3263dbbf0fcc96731afe0fa0b09609d0a2e39b5a8"
        }
      ]
    },
    {
      "id": "M5A-05",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5A_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5A_REVIEW.md",
          "sha256": "4bc545d375728697ba1245f3263dbbf0fcc96731afe0fa0b09609d0a2e39b5a8"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "M5a five technical criteria reviewed after one repair round; merged as 9c9cdb5 under owner-delegated merge authority",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_M5A_REVIEW.md",
        "sha256": "4bc545d375728697ba1245f3263dbbf0fcc96731afe0fa0b09609d0a2e39b5a8"
      }
    ],
    "product": "PENDING",
    "productSummary": "Installer, scheduled backup, encryption, merge restore and business acceptance remain owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Technical disposition

Root independent implementation review accepts M5A-01..05 on PR #7 (round 0 head 7475718; repair heads 2883456 and 9d34d3a: R1 path-free export error, R2 preview/apply in the threadpool, R3 Windows vessels/.lock in tests and cleanup of a created vessels dir, R4 platform-correct backslash test), merged to main as 9c9cdb5 under the owner-delegated merge authority. Local Windows rerun at 9d34d3a: backend 878/878, contract additive only, build OK, full browser 57/57, clean git status, integration check 29/29, worker-return and reviewer-fast gates PASS. Root NTFS probe in a data dir with spaces and Vietnamese characters: export, preview, refused restore with an open SQLite connection (rollback byte-identical), wrong confirm 409, real restore, multi-layer plan reopens with 1076 placements, pre-restore backup previews with all prior plans, no work directories left. Installer, scheduled backup, encryption, merge restore and business acceptance remain owned work.
