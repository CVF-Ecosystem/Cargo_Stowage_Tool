import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "../../apps/frontend/node_modules/@playwright/test";
import type { APIRequestContext, Locator, Page } from "../../apps/frontend/node_modules/@playwright/test";

// SUP-02A S2-06: revision panel flow (desktop + 390px) on the shared suite database.
// The suite shares one server/DB across spec files, so every revision id is derived from the live latest id.

const DATASET = "BALTIMORE-PIPE-V1-1";
const evidenceDir = resolve(__dirname, "../../docs/reviews/SCST_SUP_02A_EVIDENCE/browser");
const shotPage = async (page: Page, name: string) => {
  mkdirSync(evidenceDir, { recursive: true });
  await page.screenshot({ path: resolve(evidenceDir, name), fullPage: true });
};
const shotLocator = async (locator: Locator, name: string) => {
  mkdirSync(evidenceDir, { recursive: true });
  await locator.screenshot({ path: resolve(evidenceDir, name) });
};

type Stamp = { revision_id: string; source: null | { kind: string; reference: string; received_date: string; note: string }; confirmation: string };
type Group = {
  group_id: string; origin: string; bundle_count: number; pieces_per_bundle: number; dimensions_um: number[]; mass_g: number;
  outside_diameter_mm: string; wall_thickness_mm: string; dimension_warning: boolean; bundle_ids: string[];
  provenance: Record<string, Stamp>; overrides: unknown[];
};
type RevisionDetail = { revision_id: string; parent_revision_id: string | null; change_count: number; source: Stamp["source"]; groups: Group[] };
type RevisionList = { latest_revision_id: string; revisions: { revision_id: string }[] };
type Snapshot = {
  id: string; name: string; cargo_revision_id: string | null; recheck_status: string;
  added_count: number; removed_count: number; changed_count: number; placed_affected_count: number;
};
type Saved = { id: string };
type Evaluation = { plan: { contract_version: string; cargo_revision?: { revision_id: string } | null; placements: { unit_id: string }[] } };

const revisionNumber = (id: string) => Number(id.split("@R")[1]);
const revisionIdOf = (n: number) => `${DATASET}@R${String(n).padStart(4, "0")}`;
const WORKBOOK_REVISION = revisionIdOf(0);

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
async function getSnapshots(request: APIRequestContext): Promise<Snapshot[]> {
  return (await (await request.get("/api/snapshots")).json()) as Snapshot[];
}
async function getSnapshotEvaluation(request: APIRequestContext, id: string): Promise<Evaluation> {
  const r = await request.get(`/api/snapshots/${encodeURIComponent(id)}`);
  expect(r.ok()).toBe(true);
  return (await r.json()) as Evaluation;
}

async function postResult<T>(page: Page, path: string, action: () => Promise<void>): Promise<T> {
  const pending = page.waitForResponse((response) => response.url().endsWith(path) && response.request().method() === "POST");
  await action();
  const response = await pending;
  expect(response.ok()).toBe(true);
  return (await response.json()) as T;
}

test("S2-06 flow: list, save A, one-group sourced batch, NEEDS_RECHECK, rebase, compare, save B, reopen both", async ({ page, request }) => {
  test.setTimeout(180_000);
  const pageErrors: string[] = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  const tag = Date.now();
  const planAName = `S2-06 A ${tag}`;
  const planBName = `S2-06 B ${tag}`;
  const sourceReference = `PO-S206-${tag}`;

  // Changed group: Sheet1-R002 (bundle PIPE-R002-B0001 is placed). Untouched group: Sheet1-R022 (PIPE-R022-B0001 placed).
  const base = (await getRevisionList(request)).latest_revision_id;
  const baseDetail = await getRevision(request, base);
  const changedBase = baseDetail.groups.find((g) => g.group_id === "Sheet1-R002");
  expect(changedBase).toBeDefined();
  const changedGroup = changedBase!;
  const next = revisionIdOf(revisionNumber(base) + 1);
  // New values are offset from the CURRENT latest values so the batch is a real change on every run of this shared DB.
  const expectedMassG = changedGroup.mass_g + 1234; // grams per bundle
  const expectedLengthUm = changedGroup.dimensions_um[0] + 1234; // µm
  const expectedDims = [expectedLengthUm, changedGroup.dimensions_um[1], changedGroup.dimensions_um[2]];
  const kgText = (g: number) => `${Math.floor(g / 1000)}.${String(g % 1000).padStart(3, "0")}`; // exact, 3 decimals
  const cmText = (um: number) => `${Math.floor(um / 10000)}.${String(um % 10000).padStart(4, "0")}`; // exact, 4 decimals

  await page.goto("/");
  await expect(page.getByTestId("revision-latest")).toContainText(base);

  // 1. open list and save plan A (placed: one bundle of the changed group + one bundle of an untouched group)
  await page.getByRole("button", { name: "Xem trước list ống" }).click();
  await page.getByRole("button", { name: "Nạp list vào phương án hiện tại" }).click();
  await expect(page.getByTestId("pipe-total")).toContainText(`${baseDetail.bundle_count} bó`);
  await expect(page.getByTestId("revision-in-use")).toContainText(base);

  await page.getByTestId("unit-PIPE-R002-B0001").getByRole("button").click();
  await page.getByRole("button", { name: "Đặt bó" }).click();
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 1 bó");
  await page.getByLabel("Nhóm nguồn").selectOption("Sheet1-R022");
  await page.getByTestId("unit-PIPE-R022-B0001").getByRole("button").click();
  await page.getByRole("button", { name: "Đặt bó" }).click();
  // move the second bundle off the first one's footprint, then apply and recheck
  await page.getByLabel("Tọa độ Y (cm)").fill("100");
  await postResult(page, "/api/validate", () => page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click());
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 2 bó");

  await page.getByLabel("Tên phương án lưu").fill(planAName);
  const savedA = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await expect(page.getByTestId(`saved-item-${savedA.id}`)).toContainText("Theo dữ liệu mới nhất");
  // legacy v1 list plans are pinned implicitly to R0000; v2 (latest revision) is used when latest is not R0000
  expect((await getSnapshots(request)).find((s) => s.id === savedA.id)?.cargo_revision_id).toBe(base);
  const snapshotA = await getSnapshotEvaluation(request, savedA.id);
  expect(snapshotA.plan.contract_version).toBe(base === WORKBOOK_REVISION ? "scst.pipe-list.v1" : "scst.pipe-list.v2");
  expect(snapshotA.plan.placements.map((p) => p.unit_id).sort()).toEqual(["PIPE-R002-B0001", "PIPE-R022-B0001"]);
  const planAJsonAtSave = JSON.stringify(snapshotA.plan);

  // 2. one sourced update batch editing one group (kg with 3 decimals, cm with 4 decimals)
  const panel = page.getByRole("region", { name: "Dữ liệu hàng" });
  await panel.getByLabel("Loại nguồn").selectOption("FACTORY");
  await panel.getByLabel("Tham chiếu nguồn").fill(sourceReference);
  await panel.getByLabel("Ngày nhận").fill("2026-11-04");
  await expect(panel.locator('select[aria-label="Nhóm cần sửa"] option[value="Sheet1-R002"]')).toHaveCount(1);
  await panel.getByLabel("Nhóm cần sửa").selectOption("Sheet1-R002");
  await panel.getByLabel("Khối lượng mỗi bó (kg)").fill(kgText(expectedMassG));
  await panel.getByLabel("Chiều dài bó (cm)").fill(cmText(expectedLengthUm));
  await panel.getByLabel("Mức xác nhận").selectOption("CONFIRMED");
  await panel.getByRole("button", { name: "Xem trước lô cập nhật" }).click();
  await expect(page.getByTestId("revision-preview")).toContainText(`Bó đổi: ${changedGroup.bundle_count}`);
  for (const id of changedGroup.bundle_ids.slice(0, 3)) await expect(page.getByTestId("revision-preview")).toContainText(id);
  await panel.getByRole("button", { name: "Tạo revision" }).click();
  await expect(page.getByTestId("revision-message")).toContainText(next);
  await expect(page.getByTestId("revision-latest")).toContainText(next);
  await shotLocator(panel, "sup02a-flow-revision-panel-desktop.png");

  // 2b. stored values are exact integers, changed fields carry the batch provenance, unchanged fields keep R0000 WORKBOOK
  const created = await getRevision(request, next);
  expect(created.parent_revision_id).toBe(base);
  expect(created.change_count).toBe(1);
  expect(created.source).toMatchObject({ kind: "FACTORY", reference: sourceReference, received_date: "2026-11-04" });
  const storedGroup = created.groups.find((g) => g.group_id === "Sheet1-R002")!;
  expect(Number.isInteger(storedGroup.mass_g)).toBe(true);
  expect(storedGroup.mass_g).toBe(expectedMassG);
  expect(storedGroup.dimensions_um).toEqual(expectedDims);
  expect(storedGroup.dimensions_um.every((v) => Number.isInteger(v))).toBe(true);
  expect(storedGroup.bundle_count).toBe(changedGroup.bundle_count);
  expect(storedGroup.pieces_per_bundle).toBe(changedGroup.pieces_per_bundle);
  const changedFields = ["mass_g", "dimensions_um"];
  for (const field of changedFields) {
    expect(storedGroup.provenance[field]).toMatchObject({
      revision_id: next, source: { kind: "FACTORY", reference: sourceReference, received_date: "2026-11-04" }, confirmation: "CONFIRMED",
    });
  }
  for (const field of ["bundle_count", "pieces_per_bundle", "outside_diameter_mm", "wall_thickness_mm"]) {
    expect(storedGroup.provenance[field]).toEqual(changedGroup.provenance[field]);
    expect(storedGroup.provenance[field]).toMatchObject({ revision_id: WORKBOOK_REVISION, source: null, confirmation: "WORKBOOK" });
  }

  // 3. plan A is now NEEDS_RECHECK; counts match the server's snapshot list
  const itemA = (await getSnapshots(request)).find((s) => s.id === savedA.id)!;
  expect(itemA.recheck_status).toBe("NEEDS_RECHECK");
  expect(itemA.added_count).toBe(0);
  expect(itemA.removed_count).toBe(0);
  expect(itemA.changed_count).toBe(changedGroup.bundle_count);
  expect(itemA.placed_affected_count).toBe(1);
  await expect(page.getByTestId(`saved-item-${savedA.id}`)).toContainText(
    `Cần kiểm lại: thêm 0 · bỏ 0 · đổi ${changedGroup.bundle_count} bó; 1 bó đã đặt bị ảnh hưởng`,
  );

  // 4. rebase: candidate at the new revision, changed group's placed bundle dropped, untouched bundle kept
  await page.getByLabel("Phương án đã lưu").selectOption(savedA.id);
  await page.getByRole("button", { name: "Tạo bản theo dữ liệu mới" }).click();
  const dropped = page.getByTestId("rebase-dropped");
  await expect(dropped).toBeVisible();
  await expect(dropped).toContainText("PIPE-R002-B0001");
  await expect(dropped).toContainText("Đổi");
  await expect(dropped).toContainText("Giữ 1 vị trí; bỏ 1 vị trí");
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 1 bó");
  await expect(page.getByTestId("revision-in-use")).toContainText(next);
  await expect(page.getByTestId("comparison-summary")).toBeVisible();
  await expect(page.getByTestId("comparison-baseline")).toContainText(planAName);
  await shotPage(page, "sup02a-flow-rebase-compare-desktop.png");

  // 5. save the candidate as plan B
  await page.getByLabel("Tên phương án lưu").fill(planBName);
  const savedB = await postResult<Saved>(page, "/api/snapshots", () => page.getByRole("button", { name: "Lưu phương án" }).click());
  await expect(page.getByTestId(`saved-item-${savedB.id}`)).toContainText("Theo dữ liệu mới nhất");
  await expect(page.getByTestId(`saved-item-${savedB.id}`)).toContainText(next);
  const snapshotB = await getSnapshotEvaluation(request, savedB.id);
  expect(snapshotB.plan.contract_version).toBe("scst.pipe-list.v2");
  expect(snapshotB.plan.cargo_revision?.revision_id).toBe(next);

  // 6. reload and reopen both plans
  await page.reload();
  await expect(page.getByTestId("revision-latest")).toContainText(next);
  await page.getByLabel("Phương án đã lưu").selectOption(savedB.id);
  await page.getByRole("button", { name: "Mở phương án" }).click();
  await expect(page.getByTestId("revision-in-use")).toContainText(next);
  await expect(page.getByTestId("pipe-total")).toContainText("đã xếp 1 bó");

  await page.getByLabel("Phương án đã lưu").selectOption(savedA.id);
  await page.getByRole("button", { name: "Mở phương án" }).click();
  await expect(page.getByTestId("revision-in-use")).toContainText(base);
  await expect(page.getByTestId(`saved-item-${savedA.id}`)).toContainText("Cần kiểm lại");

  // plan A's stored plan is unchanged by every operation after saving it
  const planAAfter = await getSnapshotEvaluation(request, savedA.id);
  expect(JSON.stringify(planAAfter.plan)).toBe(planAJsonAtSave);
  expect(pageErrors).toEqual([]);
});

test("S2-06 mobile 390px: revision panel creates a small ADD_GROUP batch without horizontal overflow", async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const tag = Date.now();
  await page.goto("/");
  const before = (await getRevisionList(request)).latest_revision_id;
  await expect(page.getByTestId("revision-latest")).toContainText(before);
  const panel = page.getByRole("region", { name: "Dữ liệu hàng" });
  await panel.scrollIntoViewIfNeeded();

  await panel.getByLabel("Loại nguồn").selectOption("CUSTOMER");
  await panel.getByLabel("Tham chiếu nguồn").fill(`M-S206-${tag}`);
  await panel.getByLabel("Ngày nhận").fill("2026-11-04");
  await panel.getByLabel("Loại thay đổi").selectOption("ADD_GROUP");
  await panel.getByLabel("Số bó trong nhóm").fill("3");
  await panel.getByLabel("Số ống mỗi bó").fill("10");
  await panel.getByLabel("Khối lượng mỗi bó (kg)").fill("2000.5");
  await panel.getByLabel("Chiều dài bó (cm)").fill("600");
  await panel.getByLabel("Chiều rộng bó (cm)").fill("30");
  await panel.getByLabel("Chiều cao bó (cm)").fill("30");
  await panel.getByLabel("Đường kính ngoài (mm)").fill("114.3");
  await panel.getByLabel("Độ dày thành (mm)").fill("6.02");
  await panel.getByLabel("Mức xác nhận").selectOption("CONFIRMED");
  await panel.getByRole("button", { name: "Xem trước lô cập nhật" }).click();
  await expect(page.getByTestId("revision-preview")).toContainText("Bó thêm: 3");

  const expected = revisionIdOf(revisionNumber(before) + 1);
  await panel.getByRole("button", { name: "Tạo revision" }).click();
  await expect(page.getByTestId("revision-message")).toContainText(expected);
  await expect(page.getByTestId("revision-latest")).toContainText(expected);

  const created = await getRevision(request, expected);
  expect(created.groups.some((g) => g.origin === "ADDED" && g.bundle_count === 3 && g.pieces_per_bundle === 10)).toBe(true);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  const box = await panel.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.width).toBeLessThanOrEqual(390);
  await shotLocator(panel, "sup02a-flow-revision-panel-390px.png");
});

test("S2-06 stale parent: UI create after another revision shows the 409 message and writes nothing", async ({ page, request }) => {
  const tag = Date.now();
  await page.goto("/");
  const panel = page.getByRole("region", { name: "Dữ liệu hàng" });
  const latest = (await getRevisionList(request)).latest_revision_id;
  await expect(page.getByTestId("revision-latest")).toContainText(latest);

  await panel.getByLabel("Tham chiếu nguồn").fill(`PO-STALE-${tag}`);
  await panel.getByLabel("Ngày nhận").fill("2026-11-04");
  await panel.getByLabel("Loại thay đổi").selectOption("ADD_GROUP");
  await panel.getByLabel("Số bó trong nhóm").fill("3");
  await panel.getByLabel("Số ống mỗi bó").fill("10");
  await panel.getByLabel("Khối lượng mỗi bó (kg)").fill("2000.5");
  await panel.getByLabel("Chiều dài bó (cm)").fill("600");
  await panel.getByLabel("Chiều rộng bó (cm)").fill("30");
  await panel.getByLabel("Chiều cao bó (cm)").fill("30");
  await panel.getByLabel("Đường kính ngoài (mm)").fill("114.3");
  await panel.getByLabel("Độ dày thành (mm)").fill("6.02");
  await panel.getByLabel("Mức xác nhận").selectOption("CONFIRMED");
  await panel.getByRole("button", { name: "Xem trước lô cập nhật" }).click();
  await expect(page.getByTestId("revision-preview")).toContainText("Bó thêm: 3");

  // another client creates a revision on the same parent after the preview
  const other = await request.post("/api/cargo-revisions", {
    data: {
      parent_revision_id: latest,
      source: { kind: "FACTORY", reference: `OTHER-${tag}`, received_date: "2026-11-04", note: "" },
      changes: [{ type: "UPDATE_GROUP", group_id: "Sheet1-R003", confirmation: "CONFIRMED", set: { mass_g: 1000000 } }],
    },
  });
  expect(other.status()).toBe(200);
  const newer = ((await other.json()) as { revision_id: string }).revision_id;
  expect(revisionNumber(newer)).toBe(revisionNumber(latest) + 1);

  const beforeRevisions = (await getRevisionList(request)).revisions.map((r) => r.revision_id);
  const beforeSnapshots = (await getSnapshots(request)).length;

  await panel.getByRole("button", { name: "Tạo revision" }).click();
  await expect(page.getByTestId("revision-action-error")).toContainText("không còn là mới nhất");
  await expect(page.getByTestId("revision-latest")).toContainText(newer);
  await expect(panel.getByRole("button", { name: "Tạo revision" })).toBeDisabled();
  await expect(page.getByTestId("revision-preview")).toHaveCount(0);

  // nothing extra was written: same revision list, same latest, no new snapshot
  const afterList = await getRevisionList(request);
  expect(afterList.latest_revision_id).toBe(newer);
  expect(afterList.revisions.map((r) => r.revision_id)).toEqual(beforeRevisions);
  expect((await getSnapshots(request)).length).toBe(beforeSnapshots);
  const newerDetail = await getRevision(request, newer);
  const latestDetail = await getRevision(request, latest);
  expect(newerDetail.change_count).toBe(1);
  expect(newerDetail.groups.filter((g) => g.origin === "ADDED").length).toBe(latestDetail.groups.filter((g) => g.origin === "ADDED").length);
});
