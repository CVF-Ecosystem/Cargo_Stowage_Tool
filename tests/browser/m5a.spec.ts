import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Page } from "../../apps/frontend/node_modules/@playwright/test";

// M5A-04/05 browser flow: backup export, restore preview and apply, reload of the saved-plan list, reopen through the UI.
// The suite shares ONE server and data dir, so every assertion is relative to the saved-plan list recorded at export time
// and to the plans' own snapshots read before the restore. The pre-restore backup is stored under the data dir and has no
// API, so this spec checks its file name only; its contents are covered by the backend tests.

type Unit = { id: string };
type Placement = { unit_id: string; x_mm: number; y_mm: number; z_mm: number; layer: number; yaw_deg: number; supported_by: string[] };
type Plan = { units: Unit[]; placements: Placement[] };
type Evaluation = { plan: Plan; status: string; summary: { placed_count: number } };
type Preview = { algorithm: string; evaluation: Evaluation; unplaced: { unit_id: string }[] };
type Saved = { id: string; name: string };
type Counts = { plans: number; revisions: number; vessel_profile_versions: number };
type RevisionList = { latest_revision_id: string };
type Stored = { plan: Plan };

const WARNING = "Toàn bộ dữ liệu hiện có sẽ được thay bằng bản sao lưu; một bản sao lưu dữ liệu hiện tại sẽ được tạo tự động trước khi thay.";
const DRAFT_NOTE = "Phương án đang mở trong tab chưa thuộc dữ liệu đã khôi phục";
const LIMITS_NOTE = "Chưa có sao lưu tự động theo lịch, mã hóa hay khôi phục gộp; khôi phục luôn thay toàn bộ.";
const VIEWPORT_LIMIT = 391; // 390px plus the 1px rounding allowance

const SOURCE = { kind: "FACTORY", reference: "M5A-browser / chứng từ nhà máy", received_date: "2026-11-04", note: "sao lưu kiểm thử" };
const GROUP = { bundle_count: 3, pieces_per_bundle: 10, dimensions_um: [6000000, 300000, 300000], mass_g: 2000500, outside_diameter_mm: "114.3", wall_thickness_mm: "6.02", dimension_warning: false };
const notBackup = () => ({ name: "x.scstbak", mimeType: "application/octet-stream", buffer: Buffer.from("not a zip") });

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

async function savedIds(request: APIRequestContext): Promise<string[]> {
  return (await getJson<Saved[]>(request, "/api/snapshots")).map((s) => s.id).sort();
}

async function saveCurrent(page: Page, name: string): Promise<Saved> {
  await page.getByLabel("Tên phương án lưu").fill(name);
  return postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
}

// VINAFCO 268 with the pipe list, columns-v1 stacking and apply (the M3a path); returns the applied plan.
async function buildStackedPlan(page: Page): Promise<Evaluation> {
  await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Xem VINAFCO 268" }).click());
  await postResult(page, "/api/pipe-list/preview", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
  await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
  await page.getByRole("combobox", { name: "Cách xếp thử" }).selectOption("columns-v1");
  const preview = await postResult<Preview>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  expect(preview.algorithm).toBe("columns-v1");
  const applied = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  expect(applied.plan.placements.length).toBeGreaterThan(0);
  expect(Math.max(...applied.plan.placements.map((p) => p.layer)) + 1).toBeGreaterThanOrEqual(2);
  return applied;
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

// The suite shares one server and data dir: take a backup of the shared data before this file runs and restore it
// afterwards (through the same backup API), so the revision and plans created here never reach later spec files.
let sharedState: Buffer | null = null;
test.beforeAll(async ({ request }) => {
  const exported = await request.get("/api/backup/export");
  expect(exported.ok()).toBe(true);
  sharedState = Buffer.from(await exported.body());
});
test.afterAll(async ({ request }) => {
  if (!sharedState) return;
  const headers = { "Content-Type": "application/octet-stream" };
  const checked = await request.post("/api/backup/restore/preview", { data: sharedState, headers });
  expect(checked.ok()).toBe(true);
  const { backup_sha256 } = await checked.json() as { backup_sha256: string };
  const restored = await request.post(`/api/backup/restore/apply?confirm=${backup_sha256}`, { data: sharedState, headers });
  expect(restored.ok()).toBe(true);
});

test("M5A-05 desktop: save two plans and a revision, export, save a third, restore, reopen the first two", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();

  // 1. plan B (the synthetic demo plan) and plan A (multi-layer VINAFCO 268 with columns-v1)
  await page.goto("/");
  const planB = await saveCurrent(page, `M5A B ${tag}`);
  const applied = await buildStackedPlan(page);
  const planA = await saveCurrent(page, `M5A A nhiều tầng ${tag}`);
  const storedA = await getJson<Stored>(request, `/api/snapshots/${planA.id}`);
  const storedB = await getJson<Stored>(request, `/api/snapshots/${planB.id}`);
  expect(storedA.plan.placements).toEqual(applied.plan.placements);

  // 2. one cargo revision on the latest parent (API), then the backup through the UI
  const latestBefore = (await getJson<RevisionList>(request, "/api/cargo-revisions")).latest_revision_id;
  const created = await request.post("/api/cargo-revisions", {
    data: { parent_revision_id: latestBefore, source: SOURCE, changes: [{ type: "ADD_GROUP", confirmation: "UNVERIFIED", group: GROUP }] },
  });
  expect(created.ok(), await created.text()).toBe(true);
  const revisionId = ((await created.json()) as { revision_id: string }).revision_id;
  expect((await getJson<RevisionList>(request, "/api/cargo-revisions")).latest_revision_id).toBe(revisionId);

  const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Tải bản sao lưu", exact: true }).click()]);
  expect(download.suggestedFilename()).toMatch(/\.scstbak$/);
  const backupPath = evidencePath("m5a-backup.scstbak");
  await download.saveAs(backupPath);
  const exported = await savedIds(request);
  expect(exported).toEqual(expect.arrayContaining([planA.id, planB.id].sort()));
  await expect(page.getByTestId("backup-result")).toContainText("Đã tải bản sao lưu");

  // 3. a third plan C, saved after the export; it must be gone after the restore
  const planC = await saveCurrent(page, `M5A C ${tag}`);
  const beforeRestore = await savedIds(request);
  expect(beforeRestore).toContain(planC.id);

  // 4. choose the backup: preview with counts and the exact warning; no apply yet
  await expect(page.getByLabel("Khôi phục từ bản sao lưu")).toBeEnabled(); // a save may still be refreshing the list
  const [previewResponse] = await Promise.all([
    page.waitForResponse((r) => new URL(r.url()).pathname === "/api/backup/restore/preview" && r.request().method() === "POST"),
    page.getByLabel("Khôi phục từ bản sao lưu").setInputFiles(backupPath),
  ]);
  // Status only: the body of a response issued after the export download is not readable in this browser, so counts come from the panel.
  expect(previewResponse.status(), "preview status").toBe(200);
  const previewBox = page.getByTestId("backup-preview");
  await expect(previewBox).toBeVisible();
  const plansRow = previewBox.locator("tbody tr").first().locator("td");
  await expect(plansRow.nth(0)).toHaveText(String(exported.length));
  await expect(plansRow.nth(1)).toHaveText(String(beforeRestore.length));
  await expect(previewBox).toContainText(WARNING);
  await expect(page.getByTestId("backup-panel")).toContainText(LIMITS_NOTE);
  const restoreButton = page.getByRole("button", { name: "Khôi phục", exact: true });
  await expect(restoreButton).toBeVisible();

  // 5. restore: the apply call must succeed (a 500 here is a backend failure, reported as such)
  const [applyResponse] = await Promise.all([
    page.waitForResponse((r) => new URL(r.url()).pathname === "/api/backup/restore/apply" && r.request().method() === "POST"),
    restoreButton.click(),
  ]);
  expect(applyResponse.status(), "apply status").toBe(200);
  const result = page.getByTestId("backup-result");
  await expect(result).toContainText("Đã khôi phục");
  await expect(result).toContainText(`(${exported.length} phương án,`);
  const preRestoreName = ((await result.textContent()) ?? "").match(/pre-restore-\S+?\.scstbak/)?.[0] ?? "";
  expect(preRestoreName).toMatch(/^pre-restore-.*\.scstbak$/);
  await expect(result).toContainText(DRAFT_NOTE);
  await expect(previewBox).toHaveCount(0);
  await expect(restoreButton).toHaveCount(0);

  // 6. the saved-plan set equals the set recorded at export; the revision of the backup is the latest again
  expect(await savedIds(request)).toEqual(exported);
  expect(await savedIds(request)).not.toContain(planC.id);
  expect((await getJson<RevisionList>(request, "/api/cargo-revisions")).latest_revision_id).toBe(revisionId);
  const select = page.getByLabel("Phương án đã lưu");
  await expect(select.locator(`option[value="${planC.id}"]`)).toHaveCount(0);
  await expect(select.locator(`option[value="${planA.id}"]`)).toHaveCount(1);
  await expect(select.locator(`option[value="${planB.id}"]`)).toHaveCount(1);

  // 7. reopen A (multi-layer) through the UI: same plan as before the restore, stacked cell kept
  await select.selectOption(planA.id);
  const reopenedA = await getResult<Stored>(page, `/api/snapshots/${planA.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(reopenedA.plan).toEqual(storedA.plan);
  await expect(page.getByTestId("pipe-total")).toContainText(`Toàn list: ${applied.plan.units.length} bó`);
  const stacked = applied.plan.placements.find((p) => p.layer > 0)!;
  await findCargoRow(page, stacked.unit_id);
  await expect(page.getByTestId(`layer-cell-${stacked.unit_id}`)).toHaveText(String(stacked.layer + 1));

  // 8. reopen B (demo plan) through the UI
  await select.selectOption(planB.id);
  const reopenedB = await getResult<Stored>(page, `/api/snapshots/${planB.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(reopenedB.plan).toEqual(storedB.plan);
  await expect(page.getByTestId("unit-ST-001")).toBeVisible();

  // 9. a non-backup file: Vietnamese error, no apply button, nothing changes
  const before = await savedIds(request);
  await expect(page.getByLabel("Khôi phục từ bản sao lưu")).toBeEnabled(); // a save may still be refreshing the list
  await page.getByLabel("Khôi phục từ bản sao lưu").setInputFiles(notBackup());
  const error = page.getByTestId("backup-error");
  await expect(error).toBeVisible();
  expect(await error.textContent()).toMatch(/[À-ỹ]/);
  await expect(page.getByRole("button", { name: "Khôi phục", exact: true })).toHaveCount(0);
  await expect(previewBox).toHaveCount(0);
  expect(await savedIds(request)).toEqual(before);

  await page.getByTestId("backup-panel").screenshot({ path: evidencePath("m5a-desktop.png") });
  expect(pageErrors).toEqual([]);
});

test("M5A-04 mobile 390x844: backup panel fits, invalid file shows an error, round trip keeps the saved list", async ({ page, request }) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const panel = page.getByTestId("backup-panel");
  await panel.scrollIntoViewIfNeeded();
  await expect(panel).toBeVisible();
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(VIEWPORT_LIMIT);

  // invalid file at 390px: error, no apply button, page still fits
  await expect(page.getByLabel("Khôi phục từ bản sao lưu")).toBeEnabled(); // a save may still be refreshing the list
  await page.getByLabel("Khôi phục từ bản sao lưu").setInputFiles(notBackup());
  await expect(page.getByTestId("backup-error")).toBeVisible();
  await expect(page.getByRole("button", { name: "Khôi phục", exact: true })).toHaveCount(0);
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(VIEWPORT_LIMIT);

  // round trip at 390px: export, choose the file, preview fits, restore, saved list unchanged
  const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Tải bản sao lưu", exact: true }).click()]);
  const backupPath = evidencePath("m5a-390-backup.scstbak");
  await download.saveAs(backupPath);
  const exported = await savedIds(request);
  await expect(page.getByLabel("Khôi phục từ bản sao lưu")).toBeEnabled(); // a save may still be refreshing the list
  await page.getByLabel("Khôi phục từ bản sao lưu").setInputFiles(backupPath);
  await expect(page.getByTestId("backup-preview")).toBeVisible();
  await expect(page.getByTestId("backup-preview")).toContainText(WARNING);
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(VIEWPORT_LIMIT);
  await panel.screenshot({ path: evidencePath("m5a-390.png") });

  const [applyResponse] = await Promise.all([
    page.waitForResponse((r) => new URL(r.url()).pathname === "/api/backup/restore/apply" && r.request().method() === "POST"),
    page.getByRole("button", { name: "Khôi phục", exact: true }).click(),
  ]);
  expect(applyResponse.status(), "apply status").toBe(200);
  await expect(page.getByTestId("backup-result")).toContainText("Đã khôi phục");
  expect(await savedIds(request)).toEqual(exported);
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(VIEWPORT_LIMIT);
});
