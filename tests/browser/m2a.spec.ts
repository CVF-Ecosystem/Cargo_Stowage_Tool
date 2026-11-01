import { evidencePath } from "./evidence";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";

type Plan = { contract_version: string; source: string; vessel: { case_id: string } | null; cargo_source: string; hold: { name: string; length_mm: number; width_mm: number; height_mm: number }; units: { id: string; mass_g: number; requirement: string }[]; placements: { unit_id: string; x_mm: number; y_mm: number }[] };
type Evaluation = { plan: Plan; status: string; summary: { manifest_mass_g: number; placed_mass_g: number }; issues: { code: string }[] };
type Saved = { id: string; name: string; created_utc: string; schema_version: string };
const header = "id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg";
const csv = `\uFEFF${header}\nCSV-001,"Bó, thép thanh",BAR_BUNDLE,required,6000,900,650,1234.567\nCSV-002,Bó ống,PIPE_BUNDLE,optional,6000,900,650,25.001\n`;
const responseJson = async <T,>(page: import("../../apps/frontend/node_modules/@playwright/test").Page, path: string, action: () => Promise<void>): Promise<T> => {
  const waiting = page.waitForResponse((r) => r.url().endsWith(path));
  await action();
  const response = await waiting;
  expect(response.ok()).toBe(true);
  return await response.json() as T;
};

test("manual empty plan, cargo, hold and placement persist as immutable checked snapshots", async ({ page, request }) => {
  await page.goto("/");
  const empty = await responseJson<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Phương án mới" }).click());
  expect(empty.plan.contract_version).toBe("scst.m2a.v1");
  expect(empty.plan.source).toBe("USER_ENTERED");
  expect(empty.plan.units).toHaveLength(0);
  expect(empty.status).toBe("DRAFT");
  expect(empty.issues.map((issue) => issue.code)).toContain("EMPTY_MANIFEST");
  await expect(page.getByTestId("manifest-mass")).toHaveText("0 tấn");
  await expect(page.getByRole("heading", { name: "Chưa chọn bó" })).toBeVisible();
  await page.getByLabel("Tên hầm").fill("Hầm kiểm thử tự nhập");
  await page.getByLabel("Hầm holdLength (cm)").fill("2000");
  await page.getByLabel("Hầm holdWidth (cm)").fill("800");
  await page.getByLabel("Hầm holdHeight (cm)").fill("500");
  const holdChecked = await responseJson<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(holdChecked.plan.hold).toMatchObject({ name: "Hầm kiểm thử tự nhập", length_mm: 20000, width_mm: 8000, height_mm: 5000 });

  await page.getByLabel("Bó mới id").fill("MAN-001");
  await page.getByLabel("Bó mới name").fill("Bó tự nhập");
  await page.getByLabel("Bó mới length").fill("600");
  await page.getByLabel("Bó mới width").fill("90");
  await page.getByLabel("Bó mới height").fill("65");
  await page.getByLabel("Bó mới mass").fill("1250.125");
  const added = await responseJson<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Thêm bó", exact: true }).click());
  expect(added.plan.units).toMatchObject([{ id: "MAN-001", mass_g: 1_250_125 }]);
  expect(added.plan.placements).toHaveLength(0);
  await expect(page.getByTestId("unit-MAN-001")).toContainText("Bắt buộc chưa xếp");
  const placed = await responseJson<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Đặt bó" }).click());
  expect(placed.plan.placements).toMatchObject([{ unit_id: "MAN-001", x_mm: 0, y_mm: 0 }]);
  await page.getByLabel("Tọa độ X (cm)").fill("100");
  const checked = await responseJson<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  expect(checked.plan.placements[0].x_mm).toBe(1000);
  await page.getByLabel("Tên phương án lưu").fill(`Browser manual ${Date.now()}`);
  const first = await responseJson<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  expect(first.schema_version).toBe("scst.saved-plan.v1");
  const second = await responseJson<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  expect(second.id).not.toBe(first.id);
  const original = (await (await request.get(`/api/snapshots/${first.id}`)).json()) as Evaluation;
  expect(original.plan.hold).toEqual(checked.plan.hold);
  expect(original.plan.units).toEqual(checked.plan.units);
  expect(original.plan.placements).toEqual(checked.plan.placements);

  await page.reload();
  await expect(page.getByLabel("Phương án đã lưu").locator(`option[value="${first.id}"]`)).toHaveCount(1);
  await page.getByLabel("Phương án đã lưu").selectOption(first.id);
  const reopened = await responseJson<Evaluation>(page, `/api/snapshots/${first.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(reopened.plan).toEqual(original.plan);
  await expect(page.getByTestId("unit-MAN-001")).toContainText("100, 0");
  await expect(page.getByLabel("Tên hầm")).toHaveValue("Hầm kiểm thử tự nhập");
  await page.screenshot({ path: evidencePath("m2a.spec-browser-manual-saved.png"), fullPage: true });

  await page.getByRole("button", { name: "Bỏ vị trí" }).click();
  await expect(page.getByTestId("unit-MAN-001")).toContainText("Bắt buộc chưa xếp");
  await page.getByRole("button", { name: "Xóa bó" }).click();
  await expect(page.getByTestId("unit-MAN-001")).toHaveCount(0);
  await expect(page.getByTestId("status")).toHaveText("DRAFT");
  await page.getByRole("button", { name: "Bản trước" }).click();
  await expect(page.getByTestId("unit-MAN-001")).toHaveCount(1);
});

test("CSV preview reports row errors, preserves workspace, then atomically replaces cargo with exact grams", async ({ page }) => {
  await page.goto("/");
  const original = await page.getByTestId("manifest-mass").textContent();
  const invalid = `${header}\nCSV-001,Wrong,BAR_BUNDLE,required,6000,900,650,1.2345\nCSV-001,Duplicate,PIPE_BUNDLE,optional,6000,900,650,2\n`;
  await page.getByLabel("Nội dung CSV").fill(invalid);
  const rejected = await responseJson<{ valid: boolean; errors: { row: number; field: string }[]; candidate: null }>(page, "/api/import/csv/preview", () => page.getByRole("button", { name: "Kiểm CSV" }).click());
  expect(rejected.valid).toBe(false);
  expect(rejected.candidate).toBeNull();
  expect(rejected.errors).toEqual(expect.arrayContaining([{ row: 2, field: "mass_kg", message: expect.any(String) }, { row: 3, field: "id", message: expect.any(String) }]));
  await expect(page.getByText(/Dòng 2 · mass_kg/)).toBeVisible();
  await expect(page.getByText(/Dòng 3 · id/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Áp dụng CSV" })).toBeDisabled();
  await expect(page.getByTestId("manifest-mass")).toHaveText(original!);
  await expect(page.getByTestId("unit-ST-001")).toHaveCount(1);

  await page.getByLabel("Nội dung CSV").fill(csv);
  const preview = await responseJson<{ valid: boolean; count: number; total_mass_g: number; candidate: Plan }>(page, "/api/import/csv/preview", () => page.getByRole("button", { name: "Kiểm CSV" }).click());
  expect(preview.valid).toBe(true);
  expect(preview.count).toBe(2);
  expect(preview.total_mass_g).toBe(1_259_568);
  expect(preview.candidate.placements).toHaveLength(0);
  await expect(page.getByTestId("unit-ST-001")).toHaveCount(1);
  await page.getByLabel("Nội dung CSV").fill(csv.replace("Bó ống", "Bó ống kiểm"));
  await expect(page.getByRole("button", { name: "Áp dụng CSV" })).toBeDisabled();
  const refreshed = await responseJson<{ valid: boolean; errors: { row: number; field: string; message: string }[] }>(page, "/api/import/csv/preview", () => page.getByRole("button", { name: "Kiểm CSV" }).click());
  expect(refreshed.valid, JSON.stringify(refreshed.errors)).toBe(true);
  await expect(page.getByRole("button", { name: "Áp dụng CSV" })).toBeEnabled();
  const applied = await responseJson<Evaluation>(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng CSV" }).click());
  expect(applied.plan.contract_version).toBe("scst.m2a.v1");
  expect(applied.plan.cargo_source).toBe("USER_ENTERED");
  expect(applied.plan.units.map((item) => item.id)).toEqual(["CSV-001", "CSV-002"]);
  expect(applied.summary.manifest_mass_g).toBe(1_259_568);
  expect(applied.plan.placements).toHaveLength(0);
  await expect(page.getByTestId("unit-ST-001")).toHaveCount(0);
  await expect(page.getByTestId("unit-CSV-001")).toContainText("Bó thép thanh");
  await page.screenshot({ path: evidencePath("m2a.spec-browser-csv-import.png"), fullPage: true });
});

test("saved reference plan reopens after reload; network failure and mobile WebGL fallback keep input", async ({ page }) => {
  await page.goto("/?viewerDiagnostics=1");
  await page.getByRole("button", { name: "Xem VINAFCO 268" }).click();
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268" })).toBeVisible();
  await expect(page.getByLabel("Giới hạn chứng nhận (kg)")).toHaveJSProperty("readOnly", true);
  await page.getByLabel("Tên phương án lưu").fill(`Browser reference ${Date.now()}`);
  const saved = await responseJson<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await page.reload();
  await expect(page.getByLabel("Phương án đã lưu").locator(`option[value="${saved.id}"]`)).toHaveCount(1);
  await page.getByLabel("Phương án đã lưu").selectOption(saved.id);
  const reopened = await responseJson<Evaluation>(page, `/api/snapshots/${saved.id}`, () => page.getByRole("button", { name: "Mở phương án" }).click());
  expect(reopened.plan.source).toBe("MIXED_REFERENCE");
  expect(reopened.plan.vessel?.case_id).toBe("VR-SII");
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268" })).toBeVisible();
  await expect(page.getByTestId("three-canvas")).toHaveAttribute("data-vessel-bounds", /min/);
  await page.getByRole("button", { name: "Dùng hầm tự nhập" }).click();
  await expect(page.getByLabel("Tên hầm")).toBeVisible();
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268" })).toHaveCount(0);
  await page.getByRole("button", { name: "Bản trước" }).click();
  await expect(page.getByRole("region", { name: "Thông số VINAFCO 268" })).toBeVisible();

  const mass = page.getByLabel("Khối lượng bó (kg)");
  const prior = await mass.inputValue();
  await mass.fill("2500.001");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.route("**/api/validate", (route) => route.abort("failed"));
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(mass).toHaveValue("2500.001");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.unroute("**/api/validate");
  await mass.fill(prior);

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
  await page.getByRole("button", { name: "Mở phương án" }).click();
  await expect(page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D")).toBeVisible();
  await expect(page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)).toBe(false);
  await page.screenshot({ path: evidencePath("m2a.spec-browser-mobile-reference-fallback.png"), fullPage: true });
});

test("delayed preview, save and open cannot overwrite newer edits or selection", async ({ page, request }) => {
  await page.goto("/");
  const mass = page.getByLabel("Khối lượng bó (kg)");
  const original = await mass.inputValue();
  const row = page.getByTestId("unit-ST-001");

  let releasePreview: () => void = () => {};
  const previewGate = new Promise<void>((resolve) => { releasePreview = resolve; });
  let previewReceived = false;
  await page.route("**/api/import/csv/preview", async (route) => {
    const backend = await route.fetch();
    previewReceived = true;
    await previewGate;
    await route.fulfill({ response: backend });
  });
  await page.getByLabel("Nội dung CSV").fill(csv);
  await page.getByRole("button", { name: "Kiểm CSV" }).click();
  await expect.poll(() => previewReceived).toBe(true);
  await mass.fill("2500.001");
  releasePreview();
  await expect(page.getByRole("alert")).toContainText("Dữ liệu đổi trong lúc kiểm CSV");
  await expect(page.getByRole("button", { name: "Áp dụng CSV" })).toBeDisabled();
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await expect(mass).toHaveValue("2500.001");
  await expect(row).toContainText("2.500 kg");
  await page.unroute("**/api/import/csv/preview");
  await mass.fill(original);
  await expect(page.getByTestId("status")).not.toHaveText("STALE");

  let releaseSave: () => void = () => {};
  const saveGate = new Promise<void>((resolve) => { releaseSave = resolve; });
  let saveReceived = false;
  await page.route("**/api/snapshots", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const backend = await route.fetch();
    saveReceived = true;
    await saveGate;
    await route.fulfill({ response: backend });
  });
  await page.getByLabel("Tên phương án lưu").fill(`Browser delayed ${Date.now()}`);
  const saveResponse = page.waitForResponse((r) => r.url().endsWith("/api/snapshots") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Lưu phương án" }).click();
  await expect.poll(() => saveReceived).toBe(true);
  await mass.fill("2500.002");
  releaseSave();
  const saved = (await (await saveResponse).json()) as Saved;
  const checked = (await (await request.get(`/api/snapshots/${saved.id}`)).json()) as Evaluation;
  expect(checked.plan.units.find((item) => item.id === "ST-001")!.mass_g).toBe(2_500_000);
  await expect(mass).toHaveValue("2500.002");
  await expect(page.getByTestId("status")).toHaveText("STALE");
  await page.unroute("**/api/snapshots");

  await page.reload();
  await expect(page.getByLabel("Phương án đã lưu").locator(`option[value="${saved.id}"]`)).toHaveCount(1);
  await page.getByLabel("Phương án đã lưu").selectOption(saved.id);
  let releaseOpen: () => void = () => {};
  const openGate = new Promise<void>((resolve) => { releaseOpen = resolve; });
  let openReceived = false;
  await page.route(`**/api/snapshots/${saved.id}`, async (route) => {
    const backend = await route.fetch();
    openReceived = true;
    await openGate;
    await route.fulfill({ response: backend });
  });
  await page.getByRole("button", { name: "Mở phương án" }).click();
  await expect.poll(() => openReceived).toBe(true);
  await page.getByTestId("unit-ST-002").getByRole("button").click();
  releaseOpen();
  await expect(page.getByRole("alert")).toContainText("Dữ liệu đổi trong lúc mở");
  await expect(page.getByTestId("unit-ST-002")).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("status")).not.toHaveText("STALE");
});
