# DISPLAY_UNITS implementation worker return

Role: IMPLEMENTATION_WORKER. Authority: SCST_DISPLAY_UNITS SPEC and work order, admission 0fc26e6, BUILD acknowledgment adae04e. Independent review and final disposition belong to root.

## Delivery and criteria

- DU-01: Workspace, 3D labels and comparison show practical kg/cm/m; totals remain tonnes with at most two decimal places. CSV's technical exchange units are explicitly identified.
- DU-02: Rounded editor defaults are separate from exact Plan fields; field-specific edit tracking applies only changed fields. Exact semantic reverts clear STALE, while explicitly re-entering a rounded value is an edit when it differs from the exact original. Validation responses rebase newer edits against the checked Plan instead of discarding them. Existing placement order is preserved on draft application. Source physical values and geometry helpers remain exact.
- DU-03: Comparison presents kg/cm and calls out nonzero changes below one display unit; backend comparison remains untouched.
- DU-04: Frontend production build passed, index-DXRJy6j_.js. A focused in-memory oracle passed unchanged 2500001 g and 501 mm, explicit rounded edit, exact semantic revert, pending-validation rebase, and placement ordering. Browser and packaged-flow evidence is owned by Sol/root and pending independent review. Backend was unchanged and its suite was not rerun.

Changed implementation paths: apps/frontend/src/features/model.ts, apps/frontend/src/features/Workspace.tsx, apps/frontend/src/features/ComparisonPanel.tsx, apps/frontend/src/viewer-3d/Viewer.tsx. No backend, registry, source, storage, contracts, geometry transforms, dependency or provider changes. No commit or push.

The first attempt at the in-memory oracle failed in the Node harness because the synthetic module filename was unset; the harness was corrected and the check passed. An async edge was identified during implementation: a pending validation could otherwise replace a newer reverted draft; rebaseDraft now compares newer edits to the newly checked values. This is implementation evidence, not final acceptance or governance proof.
