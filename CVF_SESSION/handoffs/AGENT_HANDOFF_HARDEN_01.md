# SCST — HARDEN-01 hardening after SUP-02/03

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: FREEZE
- Active phase: FREEZE
- Active role: SESSION_SYNC_STEWARD
- Next allowed move: WAIT_OWNER: M2 and the supplemental roadmap are technically complete and hardened. Next needs owner input: business review of the tool and the M2d report (open the sample XLSX in Excel), decisions on OD-only recheck and provenance-in-hash, and hold measurements plus real cases for M3. Root dispatches no further cloud tranche without that input.
- Parked operator checkpoint: M3/M4/M5, observation O3 (provenance outside hash), OD-only recheck policy, real-Excel check of the M2d XLSX, O7-O11, hook/hosted-CI adoption, live-provider governance proof, measured hold and 16 source envelopes and business acceptance remain owned future work.
- Active tranche: HARDEN-01

## Intake, design and authority acknowledgment

M2d closed at 268ff35 after merge 690fcc7. On 05-11 (~02:50 +7) the owner delegated GitHub merge authority to root as orchestrator after independent review and asked root to coordinate the next session. M3 depends on owner data.

Root therefore selected HARDEN-01 and bound it in SPEC docs/specs/SCST_HARDEN_01.md (H1-H6, H-01..H-05). It is data-independent hardening of recorded observations:

- paged rebase drops (O2);
- a separate count of placements dropped on rebase (SUP-02A decision 2);
- a keyed replay cache (O4);
- pre-parse body limits (O5);
- a Windows cross-process profile lock (O6).

WORK_ORDER_AUTHOR wrote docs/work_orders/SCST_HARDEN_01.md. Coverage authority is registered as SCST-HARDEN-01.

## Baseline and preserved source

Baseline main 268ff35: backend 650, browser 50, integration check 29/29.

Preserve:

- services/backend/data/**;
- stored data formats, revision hashes and existing contract fields;
- the user SQLite file and live 8765;
- the gate kit, CI and historical evidence.

## Remainder and return

Expected return: one pull request from Claude Cloud with source, tests, regenerated contract/types and docs/reviews/SCST_HARDEN_01_EVIDENCE/worker-return.md.

Root then becomes REVIEWER and:

- reruns everything on Windows, including the two-process lock test;
- writes docs/reviews/SCST_HARDEN_01_REVIEW.md;
- merges under delegated authority if it passes;
- reports to the owner.

## Review and closure

The first HARDEN-01 cloud run stopped at the account 5-hour usage limit before any edit; root re-armed the routine after the reset. Claude Cloud returned PR #5 (head 88c4fb6). Root REVIEWER reran on Windows: backend 679/679 including real two-process msvcrt lock tests, browser 52/52, integration check 29/29, gates PASS. Review docs/reviews/SCST_HARDEN_01_REVIEW.md accepts H-01..05; root merged PR #5 as c8b9c1c under owner-delegated authority, closed the work order and synced continuity. Remaining work needs owner input, so root dispatches no further cloud tranche.
