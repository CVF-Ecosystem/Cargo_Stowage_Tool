import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import Viewer from "../viewer-3d/Viewer";
import { requestEvaluation, requestVesselPlan, requestVesselProfile, type VesselProfile } from "../api/client";
import { fmt, kgInput, massLabel, parseKg, parseMm, tonnes, type Evaluation, type Plan } from "./model";

type UnitDraft = { mass: string; x: string; y: string; yaw: string };
type Draft = { units: Record<string, UnitDraft>; certificate: string; voyage: string; onboard: string };
function draftFrom(plan: Plan): Draft {
  const units: Record<string, UnitDraft> = {};
  for (const u of plan.units) {
    const p = plan.placements.find((v) => v.unit_id === u.id);
    units[u.id] = { mass: kgInput(u.mass_g), x: String(p?.x_mm ?? 0), y: String(p?.y_mm ?? 0), yaw: String(p?.yaw_deg ?? 0) };
  }
  return { units, certificate: kgInput(plan.limits.certificate_cargo_limit_g), voyage: kgInput(plan.limits.voyage_cargo_limit_g), onboard: kgInput(plan.limits.cargo_onboard_g ?? 0) };
}
function applyDraft(plan: Plan, draft: Draft): Plan {
  const next = structuredClone(plan);
  next.limits = { certificate_cargo_limit_g: parseKg(draft.certificate), voyage_cargo_limit_g: parseKg(draft.voyage), cargo_onboard_g: parseKg(draft.onboard, true) };
  for (const unit of next.units) {
    const d = draft.units[unit.id];
    unit.mass_g = parseKg(d.mass);
    const p = next.placements.find((v) => v.unit_id === unit.id);
    if (p) Object.assign(p, { x_mm: parseMm(d.x), y_mm: parseMm(d.y), yaw_deg: Number(d.yaw) });
  }
  return next;
}

export default function Workspace() {
  const [result, setResult] = useState<Evaluation | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const draftRef = useRef<Draft | null>(null);
  const [profile, setProfile] = useState<VesselProfile | null>(null);
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState("ST-001");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<Plan[]>([]);
  const lock = useRef(false);
  const changeDraft = (d: Draft) => { draftRef.current = d; setDraft(d); };
  useEffect(() => {
    let live = true;
    requestEvaluation().then((data) => { if (live) { setResult(data); changeDraft(draftFrom(data.plan)); } }).catch(() => { if (live) setError("Không kết nối được backend. Thử lại."); });
    return () => { live = false; };
  }, []);
  const stale = !!result && !!draft && JSON.stringify(draft) !== JSON.stringify(draftFrom(result.plan));
  const run = async (mode: "draft" | "undo" | "demo") => {
    if (lock.current || !result || !draftRef.current) return;
    if (mode !== "draft" && stale) { setError("Hãy áp dụng bản nháp trước khi đổi phương án; dữ liệu đang nhập được giữ nguyên."); return; }
    let plan: Plan | undefined;
    try { plan = mode === "draft" ? applyDraft(result.plan, draftRef.current) : mode === "undo" ? history[history.length - 1] : undefined; }
    catch (e) { setError(`${e instanceof Error ? e.message : "Dữ liệu sai."} Bản nháp chưa được kiểm; bản trước vẫn được giữ.`); return; }
    const captured = JSON.stringify(draftRef.current);
    lock.current = true; setBusy(true); setError("");
    try {
      const next = await requestEvaluation(plan);
      if (mode !== "draft" && JSON.stringify(draftRef.current) !== captured) { setError("Bản nháp đã đổi trong lúc chuyển; dữ liệu và kết quả trước được giữ nguyên."); return; }
      setHistory((h) => mode === "undo" ? h.slice(0, -1) : [...h.slice(-19), structuredClone(result.plan)]);
      setResult(next);
      if (JSON.stringify(draftRef.current) === captured) changeDraft(draftFrom(next.plan));
    } catch (e) {
      setError(`${e instanceof Error ? e.message : "Không kết nối được backend."} Bản nháp chưa được kiểm; bản trước vẫn được giữ.`);
    } finally { lock.current = false; setBusy(false); }
  };
  const switchCase = async (caseId: "VR-SI" | "VR-SII") => {
    if (lock.current || !result || !draftRef.current) return;
    if (stale) { setError("Hãy áp dụng bản nháp trước khi đổi phương tiện hoặc cấp tham chiếu; dữ liệu đang nhập được giữ nguyên."); return; }
    lock.current = true; setBusy(true); setError(""); setNotice("");
    const captured = JSON.stringify(draftRef.current);
    try {
      const [p, template] = await Promise.all([requestVesselProfile(), requestVesselPlan(caseId)]);
      const old = result.plan; const next = template.plan;
      const limit = next.limits.certificate_cargo_limit_g;
      if ((old.limits.cargo_onboard_g ?? 0) > limit) throw new Error("Hàng đã có vượt mức hàng tham chiếu của cấp được chọn; giảm số này trước khi chuyển.");
      next.units = structuredClone(old.units); next.placements = structuredClone(old.placements);
      next.limits.cargo_onboard_g = old.limits.cargo_onboard_g;
      // Preserve the voyage limit unless the new reference ceiling is lower.
      next.limits.voyage_cargo_limit_g = Math.min(old.limits.voyage_cargo_limit_g, limit);
      const evaluated = await requestEvaluation(next);
      if (JSON.stringify(draftRef.current) !== captured) { setError("Bản nháp đã thay đổi trong lúc chuyển; vẫn giữ bản nháp và trạng thái trước."); return; }
      setProfile(p); setHistory(h => [...h.slice(-19), structuredClone(old)]); setResult(evaluated); changeDraft(draftFrom(evaluated.plan));
      if (old.limits.voyage_cargo_limit_g > limit) setNotice("Giới hạn chuyến đã giảm về mức hàng tham chiếu của cấp mới.");
      else if (old.source === "SYNTHETIC") setNotice("Giới hạn chuyến đang giữ từ mẫu trước; có thể chỉnh đến mức hàng tham chiếu.");
    } catch (e) { setError(e instanceof Error ? e.message : "Không đổi được trạng thái."); }
    finally { lock.current = false; setBusy(false); }
  };
  const issues = useMemo(() => new Set(result?.issues.flatMap((i) => i.unit_ids) ?? []), [result]);
  if (!result || !draft) return <main className="loading-panel"><h1>SCST · SYNTHETIC</h1><p role="status">{error || "Đang mở phương án mẫu…"}</p>{error && <button onClick={() => location.reload()}>Thử lại</button>}</main>;
  const plan = result.plan;
  const unit = plan.units.find((u) => u.id === selected)!;
  const placement = plan.placements.find((p) => p.unit_id === selected);
  const ud = draft.units[selected];
  const editUnit = (key: keyof UnitDraft, value: string) => changeDraft({ ...draft, units: { ...draft.units, [selected]: { ...ud, [key]: value } } });
  const submit = (e: FormEvent) => { e.preventDefault(); void run("draft"); };
  return <div className="app-shell"><div className="main-shell"><header className="topbar"><div className="brand"><strong>SCST</strong><span>Steel Cargo Stowage Tool</span></div><span>{result.plan.source === "MIXED_REFERENCE" ? "THAM CHIẾU · HÀNG GIẢ LẬP" : "SYNTHETIC"} · Local</span></header><main id="workspace">
    <div className="page-heading"><div><h1>Lập phương án chất xếp <span className="demo-badge">{plan.source === "MIXED_REFERENCE" ? "THAM CHIẾU / HÀNG GIẢ LẬP" : "SYNTHETIC"}</span></h1><p>Hầm mục tiêu trống · Hàng giả lập, không dùng cho phương án thực.</p></div><div className="heading-actions"><button className="button secondary" disabled={busy || !history.length} onClick={() => void run("undo")}>↶ Bản trước</button><button className="button dark" disabled={busy || stale} onClick={() => void run("demo")}>↻ Khôi phục mẫu</button></div></div>
    <div className="vessel-controls"><button className="button secondary" disabled={busy || plan.source === "MIXED_REFERENCE"} onClick={() => void switchCase("VR-SII")}>Xem VINAFCO 268</button>{plan.source === "MIXED_REFERENCE" && <label>Cấp tham chiếu <select aria-label="Cấp tham chiếu" value={plan.vessel?.case_id} disabled={busy} onChange={e => void switchCase(e.target.value as "VR-SI" | "VR-SII")}><option value="VR-SI">VR-SI</option><option value="VR-SII">VR-SII</option></select></label>}</div>
    {notice && <p role="status">{notice}</p>}
    {plan.source === "MIXED_REFERENCE" && profile && <section className="scope-note" aria-label="Thông số VINAFCO 268"><strong>VINAFCO 268 · HN-2642 — thân theo hồ sơ, hầm ước tính, hàng giả lập</strong><p>Thân {fmt(profile.dimensions_m.length)} × {fmt(profile.dimensions_m.beam)} × {fmt(profile.dimensions_m.depth)} m. Hầm ước tính 56,405 × 10,34375 × 5,408 m; kiểm dùng bề rộng 10,343 m, lùi 0,375 mm mỗi mạn.</p><p>{(() => { const c=profile.cases.find(c => c.id === plan.vessel?.case_id)!; return `Mức hàng tham chiếu ${tonnes(c.cargo_mass_g)} tấn · TTTP ${fmt(c.deadweight_t)} tấn · mớn ${fmt(c.draft_m)} m · mạn khô hồ sơ ${c.freeboard_mm} mm`; })()}</p><p>{profile.capacity_note} {profile.container_note} {profile.provenance.freeboard_note}</p><p>Khối lượng tàu không và tải sàn cho phép: chưa có dữ liệu. Không xác nhận an toàn hoặc điều kiện vận hành.</p></section>}
    <p>Thay đổi chỉ giữ trong tab; tải lại hoặc đóng trang sẽ mất thay đổi.</p>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {stale && <div className="error-banner" role="status">STALE · Bản nháp chưa được kiểm; kết quả đang thấy thuộc bản đã kiểm trước đó.</div>}
    <div className="stats-row"><section className="stat"><span className="stat-label">KHỐI LƯỢNG MANIFEST</span><strong data-testid="manifest-mass">{tonnes(result.summary.manifest_mass_g)} tấn</strong></section><section className="stat"><span className="stat-label">ĐÃ XẾP / ĐƯỢC XẾP THÊM</span><strong data-testid="placed-mass">{tonnes(result.summary.placed_mass_g)} / {tonnes(plan.limits.voyage_cargo_limit_g - (plan.limits.cargo_onboard_g ?? 0))} tấn</strong></section><section className="stat"><span className="stat-label">TRẠNG THÁI</span><strong data-testid="status">{stale ? "STALE" : result.status}</strong><small>{result.summary.placed_count} đã xếp · {plan.units.length - result.summary.placed_count} chưa xếp</small></section></div>
    <div className="workspace-grid"><Viewer plan={plan} profile={profile} selected={selected} onSelect={setSelected} issueIds={issues} /><section className="editor-card" aria-label="Chỉnh bó hàng"><div className="panel-heading"><div><span className="eyebrow">ĐANG CHỌN</span><h2>{unit.id}</h2><p>{unit.name} · {fmt(unit.length_mm)} × {fmt(unit.width_mm)} × {fmt(unit.height_mm)} mm</p></div></div><form onSubmit={submit}>
      <label>Khối lượng bó (kg)<input aria-label="Khối lượng bó (kg)" value={ud.mass} onChange={(e) => editUnit("mass",e.target.value)} /></label>
      {placement && <><label>Tọa độ X (mm)<input aria-label="Tọa độ X (mm)" value={ud.x} onChange={(e) => editUnit("x",e.target.value)} /></label><label>Tọa độ Y (mm)<input aria-label="Tọa độ Y (mm)" value={ud.y} onChange={(e) => editUnit("y",e.target.value)} /></label><label>Góc xoay<select aria-label="Góc xoay" value={ud.yaw} onChange={(e) => editUnit("yaw",e.target.value)}>{[0,90,180,270].map(v => <option key={v} value={v}>{v}°</option>)}</select></label></>}
      <label>{plan.source === "MIXED_REFERENCE" ? "Mức hàng tham chiếu (kg)" : "Giới hạn chứng nhận (kg)"}<input aria-label="Giới hạn chứng nhận (kg)" readOnly={plan.source === "MIXED_REFERENCE"} value={draft.certificate} onChange={(e) => changeDraft({...draft, certificate:e.target.value})} /></label>
      <label>Giới hạn chuyến (kg)<input aria-label="Giới hạn chuyến (kg)" value={draft.voyage} onChange={(e) => changeDraft({...draft, voyage:e.target.value})} /></label>
      <label>Hàng đã có trên tàu (kg)<input aria-label="Hàng đã có trên tàu (kg)" value={draft.onboard} onChange={(e) => changeDraft({...draft, onboard:e.target.value})} /></label>
      <button className="button primary apply-button" disabled={busy} type="submit">{busy ? "Đang kiểm…" : "Áp dụng & kiểm lại"}</button>
    </form></section></div>
    <div className="workspace-grid"><section id="cargo" className="editor-card"><h2>Danh sách hàng</h2><div className="table-wrap"><table><thead><tr><th>ID</th><th>Loại / yêu cầu</th><th>Kích thước (mm)</th><th>Khối lượng</th><th>Vị trí / lý do</th></tr></thead><tbody>{plan.units.map((u) => {const p=plan.placements.find(x=>x.unit_id===u.id); return <tr key={u.id} data-testid={`unit-${u.id}`} aria-selected={selected===u.id} onClick={()=>setSelected(u.id)}><td><button className="text-button" onClick={()=>setSelected(u.id)}>{u.id}</button></td><td>{u.kind === "BAR_BUNDLE" ? "Bó thép thanh" : "Bó thép ống"} · {u.requirement === "required" ? "Bắt buộc" : u.requirement === "optional" ? "Tùy chọn" : "Loại trừ"}</td><td>{u.length_mm} × {u.width_mm} × {u.height_mm}</td><td>{massLabel(u.mass_g)}</td><td>{p ? `${p.x_mm}, ${p.y_mm}, ${p.z_mm ?? 0} · ${p.yaw_deg}°` : u.requirement === "excluded" ? "Đã loại trừ" : u.requirement === "optional" ? "Tùy chọn chưa xếp" : "Bắt buộc chưa xếp"}</td></tr>})}</tbody></table></div></section><section id="checks" className="editor-card"><h2>Kết quả kiểm</h2><p>{plan.source === "MIXED_REFERENCE" ? "Mức hàng tham chiếu" : "Chứng nhận"}: {tonnes(plan.limits.certificate_cargo_limit_g)} tấn · Chuyến: {tonnes(plan.limits.voyage_cargo_limit_g)} tấn · Đã có ngoài hầm: {tonnes(plan.limits.cargo_onboard_g ?? 0)} tấn</p><p>Được xếp thêm: {tonnes(plan.limits.voyage_cargo_limit_g - (plan.limits.cargo_onboard_g ?? 0))} tấn</p>{result.issues.length ? <ul>{result.issues.map((i,n)=><li key={n}><strong>{i.code}</strong> {i.message}</li>)}</ul> : <p>Không phát hiện lỗi trong các kiểm M1.</p>}<div className="scope-note"><strong>CHƯA KIỂM</strong><p>{result.unchecked.join(" · ")}</p></div><p>Chưa đủ điều kiện vận hành.</p></section></div>
  </main></div></div>;
}
