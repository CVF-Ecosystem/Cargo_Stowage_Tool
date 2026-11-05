# SCST — M5b automatic local backup work order

Status: CLOSED
dispatchKind: INITIAL
Owner: project-orchestrator
Risk: R2

## Authority and bounded work

M5a closed on 05-11-2026 (review docs/reviews/SCST_M5A_REVIEW.md, merge 9c9cdb5) and the MVP handoff docs are at f4c02fa. Root selects the next data-independent slice under the owner-delegated authority: automatic local backup. The app runs only while the owner has it open, so automatic means a backup at startup when the last automatic one is older than 20 hours (and only when data exists), plus a backup-now button, keeping at most 10 automatic files.

SPEC docs/specs/SCST_M5B.md binds D1-D4 and M5B-01..M5B-04. The installer is a separate M5c and is not part of this order. Merge authority is owner-delegated to root. Core pin c4c8767 and gate profile 1.2 are unchanged. Baseline is main at f4c02fa: 878 backend tests, 57 browser cases, integration check 29/29.

Roles:
- Root (Claude local) is ORCHESTRATOR, SPEC_AUTHOR, WORK_ORDER_AUTHOR, independent REVIEWER, CLOSER, COMMIT_STEWARD and SESSION_SYNC_STEWARD.
- Claude Cloud is IMPLEMENTATION_WORKER on a non-main branch and returns through a pull request. It never merges or pushes to main.
- Roles are responsibilities, not provider requirements in the product. The reviewer is independent of the implementation session.

Worker ownership:
- services/backend/app/** (never services/backend/data/**);
- tests/backend/**;
- tests/browser/m5b.spec.ts (new);
- apps/frontend/src/**;
- contracts/openapi.json, regenerated with tooling/export_contract.py;
- apps/frontend/src/api/generated/api.ts, regenerated with npm run contract;
- docs/reviews/SCST_M5B_EVIDENCE/worker-return.md and small screenshots under docs/reviews/SCST_M5B_EVIDENCE/.

Root owns docs, CVF_SESSION, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, tooling, catalog, README and the merge decision.

Forbidden:
- data and local files: services/backend/data/**, raw VINAFCO handoff folders, runtime-data and any user SQLite or profile file;
- repository machinery: .cvf/**, scripts/cvf_gates/**, .github/**, tooling/**, requirements files, package.json/package-lock.json, new dependencies;
- existing tests and browser specs (no edits);
- changes to stored data formats, schemas, revision hashing, the scst.backup.v1 format or existing contract fields (additions only);
- secrets/API keys, provider or network calls from the product, CVF core, deployment;
- edits to closed packets or historical evidence.

Tests use a temporary SCST_DATA_DIR only.

The worker return must state explicitly how each DA control was applied:
- DA02: existing data is never lost or changed, startup never fails because of a backup, formats unchanged.
- DA03: no background schedule while the app is closed, no encryption, no off-machine copy, stated in the UI and the worker return.
- DA04: reuse backup_export.write_archive, backup_check.check and the scst.backup.v1 format.
- DA05: a usable flow in the UI.

Implementation follows SPEC D1-D4. Required tests: every D1 branch (due, not due, no data, disabled, retention, protected files, failed new backup, no overwrite, concurrency), fault injection at startup, the byte-identical round trip through the M5a restore, API name validation and path-free responses, and tests/browser/m5b.spec.ts for the M5B-04 flow at desktop and 390px.

Windows matters because root reviews on Windows/NTFS: no colons in file names, no open SQLite connection while files are replaced or deleted, and test with a data directory whose path has spaces and Vietnamese characters.

Worker verification, never weakening, skipping or editing a check:
- full backend pytest;
- contract and type regeneration, then npm run build;
- the new browser spec and the full existing browser suite, then git status after the browser run;
- python tooling/integration_check_pre_m2d.py . (29/29);
- python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return.

Budget: worker 70 minutes, root review 45 minutes, no reset on repair. Commit and push reviewed work at every milestone. Stop dependent work and report if scope, paths or dependencies must expand. No automatic M5c installer.

## Gate-To-Role Closeability Contract


closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M5B.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M5B.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_M5B.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m5b.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | services/backend/app; tests/backend; tests/browser/m5b.spec.ts; apps/frontend/src; contracts/openapi.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M5B.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | services/backend/app; tests/backend; tests/browser/m5b.spec.ts; apps/frontend/src; contracts/openapi.json; docs/reviews/SCST_M5B_EVIDENCE | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
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
    "path": "docs/specs/SCST_M5B.md",
    "heading": "## M5b acceptance",
    "sha256": "10c52d80c3786f55c721bdd6c9937690014017e0889d05d10b1a6318d3894129"
  },
  "milestone": {
    "id": "SCST-M5B",
    "consumer": "SCST owner and local tool user",
    "outcome": "Automatic local backup at startup and on demand with retention, reusing the verified scst.backup.v1 format, usable from the UI",
    "checkpoint": {
      "trigger": "Four criteria evidenced in a pull request or the 70/45 minute or scope boundary",
      "owner": "Root independent implementation reviewer with owner-delegated merge authority",
      "decision": "Accept, repair within authority or return to worker; installer M5c stays separate"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "M5B-01",
      "M5B-02",
      "M5B-03",
      "M5B-04"
    ],
    "owner": "Root independent implementation reviewer",
    "output": "docs/reviews/SCST_M5B_REVIEW.md",
    "budgetMinutes": 70,
    "stop": "Four criteria evidenced or budget/scope boundary without reset",
    "next": "Root independent review; owner MVP trial and feedback; installer M5c separate"
  },
  "rows": [
    {
      "id": "M5B-01",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5B_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5B_REVIEW.md",
          "sha256": "019ccd1a9ffbeebd00ca3af7febeced1d682518c3a71ce1b3ecb94cd81de081e"
        }
      ]
    },
    {
      "id": "M5B-02",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5B_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5B_REVIEW.md",
          "sha256": "019ccd1a9ffbeebd00ca3af7febeced1d682518c3a71ce1b3ecb94cd81de081e"
        }
      ]
    },
    {
      "id": "M5B-03",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5B_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5B_REVIEW.md",
          "sha256": "019ccd1a9ffbeebd00ca3af7febeced1d682518c3a71ce1b3ecb94cd81de081e"
        }
      ]
    },
    {
      "id": "M5B-04",
      "state": "VERIFIED",
      "gap": "Technical criterion and internally exercised flow verified; business acceptance separate",
      "owner": "Root independent implementation reviewer",
      "destination": "docs/reviews/SCST_M5B_REVIEW.md",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M5B_REVIEW.md",
          "sha256": "019ccd1a9ffbeebd00ca3af7febeced1d682518c3a71ce1b3ecb94cd81de081e"
        }
      ]
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "M5b four technical criteria reviewed with no repair round; merged as 23a9395 under owner-delegated merge authority",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_M5B_REVIEW.md",
        "sha256": "019ccd1a9ffbeebd00ca3af7febeced1d682518c3a71ce1b3ecb94cd81de081e"
      }
    ],
    "product": "PENDING",
    "productSummary": "Installer, background schedule while the app is closed, encryption, off-machine copy and business acceptance remain owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Technical disposition

Root independent implementation review accepts M5B-01..04 on PR #8 (head debafa6, no repair round), merged to main as 23a9395 under the owner-delegated merge authority. Local Windows rerun: backend 909/909, contract additive only, build OK, full browser 59/59, clean git status, integration check 29/29, worker-return and reviewer-fast gates PASS. Root NTFS probe in a data dir with spaces and Vietnamese characters: no files created at startup without data, run-now 409 without data, valid colon-free auto files that pass the M5a preview, six traversal or wrong-pattern names return 404, retention keeps exactly 10 and never deletes pre-restore or foreign files, restore from an auto file works, startup hook creates one file and none on the second start, SCST_AUTO_BACKUP=0 disables it. Installer, background schedule while the app is closed, encryption, off-machine copy and business acceptance remain owned work.
