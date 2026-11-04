# SCST — SUP-02A worker return

Status: RETURNED_FOR_REVIEW

- Role: IMPLEMENTATION_WORKER (Claude Cloud). The lead session acted as in-run advisor and reviewer of its own subagents; this does not replace the root's independent REVIEW.
- Branch: `claude/sup-02a-cargo-revisions`, from `main` a9038c8. Not merged, and nothing was pushed to main.
- Inputs acknowledged before edits: AGENTS.md, docs/specs/SCST_SUP_02A.md, docs/work_orders/SCST_SUP_02A.md, CVF_SESSION/handoffs/AGENT_HANDOFF_SUP_02A.md, SCST-DA01..DA05, .cvf/manifest.json, and the active session state.
- The hidden CVF core (`../.Controlled-Vibe-Framework-CVF`) is absent in the cloud. It was not cloned or initialized.
- No governance or AI-behaviour claim is made. The product makes no provider or network calls, and the work used no secrets or connectors.

## Changed paths (all inside worker ownership)

**Backend**
- `services/backend/app/domain/model/__init__.py`: `scst.pipe-list.v2`, `CargoRevisionRef`, `PipeSourceRefV2`, and a units/placements limit of 2000. `cargo_revision` is omitted from JSON when absent.
- `services/backend/app/domain/rules/__init__.py`: v2 gets v1 issue truncation.
- `services/backend/app/domain/cargo_revisions/__init__.py` (new): a pure module for batch validation, apply, replay/hash, provenance and derived units.
- `services/backend/app/adapters/storage.py`: D7 migration/backup, `open_migrated`, `fetch_plan` and `listing_rows`.
- `services/backend/app/adapters/revision_store.py` (new): an append-only store using `BEGIN IMMEDIATE`.
- `services/backend/app/adapters/plan_binding.py` (new): the shared binding service, recheck, rebase and revision views.
- `services/backend/app/api/cargo_models.py` (new) and `services/backend/app/api/routes.py`.
- `services/backend/app/adapters/csv_import.py`: one line drops `cargo_revision` when CSV converts a plan to m2a.

**Tests**
- `tests/backend/test_cargo_revisions_domain.py` (34 tests, new)
- `tests/backend/test_revision_store.py` (12, new)
- `tests/backend/test_sup02a_api.py` (72, new)
- `tests/browser/sup02a.spec.ts` (3, new)

**Frontend**
- `apps/frontend/src/features/CargoRevisionPanel.tsx` (new)
- `Workspace.tsx`, `ComparisonPanel.tsx`, `model.ts`, `api/client.ts`, `styles.css`

**Regenerated with the existing tools**
- `contracts/openapi.json` (`python tooling/export_contract.py`)
- `apps/frontend/src/api/generated/api.ts` (`npm run contract`)

**Evidence**
- This file
- `docs/reviews/SCST_SUP_02A_EVIDENCE/browser/*.png`, written by the new spec

**Untouched:** `services/backend/data/**` (baltimore.json sha256 `429acdeb…0330` unchanged), `.cvf/**`, `scripts/**`, `.github/**`, requirements, package files, the existing browser specs, the SUP-01 evidence, docs/specs, docs/work_orders and CVF_SESSION. The check was `git diff --quiet main..HEAD -- <paths>`.

## Decisions per design item

**D1 – Revisions**
- R0000 is derived from baltimore.json and never stored.
- `content_sha256` is the SHA-256 of `json.dumps(groups, sort_keys, (',',':'), ensure_ascii=False)` UTF-8. The R0000 value is `9392efc3…49a4`.
- Group state includes the active `bundle_ids`, `next_bundle_index` and `bundle_overrides`, so ID stability is part of the hashed content. Provenance is not hashed; it is re-derived by replay from the stored source and changes.
- Reading Rk replays only records[:k]. A later broken record does not block earlier revisions, and a mismatch refuses to serve that revision and every later one. Nothing is repaired automatically.
- A wrong parent returns 409 `ParentConflict` and writes nothing.

**D2 – Update batches**
- All three change types and confirmations are implemented as specified.
- Decreasing `bundle_count` drops ids from the end. Increasing it issues `next_bundle_index`, so a dropped id is never reissued.
- `ADD-nnn` numbering counts withdrawn ADD groups too.
- Changes within a batch apply in order.
- A bundle added by raising `bundle_count` gets its own `created` provenance stamp, so it is not shown as WORKBOOK.

**D3 – Limits and validation**
- Every limit is enforced in the domain with per-change errors `{index, field, message}` in Vietnamese. Group and total-bundle limits are checked on the final state.
- The 1 MiB limit is checked on the raw request body.
- The `/api/cargo-revisions/preview` endpoint never writes.
- Integers must be real ints. Bool and float are rejected and no value is rounded.

**D4 – Provenance**
- Each field carries a `{revision_id, source, confirmation}` stamp; WORKBOOK means R0000.
- Overrides have per-bundle stamps.
- A unit's `source_ref.revision_id` is the newest revision among its feeding fields. Its confirmation is UNVERIFIED if any feeding field is UNVERIFIED, else CONFIRMED if any is CONFIRMED, else WORKBOOK.
- An override hides only the group field it replaces.

**D5 – Revision pinning**
- `plan_binding.bind()` is the single gate. It is called from validate, snapshot save, snapshot open, both sides of compare, planner preview, the pipe-list preview input, the CSV preview input, revision plan-preview and rebase.
- Legacy contracts return immediately without opening the DB.
- A v1 plan is treated as pinned to R0000 without rewriting its data.
- A legacy plan's JSON is byte-identical. `cargo_revision` is omitted, and v1 `source_ref` keeps its own model.
- `/api/pipe-list/preview` still returns v1 at R0000. The UI uses v2 plan-preview only when the latest revision is newer than R0000, so the existing browser specs are unchanged.

**D6 – Recheck and rebase**
- The listing adds `cargo_revision_id`, a status and counts.
- `placed_affected` counts placed bundles that were removed or changed.
- Rebase keeps a placement only when the bundle exists and its `dimensions_um` and `mass_g` are unchanged. It keeps `requirement` by id, lists dropped placements, returns the comparison from `domain/comparison`, and never writes.
- Extra status `REVISION_UNAVAILABLE`: when a pinned or latest revision fails integrity, the listing stays usable instead of failing. This is a data-preserving choice outside the three named statuses, and the root should accept or reject it.

**D7 – Storage and migration**
- The `snapshots` DDL and its strict column check are unchanged.
- Opening an existing DB without `cargo_revisions` makes a one-time `scst.sqlite3.pre-sup02a.bak` through the sqlite backup API. The backup goes to a temp file and is then renamed, and an existing backup is never overwritten.
- `cargo_revisions` has a fixed DDL, and its column names and types are checked. A foreign structure is rejected in Vietnamese with no drop or reset.
- Writes use a `BEGIN IMMEDIATE` transaction.
- Dropping the table leaves the snapshots intact; this is tested.

**D8 – Interface**
- The "Dữ liệu hàng" panel shows the revision in use and the latest, the history, provenance detail, and the batch form. The form works in kg/cm/mm, and kg and cm convert to g and µm by exact string conversion.
- "Tạo revision" is enabled only after a valid preview of the identical draft.
- The saved list shows "Cần kiểm lại" with counts, plus "Tạo bản theo dữ liệu mới". That action loads the candidate, shows dropped placements, and opens the existing ComparisonPanel with the old snapshot as A.
- The UI is in Vietnamese, works at 390px, and adds no library.

## Who did what (models)

| Part | Scope | Model |
|---|---|---|
| Lead | Design (scratchpad DESIGN.md), Plan v2 model and serializer, rules flag, review of every diff, own re-runs, browser harness, commits, this return, PR | Opus 5.5 (lead) |
| A | `domain/cargo_revisions` + domain tests (replay/hash/provenance/limits) | sonnet, high |
| B | SQLite migration/backup + append-only store + tests | sonnet, high |
| C | binding service at all entry points, recheck, rebase, routes/models, API tests | sonnet, high |
| D | frontend panel, v2 pipe mode, recheck labels, rebase UI | sonnet, high |
| E | `tests/browser/sup02a.spec.ts` | haiku, high |

The lead re-read each diff and re-ran the tests before committing. At most two subagents edited at the same time (A and B), always on disjoint files.

## Commands and results (run by the lead, 2026-11-04)

- `python -m pip install -r requirements-dev.txt`: OK. The bare `pip` pointed to a different interpreter on first try.
- `python -m pytest -q`: baseline before edits `104 passed`; final `222 passed, 1 warning`. The warning is the existing starlette/httpx deprecation.
- `python tooling/export_contract.py`, then in apps/frontend `npm ci`, `npm run contract`, `npm run build`: OK, `✓ built`. Regeneration is idempotent with no diff after the commit.
- Browser:
  - Baseline before frontend changes: `36 passed (1.5m)`.
  - Final full suite including `tests/browser/sup02a.spec.ts`: `39 passed (1.7m)`.
  - E also ran `sup02a --repeat-each=2` on one server: `6 passed`.
- `PYTHONDONTWRITEBYTECODE=1 python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return`: `RESULT: PASS mandatoryControls=7 failed=0`. Results for the final tree are in the PR.

How the browser suite was run in the cloud:
- `playwright.config.ts` runs a Windows `..\..\.venv\Scripts\python.exe`, and `@playwright/test` wants chromium build 1248 while the image provides 1243.
- I used an untracked, git-excluded override `apps/frontend/playwright.linux.local.config.ts`. It spreads the repo config and changes only the webServer command to `python -m uvicorn …`, a temp `SCST_DATA_DIR`, and `launchOptions.executablePath=/opt/pw-browsers/chromium`. Tests, specs and the committed config are unchanged.

## Failed attempts and incidents

- **First browser run:** it failed to launch (chromium 1248 missing). Fixed with the executablePath override above; the checks themselves were not changed.
- **SUP-01 evidence overwritten:** the existing specs write screenshots into the tracked `docs/reviews/SCST_SUP_01_EVIDENCE/browser` through `tests/browser/evidence.ts`, so every full run overwrote that historical evidence. After each run it was restored with `git checkout -- docs/reviews/SCST_SUP_01_EVIDENCE` and was never committed. The new spec writes to `SCST_SUP_02A_EVIDENCE/browser` instead.
  - Root may want a follow-up so evidence.ts writes outside closed evidence. That needs authority to edit an existing spec helper.
- **Label collision (D's first run):** a new checkbox label collided with an existing `getByText('Kích thước cần xác minh')` locator in pipe-list.spec. The label was renamed and the existing spec was not touched.
- **Repeated runs (E):** under `--repeat-each=2`, a fixed batch value became a no-op. The spec now derives values from the live latest revision.

## DA application

- **DA01:** stored µm and g are exact and never rounded. The UI parses kg and cm strings to integers without floats (`parseKg`, `parseCmToUm`, BigInt). The browser test checks the stored integers against the typed inputs.
- **DA02:** every backend test uses a temp `SCST_DATA_DIR`, and the browser suite uses a temp directory. Migration makes a one-time backup and refuses an unknown schema without reset. Snapshot rows are byte-identical after every operation (tested). There is an undo path.
- **DA03:** each revision records its source (kind/reference/date/note) and a confirmation per change. `dimension_warning` turns off only when CONFIRMED. Values with a source are labelled WORKBOOK, CONFIRMED or UNVERIFIED in the API and UI. No tolerance was invented.
- **DA04:** reused Plan, pipe_registry, `domain/comparison`, the planner, the storage connection, ComparisonPanel and the save/open flow. Added only the revision store, binding service and panel.
- **DA05:** the internal flow was walked end to end in the browser before handing back: open → save → sourced batch → "Cần kiểm lại" → rebase → compare → save → reopen both, at desktop and 390px. A test count does not replace owner flow acceptance; business acceptance remains with the owner.

## Limitations and remaining owned work

- **Gates and core:** the root must re-run the browser suite on Windows with the repo config and run the reviewer-fast and pre-commit gates locally with the hidden core present.
- **Stored source integrity:** provenance is not hashed. Tampering a stored `source` text is detected only if it makes the record invalid. A record-level hash would be a SPEC decision.
- **Replay cost:** each v2 entry point replays from R0000, which is fine for small revision counts. No cross-request cache was added.
- **Unit name and order:** the ceiling-mm values are derived exactly as in v1.
- **Out of scope, untouched:** SUP-02B, SUP-03, M2d, other datasets, Excel/AI import, and revision delete/merge.
- **Root decisions requested:**
  - the `REVISION_UNAVAILABLE` status
  - `placed_affected` counting any changed field, while rebase drops only dimension/mass changes
  - the extra `created` provenance stamp
