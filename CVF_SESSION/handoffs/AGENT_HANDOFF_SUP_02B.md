# SCST — SUP-02B generic vessel profile and verified transform

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: BUILD
- Active phase: BUILD
- Active role: ORCHESTRATOR
- Next allowed move: Claude Cloud implements SUP-02B on a non-main branch and opens a pull request; Claude local independently reviews before any merge. SUP-03 and M2d stay closed.
- Parked operator checkpoint: SUP-03, M2d/M3/M4, SUP-02A observations O2-O5, hook/hosted-CI adoption, live-provider governance proof, measured hold and 16 source envelopes, business acceptance and merge decision remain owned future work.
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
