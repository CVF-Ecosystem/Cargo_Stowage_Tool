import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Locator, Page } from "../../apps/frontend/node_modules/@playwright/test";
import { evidenceDir as baseEvidenceDir } from "./evidence";

// SUP-03 S3-05: derived packing views, picking, the 60 000 instance budget and the 390px flow.
// The suite shares one server/DB across spec files, so every revision id is derived from the live latest id.
// Packing is a read-only DERIVED view: every assertion reads it through the UI, the canvas diagnostics or the API.

const DATASET = "BALTIMORE-PIPE-V1-1";
const BUDGET_PIECES = 60000;
const evidenceDir = () => baseEvidenceDir();
const shotPage = async (page: Page, name: string) => {
  mkdirSync(evidenceDir(), { recursive: true });
  await page.screenshot({ path: resolve(evidenceDir(), name), fullPage: true });
};
const shotLocator = async (locator: Locator, name: string) => {
  mkdirSync(evidenceDir(), { recursive: true });
  await locator.screenshot({ path: resolve(evidenceDir(), name) });
};

type Stamp = { revision_id: string; source: null | { kind: string; reference: string; received_date: string; note: string }; confirmation: string };
type Group = {
  group_id: string; origin: string; bundle_count: number; pieces_per_bundle: number; dimensions_um: number[]; mass_g: number;
  outside_diameter_mm: string; wall_thickness_mm: string; dimension_warning: boolean; bundle_ids: string[];
  provenance: Record<string, Stamp>; overrides: unknown[];
};
type RevisionDetail = { revision_id: string; parent_revision_id: string | null; change_count: number; source: Stamp["source"]; bundle_count: number; groups: Group[] };
type RevisionList = { latest_revision_id: string; revisions: { revision_id: string }[] };
type Snapshot = {
  id: string; name: string; cargo_revision_id: string | null; recheck_status: string;
  added_count: number; removed_count: number; changed_count: number; placed_affected_count: number;
};
type Saved = { id: string };
type PlanJson = {
  contract_version: string;
  cargo_revision?: { revision_id: string } | null;
  units: { id: string; requirement: string; source_ref?: { group_id?: string } | null }[];
  placements: { unit_id: string; x_mm: number; y_mm: number; z_mm: number; yaw_deg: number }[];
  [key: string]: unknown;
};
type Evaluation = { plan: PlanJson };
type PackingCore = {
  status: "DETAILED" | "ENVELOPE_ONLY"; layout: string | null; columns: number; rows: number; od_um: number | null;
  pieces_source: number; pieces_placed: number; reasons: { code: string }[];
};
type GroupPacking = PackingCore & { group_id: string; bundle_packings: (PackingCore & { bundle_id: string })[] };
type RevisionPacking = { revision_id: string; groups: GroupPacking[] };
type PackingView = {
  view: string; detailedBundles: number; simplifiedBundles: number; envelopeBundles: number; envelopeOnlyBundles: number;
  pipeInstances: number; ringInstances: number; capped: boolean; buildMs: number; candidateBundles: number; totalBundles: number;
  budgetBoxBundles: number; budget: number; sceneUuid: string; packUuid: string;
};
type Diag = {
  stats: { sceneUuid: string; loads: number; assetIdentity: number } | null;
  meshes: { id: string; uuid: string }[];
  cameraState: unknown;
  packing: PackingView | null;
  projected: { id: string; x: number; y: number }[] | null;
};

const revisionNumber = (id: string) => Number(id.split("@R")[1]);
const revisionIdOf = (n: number) => `${DATASET}@R${String(n).padStart(4, "0")}`;

async function getRevisionList(request: APIRequestContext): Promise<RevisionList> {
  const r = await request.get("/api/cargo-revisions");
  expect(r.ok()).toBe(true);
  return (await r.json()) as RevisionList;
}
async function getRevision(request: APIRequestContext, id: string): Promise<RevisionDetail> {
  const r = await request.get(`/api/cargo-revisions/${encodeURIComponent(id)}`);
  expect(r.ok()).toBe(true);
  return (await r.json()) as RevisionDetail;
}
async function getPacking(request: APIRequestContext, id: string): Promise<RevisionPacking> {
  const r = await request.get(`/api/cargo-revisions/${encodeURIComponent(id)}/packing`);
  expect(r.ok()).toBe(true);
  return (await r.json()) as RevisionPacking;
}
async function getSnapshots(request: APIRequestContext): Promise<Snapshot[]> {
  return (await (await request.get("/api/snapshots")).json()) as Snapshot[];
}
async function getSnapshotEvaluation(request: APIRequestContext, id: string): Promise<Evaluation> {
  const r = await request.get(`/api/snapshots/${encodeURIComponent(id)}`);
  expect(r.ok()).toBe(true);
  return (await r.json()) as Evaluation;
}
const groupOf = (d: RevisionDetail, id: string): Group => {
  const g = d.groups.find((x) => x.group_id === id);
  expect(g, `group ${id} in ${d.revision_id}`).toBeDefined();
  return g!;
};

async function postResult<T>(page: Page, path: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((response) => response.url().endsWith(path) && response.request().method() === "POST");
  await action();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return (await response.json()) as T;
}

async function loadList(page: Page, bundleCount: number) {
  await page.getByRole("button", { name: "Xem trước list ống" }).click();
  await page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click();
  await expect(page.getByTestId("pipe-total")).toContainText(`${bundleCount} bó`);
}

// Canvas diagnostics (?viewerDiagnostics=1). Read-only; the canvas is the only source of scene identity.
async function readDiag(page: Page): Promise<Diag> {
  return await page.getByTestId("three-canvas").evaluate((node) => {
    const c = node as HTMLCanvasElement;
    const get = (v: string | undefined) => (v ? JSON.parse(v) : null);
    return {
      stats: get(c.dataset.viewerStats),
      meshes: get(c.dataset.meshes) ?? [],
      cameraState: get(c.dataset.cameraState),
      packing: get(c.dataset.packingView),
      projected: get(c.dataset.packingProjected),
    };
  });
}
async function waitForView(page: Page, view: string): Promise<Diag> {
  await expect.poll(async () => (await readDiag(page)).packing?.view ?? "", { timeout: 120_000 }).toBe(view);
  return await readDiag(page);
}
// Scene identity, loads, asset identity, camera and every plan mesh uuid must survive a view switch.
function expectSameScene(now: Diag, base: Diag) {
  expect(base.stats).not.toBeNull();
  expect(now.stats?.sceneUuid).toBe(base.stats!.sceneUuid);
  expect(now.stats?.loads).toBe(base.stats!.loads);
  expect(now.stats?.assetIdentity).toBe(base.stats!.assetIdentity);
  expect(now.cameraState).toEqual(base.cameraState);
  for (const m of base.meshes) expect(now.meshes.find((x) => x.id === m.id)?.uuid, `mesh ${m.id}`).toBe(m.uuid);
}
const selectedId = async (page: Page) =>
  ((await page.getByRole("region", { name: "Chỉnh bó hàng" }).locator("h2").first().textContent()) ?? "").trim();
const viewSelect = (page: Page) => page.getByLabel("Cách nhìn hàng");

// Saves a snapshot whose placements are replaced by a grid: 8 per row along x every 7600 mm, rows every 600 mm in y.
async function saveGridSnapshot(request: APIRequestContext, name: string, plan: PlanJson, unitIds: string[]): Promise<Saved> {
  const placements = unitIds.map((unit_id, i) => ({
    unit_id, x_mm: (i % 8) * 7600, y_mm: Math.floor(i / 8) * 600, z_mm: 0, yaw_deg: 0,
  }));
  const r = await request.post("/api/snapshots", { data: { name, plan: { ...plan, placements } } });
  expect(r.ok()).toBe(true);
  return (await r.json()) as Saved;
}

// Pipe pieces the DETAILED view should draw for a plan: placed pipe bundles whose packing status is DETAILED.
async function expectedDetailed(request: APIRequestContext, plan: PlanJson) {
  // same rule as the UI's planRevisionId: v1 pipe-list plans are pinned to the workbook revision R0000
  const revision = plan.contract_version === "scst.pipe-list.v1" ? revisionIdOf(0) : plan.cargo_revision?.revision_id;
  expect(revision).toBeTruthy();
  const packing = await getPacking(request, revision!);
  const groups = new Map(packing.groups.map((g) => [g.group_id, g]));
  const placed = new Set(plan.placements.map((p) => p.unit_id));
  let detailedPipes = 0, detailedBundles = 0, sourcePieces = 0;
  for (const u of plan.units) {
    if (!placed.has(u.id)) continue;
    const g = groups.get(u.source_ref?.group_id ?? "");
    const core = g?.bundle_packings.find((b) => b.bundle_id === u.id) ?? g;
    if (!core) continue;
    sourcePieces += core.pieces_source;
    if (core.status === "DETAILED") { detailedPipes += core.pieces_placed; detailedBundles += 1; }
  }
  return { detailedPipes, detailedBundles, sourcePieces };
}

test("S3-05 desktop: derived packing views keep the scene, provenance links, and NEEDS_RECHECK after an OD batch", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();
  const planAName = `S3-05 A ${tag}`;

  await page.goto("/?viewerDiagnostics=1");
  const base = (await getRevisionList(request)).latest_revision_id;
  await expect(page.getByTestId("revision-latest")).toContainText(base);
  const baseDetail = await getRevision(request, base);
  const r005 = groupOf(baseDetail, "Sheet1-R005");
  const r022 = groupOf(baseDetail, "Sheet1-R022");
  expect(r005.bundle_ids).toContain("PIPE-R005-B0001");
  expect(r022.bundle_ids).toContain("PIPE-R022-B0001");

  // 1. load the list, place one bundle of R005 and one of R022, apply, save plan A
  await loadList(page, baseDetail.bundle_count);
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R005");
  await page.getByTestId("unit-PIPE-R005-B0001").getByRole("button").click();
  await page.getByRole("button", { name: "Đặt bó" }).click();
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 1 bó");
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R022");
  await page.getByTestId("unit-PIPE-R022-B0001").getByRole("button").click();
  await page.getByRole("button", { name: "Đặt bó" }).click();
  await page.getByLabel("Tọa độ Y (cm)").fill("100");
  await postResult(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 2 bó");

  await page.getByLabel("Tên phương án lưu").fill(planAName);
  const savedA = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await expect(page.getByTestId(`saved-item-${savedA.id}`)).toContainText("Theo dữ liệu mới nhất");
  const snapA = await getSnapshotEvaluation(request, savedA.id);
  // legacy v1 plans are pinned implicitly to R0000; v2 plans carry the latest revision (same rule as sup02a)
  expect((await getSnapshots(request)).find((s) => s.id === savedA.id)?.cargo_revision_id).toBe(base);
  expect(snapA.plan.contract_version).toBe(base === revisionIdOf(0) ? "scst.pipe-list.v1" : "scst.pipe-list.v2");
  expect(snapA.plan.placements.map((p) => p.unit_id).sort()).toEqual(["PIPE-R005-B0001", "PIPE-R022-B0001"]);
  const planAJsonAtSave = JSON.stringify(snapA.plan);

  // baseline scene (ENVELOPE view, the default)
  await expect(page.getByTestId("packing-view-status")).toContainText("Khối bao");
  const baseline = await waitForView(page, "ENVELOPE");
  expect(baseline.meshes.length).toBeGreaterThan(0);
  const selectedBefore = await selectedId(page);

  // 2. DETAILED view: scene identity, selection and camera unchanged, derived tubes present
  await viewSelect(page).selectOption({ label: "Chi tiết ống" });
  await expect(page.getByTestId("packing-view-status")).toContainText("Chi tiết ống");
  const detailed = await waitForView(page, "DETAILED");
  expect(detailed.packing!.pipeInstances).toBeGreaterThan(0);
  expect(detailed.packing!.envelopeOnlyBundles).toBeGreaterThanOrEqual(1);
  expectSameScene(detailed, baseline);
  expect(await selectedId(page)).toBe(selectedBefore);

  // 3. SIMPLIFIED and back to ENVELOPE keep the same invariants
  await viewSelect(page).selectOption({ label: "Bó giản lược" });
  await expect(page.getByTestId("packing-view-status")).toContainText("Bó giản lược");
  expectSameScene(await waitForView(page, "SIMPLIFIED"), baseline);
  expect(await selectedId(page)).toBe(selectedBefore);
  await viewSelect(page).selectOption({ label: "Khối bao" });
  await expect(page.getByTestId("packing-view-status")).toContainText("Khối bao");
  expectSameScene(await waitForView(page, "ENVELOPE"), baseline);
  expect(await selectedId(page)).toBe(selectedBefore);

  await viewSelect(page).selectOption({ label: "Chi tiết ống" });
  await expect(page.getByTestId("packing-view-status")).toContainText("Chi tiết ống");
  expectSameScene(await waitForView(page, "DETAILED"), baseline);

  // 4. each bundle's derived status in the editor
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R005");
  await page.getByTestId("unit-PIPE-R005-B0001").getByRole("button").click();
  await expect(page.getByTestId("packing-status")).toHaveText("Chi tiết (dẫn xuất)");
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R022");
  await page.getByTestId("unit-PIPE-R022-B0001").getByRole("button").click();
  await expect(page.getByTestId("packing-status")).toHaveText("Chỉ khối bao");
  await expect(page.getByTestId("packing-reason-PIECES_DO_NOT_FIT")).toBeVisible();

  // 5. status filter: ENVELOPE_ONLY shows R022 and no R005 row
  await page.getByLabel("Lọc trạng thái cách xếp").selectOption("ENVELOPE_ONLY");
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R022");
  await expect(page.getByTestId("packing-cell-PIPE-R022-B0001")).toBeVisible();
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R005");
  await expect(page.locator('[data-testid^="packing-cell-PIPE-R005-"]')).toHaveCount(0);
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R022");

  // 6. the table reason link (role link) and the editor reason button both open the group in Dữ liệu hàng
  await page.getByRole("link", { name: "Lý do cách xếp PIPE-R022-B0001: mở nhóm trong Dữ liệu hàng" }).click();
  await expect(page.getByTestId("revision-group-Sheet1-R022")).toHaveAttribute("aria-current", "true");
  await page.getByTestId("packing-reason-PIECES_DO_NOT_FIT").getByRole("button").click();
  await expect(page.getByTestId("revision-group-Sheet1-R022")).toHaveAttribute("aria-current", "true");
  await expect(page.getByTestId("revision-packing-Sheet1-R022")).toContainText("Chỉ khối bao");

  // 7. OD batch on R005 (50 mm, or 52 mm if the current value is already 50) creates a new revision
  const od = Number(r005.outside_diameter_mm) === 50 ? "52" : "50";
  const next = revisionIdOf(revisionNumber(base) + 1);
  const oldPacking = await getPacking(request, base);
  const panel = page.getByRole("region", { name: "Dữ liệu hàng" });
  await panel.getByLabel("Loại nguồn").selectOption("FACTORY");
  await panel.getByLabel("Tham chiếu nguồn").fill(`PO-S305-${tag}`);
  await panel.getByLabel("Ngày nhận").fill("2026-11-04");
  await panel.getByLabel("Nhóm cần sửa").selectOption("Sheet1-R005");
  await panel.getByLabel("Đường kính ngoài (mm)").fill(od);
  // An OD correction normally comes with the bundle mass the factory re-states for it. OD is not a field of the
  // SUP-02A plan units, so an OD-only batch leaves a saved plan CURRENT by design (recorded in the worker return);
  // the re-stated mass (+1 kg per bundle) is what makes the old plan "Cần kiểm lại" exactly as in SUP-02A.
  const newMassG = groupOf(await getRevision(request, base), "Sheet1-R005").mass_g + 1000;
  await panel.getByLabel("Khối lượng mỗi bó (kg)").fill(`${Math.floor(newMassG / 1000)}.${String(newMassG % 1000).padStart(3, "0")}`);
  await panel.getByLabel("Mức xác nhận").selectOption("CONFIRMED");
  await panel.getByRole("button", { name: "Xem trước lô cập nhật" }).click();
  // an OD-only edit is a group field: the preview lists it, and the bundle counts come from the server's diff
  await expect(page.getByTestId("revision-preview")).toContainText("outside_diameter_mm");
  console.log(`S3-05 OD preview: ${(await page.getByTestId("revision-preview").textContent()) ?? ""}`);
  await panel.getByRole("button", { name: "Tạo revision" }).click();
  await expect(page.getByTestId("revision-message")).toContainText(next);
  await expect(page.getByTestId("revision-latest")).toContainText(next);

  const created = await getRevision(request, next);
  expect(groupOf(created, "Sheet1-R005").outside_diameter_mm).toBe(od);
  expect(groupOf(created, "Sheet1-R005").mass_g).toBe(newMassG);

  // the new packing is derived from the new OD: od_um exact, layout from the server (expected text computed, not hard-coded)
  const newPacking = await getPacking(request, next);
  const newR005 = newPacking.groups.find((g) => g.group_id === "Sheet1-R005")!;
  const oldR005 = oldPacking.groups.find((g) => g.group_id === "Sheet1-R005")!;
  expect(newR005.od_um).toBe(Number(od) * 1000);
  expect(oldR005.od_um).not.toBe(newR005.od_um);
  expect(JSON.stringify(newR005)).not.toBe(JSON.stringify(oldR005));
  const layoutText = newR005.layout ? `${newR005.layout} ${newR005.columns} × ${newR005.rows}` : "—";
  console.log(`S3-05 R005 OD ${od} mm layout: ${layoutText}`);
  await expect(page.getByTestId("revision-group-Sheet1-R005")).toBeVisible();
  await expect(page.getByTestId("revision-packing-Sheet1-R005")).toContainText(layoutText);
  await expect(page.getByTestId("revision-packing-Sheet1-R005")).toContainText("không phải số đo");

  // plan A after the OD + mass batch: "Cần kiểm lại" exactly as in SUP-02A.
  const itemA = (await getSnapshots(request)).find((s) => s.id === savedA.id)!;
  console.log(`S3-05 plan A after OD batch: ${JSON.stringify(itemA)}`);
  expect(itemA.recheck_status).toBe("NEEDS_RECHECK");
  expect(itemA.changed_count).toBe(r005.bundle_count);
  expect(itemA.placed_affected_count).toBe(1);
  await expect(page.getByTestId(`saved-item-${savedA.id}`)).toContainText(
    `Cần kiểm lại: thêm ${itemA.added_count} · bỏ ${itemA.removed_count} · đổi ${itemA.changed_count} bó; ${itemA.placed_affected_count} bó đã đặt bị ảnh hưởng`,
  );
  expect(JSON.stringify((await getSnapshotEvaluation(request, savedA.id)).plan)).toBe(planAJsonAtSave);

  await shotLocator(panel, "sup03-revision-panel-desktop.png");
  await shotPage(page, "sup03-desktop-flow.png");
  expect(pageErrors).toEqual([]);
});

test("S3-05 picking and timing: all units laid out, detailed build time and a click picks a placed bundle", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();

  await page.goto("/?viewerDiagnostics=1");
  const latest = (await getRevisionList(request)).latest_revision_id;
  await expect(page.getByTestId("revision-latest")).toContainText(latest);
  const detail = await getRevision(request, latest);
  await loadList(page, detail.bundle_count);
  await page.getByLabel("Tên phương án lưu").fill(`S3-05 list ${tag}`);
  const listSaved = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  const listPlan = (await getSnapshotEvaluation(request, listSaved.id)).plan;
  const unitIds = listPlan.units.map((u) => u.id);
  expect(unitIds.length).toBe(detail.bundle_count);

  const grid = await saveGridSnapshot(request, `S3-05 grid ${tag}`, listPlan, unitIds);
  const gridPlan = (await getSnapshotEvaluation(request, grid.id)).plan;
  const expected = await expectedDetailed(request, gridPlan);

  await page.reload();
  await page.getByLabel("Phương án đã lưu").selectOption(grid.id);
  await page.getByRole("button", { name: "Mở phương án" }).click();
  await expect(page.getByTestId("pipe-total")).toContainText(/đã xếp \d+ bó/);

  await viewSelect(page).selectOption({ label: "Chi tiết ống" });
  const detailed = await waitForView(page, "DETAILED");
  const pk = detailed.packing!;
  expect(pk.capped).toBe(false);
  expect(pk.pipeInstances).toBe(expected.detailedPipes);
  expect(pk.detailedBundles).toBe(expected.detailedBundles);
  const detailedBuildMs = pk.buildMs;

  await viewSelect(page).selectOption({ label: "Bó giản lược" });
  const simplified = await waitForView(page, "SIMPLIFIED");
  const ringInstances = simplified.packing!.ringInstances;
  const simplifiedBuildMs = simplified.packing!.buildMs;
  await viewSelect(page).selectOption({ label: "Chi tiết ống" });
  await waitForView(page, "DETAILED");

  const timing = {
    planUnits: unitIds.length,
    placedUnits: gridPlan.placements.length,
    bundles: pk.candidateBundles,
    totalBundles: pk.totalBundles,
    detailedBundles: pk.detailedBundles,
    buildMs: detailedBuildMs,
    pipeInstances: pk.pipeInstances,
    ringInstances,
    simplifiedBuildMs,
    capped: pk.capped,
    budget: pk.budget,
    expectedDetailedPipes: expected.detailedPipes,
    sourcePiecesPlaced: expected.sourcePieces,
    cargoRevision: gridPlan.contract_version === "scst.pipe-list.v1" ? revisionIdOf(0) : gridPlan.cargo_revision?.revision_id ?? null,
  };
  mkdirSync(evidenceDir(), { recursive: true });
  writeFileSync(resolve(evidenceDir(), "sup03-timing.json"), `${JSON.stringify(timing, null, 2)}\n`);
  console.log(`S3-05 timing ${JSON.stringify(timing)}`);

  // picking in DETAILED: a projected pipe centre is clicked and selects a placed PIPE bundle; the view stays DETAILED
  const placedIds = new Set(gridPlan.placements.map((p) => p.unit_id));
  const box = await page.getByTestId("three-canvas").boundingBox();
  expect(box).not.toBeNull();
  const current = await readDiag(page);
  const point = (current.projected ?? []).find((pt) => pt.x >= 0 && pt.y >= 0 && pt.x <= box!.width && pt.y <= box!.height);
  expect(point, "a projected pipe centre inside the canvas").toBeDefined();
  await page.mouse.click(box!.x + point!.x, box!.y + point!.y);
  await expect.poll(() => selectedId(page)).toMatch(/^PIPE-/);
  const picked = await selectedId(page);
  expect(placedIds.has(picked)).toBe(true);
  console.log(`S3-05 pick: clicked probe ${point!.id}, selected ${picked}, equal=${picked === point!.id}`);
  expect((await readDiag(page)).packing?.view).toBe("DETAILED");
  expect(pageErrors).toEqual([]);
});

test("S3-05 budget: detailed view stops at 60 000 instances with a visible message; the R002 test values are restored", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();

  const before = await getRevision(request, (await getRevisionList(request)).latest_revision_id);
  const originalR002 = groupOf(before, "Sheet1-R002");
  const originalPieces = originalR002.pieces_per_bundle;
  const originalOd = originalR002.outside_diameter_mm;
  let budgetCreated = false;
  try {
    // 3a. budget revision on the live latest: 10 000 pipes per bundle at OD 3 mm (UNVERIFIED, valid source)
    const latest = (await getRevisionList(request)).latest_revision_id;
    const budgetRes = await request.post("/api/cargo-revisions", {
      data: {
        parent_revision_id: latest,
        source: { kind: "FACTORY", reference: `S3-05-BUDGET-${tag}`, received_date: "2026-11-04", note: "" },
        changes: [{ type: "UPDATE_GROUP", group_id: "Sheet1-R002", confirmation: "UNVERIFIED", set: { pieces_per_bundle: 10000, outside_diameter_mm: "3" } }],
      },
    });
    expect(budgetRes.ok()).toBe(true);
    budgetCreated = true;
    const budgetId = ((await budgetRes.json()) as { revision_id: string }).revision_id;
    const budgetDetail = await getRevision(request, budgetId);
    expect(groupOf(budgetDetail, "Sheet1-R002").pieces_per_bundle).toBe(10000);

    // 3b. list on latest, save, place >= 10 R002 bundles through a snapshot, open it
    await page.goto("/?viewerDiagnostics=1");
    await expect(page.getByTestId("revision-latest")).toContainText(budgetId);
    await loadList(page, budgetDetail.bundle_count);
    await page.getByLabel("Tên phương án lưu").fill(`S3-05 budget list ${tag}`);
    const listSaved = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
    const listPlan = (await getSnapshotEvaluation(request, listSaved.id)).plan;
    const r002Ids = listPlan.units.filter((u) => u.source_ref?.group_id === "Sheet1-R002").map((u) => u.id);
    expect(r002Ids.length).toBeGreaterThanOrEqual(10);
    const budgetSaved = await saveGridSnapshot(request, `S3-05 budget ${tag}`, listPlan, r002Ids.slice(0, 10));

    await page.reload();
    await page.getByLabel("Phương án đã lưu").selectOption(budgetSaved.id);
    await page.getByRole("button", { name: "Mở phương án" }).click();
    await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 10 bó");

    // 3c. DETAILED: capped at the budget, message shows the limit
    await viewSelect(page).selectOption({ label: "Chi tiết ống" });
    const capped = await waitForView(page, "DETAILED");
    expect(capped.packing!.capped).toBe(true);
    expect(capped.packing!.pipeInstances).toBeLessThanOrEqual(BUDGET_PIECES);
    await expect(page.getByTestId("packing-view-status")).toContainText("Vượt hạn mức 60.000");
    await shotPage(page, "sup03-budget-capped.png");
    expect(pageErrors).toEqual([]);
  } finally {
    // restore the R002 values read before step 3 so later spec files see the workbook values again
    if (budgetCreated) {
      const latest = (await getRevisionList(request)).latest_revision_id;
      const restoreRes = await request.post("/api/cargo-revisions", {
        data: {
          parent_revision_id: latest,
          source: { kind: "FACTORY", reference: `S3-05-RESTORE-${tag}`, received_date: "2026-11-04", note: "restore R002 after S3-05 budget check" },
          changes: [{ type: "UPDATE_GROUP", group_id: "Sheet1-R002", confirmation: "UNVERIFIED", set: { pieces_per_bundle: originalPieces, outside_diameter_mm: originalOd } }],
        },
      });
      expect(restoreRes.ok()).toBe(true);
      const restoredId = ((await restoreRes.json()) as { revision_id: string }).revision_id;
      const restored = groupOf(await getRevision(request, restoredId), "Sheet1-R002");
      expect(restored.pieces_per_bundle).toBe(originalPieces);
      expect(restored.outside_diameter_mm).toBe(originalOd);
    }
  }
});

test("S3-05 mobile 390px: detailed view with a selected bundle shows packing info and no horizontal overflow", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  await page.setViewportSize({ width: 390, height: 844 });

  await page.goto("/?viewerDiagnostics=1");
  const latest = (await getRevisionList(request)).latest_revision_id;
  await expect(page.getByTestId("revision-latest")).toContainText(latest);
  const detail = await getRevision(request, latest);
  await loadList(page, detail.bundle_count);
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R005");
  await page.getByTestId("unit-PIPE-R005-B0001").getByRole("button").click();
  await page.getByRole("button", { name: "Đặt bó" }).click();
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 1 bó");

  await viewSelect(page).selectOption({ label: "Chi tiết ống" });
  await waitForView(page, "DETAILED");
  await page.getByTestId("unit-PIPE-R005-B0001").getByRole("button").click();
  await expect(page.getByTestId("packing-info")).toBeVisible();
  await expect(page.getByTestId("packing-status")).toHaveText("Chi tiết (dẫn xuất)");

  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(scrollWidth).toBeLessThanOrEqual(390 + 1);
  await shotPage(page, "sup03-390px-detailed.png");
  expect(pageErrors).toEqual([]);
});
