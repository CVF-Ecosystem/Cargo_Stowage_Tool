import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { Page } from "../../apps/frontend/node_modules/@playwright/test";

type Unit = { id: string; mass_g: number; length_mm: number; width_mm: number; height_mm: number; dimensions_um?: number[] | null; source_ref?: unknown };
type Placement = { unit_id: string; x_mm: number; y_mm: number; z_mm: number; yaw_deg: number };
type Plan = { units: Unit[]; placements: Placement[]; limits: { voyage_cargo_limit_g: number } };
type Evaluation = { plan: Plan; summary: { manifest_mass_g: number; placed_count: number; placed_mass_g: number } };
type Saved = { id: string };
type Comparison = { delta: { manifest_mass_g: number }; rows: { unit_id: string; changes: { field: string; before: unknown; after: unknown }[] }[] };
type Mesh = { id: string; dimensions: number[]; position: number[] };

async function postResult<T>(page: Page, path: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((response) => response.url().endsWith(path) && response.request().method() === "POST");
  await action();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return await response.json() as T;
}

async function getResult<T>(page: Page, path: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((response) => response.url().endsWith(path) && response.request().method() === "GET");
  await action();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return await response.json() as T;
}

test("rounded practical inputs preserve untouched grams and millimetres through edit, save and reload", async ({ page, request }) => {
  const demo = await (await request.get("/api/demo")).json() as Evaluation;
  const fixture = structuredClone(demo.plan);
  fixture.units.find((u) => u.id === "ST-001")!.mass_g = 2_500_001;
  fixture.placements.find((p) => p.unit_id === "ST-001")!.x_mm = 501;
  const created = await request.post("/api/snapshots", { data: { name: `Display exact A ${Date.now()}`, plan: fixture } });
  expect(created.ok()).toBe(true);
  const savedA = await created.json() as Saved;

  await page.goto("/");
  await page.getByLabel("Phương án đã lưu").selectOption(savedA.id);
  const opened = await getResult<Evaluation>(page, `/api/snapshots/${savedA.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(opened.plan.units.find((u) => u.id === "ST-001")!.mass_g).toBe(2_500_001);
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("2500");
  await expect(page.getByLabel("Tọa độ X (cm)")).toHaveValue("50");
  await expect(page.getByTestId("unit-ST-001")).toContainText("2.500 kg");
  await expect(page.getByTestId("unit-ST-001")).toContainText("600 × 90 × 65");

  await page.getByLabel("Góc xoay").selectOption("90");
  const changed = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(changed.plan.units.find((u) => u.id === "ST-001")).toMatchObject({ mass_g: 2_500_001, length_mm: 6000, width_mm: 900, height_mm: 650 });
  expect(changed.plan.placements.find((p) => p.unit_id === "ST-001")).toMatchObject({ x_mm: 501, yaw_deg: 90 });
  const changedContext = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Xem VINAFCO 268" }).click());
  expect(changedContext.plan.units.find((u) => u.id === "ST-001")!.mass_g).toBe(2_500_001);
  expect(changedContext.plan.placements.find((p) => p.unit_id === "ST-001")!.x_mm).toBe(501);
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268" })).toBeVisible();
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("2500");
  await page.getByLabel("Tên phương án lưu").fill(`Display exact B ${Date.now()}`);
  const savedB = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  expect(savedB.id).not.toBe(savedA.id);
  await page.reload();
  await page.getByLabel("Phương án đã lưu").selectOption(savedB.id);
  const reopened = await getResult<Evaluation>(page, `/api/snapshots/${savedB.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(reopened.plan.units.find((u) => u.id === "ST-001")!.mass_g).toBe(2_500_001);
  expect(reopened.plan.placements.find((p) => p.unit_id === "ST-001")).toMatchObject({ x_mm: 501, yaw_deg: 90 });

  // The rounded default is only a view; deliberately retyping it is a real edit.
  const mass = page.getByLabel("Khối lượng bó (kg)");
  await mass.fill("");
  await mass.fill("2500");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  const roundedEdit = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(roundedEdit.plan.units.find((u) => u.id === "ST-001")!.mass_g).toBe(2_500_000);
  expect(roundedEdit.plan.placements.find((p) => p.unit_id === "ST-001")!.x_mm).toBe(501);

  await page.getByLabel("Khối lượng bó (kg)").fill("2501.125");
  await page.getByLabel("Tọa độ X (cm)").fill("51.2");
  const explicit = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(explicit.plan.units.find((u) => u.id === "ST-001")!.mass_g).toBe(2_501_125);
  expect(explicit.plan.placements.find((p) => p.unit_id === "ST-001")!.x_mm).toBe(512);
  await page.getByLabel("Tọa độ X (cm)").fill("51.23");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByLabel("Tọa độ X (cm)")).toHaveValue("51.23");
  await expect(page.getByTestId("status")).toHaveText("STALE");
});

test("comparison marks sub-resolution kg and cm changes while API retains exact deltas", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Giữ bản hiện tại làm gốc" }).click();
  await page.getByLabel("Khối lượng bó (kg)").fill("2500.001");
  await page.getByLabel("Tọa độ X (cm)").fill("50.1");
  const b = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(b.plan.units.find((u) => u.id === "ST-001")!.mass_g).toBe(2_500_001);
  expect(b.plan.placements.find((p) => p.unit_id === "ST-001")!.x_mm).toBe(501);
  const compared = await postResult<Comparison>(page, "/api/plans/compare", () => page.getByRole("button", { name: "So sánh với bản gốc" }).click());
  expect(compared.delta.manifest_mass_g).toBe(1);
  expect(compared.rows.find((r) => r.unit_id === "ST-001")?.changes).toEqual(expect.arrayContaining([
    { field: "mass_g", before: 2_500_000, after: 2_500_001 },
    { field: "placement.x_mm", before: 500, after: 501 },
  ]));
  const row = page.getByTestId("comparison-row-ST-001");
  await row.getByText("Chi tiết thay đổi").click();
  await expect(row).toContainText("dưới 1 kg");
  await expect(row).toContainText("dưới 1 cm");
  await expect(row).not.toContainText("1 g");
  await page.screenshot({ path: evidencePath("display-units.spec-compare-small-delta.png"), fullPage: true });
});

test("source cargo uses practical labels while all 1076 precise units and actual model meshes survive mobile fallback", async ({ page }) => {
  test.setTimeout(90_000);
  await page.goto("/?viewerDiagnostics=1");
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await postResult<Evaluation>(page, "/api/pipe-list/preview", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
  const loaded = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
  expect(loaded.plan.units).toHaveLength(1076);
  expect(loaded.plan.units[0]).toMatchObject({ mass_g: 911_400, dimensions_um: [6_401_000, 337_600, 295_400] });
  await expect(page.getByTestId("unit-PIPE-R002-B0001")).toContainText("911 kg");
  await expect(page.getByTestId("unit-PIPE-R002-B0001")).toContainText("640 × 34 × 30");
  await page.getByTestId("unit-PIPE-R002-B0001").getByRole("button").click();
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("911");
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveJSProperty("readOnly", true);
  await page.getByLabel("Giới hạn chuyến (kg)").fill("3517500");
  const capacity = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(capacity.plan.units).toEqual(loaded.plan.units);
  await page.getByLabel("Cách xếp thử").selectOption("guillotine-single-layer-v1");
  const preview = await postResult<{ evaluation: Evaluation }>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  const applied = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  expect(applied.plan.units).toEqual(loaded.plan.units);
  expect(applied.plan.placements).toEqual(preview.evaluation.plan.placements);
  expect(applied.summary.placed_count).toBe(167);
  const canvas = page.getByTestId("three-canvas");
  await expect.poll(async () => (JSON.parse((await canvas.getAttribute("data-meshes"))!) as Mesh[]).length).toBe(applied.summary.placed_count);
  const mesh = (JSON.parse((await canvas.getAttribute("data-meshes"))!) as Mesh[]).find((m) => m.id === applied.plan.placements[0].unit_id)!;
  const unit = applied.plan.units.find((u) => u.id === mesh.id)!;
  const placement = applied.plan.placements.find((p) => p.unit_id === mesh.id)!;
  const [lengthUm, widthUm, heightUm] = unit.dimensions_um!;
  const [footLengthUm, footWidthUm] = placement.yaw_deg === 90 ? [widthUm, lengthUm] : [lengthUm, widthUm];
  expect(mesh.dimensions).toEqual(expect.arrayContaining([footLengthUm / 1_000_000, heightUm / 1_000_000, footWidthUm / 1_000_000]));
  await page.getByRole("region", { name: "Mô hình chất xếp" }).screenshot({ path: evidencePath("display-units.spec-source-desktop-scene.png") });
  await page.getByLabel("Tên phương án lưu").fill(`Display source ${Date.now()}`);
  const saved = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...args: unknown[]) {
      if (type.includes("webgl")) return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.reload();
  await page.getByLabel("Phương án đã lưu").selectOption(saved.id);
  const reopened = await getResult<Evaluation>(page, `/api/snapshots/${saved.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(reopened.plan.units).toEqual(loaded.plan.units);
  expect(reopened.plan.placements).toEqual(applied.plan.placements);
  await expect(page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D")).toBeVisible();
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: evidencePath("display-units.spec-source-mobile-fallback.png"), fullPage: true });
});
