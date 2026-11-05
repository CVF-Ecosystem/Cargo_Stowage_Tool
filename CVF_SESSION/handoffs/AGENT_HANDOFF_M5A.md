# SCST — M5a local backup and restore

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: BUILD
- Active phase: BUILD
- Active role: ORCHESTRATOR
- Next allowed move: Claude Cloud implements M5a on a non-main branch and opens a pull request; root reviews independently and merges under owner-delegated authority. In parallel the owner trials the M3a MVP. M3b needs owner hold measurements, real cases and stack-load data.
- Parked operator checkpoint: M3b real cases and measured hold, stack and tanktop load, lashing and stability, M5b installer, scheduled backup, M4, observations O7-O11 and O-M3A-2/3, hook/hosted-CI adoption, live-provider governance proof, 16 source envelopes and business acceptance remain owned future work.
- Active tranche: M5A

## Intake, design and authority acknowledgment

M3a closed at f982225: PR #6 was merged as 9a98cb8 after one repair round, and the multi-layer MVP places 1076/1076 Baltimore bundles. The MVP goes to the owner for trial.

Root re-assessed the data-independent remainder. The largest risk once the owner stores real work locally is losing it, because there is no export or restore today. Root selected the M5 backup/restore slice under owner-delegated authority and bound it in SPEC docs/specs/SCST_M5A.md (D1-D5, M5A-01..M5A-05):

- a verified `scst.backup.v1` export: a consistent SQLite copy plus user vessel profiles;
- a read-only restore preview with zip-slip, zip-bomb, hash, schema, plan, revision and profile checks;
- replace-all restore with a pre-restore backup and atomic rollback;
- the UI flow.

WORK_ORDER_AUTHOR wrote docs/work_orders/SCST_M5A.md. Coverage authority is registered as SCST-M5A.

## Baseline and preserved source

Baseline is main after the M3a closure: backend 734, browser 55, integration check 29/29.

Preserve:

- services/backend/data/**;
- stored formats and schemas;
- revision hashes;
- the user SQLite file and live 8765;
- the gate kit, CI and historical evidence.

## Remainder and return

Expected return: one pull request from Claude Cloud with source, tests, regenerated contract/types and docs/reviews/SCST_M5A_EVIDENCE/worker-return.md.

Root then becomes REVIEWER and:

- reruns everything on Windows, including real NTFS replacement;
- writes docs/reviews/SCST_M5A_REVIEW.md;
- merges under delegated authority if it passes;
- reports to the owner.
