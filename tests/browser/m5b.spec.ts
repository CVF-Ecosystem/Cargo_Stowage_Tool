import { readFile } from "node:fs/promises";
import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Page } from "../../apps/frontend/node_modules/@playwright/test";

// M5B-04 browser flow: automatic backup block in the backup panel. Save a plan -> "Sao lưu ngay" -> the file is listed ->
// "Tải" captures the .scstbak -> save a second plan -> restore from the downloaded file through the existing restore flow ->
// the saved list is the list recorded at backup time. The suite shares ONE server and data dir, so every assertion is
// relative to the saved-plan list recorded when the backup was taken.

type Saved = { id: string; name: string };
type Evaluation = { plan: { units: { id: string }[] }; status: string; summary: { placed_count: number } };
type AutoFile = { name: string; created_utc: string; size_bytes: number };
type AutoStatus = { enabled: boolean; interval_hours: number; keep: number; files: AutoFile[]; last_error: string | null };

const WARNING = "Toàn bộ dữ liệu hiện có sẽ được thay bằng bản sao lưu; một bản sao lưu dữ liệu hiện tại sẽ được tạo tự động trước khi thay.";
const AUTO_NOTE = "Bản tự động nằm cùng máy với dữ liệu. Hãy tải một bản và cất ra ngoài máy (USB, ổ mạng). Chưa có sao lưu theo lịch khi app đang đóng, chưa mã hóa.";
const AUTO_NAME = /^auto-\d{8}T\d{6}\d{6}Z(-\d+)?\.scstbak$/;
const VIEWPORT_LIMIT = 391; // 390px plus the 1px rounding allowance

async function postResult<T>(page: Page, pathname: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((r) => new URL(r.url()).pathname === pathname && r.request().method() === "POST");
  await action();
  const response = await pending;
  if (!response.ok()) throw new Error(`POST ${pathname} ${response.status()}: ${await response.text()}`);
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

const docScrollWidth = (page: Page) => page.evaluate(() => document.documentElement.scrollWidth);

// The suite shares one server and data dir: take a backup of the shared data before this file runs and restore it
// afterwards (through the same backup API), so the plans created here never reach later spec files.
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
  const { backup_sha256 } = (await checked.json()) as { backup_sha256: string };
  const restored = await request.post(`/api/backup/restore/apply?confirm=${backup_sha256}`, { data: sharedState, headers });
  expect(restored.ok()).toBe(true);
});

test("M5B-04 desktop: auto backup now, download, save a second plan, restore from the downloaded file", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();

  // 1. plan A (the synthetic demo plan on load) saved through the UI
  await page.goto("/");
  const block = page.getByTestId("backup-auto");
  await expect(block).toBeVisible();
  await expect(block).toContainText("Sao lưu tự động");
  await expect(block).toContainText(AUTO_NOTE);
  const planA = await saveCurrent(page, `M5B A ${tag}`);

  // 2. "Sao lưu ngay" writes one automatic backup and the new file appears in the list
  const run = await postResult<AutoFile>(page, "/api/backup/auto/run", () => page.getByRole("button", { name: "Sao lưu ngay", exact: true }).click());
  expect(run.name).toMatch(AUTO_NAME);
  const item = page.getByTestId(`auto-backup-${run.name}`);
  await expect(item).toBeVisible();
  await expect(page.getByTestId("backup-auto-result")).toContainText("Đã sao lưu ngay");
  await expect(page.getByTestId("backup-auto-status")).toContainText("Bản gần nhất");
  const listed = await getJson<AutoStatus>(request, "/api/backup/auto");
  expect(listed.files.map((f) => f.name)).toContain(run.name);
  expect(listed.files.length).toBeLessThanOrEqual(listed.keep);
  // the saved-plan list at backup time: plan A is in it; other specs may have left plans on the shared server
  const atBackup = await savedIds(request);
  expect(atBackup).toContain(planA.id);

  // 3. "Tải" downloads the same bytes the API serves for that name
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    item.getByRole("button", { name: "Tải", exact: true }).click(),
  ]);
  expect(download.suggestedFilename()).toBe(run.name);
  const backupPath = evidencePath("m5b-auto.scstbak");
  await download.saveAs(backupPath);
  const served = Buffer.from(await (await request.get(`/api/backup/auto/${run.name}`)).body());
  expect(Buffer.from(await readFile(backupPath))).toEqual(served);

  // 4. a second plan (VINAFCO 268) saved after the backup; it must be gone after the restore
  await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Xem VINAFCO 268" }).click());
  const planB = await saveCurrent(page, `M5B B ${tag}`);
  expect(await savedIds(request)).toContain(planB.id);

  // 5. restore from the downloaded file through the existing picker; the apply call replaces all local data
  await expect(page.getByLabel("Khôi phục từ bản sao lưu")).toBeEnabled(); // a save may still be refreshing the list
  const [previewResponse] = await Promise.all([
    page.waitForResponse((r) => new URL(r.url()).pathname === "/api/backup/restore/preview" && r.request().method() === "POST"),
    page.getByLabel("Khôi phục từ bản sao lưu").setInputFiles(backupPath),
  ]);
  expect(previewResponse.status(), "preview status").toBe(200);
  const previewBox = page.getByTestId("backup-preview");
  await expect(previewBox).toBeVisible();
  await expect(previewBox).toContainText(WARNING);
  const restoreButton = page.getByRole("button", { name: "Khôi phục", exact: true });
  const [applyResponse] = await Promise.all([
    page.waitForResponse((r) => new URL(r.url()).pathname === "/api/backup/restore/apply" && r.request().method() === "POST"),
    restoreButton.click(),
  ]);
  expect(applyResponse.status(), "apply status").toBe(200);
  await expect(page.getByTestId("backup-result")).toContainText("Đã khôi phục");

  // 6. the saved list is the one recorded at backup time: plan B is gone, plan A is back
  expect(await savedIds(request)).toEqual(atBackup);
  expect(await savedIds(request)).not.toContain(planB.id);
  const select = page.getByLabel("Phương án đã lưu");
  await expect(select.locator(`option[value="${planB.id}"]`)).toHaveCount(0);
  await expect(select.locator(`option[value="${planA.id}"]`)).toHaveCount(1);

  // the automatic backup file itself survives the restore and is still listed
  await expect(page.getByTestId(`auto-backup-${run.name}`)).toBeVisible();

  await page.getByTestId("backup-auto").screenshot({ path: evidencePath("m5b-desktop.png") });
  expect(pageErrors).toEqual([]);
});

test("M5B-04 mobile 390x844: auto backup block fits, buttons visible, no horizontal overflow", async ({ page, request }) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await saveCurrent(page, `M5B mobile ${Date.now()}`);

  const block = page.getByTestId("backup-auto");
  await block.scrollIntoViewIfNeeded();
  await expect(block).toBeVisible();
  await expect(block).toContainText(AUTO_NOTE);
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(VIEWPORT_LIMIT);

  const run = await postResult<AutoFile>(page, "/api/backup/auto/run", () => page.getByRole("button", { name: "Sao lưu ngay", exact: true }).click());
  const item = page.getByTestId(`auto-backup-${run.name}`);
  await expect(item).toBeVisible();
  const download = item.getByRole("button", { name: "Tải", exact: true });
  await expect(download).toBeVisible();
  const box = await download.boundingBox();
  expect(box, "Tải button box").not.toBeNull();
  expect(box!.x + box!.width).toBeLessThanOrEqual(390 + 1);
  expect(box!.x).toBeGreaterThanOrEqual(0);

  const [file] = await Promise.all([page.waitForEvent("download"), download.click()]);
  expect(file.suggestedFilename()).toBe(run.name);
  expect(await docScrollWidth(page)).toBeLessThanOrEqual(VIEWPORT_LIMIT);
  await expect(page.getByTestId("backup-auto-result")).toContainText("Đã tải");

  const runButton = page.getByRole("button", { name: "Sao lưu ngay", exact: true });
  await expect(runButton).toBeVisible();
  const runBox = await runButton.boundingBox();
  expect(runBox!.x + runBox!.width).toBeLessThanOrEqual(390 + 1);
  await block.screenshot({ path: evidencePath("m5b-390.png") });
  expect(await savedIds(request)).not.toHaveLength(0);
});
