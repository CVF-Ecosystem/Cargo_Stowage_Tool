# SCST — SUP-02B worker return (Claude Cloud implementation worker)

Status: RETURNED_FOR_REVIEW
Risk: R2
Branch: `claude/sup-02b-vessel-profile` (base `ab0ae69`)
Role: IMPLEMENTATION_WORKER (cloud lead session as advisor/independent in-run reviewer, subagents as implementers)

## CVF Agent Declaration (at start of run)

- Project: Cargo_Stowage_Tool. Phase: BUILD. Risk ceiling: R2. Live governance evidence required: YES. This tranche makes no governance claim, so no provider call is involved.
- Active role: IMPLEMENTATION_WORKER. Active handoff: `CVF_SESSION/handoffs/AGENT_HANDOFF_SUP_02B.md`.
- Next allowed move: implement SUP-02B on a non-main branch and open a pull request for root review.
- Parked: SUP-03, M2d/M3/M4, SUP-02A O2-O5, measured hold, business acceptance and merge.
- Limitation: the hidden CVF core (`../.Controlled-Vibe-Framework-CVF`, pin c4c8767) and `../WORKSPACE_RULES.md` are not present in the cloud container, and PowerShell is absent. As the owner instructed, this was noted and work continued. No core initialize, clone or doctor script was run. One subagent first stopped on this condition; the lead re-briefed it with the owner instruction.

## Changed paths

| Path | Part |
|---|---|
| `services/backend/app/domain/vessel_profiles/__init__.py` (new) | D1 contract, Vietnamese field errors, canonical hash, pure transform, verification, viewer block |
| `services/backend/app/domain/vessel_profiles/glb.py` (new) | D2/D3.5 stdlib GLB header/JSON-chunk parser and POSITION bounds |
| `services/backend/app/vessel.py` | `builtin_vinafco_profile()` added; PROFILE/CASES/DATA unchanged |
| `services/backend/app/adapters/vessel_profile_store.py` (new) | D3 append-only atomic store with integrity check |
| `services/backend/app/adapters/vessel_profile_service.py` (new) | D3–D5: built-in + user profiles, preview/create, shared case-plan builder, plan reference check |
| `services/backend/app/adapters/plan_binding.py` | `bind()` calls the vessel check first for every contract |
| `services/backend/app/domain/model/__init__.py` | D4 `VesselReference` generalised; profile fields omitted from JSON when absent |
| `services/backend/app/domain/comparison/__init__.py` | profile leaves are compared only when present |
| `services/backend/app/api/routes.py`, `api/vessel_profile_models.py` (new) | D5 routes and models; the three VINAFCO routes are unchanged in output |
| `contracts/openapi.json`, `apps/frontend/src/api/generated/api.ts` | regenerated with `tooling/export_contract.py` / `npm run contract` |
| `apps/frontend/src/api/client.ts`, `features/Workspace.tsx`, `features/VesselProfilePanel.tsx` (new), `viewer-3d/Scene.tsx`, `viewer-3d/Viewer.tsx`, `styles.css` | D6 |
| `tests/backend/glb_fixture.py`, `test_sup02b_profile_domain.py`, `test_vessel_profile_store.py`, `test_sup02b_api.py` (new) | S2B-01..04 |
| `tests/browser/sup02b.spec.ts` (new) | S2B-05 |
| `tests/browser/evidence.ts`, `tests/browser/sup02a.spec.ts` (screenshot directory line only) | D8 / S2B-06 |
| `docs/reviews/SCST_SUP_02B_EVIDENCE/browser/sup02b-desktop.png`, `sup02b-390px.png`, this file | evidence |

The diff contains no forbidden paths: `services/backend/data/**`, `.cvf/**`, `scripts/cvf_gates/**`, `.github/**`, requirements and package files are all untouched (checked with `git diff --name-only ab0ae69`). No dependency was added: GLB parsing uses `struct` and `json`, and uploads are base64 in JSON, without python-multipart. No secret, provider or network call was added.

## Decisions per D1–D8

- **D1 contract and derivation**
  - `scst.vessel-profile.v1` is a pydantic model with `extra="forbid"`. It adds a `contract_version` literal and optional `hull_mesh_names` (≤50).
  - Integers are StrictInt; bool is rejected, and NaN/inf are rejected.
  - Each error is `{field, message}` in Vietnamese, using a dotted path such as `cases[0].id`.
  - Profile size limit: 256 KiB.
  - Decisions where the SPEC was silent:
    - `hold.id` must also satisfy the plan Identifier pattern.
    - Optional `deadweight_t` and `freeboard_mm` are integers, as in the source.
    - Source document `title` is 1–300 characters.
  - VINAFCO268 v1 is derived at runtime from `profile.json`. Hold, cases, the four notes, provenance hashes and the transform are verbatim.
  - `field_status`: dimensions SOURCED, hold ESTIMATED, cases SOURCED.
  - Built-in canonical `profile_sha256` = `533695df5b613815716e69fdeddd23538a494dbaea0bb233a3a75c55d1358c86`.
- **D2 transform and verification**
  - One pure function `glb_to_scene`: scene = R_y(yaw)·glb + translation, using exact integer yaw tables in the THREE `rotation.y` convention. Scale is 1.
  - Hold frame: x = scene x + L/2, y = scene z + W/2, z = scene y (mm).
  - GLB bounds: the default scene node tree (matrix or TRS composed with parents) applied to the 8 corners of each POSITION accessor min/max.
  - PASS requires every landmark within 1 mm per axis AND the transformed GLB box to contain the hold box. FAIL is never stored.
  - Generic GLB convention (decision, recorded): X runs along the vessel, Y is up from the keel, Z is transverse, and the origin is at keel, mid-length, centreline. The draft marker centre is `transform((0, draft_m, 0))` and its box comes from `dimensions_m`, swapped for yaw 90/270.
- **D3 store**
  - Layout: `SCST_DATA_DIR/vessels/<id>/v<n>/{profile.json (canonical bytes), model.glb, manifest.json}`.
  - Writes go to a `.tmp-*` directory with fsync and then one `os.rename`. Nothing is ever overwritten.
  - The next version must be latest+1, otherwise 409. A built-in id gives 409.
  - Limits: 50 ids and 50 versions per id.
  - Every read checks sha256 and size. On mismatch the version is UNAVAILABLE and nothing is repaired.
  - Body limit 28 MiB: Content-Length is checked before reading, then the body is streamed and the read aborts at the limit (413).
  - GLB ≤ 20 MiB, magic `glTF`, version 2, valid JSON chunk with asset.version 2.0. Preview never writes.
- **D4 plan reference**
  - `VesselReference` accepts the D1 id/case patterns plus optional `profile_version` and `profile_sha256`, omitted from JSON when absent.
  - Without the two fields: vessel must be VINAFCO268, and the existing model checks apply unchanged.
  - With them: both fields are required and VINAFCO268 is rejected. The model itself only checks structure.
  - `plan_binding.bind()` → `vessel_profile_service.check_reference()` checks:
    - the profile exists and passes integrity;
    - the sha matches;
    - hold equality;
    - the case belongs to the profile;
    - certificate limit == `cargo_mass_g`.
  - That check therefore runs at every entry point that already calls `bind`: validate, snapshot save/open, CSV preview, pipe-list preview, planner, compare (both sides), revision plan-preview and rebase.
  - Snapshots are never rewritten.
- **D5 API**
  - The six endpoints are as listed in the SPEC.
  - The list puts user versions first (newest `created_utc` first), then built-ins. "Mới nhất trước" was read as applying to dated user versions; built-ins have no creation date. The root may prefer built-ins first; that is a one-line sort change.
  - The upload request schema is inlined in OpenAPI with `openapi_extra`.
  - The built-in `asset_url` stays `/api/vessels/vinafco268/model`, and the VINAFCO case plan in the UI still uses the legacy route, because existing specs route those URLs.
  - The new `/api/vessel-profiles/VINAFCO268/1/cases/{c}/plan` returns the same bytes, since both routes share one builder.
- **D6 UI**
  - Panel "Tàu và hầm":
    - selects "Chọn tàu" and "Trường hợp tải" and the button "Mở tàu và trường hợp";
    - a status line showing ESTIMATED/SOURCED/MEASURED as "ước tính / theo nguồn / đã đo", plus the source.
  - Form "Nhập profile tàu":
    - inputs: JSON file and GLB file;
    - "Xem trước kiểm" shows errors, PASS/FAIL, the table "Sai số landmark" and the line "Hộp bao GLB chứa hầm";
    - "Tạo profile" is enabled only when the last preview is valid for exactly the current file contents.
  - Region "Thông số {name}" for user vessels. The VINAFCO region text is unchanged.
  - `Scene.tsx` no longer has VINAFCO constants. Hull ghost names, GLB position/yaw and the draft marker box and position all come from the server `viewer` block; the frontend does no rotation, scaling or centring of its own.
- **D7** Nothing out of scope was implemented: no edit/delete, no multi-hold, no hydrostatics, no AI.
- **D8** `tests/browser/evidence.ts` writes to `SCST_EVIDENCE_DIR` when set, otherwise to `os.tmpdir()/scst-evidence-<run>`. `sup02a.spec.ts` changed only its screenshot directory line. No assertion changed.

## VINAFCO268 landmarks (real `model.glb`, tolerance 1 mm, result PASS)

| Landmark | glb_m | expected hold_mm | actual hold_mm | error mm (x, y, z) |
|---|---|---|---|---|
| Góc sàn hầm lái-trái | [-27.23, 0.832, -5.171875] | [0, 0, 0] | [0, -0.375, 0] | 0, 0.375, 0 |
| Góc sàn hầm lái-phải | [-27.23, 0.832, 5.171875] | [0, 10343, 0] | [0, 10343.375, 0] | 0, 0.375, 0 |
| Góc sàn hầm mũi-trái | [29.175, 0.832, -5.171875] | [56405, 0, 0] | [56405, -0.375, 0] | 0, 0.375, 0 |
| Góc sàn hầm mũi-phải | [29.175, 0.832, 5.171875] | [56405, 10343, 0] | [56405, 10343.375, 0] | 0, 0.375, 0 |

- Landmarks are the four hold floor corners from `geometry` (source x min/max, y min/max, floor z). glb = (x − 38.9, z, −y).
- The 0.375 mm is the source width inset: 10.34375 m against 10343 mm.
- GLB bounds: [-38.900002, 0, -6.62]..[38.900002, 9.4, 6.62]. In scene coordinates: [-39.872502, -0.832, -6.62]..[37.927502, 8.568, 6.62].
- Hold box in scene: [-28.2025, 0, -5.1715]..[28.2025, 5.408, 5.1715]. The GLB box contains it.
- Viewer block: hull box 77.8 × 0.01 × 13.24. Draft markers: VR-SI at (-0.9725, 3.768, 0) and VR-SII at (-0.9725, 4.018, 0). These match the former Scene constants.

## Byte compatibility (golden sha256 captured from `ab0ae69` in a separate worktree)

| Item | sha256 |
|---|---|
| GET `/api/vessels/vinafco268` | `e7840ff9…f9b78f` |
| GET `/api/vessels/vinafco268/model` | `684cb4d4…b1a5d` |
| GET `…/cases/VR-SI/plan` | `788f5cce…dcbee8` |
| GET `…/cases/VR-SII/plan` = POST validate = reopened snapshot = new `/api/vessel-profiles/VINAFCO268/1/cases/VR-SII/plan` | `34014c4d…63ea89c` |
| stored snapshot `plan_json` | `b1a51101…aba3ab41` |

All are asserted in `tests/backend/test_sup02b_api.py`. A legacy snapshot row is not modified by open, list or rebase.

## Subagents (model, effort) and why

| Part | Model / effort | Why this model |
|---|---|---|
| D1/D2 contract, transform, GLB parser, VINAFCO derivation and landmark verification | sonnet / high | Owner-listed hard part: frame conventions, node-tree matrix composition, and 1 mm landmark proof against the real GLB |
| D3 append-only atomic store with integrity checks | sonnet / high | Owner-listed hard part: atomic rename, no-overwrite race and tamper detection |
| D3–D5 service, vessel binding at every Plan entry point, routes, byte-compatibility | sonnet / high | Owner-listed hard part: cross-cutting binding and byte-identical legacy JSON |
| D8 evidence path | haiku / high | Ordinary two-line change |
| D6 frontend (client, panel, form, Scene wiring) | haiku / high | Ordinary UI wiring; server provides every transform value |
| S2B-05 browser spec | haiku / high | Ordinary test authoring |

- The lead (opus, medium) wrote the shared design (`frames`, `viewer block`, `store`, `reference` rules), split the work and captured the golden hashes.
- The lead re-read every diff and re-ran every test itself; no subagent report was accepted as proof.
- Lead-local repairs, disclosed:
  1. VINAFCO landmark names had bow and stern swapped (source X points to the bow, so x min is aft, "lái"). Fixed in `vessel.py`; the values were unchanged.
  2. The upload request body schema was exposed in OpenAPI through a fake `default` response. It is now inlined in `openapi_extra` and the contract is regenerated.
- At most two subagents edited at the same time, and never the same file.

## Commands and results (cloud, Linux, Python 3.11, Node / Playwright 1.64.1)

| Command | Result |
|---|---|
| `python -m pip install -r requirements-dev.txt` then `python -m pytest` (baseline on `ab0ae69`) | 222 passed |
| `python -m pytest -q` (final) | 502 passed: 222 old + 280 new (store 46, domain 145, API 89) |
| `python tooling/export_contract.py` | no diff against the committed `contracts/openapi.json` |
| `npm ci`, `npm run contract`, `npm run build` | `api.ts` unchanged against the commit. Build passes; only the existing chunk-size warning. |
| Playwright, full suite (local override config, see below), baseline before changes | 39 passed. That run overwrote 30 committed SUP-01/02A evidence files (O1), which were then restored with `git checkout -- docs/reviews` and not committed. |
| Playwright, full suite final, including `sup02b.spec.ts` | 42 passed (39 old + 3 new) |
| `git status --short` after the final full run | only `?? tests/browser/sup02b.spec.ts` before commit; nothing under `docs/reviews` changed (S2B-06) |
| `PYTHONDONTWRITEBYTECODE=1 python scripts/cvf_gates/cvf_downstream_gate_runner.py run --phase worker-return` | PASS, 7 mandatory controls, 0 failed |

Browser override: an untracked file, `apps/frontend/playwright.local.config.ts`, excluded through `.git/info/exclude`. It changes only three things:
- the webServer command (`python -m uvicorn …`);
- a temp `SCST_DATA_DIR`;
- the chromium `executablePath` (`/opt/pw-browsers/chromium`).

Evidence screenshots from the final run came from `SCST_EVIDENCE_DIR` in the scratchpad. The two `sup02b-*.png` files were copied into this packet.

## Failed attempts

- Baseline browser run before D8 overwrote closed evidence files, as described above. They were restored and not committed.
- The D8 subagent first stopped on the missing core; it was re-briefed and then completed.
- Cropping the screenshots with PIL failed: the system PIL build is broken. The full-page screenshots are committed instead (about 0.9 and 0.8 MB).
- No test or check was weakened, skipped or edited to pass.

## DA01–DA05 application

- **DA01:**
  - Hold values are integer mm, masses integer g; StrictInt rejects floats and bools.
  - GLB, transform and source dimensions are metres.
  - Verification errors are reported in mm floats and only for display.
  - The UI shows m and tấn through existing formatters; stored values are never rounded.
- **DA02:**
  - The store only appends: temp directory then one rename, no overwrite, no update/delete API, and no repair on integrity failure.
  - All tests use a temporary `SCST_DATA_DIR`.
  - `services/backend/data/**` sha256 is asserted unchanged.
- **DA03:**
  - `provenance.field_status` (ESTIMATED/SOURCED/MEASURED) is required in every profile.
  - `hold.status` and source documents with optional sha256 are also part of the profile.
  - These are shown in the panel and in the vessel region.
  - VINAFCO keeps "hầm ước tính".
- **DA04:**
  - Reused: VesselReference, the VINAFCO routes, `plan_binding.bind` as the single gate, the Scene/Viewer, the plan flow, snapshots, the evidence helper and the contract tooling.
  - Added only what was missing: the store, the profile service, the panel and the GLB reader.
- **DA05:**
  - The usable flow is proven by `sup02b.spec.ts` at desktop and 390px: open VINAFCO, import a synthetic JSON+GLB, preview landmark errors, create, select vessel and case, check hold/draft marker/GLB transform on the canvas, save, reload, reopen.
  - This is technical flow evidence, not business acceptance.

## Limitations and remaining owned work

- The CVF core is absent in the cloud: no doctor run, no core-backed gate beyond the local runner, and no live-provider governance proof. None was needed, because nothing here claims governance behaviour.
- The generic GLB origin convention (keel, mid-length, centreline) is a recorded design decision. It is not enforced beyond landmark and bounds verification; draft markers for a GLB with a different origin would be misplaced while still passing verification. The root may want this in the SPEC.
- `check_reference` re-hashes the stored profile and GLB on every bind, up to 20 MiB, twice for compare. Acceptable for a single-user local tool; caching is future work.
- List ordering for built-ins: see D5 decision.
- Screenshots are full-page, not cropped.
- Owner and root work, untouched by this run:
  - root independent review, gates `reviewer-fast` / `pre-commit`, and the review document;
  - continuity sync;
  - business acceptance, measured hold data, SUP-03 and M2d;
  - the merge decision.
