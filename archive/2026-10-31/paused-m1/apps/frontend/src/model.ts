import type { components } from "./generated/api";

export type Plan = components["schemas"]["Plan"];
export type Evaluation = components["schemas"]["Evaluation"];
export type Unit = components["schemas"]["CargoUnit"];
export type Placement = components["schemas"]["Placement"];

const number = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 });
export const fmt = (n: number) => number.format(n);
const tonneNumber = new Intl.NumberFormat("vi-VN", {
  maximumFractionDigits: 6,
});
export const tonnes = (g: number) => tonneNumber.format(g / 1_000_000);
export const massLabel = (g: number) =>
  g > 0 && g < 1000
    ? `${fmt(g)} g`
    : g > 0 && g < 1_000_000
      ? `${fmt(g / 1000)} kg`
      : `${tonnes(g)} tấn`;
export const footprint = (u: Unit, p: Placement) =>
  p.yaw_deg % 180 ? [u.width_mm, u.length_mm] : [u.length_mm, u.width_mm];
export const kgInput = (grams: number) =>
  `${Math.floor(grams / 1000)}${
    grams % 1000
      ? "." +
        String(grams % 1000)
          .padStart(3, "0")
          .replace(/0+$/, "")
      : ""
  }`;

// Parse decimal text exactly: never round a fractional gram into compliance.
export function parseKg(text: string): number {
  const value = text.trim().replace(",", ".");
  if (!/^\d+(\.\d{1,3})?$/.test(value))
    throw new Error("Khối lượng cần số dương, tối đa 3 chữ số thập phân (kg).");
  const [whole, fraction = ""] = value.split(".");
  const grams = BigInt(whole) * 1000n + BigInt(fraction.padEnd(3, "0"));
  if (grams <= 0n || grams > 1_000_000_000_000n)
    throw new Error("Khối lượng phải lớn hơn 0 và không quá 1.000.000.000 kg.");
  return Number(grams);
}

export function parseMm(text: string): number {
  if (!/^-?\d+$/.test(text.trim())) throw new Error("Tọa độ cần số nguyên mm.");
  const value = Number(text);
  if (!Number.isSafeInteger(value) || Math.abs(value) > 1_000_000)
    throw new Error("Tọa độ ngoài phạm vi ±1.000.000 mm.");
  return value;
}

export async function requestEvaluation(plan?: Plan): Promise<Evaluation> {
  const response = await fetch(plan ? "/api/validate" : "/api/demo", {
    method: plan ? "POST" : "GET",
    headers: plan ? { "Content-Type": "application/json" } : undefined,
    body: plan ? JSON.stringify(plan) : undefined,
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    if (response.status === 422)
      throw new Error(
        "Dữ liệu không đúng cấu trúc được hỗ trợ. Phương án trước vẫn được giữ.",
      );
    throw new Error(
      `Không thể kiểm phương án (HTTP ${response.status}). Thử lại khi backend sẵn sàng.`,
    );
  }
  const data = (await response.json()) as Evaluation;
  if (
    data.plan?.contract_version !== "scst.demo.v1" ||
    data.plan.source !== "SYNTHETIC"
  )
    throw new Error("Phiên bản dữ liệu API không tương thích.");
  return data;
}
