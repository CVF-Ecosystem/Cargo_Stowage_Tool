# SCST — Practical display units handoff

Status: ACTIVE

## Current State

- Current mode: WORK_ORDER
- Active phase: WORK_ORDER
- Active role: ORCHESTRATOR
- Next allowed move: Admit practical kg/cm/m display repair under its SPEC/order, then acknowledge BUILD before worker edits; no M2d.
- Parked operator checkpoint: Measuredhold/16sourceenvelopes and business/operational acceptance pending; M2d/M3 separate.

## Authority and continuity

Owner01-11-2026 feedback1gram/1mm not useful, use at least kg/cm and roomy presentation. INTAKE/DESIGN then SPEC/order before code. Base232807d, M2c predecessor superseded, its acceptance/evidence immutable. Four criteria in docs/specs/SCST_DISPLAY_UNITS.md and order same name. Root orchestrator/author/independentreviewer/commitowner; Terra6.1High implementation, Sol-Medium browser per owner route. R2 ceiling, no external effects. Core ../.Controlled-Vibe-Framework-CVF c4c8767ac8861854f40d466ba338ffd11eb9558e read-only; doctor28/28. Live evidence required YES only for governance claims, none planned. BOOTSTRAP_MIGRATION_PENDING nonblocking.

## Design/reuse/budget

UI kg/cm/m rounded only, actual Plan/mesh/source/mm/g/µm unchanged. Editor must track explicit per-field edits: rounding draftFrom/applyDraft all fields would corrupt untouched data. Default input1kg/cm, precise representable fractions accepted. Compare subresolution labels retain exact ID state, no new tolerances. CSV contract remains explicit mm/kg. Native viewer/history/snapshot reused; no backend/schema/planner change or M2d.100min total preparation/build/review, elapsed/billing partiallyUNKNOWN, no reset. No worker implementation before admission+BUILDack. Existing live8765 session99168/PID480 can serve updated dist, no backendrestart needed; no test userDB writes.
