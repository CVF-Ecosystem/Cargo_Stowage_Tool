// SUP-03 D5: derived packing of one bundle/group, shown as DERIVED (not measured). Display rounding only.
import type { PackingCore, PackingStatus } from "./packing";
import { layoutLabel, statusLabel } from "./packing";

const cm = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 });
const mm = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 3 });
/** µm -> cm text, display only (one decimal). */
export const slackText = (p: PackingCore) =>
  p.slack_um ? `${cm.format(p.slack_um[0] / 10000)} × ${cm.format(p.slack_um[1] / 10000)} cm` : "—";
export const piecesText = (p: PackingCore) => `${p.pieces_placed}/${p.pieces_source} ống`;
export const packingCell = (p: PackingCore | null) =>
  p ? `${statusLabel(p.status)} · ${layoutLabel(p)} · ${piecesText(p)}` : "—";

export type PackingFilter = "ALL" | PackingStatus;
export const packingFilterOptions: [PackingFilter, string][] = [
  ["ALL", "Tất cả trạng thái"],
  ["DETAILED", "Chi tiết (dẫn xuất)"],
  ["ENVELOPE_ONLY", "Chỉ khối bao"],
];

export default function PackingInfo({
  packing,
  groupId,
  error,
  onOpenGroup,
}: {
  packing: PackingCore | null;
  groupId: string | null;
  error: string;
  onOpenGroup: (groupId: string) => void;
}) {
  if (!groupId) return null;
  if (!packing)
    return (
      <div className="packing-info" data-testid="packing-info">
        <p>{error || "Đang đọc cách xếp ống dẫn xuất…"}</p>
      </div>
    );
  return (
    <div className={`packing-info packing-${packing.status.toLowerCase()}`} data-testid="packing-info">
      <p>
        <strong data-testid="packing-status">{statusLabel(packing.status)}</strong> · cách xếp dẫn xuất từ dữ liệu
        revision, không phải số đo thực.
      </p>
      <p>
        Cách xếp: {layoutLabel(packing)} · {piecesText(packing)} (nguồn {packing.pieces_source}) · OD{" "}
        {packing.od_um === null ? "—" : `${mm.format(packing.od_um / 1000)} mm`} · phần dư rộng × cao {slackText(packing)}
      </p>
      {packing.reasons.length > 0 && (
        <ul className="packing-reasons" aria-label="Lý do cách xếp">
          {packing.reasons.map((r) => (
            <li key={r.code} data-testid={`packing-reason-${r.code}`}>
              <button
                type="button"
                className="text-button"
                aria-label={`Mở nhóm ${groupId} trong Dữ liệu hàng (${r.code})`}
                onClick={() => onOpenGroup(groupId)}
              >
                {r.code}
              </button>{" "}
              {r.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
