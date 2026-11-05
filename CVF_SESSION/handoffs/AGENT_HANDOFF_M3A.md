# SCST — M3a multi-layer column stacking MVP

Status: SUPERSEDED

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: FREEZE
- Active phase: FREEZE
- Active role: SESSION_SYNC_STEWARD
- Next allowed move: M3a closed technically: the MVP (multi-layer column stacking, 1076/1076 Baltimore bundles on the estimated VINAFCO hold) is handed to the owner for trial and feedback. Root may admit a data-independent tranche (local backup/restore, M5 slice) under owner-delegated authority. M3b needs owner hold measurements, real cases and stack-load data.
- Parked operator checkpoint: M3b real cases and measured hold, stack and tanktop load, lashing and stability, M4/M5, observations O7-O11 and O-M3A-2/3, hook/hosted-CI adoption, live-provider governance proof, 16 source envelopes and business acceptance remain owned future work.
- Active tranche: M3A

## Intake, design and authority acknowledgment

HARDEN-01 closed at 07c6e85. On 05-11 the owner confirmed the M2d XLSX opens without errors and restated that the development team must deliver a usable Prototype/MVP before waiting for feedback, asking whether technical work remains.

Root re-assessed the remaining items:

- The largest MVP gap is technical: the single-layer planner places only 167/1076 Baltimore bundles, and floor area, not mass, is the limit.
- The OD-only recheck question and the provenance-in-hash question are technical decisions. Root decided both in the SPEC.

Root selected M3a and bound it in SPEC docs/specs/SCST_M3A.md (D1-D5, M3A-01..M3A-05):

- an optional `stacking` mode;
- support rules (90% µm² cover, centre, exact top level, layer index);
- a deterministic `columns-v1` planner;
- the UI, 3D and report updates.

WORK_ORDER_AUTHOR wrote docs/work_orders/SCST_M3A.md. Coverage authority is registered as SCST-M3A.

## Baseline and preserved source

Baseline main 07c6e85: backend 679, browser 52, integration check 29/29.

Preserve:

- services/backend/data/**;
- legacy plans and snapshots, byte-identical;
- revision hashes;
- the user SQLite file and live 8765;
- the gate kit, CI and historical evidence.

## Remainder and return

Expected return: one pull request from Claude Cloud with source, tests, regenerated contract/types and docs/reviews/SCST_M3A_EVIDENCE/worker-return.md.

Root then becomes REVIEWER and:

- reruns everything on Windows;
- plans the Baltimore list itself and inspects the 3D view;
- writes docs/reviews/SCST_M3A_REVIEW.md;
- merges under delegated authority if it passes;
- hands the MVP to the owner.

## Review and closure

Claude Cloud returned PR #6 (head 8d205ef). Root REVIEWER reran on Windows and returned one repair round through PR comments: R1 pipe-list multi-layer default, R2 case voyage limit on switch, R3 x-sweep overlap pass (kept after review). At head 1f8c26e: backend 734/734, browser 55/55, integration check 29/29, gates PASS; columns-v1 places 1076/1076 Baltimore bundles in 0.05 s with 0 issues. Review docs/reviews/SCST_M3A_REVIEW.md accepts M3A-01..05; root merged PR #6 as 9a98cb8 under owner-delegated authority, closed the work order and synced continuity. The MVP goes to the owner for trial.
