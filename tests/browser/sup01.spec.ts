import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { Page } from "../../apps/frontend/node_modules/@playwright/test";
import { writeFileSync } from "node:fs";

type Camera = { position: number[]; target: number[]; near: number; far: number; aspect: number; fov: number; projection: number[]; worldInverse: number[] };
type Stats = { loads: number; renders: number; assetIdentity: number; geometries: number; textures: number; calls: number; objects: number };
type Mesh = { id: string; uuid: string; dimensions: number[]; position: number[] };
type Material = { name: string; ghost: boolean; opacity: number; transparent: boolean; depthWrite: boolean };
const diag = "/?viewerDiagnostics=1";
const canvas = (page: Page) => page.getByTestId("three-canvas");
async function attribute<T>(page: Page, key: string): Promise<T> {
  return JSON.parse((await canvas(page).getAttribute(`data-${key}`))!) as T;
}
async function rememberCanvas(page: Page) {
  await canvas(page).evaluate((element) => { (window as Window & { __supCanvas?: Element }).__supCanvas = element; });
}
async function sameCanvas(page: Page) {
  expect(await canvas(page).evaluate((element) => element === (window as Window & { __supCanvas?: Element }).__supCanvas)).toBe(true);
}
function finiteCamera(camera: Camera) {
  expect([...camera.position, ...camera.target, camera.near, camera.far, camera.aspect, camera.fov, ...camera.projection, ...camera.worldInverse].every(Number.isFinite)).toBe(true);
  expect(camera.near).toBeGreaterThan(0);
  expect(camera.far).toBeGreaterThan(camera.near);
  expect(camera.aspect).toBeGreaterThan(0);
}
function corners(min: number[], max: number[]): number[][] {
  return [0, 1].flatMap((x) => [0, 1].flatMap((y) => [0, 1].map((z) => [x ? max[0] : min[0], y ? max[1] : min[1], z ? max[2] : min[2]])));
}
function multiply(matrix: number[], point: number[]): number[] {
  const p = [...point, 1];
  return [0, 1, 2, 3].map((row) => matrix[row] * p[0] + matrix[row + 4] * p[1] + matrix[row + 8] * p[2] + matrix[row + 12] * p[3]);
}
function assertFramed(camera: Camera, points: number[][]): void {
  for (const point of points) {
    const view = multiply(camera.worldInverse, point);
    const clip = multiply(camera.projection, view);
    expect(clip[3], `point ${point} in front of camera`).toBeGreaterThan(0);
    for (let axis = 0; axis < 3; axis++) expect(Math.abs(clip[axis] / clip[3]), `point ${point} clip axis ${axis}`).toBeLessThanOrEqual(1.01);
  }
}
async function postJson<T>(page: Page, path: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((response) => response.url().endsWith(path) && response.request().method() === "POST");
  await action();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return response.json() as Promise<T>;
}

test("normal route omits heavy diagnostics while opt-in retains exact mesh hooks", async ({ page }) => {
  await page.goto("/");
  await expect(canvas(page)).toBeVisible();
  await canvas(page).scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: "Nhìn trên" }).click();
  for (const name of ["data-meshes", "data-projected-meshes", "data-camera", "data-camera-state", "data-viewer-stats", "data-materials"]) {
    expect(await canvas(page).getAttribute(name), name).toBeNull();
  }
  await expect(page.getByRole("button", { name: "Tập trung bó" })).toBeEnabled();
  await page.goto(diag);
  await expect.poll(() => canvas(page).getAttribute("data-meshes")).not.toBeNull();
  expect((await attribute<Mesh[]>(page, "meshes")).length).toBeGreaterThan(0);
  finiteCamera(await attribute<Camera>(page, "camera-state"));
  expect((await attribute<Stats>(page, "viewer-stats")).objects).toBeGreaterThan(0);
});

test("synthetic scene keeps canvas, camera and unchanged cargo mesh through edit, undo and camera presets", async ({ page, request }) => {
  const demo = await (await request.get("/api/demo")).json() as { plan: { hold: { length_mm: number; width_mm: number; height_mm: number } } };
  await page.goto(diag);
  await expect.poll(() => canvas(page).getAttribute("data-camera-state")).not.toBeNull();
  await rememberCanvas(page);
  const first = await attribute<Mesh[]>(page, "meshes");
  const original = first.find((mesh) => mesh.id === "ST-002")!;
  expect(original.uuid).toBeTruthy();
  await page.getByTestId("unit-ST-001").getByRole("button").click();
  await canvas(page).scrollIntoViewIfNeeded();
  const initialCamera = await attribute<Camera>(page, "camera-state");
  const box = (await canvas(page).boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 90, box.y + box.height / 2 + 30, { steps: 6 });
  await page.mouse.up();
  await expect.poll(async () => (await attribute<Camera>(page, "camera-state")).position).not.toEqual(initialCamera.position);
  const orbit = await attribute<Camera>(page, "camera-state");
  await page.getByLabel("Khối lượng bó (kg)").fill("2501");
  await postJson(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  await sameCanvas(page);
  expect((await attribute<Camera>(page, "camera-state")).position).toEqual(orbit.position);
  expect((await attribute<Mesh[]>(page, "meshes")).find((mesh) => mesh.id === "ST-002")!.uuid).toBe(original.uuid);
  await page.getByRole("button", { name: "Bản trước" }).click();
  await sameCanvas(page);
  expect((await attribute<Camera>(page, "camera-state")).position).toEqual(orbit.position);
  await page.getByRole("button", { name: "Nhìn trên" }).click();
  const top = await attribute<Camera>(page, "camera-state");
  finiteCamera(top);
  const hold = demo.plan.hold;
  const holdCorners = corners([-hold.length_mm / 2000, -0.14, -hold.width_mm / 2000], [hold.length_mm / 2000, hold.height_mm / 1000, hold.width_mm / 2000]);
  assertFramed(top, holdCorners);
  await page.getByRole("button", { name: "Nhìn mạn" }).click();
  const side = await attribute<Camera>(page, "camera-state");
  finiteCamera(side);
  assertFramed(side, holdCorners);
  expect(side.position).not.toEqual(top.position);
  await page.getByRole("button", { name: "Tập trung bó" }).click();
  const focused = await attribute<Camera>(page, "camera-state");
  finiteCamera(focused);
  expect(focused.target).not.toEqual(side.target);
  const selectedMesh = (await attribute<Mesh[]>(page, "meshes")).find((mesh) => mesh.id === "ST-001")!;
  assertFramed(focused, corners(selectedMesh.position.map((v, i) => v - selectedMesh.dimensions[i] / 2), selectedMesh.position.map((v, i) => v + selectedMesh.dimensions[i] / 2)));
  await page.getByRole("button", { name: "Vừa khung" }).click();
  const fitted = await attribute<Camera>(page, "camera-state");
  finiteCamera(fitted);
  assertFramed(fitted, corners([-hold.length_mm / 2000, -0.14, -hold.width_mm / 2000], [hold.length_mm / 2000, hold.height_mm / 1000, hold.width_mm / 2000]));
  await page.getByRole("button", { name: "Đặt lại góc nhìn" }).click();
  await sameCanvas(page);
  await page.screenshot({ path: evidencePath("sup01-synthetic-desktop.png"), fullPage: true });
});

test("VINAFCO material, visibility and case changes preserve one GLB and scene while source planner shows real cargo", async ({ page }) => {
  test.setTimeout(90_000);
  let modelRequests = 0;
  await page.route("**/api/vessels/vinafco268/model", async (route) => { modelRequests++; await route.continue(); });
  await page.goto(diag);
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await expect.poll(async () => (await attribute<Material[]>(page, "materials")).length).toBeGreaterThan(0);
  await rememberCanvas(page);
  const initialStats = await attribute<Stats>(page, "viewer-stats");
  const ghost = await attribute<Material[]>(page, "materials");
  expect(ghost.some((m) => m.ghost && m.opacity === 0.32 && !m.depthWrite)).toBe(true);
  expect(ghost.some((m) => !m.ghost && m.opacity === 1)).toBe(true);
  await page.getByRole("button", { name: "Vật liệu gốc" }).click();
  await expect.poll(async () => (await attribute<Material[]>(page, "materials")).every((m) => !m.ghost)).toBe(true);
  const original = await attribute<Material[]>(page, "materials");
  expect(original.filter((m) => ghost.find((g) => g.name === m.name)?.ghost).every((m) => m.opacity === 1 && m.depthWrite)).toBe(true);
  await page.getByRole("button", { name: "Thân mờ" }).click();
  await page.getByRole("button", { name: "Ẩn tàu" }).click();
  await page.getByRole("button", { name: "Hiện tàu" }).click();
  await page.getByLabel("Cấp tham chiếu").selectOption("VR-SI");
  await expect(canvas(page)).toHaveAttribute("data-draft-marker", /VR-SI/);
  await sameCanvas(page);
  expect(modelRequests).toBe(1);
  const afterCase = await attribute<Stats>(page, "viewer-stats");
  expect(afterCase.loads).toBe(initialStats.loads);
  expect(afterCase.assetIdentity).toBe(initialStats.assetIdentity);
  await postJson(page, "/api/pipe-list/preview", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
  await postJson(page, "/api/validate", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
  const preview = await postJson<{ evaluation: { plan: { placements: { unit_id: string }[] } } }>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  expect(preview.evaluation.plan.placements.length).toBeGreaterThan(0);
  await postJson(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  await expect.poll(async () => (await attribute<Mesh[]>(page, "meshes")).length).toBe(preview.evaluation.plan.placements.length);
  await sameCanvas(page);
  expect(modelRequests).toBe(1);
  const focusId = preview.evaluation.plan.placements[0].unit_id;
  await page.getByLabel("Nhóm nguồn").selectOption(`Sheet1-${focusId.split("-")[1]}`);
  await page.getByTestId(`unit-${focusId}`).getByRole("button").click();
  await expect(page.getByRole("button", { name: "Tập trung bó" })).toBeEnabled();
  await page.getByRole("button", { name: "Tập trung bó" }).click();
  const focused = await attribute<Camera>(page, "camera-state");
  finiteCamera(focused);
  const focusedMesh = (await attribute<Mesh[]>(page, "meshes")).find((mesh) => mesh.id === focusId)!;
  assertFramed(focused, corners(focusedMesh.position.map((v, i) => v - focusedMesh.dimensions[i] / 2), focusedMesh.position.map((v, i) => v + focusedMesh.dimensions[i] / 2)));
  await page.getByRole("button", { name: "Vừa khung" }).click();
  const fitted = await attribute<Camera>(page, "camera-state");
  const vessel = await attribute<{ min: number[]; max: number[] }>(page, "vessel-bounds");
  assertFramed(fitted, corners(vessel.min, vessel.max));
  await page.getByRole("region", { name: "Mô hình chất xếp" }).screenshot({ path: evidencePath("sup01-source-scene.png") });
  await page.screenshot({ path: evidencePath("sup01-source-desktop.png"), fullPage: true });
});

test("late obsolete model response is discarded after detaching the reference hold; repeated toggles keep resource plateau", async ({ page }) => {
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let requested = false;
  await page.route("**/api/vessels/vinafco268/model", async (route) => {
    requested = true;
    await gate;
    await route.continue();
  });
  await page.goto(diag);
  await rememberCanvas(page);
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await expect.poll(() => requested).toBe(true);
  await page.getByRole("button", { name: "Dùng hầm tự nhập" }).click();
  await expect(page.getByLabel("Tên hầm")).toBeVisible();
  release();
  await expect.poll(async () => (await attribute<Material[]>(page, "materials")).length).toBe(0);
  expect(await canvas(page).getAttribute("data-vessel-bounds")).toBeNull();
  expect(await canvas(page).getAttribute("data-draft-marker")).toBeNull();
  await sameCanvas(page);
  const beforeName = await attribute<Camera>(page, "camera-state");
  await page.getByLabel("Tên hầm").fill("SUP hold label");
  await postJson(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect((await attribute<Camera>(page, "camera-state")).position).toEqual(beforeName.position);
  await sameCanvas(page);
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await expect.poll(async () => (await attribute<Material[]>(page, "materials")).length).toBeGreaterThan(0);
  const plateau = await attribute<Stats>(page, "viewer-stats");
  for (let i = 0; i < 3; i++) {
    await page.getByRole("button", { name: "Vật liệu gốc" }).click();
    await page.getByRole("button", { name: "Thân mờ" }).click();
    await page.getByRole("button", { name: "Ẩn tàu" }).click();
    await page.getByRole("button", { name: "Hiện tàu" }).click();
    await page.getByLabel("Cấp tham chiếu").selectOption(i % 2 ? "VR-SII" : "VR-SI");
  }
  await sameCanvas(page);
  const after = await attribute<Stats>(page, "viewer-stats");
  expect(after.geometries).toBe(plateau.geometries);
  expect(after.textures).toBe(plateau.textures);
  expect(after.assetIdentity).toBe(plateau.assetIdentity);
  expect(after.loads).toBe(plateau.loads);
  writeFileSync(evidencePath("sup01-resource-diagnostics.json"), JSON.stringify({
    scenario: "late obsolete GLB response, detach, reattach, then three material/visibility/case cycles",
    before: plateau,
    after,
  }, null, 2) + "\n");
  await page.getByRole("button", { name: "Mặt bằng", exact: true }).click();
  await expect(canvas(page)).toHaveCount(0);
  await page.getByRole("button", { name: "3D", exact: true }).click();
  await expect(canvas(page)).toBeVisible();
  finiteCamera(await attribute<Camera>(page, "camera-state"));
});

test("mobile fit and WebGL context loss retain usable 2D selection with no horizontal overflow", async ({ page, request }) => {
  const demo = await (await request.get("/api/demo")).json() as { plan: { hold: { length_mm: number; width_mm: number; height_mm: number } } };
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(diag);
  await canvas(page).scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: "Vừa khung" }).click();
  const camera = await attribute<Camera>(page, "camera-state");
  finiteCamera(camera);
  const size = await canvas(page).evaluate((element) => [element.clientWidth, element.clientHeight]);
  expect(camera.aspect).toBeCloseTo(size[0] / size[1], 5);
  const hold = demo.plan.hold;
  assertFramed(camera, corners([-hold.length_mm / 2000, -0.14, -hold.width_mm / 2000], [hold.length_mm / 2000, hold.height_mm / 1000, hold.width_mm / 2000]));
  await page.getByRole("button", { name: "Nhìn trên" }).click();
  finiteCamera(await attribute<Camera>(page, "camera-state"));
  await canvas(page).evaluate((element) => element.dispatchEvent(new Event("webglcontextlost", { cancelable: true })));
  await expect(page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D")).toBeVisible();
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  await page.getByRole("button", { name: "Chọn PP-007" }).click();
  await expect(page.getByTestId("unit-PP-007")).toHaveAttribute("aria-selected", "true");
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: evidencePath("sup01-mobile-fallback.png"), fullPage: true });
});
