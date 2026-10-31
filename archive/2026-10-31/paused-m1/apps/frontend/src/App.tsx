import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import Viewer from "./Viewer";
import {
  fmt,
  kgInput,
  massLabel,
  parseKg,
  parseMm,
  requestEvaluation,
  tonnes,
  type Evaluation,
  type Plan,
} from "./model";

function Editor({
  result,
  selected,
  busy,
  onApply,
}: {
  result: Evaluation;
  selected: string;
  busy: boolean;
  onApply: (p: Plan) => Promise<void>;
}) {
  const unit = result.plan.units.find((u) => u.id === selected)!;
  const placement = result.plan.placements.find((p) => p.unit_id === selected);
  const [mass, setMass] = useState(kgInput(unit.mass_g));
  const [limit, setLimit] = useState(kgInput(result.plan.hold.cargo_limit_g));
  const [x, setX] = useState(String(placement?.x_mm ?? 0));
  const [y, setY] = useState(String(placement?.y_mm ?? 0));
  const [yaw, setYaw] = useState(String(placement?.yaw_deg ?? 0));
  const [error, setError] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const next = structuredClone(result.plan);
      next.units.find((u) => u.id === selected)!.mass_g = parseKg(mass);
      next.hold.cargo_limit_g = parseKg(limit);
      const p = next.placements.find((p) => p.unit_id === selected);
      if (p)
        Object.assign(p, {
          x_mm: parseMm(x),
          y_mm: parseMm(y),
          yaw_deg: Number(yaw),
        });
      void onApply(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Dữ liệu chưa hợp lệ.");
    }
  };
  return (
    <section className="editor-card" aria-label="Chỉnh bó hàng">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">ĐANG CHỌN</span>
          <h2>
            {unit.id}{" "}
            <span
              className={`type-pill ${unit.kind === "BAR_BUNDLE" ? "steel-text" : "pipe-text"}`}
            >
              {unit.kind === "BAR_BUNDLE" ? "Thép thanh" : "Thép ống"}
            </span>
          </h2>
        </div>
        <span className="selection-symbol">⌖</span>
      </div>
      <div className="unit-meta">
        <span>{unit.name}</span>
        <strong>
          {fmt(unit.length_mm)} × {fmt(unit.width_mm)} × {fmt(unit.height_mm)}{" "}
          mm
        </strong>
      </div>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <label>
            Khối lượng bó <span>kg</span>
            <input
              aria-label="Khối lượng bó (kg)"
              value={mass}
              onChange={(e) => setMass(e.target.value)}
              inputMode="decimal"
            />
          </label>
          <div className="form-divider">Vị trí góc bó trên đáy hầm</div>
          {placement ? (
            <>
              <div className="field-row">
                <label>
                  Tọa độ X <span>mm</span>
                  <input
                    aria-label="Tọa độ X (mm)"
                    value={x}
                    onChange={(e) => setX(e.target.value)}
                    inputMode="numeric"
                  />
                </label>
                <label>
                  Tọa độ Y <span>mm</span>
                  <input
                    aria-label="Tọa độ Y (mm)"
                    value={y}
                    onChange={(e) => setY(e.target.value)}
                    inputMode="numeric"
                  />
                </label>
              </div>
              <label>
                Góc xoay <span>Z = 0 mm</span>
                <select
                  aria-label="Góc xoay"
                  value={yaw}
                  onChange={(e) => setYaw(e.target.value)}
                >
                  <option value="0">0° · Dọc hầm</option>
                  <option value="90">90° · Ngang hầm</option>
                  <option value="180">180° · Dọc hầm</option>
                  <option value="270">270° · Ngang hầm</option>
                </select>
              </label>
            </>
          ) : (
            <p className="helper">
              Bó này chưa xếp. M1 cho phép thử khối lượng; thêm/bỏ bó vào phương
              án sẽ có ở M2.
            </p>
          )}
          <div className="form-divider">Thông số hầm dùng để kiểm</div>
          <label>
            Giới hạn khối lượng hàng <span>kg</span>
            <input
              aria-label="Giới hạn khối lượng hàng (kg)"
              value={limit}
              onChange={(e) => setLimit(e.target.value)}
              inputMode="decimal"
            />
          </label>
          {error && (
            <p className="field-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="button primary apply-button">
            {busy ? "Đang kiểm…" : "Áp dụng & kiểm lại"}
            <span>↗</span>
          </button>
        </fieldset>
      </form>
      <p className="helper editor-note">
        Tọa độ và khối lượng mới chỉ áp dụng sau khi backend trả kết quả kiểm.
      </p>
    </section>
  );
}

export default function App() {
  const [result, setResult] = useState<Evaluation | null>(null);
  const [selected, setSelected] = useState("ST-001");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<Plan[]>([]);
  const [revision, setRevision] = useState(0);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [guide, setGuide] = useState(false);
  const requestLock = useRef(false);
  const requestVersion = useRef(0);
  useEffect(() => {
    let live = true;
    const version = ++requestVersion.current;
    requestEvaluation()
      .then((data) => {
        if (live && version === requestVersion.current) setResult(data);
      })
      .catch(() => {
        if (live && version === requestVersion.current)
          setError(
            "Không kết nối được backend. Kiểm tra cửa sổ chạy SCST rồi thử lại.",
          );
      });
    return () => {
      live = false;
    };
  }, []);
  const run = async (plan?: Plan, undo = false) => {
    if (requestLock.current) return;
    requestVersion.current += 1;
    requestLock.current = true;
    setBusy(true);
    setError("");
    try {
      const next = await requestEvaluation(plan);
      if (result)
        setHistory((h) =>
          undo
            ? h.slice(0, -1)
            : [...h.slice(-19), structuredClone(result.plan)],
        );
      setResult(next);
      setRevision((v) => v + 1);
    } catch (e) {
      setError(
        e instanceof TypeError ||
          (e instanceof DOMException && e.name === "TimeoutError")
          ? "Không kết nối được backend hoặc đã hết thời gian chờ. Phương án trước vẫn được giữ; bạn có thể thử lại."
          : e instanceof Error
            ? e.message
            : "Không kết nối được backend. Phương án trước vẫn được giữ.",
      );
    } finally {
      requestLock.current = false;
      setBusy(false);
    }
  };
  const issueIds = useMemo(
    () => new Set(result?.issues.flatMap((i) => i.unit_ids) ?? []),
    [result],
  );
  const placedIds = useMemo(
    () => new Set(result?.plan.placements.map((p) => p.unit_id) ?? []),
    [result],
  );
  const visibleUnits =
    result?.plan.units.filter(
      (u) =>
        (!search ||
          `${u.id} ${u.name}`
            .toLocaleLowerCase("vi")
            .includes(search.toLocaleLowerCase("vi"))) &&
        (filter === "all" ||
          (filter === "placed"
            ? placedIds.has(u.id)
            : result.summary.unplaced_ids.includes(u.id))),
    ) ?? [];
  return (
    <div className="app-shell">
      <aside className="rail">
        <a className="logo-mark" href="#" aria-label="SCST trang đầu">
          S<span>▰</span>
        </a>
        <div className="rail-line" />
        <a
          href="#workspace"
          className="rail-link current"
          title="Không gian chất xếp"
          aria-label="Không gian chất xếp"
        >
          ◈
        </a>
        <a
          href="#cargo"
          className="rail-link"
          title="Danh sách hàng"
          aria-label="Danh sách hàng"
        >
          ▤
        </a>
        <a
          href="#checks"
          className="rail-link"
          title="Kết quả kiểm"
          aria-label="Kết quả kiểm"
        >
          ✓
        </a>
        <button
          className="rail-link rail-help"
          onClick={() => setGuide((g) => !g)}
          title="Hướng dẫn"
          aria-label="Mở hướng dẫn"
        >
          ?
        </button>
        <span className="rail-version">M1</span>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="brand">
            <strong>SCST</strong>
            <span className="brand-divider" />
            <span>Steel Cargo Stowage Tool</span>
          </div>
          <div className="topbar-meta">
            <span className="local-status">
              <i />
              Local workspace
            </span>
            <span className="avatar">LK</span>
          </div>
        </header>
        <main id="workspace">
          <div className="page-heading">
            <div>
              <div className="breadcrumb">
                WORKSPACE <span>/</span> PHƯƠNG ÁN MẪU
              </div>
              <h1>
                Lập phương án chất xếp<span className="demo-badge">DEMO</span>
              </h1>
              <p>Nhìn toàn cảnh. Chỉnh từng bó. Kiểm lại phương án.</p>
            </div>
            <div className="heading-actions">
              <button
                className="button secondary"
                onClick={() => setGuide((g) => !g)}
              >
                Hướng dẫn
              </button>
              <button
                className="button secondary"
                disabled={busy || !history.length}
                onClick={() => void run(history[history.length - 1], true)}
              >
                ↶ Bản trước
              </button>
              <button
                className="button dark"
                disabled={busy}
                onClick={() => void run()}
              >
                ↻ Khôi phục mẫu
              </button>
            </div>
          </div>
          {guide && (
            <section className="guide">
              <strong>Bắt đầu trong 3 bước</strong>
              <ol>
                <li>Chọn một bó trong bảng, mô hình 3D hoặc mặt bằng.</li>
                <li>
                  Thay khối lượng / tọa độ, bấm “Áp dụng & kiểm lại”. Thử X =
                  8.001 mm cho ST-001 để thấy lỗi vượt biên.
                </li>
                <li>
                  Dùng “Bản trước” để quay lại; “Khôi phục mẫu” để thử lại từ
                  đầu.
                </li>
              </ol>
              <p>
                M1 chỉ giữ tối đa 20 bản trước trong phiên này. Tải lại/đóng
                trang sẽ mất thay đổi. Lưu/mở và nhập dữ liệu sẽ được bổ sung ở
                M2.
              </p>
              <button onClick={() => setGuide(false)} className="text-button">
                Đóng hướng dẫn
              </button>
            </section>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <strong>{error}</strong>
              {!result && (
                <button
                  className="button secondary"
                  disabled={busy}
                  onClick={() => void run()}
                >
                  Thử kết nối lại
                </button>
              )}
            </div>
          )}
          {!result ? (
            <div className="loading-panel" role="status">
              {error
                ? "Chưa tải được dữ liệu mẫu."
                : "Đang mở hầm và phương án mẫu…"}
            </div>
          ) : (
            <>
              <div className="stats-row">
                <section className="stat">
                  <span className="stat-label">KHỐI LƯỢNG ĐÃ XẾP</span>
                  <div>
                    <strong data-testid="placed-mass">
                      {tonnes(result.summary.placed_mass_g)}
                    </strong>
                    <span> / {tonnes(result.plan.hold.cargo_limit_g)} tấn</span>
                  </div>
                  <div className="capacity-track">
                    <i
                      style={{
                        width: `${Math.min(100, (result.summary.placed_mass_g / result.plan.hold.cargo_limit_g) * 100)}%`,
                        background:
                          result.summary.remaining_capacity_g < 0
                            ? "#bc5345"
                            : undefined,
                      }}
                    />
                  </div>
                  <small>
                    {result.summary.remaining_capacity_g >= 0
                      ? "Còn "
                      : "Vượt "}
                    {massLabel(Math.abs(result.summary.remaining_capacity_g))}{" "}
                    giới hạn hàng
                  </small>
                </section>
                <section className="stat">
                  <span className="stat-label">BÓ HÀNG TRONG PHƯƠNG ÁN</span>
                  <div>
                    <strong>{result.summary.placed_count}</strong>
                    <span> / {result.plan.units.length} bó</span>
                  </div>
                  <small>
                    <i className="dot" />
                    {result.summary.unplaced_ids.length} chưa xếp ·{" "}
                    {result.summary.excluded_ids.length} loại trừ
                  </small>
                </section>
                <section className="stat">
                  <span className="stat-label">KÍCH THƯỚC HẦM MẪU</span>
                  <div className="hold-dims">
                    <strong>
                      {fmt(result.plan.hold.length_mm / 1000)} ×{" "}
                      {fmt(result.plan.hold.width_mm / 1000)} ×{" "}
                      {fmt(result.plan.hold.height_mm / 1000)}
                    </strong>
                    <span> m</span>
                  </div>
                  <small>Dài × Rộng × Cao · Hầm BOX</small>
                </section>
                <section
                  className={`stat check-stat ${result.basic_checks_passed ? "" : "has-errors"}`}
                >
                  <span className="stat-label">KIỂM CƠ BẢN</span>
                  <div>
                    <span className="check-circle">
                      {result.basic_checks_passed ? "✓" : "!"}
                    </span>
                    <strong data-testid="check-status">
                      {result.basic_checks_passed
                        ? "Đạt kiểm tra"
                        : `${result.issues.length} vấn đề`}
                    </strong>
                  </div>
                  <small>Tải hàng · Biên hầm · Va chạm · Hàng bắt buộc</small>
                </section>
              </div>
              <div className="workspace-grid">
                <Viewer
                  plan={result.plan}
                  selected={selected}
                  onSelect={setSelected}
                  issueIds={issueIds}
                />
                <Editor
                  key={`${selected}-${revision}`}
                  result={result}
                  selected={selected}
                  busy={busy}
                  onApply={run}
                />
              </div>
              <div className="details-grid">
                <section className="cargo-card" id="cargo">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">MANIFEST MẪU</span>
                      <h2>
                        Danh sách hàng{" "}
                        <span className="count-badge">
                          {result.plan.units.length}
                        </span>
                      </h2>
                    </div>
                    <label className="search-box">
                      <span>⌕</span>
                      <input
                        aria-label="Tìm bó hàng"
                        placeholder="Tìm ID hoặc tên hàng…"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </label>
                  </div>
                  <div className="table-toolbar">
                    <div className="table-filters">
                      {[
                        ["all", "Tất cả"],
                        ["placed", "Đã xếp"],
                        ["unplaced", "Chưa xếp"],
                      ].map(([value, label]) => (
                        <button
                          key={value}
                          className={filter === value ? "active" : ""}
                          aria-pressed={filter === value}
                          onClick={() => setFilter(value)}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                    <span>
                      Tổng manifest: {tonnes(result.summary.manifest_mass_g)}{" "}
                      tấn
                    </span>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Bó hàng</th>
                          <th>Loại / yêu cầu</th>
                          <th>Khối lượng</th>
                          <th>Vị trí X / Y (mm)</th>
                          <th>Trạng thái</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleUnits.map((u) => {
                          const p = result.plan.placements.find(
                            (p) => p.unit_id === u.id,
                          );
                          return (
                            <tr
                              key={u.id}
                              className={
                                u.id === selected ? "selected-row" : ""
                              }
                              data-testid={`row-${u.id}`}
                            >
                              <td>
                                <button
                                  onClick={() => setSelected(u.id)}
                                  className="unit-button"
                                  aria-pressed={u.id === selected}
                                >
                                  <i
                                    className={`swatch ${u.kind === "BAR_BUNDLE" ? "steel" : "pipe"}`}
                                  />
                                  {u.id}
                                </button>
                              </td>
                              <td>
                                {u.kind === "BAR_BUNDLE"
                                  ? "Thép thanh"
                                  : "Thép ống"}
                                <small>
                                  {u.requirement === "required"
                                    ? "Bắt buộc"
                                    : u.requirement === "optional"
                                      ? "Tùy chọn"
                                      : "Loại trừ"}
                                </small>
                              </td>
                              <td>
                                {fmt(u.mass_g / 1000)}{" "}
                                <span className="muted">kg</span>
                              </td>
                              <td className="mono">
                                {p ? `${fmt(p.x_mm)} / ${fmt(p.y_mm)}` : "—"}
                              </td>
                              <td>
                                <span
                                  className={`status-pill ${issueIds.has(u.id) ? "problem" : p ? "placed" : "unplaced"}`}
                                >
                                  {issueIds.has(u.id)
                                    ? "Cần sửa"
                                    : p
                                      ? "Đã xếp"
                                      : u.requirement === "excluded"
                                        ? "Loại trừ"
                                        : "Chưa xếp"}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    {!visibleUnits.length && (
                      <div className="empty-state">
                        Không có bó hàng phù hợp bộ lọc.
                      </div>
                    )}
                  </div>
                  <div className="table-footer">
                    {visibleUnits.length} / {result.plan.units.length} bó{" "}
                    <span>Mỗi ID là một bó nguyên vẹn</span>
                  </div>
                </section>
                <section className="validation-card" id="checks">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">KẾT QUẢ TỪ BACKEND</span>
                      <h2>Kiểm phương án</h2>
                    </div>
                    <span className="count-badge">v{revision + 1}</span>
                  </div>
                  <div className="validation-content" aria-live="polite">
                    {result.basic_checks_passed ? (
                      <div className="check-success">
                        <span>✓</span>
                        <div>
                          <strong>Không có lỗi trong phạm vi kiểm</strong>
                          <p>
                            Tải hàng, biên, va chạm và hàng bắt buộc đã được đối
                            chiếu.
                          </p>
                        </div>
                      </div>
                    ) : (
                      <ul className="issue-list">
                        {result.issues.map((i, index) => (
                          <li key={index}>
                            <span className="issue-symbol">!</span>
                            <div>
                              <strong>
                                {i.code === "OVERWEIGHT"
                                  ? "Vượt tải hàng"
                                  : i.code === "OUT_OF_BOUNDS"
                                    ? "Vượt biên hầm"
                                    : i.code === "OVERLAP"
                                      ? "Va chạm bó hàng"
                                      : i.code === "REQUIRED_UNPLACED"
                                        ? "Thiếu hàng bắt buộc"
                                        : "Cấu hình chưa hỗ trợ"}
                              </strong>
                              <p>{i.message}</p>
                              {i.unit_ids.map((id) => (
                                <button
                                  key={id}
                                  className="issue-link"
                                  onClick={() => setSelected(id)}
                                >
                                  {id} ↗
                                </button>
                              ))}
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                    {result.summary.unplaced_ids.length > 0 && (
                      <div className="unplaced-note">
                        <strong>
                          {result.summary.unplaced_ids.length} bó chưa xếp
                        </strong>
                        <p>
                          {result.summary.unplaced_ids.join(", ")} · xem yêu cầu
                          từng bó trong bảng.
                        </p>
                      </div>
                    )}
                    <div className="scope-note">
                      <span className="eyebrow">CHƯA KIỂM</span>
                      <p>{result.unchecked.join(" · ")}.</p>
                    </div>
                  </div>
                </section>
              </div>
              <footer className="footer">
                <span>
                  <i className="dot amber" />
                  Dữ liệu giả lập · Kết quả tính sơ bộ, chưa dùng cho phương án
                  thực
                </span>
                <span>Thay đổi chỉ giữ trong phiên · M1 / 0.1.0</span>
              </footer>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
