# SCST — SUP-02A cargo revisions, pinning and recheck

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: BUILD
- Active phase: BUILD
- Active role: ORCHESTRATOR
- Next allowed move: Claude Cloud implements SUP-02A on a non-main branch and opens a pull request; Claude local independently reviews before any merge. SUP-02B, SUP-03 and M2d stay closed.
- Parked operator checkpoint: SUP-02B vessel/profile contract, SUP-03, M2d/M3/M4, hook/hosted-CI adoption, live-provider governance proof, measured hold and 16 source envelopes, business acceptance and merge decision remain owned future work.
- Active tranche: SUP-02A

## Intake, design and authority acknowledgment

Owner 04-11-2026 selected SUP-02, chose to make CVF-Ecosystem/Cargo_Stowage_Tool private before pushing, and assigned implementation to Claude Cloud with Claude local controlling quality. Root re-read AGENTS.md, manifest, policy, state, memory, the SUP-01 handoff and supplemental roadmap at INTAKE. Repository visibility changed to private and verified; 23 local commits scanned for secrets (none) and pushed as a fast-forward to origin/main 573d7fb. Raw VINAFCO268_LOCAL_HANDOFF_V1_1(1) stays local and untracked.

Root as ORCHESTRATOR/SPEC_AUTHOR split SUP-02 into SUP-02A (cargo revisions, provenance, plan pinning, recheck/rebase) and SUP-02B (generic vessel/profile contract, retained). SPEC docs/specs/SCST_SUP_02A.md binds D1-D8 and S2-01..S2-06; WORK_ORDER_AUTHOR wrote docs/work_orders/SCST_SUP_02A.md with worker ownership, forbidden paths, DA01-DA05 application, 240-minute worker and 90-minute review budgets. Coverage authority registered as SCST-SUP-02A. Pre-dispatch gate 6/6 PASS after removing a gate-module bytecode cache that root had generated while computing the section digest.

## Baseline and preserved source

Baseline 573d7fb: backend 104/104 PASS locally; browser 36 cases per SUP-01 review. Preserve services/backend/data/** (Baltimore registry, VINAFCO profile and GLB), legacy plan contracts and stored snapshots, user SQLite and live 8765, gate kit, CI, core pin and historical evidence. Root transitions WORK_ORDER_AUTHOR→ORCHESTRATOR for dispatch; the worker must acknowledge the canonical inputs before edits.

## Remainder and return

Expected return: one pull request from Claude Cloud with source, tests, regenerated contract/types and docs/reviews/SCST_SUP_02A_EVIDENCE/worker-return.md. Root then becomes REVIEWER: re-runs backend, build, full browser suite on an isolated database at port 8766 and worker-return/reviewer-fast gates locally, reviews the diff against D1-D8 and ownership, walks the S2-06 flow, writes docs/reviews/SCST_SUP_02A_REVIEW.md and reports to the owner, who decides the merge. No business acceptance, SUP-02B, SUP-03 or M2d is implied.
