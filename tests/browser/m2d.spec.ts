import { spawn, type ChildProcess } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { inflateSync } from "node:zlib";
import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Page } from "../../apps/frontend/node_modules/@playwright/test";

// M2d D2/D3/D4 browser checks: saved-plan report page, XLSX download, print/PDF and recheck after a new revision.
// The M2D-05 flow creates a cargo revision. Specs that sort after this file (pipe-list, sup01) expect the shared suite DB
// to be at R0000, so that flow runs on its own backend with its own temporary SCST_DATA_DIR (same command shape as the
// Playwright webServer; SCST_TEST_PYTHON overrides the interpreter). The other cases use the shared server read-only.

type Evaluation = { plan: { placements: { unit_id: string }[] }; summary: { placed_count: number; placed_mass_g: number } };
type Preview = { evaluation: Evaluation; unplaced: { unit_id: string }[] };
type Saved = { id: string };
type Notice = { code: string; message: string };
type Unit = {
  id: string;
  name: string;
  mass_g: number;
  dimensions_um: number[];
  status: "PLACED" | "UNPLACED" | "EXCLUDED";
  placement: { x_mm: number; y_mm: number; z_mm: number } | null;
};
type TotalKey = "unit_count" | "placed_count" | "unplaced_count" | "excluded_count" | "manifest_mass_g" | "placed_mass_g" | "remaining_capacity_g";
type Report = {
  report_sha256: string;
  header: { plan_name: string; snapshot_id: string };
  notices: Notice[];
  totals: Record<TotalKey, number>;
  units: Unit[];
  cargo: { recheck: { status: string } };
};


const PRIVATE_PORT = 8768;
const PRIVATE_BASE = `http://127.0.0.1:${PRIVATE_PORT}`;
const python = () => process.env.SCST_TEST_PYTHON ?? (process.platform === "win32" ? "..\\..\\.venv\\Scripts\\python.exe" : "python");

async function privateServer(): Promise<{ stop: () => void }> {
  const dataDir = mkdtempSync(join(tmpdir(), "scst-m2d-"));
  const child: ChildProcess = spawn(python(), ["-m", "uvicorn", "app.main:app", "--app-dir", "../../services/backend", "--host", "127.0.0.1", "--port", String(PRIVATE_PORT)],
    { env: { ...process.env, SCST_DATA_DIR: dataDir }, stdio: "ignore" });
  const stop = () => { child.kill(); try { rmSync(dataDir, { recursive: true, force: true }); } catch { /* temp dir */ } };
  for (let i = 0; i < 150; i++) {
    try { if ((await fetch(`${PRIVATE_BASE}/api/health`)).ok) return { stop }; } catch { /* not up yet */ }
    await new Promise((r) => setTimeout(r, 200));
  }
  stop();
  throw new Error("private M2d backend did not start");
}

const COUNT_KEYS: TotalKey[] = ["unit_count", "placed_count", "unplaced_count", "excluded_count"];
const MASS_KEYS: TotalKey[] = ["manifest_mass_g", "placed_mass_g", "remaining_capacity_g"];

// PDF text is compared with whitespace, soft hyphens and private-use code points removed on both sides.
// Chromium interleaves private-use glyph code points (U+E000-U+F8FF) between glyphs; without them the
// SOURCE_WARNING notice does not match in this run.
const norm = (s: string) => s.replace(/[\s­--]+/g, "");

async function postResult<T>(page: Page, path: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((response) => response.url().endsWith(path) && response.request().method() === "POST");
  await action();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return (await response.json()) as T;
}

async function loadPipeList(page: Page): Promise<Evaluation> {
  await postResult<Evaluation>(page, "/api/pipe-list/preview", () => page.getByRole("button", { name: "Xem trước list ống" }).click());
  return postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click());
}

async function getJson<T>(request: APIRequestContext, path: string): Promise<T> {
  const response = await request.get(path);
  expect(response.ok()).toBe(true);
  return (await response.json()) as T;
}

async function saveDemoSnapshot(request: APIRequestContext, name: string): Promise<Saved> {
  const demo = await getJson<{ plan: unknown }>(request, "/api/demo");
  const response = await request.post("/api/snapshots", { data: { name, plan: demo.plan } });
  expect(response.ok()).toBe(true);
  return (await response.json()) as Saved;
}

// Verbatim from the verified Chromium PDF text extractor (tests only; the require.main block is dropped).
// Typed minimally: non-null assertions and a typed escape table are the only changes.
type PdfFont = { two: boolean; map: Map<number, string> };
type PdfObj = { dict: string; data: Buffer | null };

function pdfText(buf: Buffer): string {
  const s = buf.toString("latin1");
  const objs = new Map<number, PdfObj>();
  const re = /(\d+) 0 obj\s*/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(s))) {
    const start = m.index + m[0].length;
    const dictEnd = s.indexOf("stream", start);
    const end = s.indexOf("endobj", start);
    let dict = s.slice(start, end), data: Buffer | null = null;
    if (dictEnd !== -1 && dictEnd < end) {
      dict = s.slice(start, dictEnd);
      const len = Number((/\/Length (\d+)(?! 0 R)/.exec(dict) || [])[1]);
      let p = dictEnd + 6; if (s[p] === "\r") p++; if (s[p] === "\n") p++;
      let raw = buf.subarray(p, Number.isFinite(len) ? p + len : s.indexOf("endstream", p));
      data = /FlateDecode/.test(dict) ? inflateSync(raw) : raw;
      re.lastIndex = p + raw.length;
    } else re.lastIndex = end;
    objs.set(Number(m[1]), { dict, data });
  }
  const ref = (dict: string, key: string): number | null => { const r = new RegExp(`/${key} (\\d+) 0 R`).exec(dict); return r ? Number(r[1]) : null; };
  const hexText = (h: string): string => { let out = ""; for (let i = 0; i + 4 <= h.length; i += 4) out += String.fromCharCode(parseInt(h.slice(i, i + 4), 16)); return out; };
  const fonts = new Map<number, PdfFont>();
  const font = (n: number): PdfFont => {
    if (fonts.has(n)) return fonts.get(n)!;
    const o = objs.get(n)!, map = new Map<number, string>();
    const two = /\/Subtype \/Type0/.test(o.dict);
    const tu = ref(o.dict, "ToUnicode");
    if (tu !== null) {
      const c = objs.get(tu)!.data!.toString("latin1");
      for (const blk of c.matchAll(/beginbfchar([\s\S]*?)endbfchar/g))
        for (const x of blk[1].matchAll(/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/g)) map.set(parseInt(x[1], 16), hexText(x[2]));
      for (const blk of c.matchAll(/beginbfrange([\s\S]*?)endbfrange/g))
        for (const x of blk[1].matchAll(/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<[0-9A-Fa-f]+>|\[[^\]]*\])/g)) {
          const a = parseInt(x[1], 16), b = parseInt(x[2], 16);
          if (x[3].startsWith("[")) [...x[3].matchAll(/<([0-9A-Fa-f]+)>/g)].forEach((y, i) => map.set(a + i, hexText(y[1])));
          else { const h = x[3].slice(1, -1); const base = parseInt(h, 16); for (let k = a; k <= b; k++) map.set(k, hexText((base + k - a).toString(16).padStart(h.length, "0"))); }
        }
    }
    const f = { two, map }; fonts.set(n, f); return f;
  };
  const decode = (bytes: ArrayLike<number>, f: PdfFont): string => { let out = ""; const w = f.two ? 2 : 1; for (let i = 0; i + w <= bytes.length; i += w) { const code = w === 2 ? bytes[i] * 256 + bytes[i + 1] : bytes[i]; out += f.map.get(code) ?? (!f.two && code >= 32 && code < 127 ? String.fromCharCode(code) : ""); } return out; };
  const literal = (t: string): number[] => { const b: number[] = []; for (let i = 0; i < t.length; i++) { let ch = t[i]; if (ch === "\\") { const n = t[++i]; if (/[0-7]/.test(n)) { let o = n; while (o.length < 3 && /[0-7]/.test(t[i + 1])) o += t[++i]; b.push(parseInt(o, 8)); continue; } const esc: Record<string, number> = { n: 10, r: 13, t: 9, b: 8, f: 12 }; b.push(esc[n] ?? n.charCodeAt(0)); continue; } b.push(ch.charCodeAt(0)); } return b; };
  let text = "";
  for (const [, o] of objs) {
    if (!/\/Type \/Page\b/.test(o.dict) || /\/Type \/Pages/.test(o.dict)) continue;
    const res = ref(o.dict, "Resources"); const resDict = res !== null ? objs.get(res)!.dict : o.dict;
    const fontMap = new Map<string, number>([...resDict.matchAll(/\/(F\d+) (\d+) 0 R/g)].map((x): [string, number] => [x[1], Number(x[2])]));
    const cs = [...(/\/Contents\s*(\[[^\]]*\]|\d+ 0 R)/.exec(o.dict)?.[1].matchAll(/(\d+) 0 R/g) ?? [])].map((x) => Number(x[1]));
    for (const c of cs) {
      const body = objs.get(c)!.data!.toString("latin1");
      let f: PdfFont | null = null;
      for (const t of body.matchAll(/\/(F\d+) [\d.]+ Tf|<([0-9A-Fa-f]*)>|\(((?:\\.|[^\\)])*)\)|(T\*|Td|TD|')|(BT|ET)/g)) {
        if (t[1]) f = font(fontMap.get(t[1])!);
        else if (t[2] !== undefined && f) text += decode(Buffer.from(t[2], "hex"), f);
        else if (t[3] !== undefined && f) text += decode(Buffer.from(literal(t[3])), f);
        else if (t[4] || t[5]) text += "\n";
      }
    }
  }
  return text;
}

test("M2D-05 flow: save, report, XLSX, print, PDF, then a new revision flags NEEDS_RECHECK", async ({ page, playwright }) => {
  test.setTimeout(240_000);
  const server = await privateServer();
  const request = await playwright.request.newContext({ baseURL: PRIVATE_BASE });
  try {
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();
  const name = `M2d báo cáo ${tag}`;

  await page.goto(`${PRIVATE_BASE}/`);
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await loadPipeList(page);
  const preview = await postResult<Preview>(page, "/api/planner/preview", () => page.getByRole("button", { name: "Xếp thử tự động" }).click());
  expect(preview.evaluation.plan.placements.length).toBeGreaterThan(0);
  await postResult<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng xếp thử" }).click());
  await page.getByLabel("Tên phương án lưu").fill(name);
  const saved = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  const planBefore = JSON.stringify((await getJson<Evaluation>(request, `/api/snapshots/${saved.id}`)).plan);

  await page.reload();
  await page.getByLabel("Phương án đã lưu").selectOption(saved.id);
  const exportLink = page.getByRole("link", { name: "Xuất báo cáo" });
  await expect(exportLink).toHaveAttribute("href", `#/report/${saved.id}`);
  const [report] = await Promise.all([page.context().waitForEvent("page"), exportLink.click()]);
  report.on("pageerror", (e) => pageErrors.push(String(e)));

  // Page content against the JSON model (D1/D4).
  await expect(report.getByTestId("report-plan-name")).toHaveText(name);
  const model = await getJson<Report>(request, `/api/snapshots/${saved.id}/report`);
  expect(model.header.plan_name).toBe(name);
  await expect(report.locator('[data-testid="report-notices"] li')).toHaveText(model.notices.map((n) => n.message));
  for (const n of model.notices) await expect(report.getByTestId(`notice-${n.code}`)).toHaveText(n.message);
  expect(model.notices.map((n) => n.code)).toEqual(expect.arrayContaining(["GEOMETRY_UNVERIFIED", "SINGLE_LAYER", "PACKING_DERIVED", "SOURCE_WARNING"]));

  for (const key of [...COUNT_KEYS, ...MASS_KEYS]) {
    const row = report.getByTestId(`report-total-${key}`);
    const cell = MASS_KEYS.includes(key) ? row.locator("[data-exact]") : row.locator("td");
    await expect(cell).toHaveText(String(model.totals[key]));
  }

  await expect(report.locator('tr[data-testid^="report-unit-"]')).toHaveCount(model.units.length);
  const rows = await report.evaluate(() =>
    Array.from(document.querySelectorAll('tr[data-testid^="report-unit-"]')).map((tr) => ({
      id: (tr.getAttribute("data-testid") ?? "").slice("report-unit-".length),
      mass: tr.getAttribute("data-mass-g"),
      dims: tr.getAttribute("data-dims-um"),
      x: tr.getAttribute("data-x-mm"),
      y: tr.getAttribute("data-y-mm"),
    })),
  );
  expect(rows).toEqual(
    model.units.map((u) => ({
      id: u.id,
      mass: String(u.mass_g),
      dims: u.dimensions_um.join(","),
      x: u.placement ? String(u.placement.x_mm) : null,
      y: u.placement ? String(u.placement.y_mm) : null,
    })),
  );

  // The plan SVG draws one rect per placed unit at the unit's placement (mm, user units of the viewBox).
  await expect(report.locator('[data-testid="report-plan-svg"] rect[data-unit]')).toHaveCount(model.totals.placed_count);
  const first = model.units.find((u) => u.status === "PLACED" && u.placement)!;
  const firstRect = report.locator(`[data-testid="report-plan-svg"] rect[data-unit="${first.id}"]`);
  await expect(firstRect).toHaveAttribute("x", String(first.placement!.x_mm));
  await expect(firstRect).toHaveAttribute("y", String(first.placement!.y_mm));

  await expect(report.getByTestId("report-3d-image")).toHaveAttribute("src", /^data:image\/png/, { timeout: 30_000 });
  await report.screenshot({ path: evidencePath("m2d-report-desktop.png"), fullPage: true });

  // XLSX download (D2.2): a zip, byte-equal to the API body.
  const [download] = await Promise.all([report.waitForEvent("download"), report.getByRole("link", { name: "Tải XLSX" }).click()]);
  const downloaded = readFileSync((await download.path())!);
  const xlsxResponse = await request.get(`/api/snapshots/${saved.id}/report.xlsx`);
  expect(xlsxResponse.ok()).toBe(true);
  const xlsxBody = await xlsxResponse.body();
  expect(downloaded.subarray(0, 2).toString("latin1")).toBe("PK");
  expect(downloaded.equals(xlsxBody)).toBe(true);
  // D2.2 contract is on the header: an ASCII filename plus the UTF-8 filename* parameter.
  const disposition = xlsxResponse.headers()["content-disposition"] ?? "";
  expect(disposition).toMatch(/^attachment; filename="[\x20-\x7e]+\.xlsx"; filename\*=UTF-8''/);
  // Browser-side name: RFC 6266 browsers prefer the UTF-8 filename* (needs a UTF-8 locale, e.g. LANG=C.UTF-8 on Linux).
  const utf8Name = decodeURIComponent(/filename\*=UTF-8''(.+)$/.exec(disposition)![1]);
  expect(utf8Name).toContain(name);
  expect(download.suggestedFilename()).toBe(utf8Name);

  // Print button calls window.print (stubbed to count calls).
  await report.evaluate(() => {
    (window as unknown as { __printed: number }).__printed = 0;
    window.print = () => {
      (window as unknown as { __printed: number }).__printed++;
    };
  });
  await report.getByRole("button", { name: "In / Lưu PDF" }).click();
  expect(await report.evaluate(() => (window as unknown as { __printed: number }).__printed)).toBe(1);

  // A4 PDF from the print media: real PDF, more than one page, notices and plan name present in the text.
  await report.emulateMedia({ media: "print" });
  const pdf = await report.pdf({ format: "A4", printBackground: true, path: evidencePath("m2d-report.pdf") });
  expect(pdf.subarray(0, 4).toString("latin1")).toBe("%PDF");
  expect((pdf.toString("latin1").match(/\/Type \/Page\b/g) ?? []).length).toBeGreaterThan(1);
  const text = norm(pdfText(pdf));
  expect(text).toContain(norm(name));
  for (const n of model.notices) expect(text).toContain(norm(n.message));

  // Exports only read: the saved plan JSON is unchanged.
  expect(JSON.stringify((await getJson<Evaluation>(request, `/api/snapshots/${saved.id}`)).plan)).toBe(planBefore);

  // A new revision that overrides a placed bundle makes the saved plan NEEDS_RECHECK.
  expect(model.cargo.recheck.status).toBe("CURRENT");
  const latestId = (await getJson<{ latest_revision_id: string }>(request, "/api/cargo-revisions")).latest_revision_id;
  const created = await request.post("/api/cargo-revisions", {
    data: {
      parent_revision_id: latestId,
      source: { kind: "FACTORY", reference: `M2D-${tag}`, received_date: "2026-11-04", note: "m2d" },
      changes: [{ type: "BUNDLE_OVERRIDE", bundle_id: first.id, confirmation: "CONFIRMED", set: { mass_g: first.mass_g + 1000 } }],
    },
  });
  expect(created.ok()).toBe(true);

  await report.reload();
  await expect(report.getByTestId("notice-NEEDS_RECHECK")).toBeVisible();
  await expect(report.getByTestId("report-recheck")).toContainText("Cần kiểm lại");
  const recheckModel = await getJson<Report>(request, `/api/snapshots/${saved.id}/report`);
  expect(recheckModel.cargo.recheck.status).toBe("NEEDS_RECHECK");
  expect(recheckModel.report_sha256).not.toBe(model.report_sha256);
  await expect(report.getByTestId("report-sha")).toHaveText(recheckModel.report_sha256);
  await expect(report.locator('[data-testid="report-notices"] li')).toHaveText(recheckModel.notices.map((n) => n.message));
  expect(JSON.stringify((await getJson<Evaluation>(request, `/api/snapshots/${saved.id}`)).plan)).toBe(planBefore);

  expect(pageErrors).toEqual([]);
  } finally {
    await request.dispose();
    server.stop();
  }
});

test("M2D-04 without WebGL: totals and notices stay, the 3D part is replaced by a note", async ({ page, request }) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (this: HTMLCanvasElement, type: string, ...args: unknown[]) {
      if (type.includes("webgl")) return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  const name = `M2d no-webgl ${Date.now()}`;
  const saved = await saveDemoSnapshot(request, name);
  await page.goto(`/#/report/${saved.id}`);
  await expect(page.getByTestId("report-plan-name")).toHaveText(name);
  await expect(page.getByTestId("report-3d-missing")).toBeVisible();
  await expect(page.getByTestId("report-3d-image")).toHaveCount(0);
  await expect(page.getByTestId("report-totals")).toBeVisible();
  await expect(page.getByTestId("report-notices")).toBeVisible();
});

test("M2D-04 390px: report reads without horizontal page overflow", async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const name = `M2d 390px ${Date.now()}`;
  const saved = await saveDemoSnapshot(request, name);
  await page.goto(`/#/report/${saved.id}`);
  await expect(page.getByTestId("report-plan-name")).toHaveText(name);
  await expect(page.getByTestId("report-notices")).toBeVisible();
  await expect(page.getByTestId("report-totals")).toBeVisible();
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(scrollWidth).toBeLessThanOrEqual(390 + 1);
  await page.screenshot({ path: evidencePath("m2d-report-390.png"), fullPage: true });
});

test("M2D-02 refusal: an unknown snapshot id shows an alert on the report page", async ({ page }) => {
  await page.goto("/#/report/00000000-0000-4000-8000-000000000000");
  await expect(page.getByRole("alert")).toContainText("Không tìm thấy");
});
