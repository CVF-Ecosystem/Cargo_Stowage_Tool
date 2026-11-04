import { useCallback, useEffect, useState, type ReactNode } from "react";
import { getPlanReport, getVesselProfile, openSnapshot, type PlanReport, type ProfileDetail } from "../api/client";
import Viewer from "../viewer-3d/Viewer";
import { displayTime, type Evaluation } from "./model";
import { getRevisionPacking, indexPacking, planRevisionId, type PackingIndex } from "./packing";

type Report = PlanReport;
type ReportUnit = Report["units"][number];
type ReportPacking = NonNullable<ReportUnit["packing"]>;
type FieldStatus = Report["hold"]["status"];

const NO_ISSUES = new Set<string>();
const NOOP = () => {};
const AUTO_CAPTURE_MS = 2500;

const FIELD_LABEL: Record<FieldStatus, string> = {
  ESTIMATED: "ước tính",
  SOURCED: "lấy từ hồ sơ",
  MEASURED: "đã đo",
  UNCONFIRMED: "chưa xác nhận",
};
const RECHECK_LABEL: Record<Report["cargo"]["recheck"]["status"], string> = {
  CURRENT: "Theo dữ liệu mới nhất",
  NEEDS_RECHECK: "Cần kiểm lại",
  NOT_APPLICABLE: "Không áp dụng",
  REVISION_UNAVAILABLE: "Không kiểm lại được",
};
const REQUIREMENT_LABEL: Record<ReportUnit["requirement"], string> = {
  required: "Bắt buộc",
  optional: "Tùy chọn",
  excluded: "Loại trừ",
};
const UNIT_STATUS_LABEL: Record<ReportUnit["status"], string> = {
  PLACED: "Đã xếp",
  UNPLACED: "Chưa xếp",
  EXCLUDED: "Loại trừ",
};
const PACKING_LABEL: Record<ReportPacking["status"], string> = {
  DETAILED: "Chi tiết (dẫn xuất)",
  ENVELOPE_ONLY: "Chỉ khối bao",
};

// ---- Exact display helpers. Inputs are the model's integers; only integer string arithmetic, no float division. ----
const sign = (n: number) => (n < 0 ? "-" : "");
const groupDigits = (digits: string) => digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const pad = (n: number, width: number) => String(n).padStart(width, "0");
const splitBy = (a: number, base: number) => {
  const rest = a % base;
  return { whole: (a - rest) / base, rest };
};

/** grams -> kg with exactly 3 decimals, e.g. 911400 -> "911,400". */
export function kgText(g: number): string {
  const { whole, rest } = splitBy(Math.abs(g), 1000);
  return `${sign(g)}${groupDigits(String(whole))},${pad(rest, 3)}`;
}
/** micrometres -> cm, exact, trailing zeros trimmed, e.g. 6000000 -> "600", 12345 -> "1,2345". */
export function cmText(um: number): string {
  const { whole, rest } = splitBy(Math.abs(um), 10000);
  const frac = pad(rest, 4).replace(/0+$/, "");
  return `${sign(um)}${groupDigits(String(whole))}${frac ? `,${frac}` : ""}`;
}
/** millimetres -> m with exactly 3 decimals, e.g. 12345 -> "12,345". */
export function mText(mm: number): string {
  const { whole, rest } = splitBy(Math.abs(mm), 1000);
  return `${sign(mm)}${groupDigits(String(whole))},${pad(rest, 3)}`;
}
/** grams -> t, rounded half-up to whole kg (3 decimals in t), e.g. 1000000000 -> "1.000,000". */
export function tText(g: number): string {
  const a = Math.abs(g);
  const remainder = a % 1000;
  const kg = (a - remainder + (remainder >= 500 ? 1000 : 0)) / 1000;
  const { whole, rest } = splitBy(kg, 1000);
  return `${sign(g)}${groupDigits(String(whole))},${pad(rest, 3)}`;
}

const yawSwaps = (yaw: number) => ((yaw % 180) + 180) % 180 === 90;

function hasWebgl(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

const errorText = (e: unknown, fallback: string) => (e instanceof Error && e.message ? e.message : fallback);

function MassCell({ g }: { g: number }) {
  return (
    <>
      {kgText(g)} kg <span className="report-exact">(<span data-exact>{g}</span> g)</span>
    </>
  );
}

function TonneCell({ g }: { g: number }) {
  return (
    <>
      {tText(g)} t <span className="report-exact">(<span data-exact>{g}</span> g)</span>
    </>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="report-field">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function PlanSvg({ report }: { report: Report }) {
  const length = report.hold.length_mm;
  const width = report.hold.width_mm;
  const margin = Math.max(400, Math.round(Math.max(length, width) * 0.03));
  const labelSize = Math.round(margin * 0.5);
  const placed = report.units.filter((u) => u.status === "PLACED" && u.placement);
  return (
    <svg
      className="report-plan-svg"
      data-testid="report-plan-svg"
      role="img"
      aria-label="Hình chiếu bằng hầm và hàng đã xếp"
      viewBox={`${-margin} ${-margin} ${length + 2 * margin} ${width + 2 * margin}`}
    >
      <rect className="report-hold-outline" x={0} y={0} width={length} height={width} strokeWidth={margin / 8} />
      {placed.map((u) => {
        const p = u.placement!;
        const [dx, dy] = u.dimensions_um.map((v) => v / 1000);
        const w = yawSwaps(p.yaw_deg) ? dy : dx;
        const h = yawSwaps(p.yaw_deg) ? dx : dy;
        const fontSize = Math.min(w, h) * 0.3;
        return (
          <g key={u.id}>
            <rect className="report-unit-rect" data-unit={u.id} x={p.x_mm} y={p.y_mm} width={w} height={h} strokeWidth={margin / 20}>
              <title>{`${u.id} · ${u.name}`}</title>
            </rect>
            {fontSize >= labelSize / 4 && (
              <text className="report-unit-label" x={p.x_mm + w / 2} y={p.y_mm + h / 2} fontSize={Math.min(fontSize, labelSize)} textAnchor="middle" dominantBaseline="middle">
                {u.id}
              </text>
            )}
          </g>
        );
      })}
      <text className="report-svg-label" x={0} y={-margin / 2} fontSize={labelSize}>
        Gốc (0, 0) · đơn vị mm · dài {mText(length)} m × rộng {mText(width)} m
      </text>
    </svg>
  );
}

export default function ReportPage({ id }: { id: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [evaluationError, setEvaluationError] = useState("");
  const [profile, setProfile] = useState<ProfileDetail | null>(null);
  const [packing, setPacking] = useState<PackingIndex | null>(null);
  const [webglOk, setWebglOk] = useState(hasWebgl);
  const [captureSerial, setCaptureSerial] = useState(0);
  const [image, setImage] = useState("");
  const onWebglUnavailable = useCallback(() => setWebglOk(false), []);
  const onCapture = useCallback((dataUrl: string) => setImage(dataUrl), []);

  useEffect(() => {
    let live = true;
    (async () => {
      let loaded: Report;
      try {
        loaded = await getPlanReport(id);
      } catch (e) {
        if (live) setError(errorText(e, "Không đọc được báo cáo phương án."));
        return;
      }
      if (!live) return;
      setReport(loaded);
      const snapshotLoad = openSnapshot(id).then(
        (ev) => {
          if (live) setEvaluation(ev);
          return ev;
        },
        (e: unknown) => {
          if (live) setEvaluationError(errorText(e, "Không mở được phương án để dựng hình 3D."));
          return null;
        },
      );
      const profileLoad = loaded.vessel
        ? getVesselProfile(loaded.vessel.vessel_id, loaded.vessel.profile_version ?? 1).then(
            (p) => {
              if (live) setProfile(p);
            },
            () => undefined,
          )
        : Promise.resolve();
      const ev = await snapshotLoad;
      if (ev) {
        const revisionId = planRevisionId(ev.plan);
        if (revisionId)
          getRevisionPacking(revisionId)
            .then((p) => {
              if (live && p.revision_id === revisionId) setPacking(indexPacking(p));
            })
            .catch(() => undefined);
      }
      await profileLoad;
    })();
    return () => {
      live = false;
    };
  }, [id]);

  const viewerReady = Boolean(report && evaluation && webglOk);
  useEffect(() => {
    if (!viewerReady) return;
    // One automatic capture after the viewer has mounted; the user can capture again from the button.
    const timer = window.setTimeout(() => setCaptureSerial((c) => c + 1), AUTO_CAPTURE_MS);
    return () => window.clearTimeout(timer);
  }, [viewerReady]);

  const backLink = (
    <nav className="report-toolbar no-print" aria-label="Thao tác báo cáo">
      <a className="button secondary" href="#/">
        Quay lại phương án
      </a>
    </nav>
  );

  if (error)
    return (
      <div className="report-page">
        {backLink}
        <p className="report-alert" role="alert">
          {error}
        </p>
      </div>
    );
  if (!report)
    return (
      <div className="report-page">
        {backLink}
        <p role="status">Đang tải báo cáo…</p>
      </div>
    );

  const h = report.header;
  const hold = report.hold;
  const totals = report.totals;
  const issues = report.issues;
  const recheck = report.cargo.recheck;
  const vessel = report.vessel;
  type TotalKey = "unit_count" | "placed_count" | "unplaced_count" | "excluded_count" | "manifest_mass_g" | "placed_mass_g" | "remaining_capacity_g";
  const totalRows: { key: TotalKey; label: string; kind: "count" | "mass" }[] = [
    { key: "unit_count", label: "Tổng số bó", kind: "count" },
    { key: "placed_count", label: "Đã xếp", kind: "count" },
    { key: "unplaced_count", label: "Chưa xếp", kind: "count" },
    { key: "excluded_count", label: "Loại trừ", kind: "count" },
    { key: "manifest_mass_g", label: "Khối lượng danh sách", kind: "mass" },
    { key: "placed_mass_g", label: "Khối lượng đã xếp", kind: "mass" },
    { key: "remaining_capacity_g", label: "Khả năng còn lại", kind: "mass" },
  ];

  return (
    <div className="report-page">
      <nav className="report-toolbar no-print" aria-label="Thao tác báo cáo">
        <button type="button" className="button" onClick={() => window.print()}>
          In / Lưu PDF
        </button>
        <a className="button secondary" href={`/api/snapshots/${id}/report.xlsx`} download>
          Tải XLSX
        </a>
        <a className="button secondary" href="#/">
          Quay lại phương án
        </a>
      </nav>

      <header className="report-header" data-testid="report-header">
        <p className="report-eyebrow">SCST · Báo cáo phương án</p>
        <h1>Báo cáo phương án xếp hàng</h1>
        <h2 className="report-plan-name" data-testid="report-plan-name">
          {h.plan_name}
        </h2>
        <dl className="report-meta">
          <Field label="Mã ảnh chụp">
            <span className="report-sha">{h.snapshot_id}</span>
          </Field>
          <Field label="Thời điểm lưu">{displayTime(h.saved_utc)}</Field>
          <Field label="Phiên bản hợp đồng">
            {h.contract_version} · lưu {h.schema_version}
          </Field>
          <Field label="SHA-256 phương án">
            <span className="report-sha">{h.plan_sha256}</span>
          </Field>
          <Field label="SHA-256 báo cáo">
            <span className="report-sha" data-testid="report-sha">
              {report.report_sha256}
            </span>
          </Field>
          <Field label="Thời điểm tạo báo cáo">{displayTime(h.generated_utc)}</Field>
        </dl>
      </header>

      <section className="report-notices" data-testid="report-notices" aria-label="Cảnh báo bắt buộc">
        <h2>Cảnh báo bắt buộc</h2>
        <ul>
          {report.notices.map((n, i) => (
            <li key={`${n.code}-${i}`} data-testid={`notice-${n.code}`}>
              {n.message}
            </li>
          ))}
        </ul>
      </section>

      <section className="report-section" aria-labelledby="report-info-title">
        <h2 id="report-info-title">Thông tin phương án</h2>
        <div className="report-grid">
          <article className="report-card">
            <h3>Tàu</h3>
            {vessel ? (
              <dl>
                <Field label="Tên tàu">{vessel.name}</Field>
                <Field label="Mã tàu">{vessel.vessel_id}</Field>
                <Field label="Trường hợp">{vessel.case_id}</Field>
                <Field label="Phiên bản hồ sơ">{vessel.profile_version ?? "—"}</Field>
                <Field label="SHA-256 hồ sơ">
                  <span className="report-sha">{vessel.profile_sha256 ?? "—"}</span>
                </Field>
                <Field label="Trạng thái trường dữ liệu">
                  Kích thước: {FIELD_LABEL[vessel.field_status.dimensions_m]} · Hầm: {FIELD_LABEL[vessel.field_status.hold]} · Trường hợp:{" "}
                  {FIELD_LABEL[vessel.field_status.cases]}
                </Field>
              </dl>
            ) : (
              <p>Không có hồ sơ tàu</p>
            )}
          </article>

          <article className="report-card">
            <h3>Hầm hàng</h3>
            <dl>
              <Field label="Tên hầm">{hold.name}</Field>
              <Field label="Kích thước (m)">
                Dài {mText(hold.length_mm)} × rộng {mText(hold.width_mm)} × cao {mText(hold.height_mm)} m
              </Field>
              <Field label="Kích thước chính xác (mm)">
                <span data-testid="report-hold-exact">
                  {hold.length_mm} × {hold.width_mm} × {hold.height_mm} mm
                </span>
              </Field>
              <Field label="Trạng thái">{FIELD_LABEL[hold.status] ?? hold.status}</Field>
            </dl>
          </article>

          <article className="report-card">
            <h3>Giới hạn trọng lượng</h3>
            <dl>
              <Field label="Giới hạn theo chứng nhận">
                <TonneCell g={report.limits.certificate_cargo_limit_g} />
              </Field>
              <Field label="Giới hạn chuyến đi">
                <TonneCell g={report.limits.voyage_cargo_limit_g} />
              </Field>
              <Field label="Hàng đang trên tàu">
                <TonneCell g={report.limits.cargo_onboard_g} />
              </Field>
              <Field label="Khả năng còn lại (chuyến đi)">
                <TonneCell g={report.limits.available_capacity_g} />
              </Field>
            </dl>
          </article>

          <article className="report-card">
            <h3>Dữ liệu hàng</h3>
            <dl>
              <Field label="Nguồn phương án">{report.cargo.plan_source}</Field>
              <Field label="Nguồn hàng">{report.cargo.cargo_source ?? "—"}</Field>
              <Field label="Bộ dữ liệu">
                <span className="report-sha">{report.cargo.dataset_id ?? "—"}</span>
              </Field>
              <Field label="Revision">
                <span className="report-sha">{report.cargo.revision_id ?? "—"}</span>
              </Field>
              <Field label="SHA-256 nội dung">
                <span className="report-sha">{report.cargo.content_sha256 ?? "—"}</span>
              </Field>
              <Field label="Kiểm lại">
                <p className="report-recheck" data-testid="report-recheck">
                  <strong>{RECHECK_LABEL[recheck.status]}</strong> · thêm {recheck.added}, bỏ {recheck.removed}, đổi {recheck.changed} bó;{" "}
                  {recheck.placed_affected} bó đã đặt bị ảnh hưởng
                  {recheck.latest_revision_id && (
                    <>
                      {" "}· revision mới nhất: <span className="report-sha">{recheck.latest_revision_id}</span>
                    </>
                  )}
                </p>
              </Field>
            </dl>
          </article>
        </div>
      </section>

      <section className="report-section" aria-labelledby="report-totals-title">
        <h2 id="report-totals-title">Tổng</h2>
        <div className="report-table-wrap">
          <table className="report-table" data-testid="report-totals">
            <thead>
              <tr>
                <th scope="col">Mục</th>
                <th scope="col">Giá trị</th>
              </tr>
            </thead>
            <tbody>
              {totalRows.map((row) => (
                <tr key={row.key} data-testid={`report-total-${row.key}`}>
                  <th scope="row">{row.label}</th>
                  <td>{row.kind === "count" ? totals[row.key] : <MassCell g={totals[row.key]} />}</td>
                </tr>
              ))}
              <tr data-testid="report-total-manifest_envelope_volume_mm3">
                <th scope="row">Thể tích khối bao danh sách</th>
                <td>
                  {totals.manifest_envelope_volume_mm3_text} mm³
                </td>
              </tr>
              <tr data-testid="report-total-placed_envelope_volume_mm3">
                <th scope="row">Thể tích khối bao đã xếp</th>
                <td>{totals.placed_envelope_volume_mm3_text} mm³</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="report-section" aria-labelledby="report-plan-title">
        <h2 id="report-plan-title">Hình chiếu bằng</h2>
        <figure className="report-figure">
          <PlanSvg report={report} />
          <figcaption>Hình chiếu bằng từ cùng vị trí đã lưu (mm); khung ngoài là hầm hàng.</figcaption>
        </figure>
      </section>

      <section className="report-section" aria-labelledby="report-3d-title">
        <h2 id="report-3d-title">Hình 3D minh họa</h2>
        {webglOk ? (
          <figure className="report-3d" data-testid="report-3d">
            {evaluation ? (
              <div className="no-print report-live-viewer">
                <Viewer
                  plan={evaluation.plan}
                  profile={profile}
                  selected=""
                  onSelect={NOOP}
                  issueIds={NO_ISSUES}
                  packing={packing}
                  captureSerial={captureSerial}
                  onCapture={onCapture}
                  onWebglUnavailable={onWebglUnavailable}
                />
              </div>
            ) : evaluationError ? (
              <p className="report-alert" role="alert">
                {evaluationError}
              </p>
            ) : (
              <p role="status">Đang dựng hình 3D…</p>
            )}
            <div className="no-print report-3d-actions">
              <button type="button" className="button secondary" disabled={!evaluation} onClick={() => setCaptureSerial((c) => c + 1)}>
                Chụp ảnh 3D
              </button>
            </div>
            {image ? (
              <img data-testid="report-3d-image" alt="Ảnh minh họa 3D của phương án" src={image} />
            ) : (
              <p className="no-print" role="status">
                {evaluation ? "Chưa có ảnh 3D; bấm Chụp ảnh 3D." : ""}
              </p>
            )}
            <figcaption>Ảnh minh họa 3D từ viewer (không phải bản vẽ kỹ thuật).</figcaption>
          </figure>
        ) : (
          <p data-testid="report-3d-missing">
            Không có ảnh 3D: trình duyệt không hỗ trợ WebGL; các phần còn lại của báo cáo vẫn đầy đủ.
          </p>
        )}
      </section>

      <section className="report-section" aria-labelledby="report-units-title">
        <h2 id="report-units-title">Danh sách bó hàng ({report.units.length})</h2>
        <div className="report-table-wrap">
          <table className="report-table report-units" data-testid="report-units">
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">Tên</th>
                <th scope="col">Nhóm</th>
                <th scope="col">Yêu cầu</th>
                <th scope="col">Trạng thái</th>
                <th scope="col">Kích thước (cm)</th>
                <th scope="col">Khối lượng</th>
                <th scope="col">Vị trí X/Y/Z (m)</th>
                <th scope="col">Góc</th>
                <th scope="col">Packing</th>
                <th scope="col">Chính xác (g · µm)</th>
              </tr>
            </thead>
            <tbody>
              {report.units.map((u) => (
                <tr
                  key={u.id}
                  data-testid={`report-unit-${u.id}`}
                  data-mass-g={u.mass_g}
                  data-dims-um={u.dimensions_um.join(",")}
                  data-x-mm={u.placement?.x_mm}
                  data-y-mm={u.placement?.y_mm}
                >
                  <td>{u.id}</td>
                  <td>{u.name}</td>
                  <td>{u.group_id ?? "—"}</td>
                  <td>{REQUIREMENT_LABEL[u.requirement]}</td>
                  <td>{UNIT_STATUS_LABEL[u.status]}</td>
                  <td className="report-nums">
                    {u.dimensions_um.map(cmText).join(" × ")}
                  </td>
                  <td className="report-nums">
                    <MassCell g={u.mass_g} />
                  </td>
                  <td className="report-nums">
                    {u.placement
                      ? `${mText(u.placement.x_mm)} / ${mText(u.placement.y_mm)} / ${mText(u.placement.z_mm)}`
                      : "—"}
                  </td>
                  <td>{u.placement ? `${u.placement.yaw_deg}°` : "—"}</td>
                  <td>
                    {u.packing ? (
                      <>
                        {PACKING_LABEL[u.packing.status]} · {u.packing.layout ? `${u.packing.layout} ${u.packing.columns}×${u.packing.rows}` : "—"} · ống{" "}
                        {u.packing.pieces_placed}/{u.packing.pieces_source}
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="report-nums">
                    {u.mass_g} g · {u.dimensions_um.join(" × ")} µm
                    {u.placement && (
                      <>
                        {" "}· vị trí {u.placement.x_mm}, {u.placement.y_mm}, {u.placement.z_mm} mm
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="report-section" aria-labelledby="report-unplaced-title">
        <h2 id="report-unplaced-title">Hàng chưa xếp ({report.unplaced.length})</h2>
        {(
          <div className="report-table-wrap">
            <table className="report-table" data-testid="report-unplaced">
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Tên</th>
                  <th scope="col">Trạng thái</th>
                  <th scope="col">Khối lượng</th>
                  <th scope="col">Lý do</th>
                </tr>
              </thead>
              <tbody>
                {report.unplaced.map((u) => (
                  <tr key={u.id} data-testid={`report-unplaced-${u.id}`}>
                    <td>{u.id}</td>
                    <td>{u.name}</td>
                    <td>{UNIT_STATUS_LABEL[u.status]}</td>
                    <td className="report-nums">
                      <MassCell g={u.mass_g} />
                    </td>
                    <td>{u.reason}</td>
                  </tr>
                ))}
                {report.unplaced.length === 0 && (
                  <tr>
                    <td colSpan={5}>Không có bó chưa xếp hoặc bị loại trừ.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="report-section report-issues" data-testid="report-issues" aria-labelledby="report-issues-title">
        <h2 id="report-issues-title">Kiểm tra</h2>
        <p>
          Trạng thái: {issues.status} · Kiểm cơ bản: {issues.basic_checks_passed ? "đạt" : "không đạt"} · Tổng số vấn đề: {issues.total_issues}
        </p>
        {issues.issues_truncated && (
          <p>
            Danh sách bị cắt: hiển thị {issues.items.length} trên tổng {issues.total_issues} vấn đề.
          </p>
        )}
        {issues.items.length > 0 ? (
          <ul>
            {issues.items.map((it, i) => (
              <li key={`${it.code}-${i}`}>
                <strong>{it.code}</strong>
                {it.unit_ids.length > 0 && <> · bó: {it.unit_ids.join(", ")}</>} — {it.message}
              </li>
            ))}
          </ul>
        ) : (
          <p>Không có vấn đề được ghi nhận.</p>
        )}
        <h3>Chưa kiểm</h3>
        {issues.unchecked.length > 0 ? (
          <ul>
            {issues.unchecked.map((item, i) => (
              <li key={`${i}-${item}`}>{item}</li>
            ))}
          </ul>
        ) : (
          <p>Không có mục chưa kiểm.</p>
        )}
        <p className="report-not-operational">
          <strong>Chưa đủ điều kiện vận hành.</strong>
        </p>
      </section>
    </div>
  );
}
