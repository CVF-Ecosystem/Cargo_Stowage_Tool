# SCST — M5b worker return (automatic local backup)

Status: WORKER_RETURN
Risk: R2
Worker: Claude Cloud implementation worker (lead session as advisor and internal reviewer; Sonnet/Haiku subagents, see "Who did what")
Reviewer: root-independent-implementation-reviewer (Claude local) — pending; nothing here is self-approval

Branch `claude/m5b-auto-backup` from `main` 82f8356. SPEC [docs/specs/SCST_M5B.md](../../specs/SCST_M5B.md), work order [docs/work_orders/SCST_M5B.md](../../work_orders/SCST_M5B.md), handoff `CVF_SESSION/handoffs/AGENT_HANDOFF_M5B.md`.

CVF Agent Declaration (at start): project Cargo_Stowage_Tool; CVF core `../.Controlled-Vibe-Framework-CVF` @ c4c8767 — **not available in the cloud**, not initialized (as instructed; no core clone or initialize scripts run; `../WORKSPACE_RULES.md` likewise absent). Phase BUILD; risk R2; live governance evidence required YES (this tranche makes no CVF-governance claim and the product makes no provider or network call); role IMPLEMENTATION_WORKER; active handoff AGENT_HANDOFF_M5B.md; next allowed move: implement on a non-main branch and return by pull request; parked: M5c installer, schedule while the app is closed, encryption, off-machine copy, M3b, M4, observations, live-provider proof, business acceptance, merge.

Time note: the session started at 06:18Z, so the effective worker window was ~40 minutes before the 07:00Z PR deadline (budget 70). The work was split accordingly.

## Changed paths

All inside worker ownership. Untouched: `services/backend/data/**`, `.cvf/**`, `scripts/cvf_gates/**`, `.github/**`, `tooling/**`, requirements, `package.json`/`package-lock.json`, every existing test and browser spec, CVF_SESSION, memory, status, specs, work orders, `docs/reviews/**` other than this folder. No dependency added (stdlib only).

| Path | Change | Item |
|---|---|---|
| `services/backend/app/adapters/backup_auto.py` (new) | `run_if_due`, `run_now`, `has_data`, `list_files`, `last_error`, `start_background`, `NoData`, `AutoBackupFailed`, `NAME_PATTERN`, `INTERVAL_HOURS=20`, `KEEP=10` | D1 |
| `services/backend/app/main.py` | startup hook `_start_auto_backup` (try/except, appended to `app.router.on_startup`) only | D1.2 |
| `services/backend/app/api/backup_models.py` | added `AutoBackupFile`, `AutoBackupStatus` | D2 |
| `services/backend/app/api/routes.py` | appended `GET /api/backup/auto`, `POST /api/backup/auto/run`, `GET /api/backup/auto/{name}` | D2 |
| `contracts/openapi.json`, `apps/frontend/src/api/generated/api.ts` | regenerated; +160 / +169 lines, 0 removed | D3.3 |
| `apps/frontend/src/api/client.ts` | appended `autoBackupStatus`, `runAutoBackup`, `downloadAutoBackup` | D3 |
| `apps/frontend/src/features/BackupPanel.tsx` | "Sao lưu tự động" block; all existing text kept | D3.1 |
| `tests/backend/test_m5b_backup_auto.py` (new, 18) | D1 branches, startup fault injection, round trip | M5B-01, 02 |
| `tests/backend/test_m5b_backup_api.py` (new, 13) | API, 409, 500, name validation, path-free | M5B-03 |
| `tests/browser/m5b.spec.ts` (new, 2) | M5B-04 flow desktop and 390px | M5B-04 |
| `docs/reviews/SCST_M5B_EVIDENCE/` | this return, `m5b-desktop.png`, `m5b-390.png` | evidence |

## Decisions per D1-D4

**D1 (backup_auto.py)**
- Files: `<SCST_DATA_DIR>/backups/auto/auto-YYYYMMDDTHHMMSSffffffZ[-N].scstbak` (no colons; same stamp style as `pre-restore-*`). Content is exactly `backup_export.write_archive` output (scst.backup.v1); nothing in export/check/restore was changed.
- has_data: DB file exists and, opened read-only (`mode=ro`, closed before returning), `snapshots` or `cargo_revisions` (may be missing) has a row; or `vessel_profile_store.list_ids()` is non-empty. `list_ids()` only iterates, never mkdirs; an empty `vessels/.lock` is not a profile folder so it does not count. An existing empty DB is not data and is not modified.
- Due: newest auto file (by the timestamp in its name, not mtime) older than 20 h, or none. `_now()` is monkeypatchable.
- Write: `mkstemp` in `backups/auto`, `fsync`, `os.link` to the final name (fallback exclusive `open('xb')` + copy); an existing name gets `-1`, `-2`… — never overwritten. `backups/auto` is created only after has_data passed.
- Validation: the new file is read back and passed to `backup_check.check` in a private temp dir. On any failure only the new file is deleted, nothing is pruned, `last_error` = fixed Vietnamese text without a path, `AutoBackupFailed` raised (run_now) or swallowed (run_if_due). A success clears `last_error`.
- Retention: after success only, keep the newest 10 files matching `NAME_PATTERN` in `backups/auto`; anything else (pre-restore-*, manual `scst-backup-*`, other names, files in `backups/`) is never touched. Reviewer-local repair (lead): the file just created is never pruned even if a clock moved back would sort it older than ten others.
- Concurrency: one module-level blocking `threading.Lock` over the whole run; `run_if_due` re-checks has_data and the 20 h rule inside the lock, so two concurrent startup runs create exactly one file. `run_now` serializes with it and always creates a file. Vessel store locks are only taken inside `write_archive`, as in `export_bytes`.
- Startup: daemon thread when `SCST_AUTO_BACKUP` != `0`; `start_background`, the thread body and the main.py hook each swallow exceptions, so startup is never blocked or failed. `SCST_AUTO_BACKUP=0` disables startup runs only; "Sao lưu ngay" still works.
- Ambiguity resolved toward preserving data: has_data "at least one plan or revision" was read as rows in `snapshots`/`cargo_revisions`; "profile" as a listed store version.

**D2 (API)** — file names only, never paths.
- `GET /api/backup/auto` → `{enabled, interval_hours: 20, keep: 10, files: [{name, created_utc, size_bytes}] newest first, last_error}`.
- `POST /api/backup/auto/run` → the new `AutoBackupFile`; no data → 409, failure → 500. Reviewer-local repair (lead): both error bodies are `{"message", "errors":[{"field":"body","message"}]}` so they match the declared `BackupRejectedDetail` model and the M5a error shape the client already reads (the worker had a bare string).
- `GET /api/backup/auto/{name}` (declared as `{name:path}` so slashes reach our check): 404 with a Vietnamese message unless `NAME_PATTERN.fullmatch(name)` and the file exists in `backups/auto`; `..`, `/`, `\`, encoded traversal, `pre-restore-*` and other names → 404.

**D3 (UI)** — block "Sao lưu tự động" inside the existing backup card: status line (newest time, kept n/10, disabled state), `last_error` alert, the exact SPEC note, "Sao lưu ngay", up to 10 rows each with "Tải" (blob download under the original name). No new restore button: restore uses the existing picker (D3.2). Wraps at 390 px (screenshot `m5b-390.png`).

**D4** — none of the out-of-scope items were done.

## D1 test matrix (`tests/backend/test_m5b_backup_auto.py`)

| Branch | Test |
|---|---|
| due | `test_due_creates_one_valid_file` |
| not due (<20 h), then due at 20 h | `test_not_due_under_20_hours_then_due_after` |
| vessel profile alone is data | `test_vessel_profile_alone_is_data` |
| no data → nothing created | `test_no_data_creates_nothing`, `test_startup_without_data_creates_nothing` |
| empty `vessels/.lock` only → no data | `test_empty_vessels_lock_file_alone_is_no_data` |
| empty DB → no data, unmodified | `test_existing_empty_database_is_no_data_and_not_modified` |
| disabled by `SCST_AUTO_BACKUP=0`, run_now still works | `test_disabled_by_env_but_run_now_works` |
| keep 10, delete the oldest | `test_retention_keeps_10_and_deletes_the_oldest` |
| pre-restore, manual, other files untouched | `test_retention_never_touches_other_files` |
| failed new backup → only new removed, nothing pruned, path-free last_error, later success clears it | `test_failed_new_backup_removes_only_the_new_file` |
| run_if_due swallows failure | `test_run_if_due_swallows_failure_with_fixed_message` |
| no overwrite (`-1`, `-2`) | `test_never_overwrites_same_timestamp` |
| two concurrent run_if_due → one file | `test_two_concurrent_run_if_due_create_one_file` |
| startup fault injection (run_if_due, write_archive, start_background raise) | `test_startup_survives_injected_faults` |
| each auto file passes `backup_check.check` | `test_every_auto_file_passes_check` |
| byte-identical round trip through M5a `backup_restore.apply` (snapshots, cargo_revisions, vessels/**) | `test_round_trip_restores_byte_identical` |
| SCST_DATA_DIR with spaces + Vietnamese | `test_data_dir_with_spaces_and_vietnamese` |

## Who did what

| Who | Model, effort | Work | Why |
|---|---|---|---|
| Lead session | Opus 5.5, medium | design, interface contract for both workers, review of every diff, two reviewer-local repairs (prune protection, 409/500 body shape + matching test lines), all verification runs, screenshots, this return, PR | owner instruction: advisor and internal reviewer |
| Subagent 1 | Sonnet, high | D1 `backup_auto.py`, main.py hook, `test_m5b_backup_auto.py` | the hard part: retention, protected files, atomic write, failed-backup safety, concurrency, non-blocking startup — where a mistake loses data |
| Subagent 2 | Haiku, high | D2 routes/models, API tests, D3 UI + client, contract regeneration, `m5b.spec.ts` | easy, pattern-following parts modelled on M5a |

The two subagents ran concurrently on disjoint files. Subagent reports were not accepted as proof; the lead re-read the diffs and re-ran everything below.

## Commands and results (lead, on this branch)

| Command | Result |
|---|---|
| `python -m pip install -r requirements-dev.txt` | ok |
| `python -m pytest` (main baseline, before changes) | 878 passed |
| `python -m pytest tests/backend/test_m5b_backup_auto.py` | 18 passed |
| `python -m pytest` (after D1-D3) | **909 passed** (878 + 18 + 13), 1 pre-existing warning |
| `python tooling/export_contract.py`; `npm ci`; `npm run contract`; `npm run build` | ok; diff of contract/types is additions only (0 removed lines) |
| `LANG=C.UTF-8 npx playwright test -c playwright.local.config.ts m5b.spec.ts` | 2 passed |
| `LANG=C.UTF-8 npx playwright test -c playwright.local.config.ts` (full suite, fresh temp data dir) | **59 passed** (57 + 2) |
| `git status` after the browser run | only the then-uncommitted `tests/browser/m5b.spec.ts`; no file under `docs/reviews/` changed |
| `python tooling/integration_check_pre_m2d.py .` | **29/29 PASS** |
| `PYTHONDONTWRITEBYTECODE=1 python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return` | **PASS**, mandatoryControls=7 failed=0 |

The browser override `apps/frontend/playwright.local.config.ts` is untracked and listed in `.git/info/exclude`; it only replaces the webServer command (`python -m uvicorn …`), sets `SCST_DATA_DIR` to a temp dir and the chromium `executablePath` `/opt/pw-browsers/chromium`. Screenshots were produced with `SCST_EVIDENCE_DIR` in a scratch dir and copied here (the `.scstbak` the spec saves was not committed).

## Failed attempts

- None in the final runs. The API worker's first 409/500 bodies were bare strings not matching the declared `BackupRejectedDetail` response model; corrected by the lead (see D2) and the two new API test lines adjusted to the dict shape. No existing test was edited.

## DA application

- **DA02 (no loss, formats unchanged, startup never fails):** auto backup only reads live data (read-only SQLite, store lock only inside `write_archive`); nothing created without data; never overwrites; deletes only `auto-*` files beyond 10 after a verified success; a failed backup deletes only itself. Startup hook swallowed at three levels, tested with fault injection. scst.backup.v1, schemas, revision hashes and existing contract fields unchanged.
- **DA03 (limits stated):** the UI note states that the copies are on the same machine, there is no schedule while the app is closed and no encryption; this return and the PR list the same; no off-machine copy is made.
- **DA04 (reuse):** `backup_export.write_archive`, `backup_check.check`, the M5a temp+fsync+link pattern, and the M5a restore flow for restoring an auto file.
- **DA05 (usable UI flow):** "Sao lưu ngay" → listed → "Tải" → restore through the existing picker, proven in `m5b.spec.ts` at desktop and 390 px.

## Windows notes

No colons in names; SQLite connection closed before any file is written/deleted; empty `vessels/.lock` tolerated; no flock assumption (in-process `threading.Lock` only); a data dir with spaces and Vietnamese characters is tested. Not run on Windows here — root's Windows review is the check for NTFS behaviour (e.g. `os.link` on NTFS works; on FAT the `xb` copy fallback applies).

## Limitations and remaining owned work

- Not verified on Windows/NTFS (root review).
- In-process lock only: two app processes on the same data dir could each write one auto file at startup (both valid; retention still bounded). The M5a store/process locks still guard the data read.
- The startup daemon thread may still be writing when the app is closed; a partial file stays as a hidden `.auto-*.tmp` in `backups/auto` and is never listed or pruned (not cleaned up automatically).
- Owned future work unchanged: M5c installer, schedule while the app is closed, encryption, off-machine copy, retention/interval settings in the UI.
