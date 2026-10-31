import {
  expect,
  test,
} from "../../apps/frontend/node_modules/@playwright/test";

test("real API, 3D, editing, errors, undo and table identity", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const result = await (await request.get("/api/demo")).json();
  await page.goto("/");
  await expect(page.getByTestId("check-status")).toHaveText("Đạt kiểm tra");
  await expect(page.getByTestId("three-canvas")).toBeVisible();
  for (const unit of result.plan.units)
    await expect(page.getByTestId(`row-${unit.id}`)).toBeAttached();
  await page.screenshot({
    path: "../../docs/reviews/SCST_M1_EVIDENCE/desktop-3d.png",
    fullPage: true,
  });
  const canvas = page.getByTestId("three-canvas");
  const box = (await canvas.boundingBox())!;
  await canvas.click({
    position: { x: box.width * 0.65, y: box.height * 0.65 },
  });
  await expect(page.locator(".editor-card h2")).toContainText("PP-");
  const beforeOrbit = await canvas.screenshot();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(
    box.x + box.width / 2 + 90,
    box.y + box.height / 2 + 25,
    { steps: 8 },
  );
  await page.mouse.up();
  expect((await canvas.screenshot()).equals(beforeOrbit)).toBe(false);
  await page.getByRole("button", { name: "Đặt lại góc nhìn" }).click();
  expect((await canvas.screenshot()).equals(beforeOrbit)).toBe(true);
  await page.getByTestId("row-ST-001").getByRole("button").click();
  await page.getByRole("button", { name: "Mặt bằng", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Chọn ST-001", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Chọn PP-007", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "PP-007 Thép ống" }),
  ).toBeVisible();
  await page.getByTestId("row-ST-001").getByRole("button").click();
  await page.getByLabel("Khối lượng bó (kg)", { exact: true }).fill("2500.001");
  await page
    .getByLabel("Giới hạn khối lượng hàng (kg)", { exact: true })
    .fill("26100");
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/api/validate") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  const checked = await (await response).json();
  expect(checked.summary.placed_mass_g).toBe(26100001);
  expect(checked.issues.map((i: { code: string }) => i.code)).toContain(
    "OVERWEIGHT",
  );
  await expect(page.getByTestId("check-status")).toHaveText("1 vấn đề");
  await expect(
    page.getByText("Vượt 1 g giới hạn hàng", { exact: true }),
  ).toBeVisible();
  await expect(page.getByTestId("row-ST-001")).toContainText("2.500,001");
  await page.getByLabel("Tọa độ X (mm)", { exact: true }).fill("8001");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByTestId("row-ST-001")).toContainText("8.001 / 550");
  await expect(page.locator("#checks")).toContainText("Vượt biên hầm");
  await expect(
    page
      .getByRole("button", { name: "Chọn ST-001", exact: true })
      .locator("rect"),
  ).toHaveAttribute("x", "8001");
  await page.screenshot({
    path: "../../docs/reviews/SCST_M1_EVIDENCE/invalid-plan-2d.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Bản trước" }).click();
  await expect(page.getByTestId("row-ST-001")).toContainText("500 / 550");
  await expect(page.getByTestId("check-status")).toHaveText("1 vấn đề");
  await page.getByRole("button", { name: "Bản trước" }).click();
  await expect(page.getByTestId("check-status")).toHaveText("Đạt kiểm tra");
  await expect(page.getByTestId("placed-mass")).toHaveText("26,1");
  expect(errors).toEqual([]);
});

test("precision rejection and network failure preserve last checked plan", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("check-status")).toHaveText("Đạt kiểm tra");
  await page
    .getByLabel("Khối lượng bó (kg)", { exact: true })
    .fill("2500.0001");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByRole("alert")).toContainText("tối đa 3 chữ số");
  await page.getByLabel("Khối lượng bó (kg)", { exact: true }).fill("3000");
  await page.route("**/api/validate", (route) => route.abort("failed"));
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByTestId("placed-mass")).toHaveText("26,1");
  await expect(page.getByRole("button", { name: "Bản trước" })).toBeDisabled();
  await page.unroute("**/api/validate");
  await page.getByRole("button", { name: "Áp dụng & kiểm lại" }).click();
  await expect(page.getByTestId("placed-mass")).toHaveText("26,6");
});

test("no WebGL fallback, keyboard selection, filters and mobile layout", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (
      this: HTMLCanvasElement,
      type: string,
      ...args: unknown[]
    ) {
      if (type.includes("webgl")) return null;
      return Reflect.apply(original, this, [type, ...args]);
    } as typeof original;
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(
    page.getByRole("img", { name: "Mặt bằng hầm và ID từng bó" }),
  ).toBeVisible();
  await expect(
    page.getByText("WebGL không khả dụng · đang dùng mặt bằng 2D"),
  ).toBeVisible();
  const selected = page.getByRole("button", {
    name: "Chọn PP-007",
    exact: true,
  });
  await selected.focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { name: "PP-007 Thép ống" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Chưa xếp", exact: true }).click();
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.getByTestId("row-PP-013")).toContainText("Tùy chọn");
  await page.getByTestId("row-PP-013").getByRole("button").click();
  await expect(
    page.getByText("Bó này chưa xếp.", { exact: false }),
  ).toBeVisible();
  await page.getByLabel("Tìm bó hàng").fill("không có");
  await expect(
    page.getByText("Không có bó hàng phù hợp bộ lọc."),
  ).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > innerWidth,
  );
  expect(overflow).toBe(false);
  await page.screenshot({
    path: "../../docs/reviews/SCST_M1_EVIDENCE/mobile-fallback.png",
    fullPage: true,
  });
});
