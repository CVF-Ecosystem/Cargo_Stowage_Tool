import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import Viewer from "../viewer-3d/Viewer";
import ComparisonPanel from "./ComparisonPanel";
import CargoRevisionPanel from "./CargoRevisionPanel";
import { requestEvaluation, getVesselProfile, requestProfileCasePlan, profileBody, getPipeLibrary, previewPipeList, previewPlanner, previewCsv, saveSnapshot, listSnapshots, openSnapshot, listCargoRevisions, previewRevisionPlan, rebaseSnapshot, type CsvPreview, type SnapshotListItem, type RebaseResult, type CompareResult, type ProfileDetail, type PipeLibrary, type PlannerPreview, type PlannerAlgorithm, DEFAULT_PLANNER_ALGORITHM } from "../api/client";
import RebaseDropped from "./RebaseDropped";
import PackingInfo, { packingCell, packingFilterOptions, slackText, type PackingFilter } from "./PackingInfo";
import { getRevisionPacking, indexPacking, packingFor, planRevisionId, type RevisionPacking } from "./packing";
import VesselProfilePanel, { fieldStatusLabel, type OpenCurrent } from "./VesselProfilePanel";
import BackupPanel from "./BackupPanel";
import { dimensions, fmt, displayKg, displayCm, formatCm, formatKg, formatMetres, massLabel, parseKg, parseCm, tonnes, isPipePlan, type Evaluation, type Plan } from "./model";

function savedTime(value: string): string {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "Thời gian không hợp lệ";
  const parts = new Intl.DateTimeFormat("vi-VN", {day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(date);
  const part = (type: string) => parts.find(p => p.type === type)?.value ?? "";
  return `${part("day")}-${part("month")}-${part("year")} ${part("hour")}:${part("minute")}`;
}

const sourceWarnings: Record<string,string> = {
  cbm_is_one_bundle: "CBM nguồn chỉ tính một bó; tổng nhóm cần nhân số bó",
  diameter_label_unit_pair_mismatch: "Nhãn inch có thể không khớp đường kính ngoài",
  duplicate_source_serial: "STT nguồn trùng; vẫn giữ dòng là nhóm riêng",
  manual_kg_per_m_difference: "Khối lượng dài là số nhập tay khác công thức lân cận",
  optional_size_labels_missing: "Thiếu nhãn kích cỡ phụ; giữ kích thước nguồn còn lại",
  packaging_envelope_conflict: "Khối bao không phù hợp với số ống; cần xác minh kích thước",
};

type UnitDraft = { id: string; name: string; kind: string; requirement: string; length: string; width: string; height: string; mass: string; x: string; y: string; yaw: string };
export type Draft = { units: Record<string, UnitDraft>; certificate: string; voyage: string; onboard: string; holdName: string; holdLength: string; holdWidth: string; holdHeight: string; dirty: Record<string,true> };
export function draftFrom(plan: Plan): Draft {
  const units: Record<string, UnitDraft> = {};
  const placed = new Map(plan.placements.map(p=>[p.unit_id,p]));
  for (const u of plan.units) {
    const p = placed.get(u.id);
    units[u.id] = { id:u.id, name:u.name, kind:u.kind, requirement:u.requirement, length:displayCm(u.length_mm), width:displayCm(u.width_mm), height:displayCm(u.height_mm), mass:displayKg(u.mass_g), x:displayCm(p?.x_mm ?? 0), y:displayCm(p?.y_mm ?? 0), yaw:String(p?.yaw_deg ?? 0) };
  }
  return { units, holdName:plan.hold.name, holdLength:displayCm(plan.hold.length_mm), holdWidth:displayCm(plan.hold.width_mm), holdHeight:displayCm(plan.hold.height_mm), certificate:displayKg(plan.limits.certificate_cargo_limit_g), voyage:displayKg(plan.limits.voyage_cargo_limit_g), onboard:displayKg(plan.limits.cargo_onboard_g ?? 0), dirty:{} };
}
export function markDirty(dirty: Draft["dirty"], key: string, text: string, original: string | number, parse: (value:string)=>string | number): Draft["dirty"] {
  const next={...dirty};
  try { if(parse(text)===original) delete next[key]; else next[key]=true; }
  catch { next[key]=true; }
  return next;
}
export function applyDraft(plan: Plan, draft: Draft): Plan {
  const next=structuredClone(plan);const changed=(key:string)=>Boolean(draft.dirty[key]);
  if(changed("limits.certificate"))next.limits.certificate_cargo_limit_g=parseKg(draft.certificate);
  if(changed("limits.voyage"))next.limits.voyage_cargo_limit_g=parseKg(draft.voyage);
  if(changed("limits.onboard"))next.limits.cargo_onboard_g=parseKg(draft.onboard,true);
  if(next.contract_version!=="scst.m1.v1" && next.source==="USER_ENTERED") {
    if(changed("hold.holdName"))next.hold.name=draft.holdName;
    if(changed("hold.holdLength"))next.hold.length_mm=parseCm(draft.holdLength);
    if(changed("hold.holdWidth"))next.hold.width_mm=parseCm(draft.holdWidth);
    if(changed("hold.holdHeight"))next.hold.height_mm=parseCm(draft.holdHeight);
  }
  const placements=new Map<string,Plan["placements"][number]>();const byId=new Map(next.placements.map(p=>[p.unit_id,p]));let cargoEdited=false;
  for(const unit of next.units){
    const originalId=unit.id;const d=draft.units[originalId];const p=byId.get(originalId);
    const has=(k:keyof UnitDraft)=>changed(`unit.${originalId}.${k}`);
    if(isPipePlan(next) && has("requirement"))unit.requirement=d.requirement as typeof unit.requirement;
    if(next.contract_version==="scst.m2a.v1"){
      if(has("id"))unit.id=d.id;if(has("name"))unit.name=d.name;if(has("kind"))unit.kind=d.kind as typeof unit.kind;if(has("requirement"))unit.requirement=d.requirement as typeof unit.requirement;
      if(has("length"))unit.length_mm=parseCm(d.length);if(has("width"))unit.width_mm=parseCm(d.width);if(has("height"))unit.height_mm=parseCm(d.height);
      cargoEdited ||= (["id","name","kind","requirement","length","width","height","mass"] as const).some(has);
    }
    if(!isPipePlan(next) && has("mass"))unit.mass_g=parseKg(d.mass);
    if(p && unit.requirement!=="excluded")placements.set(originalId,{...p,unit_id:unit.id,x_mm:has("x")?parseCm(d.x):p.x_mm,y_mm:has("y")?parseCm(d.y):p.y_mm,yaw_deg:has("yaw")?Number(d.yaw):p.yaw_deg});
  }
  next.placements=plan.placements.flatMap(p=>{const updated=placements.get(p.unit_id);return updated?[updated]:[];});if(next.contract_version==="scst.m2a.v1" && cargoEdited)next.cargo_source="USER_ENTERED";
  return next;
}

// Preserve only edits made after submission, comparing them to the newly checked plan.
export function rebaseDraft(current: Draft, submitted: Draft, original: Plan, checked: Plan): Draft {
  const fresh=draftFrom(checked);const nextUnits=new Map(checked.units.map(u=>[u.id,u]));const positions=new Map(checked.placements.map(p=>[p.unit_id,p]));
  const keys: (keyof UnitDraft)[]=["id","name","kind","requirement","length","width","height","mass","x","y","yaw"];
  for(const old of original.units){
    const nextId=submitted.dirty[`unit.${old.id}.id`] ? submitted.units[old.id]?.id : old.id;
    const unit=nextUnits.get(nextId);const now=current.units[old.id];const sent=submitted.units[old.id];
    if(!unit || !now || !sent)continue;
    const pos=positions.get(nextId);
    const originals: Record<keyof UnitDraft,string|number>={id:unit.id,name:unit.name,kind:unit.kind,requirement:unit.requirement,length:unit.length_mm,width:unit.width_mm,height:unit.height_mm,mass:unit.mass_g,x:pos?.x_mm ?? 0,y:pos?.y_mm ?? 0,yaw:pos?.yaw_deg ?? 0};
    for(const key of keys){
      const oldKey=`unit.${old.id}.${key}`;
      if(now[key]===sent[key] && Boolean(current.dirty[oldKey])===Boolean(submitted.dirty[oldKey]))continue;
      fresh.units[nextId][key]=now[key];
      const parse=key==="mass" ? parseKg : (["length","width","height","x","y"].includes(key) ? parseCm : key==="yaw" ? Number : (v:string)=>v);
      fresh.dirty=markDirty(fresh.dirty,`unit.${nextId}.${key}`,now[key],originals[key],parse);
    }
  }
  for(const key of ["holdName","holdLength","holdWidth","holdHeight"] as const){
    const k=`hold.${key}`;if(current[key]===submitted[key] && Boolean(current.dirty[k])===Boolean(submitted.dirty[k]))continue;
    fresh[key]=current[key];const originals={holdName:checked.hold.name,holdLength:checked.hold.length_mm,holdWidth:checked.hold.width_mm,holdHeight:checked.hold.height_mm};
    fresh.dirty=markDirty(fresh.dirty,k,current[key],originals[key],key==="holdName"?(v:string)=>v:parseCm);
  }
  for(const key of ["certificate","voyage","onboard"] as const){
    const k=`limits.${key}`;if(current[key]===submitted[key] && Boolean(current.dirty[k])===Boolean(submitted.dirty[k]))continue;
    fresh[key]=current[key];const originals={certificate:checked.limits.certificate_cargo_limit_g,voyage:checked.limits.voyage_cargo_limit_g,onboard:checked.limits.cargo_onboard_g ?? 0};
    fresh.dirty=markDirty(fresh.dirty,k,current[key],originals[key],v=>parseKg(v,key==="onboard"));
  }
  return fresh;
}

// The profile a MIXED_REFERENCE plan names (built-in VINAFCO268 is version 1); reused when already loaded.
async function profileFor(plan: Plan, current: ProfileDetail | null): Promise<ProfileDetail | null> {
  if (plan.source !== "MIXED_REFERENCE" || !plan.vessel) return current;
  const id = plan.vessel.vessel_id, version = plan.vessel.profile_version ?? 1;
  if (current && current.id === id && current.version === version) return current;
  return getVesselProfile(id, version);
}

// Summary of a profile other than VINAFCO268: each number with its provenance status and its source documents (DA03).
function ProfileSummary({ detail, caseId }: { detail: ProfileDetail; caseId: string }) {
  const body = profileBody(detail);
  const d = body.dimensions_m, h = body.hold, fs = body.provenance.field_status;
  return <section className="scope-note" aria-label={`Thông số ${body.name}`}>
    <strong>{body.name}{body.registration ? ` · ${body.registration}` : ""}</strong>
    <p>Thân {formatMetres(d.length * 1000)} × {formatMetres(d.beam * 1000)} × {formatMetres(d.depth * 1000)} m.</p>
    <p>Hầm {formatMetres(h.length_mm)} × {formatMetres(h.width_mm)} × {formatMetres(h.height_mm)} m ({fieldStatusLabel(h.status)}); {h.name}.</p>
    <p>Trạng thái số liệu: thân {fieldStatusLabel(fs.dimensions_m)} · hầm {fieldStatusLabel(fs.hold)} · trường hợp tải {fieldStatusLabel(fs.cases)}.</p>
    <ul aria-label="Trường hợp tải của tàu">{body.cases.map(c => <li key={c.id}>{c.id}{c.id === caseId ? " (đang mở)" : ""}: hàng {tonnes(c.cargo_mass_g)} tấn · mớn {fmt(c.draft_m)} m</li>)}</ul>
    <p>Nguồn: {body.provenance.source_documents.map(s => s.title).join("; ") || "chưa ghi"}.</p>
    <p>Kiểm tọa độ: {detail.verification.result}; hộp bao GLB {detail.verification.bounds.contains_hold ? "chứa" : "không chứa"} hầm.</p>
    <p>Không xác nhận an toàn hoặc điều kiện vận hành.</p>
  </section>;
}

// Multi-layer preview summary (M3a): columns stand on the hold floor (z 0); layers come from the placement index.
function stackSummary(preview: PlannerPreview) {
  const placements = preview.evaluation.plan.placements;
  const columns = placements.filter(p => p.z_mm === 0).length;
  const maxLayers = placements.length ? Math.max(...placements.map(p => p.layer)) + 1 : 0;
  return { columns, maxLayers, placed: preview.evaluation.summary.placed_count, unplaced: preview.unplaced.length };
}

export default function Workspace() {
  const [result, setResult] = useState<Evaluation | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const draftRef = useRef<Draft | null>(null);
  const [profile, setProfile] = useState<ProfileDetail | null>(null);
  const [notice, setNotice] = useState("");
  const [planner, setPlanner] = useState<PlannerPreview | null>(null);
  const [plannerKey, setPlannerKey] = useState("");
  // null = automatic: a pipe-list plan defaults to columns-v1, other plans to the single-layer planner (see plannerAlgorithm below).
  // An explicit choice sticks; a changed effective algorithm invalidates the current preview through plannerKey.
  const [plannerChoice, setPlannerChoice] = useState<PlannerAlgorithm | null>(null);
  const plannerKeyOf = (p: Plan, algorithm: PlannerAlgorithm) => JSON.stringify({plan:p,revision:revision.current,algorithm});
  const [appliedReasons, setAppliedReasons] = useState<{planKey:string; unplaced:PlannerPreview["unplaced"]} | null>(null);
  const [reasonFilter, setReasonFilter] = useState("ALL");
  const [reasonPage, setReasonPage] = useState(0);
  const [pipeLibrary, setPipeLibrary] = useState<PipeLibrary | null>(null);
  const [pipeCandidate, setPipeCandidate] = useState<Evaluation | null>(null);
  const [pipePreviewKey, setPipePreviewKey] = useState("");
  const [groupFilter, setGroupFilter] = useState("ALL");
  const [packingFilter, setPackingFilter] = useState<PackingFilter>("ALL");
  const [packingData, setPackingData] = useState<RevisionPacking | null>(null);
  const [packingError, setPackingError] = useState("");
  const [focusGroup, setFocusGroup] = useState<{groupId:string; serial:number} | null>(null);
  const [page, setPage] = useState(0);
  const [csvText, setCsvText] = useState("");
  const [preview, setPreview] = useState<CsvPreview | null>(null);
  const [previewKey, setPreviewKey] = useState("");
  const [saved, setSaved] = useState<SnapshotListItem[]>([]);
  const [rebaseInfo, setRebaseInfo] = useState<{name:string; result:RebaseResult} | null>(null);
  const [externalBaseline, setExternalBaseline] = useState<{token:number; plan:Plan; label:string; comparison:CompareResult} | null>(null);
  const [saveName, setSaveName] = useState("");
  const [savedId, setSavedId] = useState("");
  const [reloadToken, setReloadToken] = useState(0);
  const [newUnit, setNewUnit] = useState({id:"",name:"",kind:"BAR_BUNDLE",requirement:"required",length:"",width:"",height:"",mass:""});
  const revision = useRef(0);
  const [selected, setSelected] = useState("ST-001");
  const selectedRef=useRef("ST-001");
  const select=useCallback((id: string) => { revision.current++; selectedRef.current=id; setSelected(id); }, []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<Plan[]>([]);
  const lock = useRef(false);
  const changeDraft = (d: Draft) => { revision.current++; draftRef.current = d; setDraft(d); setAppliedReasons(null); setPlanner(null); };
  useEffect(() => {
    let live = true;
    requestEvaluation().then((data) => { if (live) { setResult(data); changeDraft(draftFrom(data.plan)); } }).catch(() => { if (live) setError("Không kết nối được backend. Thử lại."); });
    listSnapshots().then((items) => { if (live) setSaved(items); }).catch(() => { if (live) setError("Không thể đọc danh sách phương án local."); });
    return () => { live = false; };
  }, []);
  useEffect(() => {
    if (!result || !isPipePlan(result.plan) || pipeLibrary) return;
    let live=true; getPipeLibrary().then(p=>{if(live)setPipeLibrary(p);}).catch(()=>{if(live)setError("Không tải được thư viện list ống.");}); return ()=>{live=false;};
  },[result?.plan.contract_version,pipeLibrary]);
  const packingRevision = result ? planRevisionId(result.plan) : null;
  useEffect(() => {
    // SUP-03 D3: derived packing is read per pinned revision; it is never part of the Plan or snapshot.
    if (!packingRevision) { setPackingData(null); setPackingError(""); return; }
    let live = true; setPackingError("");
    setPackingData(p => p && p.revision_id === packingRevision ? p : null);
    getRevisionPacking(packingRevision).then(p => { if (live) setPackingData(p); }).catch(e => { if (live) { setPackingData(null); setPackingError(e instanceof Error ? e.message : "Không đọc được cách xếp ống dẫn xuất; hiển thị khối bao."); } });
    return () => { live = false; };
  }, [packingRevision]);
  const packingIndex = useMemo(() => packingData && packingData.revision_id === packingRevision ? indexPacking(packingData) : null, [packingData, packingRevision]);
  const openGroup = (groupId: string) => { setFocusGroup(f => ({groupId, serial: (f?.serial ?? 0) + 1})); };
  const stale = !!draft && Object.keys(draft.dirty).length > 0;
  const run = async (mode: "draft" | "undo" | "demo") => {
    if (lock.current || !result || !draftRef.current) return;
    if (mode !== "draft" && stale) { setError("Hãy áp dụng bản nháp trước khi đổi phương án; dữ liệu đang nhập được giữ nguyên."); return; }
    let plan: Plan | undefined;
    try { plan = mode === "draft" ? applyDraft(result.plan, draftRef.current) : mode === "undo" ? history[history.length - 1] : undefined; }
    catch (e) { setError(`${e instanceof Error ? e.message : "Dữ liệu sai."} Bản nháp chưa được kiểm; bản trước vẫn được giữ.`); return; }
    const submittedDraft=structuredClone(draftRef.current);
    const captured = JSON.stringify(draftRef.current); const capturedRevision=revision.current;
    lock.current = true; setBusy(true); setError("");
    try {
      const next = await requestEvaluation(plan);
      if (mode !== "draft" && (JSON.stringify(draftRef.current) !== captured || revision.current !== capturedRevision)) { setError("Bản nháp đã đổi trong lúc chuyển; dữ liệu và kết quả trước được giữ nguyên."); return; }
      setHistory((h) => mode === "undo" ? h.slice(0, -1) : [...h.slice(-19), structuredClone(result.plan)]);
      setResult(next); if (mode !== "draft") setRebaseInfo(null);
      if (mode === "draft" && result.plan.placements.some(p => !next.plan.placements.some(q => q.unit_id === p.unit_id)) && next.plan.units.some(u => u.requirement === "excluded")) setNotice("Bó loại trừ đã được bỏ vị trí trong hầm.");
      if (JSON.stringify(draftRef.current) === captured) { changeDraft(draftFrom(next.plan)); }
      else if (mode === "draft" && draftRef.current) { changeDraft(rebaseDraft(draftRef.current,submittedDraft,result.plan,next.plan)); }
      if (!next.plan.units.some(u=>u.id===selectedRef.current)) select(next.plan.units[0]?.id ?? "");
    } catch (e) {
      setError(`${e instanceof Error ? e.message : "Không kết nối được backend."} Bản nháp chưa được kiểm; bản trước vẫn được giữ.`);
    } finally { lock.current = false; setBusy(false); }
  };
  // Opens a vessel profile (built-in or stored) at one of its cases; the loaded profile is reused when id and version match.
  const switchVessel = async (id: string, version: number, caseId: string) => {
    if (lock.current || !result || !draftRef.current) return;
    if (stale) { setError("Hãy áp dụng bản nháp trước khi đổi phương tiện hoặc cấp tham chiếu; dữ liệu đang nhập được giữ nguyên."); return; }
    lock.current = true; setBusy(true); setError(""); setNotice("");
    const captured = JSON.stringify(draftRef.current); const capturedRevision=revision.current;
    try {
      const [p, template] = await Promise.all([profile && profile.id === id && profile.version === version ? profile : getVesselProfile(id, version), requestProfileCasePlan({ id, version }, caseId)]);
      const old = result.plan; const next = template.plan;
      const onboard = old.limits.cargo_onboard_g ?? 0;
      if (onboard > next.limits.certificate_cargo_limit_g || onboard > next.limits.voyage_cargo_limit_g) throw new Error("Hàng đã có vượt mức hàng tham chiếu của cấp được chọn; giảm số này trước khi chuyển.");
      next.units = structuredClone(old.units); next.placements = structuredClone(old.placements);
      if (old.contract_version !== "scst.m1.v1") { next.contract_version=old.contract_version; next.cargo_source=old.cargo_source; next.cargo_dataset=old.cargo_dataset; if(old.cargo_revision) next.cargo_revision=structuredClone(old.cargo_revision); }
      next.limits.cargo_onboard_g = old.limits.cargo_onboard_g;
      // The new case or vessel plan keeps its own voyage limit from the template (no carry-over from the old plan).
      const evaluated = await requestEvaluation(next);
      if (JSON.stringify(draftRef.current) !== captured || revision.current !== capturedRevision) { setError("Bản nháp đã thay đổi trong lúc chuyển; vẫn giữ bản nháp và trạng thái trước."); return; }
      setProfile(p); setHistory(h => [...h.slice(-19), structuredClone(old)]); setResult(evaluated); changeDraft(draftFrom(evaluated.plan));
      setNotice(`Giới hạn chuyến theo cấp ${caseId}: ${tonnes(evaluated.plan.limits.voyage_cargo_limit_g)} tấn; vẫn có thể chỉnh trong "Giới hạn chuyến (kg)".`);
    } catch (e) { setError(e instanceof Error ? e.message : "Không đổi được trạng thái."); }
    finally { lock.current = false; setBusy(false); }
  };
  const issues = useMemo(() => new Set([...(result?.issues.flatMap((i) => i.unit_ids) ?? []),...(result?.affected_unit_ids ?? [])]), [result]);
  if (!result || !draft) return <main className="loading-panel"><h1>SCST · SYNTHETIC</h1><p role="status">{error || "Đang mở phương án mẫu…"}</p>{error && <button onClick={() => location.reload()}>Thử lại</button>}</main>;
  const plan = result.plan;
  const plannerAlgorithm: PlannerAlgorithm = plannerChoice ?? (isPipePlan(plan) ? "columns-v1" : DEFAULT_PLANNER_ALGORITHM);
  const vessel = plan.vessel;
  // The loaded profile is the one the plan names; only then do its cases, numbers and viewer data apply.
  const profileOpen = !!profile && plan.source === "MIXED_REFERENCE" && !!vessel && profile.id === vessel.vessel_id && profile.version === (vessel.profile_version ?? 1);
  const body = profileOpen && profile ? profileBody(profile) : null;
  const current: OpenCurrent = plan.source === "MIXED_REFERENCE" && vessel ? { id: vessel.vessel_id, version: vessel.profile_version ?? 1, caseId: vessel.case_id } : null;
  const caseOptions = body ? body.cases.map(c => c.id) : vessel ? [vessel.case_id] : [];
  const unit = plan.units.find((u) => u.id === selected);
  const placement = plan.placements.find((p) => p.unit_id === selected);
  const ud = draft.units[selected];
  const editUnit = (key: keyof UnitDraft, value: string) => {
    if(!unit)return;
    const originals: Record<keyof UnitDraft,string|number>={id:unit.id,name:unit.name,kind:unit.kind,requirement:unit.requirement,length:unit.length_mm,width:unit.width_mm,height:unit.height_mm,mass:unit.mass_g,x:placement?.x_mm ?? 0,y:placement?.y_mm ?? 0,yaw:placement?.yaw_deg ?? 0};
    const parse = key === "mass" ? parseKg : (["length","width","height","x","y"].includes(key) ? parseCm : key === "yaw" ? Number : (v:string)=>v);
    changeDraft({...draft,units:{...draft.units,[selected]:{...ud,[key]:value}},dirty:markDirty(draft.dirty,`unit.${selected}.${key}`,value,originals[key],parse)});
  };
  const editHold = (key:"holdName"|"holdLength"|"holdWidth"|"holdHeight",value:string) => {
    const originals={holdName:plan.hold.name,holdLength:plan.hold.length_mm,holdWidth:plan.hold.width_mm,holdHeight:plan.hold.height_mm};
    changeDraft({...draft,[key]:value,dirty:markDirty(draft.dirty,`hold.${key}`,value,originals[key],key==="holdName"?(v:string)=>v:parseCm)});
  };
  const editLimit = (key:"certificate"|"voyage"|"onboard",value:string) => {
    const originals={certificate:plan.limits.certificate_cargo_limit_g,voyage:plan.limits.voyage_cargo_limit_g,onboard:plan.limits.cargo_onboard_g ?? 0};
    changeDraft({...draft,[key]:value,dirty:markDirty(draft.dirty,`limits.${key}`,value,originals[key],v=>parseKg(v,key==="onboard"))});
  };
  const transition = async (candidate: Plan, label: string) => {
    if (lock.current || stale) { if(stale) setError("Hãy áp dụng bản nháp trước khi đổi phương án."); return; }
    const before=revision.current; lock.current=true; setBusy(true); setError("");
    try {
      const next=await requestEvaluation(candidate);
      const newProfile = await profileFor(next.plan, profile);
      if (revision.current !== before) { setError("Dữ liệu đã đổi trong lúc chờ; phương án trước được giữ."); return; }
      setHistory(h=>[...h.slice(-19),structuredClone(result.plan)]); setResult(next); setProfile(newProfile); changeDraft(draftFrom(next.plan));
      select(next.plan.units.some(u=>u.id===selectedRef.current) ? selectedRef.current : next.plan.units[0]?.id ?? ""); setPreview(null); setRebaseInfo(null); setNotice(label);
    } catch (e) { setError(e instanceof Error ? e.message : "Không thể cập nhật."); }
    finally { lock.current=false; setBusy(false); }
  };
  const newPlan = () => { const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.source="USER_ENTERED"; next.vessel=null; next.cargo_source="SYNTHETIC"; next.cargo_dataset=null; delete next.cargo_revision; next.units=[]; next.placements=[]; void transition(next,"Phương án mới; hầm tự nhập chưa xác minh."); };
  const detach = () => { const next=structuredClone(plan); if(!isPipePlan(next)) next.contract_version="scst.m2a.v1"; next.source="USER_ENTERED"; next.vessel=null; next.cargo_source=next.cargo_source ?? "SYNTHETIC"; void transition(next,"Đã bỏ liên kết phương tiện; hầm tự nhập chưa xác minh."); };
  const addUnit = () => {
    try {
      const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.cargo_source="USER_ENTERED"; delete next.cargo_revision;
      next.units.push({id:newUnit.id,name:newUnit.name,kind:newUnit.kind as "BAR_BUNDLE" | "PIPE_BUNDLE",requirement:newUnit.requirement as "required" | "optional" | "excluded",length_mm:parseCm(newUnit.length),width_mm:parseCm(newUnit.width),height_mm:parseCm(newUnit.height),mass_g:parseKg(newUnit.mass)});
      void transition(next,"Đã thêm bó chưa xếp.");
    } catch(e) { setError(e instanceof Error ? e.message : "Dữ liệu bó không hợp lệ."); }
  };
  const changePlacement = (place: boolean) => { if (!unit) return; const next=structuredClone(plan); if(!isPipePlan(next)) next.contract_version="scst.m2a.v1"; next.cargo_source=next.cargo_source ?? "SYNTHETIC"; next.placements=next.placements.filter(p=>p.unit_id!==unit.id); if(place) next.placements.push({unit_id:unit.id,x_mm:0,y_mm:0,z_mm:0,layer:0,supported_by:[],yaw_deg:0}); void transition(next,place ? "Đã đặt bó tại gốc hầm; chỉnh vị trí rồi kiểm." : "Đã bỏ vị trí bó."); };
  const deleteUnit = () => { if (!unit) return; const next=structuredClone(plan); next.contract_version="scst.m2a.v1"; next.cargo_source="USER_ENTERED"; delete next.cargo_revision; next.units=next.units.filter(u=>u.id!==unit.id); next.placements=next.placements.filter(p=>p.unit_id!==unit.id); void transition(next,"Đã xóa bó."); };
  const checkPipeList = async () => {
    if (stale || lock.current) {setError("Hãy áp dụng bản nháp trước khi xem list ống.");return;}
    const before=revision.current;lock.current=true;setBusy(true);setError("");
    try {const latest=(await listCargoRevisions()).latest_revision_id;const [library,candidate]=await Promise.all([getPipeLibrary(),latest.endsWith("@R0000") ? previewPipeList(plan) : previewRevisionPlan(latest,plan)]);if(before!==revision.current){setError("Dữ liệu đổi trong lúc xem trước; hãy kiểm lại.");return;}setPipeLibrary(library);setPipeCandidate(candidate);setPipePreviewKey(JSON.stringify({plan,revision:revision.current}));} catch(e){setError(e instanceof Error?e.message:"Không xem được list ống.");} finally{lock.current=false;setBusy(false);}
  };
  const applyPipeList = () => {if(!pipeCandidate || stale || pipePreviewKey!==JSON.stringify({plan,revision:revision.current})){setError("Xem trước đã cũ; hãy kiểm lại list ống.");return;}setGroupFilter("ALL");setPage(0);void transition(pipeCandidate.plan,"Đã nạp list ống; tất cả bó chưa xếp.");setPipeCandidate(null);};
  const previewImport = async () => {
    if (stale || lock.current) { setError("Hãy áp dụng bản nháp trước khi kiểm CSV."); return; }
    const before=revision.current; const text=csvText; lock.current=true; setBusy(true); setError("");
    try { const p=await previewCsv(plan,text); if (revision.current!==before) { setError("Dữ liệu đổi trong lúc kiểm CSV; hãy kiểm lại."); return; } setPreview(p); setPreviewKey(JSON.stringify({plan,text,revision:revision.current})); } catch(e) {setError(e instanceof Error?e.message:"Không kiểm được CSV.");} finally {lock.current=false;setBusy(false);}
  };
  const applyImport = () => { if (!preview?.valid || !preview.candidate || stale || previewKey!==JSON.stringify({plan,text:csvText,revision:revision.current})) {setError("Preview đã cũ; hãy kiểm CSV lại.");return;} void transition(preview.candidate,"Đã nhập manifest; các bó chưa xếp."); };
  const doSave = async () => {
    if(stale || lock.current) {setError("Hãy áp dụng bản nháp trước khi lưu.");return;}
    lock.current=true;setBusy(true);setError(""); const snapshot=structuredClone(plan);
    try {await saveSnapshot(snapshot,saveName); setSaved(await listSnapshots()); setRebaseInfo(null); setNotice("Đã lưu ảnh chụp đã kiểm; thay đổi mới trong tab chưa tự lưu.");} catch(e) {setError(e instanceof Error?e.message:"Không lưu được.");} finally {lock.current=false;setBusy(false);}
  };
  const doOpen = async () => {
    if(stale || lock.current || !savedId) {setError("Chọn phương án và áp dụng bản nháp trước khi mở.");return;}
    const before=revision.current;lock.current=true;setBusy(true);setError("");
    try { const next=await openSnapshot(savedId); const p=await profileFor(next.plan, profile); if(before!==revision.current) {setError("Dữ liệu đổi trong lúc mở; phương án trước được giữ.");return;} setHistory(h=>[...h.slice(-19),structuredClone(plan)]);setProfile(p);setResult(next);changeDraft(draftFrom(next.plan));select(next.plan.units[0]?.id ?? "");setPreview(null);setRebaseInfo(null);setNotice("Đã mở và kiểm lại phương án đã lưu."); } catch(e) {setError(e instanceof Error?e.message:"Không mở được.");} finally {lock.current=false;setBusy(false);}
  };
  const refreshSaved = () => { listSnapshots().then(items=>setSaved(items)).catch(()=>setError("Không thể đọc danh sách phương án local.")); };
  // After a backup restore: reload the saved-plan list (the selection may point at a removed item) and the vessel list; the open draft stays.
  const afterRestore = () => { refreshSaved(); setSavedId(""); setReloadToken(t => t + 1); };
  const doRebase = async () => {
    const item=saved.find(v=>v.id===savedId);
    if(stale || lock.current || !savedId || item?.recheck_status!=="NEEDS_RECHECK") {setError("Chọn phương án cần kiểm lại và áp dụng bản nháp trước khi tạo bản theo dữ liệu mới.");return;}
    const before=revision.current;lock.current=true;setBusy(true);setError("");
    try {
      const [rebased,old]=await Promise.all([rebaseSnapshot(savedId),openSnapshot(savedId)]);
      const p=await profileFor(rebased.candidate.plan, profile);
      if(before!==revision.current) {setError("Dữ liệu đổi trong lúc tạo bản theo dữ liệu mới; phương án trước được giữ.");return;}
      setHistory(h=>[...h.slice(-19),structuredClone(plan)]);setProfile(p);setResult(rebased.candidate);changeDraft(draftFrom(rebased.candidate.plan));
      select(rebased.candidate.plan.units[0]?.id ?? "");setPreview(null);
      const name=item?.name ?? "";
      setSaveName(`${name} · theo ${rebased.target_revision_id.split("@")[1] ?? rebased.target_revision_id}`.slice(0,100));
      setRebaseInfo({name,result:rebased});
      setExternalBaseline({token:Date.now(),plan:structuredClone(old.plan),label:`Bản lưu cũ: ${name} · ${item ? savedTime(item.created_utc) : ""} · ID ${savedId} · ${rebased.source_revision_id}`,comparison:rebased.comparison});
      setNotice(`Đã tạo bản theo dữ liệu mới (${rebased.target_revision_id}) từ «${name}». Bản này chưa lưu; nhập tên và bấm Lưu phương án để lưu thành phương án mới.`);
    } catch(e) {setError(e instanceof Error?e.message:"Không tạo được bản theo dữ liệu mới.");} finally {lock.current=false;setBusy(false);}
  };
  const previewAutomatic = async () => {
    if (stale || lock.current) {setError("Hãy áp dụng bản nháp trước khi xếp thử.");return;}
    const before=revision.current; const algorithm=plannerAlgorithm; lock.current=true;setBusy(true);setError("");
    try { const candidate=await previewPlanner(plan, algorithm); if(before!==revision.current){setError("Dữ liệu đổi trong lúc xếp thử; hãy chạy lại.");return;} setPlanner(candidate);setPlannerKey(plannerKeyOf(plan, algorithm));setReasonFilter("ALL");setReasonPage(0); }
    catch(e){setError(e instanceof Error?e.message:"Không xếp thử được.");}finally{lock.current=false;setBusy(false);}
  };
  const applyAutomatic = async () => {
    if (!planner || stale || lock.current || plannerKey!==plannerKeyOf(plan, plannerAlgorithm)){setError("Xem trước đã cũ; hãy xếp thử lại.");return;}
    const before=revision.current;const reasons=planner.unplaced;lock.current=true;setBusy(true);setError("");
    try {const next=await requestEvaluation(planner.evaluation.plan);if(before!==revision.current){setError("Dữ liệu đổi trong lúc áp dụng; phương án trước được giữ.");return;}setHistory(h=>[...h.slice(-19),structuredClone(plan)]);setResult(next);changeDraft(draftFrom(next.plan));if(!next.plan.units.some(u=>u.id===selectedRef.current))select(next.plan.units[0]?.id ?? "");setAppliedReasons({planKey:JSON.stringify(next.plan),unplaced:reasons});setNotice("Đã áp dụng xếp thử; hãy kiểm tra phương án và các nội dung chưa kiểm.");requestAnimationFrame(()=>document.querySelector(".viewer-card")?.scrollIntoView({block:"start"}));}
    catch(e){setError(e instanceof Error?e.message:"Không áp dụng được xếp thử.");}finally{lock.current=false;setBusy(false);}
  };
  const plannerCurrent=planner && !stale && plannerKey===plannerKeyOf(plan, plannerAlgorithm) ? planner : null;
  const currentReasons=appliedReasons && !stale && appliedReasons.planKey===JSON.stringify(plan) ? appliedReasons.unplaced : null;
  const shownReasons=plannerCurrent?.unplaced ?? currentReasons;
  const filteredReasons=shownReasons?.filter(r=>reasonFilter==="ALL" || r.code===reasonFilter) ?? [];
  const reasonPages=Math.max(1,Math.ceil(filteredReasons.length/50)); const safeReasonPage=Math.min(reasonPage,reasonPages-1);
  const reasonMap=new Map((currentReasons ?? []).map(r=>[r.unit_id,r.message]));
  const pipeMode=isPipePlan(plan);
  const groupIds: string[]=plan.contract_version==="scst.pipe-list.v2" ? [...new Set(plan.units.map(u=>u.source_ref?.group_id).filter((g): g is string=>!!g))] : (pipeLibrary?.groups.map(g=>g.group_id) ?? []);
  const placementMap=new Map(plan.placements.map(p=>[p.unit_id,p]));
  const groupFiltered=pipeMode && groupFilter!=="ALL" ? plan.units.filter(u=>u.source_ref?.group_id===groupFilter) : plan.units;
  const filtered=pipeMode && packingFilter!=="ALL" ? groupFiltered.filter(u=>packingIndex && packingFor(packingIndex,u)?.status===packingFilter) : groupFiltered;
  const unitPacking=(u: (typeof plan.units)[number])=>packingIndex ? packingFor(packingIndex,u) : null;
  const pageCount=Math.max(1,Math.ceil(filtered.length/50));
  const safePage=Math.min(page,pageCount-1);
  const visibleUnits=pipeMode ? filtered.slice(safePage*50,(safePage+1)*50) : filtered;
  const pipeStats=(items: typeof plan.units)=>{let placed=0,pieces=0,mass=0,placedPieces=0,placedMass=0;for(const u of items){const n=u.source_ref?.pieces ?? 0;pieces+=n;mass+=u.mass_g;if(placementMap.has(u.id)){placed++;placedPieces+=n;placedMass+=u.mass_g;}}return {count:items.length,pieces,mass,placed,placedPieces,placedMass};};
  const allPipeStats=pipeMode?pipeStats(plan.units):null; const groupPipeStats=pipeMode?pipeStats(filtered):null;
  const cargoLabel = plan.cargo_source === "DOCUMENT_CALCULATED" ? "theo list nguồn" : plan.cargo_source === "USER_ENTERED" ? "tự nhập" : "giả lập";
  const holdLabel = plan.source === "MIXED_REFERENCE" ? "hầm tham chiếu" : plan.source === "USER_ENTERED" ? "hầm tự nhập" : "hầm giả lập";
  const contextLabel = plan.source === "SYNTHETIC" && !plan.cargo_source ? "SYNTHETIC" : `${holdLabel.toUpperCase()} · HÀNG ${cargoLabel.toUpperCase()}`;
  const selectedSaved=saved.find(v=>v.id===savedId);
  const recheckText=(v:SnapshotListItem)=>v.recheck_status==="NEEDS_RECHECK" ? `Cần kiểm lại: thêm ${v.added_count} · bỏ ${v.removed_count} · đổi ${v.changed_count} bó; ${v.placed_affected_count} bó đã đặt bị ảnh hưởng (có dữ liệu đổi) · ${v.placed_dropped_on_rebase_count} vị trí sẽ bỏ khi tạo bản mới (${v.cargo_revision_id ?? "?"})` : v.recheck_status==="CURRENT" ? `Theo dữ liệu mới nhất (${v.cargo_revision_id ?? "?"})` : v.recheck_status==="REVISION_UNAVAILABLE" ? "Không đọc được revision" : "Không dùng list ống";
  const submit = (e: FormEvent) => { e.preventDefault(); void run("draft"); };
  return <div className="app-shell"><div className="main-shell"><header className="topbar"><div className="brand"><strong>SCST</strong><span>Steel Cargo Stowage Tool</span></div><span>{contextLabel} · Local</span></header><main id="workspace">
    <div className="page-heading"><div><h1>Lập phương án chất xếp <span className="demo-badge">{contextLabel}</span></h1><p>Hầm mục tiêu trống · Dữ liệu chưa xác minh, không dùng cho phương án thực.</p></div><div className="heading-actions"><button className="button secondary" disabled={busy || !history.length} onClick={() => void run("undo")}>↶ Bản trước</button><button className="button dark" disabled={busy || stale} onClick={() => void run("demo")}>↻ Khôi phục mẫu</button></div></div>
    <div className="vessel-controls"><button className="button secondary" disabled={busy} onClick={newPlan}>Phương án mới</button><button className="button secondary" disabled={busy || (plan.contract_version === "scst.m2a.v1" && plan.source === "USER_ENTERED")} onClick={detach}>Dùng hầm tự nhập</button><button className="button secondary" disabled={busy || (plan.source === "MIXED_REFERENCE" && vessel?.vessel_id === "VINAFCO268")} onClick={() => void switchVessel("VINAFCO268", 1, "VR-SII")}>Xem VINAFCO 268</button>{plan.source === "MIXED_REFERENCE" && vessel && <label>Cấp tham chiếu <select aria-label="Cấp tham chiếu" value={vessel.case_id} disabled={busy} onChange={e => void switchVessel(vessel.vessel_id, vessel.profile_version ?? 1, e.target.value)}>{caseOptions.map(id => <option key={id} value={id}>{id}</option>)}</select></label>}</div>
    {notice && <p role="status">{notice}</p>}
    <VesselProfilePanel busy={busy} current={current} onOpen={(id, version, caseId) => void switchVessel(id, version, caseId)} reloadToken={reloadToken} />
    {body && vessel?.vessel_id !== "VINAFCO268" && profile && <ProfileSummary detail={profile} caseId={vessel?.case_id ?? ""} />}
    {body && vessel?.vessel_id === "VINAFCO268" && <section className="scope-note" aria-label="Thông số VINAFCO 268"><strong>VINAFCO 268 · HN-2642 — thân theo hồ sơ, hầm ước tính, hàng {cargoLabel}</strong><p>Thân {formatMetres(body.dimensions_m.length*1000)} × {formatMetres(body.dimensions_m.beam*1000)} × {formatMetres(body.dimensions_m.depth*1000)} m. Hầm ước tính khoảng 56,41 × 10,34 × 5,41 m; kích thước chưa đo thực.</p><p>{(() => { const c=body.cases.find(c => c.id === vessel?.case_id)!; return `Mức hàng tham chiếu ${tonnes(c.cargo_mass_g)} tấn · TTTP ${fmt(c.deadweight_t ?? 0)} tấn · mớn ${fmt(c.draft_m)} m · mạn khô hồ sơ khoảng ${formatMetres(c.freeboard_mm ?? 0)} m`; })()}</p><p>{body.notes[0]} {body.notes[1]} Mạn khô hồ sơ và khoảng cách hình học có chênh lệch nhỏ, chưa đủ dữ liệu giải thích.</p><p>Khối lượng tàu không và tải sàn cho phép: chưa có dữ liệu. Không xác nhận an toàn hoặc điều kiện vận hành.</p></section>}
    <section className="editor-card m2a-card" aria-label="Thư viện list ống"><h2>List ống Baltimore</h2><p>Nguồn chưa gán phương tiện. Khối lượng mỗi bó tính K × L, chưa cân; kích thước khối bao chưa đo.</p><p>31 nhóm · 1.076 bó · 21.226 ống. Tổng tính 1.125,55 t; tổng nguồn làm tròn 1.125,52 t; chênh lệch 31,03 kg. CBM nguồn 1.130,97 m³; khối bao tính lại 1.157,54 m³; chênh lệch 26,57 m³.</p><p>16 bó ở dòng 22, 31, 32 có kích thước khối bao cần xác minh; không khẳng định an toàn hoặc vừa hầm.</p><button className="button secondary" disabled={busy} onClick={()=>void checkPipeList()}>Xem trước list ống</button>{pipeCandidate && <div role="status">Xem trước: {pipeCandidate.plan.units.length} bó chưa xếp; nạp sẽ thay danh sách và xóa vị trí hiện tại. <button className="button secondary" disabled={busy} onClick={applyPipeList}>Nạp list vào phương án hiện tại</button></div>}{pipeLibrary && <details><summary>31 nhóm nguồn và cảnh báo</summary><ul>{pipeLibrary.groups.map(g=><li key={g.group_id}>{g.group_id} · {g.bundle_count} bó × {g.pieces_per_bundle} ống · {g.issue_codes.length ? `Cần đối chiếu: ${g.issue_codes.map(code=>sourceWarnings[code] ?? "Dữ liệu nguồn cần đối chiếu").join("; ")}` : "Không có cảnh báo nguồn"}</li>)}</ul></details>}</section>
    <CargoRevisionPanel key={`revisions-${reloadToken}`} plan={plan} onCreated={refreshSaved} focusGroup={focusGroup} />
    <p>Bản nháp chỉ giữ trong tab; lưu ảnh chụp đã kiểm để mở lại sau khi tải lại hoặc khởi động lại.</p>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {stale && <div className="error-banner" role="status">STALE · Bản nháp chưa được kiểm; kết quả đang thấy thuộc bản đã kiểm trước đó.</div>}
    <section className="editor-card m2a-card" aria-label="Xếp thử tự động"><h2>Xếp thử tự động</h2><p>Hàng được đặt thử một lớp trên khối bao; không khẳng định tối ưu hay đủ điều kiện vận hành. Xếp thử sẽ thay các vị trí cũ khi áp dụng. Nhiều tầng: chồng cột cùng kích thước có kiểm đỡ; chưa kiểm tải chồng, tải sàn, chằng buộc và ổn định.</p><p>Khối lượng còn được xếp theo chuyến hiện tại: {tonnes(plan.limits.voyage_cargo_limit_g - (plan.limits.cargo_onboard_g ?? 0))} tấn. Chỉnh Giới hạn chuyến nếu cần; xếp thử không tự tăng giới hạn.</p><label>Cách xếp thử<select aria-label="Cách xếp thử" value={plannerAlgorithm} disabled={busy} onChange={e=>{setPlannerChoice(e.target.value as PlannerAlgorithm);setPlanner(null);setReasonPage(0);}}><option value="guillotine-single-layer-v1">Một tầng (như cũ)</option><option value="columns-v1">Nhiều tầng theo cột (thử nghiệm)</option></select></label><button className="button primary" disabled={busy} onClick={()=>void previewAutomatic()}>Xếp thử tự động</button>{plannerCurrent && <div data-testid="planner-preview"><p>Xem trước: {plannerCurrent.evaluation.summary.placed_count} bó · {tonnes(plannerCurrent.evaluation.summary.placed_mass_g)} tấn; còn sức chở {tonnes(plannerCurrent.evaluation.summary.remaining_capacity_g)} tấn · {plannerCurrent.unplaced.length} bó chưa đặt hoặc loại trừ. Phương án hiện tại chưa đổi.</p>{plannerCurrent.algorithm === "columns-v1" && (() => { const s = stackSummary(plannerCurrent); return <p data-testid="planner-stack-summary">Nhiều tầng: {s.columns} cột · tối đa {s.maxLayers} tầng · đã xếp {s.placed} bó · chưa xếp {s.unplaced} bó</p>; })()}<button className="button secondary" disabled={busy} onClick={()=>void applyAutomatic()}>Áp dụng xếp thử</button></div>}{shownReasons ? <div data-testid="planner-reasons"><p>{plannerCurrent ? "Lý do theo xem trước" : "Lý do của lần xếp thử đã áp dụng"}. Lý do chỉ giữ trong tab; chạy lại xếp thử sau khi mở hoặc chỉnh phương án.</p><label>Lọc lý do<select aria-label="Lọc lý do" value={reasonFilter} onChange={e=>{setReasonFilter(e.target.value);setReasonPage(0);}}><option value="ALL">Tất cả</option><option value="EXCLUDED">Loại trừ</option><option value="TOO_HIGH">Vượt chiều cao</option><option value="FOOTPRINT_TOO_LARGE">Khối bao quá lớn</option><option value="MASS_LIMIT">Giới hạn khối lượng</option><option value="HEURISTIC_NO_SPACE">Chưa tìm được chỗ</option><option value="STACK_HEIGHT">Hết chiều cao cột</option></select></label><ul>{filteredReasons.slice(safeReasonPage*50,(safeReasonPage+1)*50).map(r=><li key={r.unit_id}><strong>{r.unit_id}</strong> · {r.message}</li>)}</ul><button className="button secondary" disabled={safeReasonPage===0} onClick={()=>setReasonPage(p=>Math.max(0,p-1))}>Lý do trước</button><span data-testid="planner-page"> Trang {safeReasonPage+1}/{reasonPages} · tối đa 50 bó </span><button className="button secondary" disabled={safeReasonPage>=reasonPages-1} onClick={()=>setReasonPage(p=>p+1)}>Lý do sau</button></div> : <p>Chạy xếp thử để xem lý do bó chưa đặt; lý do không được lưu cùng phương án.</p>}</section>
    <p>Khối lượng hiển thị làm tròn tối đa hai chữ số thập phân tấn; tính toán và lưu giữ độ chính xác gốc.</p>
    <div className="stats-row"><section className="stat"><span className="stat-label">KHỐI LƯỢNG MANIFEST</span><strong data-testid="manifest-mass">{tonnes(result.summary.manifest_mass_g)} tấn</strong></section><section className="stat"><span className="stat-label">ĐÃ XẾP / ĐƯỢC XẾP THÊM</span><strong data-testid="placed-mass">{tonnes(result.summary.placed_mass_g)} / {tonnes(plan.limits.voyage_cargo_limit_g - (plan.limits.cargo_onboard_g ?? 0))} tấn</strong></section><section className="stat"><span className="stat-label">TRẠNG THÁI</span><strong data-testid="status">{stale ? "STALE" : result.status}</strong><small>{result.summary.placed_count} đã xếp · {plan.units.length - result.summary.placed_count} chưa xếp</small></section></div>
    <ComparisonPanel plan={plan} stale={stale} busy={busy} lock={lock} revision={revision} setBusy={setBusy} saved={saved} select={select} restore={transition} external={externalBaseline} />
    <div className="workspace-grid"><Viewer plan={plan} profile={profile} selected={selected} onSelect={select} issueIds={issues} packing={packingIndex} /><section className="editor-card" aria-label="Chỉnh bó hàng"><div className="panel-heading"><div><span className="eyebrow">ĐANG CHỌN</span><h2>{unit?.id ?? "Chưa chọn bó"}</h2>{unit && <p>{unit.name} · {dimensions(unit).map(formatCm).join(" × ")} cm{unit.source_ref?.dimension_warning ? " · Kích thước cần xác minh" : ""}</p>}{unit && pipeMode && <PackingInfo packing={unitPacking(unit)} groupId={unit.source_ref?.group_id ?? null} error={packingError} onOpenGroup={openGroup} />}</div></div><form onSubmit={submit}><p>Số hiển thị làm tròn đến kg/cm; chỉ trường bạn sửa mới được cập nhật.</p>
      {unit && ud && <>{pipeMode && <><p>Dữ liệu nguồn cố định · khối lượng tính, chưa cân; kích thước và khối lượng hiển thị xấp xỉ.</p><label>Yêu cầu<select aria-label="Yêu cầu" value={ud.requirement} onChange={e=>editUnit("requirement",e.target.value)}><option value="required">Bắt buộc</option><option value="optional">Tùy chọn</option><option value="excluded">Loại trừ</option></select></label></>}{plan.contract_version === "scst.m2a.v1" && <><label>ID bó<input aria-label="ID bó" value={ud.id} onChange={e=>editUnit("id",e.target.value)} /></label><label>Tên bó<input aria-label="Tên bó" value={ud.name} onChange={e=>editUnit("name",e.target.value)} /></label><label>Loại bó<select aria-label="Loại bó" value={ud.kind} onChange={e=>editUnit("kind",e.target.value)}><option value="BAR_BUNDLE">Bó thép thanh</option><option value="PIPE_BUNDLE">Bó thép ống</option></select></label><label>Yêu cầu<select aria-label="Yêu cầu" value={ud.requirement} onChange={e=>editUnit("requirement",e.target.value)}><option value="required">Bắt buộc</option><option value="optional">Tùy chọn</option><option value="excluded">Loại trừ</option></select></label>{(["length","width","height"] as const).map(k=><label key={k}>{({length:"Dài",width:"Rộng",height:"Cao"})[k]} (cm)<input aria-label={`Kích thước ${k} (cm)`} inputMode="decimal" value={ud[k]} onChange={e=>editUnit(k,e.target.value)} /></label>)}</>}
      <label>Khối lượng bó (kg)<input aria-label="Khối lượng bó (kg)" readOnly={pipeMode} value={ud.mass} onChange={(e) => editUnit("mass",e.target.value)} /></label>
      {placement && <><label>Tọa độ X (cm)<input aria-label="Tọa độ X (cm)" inputMode="decimal" value={ud.x} onChange={(e) => editUnit("x",e.target.value)} /></label><label>Tọa độ Y (cm)<input aria-label="Tọa độ Y (cm)" inputMode="decimal" value={ud.y} onChange={(e) => editUnit("y",e.target.value)} /></label><label>Góc xoay<select aria-label="Góc xoay" value={ud.yaw} onChange={(e) => editUnit("yaw",e.target.value)}>{[0,90,180,270].map(v => <option key={v} value={v}>{v}°</option>)}</select></label></>}
      {placement && <p data-testid="unit-stack-detail">Tầng {placement.layer + 1} · Z {formatCm(placement.z_mm ?? 0)} cm · Bó đỡ: {(placement.supported_by ?? []).join(", ") || "đáy hầm"}</p>}
      {plan.contract_version !== "scst.m1.v1" && <div><button type="button" className="button secondary" disabled={busy || (!placement && unit.requirement === "excluded")} onClick={()=>changePlacement(!placement)}>{placement ? "Bỏ vị trí" : "Đặt bó"}</button>{!pipeMode && <button type="button" className="button secondary" disabled={busy} onClick={deleteUnit}>Xóa bó</button>}</div>}</>}
      {plan.contract_version !== "scst.m1.v1" && plan.source === "USER_ENTERED" && <><p>Hầm tự nhập · chưa xác minh.</p><label>Tên hầm<input aria-label="Tên hầm" value={draft.holdName} onChange={e=>editHold("holdName",e.target.value)}/></label>{(["holdLength","holdWidth","holdHeight"] as const).map(k=><label key={k}>{({holdLength:"Chiều dài hầm",holdWidth:"Chiều rộng hầm",holdHeight:"Chiều cao hầm"})[k]} (cm)<input aria-label={`Hầm ${k} (cm)`} inputMode="decimal" value={draft[k]} onChange={e=>editHold(k,e.target.value)}/></label>)}</>}
      <label>{plan.source === "MIXED_REFERENCE" ? "Mức hàng tham chiếu (kg)" : "Giới hạn chứng nhận (kg)"}<input aria-label="Giới hạn chứng nhận (kg)" readOnly={plan.source === "MIXED_REFERENCE"} value={draft.certificate} onChange={(e) => editLimit("certificate",e.target.value)} /></label>
      <label>Giới hạn chuyến (kg)<input aria-label="Giới hạn chuyến (kg)" value={draft.voyage} onChange={(e) => editLimit("voyage",e.target.value)} /></label>
      <label>Hàng đã có trên tàu (kg)<input aria-label="Hàng đã có trên tàu (kg)" value={draft.onboard} onChange={(e) => editLimit("onboard",e.target.value)} /></label>
      <button className="button primary apply-button" disabled={busy} type="submit">{busy ? "Đang kiểm…" : "Áp dụng & kiểm lại"}</button>
    </form></section></div>
    {!pipeMode && <section className="editor-card m2a-card"><h2>Thêm bó hàng</h2><p>Mỗi dòng là một bó; dữ liệu nhập chưa xác minh.</p>{(["id","name","length","width","height","mass"] as const).map(k=><label key={k}>{({id:"ID bó mới",name:"Tên bó mới",length:"Chiều dài bó mới (cm)",width:"Chiều rộng bó mới (cm)",height:"Chiều cao bó mới (cm)",mass:"Khối lượng bó mới (kg)"})[k]}<input aria-label={`Bó mới ${k}`} value={newUnit[k]} onChange={e=>{revision.current++;setNewUnit({...newUnit,[k]:e.target.value});}} /></label>)}<label>Loại bó mới<select aria-label="Loại bó mới" value={newUnit.kind} onChange={e=>{revision.current++;setNewUnit({...newUnit,kind:e.target.value});}}><option value="BAR_BUNDLE">Bó thép thanh</option><option value="PIPE_BUNDLE">Bó thép ống</option></select></label><label>Yêu cầu bó mới<select aria-label="Yêu cầu bó mới" value={newUnit.requirement} onChange={e=>{revision.current++;setNewUnit({...newUnit,requirement:e.target.value});}}><option value="required">Bắt buộc</option><option value="optional">Tùy chọn</option><option value="excluded">Loại trừ</option></select></label><button className="button secondary" disabled={busy} onClick={addUnit}>Thêm bó</button></section>}
    <section className="editor-card m2a-card"><h2>Nhập CSV UTF-8</h2><p>Định dạng trao đổi CSV dùng riêng mm và kg như header; mỗi dòng một bó, kg dùng dấu chấm tối đa 3 số lẻ. Ví dụ giả lập UTF-8:</p><pre>{"id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg\nB-001,Bo thep mau,BAR_BUNDLE,required,6000,900,650,2500.001"}</pre><textarea aria-label="Nội dung CSV" value={csvText} onChange={e=>{revision.current++;setCsvText(e.target.value);setPreview(null);}} /><label>Chọn tệp CSV<input type="file" accept=".csv,text/csv" aria-label="Chọn tệp CSV" onChange={async e=>{const file=e.target.files?.[0];if(!file)return;const before=++revision.current;try {if(file.size>1048576)throw new Error("Tệp vượt 1 MiB.");const bytes=await file.arrayBuffer();const text=new TextDecoder("utf-8",{fatal:true}).decode(bytes);if(before!==revision.current){setError("Dữ liệu đã đổi trong lúc đọc tệp; hãy chọn lại.");return;}setCsvText(text);setPreview(null);} catch {setError("Tệp phải là CSV UTF-8 tối đa 1 MiB.");}}}/></label><button className="button secondary" disabled={busy} onClick={()=>void previewImport()}>Kiểm CSV</button><button className="button secondary" disabled={busy || !preview?.valid} onClick={applyImport}>Áp dụng CSV</button>{preview && <div role="status">{preview.valid ? `Xem trước: ${preview.count} bó · ${tonnes(preview.total_mass_g)} tấn; áp dụng sẽ bỏ vị trí cũ.` : <ul>{preview.errors.map((e,i)=><li key={i}>Dòng {e.row} · {e.field}: {e.message}</li>)}</ul>}</div>}</section>
    <section className="editor-card m2a-card"><h2>Lưu và mở local</h2><p>Mỗi lần lưu tạo một ảnh chụp mới; danh sách hiển thị 100 bản gần nhất.</p><label>Tên phương án lưu<input aria-label="Tên phương án lưu" maxLength={100} value={saveName} onChange={e=>{revision.current++;setSaveName(e.target.value);}}/></label><button className="button secondary" disabled={busy} onClick={()=>void doSave()}>Lưu phương án</button><label>Phương án đã lưu<select aria-label="Phương án đã lưu" value={savedId} onChange={e=>{revision.current++;setSavedId(e.target.value);}}><option value="">Chọn phương án</option>{saved.map(v=><option key={v.id} value={v.id}>{v.name} · {savedTime(v.created_utc)}</option>)}</select></label><button className="button secondary" disabled={busy || !savedId} onClick={()=>void doOpen()}>Mở phương án</button>{savedId && <a className="button secondary" href={`#/report/${savedId}`} target="_blank" rel="noopener" aria-disabled={!savedId} onClick={e=>{ if(!savedId) e.preventDefault(); }}>Xuất báo cáo</a>}<button className="button secondary" disabled={busy || stale || selectedSaved?.recheck_status!=="NEEDS_RECHECK"} onClick={()=>void doRebase()}>Tạo bản theo dữ liệu mới</button>
      {selectedSaved && <p data-testid="saved-recheck">{recheckText(selectedSaved)}</p>}
      {saved.length>0 && <ul className="saved-status" data-testid="saved-list" aria-label="Trạng thái dữ liệu hàng của các bản đã lưu">{saved.map(v=><li key={v.id} data-testid={`saved-item-${v.id}`} aria-current={v.id===savedId}><strong>{v.name}</strong> · {savedTime(v.created_utc)}{v.recheck_status!=="NOT_APPLICABLE" && <> · <span className={`recheck recheck-${v.recheck_status.toLowerCase()}`}>{recheckText(v)}</span></>}</li>)}</ul>}
      {rebaseInfo && <div data-testid="rebase-dropped" className="rebase-dropped"><strong>Bản theo dữ liệu mới từ «{rebaseInfo.name}»</strong> · {rebaseInfo.result.source_revision_id} → {rebaseInfo.result.target_revision_id}<br/>Giữ {rebaseInfo.result.kept_placement_count} vị trí; bỏ {rebaseInfo.result.dropped_placements.length} vị trí. Bó thêm {rebaseInfo.result.added_unit_ids.length}, bỏ {rebaseInfo.result.removed_unit_ids.length}, đổi {rebaseInfo.result.changed_unit_ids.length}.<RebaseDropped result={rebaseInfo.result} name={rebaseInfo.name}/></div>}</section>
    <BackupPanel busy={busy} lock={lock} setBusy={setBusy} onRestored={afterRestore} />
    <div className="workspace-grid"><section id="cargo" className="editor-card"><h2>Danh sách hàng</h2>{pipeMode && allPipeStats && groupPipeStats && <div className="m2a-card"><label>Nhóm nguồn<select aria-label="Nhóm nguồn" value={groupFilter} onChange={e=>{setGroupFilter(e.target.value);setPage(0);}}><option value="ALL">Tất cả {groupIds.length || 31} nhóm</option>{groupIds.map(id=><option key={id} value={id}>{id}</option>)}</select></label><label>Trạng thái cách xếp<select aria-label="Lọc trạng thái cách xếp" value={packingFilter} onChange={e=>{setPackingFilter(e.target.value as PackingFilter);setPage(0);}}>{packingFilterOptions.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select></label>{packingData && <p data-testid="packing-stats">Cách xếp dẫn xuất ({packingData.revision_id}): {packingData.stats.groups_by_status.DETAILED} nhóm · {packingData.stats.bundles_by_status.DETAILED} bó chi tiết; {packingData.stats.groups_by_status.ENVELOPE_ONLY} nhóm · {packingData.stats.bundles_by_status.ENVELOPE_ONLY} bó chỉ khối bao; ống dẫn xuất {packingData.stats.derived_pieces} / ống nguồn {packingData.stats.source_pieces}. Không phải số đo thực.</p>}{packingError && <p role="status">{packingError}</p>}<p data-testid="pipe-total">Toàn list: {allPipeStats.count} bó · {allPipeStats.pieces} ống · {tonnes(allPipeStats.mass)} tấn; đã xếp {allPipeStats.placed} bó · {allPipeStats.placedPieces} ống · {tonnes(allPipeStats.placedMass)} tấn; còn lại (gồm bó loại trừ) {allPipeStats.count-allPipeStats.placed} bó · {allPipeStats.pieces-allPipeStats.placedPieces} ống · {tonnes(allPipeStats.mass-allPipeStats.placedMass)} tấn.</p><p data-testid="pipe-group">Nhóm đang xem: {groupPipeStats.count} bó · {groupPipeStats.pieces} ống · {tonnes(groupPipeStats.mass)} tấn; đã xếp {groupPipeStats.placed} bó · {groupPipeStats.placedPieces} ống · {tonnes(groupPipeStats.placedMass)} tấn; còn lại (gồm bó loại trừ) {groupPipeStats.count-groupPipeStats.placed} bó · {groupPipeStats.pieces-groupPipeStats.placedPieces} ống · {tonnes(groupPipeStats.mass-groupPipeStats.placedMass)} tấn.</p><button className="button secondary" disabled={safePage===0} onClick={()=>setPage(p=>Math.max(0,p-1))}>Trang trước</button> <span data-testid="pipe-page">Trang {safePage+1}/{pageCount} · tối đa 50 bó</span> <button className="button secondary" disabled={safePage>=pageCount-1} onClick={()=>setPage(p=>p+1)}>Trang sau</button></div>}<div className="table-wrap"><table><thead><tr><th>ID</th><th>Loại / yêu cầu</th><th>Kích thước (cm)</th><th>Khối lượng</th><th>Vị trí / lý do</th>{pipeMode && <th>Cách xếp (dẫn xuất)</th>}<th>Tầng</th></tr></thead><tbody>{visibleUnits.map((u) => {const p=placementMap.get(u.id); return <tr key={u.id} data-testid={`unit-${u.id}`} aria-selected={selected===u.id} onClick={()=>select(u.id)}><td><button className="text-button" onClick={()=>select(u.id)}>{u.id}</button></td><td>{u.kind === "BAR_BUNDLE" ? "Bó thép thanh" : "Bó thép ống"} · {u.requirement === "required" ? "Bắt buộc" : u.requirement === "optional" ? "Tùy chọn" : "Loại trừ"}</td><td>{dimensions(u).map(formatCm).join(" × ")}</td><td>{massLabel(u.mass_g)}</td><td>{p ? `${formatCm(p.x_mm)}, ${formatCm(p.y_mm)}, ${formatCm(p.z_mm ?? 0)} cm · ${p.yaw_deg}°` : reasonMap.get(u.id) ?? (u.requirement === "excluded" ? "Đã loại trừ" : u.requirement === "optional" ? "Tùy chọn chưa xếp" : "Bắt buộc chưa xếp")}</td>{pipeMode && (()=>{const pk=unitPacking(u); return <td data-testid={`packing-cell-${u.id}`} className={pk?.status==="ENVELOPE_ONLY" ? "packing-warn" : undefined}>{packingCell(pk)}{pk && pk.slack_um ? ` · dư ${slackText(pk)}` : ""}{pk && pk.reasons.length ? <> · <a href="#cargo-data" className="text-button" aria-label={`Lý do cách xếp ${u.id}: mở nhóm trong Dữ liệu hàng`} onClick={e=>{e.preventDefault();e.stopPropagation();select(u.id);openGroup(u.source_ref?.group_id ?? "");}}>{pk.reasons.map(r=>r.code).join(", ")}</a></> : null}</td>;})()}<td data-testid={`layer-cell-${u.id}`}>{p ? String(p.layer + 1) : "—"}</td></tr>})}</tbody></table></div></section><section id="checks" className="editor-card"><h2>Kết quả kiểm</h2><p>{plan.source === "MIXED_REFERENCE" ? "Mức hàng tham chiếu" : "Chứng nhận"}: {tonnes(plan.limits.certificate_cargo_limit_g)} tấn · Chuyến: {tonnes(plan.limits.voyage_cargo_limit_g)} tấn · Đã có ngoài hầm: {tonnes(plan.limits.cargo_onboard_g ?? 0)} tấn</p><p>Được xếp thêm: {tonnes(plan.limits.voyage_cargo_limit_g - (plan.limits.cargo_onboard_g ?? 0))} tấn</p>{result.issues_truncated && <p role="status">Chỉ hiển thị {result.issues.length} trong tổng {result.total_issues} lỗi; các bó bị ảnh hưởng vẫn được đánh dấu.</p>}{result.issues.length ? <ul>{result.issues.map((i,n)=><li key={n}><strong>{i.code}</strong> {i.code === "OVERWEIGHT" ? `Vượt giới hạn hàng khoảng ${formatKg(Math.max(0,-result.summary.remaining_capacity_g))} kg.` : i.message}</li>)}</ul> : <p>Không phát hiện lỗi trong các kiểm M1.</p>}<div className="scope-note"><strong>CHƯA KIỂM</strong><p>{result.unchecked.join(" · ")}</p></div><p>Chưa đủ điều kiện vận hành.</p></section></div>
  </main></div></div>;
}
