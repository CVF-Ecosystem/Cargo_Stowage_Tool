import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { Page } from "../../apps/frontend/node_modules/@playwright/test";

type Unit = { id: string; mass_g: number; requirement: string; dimensions_um?: number[] | null; source_ref?: { workbook_sha256: string } | null };
type Placement = { unit_id: string; x_mm: number; y_mm: number; yaw_deg: number };
type Plan = { contract_version: string; cargo_source: string; cargo_dataset: string | null; vessel: { case_id: string } | null; units: Unit[]; placements: Placement[] };
type Evaluation = { plan: Plan; status: string; summary: { manifest_mass_g: number; placed_mass_g: number; placed_count: number } };
type Saved = { id: string; name: string };
type Change = { field: string; before: unknown; after: unknown };
type CompareRow = { unit_id: string; status: "ADDED" | "REMOVED" | "CHANGED" | "UNCHANGED"; changes: Change[]; source_identity_warning: boolean; in_after: boolean };
type Comparison = { before: { manifest_mass_g: number; placed_mass_g: number; status: string }; after: { manifest_mass_g: number; placed_mass_g: number; status: string }; delta: { manifest_mass_g: number; placed_mass_g: number }; counts: Record<string, number>; rows: CompareRow[]; context_changes: Change[] };

async function response<T>(page: Page, path: string, method: "GET" | "POST", action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((r) => r.url().endsWith(path) && r.request().method() === method);
  await action();
  const result = await pending;
  expect(result.ok()).toBe(true);
  return await result.json() as T;
}

async function loadPipeList(page: Page): Promise<Evaluation> {
  await response<Evaluation>(page, "/api/pipe-list/preview", "POST", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
  return response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
}

async function importCsv(page: Page, rows: string): Promise<Evaluation> {
  const header = "id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg";
  await page.getByLabel("Nội dung CSV").fill(`${header}\n${rows}\n`);
  const checked = await response<{ valid: boolean }>(page, "/api/import/csv/preview", "POST", () => page.getByRole("button", { name: "Kiểm CSV" }).click());
  expect(checked.valid).toBe(true);
  return response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Áp dụng CSV" }).click());
}

test("pin A, edit one gram and placement in checked B, compare exact details, restore and undo without overwriting snapshots", async ({ page, request }) => {
  const original = await (await request.get("/api/demo")).json() as Evaluation;
  await page.goto("/?viewerDiagnostics=1");
  await page.getByLabel("Tên phương án lưu").fill(`M2c A ${Date.now()}`);
  const savedA = await response<Saved>(page, "/api/snapshots", "POST", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await page.getByRole("button", { name: "Giữ bản hiện tại làm gốc" }).click();
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.001");
  await page.getByLabel("Tọa độ X (cm)").fill("50.1");
  await page.getByLabel("Góc xoay").selectOption("90");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  const checkedB = await response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(checkedB.plan.units.find((u) => u.id === "ST-001")?.mass_g).toBe(2_500_001);
  expect(checkedB.plan.placements.find((p) => p.unit_id === "ST-001")).toMatchObject({ x_mm: 501, yaw_deg: 90 });
  await expect.poll(() => page.getByTestId("three-canvas").getAttribute("data-meshes")).not.toBeNull();
  const currentMeshes = await page.getByTestId("three-canvas").getAttribute("data-meshes");
  const compared = await response<Comparison>(page, "/api/plans/compare", "POST", () => page.getByRole("button", { name: "So sánh với bản gốc" }).click());
  expect(compared.delta.manifest_mass_g).toBe(1);
  expect(compared.delta.placed_mass_g).toBe(1);
  expect(compared.before.manifest_mass_g).toBe(original.summary.manifest_mass_g);
  expect(compared.after.manifest_mass_g).toBe(checkedB.summary.manifest_mass_g);
  const changed = compared.rows.find((row) => row.unit_id === "ST-001")!;
  expect(changed.status).toBe("CHANGED");
  expect(changed.changes).toEqual(expect.arrayContaining([
    { field: "mass_g", before: 2_500_000, after: 2_500_001 },
    { field: "placement.x_mm", before: 500, after: 501 },
    { field: "placement.yaw_deg", before: 0, after: 90 },
  ]));
  expect(compared.counts.CHANGED).toBe(1);
  await expect(page.getByTestId("comparison-summary")).toBeVisible();
  await expect(page.getByTestId("comparison-rows")).toContainText("ST-001");
  await page.getByTestId("comparison-row-ST-001").getByText("Chi tiết thay đổi").click();
  await expect(page.getByTestId("comparison-row-ST-001")).toContainText("dưới 1 kg");
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("2500");
  expect(await page.getByTestId("three-canvas").getAttribute("data-meshes")).toBe(currentMeshes);
  await page.screenshot({ path: evidencePath("m2c.spec-compare-desktop.png"), fullPage: true });
  const restored = await response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Khôi phục bản gốc" }).click());
  expect(restored.plan).toEqual(original.plan);
  const undone = await response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Bản trước" }).click());
  expect(undone.plan).toEqual(checkedB.plan);
  await page.getByLabel("Tên phương án lưu").fill(`M2c B ${Date.now()}`);
  const savedB = await response<Saved>(page, "/api/snapshots", "POST", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  expect(savedB.id).not.toBe(savedA.id);
  const aAfter = await (await request.get(`/api/snapshots/${savedA.id}`)).json() as Evaluation;
  const bAfter = await (await request.get(`/api/snapshots/${savedB.id}`)).json() as Evaluation;
  expect(aAfter.plan).toEqual(original.plan);
  expect(bAfter.plan).toEqual(checkedB.plan);
});

test("saved baseline loads after reload without replacing checked B or selected cargo", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Tên phương án lưu").fill(`M2c saved A ${Date.now()}`);
  const savedA = await response<Saved>(page, "/api/snapshots", "POST", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await page.reload();
  await page.getByTestId("unit-ST-002").getByRole("button").click();
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.001");
  const checkedB = await response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  await page.getByLabel("Bản lưu làm gốc").selectOption(savedA.id);
  await response<Evaluation>(page, `/api/snapshots/${savedA.id}`, "GET", () => page.getByRole("button", { name: "Dùng bản lưu làm gốc" }).click());
  await expect(page.getByTestId("unit-ST-002")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("2500");
  const compared = await response<Comparison>(page, "/api/plans/compare", "POST", () => page.getByRole("button", { name: "So sánh với bản gốc" }).click());
  expect(compared.delta.manifest_mass_g).toBe(1);
  expect(compared.rows.find((r) => r.unit_id === "ST-002")?.status).toBe("CHANGED");
  expect(checkedB.plan.units.find((u) => u.id === "ST-002")?.mass_g).toBe(2_500_001);
});

test("source list comparison accounts all 1076, filters and pages without a second viewer on mobile fallback", async ({ page }) => {
  test.setTimeout(60_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...args: unknown[]) {
      if (type.includes("webgl")) return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.goto("/");
  const source = await loadPipeList(page);
  expect(source.plan.units).toHaveLength(1076);
  await page.getByRole("button", { name: "Giữ bản hiện tại làm gốc" }).click();
  await page.getByTestId("unit-PIPE-R002-B0001").getByRole("button").click();
  await page.getByLabel("Yêu cầu").selectOption("required");
  const checked = await response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(checked.plan.units[0].requirement).toBe("required");
  const compared = await response<Comparison>(page, "/api/plans/compare", "POST", () => page.getByRole("button", { name: "So sánh với bản gốc" }).click());
  expect(compared.rows).toHaveLength(1076);
  expect(compared.counts).toMatchObject({ ADDED: 0, REMOVED: 0, CHANGED: 1, UNCHANGED: 1075 });
  expect(compared.rows.find((r) => r.unit_id === "PIPE-R002-B0001")?.changes).toContainEqual({ field: "requirement", before: "optional", after: "required" });
  await expect(page.getByTestId("comparison-rows")).toContainText("PIPE-R002-B0001");
  await page.getByLabel("Lọc thay đổi").selectOption("ALL");
  await expect(page.getByTestId("comparison-page")).toContainText("Trang 1/22");
  expect(await page.getByTestId("comparison-rows").locator("article").count()).toBe(50);
  await page.getByRole("button", { name: "So sánh trang sau" }).click();
  await expect(page.getByTestId("comparison-page")).toContainText("Trang 2/22");
  await page.getByLabel("Tìm ID bó").fill("PIPE-R002-B0001");
  await expect(page.getByTestId("comparison-page")).toContainText("Trang 1/1");
  await page.getByTestId("comparison-row-PIPE-R002-B0001").getByRole("button", { name: "Chọn bó trong B" }).click();
  await expect(page.getByRole("heading", { name: "PIPE-R002-B0001" })).toBeVisible();
  await expect(page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D")).toBeVisible();
  await expect(page.getByTestId("three-canvas")).toHaveCount(0);
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: evidencePath("m2c.spec-compare-mobile-fallback.png"), fullPage: true });
});

test("replacing a manifest reports added, removed and changed IDs without selecting the A-only unit", async ({ page }) => {
  await page.goto("/");
  const a = await importCsv(page, "KEEP,Bó giữ,BAR_BUNDLE,required,6000,900,650,1\nDROP,Bó bỏ,PIPE_BUNDLE,optional,6000,900,650,2");
  expect(a.plan.units.map((u) => u.id)).toEqual(["KEEP", "DROP"]);
  await page.getByRole("button", { name: "Giữ bản hiện tại làm gốc" }).click();
  const b = await importCsv(page, "KEEP,Bó giữ đổi,BAR_BUNDLE,required,6000,900,650,1.001\nADD,Bó thêm,PIPE_BUNDLE,optional,6000,900,650,3");
  expect(b.plan.units.map((u) => u.id)).toEqual(["KEEP", "ADD"]);
  const compared = await response<Comparison>(page, "/api/plans/compare", "POST", () => page.getByRole("button", { name: "So sánh với bản gốc" }).click());
  expect(compared.counts).toMatchObject({ ADDED: 1, REMOVED: 1, CHANGED: 1, UNCHANGED: 0 });
  expect(compared.rows.find((r) => r.unit_id === "DROP")).toMatchObject({ status: "REMOVED", in_after: false });
  expect(compared.rows.find((r) => r.unit_id === "ADD")).toMatchObject({ status: "ADDED", in_after: true });
  expect(compared.rows.find((r) => r.unit_id === "KEEP")?.changes).toContainEqual({ field: "mass_g", before: 1000, after: 1001 });
  await expect(page.getByTestId("comparison-rows")).toContainText("DROP");
  await expect(page.getByTestId("comparison-rows")).toContainText("ADD");
  await expect(page.getByTestId("comparison-row-DROP").getByRole("button", { name: "Chọn bó trong B" })).toHaveCount(0);
  await page.getByTestId("comparison-row-ADD").getByRole("button", { name: "Chọn bó trong B" }).click();
  await expect(page.getByRole("heading", { name: "ADD" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "DROP" })).toHaveCount(0);
});

test("STALE and a late or failed compare leave B, selection and baseline intact", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Giữ bản hiện tại làm gốc" }).click();
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.001");
  await response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  const checkedMass = await page.getByTestId("placed-mass").textContent();
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.002");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.getByRole("button", { name: "So sánh với bản gốc" }).click();
  await expect(page.getByRole("region", { name: "So sánh phương án" }).getByRole("alert")).toContainText("bản nháp");
  await expect(page.getByTestId("comparison-summary")).toHaveCount(0);
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.001");
  await expect(page.getByTestId("status")).not.toHaveText("STALE");

  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let received = false;
  await page.route("**/api/plans/compare", async (route) => {
    const backend = await route.fetch(); received = true; await gate; await route.fulfill({ response: backend });
  });
  await page.getByRole("button", { name: "So sánh với bản gốc" }).click();
  await expect.poll(() => received).toBe(true);
  await page.getByTestId("unit-ST-002").getByRole("button").click();
  release();
  await expect(page.getByRole("region", { name: "So sánh phương án" }).getByRole("alert")).toContainText("Dữ liệu đã đổi trong lúc so sánh");
  await expect(page.getByTestId("comparison-summary")).toHaveCount(0);
  await expect(page.getByTestId("unit-ST-002")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("placed-mass")).toHaveText(checkedMass!);
  await expect(page.getByTestId("comparison-baseline")).toContainText("trong tab");
  await page.unroute("**/api/plans/compare");
  await page.route("**/api/plans/compare", (route) => route.abort("failed"));
  await page.getByRole("button", { name: "So sánh với bản gốc" }).click();
  await expect(page.getByRole("region", { name: "So sánh phương án" }).getByRole("alert")).toBeVisible();
  await expect(page.getByTestId("comparison-summary")).toHaveCount(0);
  await expect(page.getByTestId("placed-mass")).toHaveText(checkedMass!);
});

test("late saved-baseline and restore responses cannot overwrite a newer selection or draft", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Tên phương án lưu").fill(`M2c late A ${Date.now()}`);
  const savedA = await response<Saved>(page, "/api/snapshots", "POST", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await page.getByRole("button", { name: "Giữ bản hiện tại làm gốc" }).click();
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.001");
  const checkedB = await response<Evaluation>(page, "/api/validate", "POST", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  await page.getByLabel("Bản lưu làm gốc").selectOption(savedA.id);
  let releaseLoad: () => void = () => {};
  const loadGate = new Promise<void>((resolve) => { releaseLoad = resolve; });
  let loadReceived = false;
  await page.route(`**/api/snapshots/${savedA.id}`, async (route) => {
    const backend = await route.fetch(); loadReceived = true; await loadGate; await route.fulfill({ response: backend });
  });
  await page.getByRole("button", { name: "Dùng bản lưu làm gốc" }).click();
  await expect.poll(() => loadReceived).toBe(true);
  await page.getByTestId("unit-ST-002").getByRole("button").click();
  releaseLoad();
  await expect(page.getByRole("region", { name: "So sánh phương án" }).getByRole("alert")).toContainText("Dữ liệu đã đổi trong lúc tải bản gốc");
  await expect(page.getByTestId("comparison-baseline")).toContainText("trong tab");
  await expect(page.getByTestId("unit-ST-002")).toHaveAttribute("aria-selected", "true");
  await page.unroute(`**/api/snapshots/${savedA.id}`);

  let releaseRestore: () => void = () => {};
  const restoreGate = new Promise<void>((resolve) => { releaseRestore = resolve; });
  let restoreReceived = false;
  await page.route("**/api/validate", async (route) => {
    const backend = await route.fetch(); restoreReceived = true; await restoreGate; await route.fulfill({ response: backend });
  });
  await page.getByRole("button", { name: "Khôi phục bản gốc" }).click();
  await expect.poll(() => restoreReceived).toBe(true);
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.002");
  releaseRestore();
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("2500.002");
  await expect(page.getByTestId("unit-ST-002")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("placed-mass")).toContainText("26,1");
  await page.unroute("**/api/validate");
  // The newer selection is ST-002, whose checked source value is exactly 2500 kg.
  await page.getByLabel("Khối lượng bó (kg)").fill("2500");
  await expect(page.getByTestId("status")).not.toHaveText("STALE");
  await page.route("**/api/validate", (route) => route.abort("failed"));
  await page.getByRole("button", { name: "Khôi phục bản gốc" }).click();
  await expect(page.locator(".error-banner[role='alert']")).toBeVisible();
  await expect(page.getByTestId("comparison-baseline")).toContainText("trong tab");
  await expect(page.getByTestId("status")).toHaveText(checkedB.status);
});
