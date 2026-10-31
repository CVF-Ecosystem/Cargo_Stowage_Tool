# M1 browser proof — local synthetic candidate

Role: Sol-Medium IMPLEMENTATION_WORKER for `tests/browser/**` only. Root REVIEWER owns the acceptance decision. This record covers M1-01 (offline runtime), M1-06, M1-07 and M1-08; it is not a CVF AI-governance claim.

Run after final frontend rebuild and presentation-only CSS repair, from project root:

```powershell
$env:PYTHONPATH=(Resolve-Path 'tests/offline_guard').Path
npm.cmd --prefix apps/frontend run test:e2e
```

Exit **0**, **5/5 passed**, 11.4 seconds Playwright test time. Exact output: [browser-offline-e2e.log](browser-offline-e2e.log). The log contains `[WebServer] SCST_OFFLINE_GUARD_ACTIVE`: the Python API server loaded the non-loopback socket guard. [browser-offline-guard-probe.log](browser-offline-guard-probe.log) records the separate guard probe. The browser test routes all HTTP(S) requests and aborts any non-loopback destination; it observed none while loading, selecting, editing and validating against the local API. This proves the tested workflow after setup under these two guards; it does not prove package installation without network.

The suite fetches the real `/api/demo` result, compares every table row's ID, size, mass and placement, every 2D rectangle's coordinates and yaw footprint, and each placed unit's actual Three `Mesh.position`, `BoxGeometry.parameters` and world-matrix translation against the API values. It repeats numeric mesh checks after a real `/api/validate` yaw-90° change. A projected point computed from the live mesh and camera is clicked on the canvas to prove 3D selection; 2D and table selection, orbit, zoom and reset are checked. [browser-3d-yaw.png](browser-3d-yaw.png) captures the resulting 3D state.

For draft recovery, a raw edit immediately displays STALE while the checked row/summary remain visible. The browser transport sends `{}` to the real FastAPI endpoint to obtain HTTP 422; a separate request is aborted to simulate network loss. Both leave the raw input and previous checked result intact; retry and undo are compared with API snapshots. Another test holds a real validation response, edits the raw draft again, then releases the response: the newer input remains STALE until separately submitted. [browser-2d-stale.png](browser-2d-stale.png) captures the warning and checked 2D state.

The guarded offline flow also edits certificate limit to 30,000 kg, voyage limit to 29,000 kg and existing onboard cargo to 1,000 kg. It checks immediate STALE, then compares the real POST response's three gram limits and placed mass with the summary and checks panel. The displayed additional allowance is 28 tonnes, derived from voyage less onboard cargo.

For WebGL failure, the browser returns `null` from WebGL context creation, then proves the 2D plan, keyboard selection, table and synthetic warning remain usable at 390px width. The page has no horizontal overflow. The table itself has `overflow-x: auto`, content wider than its viewport and a working positive `scrollLeft`; [browser-mobile-fallback.png](browser-mobile-fallback.png) and [browser-mobile-table-scrolled.png](browser-mobile-table-scrolled.png) show both ends of the table.
