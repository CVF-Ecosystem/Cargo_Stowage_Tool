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
| Browser spec tests/browser/m3a.spec.ts | Subagent | haiku / high | Re-run by lead with full suite |
| Contract regeneration, verification, worker return, PR | Lead | Opus 5.5 / medium | — |

Why sonnet: D2 needs exact µm/µm² union-area, centre and level arithmetic, where an error silently admits unsupported stacks. D3 must keep the default planner byte-identical while sharing its guillotine code. The owner reserved sonnet for exactly these two parts. All other delegated parts used haiku.

## Failed attempts and deviations

- The haiku D1 worker stopped twice at the AGENTS.md first-request rule: the core and WORKSPACE_RULES.md are missing, and it could not verify the dispatch waiver itself. The lead did not override it and wrote D1 itself (about 10 lines). Later briefs quoted the dispatch waiver verbatim, and no worker blocked again.
- One D2 test (`exact µm² boundary`) monkeypatches `rules.Evaluation` to a namespace, so `evaluate` can be exercised on µm-only geometry with a legacy contract that rejects `dimensions_um`. µm-exact level rounding is also covered through real pipe-list units. Root may prefer a pipe-list-v2 fixture for the µm² boundary.
- Some level-mismatch tests also get an OVERLAP (a wrong z intersects the supporter); those tests filter it out.

## Commands and results

BROWSER_RESULTS_PLACEHOLDER

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
- In 2D, lower bundles of a column are hidden under the top rect; the "×N" label shows the count.
- The 1 mm grid gap between layers is not modelled as dunnage.
- Owner-held M3b: mixed sizes in a column, dunnage, stack/tanktop load, CoG/stability, multiple holds, non-BOX holds, 3D per-layer drag, real cases and the measured hold.
- Root review on Windows: rerun everything, plan Baltimore by hand and inspect 3D. Then write docs/reviews/SCST_M3A_REVIEW.md, decide on D2.1 rounding and the D4.1 default, and sync CVF_SESSION, memory and status (root-owned files, not touched here).
