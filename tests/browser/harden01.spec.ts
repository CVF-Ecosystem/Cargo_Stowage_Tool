import { spawn, type ChildProcess } from "node:child_process";
import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Locator, Page } from "../../apps/frontend/node_modules/@playwright/test";
import { evidenceDir as baseEvidenceDir } from "./evidence";

// HARDEN-01 H-01 (labels from H-02): the rebase panel pages its dropped placements (50 per page) and filters
// them by reason, at desktop and 390px. The fixture removes 60 bundles and changes a group's mass, which would break
// later spec files that expect the full 1076-bundle list on the suite's shared DB. So this file starts its OWN backend
// (same app, port 8767, its own temporary SCST_DATA_DIR) and leaves the shared server untouched. Revision, group and
// bundle ids are still derived from the live latest revision. Each test builds its own fixture:
// one saved v2 plan with 140 placements (70 CHANGED, 60 REMOVED, 10 kept) and one new revision that causes both reasons.

const evidenceDir = baseEvidenceDir();

const ISOLATED_PORT = 8767;
let server: ChildProcess | undefined;
test.use({ baseURL: `http://127.0.0.1:${ISOLATED_PORT}` });

test.beforeAll(async ({}, testInfo) => {
  const root = resolve(testInfo.project.testDir, "../..");
  // Same interpreter choice as the committed playwright.config.ts on Windows; SCST_PYTHON or "python" elsewhere.
  const python = process.env.SCST_PYTHON ?? (process.platform === "win32" ? resolve(root, ".venv/Scripts/python.exe") : "python");
  const dataDir = mkdtempSync(resolve(tmpdir(), "scst-harden01-"));
  server = spawn(python, ["-m", "uvicorn", "app.main:app", "--app-dir", resolve(root, "services/backend"), "--host", "127.0.0.1",
    "--port", String(ISOLATED_PORT)], { env: { ...process.env, SCST_DATA_DIR: dataDir }, stdio: "ignore" });
  const deadline = Date.now() + 30000;
  for (;;) {
    try {
      if ((await fetch(`http://127.0.0.1:${ISOLATED_PORT}/api/health`)).ok) break;
    } catch { /* not up yet */ }
    if (Date.now() > deadline || server.exitCode !== null) throw new Error("HARDEN-01 isolated backend did not start");
    await new Promise((r) => setTimeout(r, 250));
  }
});

test.afterAll(async () => {
  server?.kill();
});
const PAGE_SIZE = 50;
const CHANGED_PLACED = 70; // placed bundles of a group whose mass_g changes -> CHANGED
const REMOVED_PLACED = 60; // trailing placed bundles of a group whose bundle_count shrinks -> REMOVED
const KEPT_PLACED = 10; // placed bundles of an untouched group -> kept by rebase
const MASS_STEP_G = 1234; // grams per bundle, offset from the live value so every run is a real change
const SOURCE_DATE = "2026-11-04";

type Group = { group_id: string; bundle_count: number; mass_g: number; dimension_warning: boolean; bundle_ids: string[] };
type RevisionList = { latest_revision_id: string };
type RevisionDetail = { revision_id: string; groups: Group[] };
type Placement = { unit_id: string; x_mm: number; y_mm: number; z_mm: number; layer: number; supported_by: string[]; yaw_deg: number };
type Plan = Record<string, unknown> & { placements: Placement[]; units: { id: string }[]; hold: Record<string, number>; limits: Record<string, number> };
type Evaluation = { plan: Plan };
type Saved = { id: string };
type SnapshotItem = {
  id: string; cargo_revision_id: string | null; recheck_status: string; added_count: number; removed_count: number;
  changed_count: number; placed_affected_count: number; placed_dropped_on_rebase_count: number;
};
type Dropped = { unit_id: string; reason: "REMOVED" | "CHANGED"; x_mm: number; y_mm: number; yaw_deg: number };
type RebaseResult = { source_revision_id: string; target_revision_id: string; kept_placement_count: number; dropped_placements: Dropped[] };
type Fixture = {
  name: string; savedId: string; latestAfter: string;
  expectedDropped: number; expectedChanged: number; expectedRemoved: number; expectedKept: number;
};

const shotLocator = async (locator: Locator, name: string) => {
  mkdirSync(evidenceDir, { recursive: true });
  await locator.screenshot({ path: resolve(evidenceDir, name) });
};

async function getJson<T>(request: APIRequestContext, path: string): Promise<T> {
  const r = await request.get(path);
  expect(r.ok(), `GET ${path}`).toBe(true);
  return (await r.json()) as T;
}

async function postJson<T>(request: APIRequestContext, path: string, data: unknown): Promise<T> {
  const r = await request.post(path, { data });
  expect(r.ok(), `POST ${path}`).toBe(true);
  return (await r.json()) as T;
}

async function snapshotItem(request: APIRequestContext, id: string): Promise<SnapshotItem> {
  const items = await getJson<SnapshotItem[]>(request, "/api/snapshots");
  const item = items.find((i) => i.id === id);
  expect(item, `snapshot ${id} is listed`).toBeDefined();
  return item!;
}

// Builds plan + revision through the API only. Returns the ids the UI test needs and the expected counts.
async function buildFixture(request: APIRequestContext, name: string, sourceRef: string): Promise<Fixture> {
  const latest = (await getJson<RevisionList>(request, "/api/cargo-revisions")).latest_revision_id;
  const detail = await getJson<RevisionDetail>(request, `/api/cargo-revisions/${encodeURIComponent(latest)}`);

  const changed = detail.groups.find((g) => !g.dimension_warning && g.bundle_count >= CHANGED_PLACED);
  expect(changed, "a group with at least 70 bundles").toBeDefined();
  const removed = detail.groups.find((g) => !g.dimension_warning && g.group_id !== changed!.group_id && g.bundle_count > REMOVED_PLACED);
  expect(removed, "a group with more than 60 bundles").toBeDefined();
  const kept = detail.groups.find((g) => !g.dimension_warning && g.group_id !== changed!.group_id && g.group_id !== removed!.group_id && g.bundle_count >= KEPT_PLACED);
  expect(kept, "an untouched group with at least 10 bundles").toBeDefined();

  const changedIds = changed!.bundle_ids.slice(0, CHANGED_PLACED);
  const removedIds = removed!.bundle_ids.slice(-REMOVED_PLACED); // the bundles bundle_count < current will drop
  const keptIds = kept!.bundle_ids.slice(0, KEPT_PLACED);

  // roomy hold so the 140 placements fit on a non-overlapping grid (7.5 m columns, 0.52 m rows)
  const demo = await getJson<{ plan: Plan }>(request, "/api/demo");
  const roomy: Plan = {
    ...demo.plan,
    hold: { ...demo.plan.hold, length_mm: 60000, width_mm: 20000, height_mm: 4000 },
    limits: { ...demo.plan.limits, certificate_cargo_limit_g: 10 ** 10, voyage_cargo_limit_g: 10 ** 10, cargo_onboard_g: 0 },
  };
  const preview = await postJson<Evaluation>(request, `/api/cargo-revisions/${encodeURIComponent(latest)}/plan-preview`, roomy);
  const unitIds = new Set(preview.plan.units.map((u) => u.id));
  const placedIds = [...changedIds, ...removedIds, ...keptIds];
  expect(placedIds.every((id) => unitIds.has(id))).toBe(true);
  const placements: Placement[] = placedIds.map((unit_id, k) => ({
    unit_id, x_mm: (k % 8) * 7500, y_mm: Math.floor(k / 8) * 520, z_mm: 0, layer: 0, supported_by: [], yaw_deg: 0,
  }));
  const saved = await postJson<Saved>(request, "/api/snapshots", { name, plan: { ...preview.plan, placements } });

  const created = await postJson<{ revision_id: string }>(request, "/api/cargo-revisions", {
    parent_revision_id: latest,
    source: { kind: "FACTORY", reference: sourceRef, received_date: SOURCE_DATE, note: "" },
    changes: [
      { type: "UPDATE_GROUP", group_id: changed!.group_id, confirmation: "CONFIRMED", set: { mass_g: changed!.mass_g + MASS_STEP_G } },
      { type: "UPDATE_GROUP", group_id: removed!.group_id, confirmation: "CONFIRMED", set: { bundle_count: removed!.bundle_count - REMOVED_PLACED } },
    ],
  });
  const after = await getJson<RevisionDetail>(request, `/api/cargo-revisions/${encodeURIComponent(created.revision_id)}`);
  const removedAfter = after.groups.find((g) => g.group_id === removed!.group_id);
  expect(removedAfter?.bundle_count).toBe(removed!.bundle_count - REMOVED_PLACED);
  expect(removedAfter!.bundle_ids.some((id) => removedIds.includes(id))).toBe(false);

  return {
    name, savedId: saved.id, latestAfter: created.revision_id,
    expectedDropped: changedIds.length + removedIds.length, expectedChanged: changedIds.length,
    expectedRemoved: removedIds.length, expectedKept: keptIds.length,
  };
}

// Reload-equivalent: fresh page, select the saved plan, check the recheck text against the server counts.
async function openRecheckedPlan(page: Page, request: APIRequestContext, fx: Fixture) {
  await page.goto("/");
  await expect(page.getByTestId("revision-latest")).toContainText(fx.latestAfter);
  await page.getByLabel("Phương án đã lưu").selectOption(fx.savedId);

  const item = await snapshotItem(request, fx.savedId);
  expect(item.recheck_status).toBe("NEEDS_RECHECK");
  expect(item.placed_dropped_on_rebase_count).toBe(fx.expectedDropped);
  expect(item.placed_affected_count).toBeGreaterThanOrEqual(fx.expectedDropped);
  const recheck = `Cần kiểm lại: thêm ${item.added_count} · bỏ ${item.removed_count} · đổi ${item.changed_count} bó; `
    + `${item.placed_affected_count} bó đã đặt bị ảnh hưởng (có dữ liệu đổi) · `
    + `${item.placed_dropped_on_rebase_count} vị trí sẽ bỏ khi tạo bản mới (${item.cargo_revision_id ?? "?"})`;
  await expect(page.getByTestId(`saved-item-${fx.savedId}`)).toContainText(recheck);
  await expect(page.getByTestId("saved-recheck")).toHaveText(recheck);
}

// Clicks the UI rebase button and returns the server response the UI received.
async function rebaseFromUi(page: Page, savedId: string): Promise<RebaseResult> {
  const pending = page.waitForResponse((r) => r.url().endsWith(`/api/snapshots/${savedId}/rebase`) && r.request().method() === "POST");
  await page.getByRole("button", { name: "Tạo bản theo dữ liệu mới" }).click();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return (await response.json()) as RebaseResult;
}

const panelOf = (page: Page) => page.getByTestId("rebase-dropped");
const itemsOf = (page: Page) => page.getByTestId("rebase-dropped-item");
const prevBtn = (page: Page) => page.getByRole("button", { name: "Trang vị trí trước", exact: true });
const nextBtn = (page: Page) => page.getByRole("button", { name: "Trang vị trí sau", exact: true });
const filterOf = (page: Page) => page.getByRole("combobox", { name: "Lọc vị trí bị bỏ", exact: true });

// Checks one page of `rows` (already filtered, in server order): status text, row count, unit ids and reasons.
async function expectPage(page: Page, rows: Dropped[], pageNo: number) {
  const total = rows.length;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const start = (pageNo - 1) * PAGE_SIZE;
  const end = Math.min(total, start + PAGE_SIZE);
  await expect(page.getByTestId("rebase-dropped-page")).toHaveText(`Trang ${pageNo}/${pages} · dòng ${start + 1}–${end} trên tổng ${total}`);
  await expect(itemsOf(page)).toHaveCount(end - start);
  const texts = await itemsOf(page).allTextContents();
  expect(texts.map((t) => t.split(" · ")[0])).toEqual(rows.slice(start, end).map((d) => d.unit_id));
  expect(texts.map((t) => t.split(" · ")[1])).toEqual(rows.slice(start, end).map((d) => (d.reason === "REMOVED" ? "Bỏ" : "Đổi")));
}

// Walks every page forward (checking the last-page button state), then back to page 1.
async function walkAllPages(page: Page, rows: Dropped[]) {
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  await expectPage(page, rows, 1);
  if (rows.length <= PAGE_SIZE) return;
  await expect(prevBtn(page)).toBeDisabled();
  for (let p = 2; p <= pages; p++) {
    await nextBtn(page).click();
    await expectPage(page, rows, p);
    await expect(prevBtn(page)).toBeEnabled();
  }
  await expect(nextBtn(page)).toBeDisabled();
  for (let p = pages - 1; p >= 1; p--) {
    await prevBtn(page).click();
    await expectPage(page, rows, p);
  }
  await expect(prevBtn(page)).toBeDisabled();
}

async function expectNoHorizontalOverflow(page: Page) {
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(scrollWidth).toBeLessThanOrEqual(391); // 390px viewport, +1 px tolerance
}

test("H-01 desktop: rebase with 140 placed bundles (130 dropped: CHANGED and REMOVED) pages 50 rows and filters", async ({ page, request }) => {
  test.setTimeout(240_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();
  const fx = await buildFixture(request, `HARDEN-01 H1 desktop ${tag}`, `HARDEN01-D-${tag}`);
  expect(fx.expectedDropped).toBeGreaterThan(100);

  await openRecheckedPlan(page, request, fx);
  const heightBefore = await page.evaluate(() => document.documentElement.scrollHeight);

  const rebase = await rebaseFromUi(page, fx.savedId);
  const dropped = rebase.dropped_placements;
  const N = dropped.length;
  expect(N).toBe(fx.expectedDropped);
  expect(N).toBeGreaterThan(100);
  const removedRows = dropped.filter((d) => d.reason === "REMOVED");
  const changedRows = dropped.filter((d) => d.reason === "CHANGED");
  expect(removedRows.length).toBe(fx.expectedRemoved);
  expect(changedRows.length).toBe(fx.expectedChanged);
  expect(rebase.kept_placement_count).toBe(fx.expectedKept);

  const panel = panelOf(page);
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(`Giữ ${fx.expectedKept} vị trí; bỏ ${N} vị trí`);
  // The dropped-list panel itself must stay short (50 rows at most, paged).
  const panelBox = await panel.boundingBox();
  expect(panelBox).not.toBeNull();
  expect(panelBox!.height).toBeLessThan(1500);
  // Whole-page growth is measured, not asserted: the comparison and cargo-list sections that a rebase opens are
  // outside H1 (SPEC H6) and are recorded as an observation in the worker return.
  const heightAfter = await page.evaluate(() => document.documentElement.scrollHeight);
  test.info().annotations.push({ type: "page-growth-px", description: String(heightAfter - heightBefore) });
  console.log(`H-01 page growth after rebase: ${heightAfter - heightBefore} px; dropped panel ${Math.round(panelBox!.height)} px`);

  // page 1 of ALL: 50 rows, status, disabled previous button
  await expectPage(page, dropped, 1);
  await shotLocator(panel, "harden01-rebase-paged-desktop.png");

  // ALL: forward through the last page (30 rows), then back
  await walkAllPages(page, dropped);

  // filter labels carry the real counts
  await expect(filterOf(page).locator("option")).toHaveText([`Tất cả (${N})`, `Bỏ (${removedRows.length})`, `Đổi (${changedRows.length})`]);

  // reset to page 1 when the filter changes from page 2
  await nextBtn(page).click();
  await expectPage(page, dropped, 2);
  await filterOf(page).selectOption("REMOVED");
  await expectPage(page, removedRows, 1);
  await walkAllPages(page, removedRows);

  await filterOf(page).selectOption("CHANGED");
  await walkAllPages(page, changedRows);

  // back to ALL: full total again, summary still present
  await filterOf(page).selectOption("ALL");
  await expectPage(page, dropped, 1);
  await expect(panel).toContainText(`Giữ ${fx.expectedKept} vị trí; bỏ ${N} vị trí`);

  expect(pageErrors).toEqual([]);
});

test("H-01 390px: rebase drops page 50 rows at a time, filter works, no horizontal overflow", async ({ page, request }) => {
  test.setTimeout(240_000);
  await page.setViewportSize({ width: 390, height: 844 });
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();
  const fx = await buildFixture(request, `HARDEN-01 H1 390 ${tag}`, `HARDEN01-M-${tag}`);
  expect(fx.expectedDropped).toBeGreaterThan(100);

  await openRecheckedPlan(page, request, fx);
  const rebase = await rebaseFromUi(page, fx.savedId);
  const dropped = rebase.dropped_placements;
  const N = dropped.length;
  expect(N).toBe(fx.expectedDropped);
  const removedRows = dropped.filter((d) => d.reason === "REMOVED");
  const changedRows = dropped.filter((d) => d.reason === "CHANGED");

  const panel = panelOf(page);
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(`Giữ ${fx.expectedKept} vị trí; bỏ ${N} vị trí`);
  await expectPage(page, dropped, 1);
  await expect(itemsOf(page)).toHaveCount(PAGE_SIZE);
  await expect(page.getByTestId("rebase-dropped-page")).toHaveText(`Trang 1/${Math.ceil(N / PAGE_SIZE)} · dòng 1–50 trên tổng ${N}`);
  await expectNoHorizontalOverflow(page);
  const box = await panel.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.x + box!.width).toBeLessThanOrEqual(390);
  await shotLocator(panel, "harden01-rebase-paged-390.png");

  // paging works on the phone layout
  await nextBtn(page).click();
  await expectPage(page, dropped, 2);

  // REMOVED: 60 rows -> 50 on page 1, then 10 on page 2
  await filterOf(page).selectOption("REMOVED");
  await expectPage(page, removedRows, 1);
  await expect(itemsOf(page)).toHaveCount(PAGE_SIZE);
  await nextBtn(page).click();
  await expectPage(page, removedRows, 2);
  await expect(itemsOf(page)).toHaveCount(removedRows.length - PAGE_SIZE);

  // CHANGED: 70 rows -> 50 on page 1
  await filterOf(page).selectOption("CHANGED");
  await expectPage(page, changedRows, 1);
  await expect(itemsOf(page)).toHaveCount(PAGE_SIZE);
  await expectNoHorizontalOverflow(page);

  expect(pageErrors).toEqual([]);
});
