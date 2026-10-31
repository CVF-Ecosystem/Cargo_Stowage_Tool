import type { components } from "../api/generated/api";

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
export const dimensions = (u: Unit) => u.dimensions_um ? u.dimensions_um.map(n=>n/1000) : [u.length_mm,u.width_mm,u.height_mm];
export const footprint = (u: Unit, p: Placement) => {
  const [length,width]=dimensions(u); return p.yaw_deg % 180 ? [width,length] : [length,width];
};
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
export function parseKg(text: string, allowZero = false): number {
  const value = text.trim().replace(",", ".");
  if (!/^\d+(\.\d{1,3})?$/.test(value))
    throw new Error("Khối lượng cần số dương, tối đa 3 chữ số thập phân (kg).");
  const [whole, fraction = ""] = value.split(".");
  const grams = BigInt(whole) * 1000n + BigInt(fraction.padEnd(3, "0"));
  if ((!allowZero && grams === 0n) || grams > 1_000_000_000_000n)
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
