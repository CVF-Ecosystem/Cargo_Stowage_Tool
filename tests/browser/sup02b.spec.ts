import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Locator, Page } from "../../apps/frontend/node_modules/@playwright/test";
import { evidencePath } from "./evidence";

// SUP-02B S2B-05 (docs/specs/SCST_SUP_02B.md, D6): internal flow on the shared suite database.
// VINAFCO 268 is opened, a synthetic profile (JSON + box GLB built here at run time) is previewed,
// created, selected with a case, opened, saved, reloaded and reopened. Desktop 1440px and 390px.
// Every profile id is unique per run, so repeated runs against the shared DB never collide.

type Triple = [number, number, number];
type Bounds = { min: Triple; max: Triple; position: Triple };
type Marker = { caseId: string; y: number; draft: number };
type PlanShape = {
  hold: { length_mm: number; width_mm: number; height_mm: number };
  vessel: { vessel_id: string; case_id: string; profile_version?: number; profile_sha256?: string } | null;
};
type Evaluation = { plan: PlanShape; status: string };
type Profile = Record<string, unknown>;
type ListItem = { id: string; version: number; builtin: boolean; status: string; verification: string | null };
type Detail = { profile_sha256: string };

// Synthetic hold and GLB frames. Hold 20 m x 8 m x 4 m; GLB box x -15..15, y 0..6, z -5..5 (metres).
const HOLD_L_M = 20;
const HOLD_W_M = 8;
const TRANSLATION: Triple = [1, -1, 0];
const BOX_MIN: Triple = [-15, 0, -5];
const BOX_MAX: Triple = [15, 6, 5];
const HOLD_CORNERS_MM: Triple[] = [[0, 0, 0], [20000, 0, 0], [0, 8000, 0], [20000, 8000, 0]];

const tempDirs: string[] = [];
test.afterAll(() => {
  for (const dir of tempDirs) rmSync(dir, { recursive: true, force: true });
});

const newId = (tag: string) => `TEST-${Date.now().toString(36).toUpperCase()}${tag}`.slice(0, 32);

// Hold mm -> scene m: (x/1000 - L/2, z/1000, y/1000 - W/2); glb = scene - translation. Exact for these corners.
function holdMmToGlb(mm: Triple): Triple {
  const scene: Triple = [mm[0] / 1000 - HOLD_L_M / 2, mm[2] / 1000, mm[1] / 1000 - HOLD_W_M / 2];
  return [scene[0] - TRANSLATION[0], scene[1] - TRANSLATION[1], scene[2] - TRANSLATION[2]];
}

// One box mesh: 8 float32 POSITION vertices with accessor min/max, 12 triangles as uint16 indices, one BIN chunk.
function buildGlb(): Buffer {
  const positions: number[] = [];
  for (let i = 0; i < 8; i++) positions.push(i & 1 ? BOX_MAX[0] : BOX_MIN[0], i & 2 ? BOX_MAX[1] : BOX_MIN[1], i & 4 ? BOX_MAX[2] : BOX_MIN[2]);
  const triangles = [0, 2, 3, 0, 3, 1, 4, 5, 7, 4, 7, 6, 0, 4, 6, 0, 6, 2, 1, 3, 7, 1, 7, 5, 0, 1, 5, 0, 5, 4, 2, 6, 7, 2, 7, 3];
  const posBytes = Buffer.alloc(positions.length * 4);
  positions.forEach((v, i) => posBytes.writeFloatLE(v, i * 4));
  const idxBytes = Buffer.alloc(triangles.length * 2);
  triangles.forEach((v, i) => idxBytes.writeUInt16LE(v, i * 2));
  const bin = Buffer.concat([posBytes, idxBytes]); // 96 + 72 = 168 bytes, multiple of 4
  const gltf = {
    asset: { version: "2.0", generator: "sup02b-spec" },
    scene: 0,
    scenes: [{ nodes: [0] }],
    nodes: [{ mesh: 0 }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0 }, indices: 1, mode: 4 }] }],
    buffers: [{ byteLength: bin.length }],
    bufferViews: [
      { buffer: 0, byteOffset: 0, byteLength: posBytes.length, target: 34962 },
      { buffer: 0, byteOffset: posBytes.length, byteLength: idxBytes.length, target: 34963 },
    ],
    accessors: [
      { bufferView: 0, byteOffset: 0, componentType: 5126, count: 8, type: "VEC3", min: BOX_MIN, max: BOX_MAX },
      { bufferView: 1, byteOffset: 0, componentType: 5123, count: triangles.length, type: "SCALAR", min: [0], max: [7] },
    ],
  };
  let json = Buffer.from(JSON.stringify(gltf), "utf8");
  json = Buffer.concat([json, Buffer.alloc((4 - (json.length % 4)) % 4, 0x20)]); // JSON padded with spaces
  const binPadded = Buffer.concat([bin, Buffer.alloc((4 - (bin.length % 4)) % 4, 0)]); // BIN padded with zeros
  const header = Buffer.alloc(12);
  header.write("glTF", 0, "ascii");
  header.writeUInt32LE(2, 4);
  header.writeUInt32LE(12 + 8 + json.length + 8 + binPadded.length, 8);
  const jsonHead = Buffer.alloc(8);
  jsonHead.writeUInt32LE(json.length, 0);
  jsonHead.writeUInt32LE(0x4e4f534a, 4); // "JSON"
  const binHead = Buffer.alloc(8);
  binHead.writeUInt32LE(binPadded.length, 0);
  binHead.writeUInt32LE(0x004e4942, 4); // "BIN\0"
  return Buffer.concat([header, jsonHead, json, binHead, binPadded]);
}

// VesselProfileV1 body. `landmarkShiftX_m` moves the first landmark in the GLB frame (used for the FAIL case).
function buildProfile(id: string, name: string, landmarkShiftX_m = 0): Profile {
  const landmarks = HOLD_CORNERS_MM.map((mm, i) => {
    const glb = holdMmToGlb(mm);
    if (i === 0) glb[0] = glb[0] + landmarkShiftX_m;
    return { name: `Góc hầm ${i + 1}`, glb_m: glb, hold_mm: mm };
  });
  return {
    contract_version: "scst.vessel-profile.v1",
    id,
    version: 1,
    name,
    registration: "TEST-01",
    dimensions_m: { length: 30, beam: 10, depth: 6 },
    hold: { id: "HOLD-T1", name: "Hầm thử", length_mm: 20000, width_mm: 8000, height_mm: 4000, status: "ESTIMATED" },
    cases: [
      { id: "C1", cargo_mass_g: 40000000, draft_m: 3.5 },
      { id: "C2", cargo_mass_g: 50000000, draft_m: 4 },
    ],
    notes: ["Profile thử do test tạo."],
    provenance: {
      source_documents: [{ title: "Dữ liệu thử của test" }],
      field_status: { dimensions_m: "ESTIMATED", hold: "ESTIMATED", cases: "ESTIMATED" },
    },
    transform: { translation_m: [...TRANSLATION], yaw_deg: 0 },
    landmarks,
  };
}

function writeFixture(name: string, profile: Profile, glb: Buffer) {
  const dir = mkdtempSync(join(tmpdir(), "sup02b-"));
  tempDirs.push(dir);
  const jsonPath = join(dir, `${name}.json`);
  const glbPath = join(dir, `${name}.glb`);
  writeFileSync(jsonPath, JSON.stringify(profile, null, 2), "utf8");
  writeFileSync(glbPath, glb);
  return { jsonPath, glbPath };
}

async function postResult<T>(page: Page, path: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((response) => response.url().endsWith(path) && response.request().method() === "POST");
  await action();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return (await response.json()) as T;
}

async function readJsonAttr<T>(canvas: Locator, name: string): Promise<T | null> {
  const raw = await canvas.getAttribute(name);
  return raw === null ? null : (JSON.parse(raw) as T);
}

const panelOf = (page: Page) => page.getByRole("region", { name: "Tàu và hầm", exact: true });

// Sets both files, runs the preview and checks the landmark table. Create is enabled only after a valid preview.
async function previewProfile(page: Page, files: { jsonPath: string; glbPath: string }) {
  const form = page.getByRole("region", { name: "Nhập profile tàu", exact: true });
  await form.getByLabel("Tệp profile JSON", { exact: true }).setInputFiles(files.jsonPath);
  await form.getByLabel("Tệp GLB", { exact: true }).setInputFiles(files.glbPath);
  const create = form.getByRole("button", { name: "Tạo profile", exact: true });
  await expect(create).toBeDisabled();
  await form.getByRole("button", { name: "Xem trước kiểm", exact: true }).click();
  const preview = form.getByRole("region", { name: "Kết quả xem trước", exact: true });
  await expect(preview).toBeVisible();
  return { form, preview, create };
}

// Creates a version through the import form and returns the POST response body.
async function createProfile(page: Page, files: { jsonPath: string; glbPath: string }, id: string) {
  const { form, preview, create } = await previewProfile(page, files);
  await expect(preview).toContainText("Kết quả kiểm: PASS");
  await expect(create).toBeEnabled();
  const created = await postResult<{ id: string; version: number }>(page, "/api/vessel-profiles", () => create.click());
  expect(created.id).toBe(id);
  await expect(form.getByRole("status")).toContainText(`Đã tạo profile ${id} v1.`);
  return created;
}

test("S2B-05 desktop: VINAFCO open, import a synthetic profile, select case C2, save, reload and reopen", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  await page.setViewportSize({ width: 1440, height: 1100 });
  const id = newId("A");
  const glb = buildGlb();
  const files = writeFixture("desktop", buildProfile(id, "Sà lan thử"), glb);

  await page.goto("/?viewerDiagnostics=1");
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268", exact: true })).toBeVisible();

  // 1. preview: landmark table with four rows, containment, and create disabled until the preview is valid
  const panel = panelOf(page);
  const { preview, create } = await previewProfile(page, files);
  await expect(preview).toContainText("Kết quả kiểm: PASS");
  const table = preview.getByRole("table", { name: "Sai số landmark", exact: true });
  await expect(table.locator("tbody tr")).toHaveCount(4);
  await expect(table.locator("tbody tr").first()).toContainText("Đạt");
  await expect(preview).toContainText("Hộp bao GLB chứa hầm: có");
  await expect(create).toBeEnabled();

  // 2. create, then the new vessel is selectable
  const created = await postResult<{ id: string; version: number }>(page, "/api/vessel-profiles", () => create.click());
  expect(created).toMatchObject({ id, version: 1 });
  await expect(page.getByRole("region", { name: "Nhập profile tàu", exact: true }).getByRole("status")).toContainText(`Đã tạo profile ${id} v1.`);
  await panel.getByLabel("Chọn tàu", { exact: true }).selectOption(`${id}@1`);
  const caseSelect = panel.getByLabel("Trường hợp tải", { exact: true });
  await expect(caseSelect.locator('option[value="C2"]')).toHaveCount(1);
  await caseSelect.selectOption("C2");

  // 3. open: the case plan carries the hold and the profile binding; the viewer shows the transformed hull and marker
  const planPending = page.waitForResponse((r) => r.url().includes(`/api/vessel-profiles/${id}/1/cases/C2/plan`) && r.request().method() === "GET");
  await panel.getByRole("button", { name: "Mở tàu và trường hợp", exact: true }).click();
  const planResponse = await planPending;
  expect(planResponse.ok()).toBe(true);
  const casePlan = (await planResponse.json()) as Evaluation;
  expect(casePlan.plan.hold).toMatchObject({ length_mm: 20000, width_mm: 8000, height_mm: 4000 });
  expect(casePlan.plan.vessel).toMatchObject({
    vessel_id: id,
    case_id: "C2",
    profile_version: 1,
    profile_sha256: expect.stringMatching(/^[0-9a-f]{64}$/),
  });
  const detail = (await (await request.get(`/api/vessel-profiles/${id}/1`)).json()) as Detail;
  expect(casePlan.plan.vessel?.profile_sha256).toBe(detail.profile_sha256);

  await expect(page.getByRole("region", { name: "Thông số Sà lan thử", exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Thông số Sà lan thử", exact: true })).toContainText("C2 (đang mở)");

  const canvas = page.getByTestId("three-canvas");
  // The VINAFCO model was loaded before, so wait for this profile's bounds (position y -1, not VINAFCO's -0.832).
  await expect.poll(async () => (await readJsonAttr<Bounds>(canvas, "data-vessel-bounds"))?.position[1] ?? null, { timeout: 20_000 }).toBeCloseTo(-1, 3);
  const bounds = (await readJsonAttr<Bounds>(canvas, "data-vessel-bounds"))!;
  expect(bounds.position[0]).toBeCloseTo(1, 3);
  expect(bounds.position[1]).toBeCloseTo(-1, 3);
  expect(bounds.position[2]).toBeCloseTo(0, 3);
  expect(bounds.max[0] - bounds.min[0]).toBeCloseTo(30, 3);
  expect(bounds.max[1] - bounds.min[1]).toBeCloseTo(6, 3);
  expect(bounds.max[2] - bounds.min[2]).toBeCloseTo(10, 3);

  await expect.poll(async () => (await readJsonAttr<Marker>(canvas, "data-draft-marker"))?.caseId ?? null).toBe("C2");
  const marker = (await readJsonAttr<Marker>(canvas, "data-draft-marker"))!;
  expect(marker.draft).toBeCloseTo(4, 3);
  expect(marker.y).toBeCloseTo(3, 3); // draft 4 m minus translation -1 m
  await page.screenshot({ path: evidencePath("sup02b-desktop.png"), fullPage: true });

  // 4. registry and model bytes through the API
  const list = (await (await request.get("/api/vessel-profiles")).json()) as ListItem[];
  expect(list.find((item) => item.id === id && item.version === 1)).toMatchObject({ builtin: false, status: "AVAILABLE", verification: "PASS" });
  const model = await request.get(`/api/vessel-profiles/${id}/1/model`);
  expect(model.ok()).toBe(true);
  expect(model.headers()["content-type"]).toContain("model/gltf-binary");
  expect(Buffer.from(await model.body()).equals(glb)).toBe(true);

  // 5. save through the existing save control, reload, reopen through the existing open control
  const saveName = `S2B-05 ${id}`;
  await page.getByLabel("Tên phương án lưu", { exact: true }).fill(saveName);
  const saved = await postResult<{ id: string }>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án", exact: true }).click());
  await expect(page.getByTestId(`saved-item-${saved.id}`)).toContainText(saveName);

  await page.reload();
  const savedSelect = page.getByLabel("Phương án đã lưu", { exact: true });
  await expect(savedSelect.locator(`option[value="${saved.id}"]`)).toHaveCount(1);
  await savedSelect.selectOption(saved.id);
  const openPending = page.waitForResponse((r) => r.url().endsWith(`/api/snapshots/${saved.id}`) && r.request().method() === "GET");
  await page.getByRole("button", { name: "Mở phương án", exact: true }).click();
  const reopened = (await (await openPending).json()) as Evaluation;
  expect(reopened.plan.hold).toMatchObject({ length_mm: 20000, width_mm: 8000, height_mm: 4000 });
  expect(reopened.plan.vessel).toMatchObject({ vessel_id: id, case_id: "C2", profile_version: 1, profile_sha256: casePlan.plan.vessel?.profile_sha256 });

  await expect(page.getByRole("region", { name: "Thông số Sà lan thử", exact: true })).toBeVisible();
  await expect(panel.getByLabel("Chọn tàu", { exact: true })).toHaveValue(`${id}@1`);
  await expect.poll(async () => (await readJsonAttr<Bounds>(canvas, "data-vessel-bounds"))?.position[1] ?? null, { timeout: 20_000 }).toBeCloseTo(-1, 3);
  expect(pageErrors).toEqual([]);
});

test("S2B-05 390px: import panel previews, creates, opens a profile without horizontal overflow", async ({ page }) => {
  test.setTimeout(120_000);
  await page.setViewportSize({ width: 390, height: 844 });
  const id = newId("M");
  const files = writeFixture("mobile", buildProfile(id, "Sà lan 390"), buildGlb());

  await page.goto("/");
  const panel = panelOf(page);
  await panel.scrollIntoViewIfNeeded();
  await expect(panel.getByLabel("Chọn tàu", { exact: true })).toBeEnabled();

  const { form, preview, create } = await previewProfile(page, files);
  await expect(preview).toContainText("Kết quả kiểm: PASS");
  const table = preview.getByRole("table", { name: "Sai số landmark", exact: true });
  await expect(table.locator("tbody tr")).toHaveCount(4);
  await expect(preview).toContainText("Hộp bao GLB chứa hầm: có");

  // Controls of the import form stay inside the 390px viewport.
  for (const control of [
    form.getByLabel("Tệp profile JSON", { exact: true }),
    form.getByLabel("Tệp GLB", { exact: true }),
    form.getByRole("button", { name: "Xem trước kiểm", exact: true }),
    create,
  ]) {
    const box = await control.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(390 + 1);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);

  await expect(create).toBeEnabled();
  await postResult<{ id: string }>(page, "/api/vessel-profiles", () => create.click());
  await expect(form.getByRole("status")).toContainText(`Đã tạo profile ${id} v1.`);
  await panel.getByLabel("Chọn tàu", { exact: true }).selectOption(`${id}@1`);
  await panel.getByRole("button", { name: "Mở tàu và trường hợp", exact: true }).click();
  await expect(page.getByRole("region", { name: "Thông số Sà lan 390", exact: true })).toBeVisible();

  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: evidencePath("sup02b-390px.png"), fullPage: true });
});

test("S2B-05 landmark off by 2 mm previews FAIL, keeps create disabled and stores nothing", async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 1100 });
  const id = newId("F");
  const files = writeFixture("fail", buildProfile(id, "Sà lan lệch", -0.002), buildGlb());

  await page.goto("/");
  await expect(panelOf(page).getByLabel("Chọn tàu", { exact: true })).toBeEnabled();
  const { form, preview, create } = await previewProfile(page, files);

  await expect(preview).toContainText("Kết quả kiểm: FAIL");
  const table = preview.getByRole("table", { name: "Sai số landmark", exact: true });
  await expect(table.locator("tbody tr").first()).toContainText("Không đạt");
  await expect(preview).toContainText("Kiểm landmark hoặc hộp bao không đạt; profile này không được lưu.");
  await expect(create).toBeDisabled();
  await expect(form.getByRole("status")).toHaveCount(0);

  const list = (await (await request.get("/api/vessel-profiles")).json()) as ListItem[];
  expect(list.some((item) => item.id === id)).toBe(false);
  expect((await request.get(`/api/vessel-profiles/${id}/1`)).status()).toBe(404);
});
