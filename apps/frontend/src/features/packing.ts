// SUP-03 derived packing (D1-D3). Read-only view keyed by cargo revision and group; never part of Plan or snapshot JSON.
// All geometry is exact integer µm from the server; rounding to cm happens only in display helpers here.
import type { Plan, Unit } from "./model";

export type PackingStatus = "DETAILED" | "ENVELOPE_ONLY";
export type PackingLayout = "RECT" | "HEX";
export type PackingReasonCode =
  | "OD_MISSING"
  | "OD_EXCEEDS_SECTION"
  | "PIECES_DO_NOT_FIT"
  | "INPUT_INVALID"
  | "ENVELOPE_LOOSE"
  | "SOURCE_WARNING";
export type PackingReason = { code: PackingReasonCode; message: string };
export type PackingChecks = { count: boolean; od_fit: boolean; envelope_fit: boolean; slack_loose: boolean };
/** Packing of one cross-section (a group, or one bundle whose dimensions are overridden). */
export type PackingCore = {
  status: PackingStatus;
  basis: "DERIVED";
  layout: PackingLayout | null;
  columns: number;
  rows: number;
  od_um: number | null;
  wall_thickness_um: number | null;
  length_um: number;
  section_um: number[]; // [width, height]
  pieces_source: number;
  pieces_placed: number;
  max_fit: number;
  pipe_centres_um: number[][]; // [y, z] per pipe, origin bottom-left of the section
  slack_um: number[] | null; // [width, height]
  checks: PackingChecks;
  reasons: PackingReason[];
};
export type BundlePacking = PackingCore & { bundle_id: string };
export type GroupPacking = PackingCore & {
  group_id: string;
  bundle_count: number;
  bundle_packings: BundlePacking[];
};
export type PackingStats = {
  group_count: number;
  groups_by_status: Record<PackingStatus, number>;
  bundle_count: number;
  bundles_by_status: Record<PackingStatus, number>;
  derived_pieces: number;
  source_pieces: number;
};
export type RevisionPacking = {
  dataset_id: string;
  revision_id: string;
  content_sha256: string;
  basis: "DERIVED";
  groups: GroupPacking[];
  stats: PackingStats;
};

export async function getRevisionPacking(revisionId: string): Promise<RevisionPacking> {
  let response: Response;
  try {
    response = await fetch(`/api/cargo-revisions/${encodeURIComponent(revisionId)}/packing`, { signal: AbortSignal.timeout(15000) });
  } catch {
    throw new Error("Không đọc được cách xếp ống dẫn xuất; hiển thị khối bao.");
  }
  if (!response.ok) {
    let message = "Không đọc được cách xếp ống dẫn xuất; hiển thị khối bao.";
    try {
      const detail = ((await response.json()) as { detail?: unknown }).detail;
      if (typeof detail === "string") message = detail;
      else if (detail && typeof detail === "object" && typeof (detail as { message?: unknown }).message === "string")
        message = (detail as { message: string }).message;
    } catch {
      /* keep fallback */
    }
    throw new Error(message);
  }
  return (await response.json()) as RevisionPacking;
}

/** Revision a pipe plan is pinned to: v1 -> R0000 implicitly, v2 -> plan.cargo_revision. null for non-pipe plans. */
export function planRevisionId(plan: Plan): string | null {
  if (plan.contract_version === "scst.pipe-list.v1") return "BALTIMORE-PIPE-V1-1@R0000";
  if (plan.contract_version === "scst.pipe-list.v2") return plan.cargo_revision?.revision_id ?? null;
  return null;
}

export type PackingIndex = { groups: Map<string, GroupPacking>; bundles: Map<string, BundlePacking> };
export function indexPacking(p: RevisionPacking | null): PackingIndex {
  const groups = new Map<string, GroupPacking>(),
    bundles = new Map<string, BundlePacking>();
  for (const g of p?.groups ?? []) {
    groups.set(g.group_id, g);
    for (const b of g.bundle_packings) bundles.set(b.bundle_id, b);
  }
  return { groups, bundles };
}
/** Packing for one plan unit: a bundle-level override wins over its group; null when not a pipe unit or unknown. */
export function packingFor(index: PackingIndex, unit: Unit): PackingCore | null {
  const gid = unit.source_ref?.group_id;
  if (!gid) return null;
  return index.bundles.get(unit.id) ?? index.groups.get(gid) ?? null;
}

export const statusLabel = (s: PackingStatus) => (s === "DETAILED" ? "Chi tiết (dẫn xuất)" : "Chỉ khối bao");
export const layoutLabel = (p: PackingCore) => (p.layout ? `${p.layout} ${p.columns} × ${p.rows}` : "—");
