import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";

type Triple = [number, number, number];
type Plan = {
  source: string;
  vessel: { vessel_id: string; case_id: string } | null;
  hold: { length_mm: number; width_mm: number; height_mm: number };
  limits: { certificate_cargo_limit_g: number; voyage_cargo_limit_g: number; cargo_onboard_g: number };
  units: { id: string; length_mm: number; width_mm: number; height_mm: number }[];
  placements: { unit_id: string; x_mm: number; y_mm: number; z_mm: number; yaw_deg: number }[];
};
type Evaluation = { plan: Plan; status: string };
type Profile = {
  dimensions_m: { length: number; beam: number; depth: number };
  hold: { length_mm: number; width_mm: number; height_mm: number; source_width_m: number; status: string };
  cases: { id: string; cargo_mass_g: number; draft_m: number; deadweight_t: number; freeboard_mm: number }[];
  lightship_mass_t: number | null;
  tanktop_load_limit_t_per_m2: number | null;
  asset_url: string;
};
type Mesh = { id: string; position: Triple; dimensions: Triple; worldMatrix: number[] };
const near = (actual: number, expected: number) => expect(actual).toBeCloseTo(expected, 3);

async function openVessel(page: import("../../apps/frontend/node_modules/@playwright/test").Page, diagnostics = false) {
  await page.goto(diagnostics ? "/?viewerDiagnostics=1" : "/");
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268" })).toBeVisible();
}

test("real GLB and placed cargo share backend coordinates; camera, picking and hull toggle work", async ({ page, request }) => {
  const profile = (await (await request.get("/api/vessels/vinafco268")).json()) as Profile;
  const model = await request.get(profile.asset_url);
  expect(model.ok()).toBe(true);
  expect(model.headers()["content-type"]).toContain("model/gltf-binary");
  const modelBytes = await model.body();
  expect(modelBytes.subarray(0, 4).toString()).toBe("glTF");
  await openVessel(page, true);
  const canvas = page.getByTestId("three-canvas");
  await expect.poll(() => canvas.getAttribute("data-vessel-bounds")).not.toBeNull();
  const bounds = JSON.parse((await canvas.getAttribute("data-vessel-bounds"))!) as { min: Triple; max: Triple; position: Triple };
  near(bounds.position[0], -0.9725);
  near(bounds.position[1], -0.832);
  near(bounds.position[2], 0);
  near(bounds.max[0] - bounds.min[0], profile.dimensions_m.length);
  expect(bounds.max[2] - bounds.min[2]).toBeGreaterThanOrEqual(profile.dimensions_m.beam - 0.1);
  expect(bounds.max[1] - bounds.min[1]).toBeGreaterThanOrEqual(profile.dimensions_m.depth - 0.1);

  const checked = (await (await request.get("/api/vessels/vinafco268/cases/VR-SII/plan")).json()) as Evaluation;
  expect(checked.plan.hold).toMatchObject({ length_mm: 56405, width_mm: 10343, height_mm: 5408 });
  await expect.poll(() => canvas.getAttribute("data-meshes")).not.toBeNull();
  const meshes = JSON.parse((await canvas.getAttribute("data-meshes"))!) as Mesh[];
  expect(meshes).toHaveLength(checked.plan.placements.length);
  for (const placement of checked.plan.placements) {
    const unit = checked.plan.units.find((item) => item.id === placement.unit_id)!;
    const mesh = meshes.find((item) => item.id === unit.id)!;
    expect(mesh).toBeDefined();
    const dx = (placement.yaw_deg % 180 ? unit.width_mm : unit.length_mm) / 1000;
    const dz = (placement.yaw_deg % 180 ? unit.length_mm : unit.width_mm) / 1000;
    [dx, unit.height_mm / 1000, dz].forEach((expected, i) => near(mesh.dimensions[i], expected));
    const expectedPosition = [
      placement.x_mm / 1000 + dx / 2 - checked.plan.hold.length_mm / 2000,
      placement.z_mm / 1000 + unit.height_mm / 2000,
      placement.y_mm / 1000 + dz / 2 - checked.plan.hold.width_mm / 2000,
    ];
    expectedPosition.forEach((expected, i) => { near(mesh.position[i], expected); near(mesh.worldMatrix[12 + i], expected); });
  }
  const marker = JSON.parse((await canvas.getAttribute("data-draft-marker"))!) as { caseId: string; y: number; draft: number };
  expect(marker.caseId).toBe("VR-SII");
  near(marker.draft, 4.85);
  near(marker.y, 4.85 - 0.832);
  const { writeFileSync } = await import("node:fs");
  writeFileSync(evidencePath("vinafco-geometry.json"), JSON.stringify({
    assetUrl: profile.asset_url,
    assetBytes: modelBytes.length,
    dimensionsFromApiM: profile.dimensions_m,
    holdFromApiMm: checked.plan.hold,
    worldVesselBoundsM: bounds,
    draftMarker: marker,
    cargoMeshes: meshes,
  }, null, 2) + "\n");
  await canvas.scrollIntoViewIfNeeded();
  const firstCamera = await canvas.getAttribute("data-camera");
  const box = (await canvas.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 100, box.y + box.height / 2 + 30, { steps: 8 });
  await page.mouse.up();
  await expect.poll(() => canvas.getAttribute("data-camera")).not.toBe(firstCamera);
  await page.getByRole("button", { name: "Đặt lại góc nhìn" }).click();
  await expect.poll(() => canvas.getAttribute("data-camera")).toBe(firstCamera);
  await canvas.hover();
  await page.mouse.wheel(0, -300);
  await expect.poll(() => canvas.getAttribute("data-camera")).not.toBe(firstCamera);
  await page.getByRole("button", { name: "Đặt lại góc nhìn" }).click();
  const projected = JSON.parse((await canvas.getAttribute("data-projected-meshes"))!) as { id: string; x: number; y: number }[];
  const target = projected.find((item) => item.id === "PP-007")!;
  await canvas.click({ position: { x: target.x, y: target.y } });
  await expect(page.getByTestId("unit-PP-007")).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "Ẩn tàu" }).click();
  await expect(page.getByRole("button", { name: "Hiện tàu" })).toBeVisible();
  await page.getByRole("button", { name: "Hiện tàu" }).click();
  await expect(page.getByRole("button", { name: "Ẩn tàu" })).toBeVisible();
  await page.screenshot({ path: evidencePath("vinafco.spec-browser-vessel-3d.png"), fullPage: true });
});

test("SI/SII reference limits, labels, history and pending edits remain tied to the selected case", async ({ page, request }) => {
  const profile = (await (await request.get("/api/vessels/vinafco268")).json()) as Profile;
  expect(profile.lightship_mass_t).toBeNull();
  expect(profile.tanktop_load_limit_t_per_m2).toBeNull();
  expect(profile.hold.status).toBe("ESTIMATED");
  expect(profile.hold.source_width_m).toBe(10.34375);
  const si = (await (await request.get("/api/vessels/vinafco268/cases/VR-SI/plan")).json()) as Evaluation;
  const sii = (await (await request.get("/api/vessels/vinafco268/cases/VR-SII/plan")).json()) as Evaluation;
  expect(si.plan.limits.certificate_cargo_limit_g).toBe(3_282_500_000);
  expect(sii.plan.limits.certificate_cargo_limit_g).toBe(3_517_500_000);
  expect(profile.cases.map((item) => [item.draft_m, item.deadweight_t, item.freeboard_mm])).toEqual([[4.6, 3301, 612], [4.85, 3536, 362]]);
  for (const [template, excessive] of [[si, 3_300_000_000], [sii, 3_520_000_000]] as const) {
    const altered = structuredClone(template.plan);
    altered.limits.voyage_cargo_limit_g = excessive;
    const rejected = await request.post("/api/validate", { data: altered });
    expect(rejected.status()).toBe(422);
  }
  await openVessel(page, true);
  const note = page.getByRole("region", { name: "Thông số VINAFCO 268" });
  await expect(note).toContainText("3.517,5 tấn");
  await expect(note).toContainText("TTTP 3.536 tấn");
  await expect(note).toContainText("chưa có dữ liệu");
  await expect(note).toContainText("Hầm ước tính");
  await expect(note).toContainText("4,17 m");
  await expect(page.getByLabel("Giới hạn chứng nhận (kg)")).toHaveJSProperty("readOnly", true);
  const caseSelect = page.getByLabel("Cấp tham chiếu");
  const mass = page.getByLabel("Khối lượng bó (kg)");
  await mass.fill("2500.001");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await caseSelect.selectOption("VR-SI");
  await expect(page.getByRole("alert")).toContainText("bản nháp");
  await expect(mass).toHaveValue("2500.001");
  await expect(caseSelect).toHaveValue("VR-SII");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByTestId("status")).not.toHaveText("STALE");
  await caseSelect.selectOption("VR-SI");
  await expect(caseSelect).toHaveValue("VR-SI");
  await expect(note).toContainText("3.282,5 tấn");
  await expect(note).toContainText("TTTP 3.301 tấn");
  await expect(page.getByTestId("three-canvas")).toHaveAttribute("data-draft-marker", /VR-SI/);
  await expect(mass).toHaveValue("2500");
  await page.getByRole("button", { name: "Bản trước" }).click();
  await expect(caseSelect).toHaveValue("VR-SII");
  await expect(mass).toHaveValue("2500");
  await page.screenshot({ path: evidencePath("vinafco.spec-browser-vessel-si.png"), fullPage: true });
});

test("model failure and mobile WebGL fallback keep case data and editing usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/vessels/vinafco268/model", (route) => route.abort("failed"));
  await openVessel(page);
  await expect(page.getByText(/Không tải được mô hình tàu/)).toBeVisible();
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268" })).toContainText("3.517,5 tấn");
  await page.getByLabel("Tọa độ X (cm)").fill("50.1");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByTestId("unit-ST-001")).toContainText("50, 55");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: evidencePath("vinafco.spec-browser-vessel-model-failure.png"), fullPage: true });
  await page.unroute("**/api/vessels/vinafco268/model");

  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...args: unknown[]) {
      if (type.includes("webgl")) return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.reload();
  await openVessel(page);
  await expect(page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D")).toBeVisible();
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  await page.getByRole("button", { name: "Chọn PP-007" }).click();
  await expect(page.getByTestId("unit-PP-007")).toHaveAttribute("aria-selected", "true");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: evidencePath("vinafco.spec-browser-vessel-mobile-fallback.png"), fullPage: true });
});

test("case request failure and a newer edit during a pending switch preserve the checked case", async ({ page }) => {
  await openVessel(page);
  const caseSelect = page.getByLabel("Cấp tham chiếu");
  const mass = page.getByLabel("Khối lượng bó (kg)");
  const originalMass = await mass.inputValue();
  await page.route("**/api/vessels/vinafco268/cases/VR-SI/plan", (route) => route.abort("failed"));
  await caseSelect.selectOption("VR-SI");
  await expect(page.getByRole("alert")).toContainText("Không tải được trạng thái phương tiện");
  await expect(caseSelect).toHaveValue("VR-SII");
  await expect(mass).toHaveValue(originalMass);
  await page.unroute("**/api/vessels/vinafco268/cases/VR-SI/plan");

  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let received = false;
  await page.route("**/api/vessels/vinafco268/cases/VR-SI/plan", async (route) => {
    const backend = await route.fetch();
    received = true;
    await gate;
    await route.fulfill({ response: backend });
  });
  await caseSelect.selectOption("VR-SI");
  await expect.poll(() => received).toBe(true);
  await mass.fill("2500.002");
  release();
  await expect(page.getByRole("alert")).toContainText("Bản nháp đã thay đổi");
  await expect(caseSelect).toHaveValue("VR-SII");
  await expect(mass).toHaveValue("2500.002");
  await expect(page.getByTestId("status")).toHaveText("STALE");
});
