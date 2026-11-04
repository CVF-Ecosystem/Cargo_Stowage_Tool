# SCST SUP-03 worker return — derived packing and bundle/pipe views

Risk: R2
Worker: Claude Cloud implementation team (lead session as IMPLEMENTATION_WORKER and in-run advisor/reviewer; subagents listed below)
Reviewer: Root Claude local session (independent REVIEWER and COMMIT_STEWARD, pending); in-run lead review is not independent review

Status: RETURNED_FOR_INDEPENDENT_REVIEW. SPEC docs/specs/SCST_SUP_03.md, WORK_ORDER docs/work_orders/SCST_SUP_03.md. Branch `claude/sup-03-packing-views`; pull request base `claude/sup-02b-vessel-profile`.

## CVF Agent Declaration (cloud run)

Project Cargo_Stowage_Tool · CVF core pin c4c8767 (hidden core and `../WORKSPACE_RULES.md` are not available in the cloud; core initialize/clone scripts were not run, as instructed) · phase BUILD · risk ceiling R2 · live governance evidence required YES (no governance claim is made here, so no provider call; the product makes none) · role IMPLEMENTATION_WORKER · active handoff `CVF_SESSION/handoffs/AGENT_HANDOFF_SUP_02B.md` (section "Stacked SUP-03 dispatch") · next allowed move: worker return through a pull request for root review · parked checkpoint none for SUP-03.

**Continuity finding for root (not repaired, root-owned files):** `CVF_SESSION/ACTIVE_SESSION_STATE.json` `nextAllowedMove` still says "SUP-03 and M2d stay closed" and `parkedOperatorCheckpoint` lists SUP-03, while the handoff, `CVF_SESSION_MEMORY.md`, `IMPLEMENTATION_STATUS.json` and the ACTIVE work order admit SUP-03. The worker followed the newer dispatch (work order ACTIVE, SPEC APPROVED_FOR_EXECUTION, owner's scheduled prompt) on a non-main branch, disclosed this drift here and notified the owner. Root should reconcile the state file before REVIEW/FREEZE.

## Base commits

- Resumed `origin/claude/sup-03-packing-views` at f669e67 (previous cloud run's only commit; it stopped at an account usage limit and its uncommitted work was lost).
- Merged `origin/claude/sup-02b-vessel-profile` (head 9f8969e, root review repair for Windows) → merge commit 2f79815. Baseline on 2f79815: `python -m pytest` 503 passed; full browser suite 42 passed.
- f669e67 (`apps/frontend/src/features/packing.ts`) was **kept unchanged** as the frontend data contract; the backend response models were written to match it exactly.

Commits of this run: 8bb4035 (domain + endpoint), 328f3a5 (table/panel WIP), 94e2ca2 (API tests), 2c303d8 (contract regen), 337bfdc (viewer), 723e927 (row button repair), c9ebad1 (browser spec + evidence), plus this worker return.

## Changed paths

services/backend/app/domain/packing/__init__.py (new) · services/backend/app/api/routes.py · services/backend/app/api/cargo_models.py · tests/backend/test_sup03_packing_domain.py (new) · tests/backend/test_sup03_api.py (new) · contracts/openapi.json · apps/frontend/src/api/generated/api.ts · apps/frontend/src/features/PackingInfo.tsx (new) · apps/frontend/src/features/Workspace.tsx · apps/frontend/src/features/CargoRevisionPanel.tsx · apps/frontend/src/viewer-3d/packingMeshes.ts (new) · apps/frontend/src/viewer-3d/Scene.tsx · apps/frontend/src/viewer-3d/Viewer.tsx · apps/frontend/src/styles.css · tests/browser/sup03.spec.ts (new) · docs/reviews/SCST_SUP_03_EVIDENCE/** (this file, browser/sup03-timing.json, browser/sup03-revision-panel-desktop.png).

Not touched: services/backend/data/**, .cvf/**, scripts/cvf_gates/**, .github/**, requirements, package.json/package-lock.json, existing browser specs, SUP-02A change types and hashed group fields, CVF_SESSION, memory, status, docs/specs, docs/work_orders. No dependency added. An untracked, git-excluded `apps/frontend/playwright.local.config.ts` (webServer command, temp SCST_DATA_DIR, chromium executablePath only) was used for browser runs.

## Decisions per D1–D6

- **D1 packing (pure).** `domain/packing.pack_section/pack_group/pack_revision`: no I/O, no float anywhere in the output. `mm_to_um` converts the OD/wall decimal string exactly; a value that is not a whole number of µm (e.g. "42.2005") is treated as `OD_MISSING` rather than rounded (data-preserving choice). First centre offset r = ceil(OD/2); fit checked exactly with doubled integers (2y±OD within 0..2W). RECT first (cols = floor(W/OD) adjusted for odd OD), filled bottom-up, left to right; HEX only if RECT is short: row pitch `isqrt(3·OD²)//2` = floor(OD·√3/2), odd rows shifted by ceil(OD/2). Reported `columns`/`rows` are those used (widest placed row × rows reached), e.g. R002 grid 8×7, placed 8×6 for 42 pipes. `max_fit` = max(RECT, HEX capacity), clamped to 2^53−1. Known limit: with floored pitch adjacent HEX rows can overlap by < 1 µm (pipe collision is out of scope, D6); for odd-µm OD the grid can lose 1 µm of width (conservative).
- **D2 checks/reasons.** checks `count`, `od_fit`, `envelope_fit`, `slack_loose`. Reason codes: `OD_MISSING`, `OD_EXCEEDS_SECTION` (added: D2.1 od_fit failure needs its own code), `PIECES_DO_NOT_FIT` (message includes max fit), `INPUT_INVALID` (defensive; revision validation normally prevents it), `ENVELOPE_LOOSE` (informational; slack ≥ 1 OD in either axis — equality counts, so R002/R003 are LOOSE with exactly 1 OD of height slack), `SOURCE_WARNING` (dimension_warning or any existing issue code; it never changes status — data-preserving reading of D2.2). ENVELOPE_ONLY messages end with "Kiểm lại OD, số ống mỗi bó hoặc kích thước bó trong revision." Bundles with a `dimensions_um` override get their own `bundle_packings` entry; others inherit the group. Stats per D2.4 (groups/bundles by status, derived vs source pipes).
- **D3 API.** `GET /api/cargo-revisions/{revision_id}/packing` (response model `RevisionPacking`, `basis: "DERIVED"`): read-only, 404 unknown/malformed id, 400 `{message, errors: []}` for a revision failing replay integrity (same path as SUP-02A `GET /api/cargo-revisions/{id}`). Not embedded in Plan or snapshot; `scst.pipe-list.v1/v2` JSON unchanged.
- **D4 viewer.** "Cách nhìn hàng" select: Khối bao (default, unchanged), Bó giản lược (translucent box + end-face rings, InstancedMesh), Chi tiết ống (hollow tubes OD/wall, 12 radial segments, InstancedMesh per (OD, wall) key, bundle pose incl. yaw). Only a dedicated `s.pack` group is rebuilt; renderer, scene, GLB, camera, selection and the envelope box meshes (same uuid) are preserved; rebuild is keyed by view/packing/units/placements (and selection only when capped), never by camera movement. ENVELOPE_ONLY or packing-less pipe bundles stay solid with an orange warning outline. Budget 60 000 tube instances: if total ≤ budget all bundles are detailed; otherwise selected bundle, then in-frustum bundles by distance; the rest get rings (ring cap 120 000 = 2 per pipe), beyond that a translucent box. Status line `packing-view-status` states counts and the cap message "Vượt hạn mức 60.000 ống…". Picking maps `instanceId` → bundle id; boxes stay pickable. Opt-in diagnostics (`?viewerDiagnostics=1`): `packingView`, `packingProjected`, and `sceneUuid` added to `viewerStats` (keys only added). Yaw convention for the section axes (counter-clockwise about the box min corner) is the worker's choice; it only affects where asymmetric layouts sit inside the box — root please confirm. 2D: ENVELOPE_ONLY bundles get a dashed warning stroke; table carries the packing column.
- **D5 table and panel.** Table column "Cách xếp (dẫn xuất)" (status, RECT/HEX cols × rows, placed/source pipes, slack in cm, reason codes); filter "Lọc trạng thái cách xếp"; dataset stats line. Bundle panel `PackingInfo` (status, layout, pipes, OD, slack cm, reasons with Vietnamese text, labelled "không phải số đo thực"). Clicking a reason (panel button, or table link) opens the group in "Dữ liệu hàng" on the plan's pinned revision, focuses/scrolls it, pre-selects it in an empty change row, and each shown group displays its derived packing for the revision in view, so a new revision visibly changes the group's packing. The table reason is a link (not a button) so every row keeps exactly one button (existing specs depend on it; see failed attempts).
- **D6.** Nothing out of scope was built (no user-declared layouts, collisions, CoG, multi-tier, report export, AI, engine change).

## S3 acceptance mapping

| ID | Implemented | Tested |
|---|---|---|
| S3-01 | domain/packing | tests/backend/test_sup03_packing_domain.py (82 tests: RECT, HEX, no fit, OD missing/invalid, OD > section, odd OD, int-only, determinism, 10 000 pipes, R0000 table) |
| S3-02 | domain/packing reasons/stats | domain tests per reason code; isolation of a broken group; test_sup03_api.py OD 400 mm group only; R022 keeps SOURCE_WARNING |
| S3-03 | routes.py + cargo_models.py | test_sup03_api.py (12): read-only (no rows), 404, integrity 400 like SUP-02A, R0000 hash = golden BASE_SHA, v2 snapshot raw plan_json and GET bytes identical, no packing keys in plan |
| S3-04 | Scene.tsx, Viewer.tsx, packingMeshes.ts | sup03.spec.ts: three views keep sceneUuid/loads/assetIdentity/mesh uuids/camera/selection; pipe click selects bundle in DETAILED; budget capped with message; timing below |
| S3-05 | Workspace.tsx, CargoRevisionPanel.tsx, PackingInfo.tsx, contract regen | sup03.spec.ts desktop flow + 390px; full browser suite 46 passed; `npm run build` passes |

## Baltimore R0000 packing (31 groups, DERIVED)

| Group | Status | Layout | cols × rows | placed / source per bundle | slack W, H (µm) | Reasons |
|---|---|---|---|---|---|---|
| R002 | DETAILED | RECT | 8 × 6 | 42 / 42 | 0, 42 200 | ENVELOPE_LOOSE, SOURCE_WARNING |
| R003 | DETAILED | RECT | 8 × 6 | 42 / 42 | 0, 42 200 | ENVELOPE_LOOSE, SOURCE_WARNING |
| R004 | DETAILED | RECT | 8 × 5 | 36 / 36 | 0, 48 300 | ENVELOPE_LOOSE, SOURCE_WARNING |
| R005–R009 | DETAILED | RECT | 6 × 5 | 26 / 26 | 0, 60 300 | ENVELOPE_LOOSE |
| R010–R012 | DETAILED | RECT | 5 × 4 | 18 / 18 | 0, 73 000 | ENVELOPE_LOOSE |
| R013–R016 | DETAILED | RECT | 4 × 3 | 12 / 12 | 0, 101 600 | ENVELOPE_LOOSE |
| R017 | DETAILED | RECT | 4 × 3 | 10 / 10 | 0, 100 | SOURCE_WARNING |
| R018–R021 | DETAILED | RECT | 3 × 3 | 7 / 7 | 0, 0 | — |
| R022 | ENVELOPE_ONLY | — | — | 0 / 5 (max fit 4) | — | PIECES_DO_NOT_FIT, SOURCE_WARNING |
| R023–R030 | DETAILED | RECT | 3 × 3 | 7 / 7 | 0, 0 | SOURCE_WARNING |
| R031 | ENVELOPE_ONLY | — | — | 0 / 5 (max fit 4) | — | PIECES_DO_NOT_FIT, SOURCE_WARNING |
| R032 | ENVELOPE_ONLY | — | — | 0 / 5 (max fit 4) | — | PIECES_DO_NOT_FIT, SOURCE_WARNING |

Rows grouped where every value is identical (R005–R009 etc.); the per-group values are asserted in the domain test. Stats: 31 groups (28 DETAILED / 3 ENVELOPE_ONLY), 1 076 bundles (1 060 / 16), derived pipes 21 146 vs source 21 226; the 80 difference is exactly the 16 envelope-only bundles × 5 pipes. For every DETAILED group derived = source. The three ENVELOPE_ONLY groups are the source rows already flagged `packaging_envelope_conflict` (5 × 219.1 mm in a 438.2 mm square: RECT 2×2, HEX 2+1).

## Timing (measured, headless Chromium in the cloud container, software WebGL)

From tests/browser/sup03.spec.ts, `docs/reviews/SCST_SUP_03_EVIDENCE/browser/sup03-timing.json`: all units of the shared-suite latest revision placed (1 079 = 1 076 Baltimore + 3 added by the SUP-02A spec earlier in the suite), 1 060 bundles detailed, 21 146 tube instances, not capped: **detailed build 36.1 ms**; simplified build (42 292 ring instances) 55 ms. A previous run of the same spec on 1 076 units measured 37.3 ms / 55.3 ms. This is pack-group build time only (performance.now around building instances), not frame rate; **no FPS claim**.

## Who did what

| Work | Agent | Model / effort | Why |
|---|---|---|---|
| Design, split, API route/models, table/panel/Dữ liệu hàng wiring, PackingInfo, CSS, contract regen, review of every result, fixes, verification, worker return, PR | lead session | Opus 5.5 / medium | lead/advisor; the table/panel code was done by the lead instead of Haiku because Workspace.tsx is dense single-line JSX where precise anchored edits were cheaper and safer |
| Packing domain + domain tests | subagent | Sonnet / high | exact integer RECT/HEX geometry (owner rule) |
| Viewer views, InstancedMesh, picking, budget, scene lifecycle | subagent | Sonnet / high | InstancedMesh views with picking, budget and scene preservation (owner rule) |
| API tests | subagent | Haiku / high | default tier |
| Browser spec | subagent | Haiku / high | default tier; lead then hardened it (below) |

The lead re-read every diff and re-ran all tests itself; subagent reports were not taken as proof. At most two subagents edited at once, never the same file.

## Commands and results

- `python -m pip install -r requirements-dev.txt; python -m pytest` — baseline 503 passed; after: **597 passed** (1 warning, pre-existing).
- `python tooling/export_contract.py`; `cd apps/frontend && npm ci && npm run contract && npm run build` — pass (only the pre-existing chunk-size warning).
- `npx playwright test -c playwright.local.config.ts` (full suite incl. sup03) — **46 passed** (42 existing + 4 new). After the run `git status` showed no change under docs/reviews (screenshots go to SCST_EVIDENCE_DIR in the scratchpad).
- `PYTHONDONTWRITEBYTECODE=1 python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return` — PASS (7 mandatory controls, 0 failed); re-run after this file, result in the PR.

## Failed attempts and corrections

1. Previous cloud run stopped at an account usage limit; only f669e67 survived. This run committed and pushed at every milestone.
2. The first API-test subagent stopped at the AGENTS.md first-request protocol (missing CVF core/WORKSPACE_RULES, state drift). The lead recorded the drift as a disclosed finding (above) and resumed it within the same scope.
3. First full browser run after the viewer: **6 existing tests failed** (strict mode: `row.getByRole("button")` found two buttons because the table reason was a button). Fixed in product code (reason became a link, 723e927); existing specs not edited. Re-run: 46 passed.
4. SPEC gap found by the browser spec: an **OD-only revision does not make an old plan "Cần kiểm lại"**. OD is not a field of the SUP-02A plan units (derive_units/diff_units), so recheck correctly reports CURRENT; adding OD to units would change Plan JSON and hashed unit content, which the SPEC forbids. The subagent had used soft assertions; the lead replaced them with hard assertions and made the flow's batch an OD correction **plus the re-stated bundle mass** (+1 kg/bundle), which yields NEEDS_RECHECK exactly as in SUP-02A. Owner/root decision: whether an OD-only change should mark plans (would need a new SPEC revision).

## DA application

- **DA01:** µm/mm integers end to end; OD/wall strings converted exactly; cm/mm rounding only in PackingInfo/table/viewer display.
- **DA02:** no persistence change; no new table; tests prove no rows written and snapshot bytes unchanged.
- **DA03:** every packing payload has `basis: "DERIVED"`; UI says "dẫn xuất, không phải số đo"; source warnings retained as SOURCE_WARNING; no stability/fit claim for the hold.
- **DA04:** reuses cargo revisions/view replay, derive_units-free lookup by group/bundle, Scene lifecycle, existing display modes, table, panel and SUP-02A revision panel; only the packing module, endpoint, pack group and panel were added.
- **DA05:** internal flow evidenced in the browser: open list → Chi tiết ống → DETAILED and ENVELOPE_ONLY bundle → reason → group in Dữ liệu hàng → revision correcting OD (+mass) → group packing changes → old plan Cần kiểm lại; desktop and 390px. Business acceptance is not claimed.

## Limitations and remaining owned work

- Independent root review (backend, build, full browser on port 8766, gates, own S3-05 walk-through) and the integration check before M2d are pending.
- State drift in `CVF_SESSION/ACTIVE_SESSION_STATE.json` (root).
- OD-only recheck semantics (owner decision; see failed attempt 4).
- Timing measured with software WebGL in a container; desktop GPU timing and FPS not measured.
- Screenshots kept small: only the revision panel PNG is committed; the others are in the run's temp evidence dir.
- Yaw convention of the section axes to be confirmed by root; HEX sub-µm overlap and odd-µm OD 1 µm conservatism documented.
- Measured hold, real packing layouts, M2d and business acceptance remain owner-owned.
