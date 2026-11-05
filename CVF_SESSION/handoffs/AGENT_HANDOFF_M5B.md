# SCST — M5b automatic local backup

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: FREEZE
- Active phase: FREEZE
- Active role: SESSION_SYNC_STEWARD
- Next allowed move: M5b closed technically: automatic local backup at startup and on demand is available. The MVP (multi-layer stacking plus manual and automatic backup/restore) is with the owner for trial and feedback. M3b needs owner hold measurements, real cases and stack-load data; the M5c installer is separate local work; M4 AI needs an owner decision (docs/SCST_M4_PROPOSAL.md).
- Parked operator checkpoint: M3b real cases and measured hold, stack and tanktop load, lashing and stability, M5c installer, background schedule while the app is closed, encryption, off-machine backup copy, M4 AI (owner decision), observations O7-O11, O-M3A-2/3, O-M5A-1/2 and O-M5B-1/2, hook/hosted-CI adoption, live-provider governance proof, 16 source envelopes and business acceptance remain owned future work.
- Active tranche: M5B

## Intake, design and authority acknowledgment

M5a closed at 53233f8 and the MVP handoff docs are at f4c02fa. The owner asked to continue with the remaining roadmap and to delegate to the cloud. The remaining cloud credit was about 1 hour 45 minutes at admission, so root chose the slice that fits: automatic local backup, which needs no owner data. The installer needs a Windows run to verify, so it was split off as M5c and stays local.

Root bound M5b in SPEC docs/specs/SCST_M5B.md (D1-D4, M5B-01..M5B-04):

- a backup at app startup when the last automatic one is older than 20 hours and data exists, never blocking or failing startup;
- a backup-now button;
- at most 10 automatic files, never deleting manual or pre-restore backups;
- list, run and download endpoints that return file names only;
- the UI block.

WORK_ORDER_AUTHOR wrote docs/work_orders/SCST_M5B.md. Coverage authority is registered as SCST-M5B.

## Baseline and preserved source

Baseline is main at f4c02fa: backend 878, browser 57, integration check 29/29.

Preserve:

- services/backend/data/**;
- stored formats, schemas and the scst.backup.v1 format;
- revision hashes;
- the user SQLite file and live 8765;
- the gate kit, CI and historical evidence.

## Remainder and return

Expected return: one pull request from Claude Cloud with source, tests, regenerated contract/types and docs/reviews/SCST_M5B_EVIDENCE/worker-return.md.

Root then becomes REVIEWER and:

- reruns everything on Windows, with a data directory containing spaces and Vietnamese characters;
- writes docs/reviews/SCST_M5B_REVIEW.md;
- merges under delegated authority if it passes;
- reports to the owner.

## Review and closure

Claude Cloud returned PR #8 (head debafa6) 30 minutes after dispatch. Root REVIEWER reran on Windows: backend 909, browser 59, integration check 29/29, gates PASS, plus an NTFS probe in a data directory with spaces and Vietnamese characters (startup without data creates nothing; retention keeps exactly 10; traversal names 404; restore from an auto file; startup hook creates one file). No repair round was needed. Review docs/reviews/SCST_M5B_REVIEW.md accepts M5B-01..04; root merged PR #8 as 23a9395 under owner-delegated authority, closed the work order and synced continuity.
