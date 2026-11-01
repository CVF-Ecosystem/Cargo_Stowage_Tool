import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";

type Unit = { id: string; length_mm: number; width_mm: number; height_mm: number; mass_g: number };
type Placement = { unit_id: string; x_mm: number; y_mm: number; z_mm: number; yaw_deg: number };
type Plan = { hold: { length_mm: number; width_mm: number }; units: Unit[]; placements: Placement[] };
type Evaluation = { plan: Plan; status: string; summary: { placed_mass_g: number } };
type Mesh = { id: string; position: number[]; dimensions: number[]; worldMatrix: number[] };
type ProjectedMesh = { id: string; x: number; y: number };

const near = (actual: number, expected: number) => expect(actual).toBeCloseTo(expected, 7);
const footprint = (unit: Unit, placement: Placement) =>
  placement.yaw_deg % 180 ? [unit.width_mm, unit.length_mm] : [unit.length_mm, unit.width_mm];

test("real API drives table, 2D and actual Three meshes through yaw and selection", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const response = await request.get("/api/demo");
  expect(response.ok()).toBe(true);
  const evaluated = (await response.json()) as Evaluation;
  const plan = evaluated.plan;
  await page.goto("/?viewerDiagnostics=1");
  await expect(page.getByTestId("status")).toHaveText(evaluated.status);
  await expect(page.getByText("SYNTHETIC", { exact: true }).first()).toBeVisible();
  const canvas = page.getByTestId("three-canvas");
  await expect(canvas).toBeVisible();
  await expect.poll(async () => canvas.getAttribute("data-meshes")).not.toBeNull();
  const meshes = JSON.parse((await canvas.getAttribute("data-meshes"))!) as Mesh[];
  expect(meshes).toHaveLength(plan.placements.length);
  for (const unit of plan.units) {
    const row = page.getByTestId(`unit-${unit.id}`);
    await expect(row).toContainText(`${Math.round(unit.length_mm / 10)} × ${Math.round(unit.width_mm / 10)} × ${Math.round(unit.height_mm / 10)}`);
    const mass = `${new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 0 }).format(Math.round(unit.mass_g / 1000))} kg`;
    await expect(row).toContainText(mass);
    if (plan.placements.some((placement) => placement.unit_id === unit.id)) {
      const placement = plan.placements.find((p) => p.unit_id === unit.id)!;
      await expect(row).toContainText(`${Math.round(placement.x_mm / 10)}, ${Math.round(placement.y_mm / 10)}, ${Math.round((placement.z_mm ?? 0) / 10)} cm · ${placement.yaw_deg}°`);
      const mesh = meshes.find((item) => item.id === unit.id)!;
      expect(mesh).toBeDefined();
      const [dx, dy] = footprint(unit, placement);
      const expectedPosition = [
        (placement.x_mm + dx / 2 - plan.hold.length_mm / 2) / 1000,
        ((placement.z_mm ?? 0) + unit.height_mm / 2) / 1000,
        (placement.y_mm + dy / 2 - plan.hold.width_mm / 2) / 1000,
      ];
      [dx / 1000, unit.height_mm / 1000, dy / 1000].forEach((expected, i) => near(mesh.dimensions[i], expected));
      expectedPosition.forEach((expected, i) => {
        near(mesh.position[i], expected);
        near(mesh.worldMatrix[12 + i], expected);
      });
    } else {
      await expect(row).toContainText("chưa xếp");
      expect(meshes.some((mesh) => mesh.id === unit.id)).toBe(false);
    }
  }

  await page.getByTestId("unit-ST-002").getByRole("button").click();
  await expect(page.getByRole("heading", { name: "ST-002" })).toBeVisible();
  await expect(page.getByTestId("unit-ST-002")).toHaveAttribute("aria-selected", "true");
  const projected = JSON.parse((await canvas.getAttribute("data-projected-meshes"))!) as ProjectedMesh[];
  const hitTarget = projected.find((mesh) => mesh.id === "PP-007")!;
  expect(hitTarget).toBeDefined();
  await canvas.click({ position: { x: hitTarget.x, y: hitTarget.y } });
  await expect(page.getByTestId("unit-PP-007")).toHaveAttribute("aria-selected", "true");
  const firstCamera = JSON.parse((await canvas.getAttribute("data-camera"))!) as number[];
  const box = (await canvas.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 100, box.y + box.height / 2 + 35, { steps: 8 });
  await page.mouse.up();
  await expect.poll(async () => canvas.getAttribute("data-camera")).not.toBe(JSON.stringify(firstCamera));
  await page.getByRole("button", { name: "Đặt lại góc nhìn" }).click();
  await expect.poll(async () => JSON.parse((await canvas.getAttribute("data-camera"))!) as number[])
    .toEqual(firstCamera);
  await canvas.hover();
  await page.mouse.wheel(0, -300);
  await expect.poll(async () => canvas.getAttribute("data-camera")).not.toBe(JSON.stringify(firstCamera));
  await page.getByRole("button", { name: "Đặt lại góc nhìn" }).click();

  await page.getByRole("button", { name: "Mặt bằng", exact: true }).click();
  const map = page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" });
  await expect(map).toBeVisible();
  for (const placement of plan.placements) {
    const unit = plan.units.find((item) => item.id === placement.unit_id)!;
    const [width, height] = footprint(unit, placement);
    const rect = page.getByRole("button", { name: `Chọn ${unit.id}` }).locator("rect");
    await expect(rect).toHaveAttribute("x", String(placement.x_mm));
    await expect(rect).toHaveAttribute("y", String(placement.y_mm));
    await expect(rect).toHaveAttribute("width", String(width));
    await expect(rect).toHaveAttribute("height", String(height));
  }
  await expect(page.getByRole("button", { name: "Chọn PP-007" })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Chọn ST-002" }).click();
  await expect(page.getByTestId("unit-ST-002")).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "Chọn PP-007" }).click();
  await expect(page.getByTestId("unit-PP-007")).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "3D", exact: true }).click();
  await page.getByTestId("unit-ST-001").getByRole("button").click();
  await page.getByLabel("Góc xoay").selectOption("90");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  const yawResponse = page.waitForResponse((response) => response.url().endsWith("/api/validate") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  const yawChecked = (await (await yawResponse).json()) as Evaluation;
  const turned = yawChecked.plan.placements.find((placement) => placement.unit_id === "ST-001")!;
  expect(turned.yaw_deg).toBe(90);
  await expect.poll(async () => canvas.getAttribute("data-meshes")).not.toBeNull();
  const turnedMesh = (JSON.parse((await canvas.getAttribute("data-meshes"))!) as Mesh[]).find((mesh) => mesh.id === "ST-001")!;
  const turnedUnit = yawChecked.plan.units.find((unit) => unit.id === "ST-001")!;
  const [turnedX, turnedY] = footprint(turnedUnit, turned);
  near(turnedMesh.dimensions[0], turnedX / 1000);
  near(turnedMesh.dimensions[2], turnedY / 1000);
  near(turnedMesh.position[0], (turned.x_mm + turnedX / 2 - plan.hold.length_mm / 2) / 1000);
  near(turnedMesh.position[2], (turned.y_mm + turnedY / 2 - plan.hold.width_mm / 2) / 1000);
  await page.screenshot({ path: evidencePath("workspace.spec-browser-3d-yaw.png"), fullPage: true });
  expect(errors).toEqual([]);
});

test("raw edit is immediately STALE; real API 422 and network loss preserve checked result and draft; retry and undo recover", async ({ page, request }) => {
  const initial = (await (await request.get("/api/demo")).json()) as Evaluation;
  await page.goto("/");
  await expect(page.getByTestId("status")).toHaveText(initial.status);
  const originalPlaced = await page.getByTestId("placed-mass").textContent();
  const row = page.getByTestId("unit-ST-001");
  const originalRow = await row.textContent();
  const mass = page.getByLabel("Khối lượng bó (kg)", { exact: true });
  const x = page.getByLabel("Tọa độ X (cm)", { exact: true });
  const originalMass = await mass.inputValue();
  const originalX = await x.inputValue();
  await mass.fill("2500.001");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await expect(page.getByTestId("placed-mass")).toHaveText(originalPlaced!);
  await expect(row).toHaveText(originalRow!);
  await expect(page.getByText(/Bản nháp chưa được kiểm/)).toBeVisible();

  // The browser still sends its normal plan. Corrupt only the transport body so FastAPI returns a real 422.
  let rejectedStatus = 0;
  await page.route("**/api/validate", async (route) => {
    const backend = await route.fetch({ postData: "{}" });
    rejectedStatus = backend.status();
    await route.fulfill({ response: backend });
  });
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByRole("alert")).toContainText("không đúng cấu trúc");
  expect(rejectedStatus).toBe(422);
  await expect(mass).toHaveValue("2500.001");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await expect(page.getByTestId("placed-mass")).toHaveText(originalPlaced!);
  await expect(row).toHaveText(originalRow!);
  await page.unroute("**/api/validate");

  await x.fill("50.1");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.getByRole("button", { name: "Mặt bằng", exact: true }).click();
  await page.screenshot({ path: evidencePath("workspace.spec-browser-2d-stale.png"), fullPage: true });
  await page.route("**/api/validate", (route) => route.abort("failed"));
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(mass).toHaveValue("2500.001");
  await expect(x).toHaveValue("50.1");
  await expect(page.getByTestId("placed-mass")).toHaveText(originalPlaced!);
  await expect(row).toHaveText(originalRow!);
  await page.unroute("**/api/validate");

  const checkedResponse = page.waitForResponse((response) => response.url().endsWith("/api/validate") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  const checked = (await (await checkedResponse).json()) as Evaluation;
  expect(checked.summary.placed_mass_g).toBe(initial.summary.placed_mass_g + 1);
  await expect(page.getByTestId("status")).toHaveText(checked.status);
  await expect(mass).toHaveValue("2500");
  await expect(x).toHaveValue("50");
  await expect(row).toContainText("50, 55");
  await page.getByRole("button", { name: "Bản trước" }).click();
  await expect(page.getByTestId("status")).toHaveText(initial.status);
  await expect(mass).toHaveValue(originalMass);
  await expect(x).toHaveValue(originalX);
  await expect(page.getByTestId("placed-mass")).toHaveText(originalPlaced!);
  await expect(row).toHaveText(originalRow!);
});

test("WebGL failure keeps accessible 2D, table selection and synthetic warning", async ({ page }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...args: unknown[]) {
      if (type.includes("webgl")) return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D")).toBeVisible();
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  await expect(page.getByTestId("unit-PP-013")).toContainText("Tùy chọn chưa xếp");
  await expect(page.getByText(/không dùng cho phương án thực/)).toBeVisible();
  const selected = page.getByRole("button", { name: "Chọn PP-007" });
  await selected.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("unit-PP-007")).toHaveAttribute("aria-selected", "true");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  const shellWidth = (await page.locator(".main-shell").boundingBox())!.width;
  expect(shellWidth).toBe(await page.evaluate(() => innerWidth));
  await page.screenshot({ path: evidencePath("workspace.spec-browser-mobile-fallback.png"), fullPage: true });
  const tableScroll = await page.locator(".table-wrap").evaluate((element) => {
    const table = element as HTMLElement;
    const overflowX = getComputedStyle(table).overflowX;
    const extendsBeyondViewport = table.scrollWidth > table.clientWidth;
    table.scrollLeft = table.scrollWidth;
    return { overflowX, extendsBeyondViewport, scrollLeft: table.scrollLeft };
  });
  expect(tableScroll.overflowX).toBe("auto");
  expect(tableScroll.extendsBeyondViewport).toBe(true);
  expect(tableScroll.scrollLeft).toBeGreaterThan(0);
  await page.screenshot({ path: evidencePath("workspace.spec-browser-mobile-table-scrolled.png"), fullPage: true });
});

test("an edit during pending validation keeps the newer raw draft STALE until separately checked", async ({ page }) => {
  await page.goto("/");
  const mass = page.getByLabel("Khối lượng bó (kg)", { exact: true });
  const row = page.getByTestId("unit-ST-001");
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let received = false;
  await page.route("**/api/validate", async (route) => {
    const backend = await route.fetch();
    received = true;
    await gate;
    await route.fulfill({ response: backend });
  });
  await mass.fill("2500.001");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect.poll(() => received).toBe(true);
  await mass.fill("2500.002");
  release();
  await expect(mass).toHaveValue("2500.002");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await expect(row).toContainText("2.500 kg");
  await page.unroute("**/api/validate");
  const retry = page.waitForResponse((response) => response.url().endsWith("/api/validate") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  const checked = (await (await retry).json()) as Evaluation;
  expect(checked.plan.units.find((unit) => unit.id === "ST-001")?.mass_g).toBe(2_500_002);
  await expect(page.getByTestId("status")).toHaveText(checked.status);
  await expect(mass).toHaveValue("2500");
});

test("after setup the browser runs locally with all non-loopback traffic blocked", async ({ page, request }) => {
  const health = await (await request.get("/api/health")).json();
  expect(health.mode).toBe("synthetic-demo");
  expect(health.ai).toBe("off");
  const blocked: string[] = [];
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    if (url.protocol === "http:" || url.protocol === "https:") {
      if (url.hostname !== "127.0.0.1" && url.hostname !== "localhost" && url.hostname !== "::1") {
        blocked.push(url.href);
        return route.abort("blockedbyclient");
      }
    }
    return route.continue();
  });
  await page.goto("/");
  await expect(page.getByTestId("status")).toBeVisible();
  await page.getByTestId("unit-ST-001").getByRole("button").click();
  await page.getByLabel("Tọa độ X (cm)").fill("50.1");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByTestId("unit-ST-001")).toContainText("50, 55");
  await page.getByLabel("Giới hạn chứng nhận (kg)").fill("30000");
  await page.getByLabel("Giới hạn chuyến (kg)").fill("29000");
  await page.getByLabel("Hàng đã có trên tàu (kg)").fill("1000");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  const limitsResponse = page.waitForResponse((response) => response.url().endsWith("/api/validate") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  const checked = (await (await limitsResponse).json()) as Evaluation & { plan: Plan & { limits: { certificate_cargo_limit_g: number; voyage_cargo_limit_g: number; cargo_onboard_g: number } } };
  expect(checked.plan.limits).toEqual({ certificate_cargo_limit_g: 30_000_000, voyage_cargo_limit_g: 29_000_000, cargo_onboard_g: 1_000_000 });
  const fmtTonnes = (grams: number) => new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(grams / 1_000_000);
  await expect(page.getByTestId("placed-mass")).toHaveText(`${fmtTonnes(checked.summary.placed_mass_g)} / ${fmtTonnes(checked.plan.limits.voyage_cargo_limit_g - checked.plan.limits.cargo_onboard_g)} tấn`);
  await expect(page.locator("#checks")).toContainText("Chứng nhận: 30 tấn · Chuyến: 29 tấn · Đã có ngoài hầm: 1 tấn");
  await expect(page.locator("#checks")).toContainText("Được xếp thêm: 28 tấn");
  await expect(page.getByTestId("status")).toHaveText(checked.status);
  expect(blocked).toEqual([]);
});
