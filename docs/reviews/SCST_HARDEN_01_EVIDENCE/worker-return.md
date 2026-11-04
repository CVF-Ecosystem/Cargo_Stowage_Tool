# SCST — HARDEN-01 worker return (paged rebase drops, recheck counts, replay cache, pre-parse limits, Windows lock)

Status: WORKER_RETURN
Risk: R2
Worker: Claude Cloud implementation worker (lead session as advisor and internal reviewer; Sonnet/Haiku subagents, see "Who did what")
Reviewer: root-independent-implementation-reviewer (Claude local) — pending; nothing here is self-approval

Branch `claude/harden-01` from `main` 11dacda. SPEC [docs/specs/SCST_HARDEN_01.md](../../specs/SCST_HARDEN_01.md), work order [docs/work_orders/SCST_HARDEN_01.md](../../work_orders/SCST_HARDEN_01.md), handoff `CVF_SESSION/handoffs/AGENT_HANDOFF_HARDEN_01.md`.

CVF Agent Declaration (at start): project Cargo_Stowage_Tool; CVF core `../.Controlled-Vibe-Framework-CVF` @ c4c8767 — **not available in the cloud**, not initialized (as instructed; no core clone or initialize scripts run); phase BUILD; risk R2; live governance evidence required YES (this tranche makes no CVF-governance claim); role IMPLEMENTATION_WORKER; active handoff AGENT_HANDOFF_HARDEN_01.md; next allowed move: implement on a non-main branch and return by pull request; parked: M3/M4/M5, O3/O7-O11, OD-only recheck policy, live-provider proof, business acceptance, merge.

## Changed paths

All inside worker ownership. Untouched: `services/backend/data/**`, `.cvf/**`, `scripts/cvf_gates/**`, `.github/**`, `tooling/**`, requirements, `package.json`/`package-lock.json`, every existing test and browser spec, CVF_SESSION, memory, status, specs, work orders, `docs/reviews/**` other than this file.

| Path | Change | Item |
|---|---|---|
| `services/backend/app/adapters/plan_binding.py` | `_drop_reason` (single rebase rule) + `_dropped_count`; recheck/listing add `placed_dropped_on_rebase(_count)`; replay cache `_replay`, `_Records`, `clear_replay_cache` | H2, H3 |
| `services/backend/app/adapters/revision_store.py` | `read_rows` (raw columns) and `decode_rows`; `read_records` = decode(read_rows) — identical output; `append` unchanged | H3 |
| `services/backend/app/api/cargo_models.py` | `SnapshotListItem.placed_dropped_on_rebase_count: int` (added) | H2 |
| `services/backend/app/api/routes.py` | `_cargo_body` + `_BoundedBodyRoute`; the two cargo-revision POSTs registered with `add_api_route(..., route_class_override=...)`, same models/responses | H4 |
| `services/backend/app/adapters/vessel_profile_store.py` | `_process_lock(base)`: POSIX flock as before, Windows `msvcrt.locking` on `vessels/.lock` with bounded retry | H5 |
| `contracts/openapi.json`, `apps/frontend/src/api/generated/api.ts` | regenerated; only diff is the added `placed_dropped_on_rebase_count` (required integer) | H2 |
| `apps/frontend/src/features/RebaseDropped.tsx` (new), `Workspace.tsx`, `styles.css` | paged (50) + filtered dropped list; recheck text shows both counts | H1, H2 |
| `tests/backend/test_harden01_recheck_counts.py` (6), `test_harden01_replay_cache.py` (7), `test_harden01_body_limit.py` (11), `test_harden01_profile_lock.py` (5) | new tests | H-02..H-05 |
| `tests/browser/harden01.spec.ts` | new browser spec, desktop + 390px | H-01, H-02 labels |

## Decisions per item

**H1 (H-01).** New component `RebaseDropped.tsx`: filter select «Lọc vị trí bị bỏ» (Tất cả / Bỏ / Đổi with counts), 50 rows per page, status `Trang P/T · dòng a–b trên tổng N`, buttons «Trang vị trí trước» / «Trang vị trí sau» (named differently from the cargo table's «Trang trước»/«Trang sau» so role lookups stay unambiguous). Filter and page reset on every new rebase result; filter change returns to page 1. Summary line and per-row text are unchanged (existing specs depend on them). Rows are kept in server order.

**H2 (H-02).** `placed_dropped_on_rebase_count` counts placements whose unit `rebase` would drop, using the very same function `_drop_reason` that `rebase` now calls (REMOVED when absent from target; CHANGED when absent from pinned or dimensions/mass differ). `placed_affected_count` is unchanged. 0 for NOT_APPLICABLE and REVISION_UNAVAILABLE. The internal `recheck()` dict also gains the key (report_service picks fields explicitly, so the report model is unchanged). Field is required in the contract (always present), an addition only.
*SPEC ambiguity recorded:* SPEC asks for the label «bó đã đặt có dữ liệu đổi», but the existing (non-editable) specs `sup02a.spec.ts:168` and `sup03.spec.ts:309` assert the substring `… bó; N bó đã đặt bị ảnh hưởng`. Chosen option that preserves existing behaviour: keep that prefix and make the meaning explicit right after it:
`Cần kiểm lại: thêm A · bỏ R · đổi C bó; N bó đã đặt bị ảnh hưởng (có dữ liệu đổi) · D vị trí sẽ bỏ khi tạo bản mới (REV)`.
If root prefers the exact SPEC wording, it needs a root-owned change to those two existing specs. The report page (`ReportPage.tsx`, «bó đã đặt bị ảnh hưởng») is left unchanged (H6).

**H3 (H-03).** In-process LRU (`OrderedDict`, max 8, `threading.Lock`) in `plan_binding`. Every request still reads rows from the DB; the key is SHA-256 of `json.dumps` of the raw row tuples of the replayed prefix, in sequence order. *Decision:* the key covers **all eight selected columns** (revision_id, dataset_id, sequence, parent_revision_id, created_utc, source_json, changes_json, content_sha256), a superset of the four SPEC names, because created_utc and parent_revision_id also reach the served view and a hand-edit of them must not be masked (tested). Cached value is the views list or the integrity error (re-raised with same revision id/message). Callers get a deep copy (only of the picked view for `view()`); only `list_revisions`, which reads through `summary_of_view`, shares the cached list. `create_revision`'s `build()` keeps an uncached replay inside the write transaction (it receives decoded records only; uncached is the safer choice for a write). Integrity semantics unchanged: all SUP-02A/revision-store tests pass unedited.

**H4 (H-04).** A `fastapi.routing.APIRoute` subclass reads the body before FastAPI's own parse: numeric `Content-Length` > 1 MiB → reject without reading; otherwise stream and stop as soon as the running size exceeds 1 MiB; then sets `request._body` so FastAPI parses the bounded bytes. Error unchanged: 400 `{"message": "Dữ liệu gửi lên quá lớn.", "errors": check_payload_size(size)}`. Endpoint functions and `_check_size` unchanged. `contracts/openapi.json`: **no change** from H4 (verified by regenerating). The two vessel-profile upload endpoints already rejected pre-parse (`_upload_body`, 28 MiB, 413) — unchanged, now pinned by tests.

**H5 (H-05).** `_process_lock(base)` inside the existing thread lock. POSIX: unchanged directory-fd `fcntl.flock`. Windows: `os.open(vessels/.lock, O_RDWR|O_CREAT)`, `msvcrt.locking(fd, LK_LOCK, 1)` at offset 0, retried up to `LOCK_WAIT_SECONDS = 60` (LK_LOCK itself gives up after ~10 s), then `StoreError('Kho hồ sơ tàu đang bận; hãy thử lại.')`; always unlock+close. `.lock` never lists as a profile id (ID_PATTERN needs a leading `[A-Z0-9]`; tested).

**H6.** Nothing outside scope was implemented (no provenance hash, OD-only policy, GLB origin, evidence images, M3).

## Tests and what they prove

- `test_harden01_recheck_counts.py`: count == `len(rebase.dropped_placements)` for: REMOVED on a v1 plan (1), mass change on a v2 plan (1, CHANGED), confirmation/pipe-count/warning-only changes (0 while affected ≥ 1), a mixed batch (2 of 3 affected), CURRENT/NOT_APPLICABLE (0), REVISION_UNAVAILABLE (0); old fields still present.
- `test_harden01_replay_cache.py`: hand-edited `content_sha256`, `changes_json` and `created_utc` after the cache is warm are detected/reflected on the next read; a spy on `cr.replay` sees zero replays on identical reads and new keys after a new revision; mutating returned views does not leak into the cache; never more than 8 entries; a cached integrity failure re-raises the same revision id/message (GET still 400).
- `test_harden01_body_limit.py`: over-limit non-JSON body with Content-Length → 400 size error (was 422) on both endpoints; chunked body without Content-Length → 400 and the server stops after 17 of 64 offered 64 KiB chunks; declared length > limit with a small body → 400 without calling `stream()`; valid small drafts still 200, invalid small JSON still 422, rejected requests write no row; vessel-profile uploads 413 pre-parse (declared and chunked). Against the original routes.py, 7 cargo tests fail as expected.
- `test_harden01_profile_lock.py`: two spawned processes × 5 ids racing for v1 → exactly one `ok`, one `VersionConflict`, one `v1` dir, no `.tmp-*`; parent holding `_process_lock` blocks a child process's append for 1.5 s and it completes once released (fails if flock is replaced by `pass` — mutation-checked by the worker); fake-`msvcrt` tests of the Windows branch (lock/unlock order on one fd at offset 0, retry loop, bounded give-up without unlock, unlock on exception, `.lock` path not listed).
- `tests/browser/harden01.spec.ts`: a v2 plan with 140 placed bundles and a revision that changes mass of one group (70 placed) and removes 60 placed bundles of another → API `placed_dropped_on_rebase_count` = 130 and the saved-list/selected texts show both labelled numbers; UI rebase shows 50 rows, `Trang 1/3 · dòng 1–50 trên tổng 130`, every page's ids/reasons equal the server order, last page 30 rows, filter Bỏ (60, 2 pages) and Đổi (70, 2 pages) reset to page 1; dropped panel height 412 px. At 390 px: 50 rows, filter and paging work, `scrollWidth` ≤ 391 and the panel's right edge ≤ 390.

## H3 timing (20 revisions, 5 saved plans, median of 15, `TestClient`, same machine)

| Request | Before (main 11dacda + H2) | After |
|---|---|---|
| `GET /api/snapshots` | 259.6 ms | 76.8 ms / 74.2 ms (two runs) |
| `POST /api/validate` (bind v2 @R0020) | 128.1 ms | 43.1 ms / 42.7 ms |

Script: 20 `ADD_GROUP` revisions through the API, 5 saved v2 plans pinned to R0020 and R0011..R0014, one warm-up call. A first H3 version that deep-copied the whole view list on every hit measured ~190 ms / ~75 ms; copying only the picked view fixed it.

## Commands and results (lead re-ran each)

| Command | Result |
|---|---|
| `python -m pip install -r requirements-dev.txt` | ok |
| `python -m pytest -q` (baseline) | 650 passed |
| `python -m pytest -q` (final) | 679 passed (650 baseline unchanged + 29 new) |
| `python tooling/export_contract.py`; `npm ci`; `npm run contract`; `npm run build` | ok; contract diff = the one added field; build ok (pre-existing chunk-size warning) |
| `npx playwright test -c playwright.local.config.ts harden01` | 2 passed |
| `npx playwright test -c playwright.local.config.ts` (full suite) | first run 9 failed / 43 passed (cause: the first `harden01` spec mutated the shared suite DB, see Failed attempts); after isolation, without UTF-8 locale 51 passed / 1 failed (`m2d.spec.ts:157` download name "download" — the known Linux-locale issue recorded in the M2d worker return); with `LANG=C.UTF-8` **52 passed** (50 existing + 2 new) |
| `git status` after browser runs | clean; no file under `docs/reviews/` changed |
| `python tooling/integration_check_pre_m2d.py .` | 29/29 PASS |
| `PYTHONDONTWRITEBYTECODE=1 python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return` | `RESULT: PASS phase=worker-return mandatoryControls=7 failed=0` (run on a clean tree at 9c47068; ROLE/APPL NOT_APPLICABLE_WITH_REASON: no candidate in worktree scope) |

Browser runs used an untracked, `.git/info/exclude`d `apps/frontend/playwright.local.config.ts` that imports the committed config and overrides only the webServer command (Linux `python -m uvicorn`), a temp `SCST_DATA_DIR`, and the chromium `executablePath` `/opt/pw-browsers/chromium`. Screenshots go to the temp evidence dir (`tests/browser/evidence.ts`), never `docs/reviews/`.

## Who did what

| Part | Who | Model / effort | Why |
|---|---|---|---|
| Design, split, H2 backend + its tests, all reviews, H3 timing, fixes, verification, worker return, PR | lead session | Opus 5.5, medium | advisor/internal reviewer role |
| H4 pre-parse limit + tests | subagent | Haiku, high | default model |
| H5 cross-process lock + two-process tests | subagent | **Sonnet, high** | cross-platform locking with spawned-process tests and a Windows branch that can only be simulated here — needs careful concurrency reasoning |
| H3 replay cache + tests | subagent | **Sonnet, high** | cache must not weaken integrity semantics (key choice, mutation safety, error caching, thread safety) |
| H1/H2 frontend | subagent | Haiku, high | default model |
| Browser spec | subagent | Haiku, high | default model |

Lead review changes to subagent output: renamed the rebase pager buttons to avoid duplicate accessible names with the cargo table pager; moved the browser spec onto its own isolated backend; replaced a failing page-growth assertion in the browser spec (a criterion the lead's brief had invented, not in the SPEC) by a recorded measurement (see Limitations).

## Failed attempts

- First H2 test asserted removed_count 1 after shrinking a 20-bundle group to 18 (actually 2); test expectation fixed.
- Frontend subagent first stopped at INTAKE because the CVF core is absent; resumed after the lead pointed at the work order's instruction to note it and continue.
- Browser spec first required whole-page growth < 1500 px after rebase; measured 6545 px (see Limitations), so it became a measurement.
- H3 first version deep-copied all views on every hit (slow, see timing).
- The first `harden01.spec.ts` created its revisions on the shared suite server; because it sorts before `m2b`/`m2c`/`m2d`/`pipe-list`/`sup01`, the removed bundles made 9 of their tests fail (they expect the full 1076-bundle list). Fix: the spec now starts its own backend (same app, port 8767, own temporary `SCST_DATA_DIR`; on Windows it uses `.venv/Scripts/python.exe` like the committed config, elsewhere `SCST_PYTHON` or `python`). Root should confirm this on Windows.

## DA01–DA05 application

- **DA01** exact integers: the new count is an integer count from integer unit data; mass/dimension comparison in `_drop_reason` is exact integer equality, unchanged from rebase; nothing rounded.
- **DA02** no storage format change: no DB schema/rows, profile files or `baltimore.json` touched; `.lock` is a new empty lock file only on Windows; every test uses a temp `SCST_DATA_DIR`; revision hashes unchanged (integrity tests and integration check 29/29, incl. "source data unchanged byte-for-byte").
- **DA03** labels match meaning: two numbers with distinct labels («bó đã đặt bị ảnh hưởng (có dữ liệu đổi)» vs «vị trí sẽ bỏ khi tạo bản mới»), computed by the same rule as rebase; filter labels Bỏ/Đổi match REMOVED/CHANGED.
- **DA04** local fixes: one shared helper extracted from rebase, a cache wrapper around existing replay calls, a route class around unchanged endpoints, a lock context manager around the unchanged append body. No rewrites.
- **DA05** usable flow: browser spec drives save → new revision → listing labels → rebase → paging/filter at desktop and 390 px.

## Limitations

- **Windows branch of H5 is only simulated here** (fake `msvcrt`); the real two-process test on Windows is for root to run on the Windows machine (`python -m pytest tests/backend/test_harden01_profile_lock.py`).
- **Whole-page height after rebase** still grows ~6545 px at desktop with 130 drops: the dropped panel itself is 412 px, but the rebase opens the comparison section (+~4467 px, 50 tall rows) and the cargo table switches to the candidate (+~1942 px, 50 rows/page). Those sections are outside H1 (H6 "Thay đổi giao diện khác"); root may open a follow-up if wanted. The old dropped `<ul>` already had a 14rem scroll box, so H1 mainly adds paging/filter/totals rather than height savings.
- The rebase panel shows revision-level bundle counts («Bó thêm 0, bỏ 60, đổi 160») next to placement counts («bỏ 130 vị trí») in one line — unchanged pre-existing text, noted for DA03 review.
- `harden01.spec.ts` spawns its own uvicorn on port 8767; that port must be free.
- Linux browser runs need a UTF-8 locale for the pre-existing M2d download-name check.
- CVF core not present in the cloud; no doctor/core gates run beyond the project runner.
- No CVF-governance claim; no provider calls.

## Remaining owned work

- Root: independent review on Windows incl. H-05 two-process test; decide H2 label wording (see SPEC ambiguity); write `docs/reviews/SCST_HARDEN_01_REVIEW.md`; merge decision; continuity sync.
- Owner: M3 data (hold measurements, real cases), business acceptance.
