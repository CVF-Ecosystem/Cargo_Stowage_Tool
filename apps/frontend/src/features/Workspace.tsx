import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import Viewer from "../viewer-3d/Viewer";
import { requestEvaluation, requestVesselPlan, requestVesselProfile, previewCsv, saveSnapshot, listSnapshots, openSnapshot, type CsvPreview, type SavedSummary, type VesselProfile } from "../api/client";
import { fmt, kgInput, massLabel, parseKg, parseMm, tonnes, type Evaluation, type Plan } from "./model";

function savedTime(value: string): string {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "Thời gian không hợp lệ";
  const parts = new Intl.DateTimeFormat("vi-VN", {day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(date);
  const part = (type: string) => parts.find(p => p.type === type)?.value ?? "";
  return `${part("day")}-${part("month")}-${part("year")} ${part("hour")}:${part("minute")}`;
}

type UnitDraft = { id: string; name: string; kind: string; requirement: string; length: string; width: string; height: string; mass: string; x: string; y: string; yaw: string };
type Draft = { units: Record<string, UnitDraft>; certificate: string; voyage: string; onboard: string; holdName: string; holdLength: string; holdWidth: string; holdHeight: string };
function draftFrom(plan: Plan): Draft {
  const units: Record<string, UnitDraft> = {};
  for (const u of plan.units) {
    const p = plan.placements.find((v) => v.unit_id === u.id);
    units[u.id] = { id:u.id, name:u.name, kind:u.kind, requirement:u.requirement, length:String(u.length_mm), width:String(u.width_mm), height:String(u.height_mm), mass: kgInput(u.mass_g), x: String(p?.x_mm ?? 0), y: String(p?.y_mm ?? 0), yaw: String(p?.yaw_deg ?? 0) };
  }
  return { units, holdName:plan.hold.name, holdLength:String(plan.hold.length_mm), holdWidth:String(plan.hold.width_mm), holdHeight:String(plan.hold.height_mm), certificate: kgInput(plan.limits.certificate_cargo_limit_g), voyage: kgInput(plan.limits.voyage_cargo_limit_g), onboard: kgInput(plan.limits.cargo_onboard_g ?? 0) };
}
function applyDraft(plan: Plan, draft: Draft): Plan {
  const next = structuredClone(plan);
  next.limits = { certificate_cargo_limit_g: parseKg(draft.certificate), voyage_cargo_limit_g: parseKg(draft.voyage), cargo_onboard_g: parseKg(draft.onboard, true) };
  if (next.contract_version === "scst.m2a.v1" && next.source === "USER_ENTERED") {
    next.hold = {...next.hold, name:draft.holdName, length_mm:parseMm(draft.holdLength), width_mm:parseMm(draft.holdWidth), height_mm:parseMm(draft.holdHeight)};
  }
  const placements = [];
  for (const unit of next.units) {
    const d = draft.units[unit.id];
    const p = next.placements.find((v) => v.unit_id === unit.id);
    if (next.contract_version === "scst.m2a.v1") {
      unit.id=d.id; unit.name=d.name; unit.kind=d.kind as typeof unit.kind; unit.requirement=d.requirement as typeof unit.requirement;
      unit.length_mm=parseMm(d.length); unit.width_mm=parseMm(d.width); unit.height_mm=parseMm(d.height);
    }
    unit.mass_g = parseKg(d.mass);
    if (p && unit.requirement !== "excluded") placements.push({...p, unit_id:unit.id, x_mm:parseMm(d.x), y_mm:parseMm(d.y), yaw_deg:Number(d.yaw)});
  }
  next.placements=placements;
  if (next.contract_version === "scst.m2a.v1" && plan.units.some(u => { const d=draft.units[u.id]; return d.id!==u.id || d.name!==u.name || d.kind!==u.kind || d.requirement!==u.requirement || d.length!==String(u.length_mm) || d.width!==String(u.width_mm) || d.height!==String(u.height_mm) || d.mass!==kgInput(u.mass_g); })) next.cargo_source="USER_ENTERED";
  return next;
}

export default function Workspace() {
  const [result, setResult] = useState<Evaluation | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const draftRef = useRef<Draft | null>(null);
  const [profile, setProfile] = useState<VesselProfile | null>(null);
  const [notice, setNotice] = useState("");
  const [csvText, setCsvText] = useState("");
  const [preview, setPreview] = useState<CsvPreview | null>(null);
  const [previewKey, setPreviewKey] = useState("");
  const [saved, setSaved] = useState<SavedSummary[]>([]);
  const [saveName, setSaveName] = useState("");
  const [savedId, setSavedId] = useState("");
  const [newUnit, setNewUnit] = useState({id:"",name:"",kind:"BAR_BUNDLE",requirement:"required",length:"",width:"",height:"",mass:""});
  const revision = useRef(0);
  const [selected, setSelected] = useState("ST-001");
  const selectedRef=useRef("ST-001");
  const select=useCallback((id: string) => { revision.current++; selectedRef.current=id; setSelected(id); }, []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<Plan[]>([]);
  const lock = useRef(false);
  const changeDraft = (d: Draft) => { revision.current++; draftRef.current = d; setDraft(d); };
  useEffect(() => {
    let live = true;
    requestEvaluation().then((data) => { if (live) { setResult(data); changeDraft(draftFrom(data.plan)); } }).catch(() => { if (live) setError("Không kết nối được backend. Thử lại."); });
    listSnapshots().then((items) => { if (live) setSaved(items); }).catch(() => { if (live) setError("Không thể đọc danh sách phương án local."); });
    return () => { live = false; };
  }, []);
  const stale = !!result && !!draft && JSON.stringify(draft) !== JSON.stringify(draftFrom(result.plan));
  const run = async (mode: "draft" | "undo" | "demo") => {
    if (lock.current || !result || !draftRef.current) return;
    if (mode !== "draft" && stale) { setError("Hãy áp dụng bản nháp trước khi đổi phương án; dữ liệu đang nhập được giữ nguyên."); return; }
    let plan: Plan | undefined;
    try { plan = mode === "draft" ? applyDraft(result.plan, draftRef.current) : mode === "undo" ? history[history.length - 1] : undefined; }
    catch (e) { setError(`${e instanceof Error ? e.message : "Dữ liệu sai."} Bản nháp chưa được kiểm; bản trước vẫn được giữ.`); return; }
    const captured = JSON.stringify(draftRef.current); const capturedRevision=revision.current;
    lock.current = true; setBusy(true); setError("");
    try {
      const next = await requestEvaluation(plan);
      if (mode !== "draft" && (JSON.stringify(draftRef.current) !== captured || revision.current !== capturedRevision)) { setError("Bản nháp đã đổi trong lúc chuyển; dữ liệu và kết quả trước được giữ nguyên."); return; }
      setHistory((h) => mode === "undo" ? h.slice(0, -1) : [...h.slice(-19), structuredClone(result.plan)]);
      setResult(next);
      if (mode === "draft" && result.plan.placements.some(p => !next.plan.placements.some(q => q.unit_id === p.unit_id)) && next.plan.units.some(u => u.requirement === "excluded")) setNotice("Bó loại trừ đã được bỏ vị trí trong hầm.");
      if (JSON.stringify(draftRef.current) === captured) { changeDraft(draftFrom(next.plan)); if (!next.plan.units.some(u=>u.id===selectedRef.current)) select(next.plan.units[0]?.id ?? ""); }
    } catch (e) {
      setError(`${e instanceof Error ? e.message : "Không kết nối được backend."} Bản nháp chưa được kiểm; bản trước vẫn được giữ.`);
    } finally { lock.current = false; setBusy(false); }
  };
  const switchCase = async (caseId: "VR-SI" | "VR-SII") => {
    if (lock.current || !result || !draftRef.current) return;
    if (stale) { setError("Hãy áp dụng bản nháp trước khi đổi phương tiện hoặc cấp tham chiếu; dữ liệu đang nhập được giữ nguyên."); return; }
    lock.current = true; setBusy(true); setError(""); setNotice("");
    const captured = JSON.stringify(draftRef.current); const capturedRevision=revision.current;
    try {
      const [p, template] = await Promise.all([requestVesselProfile(), requestVesselPlan(caseId)]);
      const old = result.plan; const next = template.plan;
      const limit = next.limits.certificate_cargo_limit_g;
      if ((old.limits.cargo_onboard_g ?? 0) > limit) throw new Error("Hàng đã có vượt mức hàng tham chiếu của cấp được chọn; giảm số này trước khi chuyển.");
      next.units = structuredClone(old.units); next.placements = structuredClone(old.placements);
      if (old.contract_version === "scst.m2a.v1") { next.contract_version=old.contract_version; next.cargo_source=old.cargo_source; }
      next.limits.cargo_onboard_g = old.limits.cargo_onboard_g;
      // Preserve the voyage limit unless the new reference ceiling is lower.
      next.limits.voyage_cargo_limit_g = Math.min(old.limits.voyage_cargo_limit_g, limit);
      const evaluated = await requestEvaluation(next);
      if (JSON.stringify(draftRef.current) !== captured || revision.current !== capturedRevision) { setError("Bản nháp đã thay đổi trong lúc chuyển; vẫn giữ bản nháp và trạng thái trước."); return; }
      setProfile(p); setHistory(h => [...h.slice(-19), structuredClone(old)]); setResult(evaluated); changeDraft(draftFrom(evaluated.plan));
      if (old.limits.voyage_cargo_limit_g > limit) setNotice("Giới hạn chuyến đã giảm về mức hàng tham chiếu của cấp mới.");
      else if (old.source === "SYNTHETIC") setNotice("Giới hạn chuyến đang giữ từ mẫu trước; có thể chỉnh đến mức hàng tham chiếu.");
    } catch (e) { setError(e instanceof Error ? e.message : "Không đổi được trạng thái."); }
    finally { lock.current = false; setBusy(false); }
  };
  const issues = useMemo(() => new Set(result?.issues.flatMap((i) => i.unit_ids) ?? []), [result]);
  if (!result || !draft) return <main className="loading-panel"><h1>SCST · SYNTHETIC</h1><p role="status">{error || "Đang mở phương án mẫu…"}</p>{error && <button onClick={() => location.reload()}>Thử lại</button>}</main>;
  const plan = result.plan;
  const unit = plan.units.find((u) => u.id === selected);
  const placement = plan.placements.find((p) => p.unit_id === selected);
  const ud = draft.units[selected];
  const editUnit = (key: keyof UnitDraft, value: string) => changeDraft({ ...draft, units: { ...draft.units, [selected]: { ...ud, [key]: value } } });
  const transition = async (candidate: Plan, label: string) => {
    if (lock.current || stale) { if(stale) setError("Hãy áp dụng bản nháp trước khi đổi phương án."); return; }
    const before=revision.current; lock.current=true; setBusy(true); setError("");
    try {
      const next=await requestEvaluation(candidate);
      let newProfile=profile;
      if (next.plan.source === "MIXED_REFERENCE" && !newProfile) newProfile=await requestVesselProfile();
      if (revision.current !== before) { setError("Dữ liệu đã đổi trong lúc chờ; phương án trước được giữ."); return; }
      setHistory(h=>[...h.slice(-19),structuredClone(result.plan)]); setResult(next); setProfile(newProfile); changeDraft(draftFrom(next.plan));
      select(next.plan.units[0]?.id ?? ""); setPreview(null); setNotice(label);
    } catch (e) { setError(e instanceof Error ? e.message : "Không thể cập nhật."); }
    finally { lock.current=false; setBusy(false); }
  };
  const newPlan = () => { const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.source="USER_ENTERED"; next.vessel=null; next.cargo_source="SYNTHETIC"; next.units=[]; next.placements=[]; void transition(next,"Phương án mới; hầm tự nhập chưa xác minh."); };
  const detach = () => { const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.source="USER_ENTERED"; next.vessel=null; next.cargo_source=next.cargo_source ?? "SYNTHETIC"; void transition(next,"Đã bỏ liên kết phương tiện; hầm tự nhập chưa xác minh."); };
  const addUnit = () => {
    try {
      const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.cargo_source="USER_ENTERED";
      next.units.push({id:newUnit.id,name:newUnit.name,kind:newUnit.kind as "BAR_BUNDLE" | "PIPE_BUNDLE",requirement:newUnit.requirement as "required" | "optional" | "excluded",length_mm:parseMm(newUnit.length),width_mm:parseMm(newUnit.width),height_mm:parseMm(newUnit.height),mass_g:parseKg(newUnit.mass)});
      void transition(next,"Đã thêm bó chưa xếp.");
    } catch(e) { setError(e instanceof Error ? e.message : "Dữ liệu bó không hợp lệ."); }
  };
  const changePlacement = (place: boolean) => { if (!unit) return; const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.cargo_source=next.cargo_source ?? "SYNTHETIC"; next.placements=next.placements.filter(p=>p.unit_id!==unit.id); if(place) next.placements.push({unit_id:unit.id,x_mm:0,y_mm:0,z_mm:0,layer:0,supported_by:[],yaw_deg:0}); void transition(next,place ? "Đã đặt bó tại gốc hầm; chỉnh vị trí rồi kiểm." : "Đã bỏ vị trí bó."); };
  const deleteUnit = () => { if (!unit) return; const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.cargo_source="USER_ENTERED"; next.units=next.units.filter(u=>u.id!==unit.id); next.placements=next.placements.filter(p=>p.unit_id!==unit.id); void transition(next,"Đã xóa bó."); };
  const previewImport = async () => {
    if (stale || lock.current) { setError("Hãy áp dụng bản nháp trước khi kiểm CSV."); return; }
    const before=revision.current; const text=csvText; lock.current=true; setBusy(true); setError("");
    try { const p=await previewCsv(plan,text); if (revision.current!==before) { setError("Dữ liệu đổi trong lúc kiểm CSV; hãy kiểm lại."); return; } setPreview(p); setPreviewKey(JSON.stringify({plan,text,revision:revision.current})); } catch(e) {setError(e instanceof Error?e.message:"Không kiểm được CSV.");} finally {lock.current=false;setBusy(false);}
  };
  const applyImport = () => { if (!preview?.valid || !preview.candidate || stale || previewKey!==JSON.stringify({plan,text:csvText,revision:revision.current})) {setError("Preview đã cũ; hãy kiểm CSV lại.");return;} void transition(preview.candidate,"Đã nhập manifest; các bó chưa xếp."); };
  const doSave = async () => {
    if(stale || lock.current) {setError("Hãy áp dụng bản nháp trước khi lưu.");return;}
    lock.current=true;setBusy(true);setError(""); const snapshot=structuredClone(plan);
    try {await saveSnapshot(snapshot,saveName); setSaved(await listSnapshots()); setNotice("Đã lưu ảnh chụp đã kiểm; thay đổi mới trong tab chưa tự lưu.");} catch(e) {setError(e instanceof Error?e.message:"Không lưu được.");} finally {lock.current=false;setBusy(false);}
  };
  const doOpen = async () => {
    if(stale || lock.current || !savedId) {setError("Chọn phương án và áp dụng bản nháp trước khi mở.");return;}
    const before=revision.current;lock.current=true;setBusy(true);setError("");
    try { const next=await openSnapshot(savedId); let p=profile; if(next.plan.source==="MIXED_REFERENCE" && !p) p=await requestVesselProfile(); if(before!==revision.current) {setError("Dữ liệu đổi trong lúc mở; phương án trước được giữ.");return;} setHistory(h=>[...h.slice(-19),structuredClone(plan)]);setProfile(p);setResult(next);changeDraft(draftFrom(next.plan));select(next.plan.units[0]?.id ?? "");setPreview(null);setNotice("Đã mở và kiểm lại phương án đã lưu."); } catch(e) {setError(e instanceof Error?e.message:"Không mở được.");} finally {lock.current=false;setBusy(false);}
  };
  const submit = (e: FormEvent) => { e.preventDefault(); void run("draft"); };
  return <div className="app-shell"><div className="main-shell"><header className="topbar"><div className="brand"><strong>SCST</strong><span>Steel Cargo Stowage Tool</span></div><span>{result.plan.source === "MIXED_REFERENCE" ? `THAM CHIẾU · HÀNG ${result.plan.cargo_source === "USER_ENTERED" ? "TỰ NHẬP" : "GIẢ LẬP"}` : result.plan.source === "USER_ENTERED" ? `HẦM TỰ NHẬP · HÀNG ${result.plan.cargo_source === "USER_ENTERED" ? "TỰ NHẬP" : "GIẢ LẬP"} · CHƯA XÁC MINH` : result.plan.cargo_source === "USER_ENTERED" ? "HẦM GIẢ LẬP · HÀNG TỰ NHẬP" : "SYNTHETIC"} · Local</span></header><main id="workspace">
    <div className="page-heading"><div><h1>Lập phương án chất xếp <span className="demo-badge">{plan.source === "MIXED_REFERENCE" ? `THAM CHIẾU / HÀNG ${plan.cargo_source === "USER_ENTERED" ? "TỰ NHẬP" : "GIẢ LẬP"}` : plan.source === "USER_ENTERED" ? "TỰ NHẬP / CHƯA XÁC MINH" : plan.cargo_source === "USER_ENTERED" ? "HẦM GIẢ LẬP / HÀNG TỰ NHẬP" : "SYNTHETIC"}</span></h1><p>Hầm mục tiêu trống · Dữ liệu chưa xác minh, không dùng cho phương án thực.</p></div><div className="heading-actions"><button className="button secondary" disabled={busy || !history.length} onClick={() => void run("undo")}>↶ Bản trước</button><button className="button dark" disabled={busy || stale} onClick={() => void run("demo")}>↻ Khôi phục mẫu</button></div></div>
    <div className="vessel-controls"><button className="button secondary" disabled={busy} onClick={newPlan}>Phương án mới</button><button className="button secondary" disabled={busy || (plan.contract_version === "scst.m2a.v1" && plan.source === "USER_ENTERED")} onClick={detach}>Dùng hầm tự nhập</button><button className="button secondary" disabled={busy || plan.source === "MIXED_REFERENCE"} onClick={() => void switchCase("VR-SII")}>Xem VINAFCO 268</button>{plan.source === "MIXED_REFERENCE" && <label>Cấp tham chiếu <select aria-label="Cấp tham chiếu" value={plan.vessel?.case_id} disabled={busy} onChange={e => void switchCase(e.target.value as "VR-SI" | "VR-SII")}><option value="VR-SI">VR-SI</option><option value="VR-SII">VR-SII</option></select></label>}</div>
    {notice && <p role="status">{notice}</p>}
    {plan.source === "MIXED_REFERENCE" && profile && <section className="scope-note" aria-label="Thông số VINAFCO 268"><strong>VINAFCO 268 · HN-2642 — thân theo hồ sơ, hầm ước tính, hàng {plan.cargo_source === "USER_ENTERED" ? "tự nhập" : "giả lập"}</strong><p>Thân {fmt(profile.dimensions_m.length)} × {fmt(profile.dimensions_m.beam)} × {fmt(profile.dimensions_m.depth)} m. Hầm ước tính 56,405 × 10,34375 × 5,408 m; kiểm dùng bề rộng 10,343 m, lùi 0,375 mm mỗi mạn.</p><p>{(() => { const c=profile.cases.find(c => c.id === plan.vessel?.case_id)!; return `Mức hàng tham chiếu ${tonnes(c.cargo_mass_g)} tấn · TTTP ${fmt(c.deadweight_t)} tấn · mớn ${fmt(c.draft_m)} m · mạn khô hồ sơ ${c.freeboard_mm} mm`; })()}</p><p>{profile.capacity_note} {profile.container_note} {profile.provenance.freeboard_note}</p><p>Khối lượng tàu không và tải sàn cho phép: chưa có dữ liệu. Không xác nhận an toàn hoặc điều kiện vận hành.</p></section>}
    <p>Bản nháp chỉ giữ trong tab; lưu ảnh chụp đã kiểm để mở lại sau khi tải lại hoặc khởi động lại.</p>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {stale && <div className="error-banner" role="status">STALE · Bản nháp chưa được kiểm; kết quả đang thấy thuộc bản đã kiểm trước đó.</div>}
    <div className="stats-row"><section className="stat"><span className="stat-label">KHỐI LƯỢNG MANIFEST</span><strong data-testid="manifest-mass">{tonnes(result.summary.manifest_mass_g)} tấn</strong></section><section className="stat"><span className="stat-label">ĐÃ XẾP / ĐƯỢC XẾP THÊM</span><strong data-testid="placed-mass">{tonnes(result.summary.placed_mass_g)} / {tonnes(plan.limits.voyage_cargo_limit_g - (plan.limits.cargo_onboard_g ?? 0))} tấn</strong></section><section className="stat"><span className="stat-label">TRẠNG THÁI</span><strong data-testid="status">{stale ? "STALE" : result.status}</strong><small>{result.summary.placed_count} đã xếp · {plan.units.length - result.summary.placed_count} chưa xếp</small></section></div>
    <div className="workspace-grid"><Viewer plan={plan} profile={profile} selected={selected} onSelect={select} issueIds={issues} /><section className="editor-card" aria-label="Chỉnh bó hàng"><div className="panel-heading"><div><span className="eyebrow">ĐANG CHỌN</span><h2>{unit?.id ?? "Chưa chọn bó"}</h2>{unit && <p>{unit.name} · {fmt(unit.length_mm)} × {fmt(unit.width_mm)} × {fmt(unit.height_mm)} mm</p>}</div></div><form onSubmit={submit}>
      {unit && ud && <>{plan.contract_version === "scst.m2a.v1" && <><label>ID bó<input aria-label="ID bó" value={ud.id} onChange={e=>editUnit("id",e.target.value)} /></label><label>Tên bó<input aria-label="Tên bó" value={ud.name} onChange={e=>editUnit("name",e.target.value)} /></label><label>Loại bó<select aria-label="Loại bó" value={ud.kind} onChange={e=>editUnit("kind",e.target.value)}><option value="BAR_BUNDLE">Bó thép thanh</option><option value="PIPE_BUNDLE">Bó thép ống</option></select></label><label>Yêu cầu<select aria-label="Yêu cầu" value={ud.requirement} onChange={e=>editUnit("requirement",e.target.value)}><option value="required">Bắt buộc</option><option value="optional">Tùy chọn</option><option value="excluded">Loại trừ</option></select></label>{(["length","width","height"] as const).map(k=><label key={k}>{({length:"Dài",width:"Rộng",height:"Cao"})[k]} (mm)<input aria-label={`Kích thước ${k} (mm)`} value={ud[k]} onChange={e=>editUnit(k,e.target.value)} /></label>)}</>}
      <label>Khối lượng bó (kg)<input aria-label="Khối lượng bó (kg)" value={ud.mass} onChange={(e) => editUnit("mass",e.target.value)} /></label>
      {placement && <><label>Tọa độ X (mm)<input aria-label="Tọa độ X (mm)" value={ud.x} onChange={(e) => editUnit("x",e.target.value)} /></label><label>Tọa độ Y (mm)<input aria-label="Tọa độ Y (mm)" value={ud.y} onChange={(e) => editUnit("y",e.target.value)} /></label><label>Góc xoay<select aria-label="Góc xoay" value={ud.yaw} onChange={(e) => editUnit("yaw",e.target.value)}>{[0,90,180,270].map(v => <option key={v} value={v}>{v}°</option>)}</select></label></>}
      {plan.contract_version === "scst.m2a.v1" && <div><button type="button" className="button secondary" disabled={busy || (!placement && unit.requirement === "excluded")} onClick={()=>changePlacement(!placement)}>{placement ? "Bỏ vị trí" : "Đặt bó"}</button><button type="button" className="button secondary" disabled={busy} onClick={deleteUnit}>Xóa bó</button></div>}</>}
      {plan.contract_version === "scst.m2a.v1" && plan.source === "USER_ENTERED" && <><p>Hầm tự nhập · chưa xác minh.</p><label>Tên hầm<input aria-label="Tên hầm" value={draft.holdName} onChange={e=>changeDraft({...draft,holdName:e.target.value})}/></label>{(["holdLength","holdWidth","holdHeight"] as const).map(k=><label key={k}>{({holdLength:"Chiều dài hầm",holdWidth:"Chiều rộng hầm",holdHeight:"Chiều cao hầm"})[k]} (mm)<input aria-label={`Hầm ${k} (mm)`} value={draft[k]} onChange={e=>changeDraft({...draft,[k]:e.target.value})}/></label>)}</>}
      <label>{plan.source === "MIXED_REFERENCE" ? "Mức hàng tham chiếu (kg)" : "Giới hạn chứng nhận (kg)"}<input aria-label="Giới hạn chứng nhận (kg)" readOnly={plan.source === "MIXED_REFERENCE"} value={draft.certificate} onChange={(e) => changeDraft({...draft, certificate:e.target.value})} /></label>
      <label>Giới hạn chuyến (kg)<input aria-label="Giới hạn chuyến (kg)" value={draft.voyage} onChange={(e) => changeDraft({...draft, voyage:e.target.value})} /></label>
      <label>Hàng đã có trên tàu (kg)<input aria-label="Hàng đã có trên tàu (kg)" value={draft.onboard} onChange={(e) => changeDraft({...draft, onboard:e.target.value})} /></label>
      <button className="button primary apply-button" disabled={busy} type="submit">{busy ? "Đang kiểm…" : "Áp dụng & kiểm lại"}</button>
    </form></section></div>
    <section className="editor-card m2a-card"><h2>Thêm bó hàng</h2><p>Mỗi dòng là một bó; dữ liệu nhập chưa xác minh.</p>{(["id","name","length","width","height","mass"] as const).map(k=><label key={k}>{({id:"ID bó mới",name:"Tên bó mới",length:"Chiều dài bó mới (mm)",width:"Chiều rộng bó mới (mm)",height:"Chiều cao bó mới (mm)",mass:"Khối lượng bó mới (kg)"})[k]}<input aria-label={`Bó mới ${k}`} value={newUnit[k]} onChange={e=>{revision.current++;setNewUnit({...newUnit,[k]:e.target.value});}} /></label>)}<label>Loại bó mới<select aria-label="Loại bó mới" value={newUnit.kind} onChange={e=>{revision.current++;setNewUnit({...newUnit,kind:e.target.value});}}><option value="BAR_BUNDLE">Bó thép thanh</option><option value="PIPE_BUNDLE">Bó thép ống</option></select></label><label>Yêu cầu bó mới<select aria-label="Yêu cầu bó mới" value={newUnit.requirement} onChange={e=>{revision.current++;setNewUnit({...newUnit,requirement:e.target.value});}}><option value="required">Bắt buộc</option><option value="optional">Tùy chọn</option><option value="excluded">Loại trừ</option></select></label><button className="button secondary" disabled={busy} onClick={addUnit}>Thêm bó</button></section>
    <section className="editor-card m2a-card"><h2>Nhập CSV UTF-8</h2><p>Mỗi dòng một bó; kg dùng dấu chấm, tối đa 3 số lẻ. Ví dụ giả lập để lưu thành CSV UTF-8:</p><pre>{"id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\nB-001,Bo thep mau,BAR_BUNDLE,required,6000,900,650,2500.001"}</pre><textarea aria-label="Nội dung CSV" value={csvText} onChange={e=>{revision.current++;setCsvText(e.target.value);setPreview(null);}} /><label>Chọn tệp CSV<input type="file" accept=".csv,text/csv" aria-label="Chọn tệp CSV" onChange={async e=>{const file=e.target.files?.[0];if(!file)return;const before=++revision.current;try {if(file.size>1048576)throw new Error("Tệp vượt 1 MiB.");const bytes=await file.arrayBuffer();const text=new TextDecoder("utf-8",{fatal:true}).decode(bytes);if(before!==revision.current){setError("Dữ liệu đã đổi trong lúc đọc tệp; hãy chọn lại.");return;}setCsvText(text);setPreview(null);} catch {setError("Tệp phải là CSV UTF-8 tối đa 1 MiB.");}}}/></label><button className="button secondary" disabled={busy} onClick={()=>void previewImport()}>Kiểm CSV</button><button className="button secondary" disabled={busy || !preview?.valid} onClick={applyImport}>Áp dụng CSV</button>{preview && <div role="status">{preview.valid ? `Xem trước: ${preview.count} bó · ${tonnes(preview.total_mass_g)} tấn; áp dụng sẽ bỏ vị trí cũ.` : <ul>{preview.errors.map((e,i)=><li key={i}>Dòng {e.row} · {e.field}: {e.message}</li>)}</ul>}</div>}</section>
    <section className="editor-card m2a-card"><h2>Lưu và mở local</h2><p>Mỗi lần lưu tạo một ảnh chụp mới; danh sách hiển thị 100 bản gần nhất.</p><label>Tên phương án lưu<input aria-label="Tên phương án lưu" maxLength={100} value={saveName} onChange={e=>{revision.current++;setSaveName(e.target.value);}}/></label><button className="button secondary" disabled={busy} onClick={()=>void doSave()}>Lưu phương án</button><label>Phương án đã lưu<select aria-label="Phương án đã lưu" value={savedId} onChange={e=>{revision.current++;setSavedId(e.target.value);}}><option value="">Chọn phương án</option>{saved.map(v=><option key={v.id} value={v.id}>{v.name} · {savedTime(v.created_utc)}</option>)}</select></label><button className="button secondary" disabled={busy || !savedId} onClick={()=>void doOpen()}>Mở phương án</button></section>
    <div className="workspace-grid"><section id="cargo" className="editor-card"><h2>Danh sách hàng</h2><div className="table-wrap"><table><thead><tr><th>ID</th><th>Loại / yêu cầu</th><th>Kích thước (mm)</th><th>Khối lượng</th><th>Vị trí / lý do</th></tr></thead><tbody>{plan.units.map((u) => {const p=plan.placements.find(x=>x.unit_id===u.id); return <tr key={u.id} data-testid={`unit-${u.id}`} aria-selected={selected===u.id} onClick={()=>select(u.id)}><td><button className="text-button" onClick={()=>select(u.id)}>{u.id}</button></td><td>{u.kind === "BAR_BUNDLE" ? "Bó thép thanh" : "Bó thép ống"} · {u.requirement === "required" ? "Bắt buộc" : u.requirement === "optional" ? "Tùy chọn" : "Loại trừ"}</td><td>{u.length_mm} × {u.width_mm} × {u.height_mm}</td><td>{massLabel(u.mass_g)}</td><td>{p ? `${p.x_mm}, ${p.y_mm}, ${p.z_mm ?? 0} · ${p.yaw_deg}°` : u.requirement === "excluded" ? "Đã loại trừ" : u.requirement === "optional" ? "Tùy chọn chưa xếp" : "Bắt buộc chưa xếp"}</td></tr>})}</tbody></table></div></section><section id="checks" className="editor-card"><h2>Kết quả kiểm</h2><p>{plan.source === "MIXED_REFERENCE" ? "Mức hàng tham chiếu" : "Chứng nhận"}: {tonnes(plan.limits.certificate_cargo_limit_g)} tấn · Chuyến: {tonnes(plan.limits.voyage_cargo_limit_g)} tấn · Đã có ngoài hầm: {tonnes(plan.limits.cargo_onboard_g ?? 0)} tấn</p><p>Được xếp thêm: {tonnes(plan.limits.voyage_cargo_limit_g - (plan.limits.cargo_onboard_g ?? 0))} tấn</p>{result.issues.length ? <ul>{result.issues.map((i,n)=><li key={n}><strong>{i.code}</strong> {i.message}</li>)}</ul> : <p>Không phát hiện lỗi trong các kiểm M1.</p>}<div className="scope-note"><strong>CHƯA KIỂM</strong><p>{result.unchecked.join(" · ")}</p></div><p>Chưa đủ điều kiện vận hành.</p></section></div>
  </main></div></div>;
}
