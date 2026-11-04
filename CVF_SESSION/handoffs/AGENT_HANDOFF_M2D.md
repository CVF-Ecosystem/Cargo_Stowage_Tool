# SCST — M2d plan report export

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: BUILD
- Active phase: BUILD
- Active role: ORCHESTRATOR
- Next allowed move: Claude Cloud implements M2d on a non-main branch and opens a pull request; Claude local independently reviews before any merge, which the owner decides. M3 needs owner hold measurements and real cases.
- Parked operator checkpoint: M3/M4/M5, observations O2-O9, OD-only recheck policy, hook/hosted-CI adoption, live-provider governance proof, measured hold and 16 source envelopes, business acceptance and merge decision remain owned future work.
- Active tranche: M2D

## Intake, design and authority acknowledgment

SUP-02B and SUP-03 closed at 52351e1 after owner-approved merges de2aeea and 164dce5. Root ran the roadmap pre-M2d integration check (docs/reviews/SCST_INTEGRATION_CHECK_PRE_M2D.md, 29/29 PASS, e73c876); the single-layer planner placing 167/1076 Baltimore bundles in the estimated VINAFCO hold is recorded as an M3 gap. The owner instructed root to continue the roadmap without waiting and reviews before each merge.

Root, as ORCHESTRATOR/SPEC_AUTHOR, selected M2d and bound it in SPEC docs/specs/SCST_M2D.md (D1-D5, M2D-01..M2D-05):

- one shared report model from saved snapshots, with reconciliation and mandatory notices;
- read-only JSON and XLSX endpoints;
- deterministic stdlib XLSX;
- a printable A4 page with a 2D plan and one 3D image, PDF through the browser print;
- no new dependencies and no server-side PDF.

WORK_ORDER_AUTHOR wrote docs/work_orders/SCST_M2D.md. Coverage authority is registered as SCST-M2D.

## Baseline and preserved source

Baseline main e73c876: backend 597/597 and browser 46/46.

Preserve:

- services/backend/data/**;
- stored snapshots and Plan contracts;
- revision hashes;
- the user SQLite file and live 8765;
- the gate kit, CI, core pin and historical evidence.

## Remainder and return

Expected return: one pull request from Claude Cloud with source, tests, regenerated contract/types and docs/reviews/SCST_M2D_EVIDENCE/worker-return.md.

Root then becomes REVIEWER and:

- reruns everything locally on Windows;
- opens the XLSX in Excel if available and prints a PDF;
- walks M2D-05;
- writes docs/reviews/SCST_M2D_REVIEW.md;
- reports to the owner, who decides the merge.

No business acceptance or M3 is implied.
