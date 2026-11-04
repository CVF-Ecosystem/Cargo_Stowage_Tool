# Project Session Memory

Memory class: POINTER_RECORD

## Current Truth

- Contract: cvf.downstreamContinuityContract@1.0.0
- Current mode: BUILD
- Active phase: BUILD
- Active handoff: CVF_SESSION/handoffs/AGENT_HANDOFF_HARDEN_01.md

## Current operator boundary

HARDEN-01 dispatched 05-11-2026 under owner-delegated authority: data-independent hardening (paged rebase drops, drop-on-rebase count, replay cache, pre-parse limits, Windows profile lock). SPEC docs/specs/SCST_HARDEN_01.md, order docs/work_orders/SCST_HARDEN_01.md, handoff CVF_SESSION/handoffs/AGENT_HANDOFF_HARDEN_01.md.

M2d closed 05-11-2026: root reviewed PR #4 (docs/reviews/SCST_M2D_REVIEW.md) and merged it as 690fcc7 under owner-delegated authority. M2 flow complete technically. Next: M2d technical handoff; root dispatches HARDEN-01 (data-independent hardening of observations) under owner-delegated authority. M3 needs owner hold measurements and real cases. Owner: open the sample XLSX in Excel.

M2d dispatched 05-11-2026 after the pre-M2d integration check passed 29/29 (docs/reviews/SCST_INTEGRATION_CHECK_PRE_M2D.md): shared report model, stdlib XLSX and printable A4 page. SPEC docs/specs/SCST_M2D.md, order docs/work_orders/SCST_M2D.md, handoff CVF_SESSION/handoffs/AGENT_HANDOFF_M2D.md. Claude Cloud implements on a branch; root reviews; owner decides the merge.

SUP-02B and SUP-03 closed 05-11-2026: root reviewed both PRs independently (docs/reviews/SCST_SUP_02B_REVIEW.md with root Windows repair 9f8969e; docs/reviews/SCST_SUP_03_REVIEW.md), owner decided the merges, root merged as de2aeea and 164dce5. Current FREEZE / SESSION_SYNC_STEWARD. Next: SUP-02B and SUP-03 technical handoff; root runs the roadmap integration check before M2d. M2d, M3, measured hold/packing and a second real vessel profile each need owner selection and a bounded SPEC/WORK_ORDER. Business acceptance separate. Earlier text below is history.

SUP-03 dispatched 04-11-2026 stacked on SUP-02B (owner: long-horizon overnight run, review 05-11 before merge): derived packing, three cargo views, envelope fallback. SPEC docs/specs/SCST_SUP_03.md, order docs/work_orders/SCST_SUP_03.md; same active handoff.

SUP-02B dispatched 04-11-2026 on owner instruction to continue without waiting: generic vessel profile, verified GLB-to-hold transform, append-only user profiles, vessel-pinned plans and supporting fix O1. SPEC docs/specs/SCST_SUP_02B.md, order docs/work_orders/SCST_SUP_02B.md, handoff CVF_SESSION/handoffs/AGENT_HANDOFF_SUP_02B.md. Claude Cloud implements on a branch with pull-request return; Claude local reviews independently; owner decides the merge. SUP-03/M2d closed.

SUP-02A closed 04-11-2026: Claude Cloud implemented on a branch, root reviewed independently (docs/reviews/SCST_SUP_02A_REVIEW.md, S2-01..06 VERIFIED technically), owner decided the merge and root merged PR #1 as 569c7ee. Current FREEZE / SESSION_SYNC_STEWARD. Next: SUP-02A technical handoff only; SUP-02B vessel/profile contract, SUP-03 or follow-up of review observations O1-O5 each need owner selection and a bounded SPEC/WORK_ORDER. Business acceptance separate. Earlier SUP-01 text below is history.

Current FREEZE / SESSION_SYNC_STEWARD. Next: SUP-01 technical handoff only; next SUP-02 needs bounded SPEC/WORK_ORDER when selected. Business acceptance and live CVF governance proof remain separate. Parked: SUP-02/03, M2d/M3/M4, hook/hosted-CI adoption and live-provider governance proof remain owned future work; measured hold and16source envelopes/business acceptance stay pending.

Owner asks inspect transferred CVF guidance, apply and continue roadmap. Supplemental operator-local project-development-application standard SHA d06b62387e015160a77658f333882a2a316d54ffd0421071354cf63a3730dd7a verified; public Core pin c4c8767 unchanged/read-only. Incoming owner additions preserved in evidence/incoming-transfer.json. AGENTS routes SCST-DA01..05; active order selects DA01/04/05 and holds DA02/03 boundaries. Source delivery/document checks are not agent-governance proof.

Bounded CVF-DEV continuation independently reviewed by Sol; see docs/reviews/SCST_CVF_DEV_APPLICATION_RECONCILIATION.md. DEV-01 IMPLEMENTED_UNPROVED, DEV-02/03 UNKNOWN remain; no full adoption/hosted CI/live-provider claim. Governance proof NOT_RUN, credentials/provider/hooks/CI outside selected scope. Native reuse/direct runner sufficient for current pure viewer; owned future gap destination docs/specs/SCST_CVF_DEV.md.

SPEC docs/specs/SCST_SUP_01.md and order docs/work_orders/SCST_SUP_01.md bind four criteria. Root orchestrates/specs/reviews worker implementation/local commit; Terra viewer/styles, Sol browser/config/evidence. Risk R2, independent review, live evidence YES for behavior claims, none planned. 120minute total prep/workers/review ceiling, no reset; baseline before first new build, one full browser regression after freeze, user DB/live8765 untouched. BOOTSTRAP_MIGRATION_PENDING nonblocking.

## Bổ sung áp dụng nền ngày 01-11-2026

Owner transfer added common/project controls DA01..05 to adoption DESIGN and AGENTS using active local rule-pack; Core pin and checkpoint hashes preserved. Original mapping acceptance was ACCEPT_WITH_LIMITS for document/source scope, not app BUILD or agent behavior. Use concrete task controls and usable flow proof, not only test counts. Parent SCST-L001 assessment remains pending; no returned parent implementation claimed.

## Read next

SUP-01 technical review accepted at docs/reviews/SCST_SUP_01_REVIEW.md: final build index-D-_1-kxf.js;36/36 full browser,5focused and2focused output-path checks,14source/document integrity checks. Artifact path error repaired;27owned files recovered, external wrong base empty, no pre/post move byte-equality claim. SCST-L002 candidate/intake generated only; parent assessment pending, SCST-L001 separate. Root REVIEWER→CLOSER→SESSION_SYNC_STEWARD/COMMIT_STEWARD recorded in handoff. Local live8765 health/index checked read-only, new bundle served; user DB unchanged during regression. No automatic next slice.

Manifest/policy/state/active handoff/truth/index, active SPEC/WO, adoption matrix and triggered SCST-L001 learning. Preserve original kg/cm presentation and exact stored/geometry data, source coordinate mapping, GLB and historical evidence. Raw VINAFCO268_LOCAL_HANDOFF_V1_1(1) stays local/untracked, never bulk-add. No automatic SUP-02/M2d.
