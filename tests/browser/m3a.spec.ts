import { spawn, type ChildProcess } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Page } from "../../apps/frontend/node_modules/@playwright/test";

// M3a M3A-04/M3A-05 browser flow: multi-layer column stacking (columns-v1) on the VINAFCO 268 Baltimore list.
// Desktop: preview -> apply -> layer cells, 3D and 2D -> save -> reopen -> report and XLSX -> new cargo revision -> rebase.
// The revision step changes the shared DB, so the desktop flow runs on its OWN backend (port 8769, temporary SCST_DATA_DIR),
// the same way m2d does; the shared suite DB stays at its revision for the specs that sort after this file.
// Screenshots go to testInfo.outputPath (never under docs/reviews). Only the M3a planner/stacking surface is asserted here.

const PRIVATE_PORT = 8769;
const PRIVATE_BASE = `http://127.0.0.1:${PRIVATE_PORT}`;
const python = () => process.env.SCST_TEST_PYTHON ?? (process.platform === "win32" ? "..\\..\\.venv\\Scripts\\python.exe" : "python");

const GEOMETRY_CODES = new Set(["OUT_OF_BOUNDS", "OVERLAP", "LAYER_UNSUPPORTED", "LAYER_INDEX_INVALID"]);
const PLANNER_UNPLACED_CODES = ["EXCLUDED", "TOO_HIGH", "FOOTPRINT_TOO_LARGE", "MASS_LIMIT", "HEURISTIC_NO_SPACE", "STACK_HEIGHT"];
const UNCHECKED_STACKING = [
  "Tải chồng cho phép trên bó (chưa có dữ liệu)",
  "Tải cục bộ đáy hầm",
  "Kê, chèn và chằng buộc",
  "Ổn định phương tiện",
];
const MULTI_LAYER_NOTICE = "Phương án nhiều tầng: chưa kiểm tải chồng, tải sàn, chằng buộc và ổn định.";

type Unit = { id: string; mass_g: number; requirement: string; dimensions_um?: number[] | null; source_ref?: { workbook_sha256: string; group_id?: string } | null };
type Placement = { unit_id: string; x_mm: number; y_mm: number; z_mm: number; layer: number; yaw_deg: number; supported_by: string[] };
type Plan = Record<string, unknown> & { stacking?: string; hold: { length_mm: number; width_mm: number; height_mm: number }; limits: { voyage_cargo_limit_g: number; cargo_onboard_g?: number }; units: Unit[]; placements: Placement[] };
type Issue = { code: string; message?: string };
type Evaluation = { plan: Plan; status: string; summary: { manifest_mass_g: number; placed_mass_g: number; placed_count: number; remaining_capacity_g: number }; issues: Issue[]; unchecked: string[] };
type Unplaced = { unit_id: string; code: string; message: string };
type Preview = { algorithm: string; evaluation: Evaluation; unplaced: Unplaced[] };
type Mesh = { id: string; position: number[]; dimensions: number[] };
type Saved = { id: string };
type Dropped = { unit_id: string; reason: "REMOVED" | "CHANGED" | "SUPPORT_LOST"; x_mm: number; y_mm: number; yaw_deg: number };
type RebaseResult = { source_revision_id: string; target_revision_id: string; kept_placement_count: number; dropped_placements: Dropped[]; candidate: Evaluation };
type SnapshotItem = { id: string; recheck_status: string };
type ReportModel = { notices: { code: string; message: string }[] };

const geometryIssues = (evaluation: Evaluation) => evaluation.issues.filter((i) => GEOMETRY_CODES.has(i.code) || i.code.startsWith("SUPPORT_"));

async function postResult<T>(page: Page, pathname: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((r) => new URL(r.url()).pathname === pathname && r.request().method() === "POST");
  await action();
  const response = await pending;
  if (!response.ok()) throw new Error(`POST ${pathname} ${response.status()}: ${await response.text()}`);
  return (await response.json()) as T;
}

async function getResult<T>(page: Page, pathname: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((r) => new URL(r.url()).pathname === pathname && r.request().method() === "GET");
  await action();
  const response = await pending;
  expect(response.ok(), `GET ${pathname}`).toBe(true);
  return (await response.json()) as T;
}

async function getJson<T>(request: APIRequestContext, path: string): Promise<T> {
  const response = await request.get(path);
  expect(response.ok(), `GET ${path}`).toBe(true);
  return (await response.json()) as T;
}

async function loadPipeList(page: Page): Promise<Evaluation> {
  await postResult<Evaluation>(page, "/api/pipe-list/preview", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
  return postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
}

// Switching to VINAFCO 268 keeps the voyage limit of the plan already open (min with the case ceiling, by design), so a
// fresh page would keep the 32 t demo limit and plan only ~22 bundles. The owner sets the VR-SII case ceiling (3 517 500 kg,
// the case's own voyage limit) in the UI, then applies it, before the planner runs. Returns the checked plan with that limit.
async function setCaseVoyageLimit(page: Page): Promise<Evaluation> {
  await page.getByLabel("Giới hạn chuyến (kg)").fill("3517500");
  const checked = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(checked.plan.limits.voyage_cargo_limit_g).toBe(3_517_500_000);
  expect(checked.plan.units).toHaveLength(1076);
  return checked;
}

async function rebaseFromUi(page: Page, savedId: string): Promise<RebaseResult> {
  const pending = page.waitForResponse((r) => r.url().endsWith(`/api/snapshots/${savedId}/rebase`) && r.request().method() === "POST");
  await page.getByRole("button", { name: "Tạo bản theo dữ liệu mới" }).click();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return (await response.json()) as RebaseResult;
}

// Accounting for a columns-v1 preview: every bundle is placed once or has a reason, z/layer/support rules hold (D2.4).
function checkStackedPreview(preview: Preview, input: Plan): void {
  const candidate = preview.evaluation.plan;
  const placements = candidate.placements;
  const placed = new Set(placements.map((p) => p.unit_id));
  const unplaced = new Set(preview.unplaced.map((r) => r.unit_id));
  expect(placed.size).toBe(placements.length);
  expect(unplaced.size).toBe(preview.unplaced.length);
  expect([...placed].filter((id) => unplaced.has(id))).toEqual([]);
  expect(placed.size + unplaced.size).toBe(input.units.length);
  const { placements: _candidatePlacements, stacking, ...candidateRest } = candidate;
  const { placements: _inputPlacements, ...inputRest } = input;
  expect(stacking).toBe("COLUMNS_V1");
  expect(candidateRest).toEqual(inputRest);
  expect(candidate.units).toEqual(input.units);
  expect(preview.unplaced.every((r) => PLANNER_UNPLACED_CODES.includes(r.code) && r.message.length > 0)).toBe(true);

  const byId = new Map(placements.map((p) => [p.unit_id, p]));
  for (const p of placements) {
    expect([0, 90]).toContain(p.yaw_deg);
    if (p.z_mm === 0) {
      expect(p.layer).toBe(0);
      expect(p.supported_by).toEqual([]);
    } else {
      expect(p.z_mm).toBeGreaterThan(0);
      expect(p.supported_by.length).toBeGreaterThan(0);
      expect(p.layer).toBe(Math.max(...p.supported_by.map((s) => byId.get(s)!.layer)) + 1);
    }
  }
  const massOf = new Map(input.units.map((u) => [u.id, u.mass_g]));
  const placedMass = placements.reduce((sum, p) => sum + massOf.get(p.unit_id)!, 0);
  expect(preview.evaluation.summary.placed_mass_g).toBe(placedMass);
  expect(preview.evaluation.summary.placed_mass_g).toBeLessThanOrEqual(input.limits.voyage_cargo_limit_g - (input.limits.cargo_onboard_g ?? 0));
}

// Walks the cargo table pages until a layer cell shows more than one layer. Reads all cells of a page in one call.
async function firstStackedRow(page: Page): Promise<{ id: string; layerText: string }> {
  const next = page.getByRole("button", { name: "Trang sau", exact: true });
  for (let guard = 0; guard < 60; guard++) {
    const cells = await page.locator('[data-testid^="layer-cell-"]').evaluateAll((els) =>
      els.map((el) => [el.getAttribute("data-testid") ?? "", (el.textContent ?? "").trim()] as const));
    const hit = cells.find(([, text]) => /^\d+$/.test(text) && Number(text) > 1);
    if (hit) return { id: hit[0].slice("layer-cell-".length), layerText: hit[1] };
    if (await next.isDisabled()) break;
    await next.click();
  }
  throw new Error("no stacked layer cell in the cargo table");
}

// Walks the cargo table pages until the given unit row is rendered on the current page.
async function findCargoRow(page: Page, id: string): Promise<void> {
  const next = page.getByRole("button", { name: "Trang sau", exact: true });
  for (let guard = 0; guard < 60; guard++) {
    if ((await page.getByTestId(`unit-${id}`).count()) > 0) return;
    if (await next.isDisabled()) break;
    await next.click();
  }
  throw new Error(`cargo row ${id} not found`);
}

const docScrollWidth = (page: Page) => page.evaluate(() => document.documentElement.scrollWidth);
const meshesOf = async (page: Page): Promise<Mesh[]> =>
  JSON.parse((await page.getByTestId("three-canvas").getAttribute("data-meshes")) ?? "[]") as Mesh[];

async function privateServer(): Promise<{ stop: () => void }> {
  const dataDir = mkdtempSync(join(tmpdir(), "scst-m3a-"));
  const child: ChildProcess = spawn(python(), ["-m", "uvicorn", "app.main:app", "--app-dir", "../../services/backend", "--host", "127.0.0.1", "--port", String(PRIVATE_PORT)],
    { env: { ...process.env, SCST_DATA_DIR: dataDir }, stdio: "ignore" });
  const stop = () => { child.kill(); try { rmSync(dataDir, { recursive: true, force: true }); } catch { /* temp dir */ } };
  for (let i = 0; i < 150; i++) {
    try { if ((await fetch(`${PRIVATE_BASE}/api/health`)).ok) return { stop }; } catch { /* not up yet */ }
    await new Promise((r) => setTimeout(r, 200));
  }
  stop();
  throw new Error("private M3a backend did not start");
}

test("M3A-05 desktop: columns-v1 preview, apply, layer cells, 3D, 2D, save, reopen, report, XLSX, new revision, rebase", async ({ page, playwright }, testInfo) => {
  test.setTimeout(120_000);
  const server = await privateServer();
  const request = await playwright.request.newContext({ baseURL: PRIVATE_BASE });
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  try {
    const name = `M3a nhiều tầng ${Date.now()}`;

    // 1. list in VINAFCO 268, multi-layer preview
    await page.goto(`${PRIVATE_BASE}/?viewerDiagnostics=1`);
    await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
    const loaded = await loadPipeList(page);
    expect(loaded.plan.units).toHaveLength(1076);
    const ready = await setCaseVoyageLimit(page);
    await page.getByRole("combobox", { name: "Cách xếp thử" }).selectOption("columns-v1");
    const preview = await postResult<Preview>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
    expect(preview.algorithm).toBe("columns-v1");
    checkStackedPreview(preview, ready.plan);
    const candidate = preview.evaluation.plan;
    expect(candidate.placements.length).toBeGreaterThanOrEqual(900);
    expect(candidate.placements.length).toBe(preview.evaluation.summary.placed_count);
    const columns = candidate.placements.filter((p) => p.z_mm === 0).length;
    const maxLayers = Math.max(...candidate.placements.map((p) => p.layer)) + 1;
    expect(maxLayers).toBeGreaterThanOrEqual(2);
    await expect(page.getByTestId("planner-stack-summary")).toHaveText(
      `Nhiều tầng: ${columns} cột · tối đa ${maxLayers} tầng · đã xếp ${preview.evaluation.summary.placed_count} bó · chưa xếp ${preview.unplaced.length} bó`,
    );
    await expect(page.getByTestId("planner-preview")).toBeVisible();

    // 2. apply: validated plan equals the preview and has no geometry issues; the unchecked list names the stacking gaps
    const applied = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
    expect(applied.plan.placements).toEqual(candidate.placements);
    expect(applied.plan.stacking).toBe("COLUMNS_V1");
    expect(geometryIssues(applied)).toEqual([]);
    expect(applied.unchecked).toEqual(expect.arrayContaining(UNCHECKED_STACKING));
    await expect(page.getByTestId("pipe-total")).toContainText(`đã xếp ${applied.summary.placed_count} bó`);
    await expect(page.locator("#checks")).toContainText("Kê, chèn và chằng buộc");

    // 3. a stacked bundle: its layer cell is > 1 and the detail panel names its supporting bundles
    const row = await firstStackedRow(page);
    const stackedPlacement = applied.plan.placements.find((p) => p.unit_id === row.id)!;
    expect(stackedPlacement.layer).toBeGreaterThan(0);
    expect(row.layerText).toBe(String(stackedPlacement.layer + 1));
    expect(stackedPlacement.supported_by.length).toBeGreaterThan(0);
    await page.getByTestId(`unit-${row.id}`).getByRole("button").click();
    const detail = page.getByTestId("unit-stack-detail");
    await expect(detail).toContainText(`Tầng ${stackedPlacement.layer + 1} · Z `);
    await expect(detail).toContainText(`Bó đỡ: ${stackedPlacement.supported_by.join(", ")}`);

    // 4. 3D: one mesh per placement; the stacked mesh sits at its z_mm (box bottom = z, centre = z + height/2)
    await expect.poll(async () => (await meshesOf(page)).length).toBe(applied.plan.placements.length);
    const mesh = (await meshesOf(page)).find((m) => m.id === row.id)!;
    expect(mesh).toBeDefined();
    expect(stackedPlacement.z_mm).toBeGreaterThan(0);
    expect(mesh.position[1]).toBeCloseTo(stackedPlacement.z_mm / 1000 + mesh.dimensions[1] / 2, 6);

    // 5. 2D plan: stacked columns carry a ×N label
    await page.getByRole("button", { name: "Mặt bằng", exact: true }).click();
    await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
    const stackLabels = page.getByTestId("plan2d-stack-label");
    await expect.poll(() => stackLabels.count()).toBeGreaterThan(0);
    for (const text of await stackLabels.allTextContents()) expect(text).toMatch(/^×\d+$/);
    await page.screenshot({ path: testInfo.outputPath("m3a-desktop-planned.png"), fullPage: true });

    // 6. save, reload, reopen from the list: placements identical
    await page.getByLabel("Tên phương án lưu").fill(name);
    const saved = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
    const stored = await getJson<Evaluation>(request, `/api/snapshots/${saved.id}`);
    expect(stored.plan.placements).toEqual(applied.plan.placements);
    expect(stored.plan.stacking).toBe("COLUMNS_V1");
    await page.reload();
    await page.getByLabel("Phương án đã lưu").selectOption(saved.id);
    const reopened = await getResult<Evaluation>(page, `/api/snapshots/${saved.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
    expect(reopened.plan.placements).toEqual(applied.plan.placements);
    await expect(page.getByTestId("pipe-total")).toContainText(`đã xếp ${applied.summary.placed_count} bó`);
    await findCargoRow(page, row.id);
    await expect(page.getByTestId(`layer-cell-${row.id}`)).toHaveText(row.layerText);

    // 7. report page: multi-layer notice, no single-layer notice, stack labels, layer and column totals, units columns
    const exportLink = page.getByRole("link", { name: "Xuất báo cáo" });
    await expect(exportLink).toHaveAttribute("href", `#/report/${saved.id}`);
    const [report] = await Promise.all([page.context().waitForEvent("page"), exportLink.click()]);
    report.on("pageerror", (e) => pageErrors.push(String(e)));
    await expect(report.getByTestId("report-plan-name")).toHaveText(name);
    const model = await getJson<ReportModel>(request, `/api/snapshots/${saved.id}/report`);
    expect(model.notices.map((n) => n.code)).toContain("MULTI_LAYER");
    expect(model.notices.map((n) => n.code)).not.toContain("SINGLE_LAYER");
    await expect(report.getByTestId("notice-MULTI_LAYER")).toHaveText(MULTI_LAYER_NOTICE);
    await expect(report.getByTestId("notice-SINGLE_LAYER")).toHaveCount(0);
    await expect.poll(() => report.getByTestId("report-stack-label").count()).toBeGreaterThan(0);
    await expect(report.getByTestId("report-total-layer_count").locator("th")).toHaveText("Tổng số tầng");
    await expect(report.getByTestId("report-total-layer_count").locator("td")).toHaveText(String(maxLayers));
    await expect(report.getByTestId("report-total-column_count").locator("td")).toHaveText(String(columns));
    const unitHeaders = report.getByTestId("report-units").locator("thead th");
    await expect(unitHeaders.filter({ hasText: /^Tầng$/ })).toHaveCount(1);
    await expect(unitHeaders.filter({ hasText: /^Bó đỡ$/ })).toHaveCount(1);
    await expect(report.getByTestId(`report-unit-${row.id}`)).toContainText(stackedPlacement.supported_by[0]);
    await report.screenshot({ path: testInfo.outputPath("m3a-desktop-report.png"), fullPage: true });

    // 8. XLSX download: status 200, non-empty, a zip
    const [download] = await Promise.all([report.waitForEvent("download"), report.getByRole("link", { name: "Tải XLSX" }).click()]);
    const downloaded = readFileSync((await download.path())!);
    expect(downloaded.length).toBeGreaterThan(0);
    expect(downloaded.subarray(0, 2).toString("latin1")).toBe("PK");
    const xlsx = await request.get(`/api/snapshots/${saved.id}/report.xlsx`);
    expect(xlsx.status()).toBe(200);
    expect((await xlsx.body()).length).toBeGreaterThan(0);
    await report.close();

    // 9. a new revision changes the mass of a group that supports bundles of another group
    const groupOf = new Map(applied.plan.units.map((u) => [u.id, u.source_ref?.group_id ?? ""]));
    const massOf = new Map(applied.plan.units.map((u) => [u.id, u.mass_g]));
    const lowerSupported = applied.plan.placements.find((p) => p.supported_by.length > 0 && groupOf.get(p.supported_by[0]) !== groupOf.get(p.unit_id))!;
    const supportGroup = groupOf.get(lowerSupported.supported_by[0])!;
    const member = applied.plan.placements.find((p) => groupOf.get(p.unit_id) === supportGroup)!;
    const latest = (await getJson<{ latest_revision_id: string }>(request, "/api/cargo-revisions")).latest_revision_id;
    const created = await request.post("/api/cargo-revisions", {
      data: {
        parent_revision_id: latest,
        source: { kind: "FACTORY", reference: "M3A browser", received_date: "2026-11-05", note: "kiểm" },
        changes: [{ type: "UPDATE_GROUP", group_id: supportGroup, confirmation: "CONFIRMED", set: { mass_g: massOf.get(member.unit_id)! - 1000 } }],
      },
    });
    expect(created.ok()).toBe(true);
    const newRevision = (await created.json()) as { revision_id: string };

    // 10. UI: the saved plan needs a recheck; rebase creates the new candidate and lists the dropped bundles
    await page.reload();
    await expect(page.getByTestId("revision-latest")).toContainText(newRevision.revision_id);
    await page.getByLabel("Phương án đã lưu").selectOption(saved.id);
    const item = (await getJson<SnapshotItem[]>(request, "/api/snapshots")).find((i) => i.id === saved.id)!;
    expect(item.recheck_status).toBe("NEEDS_RECHECK");
    await expect(page.getByTestId(`saved-item-${saved.id}`)).toContainText("Cần kiểm lại");

    const rebase = await rebaseFromUi(page, saved.id);
    const dropped = rebase.dropped_placements;
    const lost = dropped.filter((d) => d.reason === "SUPPORT_LOST");
    expect(lost.length).toBeGreaterThan(0);
    const droppedIds = new Set(dropped.map((d) => d.unit_id));
    const groupPlacedIds = applied.plan.placements.filter((p) => groupOf.get(p.unit_id) === supportGroup).map((p) => p.unit_id).sort();
    expect(dropped.filter((d) => d.reason === "CHANGED").map((d) => d.unit_id).sort()).toEqual(groupPlacedIds);
    // every SUPPORT_LOST bundle rests on a dropped bundle; no kept bundle rests on a dropped one
    for (const d of lost) expect(byIdOf(applied.plan, d.unit_id).supported_by.some((s) => droppedIds.has(s))).toBe(true);
    const kept = rebase.candidate.plan.placements;
    expect(kept.length).toBe(rebase.kept_placement_count);
    expect(kept.length + dropped.length).toBe(applied.plan.placements.length);
    const keptIds = new Set(kept.map((p) => p.unit_id));
    for (const p of kept) for (const s of p.supported_by) expect(keptIds.has(s)).toBe(true);
    // the candidate validates without geometry issues on the server
    expect(geometryIssues(rebase.candidate)).toEqual([]);
    const revalidated = await request.post("/api/validate", { data: rebase.candidate.plan });
    expect(revalidated.ok()).toBe(true);
    expect(geometryIssues((await revalidated.json()) as Evaluation)).toEqual([]);

    const panel = page.getByTestId("rebase-dropped");
    await expect(panel).toBeVisible();
    await expect(panel).toContainText(`Giữ ${rebase.kept_placement_count} vị trí; bỏ ${dropped.length} vị trí`);
    await expect(page.getByTestId("revision-in-use")).toContainText(rebase.target_revision_id);
    await expect(page.getByTestId("pipe-total")).toContainText(`đã xếp ${rebase.kept_placement_count} bó`);
    await expect(panel.locator('select[aria-label="Lọc vị trí bị bỏ"] option[value="SUPPORT_LOST"]')).toHaveText(`Mất đỡ (${lost.length})`);
    await panel.getByRole("combobox", { name: "Lọc vị trí bị bỏ", exact: true }).selectOption("SUPPORT_LOST");
    const items = page.getByTestId("rebase-dropped-item");
    await expect(items).toHaveCount(Math.min(50, lost.length));
    const texts = await items.allTextContents();
    expect(texts.map((t) => t.split(" · ")[0])).toEqual(lost.slice(0, 50).map((d) => d.unit_id));
    expect(texts.every((t) => t.split(" · ")[1] === "Mất đỡ")).toBe(true);
    await expect(page.getByTestId("rebase-dropped-page")).toHaveText(`Trang 1/${Math.ceil(lost.length / 50)} · dòng 1–${Math.min(50, lost.length)} trên tổng ${lost.length}`);
    await panel.screenshot({ path: testInfo.outputPath("m3a-desktop-rebase-dropped.png") });

    expect(pageErrors).toEqual([]);
  } finally {
    await request.dispose();
    server.stop();
  }
});

function byIdOf(plan: Plan, unitId: string): Placement {
  const found = plan.placements.find((p) => p.unit_id === unitId);
  if (!found) throw new Error(`no placement for ${unitId}`);
  return found;
}

test("M3A-04 390px: multi-layer preview and apply, the Tầng column is reached by the table's horizontal scroll, no page overflow", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 390, height: 844 });
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  await page.goto("/");
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await loadPipeList(page);
  await setCaseVoyageLimit(page);

  const select = page.getByRole("combobox", { name: "Cách xếp thử" });
  await expect(select).toBeVisible();
  await select.selectOption("columns-v1");
  const preview = await postResult<Preview>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  expect(preview.algorithm).toBe("columns-v1");
  expect(preview.evaluation.plan.placements.length).toBeGreaterThanOrEqual(900);
  await expect(page.getByTestId("planner-stack-summary")).toBeVisible();
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(390 + 1);

  const applied = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  expect(geometryIssues(applied)).toEqual([]);
  expect(applied.plan.placements).toEqual(preview.evaluation.plan.placements);
  await expect(page.getByTestId("pipe-total")).toContainText(`đã xếp ${applied.summary.placed_count} bó`);

  // The cargo table scrolls horizontally inside its own wrapper; the page itself does not overflow.
  const wrap = page.locator("#cargo .table-wrap");
  await expect.poll(() => wrap.evaluate((el) => el.scrollWidth > el.clientWidth)).toBe(true);
  const row = await firstStackedRow(page);
  const cell = page.getByTestId(`layer-cell-${row.id}`);
  await cell.scrollIntoViewIfNeeded();
  await expect(cell).toBeInViewport();
  await expect(cell).toHaveText(row.layerText);
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(390 + 1);
  expect(pageErrors).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("m3a-390-planned.png"), fullPage: true });
});

test("default planner stays one-layer: no multi-layer choice is made, the preview is single-layer with no stack summary", async ({ page }) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  const loaded = await loadPipeList(page);
  expect(loaded.plan.units).toHaveLength(1076);
  await expect(page.getByRole("combobox", { name: "Cách xếp thử" })).toHaveValue("guillotine-single-layer-v1");

  const pending = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/planner/preview" && r.request().method() === "POST");
  await page.getByRole("button", { name: "Xếp thử tự động" }).click();
  const response = await pending;
  expect(response.ok()).toBe(true);
  expect(new URL(response.url()).searchParams.get("algorithm") ?? "guillotine-single-layer-v1").toBe("guillotine-single-layer-v1");

  const preview = (await response.json()) as Preview;
  expect(preview.algorithm).toBe("guillotine-single-layer-v1");
  expect(preview.evaluation.plan.stacking).toBeUndefined();
  expect(preview.evaluation.plan.placements.length).toBeGreaterThan(0);
  expect(preview.evaluation.plan.placements.every((p) => p.z_mm === 0 && p.layer === 0 && p.supported_by.length === 0)).toBe(true);
  await expect(page.getByTestId("planner-preview")).toBeVisible();
  await expect(page.getByTestId("planner-stack-summary")).toHaveCount(0);
});
