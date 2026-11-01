/* Same-environment before/after observation; execute from the project root with `node docs/reviews/SCST_SUP_01_EVIDENCE/browser/viewer-measure.cjs <baseline|candidate>`. */
const { chromium } = require("../../../../apps/frontend/node_modules/@playwright/test");
const cp = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const root = path.resolve(__dirname, "../../../..");
const label = process.argv[2];
if (!["baseline", "candidate"].includes(label)) throw new Error("Use baseline or candidate");
const base = "http://127.0.0.1:8766";
const dataDir = fs.mkdtempSync(path.join(os.tmpdir(), `scst-sup01-${label}-`));
const started = process.hrtime.bigint();
const ms = () => Number(process.hrtime.bigint() - started) / 1e6;
const duration = async (action) => { const t = ms(); const result = await action(); return { ms: Math.round((ms() - t) * 100) / 100, result }; };
const metrics = { label, asset: fs.readdirSync(path.join(root, "apps/frontend/dist/assets")).find((name) => /^index-.*\.js$/.test(name)), browser: "", platform: process.platform, viewport: { width: 1440, height: 1100 }, runs: [] };

async function waitHealth() {
  const deadline = Date.now() + 30000;
  while (Date.now() < deadline) {
    try { const response = await fetch(`${base}/api/health`); if (response.ok) return; } catch {}
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error("isolated server health timeout");
}
async function post(page, ending, action) {
  const waiting = page.waitForResponse((r) => r.url().endsWith(ending) && r.request().method() === "POST");
  await action();
  const response = await waiting;
  if (!response.ok()) throw new Error(`${ending}: ${response.status()}`);
  return response.json();
}
async function canvasToken(page, name) {
  const canvas = page.getByTestId("three-canvas");
  await canvas.waitFor();
  await canvas.evaluate((element, token) => { element.dataset.measureToken = token; }, name);
  return canvas;
}
async function hasToken(page, name) {
  return page.getByTestId("three-canvas").getAttribute("data-measure-token").then((value) => value === name);
}
async function runOnce(browser, index) {
  const page = await browser.newPage({ viewport: metrics.viewport });
  const record = { index, synthetic: {}, vessel: {}, source: {}, errors: [] };
  let modelRequests = 0;
  page.on("request", (request) => { if (request.url().endsWith("/api/vessels/vinafco268/model")) modelRequests++; });
  page.on("pageerror", (error) => record.errors.push(error.message));
  try {
    const opened = await duration(async () => { await page.goto(`${base}/?viewerDiagnostics=1`); await page.getByTestId("status").waitFor(); await page.getByTestId("three-canvas").waitFor(); });
    record.synthetic.openMs = opened.ms;
    if (index === 0) record.userAgent = await page.evaluate(() => navigator.userAgent);
    const canvas = await canvasToken(page, `synthetic-${index}`);
    const firstCamera = await canvas.getAttribute("data-camera");
    const orbit = await duration(async () => {
      await canvas.scrollIntoViewIfNeeded();
      const box = await canvas.boundingBox();
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 80, box.y + box.height / 2 + 25, { steps: 5 });
      await page.mouse.up();
      await page.waitForFunction((old) => document.querySelector('[data-testid="three-canvas"]')?.getAttribute("data-camera") !== old, firstCamera);
    });
    record.synthetic.orbitMs = orbit.ms;
    const orbitCamera = await canvas.getAttribute("data-camera");
    await page.getByLabel("Tọa độ X (cm)").fill("50.1");
    const applied = await duration(() => post(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click()));
    record.synthetic.applyMs = applied.ms;
    record.synthetic.canvasRetainedApply = await hasToken(page, `synthetic-${index}`);
    record.synthetic.cameraRetainedApply = (await page.getByTestId("three-canvas").getAttribute("data-camera")) === orbitCamera;
    const undone = await duration(() => post(page, "/api/validate", () => page.getByRole("button", { name: "Bản trước" }).click()));
    record.synthetic.undoMs = undone.ms;
    record.synthetic.canvasRetainedUndo = await hasToken(page, `synthetic-${index}`);

    const vessel = await duration(async () => {
      await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
      await page.getByRole("region", { name: "Thông số VINAFCO 268" }).waitFor();
      await page.waitForFunction(() => !!document.querySelector('[data-testid="three-canvas"]')?.getAttribute("data-vessel-bounds"));
    });
    record.vessel.openMs = vessel.ms;
    await canvasToken(page, `vessel-${index}`);
    const beforeVisibility = modelRequests;
    const hide = await duration(() => page.getByRole("button", { name: "Ẩn tàu" }).click());
    const show = await duration(() => page.getByRole("button", { name: "Hiện tàu" }).click());
    record.vessel.hideMs = hide.ms; record.vessel.showMs = show.ms;
    record.vessel.canvasRetainedVisibility = await hasToken(page, `vessel-${index}`);
    record.vessel.modelRequestsVisibility = modelRequests - beforeVisibility;
    record.vessel.modelRequestsTotal = modelRequests;

    const list = await duration(async () => {
      await post(page, "/api/pipe-list/preview", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
      return post(page, "/api/validate", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
    });
    record.source.loadMs = list.ms; record.source.unitCount = list.result.plan.units.length;
    await page.getByLabel("Giới hạn chuyến (kg)").fill("3517500");
    await post(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
    const preview = await duration(() => post(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click()));
    record.source.previewMs = preview.ms;
    const plan = await duration(() => post(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click()));
    record.source.applyMs = plan.ms;
    record.source.placedCount = plan.result.summary.placed_count;
    record.source.unplacedCount = plan.result.plan.units.length - plan.result.summary.placed_count;
    await page.waitForFunction((count) => { const text = document.querySelector('[data-testid="three-canvas"]')?.getAttribute("data-meshes"); return !!text && JSON.parse(text).length === count; }, record.source.placedCount);
    const sourceCanvas = await canvasToken(page, `source-${index}`);
    const sourceCamera = await sourceCanvas.getAttribute("data-camera");
    const sourceOrbit = await duration(async () => {
      await sourceCanvas.scrollIntoViewIfNeeded(); const box = await sourceCanvas.boundingBox();
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down(); await page.mouse.move(box.x + box.width / 2 + 60, box.y + box.height / 2 + 20, { steps: 5 }); await page.mouse.up();
      await page.waitForFunction((old) => document.querySelector('[data-testid="three-canvas"]')?.getAttribute("data-camera") !== old, sourceCamera);
    });
    record.source.orbitMs = sourceOrbit.ms;
  } catch (error) { record.errors.push(String(error.stack || error)); }
  finally { await page.close(); }
  return record;
}

(async () => {
  const python = path.join(root, ".venv/Scripts/python.exe");
  const server = cp.spawn(python, ["-m", "uvicorn", "app.main:app", "--app-dir", path.join(root, "services/backend"), "--host", "127.0.0.1", "--port", "8766"], { cwd: root, env: { ...process.env, SCST_DATA_DIR: dataDir }, stdio: "ignore", windowsHide: true });
  let browser;
  try {
    await waitHealth(); browser = await chromium.launch({ headless: true }); metrics.browser = browser.version();
    for (let i = 0; i < 3; i++) metrics.runs.push(await runOnce(browser, i + 1));
  } finally {
    if (browser) await browser.close();
    server.kill();
    metrics.elapsedMs = Math.round(ms());
    metrics.isolatedDataDir = dataDir;
    fs.writeFileSync(path.join(__dirname, `viewer-${label}.json`), JSON.stringify(metrics, null, 2) + "\n");
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
