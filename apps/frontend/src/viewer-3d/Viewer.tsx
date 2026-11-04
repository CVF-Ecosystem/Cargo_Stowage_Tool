import { useRef, useState } from "react";
import type { ProfileDetail } from "../api/client";
import { footprint, formatMetres, type Plan } from "../features/model";
import type { PackingIndex } from "../features/packing";
import Scene from "./Scene";
import {
  isWarnUnit,
  PIPE_BUDGET,
  RING_BUDGET,
  type CargoView,
  type PackingInfo,
} from "./packingMeshes";

const count = new Intl.NumberFormat("vi-VN");
const n = (v: number) => count.format(v);

// Status line for the cargo view. Counts come from the scene's last build (derived geometry, not measurements).
function packingStatus(
  view: CargoView,
  info: PackingInfo | null,
  hasPacking: boolean,
): string {
  if (view === "ENVELOPE")
    return "Khối bao: mỗi bó là một khối chữ nhật bao quanh; chưa hiện từng ống.";
  if (!hasPacking)
    return "Chưa có dữ liệu xếp ống dẫn xuất; đang hiện khối bao.";
  if (!info || info.view !== view) return "Đang dựng cách nhìn hàng…";
  const warn = info.envelopeOnlyBundles
    ? ` · ${n(info.envelopeOnlyBundles)} bó chỉ khối bao (cảnh báo)`
    : "";
  if (view === "DETAILED") {
    if (info.capped && info.detailedBundles < info.candidateBundles)
      return `Vượt hạn mức ${n(PIPE_BUDGET)} ống: chỉ hiện chi tiết ${n(info.detailedBundles)} bó (bó đang chọn và bó trong khung nhìn); ${n(info.candidateBundles - info.detailedBundles)} bó còn lại giữ bó giản lược.${warn}`;
    return `Chi tiết ống (dẫn xuất, không phải số đo): ${n(info.detailedBundles)}/${n(info.candidateBundles)} bó hiện chi tiết${warn}`;
  }
  if (info.capped)
    return `Vượt hạn mức ${n(RING_BUDGET)} vòng đầu ống: chỉ hiện vòng ống cho ${n(info.simplifiedBundles)} bó; ${n(info.budgetBoxBundles)} bó còn lại giữ khối bao mờ.${warn}`;
  return `Bó giản lược (dẫn xuất, không phải số đo): ${n(info.simplifiedBundles)}/${n(info.candidateBundles)} bó hiện vòng ống hai đầu${warn}`;
}

type Props = {
  plan: Plan;
  profile: ProfileDetail | null;
  selected: string;
  onSelect: (id: string) => void;
  issueIds: Set<string>;
  packing?: PackingIndex | null;
};

export default function Viewer(props: Props) {
  const [view, setView] = useState<"3d" | "2d">("3d");
  const [failed, setFailed] = useState(false);
  const [cameraCommand, setCameraCommand] = useState({
    kind: "fit",
    serial: 0,
  });
  const [ghost, setGhost] = useState(true);
  const [shipVisible, setShipVisible] = useState(true);
  const [assetStatus, setAssetStatus] = useState("");
  const [cargoView, setCargoView] = useState<CargoView>("ENVELOPE");
  const [packingInfo, setPackingInfo] = useState<PackingInfo | null>(null);
  const packingInfoRef = useRef((info: PackingInfo) =>
    setPackingInfo((prev) =>
      prev && JSON.stringify({ ...prev, buildMs: 0 }) === JSON.stringify({ ...info, buildMs: 0 })
        ? prev
        : info,
    ),
  );
  const failureRef = useRef(() => {
    setFailed(true);
    setView("2d");
  });
  const { plan, selected, onSelect, issueIds } = props;
  const packing = props.packing ?? null;
  const pipePlan = plan.units.some((u) => u.source_ref?.group_id);
  const warnIds = new Set(
    plan.units.filter((u) => isWarnUnit(packing, u)).map((u) => u.id),
  );
  const margin = 1100;
  const unitMap = new Map(plan.units.map((u) => [u.id, u]));
  return (
    <section className="viewer-card" aria-label="Mô hình chất xếp">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">PHƯƠNG ÁN / 01</span>
          <h2>Không gian chất xếp</h2>
        </div>
        <div className="view-toggle" aria-label="Chế độ xem">
          <button
            className={view === "3d" ? "active" : ""}
            onClick={() => {
              setFailed(false);
              setView("3d");
            }}
            aria-pressed={view === "3d"}
          >
            3D
          </button>
          <button
            className={view === "2d" ? "active" : ""}
            onClick={() => setView("2d")}
            aria-pressed={view === "2d"}
          >
            Mặt bằng
          </button>
        </div>
      </div>
      <div className="viewport">
        <div className="viewport-label">
          <span className="dot" />
          BOX · MỘT LỚP <span className="muted">/</span> {plan.hold.name}
        </div>
        {view === "3d" ? (
          <Scene
            {...props}
            onFailure={failureRef.current}
            cameraCommand={cameraCommand}
            shipVisible={shipVisible}
            ghost={ghost}
            onAssetStatus={setAssetStatus}
            cargoView={cargoView}
            packing={packing}
            onPackingInfo={packingInfoRef.current}
          />
        ) : (
          <svg
            className="plan-svg"
            viewBox={`${-margin} ${-margin} ${plan.hold.length_mm + 2 * margin} ${plan.hold.width_mm + 2 * margin}`}
            role="img"
            aria-label="Mặt bằng hầm và ID từng bó"
          >
            <defs>
              <pattern
                id="floor-grid"
                width="1000"
                height="1000"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 1000 0 L 0 0 0 1000"
                  fill="none"
                  stroke="#ccd8cf"
                  strokeWidth="20"
                />
              </pattern>
            </defs>
            <rect
              width={plan.hold.length_mm}
              height={plan.hold.width_mm}
              fill="url(#floor-grid)"
              stroke="#7f9a8a"
              strokeWidth="50"
            />
            {plan.placements.map((p) => {
              const u = unitMap.get(p.unit_id)!;
              const [w, h] = footprint(u, p);
              return (
                <g
                  key={u.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`Chọn ${u.id}`}
                  aria-pressed={selected === u.id}
                  onClick={() => onSelect(u.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onSelect(u.id);
                    }
                  }}
                  className="svg-unit"
                >
                  <rect
                    x={p.x_mm}
                    y={p.y_mm}
                    width={w}
                    height={h}
                    rx="60"
                    fill={
                      selected === u.id
                        ? "#9ed7bb"
                        : issueIds.has(u.id)
                          ? "#cf8275"
                          : u.kind === "BAR_BUNDLE"
                            ? "#388778"
                            : "#c69b56"
                    }
                    stroke={
                      selected === u.id
                        ? "#173e31"
                        : warnIds.has(u.id)
                          ? "#e07a1f"
                          : "#ffffff"
                    }
                    strokeWidth={selected === u.id ? 65 : warnIds.has(u.id) ? 40 : 20}
                    strokeDasharray={warnIds.has(u.id) ? "120 70" : undefined}
                  />
                  <text
                    x={p.x_mm + w / 2}
                    y={p.y_mm + h / 2 + 75}
                    textAnchor="middle"
                    fontSize="240"
                    fill={selected === u.id ? "#173e31" : "#fff"}
                  >
                    {u.id}
                  </text>
                </g>
              );
            })}
            <text
              x={plan.hold.length_mm / 2}
              y={plan.hold.width_mm + 650}
              textAnchor="middle"
              fontSize="300"
              fill="#587064"
            >
              X · {formatMetres(plan.hold.length_mm)} m
            </text>
            <text x="0" y="-400" fontSize="260" fill="#587064">
              Gốc (0, 0) · Y theo chiều rộng
            </text>
          </svg>
        )}
        <div className="viewport-bottom">
          <span>
            {failed
              ? "WebGL không khả dụng · đang dùng mặt bằng 2D"
              : view === "3d"
                ? "Kéo để xoay · Cuộn để zoom · Bấm bó để chọn"
                : "Bấm bó hoặc dùng Tab + Enter để chọn"}
          </span>
          {view === "3d" && (
            <button
              className="icon-button"
              onClick={() =>
                setCameraCommand((c) => ({ kind: "fit", serial: c.serial + 1 }))
              }
              aria-label="Đặt lại góc nhìn"
            >
              ↺
            </button>
          )}
        </div>
      </div>
      {view === "3d" && (
        <div className="viewer-controls" aria-label="Góc nhìn 3D">
          {[
            ["fit", "Vừa khung"],
            ["top", "Nhìn trên"],
            ["side", "Nhìn mạn"],
            ["focus", "Tập trung bó"],
          ].map(([kind, label]) => (
            <button
              key={kind}
              type="button"
              className="button secondary"
              disabled={
                kind === "focus" &&
                !plan.placements.some((p) => p.unit_id === selected)
              }
              onClick={() =>
                setCameraCommand((c) => ({ kind, serial: c.serial + 1 }))
              }
            >
              {label}
            </button>
          ))}
        </div>
      )}
      {view === "3d" && (pipePlan || packing) && (
        <div className="cargo-view">
          <label className="cargo-view-label">
            <span>Cách nhìn hàng</span>
            <select
              aria-label="Cách nhìn hàng"
              value={cargoView}
              disabled={!packing}
              onChange={(e) => setCargoView(e.target.value as CargoView)}
            >
              <option value="ENVELOPE">Khối bao</option>
              <option value="SIMPLIFIED">Bó giản lược</option>
              <option value="DETAILED">Chi tiết ống</option>
            </select>
          </label>
          <p
            className="cargo-view-status"
            data-testid="packing-view-status"
            role="status"
          >
            {packingStatus(cargoView, packingInfo, !!packing)}
          </p>
        </div>
      )}
      {plan.placements.length === 0 && (
        <p className="scope-note" role="status">
          Chưa có bó nào được đặt. Chọn Xếp thử tự động → Áp dụng xếp thử, hoặc
          đặt từng bó bằng tay.
        </p>
      )}
      {plan.source === "MIXED_REFERENCE" && (
        <div className="scope-note">
          <button
            className="button secondary"
            onClick={() => setShipVisible((v) => !v)}
            aria-pressed={shipVisible}
          >
            {shipVisible ? "Ẩn tàu" : "Hiện tàu"}
          </button>
          <button
            className="button secondary"
            onClick={() => setGhost((v) => !v)}
          >
            {ghost ? "Vật liệu gốc" : "Thân mờ"}
          </button>
          <p role="status">
            {assetStatus} Màu thân GLB cố định theo mớn 4,85 m; khung xanh biểu
            thị mớn tham chiếu đã chọn.
          </p>
        </div>
      )}
      <div className="viewer-legend">
        <span>
          <i className="swatch steel" />
          Thép thanh
        </span>
        <span>
          <i className="swatch pipe" />
          Thép ống
        </span>
        <span>
          <i className="swatch selected" />
          Đang chọn
        </span>
        {cargoView !== "ENVELOPE" && view === "3d" && packing && (
          <span>
            <i className="swatch derived-pipe" />
            Ống dẫn xuất (không phải số đo)
          </span>
        )}
        {warnIds.size > 0 && (
          <span>
            <i className="swatch warn-outline" />
            Chỉ khối bao (cảnh báo)
          </span>
        )}
        <span className="legend-end">Khối bao bó hàng · cm</span>
      </div>
    </section>
  );
}
