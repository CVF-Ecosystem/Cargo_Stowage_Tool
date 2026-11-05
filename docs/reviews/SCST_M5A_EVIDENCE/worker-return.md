# SCST — M5a worker return (local backup and restore)

Status: WORKER_RETURN
Risk: R2
Worker: Claude Cloud implementation worker (lead session as advisor and internal reviewer; Sonnet/Haiku subagents, see "Who did what")
Reviewer: root-independent-implementation-reviewer (Claude local) — pending; nothing here is self-approval

Branch `claude/m5a-backup-restore` from `main` 3396555. SPEC [docs/specs/SCST_M5A.md](../../specs/SCST_M5A.md), work order [docs/work_orders/SCST_M5A.md](../../work_orders/SCST_M5A.md), handoff `CVF_SESSION/handoffs/AGENT_HANDOFF_M5A.md`.

CVF Agent Declaration (at start): project Cargo_Stowage_Tool; CVF core `../.Controlled-Vibe-Framework-CVF` @ c4c8767 — **not available in the cloud**, not initialized (as instructed; no core clone or initialize scripts run). `../WORKSPACE_RULES.md` is absent for the same reason (it lives in the same workspace container); one subagent stopped on that under the First-Request Protocol, and the lead ruled to continue under the owner's stored dispatch and records it here for root. Phase BUILD; risk R2; live governance evidence required YES (this tranche makes no CVF-governance claim, and the product makes no provider or network call); role IMPLEMENTATION_WORKER; active handoff AGENT_HANDOFF_M5A.md; next allowed move: implement on a non-main branch and return by pull request; parked: M5b installer, scheduled backup, M3b, M4, observations, live-provider proof, business acceptance, merge.

## Changed paths

All inside worker ownership. Untouched: `services/backend/data/**`, `.cvf/**`, `scripts/cvf_gates/**`, `.github/**`, `tooling/**`, requirements, `package.json`/`package-lock.json`, every existing test and browser spec, CVF_SESSION, memory, status, specs, work orders, `docs/reviews/**` other than this folder. No dependency added (stdlib `zipfile`, `hashlib`, `sqlite3`, `tempfile`, `os`, `shutil`).

| Path | Change | Item |
|---|---|---|
| `services/backend/app/adapters/backup_export.py` (new) | `write_archive(fileobj, lock_held=False)`, `export_bytes()`; read-only source DB (`mode=ro`), `Connection.backup` copy in a private temp dir, vessels copied under the store lock | D1 |
| `services/backend/app/adapters/backup_check.py` (new) | `BackupRejected`, limits, `check(body, workdir)`, `current_counts()`, `preview(body)` | D2 |
| `services/backend/app/adapters/backup_restore.py` (new) | `apply(body, confirm)`, `ConfirmMismatch`, journaled swap with rollback, `_step` fault hook, `_now` | D3 |
| `services/backend/app/adapters/vessel_profile_store.py` | `read(..., *, base=None)` — additive keyword; default behaviour unchanged | D2.5 reuse |
| `services/backend/app/api/backup_models.py` (new) | `BackupCounts`, `BackupPreview`, `RestoreResult`, `BackupFieldError`, `BackupRejectedDetail` | D1-D3 contract |
| `services/backend/app/api/routes.py` | appended: `GET /api/backup/export`, `POST /api/backup/restore/preview`, `POST /api/backup/restore/apply?confirm=`; streamed 256 MiB body limit (same pattern as `_upload_body`) | D1-D3 |
| `contracts/openapi.json`, `apps/frontend/src/api/generated/api.ts` | regenerated; additions only (0 removed lines) | D4.3 |
| `apps/frontend/src/features/BackupPanel.tsx` (new) | "Sao lưu và khôi phục" card | D4.1 |
| `apps/frontend/src/api/client.ts` | appended `exportBackup`, `previewBackup`, `applyBackup`, `BackupApiError`; types alias the generated schemas | D4 |
| `apps/frontend/src/features/Workspace.tsx` | mounts BackupPanel after "Lưu và mở local"; `afterRestore` reloads saved list, clears the selection, bumps `reloadToken`; CargoRevisionPanel keyed on `reloadToken` | D4.2 |
| `apps/frontend/src/features/VesselProfilePanel.tsx` | optional `reloadToken` prop re-reads the profile list; the mount effect is unchanged | D4.2 |
| `apps/frontend/src/styles.css` | appended `.backup-*` rules (wrap at 390px) | D4.3 |
| `tests/backend/test_m5a_export.py` (13), `test_m5a_preview.py` (74), `test_m5a_restore.py` (46) (new) | backend tests | M5A-01..03, 05 |
| `tests/browser/m5a.spec.ts` (new, 2 tests) | M5A-05 desktop flow, M5A-04 390px | M5A-04, 05 |

## Decisions per D1-D5

**D1 export.**
- The archive holds `manifest.json`, `scst.sqlite3` and `vessels/<ID>/v<n>/{profile.json, model.glb, manifest.json}` only.
- The manifest has `format`, `created_utc`, `counts` (`plans`, `revisions`, `vessel_profile_versions`) and `files[]` (`path`, `size`, `sha256`, sorted). It lists every entry except itself.
- Export never calls `storage.open_migrated()`, because that creates the DB and may write the pre-SUP-02A `.bak`. Instead the source is opened `mode=ro` and checked with the same column rule as `storage._prepare`. A legacy DB without `cargo_revisions` gets that table in the temporary copy only.
- A missing DB exports an empty DB that has both tables. Nothing is created in `SCST_DATA_DIR`.
- The DB copy is taken before the vessel lock. A profile appended in that gap is still included, which is harmless. Vessel files are copied while holding `_LOCK` and `_process_lock`.
- A store-listed version that is missing one of its three files makes the export fail with a Vietnamese message. A partial archive could not be restored, so it is not produced.
- The file name is `scst-backup-YYYYMMDD-HHMMSS.scstbak` (UTC). No API response contains a filesystem path.

**D2 preview.**
- The route refuses a body over 256 MiB from `Content-Length` and while streaming (413).
- `check()` rejects these archives in Vietnamese:
  - bad ZIP;
  - absolute path, backslash, `..` or drive letter;
  - symlink or non-regular mode;
  - directory entry;
  - duplicate name (case-folded, for NTFS);
  - name outside the allow-list;
  - encrypted entry or unknown compression;
  - more than 20 000 entries;
  - declared size over 1 GiB, or real bytes over 1 GiB or over the declared size (counted while extracting).
- It also rejects:
  - missing or invalid `manifest.json`, or wrong `format`;
  - `files` not exactly equal to the real entries;
  - `size` or `sha256` mismatch;
  - `counts` that differ from the counted data;
  - `integrity_check` not `ok`;
  - `snapshots` or `cargo_revisions` columns other than `storage.SNAPSHOT_COLUMNS` and `storage.REVISIONS_COLUMNS` (both required);
  - extra DB objects;
  - a plan that is not a UUID or not `scst.saved-plan.v1`, a non-UTC time, or a plan that fails `Plan.model_validate`;
  - a revision with a foreign dataset, a non-contiguous sequence, or a failed `cargo_revisions.replay` (parent chain and `content_sha256`);
  - a profile that fails `vessel_profile_store.read(..., base=<extracted>)` or the `_load` re-validation (`validate_profile`, id, version, `profile_sha256`). That re-validation is restated because `_load` is bound to the live data dir.
- Preview extracts only into a system `TemporaryDirectory`, reads live counts read-only, and never creates the DB or the vessels dir.

**D3 restore.**
- `confirm` ≠ sha256(body) → 409 before anything is written.
- Under `_LOCK` and `_process_lock` for the whole operation, the restore runs these steps:
  1. Full D2 again, into `<data>/.restore-*/new`.
  2. Pre-restore backup to `<data>/backups/pre-restore-<UTC>.scstbak`, written as a temp file and then `os.link` (or `open('xb')`). It never overwrites; `-1`, `-2` suffixes are added on collision.
  3. Move the live DB, and any `-journal`/`-wal`/`-shm`, aside with `os.replace`. Then `os.replace` the new DB in.
  4. Move every child of `vessels/` except `.lock` aside, then move the new `<ID>` directories in.
  5. `plan_binding.clear_replay_cache()`.
  6. Remove the work dir.
- **Deviation, recorded:** the SPEC says to rename the old `vessels` directory aside. On Windows the store's lock file `<vessels>/.lock` is held open during the restore, so that directory cannot be renamed while locked. The restore therefore swaps its children. Each move is journaled before it is attempted, and rollback undoes the completed moves in reverse.
- Any `Exception` rolls back, removes the work dir, and is reported as 400: "Khôi phục thất bại; dữ liệu hiện tại đã được giữ nguyên…". A `KeyboardInterrupt` or `SystemExit` also rolls back, then propagates unchanged.
- The pre-restore backup is kept on both success and failure.

**D4 UI.**
- The card has "Tải bản sao lưu" and the file input "Khôi phục từ bản sao lưu". The preview table compares the counts in the file with the current counts and shows the creation time and a short sha. The SPEC warning is shown verbatim, followed by the "Khôi phục" button.
- A rejected preview shows the Vietnamese message and errors, with no restore button.
- After a restore, the saved-plan list and the vessel profile list are reloaded, and the cargo revision panel is remounted. The open draft is kept, with the notice "Phương án đang mở trong tab chưa thuộc dữ liệu đã khôi phục; hãy lưu lại nếu cần."
- The DA03 note is visible in the card.

**D5.** Not built: scheduled backup, merge or partial restore, encryption, cloud sync, installer, deletion, format or schema change.

**Ambiguity choices (data-preserving).**
- The restored DB file is the backup's `Connection.backup` copy. "Byte-identical" is proven for DB rows (`snapshots`, `cargo_revisions`) and for every `vessels/**` file. It is not proven for the raw SQLite page layout.
- Rows from an unknown revision dataset are rejected rather than silently restored.

## Fault-injection matrix (D3.4, `tests/backend/test_m5a_restore.py`)

After every case the data fingerprint is byte-identical to before. The fingerprint is the sha256 of every file under `SCST_DATA_DIR` except `backups/`. Every case also leaves no `.restore-*` directory and keeps the live API working.

| Injected at | Errors | Result |
|---|---|---|
| `checked` (after full D2 into work dir) | RuntimeError, OSError | 400, data byte-identical, no work dir |
| `pre_backup_written` | RuntimeError, OSError | 400, byte-identical; pre-restore backup kept |
| `db_moved_aside` | RuntimeError, OSError | 400, live DB moved back, byte-identical |
| `db_replaced` | RuntimeError, OSError | 400, new DB moved out, old DB back, byte-identical |
| `vessel_moved_aside` (each; also 1st, 2nd and 3rd occurrence) | RuntimeError, OSError | 400, byte-identical |
| `vessels_old_aside` | RuntimeError, OSError | 400, byte-identical |
| `vessel_moved_in` (each; also 1st and 2nd occurrence) | RuntimeError, OSError | 400, byte-identical |
| `vessels_replaced` | RuntimeError, OSError | 400, byte-identical |
| `cache_cleared` (last step before commit) | RuntimeError, OSError | 400, byte-identical; cache cleared again |
| `os.replace` fails moving the live DB aside | OSError | 400, byte-identical |
| `os.replace` fails installing the new DB | OSError | 400, byte-identical |
| `os.replace` fails moving a vessel dir in | OSError | 400, byte-identical |
| pre-restore backup write fails | OSError | 400, byte-identical, no partial backup file |
| no live DB / no vessels dir before restore | RuntimeError | rolled back; created `vessels/` removed again |
| `KeyboardInterrupt` mid-swap | — | rolled back, byte-identical, propagates |

The other M5A-03 tests are:
- a wrong or empty `confirm` returns 409 and writes nothing;
- a round trip with a pre-restore backup that passes `check()` and holds all three plans;
- the replay cache serves no pre-restore data;
- a concurrent `vessel_profile_store.append` blocks until the restore ends, both during the swap and during the pre-restore backup;
- an existing pre-restore backup file is never overwritten.

## Who did what

| Part | Who | Model, effort | Lead review |
|---|---|---|---|
| Design contract (format, module split, API), routes, models, contract regeneration, worker return, PR | lead session | Opus 5.5, medium | — |
| D1 export + `test_m5a_export.py` | subagent | Haiku, high | First run stopped at the First-Request Protocol (missing core/WORKSPACE_RULES); lead ruled. Its design notes were adopted: no `open_migrated` and a non-reentrant lock. The lead re-read the code and reran the tests (13 pass). |
| D2 validation + `test_m5a_preview.py` + `read(base=)` | subagent | **Sonnet, high**: security-critical untrusted-archive parsing (zip-slip, zip-bomb, hashes, SQLite, replay) | Lead re-read the whole module and reran 74 + store tests. |
| D3 atomic restore + `test_m5a_restore.py` | subagent | **Sonnet, high**: rollback correctness on every step and Windows lock/rename semantics | Lead traced the journal undo for each move and reran 46 tests. |
| D4 UI | subagent | Haiku, high | Lead switched to the generated types and remounts the revision panel after restore; build passes. |
| `tests/browser/m5a.spec.ts` | subagent (same as D4) | Haiku, high | Lead found the shared-data leak in the full-suite run and repaired the spec (see below). |

At most two subagents edited at once (D1 with D2, then D2 with D4, then D3 with the browser spec), never the same file.

## Commands and results (run by the lead on the final head)

| Command | Result |
|---|---|
| `python -m pip install -r requirements-dev.txt` | OK |
| `python -m pytest` (baseline on 3396555) | 734 passed |
| `python -m pytest` (branch) | **867 passed** (734 + 133 new), 1 warning (existing httpx deprecation) |
| `python tooling/export_contract.py`; `npm ci`; `npm run contract`; `npm run build` | OK; contract diff additions only; build OK |
| Browser, full suite + m5a (local override, temp `SCST_DATA_DIR`, chromium `/opt/pw-browsers/chromium`, `LANG=C.UTF-8`) | **57 passed** (55 existing + 2 `m5a.spec.ts`), 3.1 min |
| `git status` after browser run | no change under `docs/reviews/` (evidence goes to a temp dir) |
| `python tooling/integration_check_pre_m2d.py .` | 29/29 PASS |
| `PYTHONDONTWRITEBYTECODE=1 python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return` | GATE_RESULT |

The browser override `apps/frontend/playwright.local.config.ts` is untracked and listed in `.git/info/exclude`. It changes only the webServer command, the temporary `SCST_DATA_DIR` and the chromium `executablePath`.

## Failed attempts

- The first D1 dispatch returned BLOCKED, with no files changed, because the core and `WORKSPACE_RULES.md` were missing. The lead resolved it as above.
- The first full browser run gave **52 passed, 5 failed**: four `pipe-list.spec.ts` tests and one `sup01.spec.ts` test. All the browser specs share one server and data dir, so the m5a spec's added cargo revision leaked into later spec files. Run alone, those specs pass (9/9).
- Repair, in the new spec only: `beforeAll` exports the shared data through the backup API, and `afterAll` restores it through preview + apply. Then `m5a` + `pipe-list` gave 6/6, and the full run gave the result above.
- The second full run gave **56 passed, 1 failed**: `m5a` desktop timed out waiting for the preview request. The trace shows `setInputFiles` reached the file input while it was still `disabled`, because the third save's list refresh is slower with the suite's larger shared DB. The change event never fired.
- Repair, in the new spec only: `await expect(input).toBeEnabled()` before each file pick. The third full run gave the 57/57 above.
- The browser spec cannot read response bodies after the download event ("navigated away" in Playwright). It reads counts and the pre-restore name from the rendered panel instead.

## DA02-DA05 application

- **DA02 (no loss, formats unchanged):**
  - preview writes nothing, and the tests hash the data dir before and after;
  - restore rolls back byte-identically at every injected step;
  - a pre-restore backup is always written first and never overwritten;
  - the round trip is identical in rows and in `vessels/**` bytes;
  - no stored format, schema, revision hash or existing contract field changed (contract additions only);
  - all tests use a temporary `SCST_DATA_DIR`.
- **DA03 (stated gaps):** the UI note reads "Chưa có sao lưu tự động theo lịch, mã hóa hay khôi phục gộp; khôi phục luôn thay toàn bộ.", and the gaps are listed again below.
- **DA04 (reuse):**
  - storage column constants and `_prepare` rule;
  - `Plan.model_validate`;
  - `cargo_revisions.replay` with `revision_store.decode_rows`;
  - `vessel_profile_store.read` (additive `base=`) plus `validate_profile`/`profile_sha256`;
  - the store's `_LOCK` and `_process_lock`;
  - `plan_binding.clear_replay_cache`;
  - the route body-limit pattern of `_upload_body`.
- **DA05 (usable flow):** in the UI flow, verified in the browser at 1440 px and 390 px:
  1. save two plans (one multi-layer `columns-v1`) and one revision;
  2. download the backup;
  3. save a third plan;
  4. pick the file, see the preview and warning, and restore;
  5. the list holds exactly the export-time plans, both reopen with equal plans, and the revision is latest again.

  The invalid-file error is shown in Vietnamese. Screenshots: `m5a-desktop.png`, `m5a-390.png` in this folder.

## Limitations and remaining owned work

- **Concurrent SQLite writers during a restore are not fenced.**
  - The apply endpoint is `async` and runs synchronously on the event loop, so other async handlers wait. Sync handlers in the threadpool, or another process, could still hold a connection.
  - On Windows, an open handle makes `os.replace` fail, and the restore rolls back.
  - On POSIX, a write by a connection opened before the swap would land in the moved-aside file and be lost with the work dir.
  - Root may want a DB-level fence (for example a `BEGIN EXCLUSIVE` held until just before the swap) in a later tranche.
- Rollback reports "đã được giữ nguyên" even if one undo move itself failed. Undo continues with the remaining moves but does not surface that case separately.
- Readers that take no lock (`list_ids`, `versions`) can see a partial vessels tree during the child-by-child swap.
- Real NTFS replacement (open handles, `os.link`, `msvcrt` lock with children moved) is **not run here**. It is owned by root on Windows, as the SPEC says.
- A store-listed vessel version with a missing file blocks export entirely. There is no partial export.
- Backup files are deliberately unencrypted.
- Out of scope and owned: scheduled backup, encryption/password, merge or partial restore, cloud sync, M5b installer, deletion, and business acceptance by the owner.
