import { useEffect, useState } from "react";
import { comparePlans, openSnapshot, type CompareResult, type SavedSummary } from "../api/client";
import { fmt, formatKg, formatCm, tonnes, type Plan } from "./model";

type Props = {
  plan: Plan; stale: boolean; busy: boolean; lock: {current:boolean}; revision: {current:number};
  setBusy: (value:boolean)=>void; saved: SavedSummary[]; select: (id:string)=>void;
  restore: (plan:Plan,label:string)=>Promise<void>;
  // Externally supplied baseline A and comparison (rebase candidate vs. the old saved plan); applied once per token.
  external?: {token:number; plan:Plan; label:string; comparison:CompareResult} | null;
};
type Baseline = {plan:Plan; label:string};
type Change = CompareResult["rows"][number]["changes"][number];

const labels: Record<string,string> = {
  contract_version:"Phiên bản phương án",source:"Nguồn hầm",cargo_source:"Nguồn hàng",cargo_dataset:"Bộ dữ liệu hàng",
  'vessel.vessel_id':"Phương tiện",'vessel.case_id':"Cấp tham chiếu",'hold.id':"ID hầm",'hold.name':"Tên hầm",'hold.shape':"Hình dạng hầm",
  'hold.length_mm':"Chiều dài hầm (cm)",'hold.width_mm':"Chiều rộng hầm (cm)",'hold.height_mm':"Chiều cao hầm (cm)",
  'limits.certificate_cargo_limit_g':"Mức chứng nhận/tham chiếu (kg)",'limits.voyage_cargo_limit_g':"Giới hạn chuyến (kg)",'limits.cargo_onboard_g':"Hàng đã có ngoài hầm (kg)",
  name:"Tên bó",kind:"Loại bó",requirement:"Yêu cầu",length_mm:"Chiều dài tương thích (cm)",width_mm:"Chiều rộng tương thích (cm)",height_mm:"Chiều cao tương thích (cm)",mass_g:"Khối lượng (kg)",dimensions_um:"Kích thước nguồn dài × rộng × cao (cm)",
  'placement.x_mm':"Vị trí X (cm)",'placement.y_mm':"Vị trí Y (cm)",'placement.z_mm':"Vị trí Z (cm)",'placement.yaw_deg':"Góc xoay (độ)",'placement.layer':"Tầng",'placement.supported_by':"Bó đỡ",
  'source_ref.dataset_id':"Bộ dữ liệu nguồn",'source_ref.workbook_sha256':"Mã SHA-256 nguồn",'source_ref.sheet':"Sheet nguồn",'source_ref.group_id':"Nhóm nguồn",'source_ref.source_row':"Dòng nguồn",'source_ref.bundle_index':"Thứ tự bó",'source_ref.pieces':"Số ống/bó",'source_ref.dimension_warning':"Cảnh báo kích thước",
};
const statusLabel: Record<string,string> = {ADDED:"Thêm",REMOVED:"Đã bỏ",CHANGED:"Thay đổi",UNCHANGED:"Không đổi"};
const valueLabels: Record<string,string> = {BAR_BUNDLE:"Bó thép thanh",PIPE_BUNDLE:"Bó thép ống",required:"Bắt buộc",optional:"Tùy chọn",excluded:"Loại trừ",SYNTHETIC:"Giả lập",USER_ENTERED:"Tự nhập",MIXED_REFERENCE:"Tham chiếu phương tiện",DOCUMENT_CALCULATED:"Tính theo chứng từ"};
function valueText(value: unknown, field = ""): string {
  if(value === null || value === undefined) return "—";
  if(Array.isArray(value)) return value.length ? value.map(v=>valueText(v,field)).join(field === "dimensions_um" ? " × " : ", ") : "Không có";
  if(typeof value === "boolean") return value ? "Có" : "Không";
  if(typeof value === "number") {
    if(field.endsWith("_g")) return formatKg(value);
    if(field.endsWith("_mm")) return formatCm(value);
    if(field === "dimensions_um") return formatCm(value/1000);
  }
  return typeof value === "string" ? valueLabels[value] ?? value : String(value);
}
function smallDifference(change: Change): string | null {
  const threshold=change.field.endsWith("_g") ? 1000 : change.field.endsWith("_mm") ? 10 : change.field === "dimensions_um" ? 10000 : 0;
  if(!threshold || change.before == null || change.after == null) return null;
  const before=Array.isArray(change.before)?change.before:[change.before];
  const after=Array.isArray(change.after)?change.after:[change.after];
  const tiny=before.some((a,i)=>typeof a === "number" && typeof after[i] === "number" && Math.abs(after[i]-a)>0 && Math.abs(after[i]-a)<threshold);
  return tiny ? `Chênh lệch dưới 1 ${change.field.endsWith("_g") ? "kg" : "cm"}; số hiển thị đã làm tròn.` : null;
}
function displayTime(value:string):string {
  const d=new Date(value);if(!Number.isFinite(d.getTime()))return "Thời gian không hợp lệ";
  const p=new Intl.DateTimeFormat("vi-VN",{day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit",hourCycle:"h23"}).formatToParts(d);
  const get=(name:string)=>p.find(x=>x.type===name)?.value ?? "";
  return `${get("day")}-${get("month")}-${get("year")} ${get("hour")}:${get("minute")}`;
}
function Detail({changes}:{changes:Change[]}) {
  return <dl>{changes.map(c=><div key={c.field}><dt>{labels[c.field] ?? c.field}</dt><dd>Gốc A: {valueText(c.before,c.field)} → Hiện tại B: {valueText(c.after,c.field)}{smallDifference(c) && <span> · {smallDifference(c)}</span>}</dd></div>)}</dl>;
}

export default function ComparisonPanel({plan,stale,busy,lock,revision,setBusy,saved,select,restore,external}:Props) {
  const [baseline,setBaseline]=useState<Baseline|null>(null);
  const [savedId,setSavedId]=useState("");
  const [comparison,setComparison]=useState<CompareResult|null>(null);
  const [comparisonKey,setComparisonKey]=useState("");
  const [status,setStatus]=useState("CHANGES");
  const [query,setQuery]=useState("");
  const [page,setPage]=useState(0);
  const [error,setError]=useState("");
  const key=(a:Plan,b:Plan)=>JSON.stringify({a,b,revision:revision.current});
  const ready=comparison && baseline && !stale && comparisonKey===key(baseline.plan,plan) ? comparison : null;
  useEffect(()=>{
    if(!external)return;
    setBaseline({plan:structuredClone(external.plan),label:external.label});setComparison(external.comparison);setComparisonKey(key(external.plan,plan));
    setStatus("CHANGES");setQuery("");setPage(0);setError("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  },[external?.token]);
  const rows=ready?.rows.filter(r=>(status==="ALL" || (status==="CHANGES" ? r.status!=="UNCHANGED" : r.status===status)) && r.unit_id.toLowerCase().includes(query.toLowerCase())) ?? [];
  const pages=Math.max(1,Math.ceil(rows.length/50));const safePage=Math.min(page,pages-1);
  const pin=()=>{if(stale||lock.current){setError("Hãy áp dụng bản nháp trước khi giữ bản gốc.");return;}setBaseline({plan:structuredClone(plan),label:"Bản hiện tại trong tab (chưa tự lưu)"});setComparison(null);setError("");};
  const load=async()=>{
    if(stale||lock.current||!savedId){setError("Chọn bản lưu và áp dụng bản nháp trước khi đổi bản gốc.");return;}
    const before=revision.current;lock.current=true;setBusy(true);setError("");
    try {const candidate=await openSnapshot(savedId);if(before!==revision.current){setError("Dữ liệu đã đổi trong lúc tải bản gốc; giữ bản trước.");return;}const item=saved.find(x=>x.id===savedId);setBaseline({plan:structuredClone(candidate.plan),label:`Bản lưu: ${item?.name ?? ""} · ${item ? displayTime(item.created_utc) : ""} · ID ${savedId}`});setComparison(null);}
    catch(e){setError(e instanceof Error?e.message:"Không tải được bản gốc.");}finally{lock.current=false;setBusy(false);}
  };
  const run=async()=>{
    if(stale||lock.current||!baseline){setError("Chọn bản gốc và áp dụng bản nháp trước khi so sánh.");return;}
    const before=revision.current;lock.current=true;setBusy(true);setError("");
    try {const result=await comparePlans(baseline.plan,plan);if(before!==revision.current){setError("Dữ liệu đã đổi trong lúc so sánh; hãy chạy lại.");return;}setComparison(result);setComparisonKey(key(baseline.plan,plan));setStatus("CHANGES");setQuery("");setPage(0);}
    catch(e){setError(e instanceof Error?e.message:"Không so sánh được.");}finally{lock.current=false;setBusy(false);}
  };
  const selectRow=(id:string)=>{select(id);if(baseline && ready)setComparisonKey(key(baseline.plan,plan));};
  return <section className="editor-card m2a-card comparison-panel" aria-label="So sánh phương án">
    <h2>Giữ gốc và so sánh phương án</h2><p>Bản gốc A được giữ trong tab; phương án hiện tại B vẫn ở màn hình chính. So sánh chỉ đối chiếu dữ liệu và các kiểm hiện có, chưa xác nhận điều kiện vận hành.</p>
    <button className="button secondary" disabled={busy} onClick={pin}>Giữ bản hiện tại làm gốc</button>
    <label>Bản lưu làm gốc<select aria-label="Bản lưu làm gốc" value={savedId} onChange={e=>{revision.current++;setSavedId(e.target.value);}}><option value="">Chọn bản lưu</option>{saved.map(s=><option key={s.id} value={s.id}>{s.name} · {displayTime(s.created_utc)}</option>)}</select></label>
    <button className="button secondary" disabled={busy||!savedId} onClick={()=>void load()}>Dùng bản lưu làm gốc</button>
    <p data-testid="comparison-baseline">{baseline ? baseline.label : "Chưa chọn bản gốc A."}</p>
    <button className="button primary" disabled={busy||!baseline} onClick={()=>void run()}>So sánh với bản gốc</button>
    <button className="button secondary" disabled={busy||!baseline} onClick={()=>{if(stale){setError("Hãy áp dụng bản nháp trước khi khôi phục.");return;} setError("");if(baseline)void restore(structuredClone(baseline.plan),"Đã khôi phục bản gốc; bản B được giữ trong Bản trước.");}}>Khôi phục bản gốc</button>
    {error && <p role="alert">{error}</p>}
    {ready && <div data-testid="comparison-summary">
      <h3>Kết quả so sánh A → B</h3><p>Số bó: thêm {ready.counts.ADDED}, bỏ {ready.counts.REMOVED}, đổi {ready.counts.CHANGED}, không đổi {ready.counts.UNCHANGED}.</p>
      <div className="table-wrap"><table><thead><tr><th>Chỉ tiêu</th><th>Gốc A</th><th>Hiện tại B</th><th>Chênh lệch B−A</th></tr></thead><tbody>
        {([['manifest_mass_g','Tổng hàng','mass'],['placed_mass_g','Đã xếp','mass'],['remaining_capacity_g','Sức chở còn lại','mass'],['placed_count','Số bó đã xếp','count'],['unplaced_count','Số bó chưa xếp','count'],['excluded_count','Số bó loại trừ','count'],['issue_count','Số lỗi kiểm','count']] as const).map(([field,label,kind])=><tr key={field}><td>{label}</td><td>{kind==='mass'?`${tonnes(ready.before[field])} tấn`:fmt(ready.before[field])}</td><td>{kind==='mass'?`${tonnes(ready.after[field])} tấn`:fmt(ready.after[field])}</td><td>{kind==='mass' ? (ready.delta[field] !== 0 && Math.abs(ready.delta[field]) < 1000 ? 'Chênh lệch dưới 1 kg' : `${ready.delta[field]>0?'+':''}${formatKg(ready.delta[field])} kg`) : fmt(ready.delta[field])}</td></tr>)}
      </tbody></table></div><p>A: {ready.before.status} · B: {ready.after.status} · Chưa cấp điều kiện vận hành.</p>
      {ready.context_changes.length>0 && <div><strong>Điều kiện A và B khác nhau; không tự kết luận bản nào tốt hơn.</strong><Detail changes={ready.context_changes}/></div>}
      <p>Chưa kiểm A: {ready.before.unchecked.join(" · ")}<br/>Chưa kiểm B: {ready.after.unchecked.join(" · ")}</p>
      <label>Lọc thay đổi<select aria-label="Lọc thay đổi" value={status} onChange={e=>{setStatus(e.target.value);setPage(0);}}><option value="CHANGES">Chỉ thay đổi</option><option value="ALL">Tất cả</option><option value="ADDED">Thêm</option><option value="REMOVED">Đã bỏ</option><option value="CHANGED">Thay đổi</option><option value="UNCHANGED">Không đổi</option></select></label>
      <label>Tìm ID bó<input aria-label="Tìm ID bó" value={query} onChange={e=>{setQuery(e.target.value);setPage(0);}}/></label>
      <div data-testid="comparison-rows">{rows.slice(safePage*50,(safePage+1)*50).map(r=><article key={r.unit_id} data-testid={`comparison-row-${r.unit_id}`}><p><strong>{r.unit_id}</strong> · {statusLabel[r.status]} {r.in_after && <button className="text-button" onClick={()=>selectRow(r.unit_id)}>Chọn bó trong B</button>}</p>{r.source_identity_warning && <p>Cảnh báo: nguồn khác nhau; không xác nhận đây là cùng một bó vật lý.</p>}{r.changes.length>0 && <details><summary>Chi tiết thay đổi</summary><Detail changes={r.changes}/></details>}</article>)}</div>
      <button className="button secondary" disabled={safePage===0} onClick={()=>setPage(p=>Math.max(0,p-1))}>So sánh trang trước</button><span data-testid="comparison-page"> Trang {safePage+1}/{pages} · tối đa 50 bó </span><button className="button secondary" disabled={safePage>=pages-1} onClick={()=>setPage(p=>p+1)}>So sánh trang sau</button>
    </div>}
  </section>;
}
