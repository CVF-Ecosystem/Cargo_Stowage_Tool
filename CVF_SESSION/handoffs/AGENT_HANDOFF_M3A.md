# SCST — M3a multi-layer column stacking MVP

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: BUILD
- Active phase: BUILD
- Active role: ORCHESTRATOR
- Next allowed move: Claude Cloud implements M3a on a non-main branch and opens a pull request; root reviews independently and merges under owner-delegated authority, then hands the MVP to the owner for feedback. M3b needs owner hold measurements and real cases.
- Parked operator checkpoint: M3b real cases and measured hold, stack and tanktop load, M4/M5, observations O7-O11, hook/hosted-CI adoption, live-provider governance proof, 16 source envelopes and business acceptance remain owned future work.
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
