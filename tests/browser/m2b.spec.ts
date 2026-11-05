import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { Page } from "../../apps/frontend/node_modules/@playwright/test";

type Unit = { id: string; mass_g: number; requirement: "required" | "optional" | "excluded"; dimensions_um?: number[] | null; source_ref?: { workbook_sha256: string } | null };
type Placement = { unit_id: string; x_mm: number; y_mm: number; z_mm: number; layer: number; yaw_deg: number; supported_by: string[] };
type Plan = { contract_version: string; source: string; cargo_source: string; cargo_dataset: string | null; vessel: { case_id: string } | null; hold: { length_mm: number; width_mm: number; height_mm: number }; limits: { voyage_cargo_limit_g: number; cargo_onboard_g: number }; units: Unit[]; placements: Placement[] };
type Evaluation = { plan: Plan; status: string; summary: { manifest_mass_g: number; placed_mass_g: number; placed_count: number; remaining_capacity_g: number }; issues: { code: string }[] };
type Preview = { algorithm: string; evaluation: Evaluation; unplaced: { unit_id: string; code: string; message: string }[] };
type Mesh = { id: string; position: number[]; dimensions: number[] };
type Saved = { id: string };

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

async function loadPipeList(page: Page): Promise<Evaluation> {
  await postResult<Evaluation>(page, "/api/pipe-list/preview", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
  return postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
}

function checkAccounting(preview: Preview, input: Plan): void {
  const candidate = preview.evaluation.plan;
  const placed = new Set(candidate.placements.map((placement) => placement.unit_id));
  const unplaced = new Set(preview.unplaced.map((reason) => reason.unit_id));
  expect(placed.size).toBe(candidate.placements.length);
  expect(unplaced.size).toBe(preview.unplaced.length);
  expect([...placed].filter((id) => unplaced.has(id))).toEqual([]);
  expect(placed.size + unplaced.size).toBe(input.units.length);
  expect(candidate.units).toEqual(input.units);
  expect({ ...candidate, placements: [] }).toEqual({ ...input, placements: [] });
  expect(candidate.placements.every((p) => p.z_mm === 0 && p.layer === 0 && p.supported_by.length === 0 && [0, 90].includes(p.yaw_deg))).toBe(true);
  expect(preview.unplaced.every((r) => r.message.length > 0)).toBe(true);
  expect(preview.unplaced.every((r) => ["EXCLUDED", "TOO_HIGH", "FOOTPRINT_TOO_LARGE", "MASS_LIMIT", "HEURISTIC_NO_SPACE"].includes(r.code))).toBe(true);
  expect(preview.evaluation.summary.placed_mass_g).toBe(candidate.placements.reduce((sum, p) => sum + input.units.find((u) => u.id === p.unit_id)!.mass_g, 0));
  expect(preview.evaluation.summary.placed_mass_g).toBeLessThanOrEqual(input.limits.voyage_cargo_limit_g - input.limits.cargo_onboard_g);
}

test("demo planner previews replacement without mutation, then applies checked real meshes and undo", async ({ page, request }) => {
  const original = await (await request.get("/api/demo")).json() as Evaluation;
  await page.goto("/?viewerDiagnostics=1");
  const beforeMass = await page.getByTestId("placed-mass").textContent();
  await expect.poll(() => page.getByTestId("three-canvas").getAttribute("data-meshes")).not.toBeNull();
  const beforeMeshes = await page.getByTestId("three-canvas").getAttribute("data-meshes");
  const preview = await postResult<Preview>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  expect(preview.algorithm).toBe("guillotine-single-layer-v1");
  checkAccounting(preview, original.plan);
  expect(preview.evaluation.plan.placements.length).toBeGreaterThan(0);
  await expect(page.getByTestId("planner-preview")).toBeVisible();
  await expect(page.getByTestId("placed-mass")).toHaveText(beforeMass!);
  expect(await page.getByTestId("three-canvas").getAttribute("data-meshes")).toBe(beforeMeshes);
  const applied = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  expect(applied.plan.placements).toEqual(preview.evaluation.plan.placements);
  expect(applied.summary.placed_mass_g).toBe(preview.evaluation.summary.placed_mass_g);
  await expect(page.getByTestId("three-canvas")).toBeInViewport();
  await expect.poll(async () => (JSON.parse((await page.getByTestId("three-canvas").getAttribute("data-meshes"))!) as Mesh[]).length).toBe(applied.plan.placements.length);
  await page.getByRole("button", { name: "Mặt bằng", exact: true }).click();
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  await page.getByRole("button", { name: "Bản trước" }).click();
  await expect(page.getByTestId("placed-mass")).toHaveText(beforeMass!);
  await expect(page.getByTestId("status")).toHaveText(original.status);
});

test("VINAFCO source list planner puts actual bundles in the hold, reconciles all 1076 and survives save/reload", async ({ page, request }) => {
  test.setTimeout(60_000);
  await page.goto("/?viewerDiagnostics=1");
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  const loaded = await loadPipeList(page);
  expect(loaded.plan.units).toHaveLength(1076);
  expect(loaded.summary.manifest_mass_g).toBe(1_125_551_030);
  await expect(page.getByTestId("manifest-mass")).toHaveText("1.125,55 tấn");
  await page.getByTestId("unit-PIPE-R002-B0001").getByRole("button").click();
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("911");
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveJSProperty("readOnly", true);
  await page.getByLabel("Cách xếp thử").selectOption("guillotine-single-layer-v1");
  const preview = await postResult<Preview>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  checkAccounting(preview, loaded.plan);
  expect(preview.evaluation.plan.placements.length).toBeGreaterThan(0);
  expect(preview.unplaced.length).toBeGreaterThan(0);
  expect(preview.evaluation.plan.cargo_source).toBe("DOCUMENT_CALCULATED");
  expect(preview.evaluation.plan.units[0].dimensions_um).toEqual([6_401_000, 337_600, 295_400]);
  expect(preview.evaluation.plan.units[0].source_ref?.workbook_sha256).toBe(loaded.plan.units[0].source_ref?.workbook_sha256);
  await expect(page.getByTestId("planner-preview")).toContainText(String(preview.evaluation.plan.placements.length));
  await expect(page.getByTestId("planner-reasons")).toBeVisible();
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 0 bó");
  const applied = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  expect(applied.plan.placements).toEqual(preview.evaluation.plan.placements);
  await expect(page.getByTestId("pipe-total")).toContainText(`đã xếp ${applied.summary.placed_count} bó`);
  const canvas = page.getByTestId("three-canvas");
  await expect(canvas).toHaveAttribute("data-vessel-bounds", /min/);
  await expect.poll(async () => (JSON.parse((await canvas.getAttribute("data-meshes"))!) as Mesh[]).length).toBe(applied.summary.placed_count);
  const meshes = JSON.parse((await canvas.getAttribute("data-meshes"))!) as Mesh[];
  expect(meshes.some((m) => m.id.startsWith("PIPE-"))).toBe(true);
  const mesh = meshes[0];
  const placement = applied.plan.placements.find((p) => p.unit_id === mesh.id)!;
  const sourceUnit = applied.plan.units.find((u) => u.id === mesh.id)!;
  const [lengthUm, widthUm, heightUm] = sourceUnit.dimensions_um!;
  const [footLengthUm, footWidthUm] = placement.yaw_deg === 90 ? [widthUm, lengthUm] : [lengthUm, widthUm];
  expect(mesh.dimensions[0]).toBeCloseTo(footLengthUm / 1_000_000, 6);
  expect(mesh.dimensions[1]).toBeCloseTo(heightUm / 1_000_000, 6);
  expect(mesh.dimensions[2]).toBeCloseTo(footWidthUm / 1_000_000, 6);
  expect(mesh.position[0]).toBeCloseTo((placement.x_mm + footLengthUm / 2000 - applied.plan.hold.length_mm / 2) / 1000, 6);
  expect(mesh.position[2]).toBeCloseTo((placement.y_mm + footWidthUm / 2000 - applied.plan.hold.width_mm / 2) / 1000, 6);
  await page.getByRole("region", { name: "Mô hình chất xếp" }).screenshot({ path: evidencePath("m2b.spec-vinafco-planned-scene.png") });
  await page.screenshot({ path: evidencePath("m2b.spec-vinafco-planned-desktop.png"), fullPage: true });
  await page.getByLabel("Tên phương án lưu").fill(`M2b browser ${Date.now()}`);
  const saved = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  const snapshot = await (await request.get(`/api/snapshots/${saved.id}`)).json() as Evaluation;
  expect(snapshot.plan.placements).toEqual(applied.plan.placements);
  expect(snapshot.plan.units).toEqual(loaded.plan.units);
  await page.reload();
  await page.getByLabel("Phương án đã lưu").selectOption(saved.id);
  const reopened = await getResult<Evaluation>(page, `/api/snapshots/${saved.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(reopened.plan.placements).toEqual(applied.plan.placements);
  await expect(page.getByTestId("pipe-total")).toContainText(`đã xếp ${applied.summary.placed_count} bó`);
});

test("a one-gram manual unit has practical rounded detail while API retains exact grams", async ({ page }) => {
  await page.goto("/");
  await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Phương án mới" }).click());
  await page.getByLabel("Bó mới id").fill("TINY-001");
  await page.getByLabel("Bó mới name").fill("Bó kiểm khối lượng nhỏ");
  await page.getByLabel("Bó mới length").fill("100");
  await page.getByLabel("Bó mới width").fill("100");
  await page.getByLabel("Bó mới height").fill("100");
  await page.getByLabel("Bó mới mass").fill("0.001");
  const added = await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Thêm bó", exact: true }).click());
  expect(added.plan.units).toMatchObject([{ id: "TINY-001", mass_g: 1 }]);
  expect(added.summary.manifest_mass_g).toBe(1);
  await expect(page.getByTestId("manifest-mass")).toHaveText("<0,01 tấn");
  await expect(page.getByTestId("unit-TINY-001")).toContainText("<1 kg");
  await expect(page.getByLabel("Khối lượng bó (kg)")).toHaveValue("0");
});

test("STALE edits, delayed planner response and network failure leave the checked plan unchanged", async ({ page }) => {
  await page.goto("/");
  const original = await page.getByTestId("placed-mass").textContent();
  await page.getByLabel("Giới hạn chuyến (kg)").fill("31999");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.getByRole("button", { name: "Xếp thử tự động" }).click();
  await expect(page.getByRole("alert")).toContainText("bản nháp");
  await expect(page.getByTestId("placed-mass")).toHaveText(original!);
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByTestId("status")).not.toHaveText("STALE");
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let received = false;
  await page.route("**/api/planner/preview", async (route) => {
    const backend = await route.fetch();
    received = true;
    await gate;
    await route.fulfill({ response: backend });
  });
  await page.getByRole("button", { name: "Xếp thử tự động" }).click();
  await expect.poll(() => received).toBe(true);
  await page.getByLabel("Giới hạn chuyến (kg)").fill("31998");
  release();
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await expect(page.getByRole("button", { name: "Áp dụng xếp thử" })).toHaveCount(0);
  await page.unroute("**/api/planner/preview");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  const checkedMass = await page.getByTestId("placed-mass").textContent();
  await page.route("**/api/planner/preview", (route) => route.abort("failed"));
  await page.getByRole("button", { name: "Xếp thử tự động" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByTestId("placed-mass")).toHaveText(checkedMass!);
  await expect(page.getByRole("button", { name: "Áp dụng xếp thử" })).toHaveCount(0);
});

test("mobile WebGL fallback shows applied source cargo and paged reasons without page overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...args: unknown[]) {
      if (type.includes("webgl")) return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.goto("/");
  await loadPipeList(page);
  await page.getByLabel("Cách xếp thử").selectOption("guillotine-single-layer-v1");
  const preview = await postResult<Preview>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  expect(preview.unplaced.length).toBeGreaterThan(50);
  await expect(page.getByTestId("planner-page")).toContainText("Trang 1/");
  await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  await expect(page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D")).toBeVisible();
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  expect(await page.getByRole("button", { name: /^Chọn PIPE-/ }).count()).toBeGreaterThan(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.getByRole("region", { name: "Mô hình chất xếp" }).screenshot({ path: evidencePath("m2b.spec-planned-mobile-scene.png") });
  await page.screenshot({ path: evidencePath("m2b.spec-planned-mobile-fallback.png"), fullPage: true });
});
