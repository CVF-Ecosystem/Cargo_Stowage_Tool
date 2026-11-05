# SCST M3a worker return — multi-layer column stacking MVP

Risk: R2
Worker: Claude Cloud implementation team (lead session as IMPLEMENTATION_WORKER, in-run advisor and reviewer; subagents listed below)
Reviewer: Root Claude local session (independent REVIEWER and COMMIT_STEWARD, pending); in-run lead review is not independent review

Status: RETURNED_FOR_INDEPENDENT_REVIEW. SPEC docs/specs/SCST_M3A.md, WORK_ORDER docs/work_orders/SCST_M3A.md, handoff CVF_SESSION/handoffs/AGENT_HANDOFF_M3A.md. Branch `claude/m3a-column-stacking` from main 6dac6bd.

## CVF Agent Declaration (cloud run)

Project Cargo_Stowage_Tool · CVF core pin c4c8767 (the hidden core and `../WORKSPACE_RULES.md` are not available in the cloud; core initialize/clone scripts were not run, as instructed) · phase BUILD · risk ceiling R2 · live governance evidence required YES (M3a makes no governance claim, so no provider call; the product makes none) · role IMPLEMENTATION_WORKER · active handoff `CVF_SESSION/handoffs/AGENT_HANDOFF_M3A.md` · next allowed move: worker return through a pull request for root review · parked: M3b, M4/M5, O7–O11 and the rest of the owner-held remainder.

## Changed paths

Backend: services/backend/app/domain/model/__init__.py · domain/rules/__init__.py · domain/planner/__init__.py · domain/report/__init__.py · domain/report/xlsx.py · adapters/plan_binding.py · api/routes.py · api/cargo_models.py · api/report_models.py.
Tests (new only): tests/backend/test_m3a_model.py · test_m3a_rules.py · test_m3a_planner.py · test_m3a_flow.py · tests/browser/m3a.spec.ts.
Contract: contracts/openapi.json (tooling/export_contract.py) · apps/frontend/src/api/generated/api.ts (npm run contract).
Frontend: apps/frontend/src/api/client.ts · features/Workspace.tsx · features/RebaseDropped.tsx · features/ReportPage.tsx · viewer-3d/Viewer.tsx · styles.css.
Evidence: this file.

Not touched: services/backend/data/**, .cvf/**, scripts/cvf_gates/**, .github/**, tooling/**, requirements, package.json/package-lock.json, existing backend tests and browser specs, Scene.tsx (3D scene lifecycle), revision hashing, CVF_SESSION, memory, status, docs/specs, docs/work_orders. No dependency added. Browser runs used an untracked, git-excluded `apps/frontend/playwright.cloud.config.ts` that differs from playwright.config.ts only in the webServer command, a temp SCST_DATA_DIR and the chromium executablePath.

## Decisions per D1–D5

**D1 (model).** `Plan.stacking: "SINGLE_LAYER" | "COLUMNS_V1" | None`, popped from JSON when None by the existing `omit_absent_revision` serializer. Five Issue codes appended. Absent and `SINGLE_LAYER` keep `LAYER_UNSUPPORTED` exactly. No contract-specific restriction, because every hold is BOX.

**D2 (rules, `domain/rules`).** `_check_columns` runs after the unchanged overlap loop, only for COLUMNS_V1. The rules work in exact integer µm and µm².
- **Ambiguity (data-preserving choice):** D2.1 asks that the support top equal `z_mm` exactly in µm, but D3.1 stacks on `z_mm` = height rounded up to whole mm, and Baltimore heights are not whole mm (for example 504.9 mm or 295.4 mm). Strict equality would reject every Baltimore stack. Implemented rule: `(support_top_um + 999) // 1000 == z_mm`, meaning the support top rounded up to the mm grid equals `z_mm`. This is exact equality for integer-mm units, leaves a gap under 1 mm, and never allows interpenetration (the top stays ≤ z). Root should confirm.
- **Error codes:**
  - z = 0 with `supported_by` gives SUPPORT_LEVEL_MISMATCH; z = 0 with layer ≠ 0 gives LAYER_INDEX_INVALID.
  - z > 0 with empty, unplaced, duplicated or self supporters gives SUPPORT_MISSING (other support checks skipped).
  - Each supporter at the wrong level gives SUPPORT_LEVEL_MISMATCH (area and centre skipped).
- **Cover:** union of the clipped supporter tops by coordinate compression, then `cover*10 >= base*9`. The message gives the floored percentage.
- **Centre:** doubled integer centre in the closed top of any one supporter.
- **Layer:** max(supporter layer) + 1.
- All new codes are geometry codes (status DRAFT).
- The unchecked list for COLUMNS_V1 drops "Chất xếp nhiều tầng" and adds "Tải chồng cho phép trên bó (chưa có dữ liệu)". "Kê, chèn và chằng buộc", "Tải cục bộ đáy hầm" and "Ổn định phương tiện" were already present.
- Every entry point reuses `evaluate`: validate, save, open, compare, report, rebase candidate.

**D3 (planner `columns-v1`).**
- **Default path:** `preview(plan, algorithm)` with default `guillotine-single-layer-v1`. The guillotine best-area-fit was factored into `_floor_slot` with identical tie-breaks. The default output was checked byte-identical to the HEAD planner on the Baltimore plan, and the request URL from the UI is unchanged for the default.
- **Ordering:** units are processed in the order (requirement rank, −grid base area, grid dims, id).
- **Columns:** there is one open column per grid-dims key, so optional units can top up a column that required units started. A unit stacks at `z = below.z + grid_h(below)` when `z*1000 + exact_height_um ≤ hold_height*1000`, with `supported_by = [below]` and `layer = below.layer + 1`. Otherwise a new floor column is opened by guillotine.
- **Unplaced reasons:**
  - When there is no floor space left: STACK_HEIGHT if columns of that size already exist (all full), otherwise HEURISTIC_NO_SPACE.
  - MASS_LIMIT is per unit (lighter units may still go).
  - EXCLUDED, TOO_HIGH and FOOTPRINT_TOO_LARGE are reused.
- **Candidate and API:** the candidate carries `stacking = COLUMNS_V1`. Nothing is written. `POST /api/planner/preview?algorithm=columns-v1`; an unknown value gives 422.

**Rebase (M3A-05 choice): cascade drop.**
- When a cargo revision drops a placement (REMOVED or CHANGED), every placement resting on it, transitively, is also dropped with the new reason `SUPPORT_LOST` (`DroppedPlacement.reason` gains that value). The rebase candidate therefore has valid support geometry and can be checked and saved. The alternative, keeping the upper bundles and reporting SUPPORT_MISSING, would leave a candidate with geometry errors.
- `placed_dropped_on_rebase_count` (H2 shared rule) counts the same cascade, so the listing equals the real rebase.
- Single-layer plans have empty `supported_by`, so nothing cascades and their output is unchanged.
- The UI dropped list labels SUPPORT_LOST "Mất đỡ" and has a filter for it.

**D4 (UI/report).**
- **Planner select:** "Cách xếp thử" offers "Một tầng (như cũ)" and "Nhiều tầng theo cột (thử nghiệm)". The algorithm is part of the preview stale key. The preview summary reads "Nhiều tầng: N cột · tối đa M tầng · đã xếp P bó · chưa xếp U bó", and the reason filter gains STACK_HEIGHT.
- **Deviation:** D4.1 asks for multi-layer as the default for pipe lists. Existing browser specs, which may not be edited, run the default planner on the pipe list and assert single-layer results: display-units expects 167 placed, m2b expects unplaced > 0, m2d expects the SINGLE_LAYER notice. A multi-layer default would break them, so the default stays "Một tầng (như cũ)" for every plan. Root can flip the default together with those specs.
- **Table and panel:** the cargo table has a last column "Tầng" (1-based). The selected-bundle panel shows "Tầng N · Z … cm · Bó đỡ: … / đáy hầm".
- **2D views:** the 2D plan keeps one rect per placement, drawn bottom-up, with a "×N" label per column of more than one. The hold caption reads "BOX · NHIỀU TẦNG" for COLUMNS_V1. 3D unchanged, since it already used z_mm.
- **Report:** multi-layer-only keys `stacking`, `totals.layer_count`, `totals.column_count` and `placement.supported_by` are omitted for legacy reports (report_sha256 and JSON bytes unchanged). The MULTI_LAYER notice replaces SINGLE_LAYER, and reconcile checks `layer_count`. The page shows extra overview rows and "Tầng"/"Bó đỡ" columns, plus "×N" labels in the report SVG. The XLSX appends "Tầng"/"Bó đỡ" columns and the overview rows "Cách xếp", "Tổng số tầng" and "Số cột", for multi-layer only.

**D5.** Nothing out of scope was attempted.

## Baltimore / VINAFCO VR-SII result

The hold is an estimate, 56 405 × 10 343 × 5 408 mm. The voyage limit is 3 517.5 t.

| Algorithm | Placed | Columns | Max layers | Unplaced | Placed mass | Evaluate | Planner time (3 runs) |
|---|---|---|---|---|---|---|---|
| guillotine-single-layer-v1 | 167 | 167 | 1 | 909 HEURISTIC_NO_SPACE | 217.74 t | RULES_CHECKED, 0 issues | 0.049 / 0.049 / 0.077 s |
| columns-v1 | **1076/1076** | 98 | 18 | 0 | 1 125.55 t | RULES_CHECKED, 0 issues | 0.579 / 0.519 / 0.512 s |

The highest placement base is z = 5 032 mm, below the hold height of 5 408 mm. The time is `preview()` including `evaluate` on the cloud container, under the 2 s limit. Two runs give byte-identical JSON. This result covers floor area and height only; stack load, tanktop load, lashing and stability are unchecked (DA03).

## Who did what

| Part | Done by | Model / effort | Reviewed by lead |
|---|---|---|---|
| D1 field, serializer, codes, test_m3a_model.py | Lead | Opus 5.5 / medium | — (see failed attempts) |
| D2 support rules + test_m3a_rules.py (33 tests) | Subagent | sonnet / high | Diff re-read; full pytest re-run |
| D3 columns-v1 planner, route param, test_m3a_planner.py (7 tests) | Subagent | sonnet / high | Diff re-read; Baltimore and timing re-measured by lead |
| Rebase cascade, report/XLSX backend, report models, test_m3a_flow.py | Lead | Opus 5.5 / medium | — |
| D4a Workspace select/summary/Tầng/panel, client.ts, RebaseDropped | Subagent | haiku / high | Diff re-read; build re-run |
| D4b Viewer 2D labels, ReportPage, styles | Subagent | haiku / high | Diff re-read; build re-run |
| Browser spec tests/browser/m3a.spec.ts | Subagent | haiku / high | Re-run by lead with full suite; lead repaired the Mất đỡ option visibility (RebaseDropped.tsx) after the harden01 regression |
| Contract regeneration, verification, worker return, PR | Lead | Opus 5.5 / medium | — |

Why sonnet: D2 needs exact µm/µm² union-area, centre and level arithmetic, where an error silently admits unsupported stacks. D3 must keep the default planner byte-identical while sharing its guillotine code. The owner reserved sonnet for exactly these two parts. All other delegated parts used haiku.

## Failed attempts and deviations

- The haiku D1 worker stopped twice at the AGENTS.md first-request rule: the core and WORKSPACE_RULES.md are missing, and it could not verify the dispatch waiver itself. The lead did not override it and wrote D1 itself (about 10 lines). Later briefs quoted the dispatch waiver verbatim, and no worker blocked again.
- One D2 test (`exact µm² boundary`) monkeypatches `rules.Evaluation` to a namespace, so `evaluate` can be exercised on µm-only geometry with a legacy contract that rejects `dimensions_um`. µm-exact level rounding is also covered through real pipe-list units. Root may prefer a pipe-list-v2 fixture for the µm² boundary.
- Some level-mismatch tests also get an OVERLAP (a wrong z intersects the supporter); those tests filter it out.

## Commands and results

All of these were run by the lead on the final branch state:

| Command | Result |
|---|---|
| `python -m pip install -r requirements-dev.txt` | OK |
| `python -m pytest` (baseline on main) | 679 passed |
| `python -m pytest` (final) | **726 passed** (+47 new: model 5, rules 33, planner 7, flow 2) |
| `python tooling/export_contract.py`, then `npm ci`, `npm run contract` | Regenerated. The final re-run gives no diff. The openapi changes are additions only: the `algorithm` query parameter, `Plan.stacking`, five Issue codes, `SUPPORT_LOST`, `STACK_HEIGHT`, `columns-v1` and the optional report fields. |
| `npm run build` | PASS (only the existing chunk-size warning) |
| Browser, full suite incl. m3a.spec.ts (`LANG=C.UTF-8 npx playwright test --config playwright.cloud.config.ts`) | **55 passed** (52 existing + 3 new) in 4.2 min |
| `git status` after the browser run | Clean except work in progress; **no committed file under docs/reviews changed** |
| `python tooling/integration_check_pre_m2d.py .` | **29/29 PASS** |
| `PYTHONDONTWRITEBYTECODE=1 python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return` | PASS, 7 mandatory controls, 0 failed (INVOKED; see the final run in the PR) |

**Browser failure and repair.** The first full run gave 54 passed and 1 failed: `harden01.spec.ts:212` asserts that the rebase filter options are exactly [Tất cả, Bỏ, Đổi]. The new "Mất đỡ (0)" option broke it. Fix: that option renders only when SUPPORT_LOST rows exist, so the legacy UI is unchanged. The existing spec was not edited. After the fix the full suite gives 55/55.

**m3a.spec.ts:**
- **Desktop M3A-05 flow:** runs on a private backend on port 8769 with a temp data dir, the same pattern as m2d. It covers:
  - multi-layer preview, apply, the Tầng cell and the support detail;
  - 3D meshes equal to placements, with a stacked mesh at the right z;
  - 2D ×N labels;
  - save, reload and reopen;
  - the report notices (MULTI_LAYER, no SINGLE_LAYER), labels and totals;
  - the XLSX download;
  - a revision, NEEDS_RECHECK, and a rebase where the "Mất đỡ" rows match the server and the candidate has no geometry issues.
- **390px:** multi-layer preview and apply, no page overflow, and the Tầng column reached by the table's horizontal scroll.
- **Default:** stays single-layer.

**Observation O-M3A-1 (existing behaviour, not changed):** switching to VINAFCO 268 in the UI keeps the open plan's voyage limit (`switchVessel` takes `min(old, case)`; on a fresh page that is the 32 t demo limit). columns-v1 in the UI then places only 22/1076, with MASS_LIMIT on the rest, until the user sets "Giới hạn chuyến (kg)" to 3 517 500, exactly as display-units.spec already does for the single-layer planner. The backend VR-SII case plan places 1076/1076. Root or owner should decide whether a case switch should adopt the case voyage limit.

## DA01–DA05 application

- **DA01:** placements stay integer mm. Support level, area (µm²) and centre are exact integer µm. Planner footprints are rounded up to the mm grid, as before. UI values are display-only cm and are never round-tripped.
- **DA02:**
  - Plan, report and listing JSON are byte-identical for legacy plans: `stacking` and the multi-layer report keys are omitted when absent, and tests assert this.
  - Revision hashes, stored formats and existing contract fields are unchanged; the contract only gains additions.
  - Every new test uses a temp `SCST_DATA_DIR`, and the browser run used a temp data dir.
  - The integration check (8.1) confirms source data unchanged.
- **DA03:** COLUMNS_V1 checks and the report state that stack load ("Tải chồng cho phép trên bó (chưa có dữ liệu)"), tanktop load, lashing/dunnage and stability are unchecked, and the MULTI_LAYER notice says so. The hold stays ESTIMATED (GEOMETRY_UNVERIFIED notice).
- **DA04:** reuses the M1 Placement fields `z_mm`, `layer` and `supported_by`, plus `evaluate`, the guillotine code, the preview/apply flow, the viewer (3D unchanged) and the M2d report/XLSX. No new endpoint; only a query parameter.
- **DA05:** usable flow, proven by the backend `test_m3a_flow.py` and the browser `m3a.spec.ts`: open the pipe list in VINAFCO → multi-layer preview → apply → check without geometry errors → save → reopen → report and XLSX → new revision → recheck → new version with SUPPORT_LOST drops → save and CURRENT.

## Limitations and remaining owned work

- Default planner choice stays single-layer; see the D4 deviation. This is a root decision.
- O-M3A-1: a VINAFCO case switch in the UI keeps the earlier voyage limit (existing behaviour); a multi-layer plan in the UI needs the voyage limit set first.
- In 2D, lower bundles of a column are hidden under the top rect; the "×N" label shows the count.
- The 1 mm grid gap between layers is not modelled as dunnage.
- Owner-held M3b: mixed sizes in a column, dunnage, stack/tanktop load, CoG/stability, multiple holds, non-BOX holds, 3D per-layer drag, real cases and the measured hold.
- Root review on Windows: rerun everything, plan Baltimore by hand and inspect 3D. Then write docs/reviews/SCST_M3A_REVIEW.md, decide on D2.1 rounding and the D4.1 default, and sync CVF_SESSION, memory and status (root-owned files, not touched here).

## Repair round 1 (root RETURN_FOR_REPAIR on PR #6, same budget)

Root accepted the D2.1 level rule and the SUPPORT_LOST rebase cascade, and returned R1–R3. Repairs were made by subagents and reviewed by the lead (Opus 5.5 / medium), who re-read each diff and re-ran the checks.

| Item | Done by | Model / effort | Commit |
|---|---|---|---|
| R1 pipe-list default multi-layer | Subagent | haiku / high | see below |
| R2 voyage limit on case switch | Subagent | haiku / high | see below |
| R3 overlap-pass performance | Subagent | sonnet / high | af29e67, reverted in 50292e0, restored in 8d6021f |

**R1.**
- `Workspace.tsx` now keeps `plannerChoice` (null means automatic). The effective planner is the user's choice, otherwise `columns-v1` for a pipe-list plan and `guillotine-single-layer-v1` for other plans. An explicit choice sticks.
- **Root-authorized edits to existing specs** (exactly one added line each, no assertion changed or removed; `git diff --numstat` shows only additions): `await page.getByLabel("Cách xếp thử").selectOption("guillotine-single-layer-v1");` at
  - tests/browser/display-units.spec.ts:123
  - tests/browser/m2b.spec.ts:87
  - tests/browser/m2b.spec.ts:193
  - tests/browser/m2d.spec.ts:170
  - tests/browser/sup01.spec.ts:146
- Demo-plan planner uses (m2b.spec.ts:57, 152, 166, 176) keep the single-layer default and were not edited.
- The m3a.spec "default" case now asserts that a pipe list defaults to columns-v1 without touching the select, and that the demo plan stays single-layer.

**R3.**
- **Profile:** about 97% of the columns-v1 preview was `evaluate()`'s all-pairs OVERLAP loop (578 350 `overlaps` calls). Pydantic validation and serialization each took ≤ 0.02 s.
- **Change:** `_overlap_pairs` runs an x-sweep with strict `<` on y and z, skips empty volumes and re-sorts the pairs to the old (i, j) order. The `add()` order, the 200-issue cap and the messages are unchanged.
- **Proof:** `tests/backend/test_m3a_perf.py` (8 tests) compares `evaluate().model_dump_json()` against a frozen copy of the original loop on these cases:
  - the Baltimore single-layer and columns-v1 candidates;
  - a pipe plan with more than 200 overlaps (truncation order);
  - scattered and yawed plans, touching faces, identical boxes;
  - 300 random box sets.
- **Lead review:** a pair overlapping in x always has one box with x0 ≤ the other's x0, so it is found while the earlier box is active. Ties are included. The strict comparisons match `geometry.overlaps`.
- **Timings (container, 3 runs, seconds):**

| Measure | Before | After |
|---|---|---|
| `preview` columns-v1 | 0.508 / 0.512 / 0.539 | 0.053 / 0.054 / 0.084 |
| `evaluate` alone (columns candidate) | 0.594 / 0.651 / 0.583 | 0.021 / 0.020 / 0.022 |
| HTTP POST columns-v1 | 0.733 / 0.660 / 0.664 | 0.150 / 0.107 / 0.173 |
| `preview` default | 0.063 / 0.082 / 0.049 | 0.053 / 0.079 / 0.037 |

- **History:** root's "R3 cancelled" comment arrived after `af29e67` was pushed, so the lead reverted it (`50292e0`, a byte-identical return to 8d205ef). Root's next comment said to keep R3, so it was restored (`8d6021f`, identical to af29e67). No history was rewritten.
