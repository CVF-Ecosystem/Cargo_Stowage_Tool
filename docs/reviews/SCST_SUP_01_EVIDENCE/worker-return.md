# SUP-01 implementation worker return

Role IMPLEMENTATION_WORKER; admission 17ee7e5; current order SCST_SUP_01. Scope: viewer-3d/Scene.tsx, Viewer.tsx, styles.css; no backend, database, schema, profile, source, GLB, dependency, policy or core changes.

- S1-01: persistent scene, controls, camera and renderer; cargo by stable ID, context and asset identity separated, asynchronous generation guards, updated callback references and cleanup. Proof: source/typecheck/build; independent browser lifecycle and load-race evidence pending.
- S1-02: bounds/FOV/aspect framing, top/side/focus/reset, selected-placement guard and existing 2D fallback. Proof: source/typecheck/build; desktop/mobile/browser flow evidence pending.
- S1-03: selected hull nodes use owned cloned materials, originals restored; hull visibility remains independent. Exact source/geometry helpers and Plan contracts retained. Proof: source/typecheck/build; independent exact data and material-flow tests pending.
- S1-04: render on demand retained, heavy mesh diagnostics enabled only by ?viewerDiagnostics=1; old attribute shapes retained with added UUID and lifecycle/camera/material counters. Old-dist baseline captured by browser worker before build; candidate measurements and full regression pending.

Checks: npx tsc -b --pretty false PASS; npm run build PASS (final index-D-_1-kxf.js), with existing Three.js chunk warning. Installed Prettier formatted viewer files. Browser worker owns isolated database and tests; no backend suite run because backend unchanged. Two initial shell write attempts used paths relative to the wrong working directory and failed before writing intended files; corrected commands passed. No provider/governance behavior claim, commit or push.

DA01 preserves exact mm/µm geometry and practical kg/cm display; DA04 reuses Three/GLB and direct gate runner without full adoption claims; DA05 requires independent browser/isolated save-reopen flow proof, pending root/browser evidence. DA02/DA03 remain protected boundaries. Final acceptance and any unresolved findings belong to independent root review.
