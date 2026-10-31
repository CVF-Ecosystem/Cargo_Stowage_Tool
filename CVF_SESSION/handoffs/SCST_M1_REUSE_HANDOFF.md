# SCST M1 — Selective reuse execution handoff

Status: ACTIVE

## Current State

- Project: Cargo_Stowage_Tool
- Current mode: WORK_ORDER
- Active phase: WORK_ORDER
- Active role: ORCHESTRATOR
- Next allowed move: Validate and commit SCST_M1_REUSE dispatch, acknowledge material-SHA marker, then Terra worker implements M1-01 through M1-09; root reviews independently before closure.
- Parked operator checkpoint: Scope changes or risk above R2 return to owner; M2-M5 and operational use remain outside this work order.

## Authority and responsibilities

- Owner instructed root to orchestrate/review, use Terra 6.1 High as worker and Sol-Medium for difficult work, and continue the agreed M1 plan. SCST-D002 records this authority. SPEC v0.2 and the selected reuse appendix are admitted for this M1 work order; this is not product/business acceptance.
- Root: ORCHESTRATOR / WORK_ORDER_AUTHOR, then REVIEWER, COMMIT_STEWARD and SESSION_SYNC_STEWARD. Worker: `/root/m1_worker`, Terra 6.1 High. Risk R2 (local implementation/dependency setup), ceiling R2; real API evidence YES if claiming AI governance, but this tranche has no such claim or provider call. No downstream work inside core.
- Required rehydration completed from current manifest/policy/state/memory/handoff/status/index. Core c4c8767ac8861854f40d466ba338ffd11eb9558e; doctor 28/28 passed before dispatch preparation. Missing bootstrap read model remains a nonblocking migration note.
- Current work order: `docs/work_orders/SCST_M1_REUSE.md`; source acceptance: `docs/specs/SCST_M1.md` / `## M1 acceptance`; registry `SCST-M1`. Selected all nine criteria; source archive tree e4004e274fc28aa143ce0e300b6c060d1cb1e5a0 stays immutable. No old results accepted as new proof.
- Cost/stop: 120-minute implementation + 45-minute review/repair ceiling including bounded setup support; no automatic successor or budget reset. Previous source reviews reused. Worker reports scope/compatibility problems before changing requirements or spending support budget.

## Read-only preflight

- Terra confirmed Python 3.11.9, Node 22.17.0, npm 10.9.2 and cached Chromium. Proposed backend/contracts → frontend → launcher/test order. No source edits/install/runtime execution in preflight.
- Terra additionally invoked the workspace-container `../Test-CVF-Workspace.ps1 -Json`, reporting REPAIR_REQUIRED for the sibling workspace installation/profile. Root inspected that wrapper: it hardcodes `-WorkspaceRoot` to the parent container and does not target this downstream project. This is a separate reported workspace-maintenance condition; no claim it is repaired. Project-specific pinned core identity, doctor and portable gates are the applicable dispatch checks here; do not modify the container/core to hide that result.

## Dispatch record

- WORK_ORDER prepared from SPEC v0.2; root owns admission and evidence/commit decisions. Worker remains read-only until dispatch validation, commit and material-SHA acknowledgment.
- Previous handoff/history: `CVF_SESSION/handoffs/AGENT_HANDOFF_V1_2026-10-31.md`; reference only, superseded by this active pointer and latest user authority.
