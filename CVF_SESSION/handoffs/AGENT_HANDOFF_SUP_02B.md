# SCST — SUP-02B generic vessel profile and verified transform

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: FREEZE
- Active phase: FREEZE
- Active role: SESSION_SYNC_STEWARD
- Next allowed move: SUP-02B and SUP-03 technical handoff; root runs the roadmap integration check before M2d. M2d, M3, measured hold/packing and a second real vessel profile each need owner selection and a bounded SPEC/WORK_ORDER. Business acceptance separate.
- Parked operator checkpoint: M2d/M3/M4, SUP-02A observations O2-O5, SUP-02B O6-O7, SUP-03 O8-O9, OD-only recheck policy, hook/hosted-CI adoption, live-provider governance proof, measured hold and 16 source envelopes and business acceptance remain owned future work.
- Active tranche: SUP-02B

## Intake, design and authority acknowledgment

SUP-02A closed at dd61bee after the owner-approved merge 569c7ee. On 04-11-2026 the owner instructed root to continue the roadmap without waiting for questions. Root re-read the supplemental roadmap SUP-02 row, data and geometry principles, the vessel module, routes, VesselReference and Scene viewer constants at INTAKE.

Root, as ORCHESTRATOR/SPEC_AUTHOR, selected SUP-02B (the retained remainder of SUP-02) and bound it in SPEC docs/specs/SCST_SUP_02B.md:

- D1-D8 and acceptance criteria S2B-01..S2B-06.
- A generic profile contract with the VINAFCO268 profile derived as a built-in.
- A landmark- and GLB-bounds-verified transform.
- An append-only user profile file store.
- Vessel-pinned plans through the shared binding service.
- Viewer constants removed.
- Supporting fix O1, so evidence screenshots no longer overwrite closed packets.

WORK_ORDER_AUTHOR wrote docs/work_orders/SCST_SUP_02B.md with:

- worker ownership and forbidden paths;
- DA01-DA05 application;
- 240-minute worker and 90-minute review budgets.

Coverage authority is registered as SCST-SUP-02B.

## Baseline and preserved source

Baseline dd61bee: backend 222/222 and browser 39/39 PASS per the SUP-02A review.

Preserve:

- services/backend/data/** byte-for-byte;
- the three /api/vessels/vinafco268 responses;
- VINAFCO plans and stored snapshots;
- the user SQLite file and live 8765;
- the gate kit, CI, core pin and historical evidence.

## Remainder and return

Expected return: one pull request from Claude Cloud with source, tests, regenerated contract/types and docs/reviews/SCST_SUP_02B_EVIDENCE/worker-return.md.

Root then becomes REVIEWER and:

- reruns backend, build and the full browser suite on an isolated port 8766, and checks git status for S2B-06;
- runs the gates;
- reviews the diff against D1-D8 and ownership;
- walks the S2B-05 flow;
- writes docs/reviews/SCST_SUP_02B_REVIEW.md;
- reports to the owner, who decides the merge.

No business acceptance, SUP-03 or M2d is implied.

## Stacked SUP-03 dispatch

Owner on 04-11-2026 asked for a longer-horizon spec so the cloud continues overnight, with owner review on 05-11 before any merge. Root admitted SUP-03 (docs/specs/SCST_SUP_03.md, docs/work_orders/SCST_SUP_03.md, coverage SCST-SUP-03) as a stacked tranche: the cloud worker branches from the SUP-02B branch head and returns a pull request against it. This handoff stays the single ACTIVE handoff for both; merge order is SUP-02B then SUP-03, each after independent root review. Integration check before M2d follows SUP-03.

## Review and closure

Claude Cloud returned PR #2 (SUP-02B, head 94cb628) and, after one usage-limit stop and a root-launched resume, PR #3 (SUP-03, head 0d8bdff, stacked). Root REVIEWER reran each locally on Windows in separate worktrees: SUP-02B backend 503/503 after root repair 9f8969e (Windows empty leftover rename), browser 42/42; SUP-03 backend 597/597, browser 46/46; contract regeneration identical, gates PASS, no change under docs/reviews after browser runs. Reviews docs/reviews/SCST_SUP_02B_REVIEW.md and docs/reviews/SCST_SUP_03_REVIEW.md accept S2B-01..06 and S3-01..05. The owner reviewed on 05-11 and decided the merges; root merged PR #2 as de2aeea, retargeted PR #3 to main after confirming the merged tree equals the tested tree, and merged it as 164dce5. Root closed both work orders and synced state, status and memory. Raw VINAFCO folder and gate receipts stay untracked.
