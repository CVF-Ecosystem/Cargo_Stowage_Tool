import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  RevisionApiError, createCargoRevision, getCargoRevision, listCargoRevisions, previewCargoRevision,
  type ProvenanceStamp, type RevisionDetail, type RevisionDraft, type RevisionGroup,
  type RevisionList, type RevisionPreview,
} from "../api/client";
import { displayTime, fmt, isPipePlan, kgInput, parseCmToUm, parseKg, tonnes, umToCm, type Plan } from "./model";

const BASE_SUFFIX = "@R0000";
const kindLabels: Record<string, string> = {USER:"Người dùng", FACTORY:"Nhà máy", CUSTOMER:"Khách hàng", OTHER:"Khác"};
const confirmationLabels: Record<string, string> = {WORKBOOK:"Workbook", UNVERIFIED:"Chưa xác minh", CONFIRMED:"Đã xác nhận"};
const typeLabels: Record<string, string> = {UPDATE_GROUP:"Sửa nhóm", ADD_GROUP:"Thêm nhóm", BUNDLE_OVERRIDE:"Ghi đè bó"};
const fieldLabels: Record<string, string> = {
  bundle_count:"Số bó", pieces_per_bundle:"Số ống mỗi bó", dimensions_um:"Kích thước mỗi bó (cm)", mass_g:"Khối lượng mỗi bó (kg)",
  outside_diameter_mm:"Đường kính ngoài (mm)", wall_thickness_mm:"Độ dày thành (mm)", dimension_warning:"Cảnh báo kích thước",
};
const MAX_SHOWN_IDS = 50;

type ChangeType = "UPDATE_GROUP" | "ADD_GROUP" | "BUNDLE_OVERRIDE";
type Row = {
  key: number; type: ChangeType; group_id: string; bundle_id: string; confirmation: "UNVERIFIED" | "CONFIRMED";
  bundle_count: string; pieces_per_bundle: string; mass_kg: string; length_cm: string; width_cm: string; height_cm: string;
  outside_diameter_mm: string; wall_thickness_mm: string; warning: boolean; warningTouched: boolean;
};
type Source = {kind: string; reference: string; received_date: string; note: string};
type Problem = {index: number | null; field: string; message: string};

let rowCounter = 0;
const blankRow = (): Row => ({key: ++rowCounter, type:"UPDATE_GROUP", group_id:"", bundle_id:"", confirmation:"UNVERIFIED", bundle_count:"", pieces_per_bundle:"", mass_kg:"", length_cm:"", width_cm:"", height_cm:"", outside_diameter_mm:"", wall_thickness_mm:"", warning:false, warningTouched:false});
const blankSource = (): Source => ({kind:"USER", reference:"", received_date:"", note:""});

const shortId = (revisionId: string) => revisionId.includes("@") ? revisionId.split("@")[1] : revisionId;
const isBase = (revisionId: string) => revisionId.endsWith(BASE_SUFFIX);
const totalText = (grams: number | null) => grams === null ? "—" : `${fmt(grams / 1000)} kg · ${tonnes(grams)} t`;
const sourceText = (s: ProvenanceStamp["source"]) => s ? `${kindLabels[s.kind] ?? s.kind}: ${s.reference} (${s.received_date})` : "Workbook gốc";
const stampText = (p: ProvenanceStamp) => `${shortId(p.revision_id)} · ${isBase(p.revision_id) ? "Workbook gốc" : sourceText(p.source)} · ${confirmationLabels[p.confirmation] ?? p.confirmation}`;

function valueText(field: string, group: RevisionGroup): string {
  const v = (group as unknown as Record<string, unknown>)[field];
  if (v === undefined || v === null) return "—";
  if (field === "dimensions_um" && Array.isArray(v)) return `${(v as number[]).map(umToCm).join(" × ")} cm`;
  if (field === "mass_g" && typeof v === "number") return `${kgInput(v)} kg`;
  if (typeof v === "boolean") return v ? "Có" : "Không";
  return String(v);
}

function parseCount(text: string, label: string, min: number): number {
  const t = text.trim();
  if (!/^\d+$/.test(t) || !Number.isSafeInteger(Number(t)) || Number(t) < min) throw new Error(`${label} cần số nguyên từ ${min} trở lên.`);
  return Number(t);
}
function parseDimensions(row: Row): number[] {
  return [parseCmToUm(row.length_cm), parseCmToUm(row.width_cm), parseCmToUm(row.height_cm)];
}

// Builds exact change objects from the form; only touched fields are sent.
function buildChanges(rows: Row[], groups: RevisionGroup[]): {changes: Record<string, unknown>[]; problems: Problem[]} {
  const changes: Record<string, unknown>[] = [], problems: Problem[] = [];
  rows.forEach((row, index) => {
    const out: Record<string, unknown> = {type: row.type, confirmation: row.confirmation};
    const set: Record<string, unknown> = {};
    const fail = (field: string, e: unknown) => problems.push({index, field, message: e instanceof Error ? e.message : "Giá trị không hợp lệ."});
    const attempt = (field: string, fn: () => void) => { try { fn(); } catch (e) { fail(field, e); } };
    const group = groups.find(g => g.group_id === row.group_id);
    const addAll = row.type === "ADD_GROUP";
    if (row.type === "UPDATE_GROUP") {
      if (!row.group_id) fail("group_id", new Error("Chọn nhóm cần sửa."));
      out.group_id = row.group_id;
    }
    if (row.type === "BUNDLE_OVERRIDE") {
      if (!row.bundle_id.trim()) fail("bundle_id", new Error("Nhập mã bó cần ghi đè."));
      out.bundle_id = row.bundle_id.trim();
    }
    if (row.type !== "BUNDLE_OVERRIDE") {
      const need = (v: string, field: string, label: string, fn: () => void) => {
        if (v.trim() !== "") attempt(field, fn);
        else if (addAll) fail(field, new Error(`Thêm nhóm cần nhập ${label}.`));
      };
      need(row.bundle_count, "bundle_count", "số bó", () => { set.bundle_count = parseCount(row.bundle_count, "Số bó", addAll ? 1 : 0); });
      need(row.pieces_per_bundle, "pieces_per_bundle", "số ống mỗi bó", () => { set.pieces_per_bundle = parseCount(row.pieces_per_bundle, "Số ống mỗi bó", 1); });
      need(row.outside_diameter_mm, "outside_diameter_mm", "đường kính ngoài", () => { set.outside_diameter_mm = row.outside_diameter_mm.trim().replace(",", "."); });
      need(row.wall_thickness_mm, "wall_thickness_mm", "độ dày thành", () => { set.wall_thickness_mm = row.wall_thickness_mm.trim().replace(",", "."); });
      if (addAll || row.warningTouched) set.dimension_warning = row.warning;
    }
    // mass: per-bundle (group) or override (bundle)
    if (row.mass_kg.trim() !== "") attempt("mass_g", () => { set.mass_g = parseKg(row.mass_kg); });
    else if (addAll) fail("mass_g", new Error("Thêm nhóm cần nhập khối lượng mỗi bó."));
    // dimensions: all three or none; a partial edit of an existing group is completed from its current size
    const dimsTouched = [row.length_cm, row.width_cm, row.height_cm].map(v => v.trim() !== "");
    if (dimsTouched.some(Boolean)) {
      attempt("dimensions_um", () => {
        if (dimsTouched.every(Boolean)) { set.dimensions_um = parseDimensions(row); return; }
        if (row.type === "UPDATE_GROUP" && group) {
          const cur = group.dimensions_um.map(umToCm);
          set.dimensions_um = [row.length_cm.trim() || cur[0], row.width_cm.trim() || cur[1], row.height_cm.trim() || cur[2]].map(parseCmToUm);
          return;
        }
        throw new Error("Cần nhập đủ chiều dài, rộng, cao của bó.");
      });
    } else if (addAll) fail("dimensions_um", new Error("Thêm nhóm cần nhập chiều dài, rộng, cao của bó."));
    if (Object.keys(set).length === 0 && row.type !== "ADD_GROUP") fail("set", new Error("Chưa nhập trường nào để thay đổi."));
    if (row.type === "ADD_GROUP") out.group = set; else out.set = set;
    changes.push(out);
  });
  return {changes, problems};
}

function ProvenanceList({detail, allGroups}: {detail: RevisionDetail; allGroups: boolean}) {
  const shown = detail.groups.map(g => {
    const fields = Object.entries(g.provenance).filter(([, p]) => allGroups || !isBase(p.revision_id));
    return {g, fields: allGroups ? Object.entries(g.provenance) : fields, hasOverrides: g.overrides.length > 0};
  }).filter(x => allGroups || x.fields.length > 0 || x.hasOverrides);
  if (!shown.length) return <p>Revision này không có nhóm nào thay đổi so với workbook gốc.</p>;
  return <ul className="revision-groups">{shown.map(({g, fields}) => <li key={g.group_id} data-testid={`revision-group-${g.group_id}`}>
    <strong>{g.group_id}</strong> · {g.origin === "ADDED" ? "nhóm thêm" : "nhóm workbook"} · {g.bundle_count} bó × {g.pieces_per_bundle} ống · {valueText("mass_g", g)} · {valueText("dimensions_um", g)}
    <ul>{fields.map(([field, p]) => <li key={field}>{fieldLabels[field] ?? field}: <strong>{valueText(field, g)}</strong> — {stampText(p)}</li>)}
      {g.overrides.map(o => <li key={o.bundle_id}>Bó {o.bundle_id} ghi đè: {o.mass_g !== null && `${kgInput(o.mass_g)} kg `}{o.dimensions_um && `${o.dimensions_um.map(umToCm).join(" × ")} cm `}— {Object.values(o.provenance).map(stampText).filter((v, i, a) => a.indexOf(v) === i).join("; ")}</li>)}
    </ul></li>)}</ul>;
}

export default function CargoRevisionPanel({plan, onCreated}: {plan: Plan; onCreated?: () => void}) {
  const [revisions, setRevisions] = useState<RevisionList | null>(null);
  const [loadError, setLoadError] = useState("");
  const [details, setDetails] = useState<Record<string, RevisionDetail>>({});
  const [selectedId, setSelectedId] = useState("");
  const [detailError, setDetailError] = useState("");
  const [allGroups, setAllGroups] = useState(false);
  const [source, setSource] = useState<Source>(blankSource);
  const [rows, setRows] = useState<Row[]>(() => [blankRow()]);
  const [preview, setPreview] = useState<{data: RevisionPreview; key: string} | null>(null);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);

  const latestId = revisions?.latest_revision_id ?? "";
  const inUse = isPipePlan(plan) ? (plan.cargo_revision?.revision_id ?? `${plan.cargo_dataset ?? "BALTIMORE-PIPE-V1-1"}${BASE_SUFFIX}`) : "";

  const loadDetail = useCallback(async (id: string): Promise<RevisionDetail | null> => {
    try {
      const d = await getCargoRevision(id);
      setDetails(prev => ({...prev, [id]: d}));
      setDetailError("");
      return d;
    } catch (e) { setDetailError(e instanceof Error ? e.message : "Không đọc được revision."); return null; }
  }, []);
  const reload = useCallback(async (select?: string) => {
    try {
      const list = await listCargoRevisions();
      setRevisions(list); setLoadError("");
      setDetails({});
      const target = select ?? list.latest_revision_id;
      setSelectedId(target);
      await loadDetail(list.latest_revision_id);
      if (target !== list.latest_revision_id) await loadDetail(target);
      return list;
    } catch (e) { setLoadError(e instanceof Error ? e.message : "Không đọc được danh sách revision."); return null; }
  }, [loadDetail]);
  useEffect(() => { void reload(); }, [reload]);

  const latestDetail = latestId ? details[latestId] : undefined;
  const groups = latestDetail?.groups ?? [];
  const built = useMemo(() => buildChanges(rows, groups), [rows, groups]);
  const draft: RevisionDraft = {parent_revision_id: latestId, source: {...source}, changes: built.changes};
  const draftKey = JSON.stringify(draft);
  const previewCurrent = preview && preview.key === draftKey && built.problems.length === 0 ? preview.data : null;
  const canCreate = !!previewCurrent && previewCurrent.valid && previewCurrent.parent_is_latest && !busy && !!latestId;

  const edit = (patch: Partial<Source>) => { setSource(s => ({...s, ...patch})); setMessage(""); };
  const editRow = (key: number, patch: Partial<Row>) => { setRows(rs => rs.map(r => r.key === key ? {...r, ...patch} : r)); setMessage(""); };
  const shownProblems: Problem[] = problems.length ? problems : (preview && preview.key === draftKey && !preview.data.valid ? preview.data.errors : []);

  const doPreview = async () => {
    if (lock.current || !latestId) return;
    setMessage(""); setActionError("");
    if (built.problems.length) { setProblems(built.problems); setPreview(null); return; }
    setProblems([]);
    lock.current = true; setBusy(true);
    const key = draftKey;
    try { const data = await previewCargoRevision(draft); setPreview({data, key}); }
    catch (e) { setPreview(null); setActionError(e instanceof Error ? e.message : "Không xem trước được lô cập nhật."); if (e instanceof RevisionApiError && e.errors.length) setProblems(e.errors); }
    finally { lock.current = false; setBusy(false); }
  };
  const doCreate = async () => {
    if (lock.current || !canCreate) return;
    setMessage(""); setActionError("");
    lock.current = true; setBusy(true);
    try {
      const created = await createCargoRevision(draft);
      setMessage(`Đã tạo ${created.revision_id}. Các phương án đã lưu được kiểm lại theo revision mới nhất.`);
      setRows([blankRow()]); setSource(blankSource()); setPreview(null); setProblems([]);
      await reload(created.revision_id);
      onCreated?.();
    } catch (e) {
      setPreview(null);
      if (e instanceof RevisionApiError) {
        setActionError(e.message);
        if (e.errors.length) setProblems(e.errors);
        if (e.status === 409) await reload();
      } else setActionError("Không tạo được revision dữ liệu hàng.");
    } finally { lock.current = false; setBusy(false); }
  };
  const openDetail = async (id: string) => { setSelectedId(id); setDetailError(""); if (!details[id]) await loadDetail(id); };
  const selectedDetail = selectedId ? details[selectedId] : undefined;

  const problemLine = (p: Problem) => `${p.index === null ? "Lô cập nhật" : `Thay đổi ${p.index + 1}`} · ${p.field}: ${p.message}`;
  const pv = previewCurrent;
  const ids = (label: string, list: string[]) => <p>{label}: {list.length}{list.length ? ` — ${list.slice(0, MAX_SHOWN_IDS).join(", ")}${list.length > MAX_SHOWN_IDS ? ` … và ${list.length - MAX_SHOWN_IDS} bó khác` : ""}` : ""}</p>;

  return <section className="editor-card m2a-card cargo-revision-panel" aria-label="Dữ liệu hàng">
    <h2>Dữ liệu hàng</h2>
    <p>Mỗi lô cập nhật tạo một revision mới, chỉ thêm, không sửa revision cũ; phương án đã lưu giữ nguyên revision đã ghim. Số chưa xác minh vẫn được đánh dấu rõ.</p>
    <p data-testid="revision-in-use">{inUse ? <>Revision đang dùng trong phương án đang mở: <strong>{inUse}</strong></> : "Phương án đang mở không dùng list ống nên chưa ghim revision dữ liệu hàng."}</p>
    <p data-testid="revision-latest">{revisions ? <>Revision mới nhất: <strong>{revisions.latest_revision_id}</strong>{inUse && inUse !== revisions.latest_revision_id ? " · phương án đang mở dùng revision cũ hơn; dùng “Xem trước list ống” để nạp revision mới nhất." : ""}</> : (loadError || "Đang đọc revision dữ liệu hàng…")}</p>
    {loadError && revisions && <p>{loadError}</p>}

    {revisions && <><h3>Lịch sử revision</h3>
      <ul className="revision-history" data-testid="revision-history">{revisions.revisions.map(r => <li key={r.revision_id} data-testid={`revision-item-${shortId(r.revision_id)}`} aria-current={selectedId === r.revision_id}>
        <strong>{r.revision_id}</strong>{r.revision_id === revisions.latest_revision_id ? " (mới nhất)" : ""}{!r.available && " · không đọc được"}
        <br />{r.created_utc ? displayTime(r.created_utc) : "Revision gốc từ workbook"} · {r.source ? `${kindLabels[r.source.kind] ?? r.source.kind}: ${r.source.reference} · nhận ${r.source.received_date}` : "Nguồn: workbook"}
        <br />{r.change_count} thay đổi · {r.group_count ?? "—"} nhóm · {r.bundle_count ?? "—"} bó · {totalText(r.total_mass_g)}
        {r.integrity_error && <><br />{r.integrity_error}</>}
        <br /><button type="button" className="button secondary" aria-label={`Xem chi tiết revision ${shortId(r.revision_id)}`} disabled={!r.available} onClick={() => void openDetail(r.revision_id)}>Xem chi tiết {shortId(r.revision_id)}</button>
      </li>)}</ul></>}

    {selectedDetail && <div data-testid="revision-detail"><h3>Chi tiết {selectedDetail.revision_id}</h3>
      <p>{selectedDetail.change_count} thay đổi · {selectedDetail.group_count ?? "—"} nhóm · {selectedDetail.bundle_count ?? "—"} bó · {totalText(selectedDetail.total_mass_g)} · SHA-256 {selectedDetail.content_sha256.slice(0, 12)}…</p>
      <label className="check-row"><input type="checkbox" aria-label="Hiện tất cả nhóm" checked={allGroups} onChange={e => setAllGroups(e.target.checked)} />Hiện tất cả nhóm (mặc định chỉ nhóm có trường đổi)</label>
      {isBase(selectedDetail.revision_id) && !allGroups && <p>Revision gốc: mọi trường đều từ workbook (Workbook).</p>}
      <ProvenanceList detail={selectedDetail} allGroups={allGroups} /></div>}
    {detailError && <p role="alert">{detailError}</p>}

    <h3>Tạo lô cập nhật</h3>
    <p>Lô cập nhật dựa trên revision mới nhất {latestId ? <strong>{latestId}</strong> : "(đang đọc)"}. Chỉ trường bạn nhập mới được gửi; để trống nghĩa là giữ nguyên.</p>
    <div className="revision-grid">
      <label>Loại nguồn<select aria-label="Loại nguồn" value={source.kind} onChange={e => edit({kind: e.target.value})}>{Object.entries(kindLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
      <label>Tham chiếu nguồn<input aria-label="Tham chiếu nguồn" maxLength={200} value={source.reference} onChange={e => edit({reference: e.target.value})} /></label>
      <label>Ngày nhận<input type="date" aria-label="Ngày nhận" value={source.received_date} onChange={e => edit({received_date: e.target.value})} /></label>
      <label>Ghi chú lô cập nhật<input aria-label="Ghi chú lô cập nhật" maxLength={500} value={source.note} onChange={e => edit({note: e.target.value})} /></label>
    </div>
    {rows.map((row, i) => {
      const group = groups.find(g => g.group_id === row.group_id);
      const hint = (v: string | undefined) => (row.type === "UPDATE_GROUP" && v !== undefined ? `hiện tại ${v}` : "");
      const warning = row.warningTouched ? row.warning : (row.type === "UPDATE_GROUP" ? (group?.dimension_warning ?? false) : row.warning);
      const dims = group?.dimensions_um.map(umToCm);
      return <fieldset key={row.key} className="revision-change" role="group" aria-label={`Thay đổi ${i + 1}`} data-testid={`change-row-${i}`}>
        <legend>Thay đổi {i + 1}</legend>
        <div className="revision-grid">
          <label>Loại thay đổi<select aria-label="Loại thay đổi" value={row.type} onChange={e => editRow(row.key, {type: e.target.value as ChangeType})}>{Object.entries(typeLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
          {row.type === "UPDATE_GROUP" && <label>Nhóm cần sửa<select aria-label="Nhóm cần sửa" value={row.group_id} onChange={e => editRow(row.key, {group_id: e.target.value})}><option value="">Chọn nhóm</option>{groups.map(g => <option key={g.group_id} value={g.group_id}>{g.group_id} · {g.bundle_count} bó × {g.pieces_per_bundle} ống</option>)}</select></label>}
          {row.type === "BUNDLE_OVERRIDE" && <label>Mã bó ghi đè<input aria-label="Mã bó ghi đè" placeholder="PIPE-R002-B0001" value={row.bundle_id} onChange={e => editRow(row.key, {bundle_id: e.target.value})} /></label>}
          <label>Mức xác nhận<select aria-label="Mức xác nhận" value={row.confirmation} onChange={e => editRow(row.key, {confirmation: e.target.value as Row["confirmation"]})}><option value="UNVERIFIED">Chưa xác minh</option><option value="CONFIRMED">Đã xác nhận</option></select></label>
          {row.type !== "BUNDLE_OVERRIDE" && <>
            <label>Số bó trong nhóm<input aria-label="Số bó trong nhóm" inputMode="numeric" placeholder={hint(group && String(group.bundle_count))} value={row.bundle_count} onChange={e => editRow(row.key, {bundle_count: e.target.value})} /></label>
            <label>Số ống mỗi bó<input aria-label="Số ống mỗi bó" inputMode="numeric" placeholder={hint(group && String(group.pieces_per_bundle))} value={row.pieces_per_bundle} onChange={e => editRow(row.key, {pieces_per_bundle: e.target.value})} /></label>
          </>}
          <label>{row.type === "BUNDLE_OVERRIDE" ? "Khối lượng ghi đè (kg)" : "Khối lượng mỗi bó (kg)"}<input aria-label={row.type === "BUNDLE_OVERRIDE" ? "Khối lượng ghi đè (kg)" : "Khối lượng mỗi bó (kg)"} inputMode="decimal" placeholder={hint(group && kgInput(group.mass_g))} value={row.mass_kg} onChange={e => editRow(row.key, {mass_kg: e.target.value})} /></label>
          <label>Chiều dài bó (cm)<input aria-label="Chiều dài bó (cm)" inputMode="decimal" placeholder={hint(dims?.[0])} value={row.length_cm} onChange={e => editRow(row.key, {length_cm: e.target.value})} /></label>
          <label>Chiều rộng bó (cm)<input aria-label="Chiều rộng bó (cm)" inputMode="decimal" placeholder={hint(dims?.[1])} value={row.width_cm} onChange={e => editRow(row.key, {width_cm: e.target.value})} /></label>
          <label>Chiều cao bó (cm)<input aria-label="Chiều cao bó (cm)" inputMode="decimal" placeholder={hint(dims?.[2])} value={row.height_cm} onChange={e => editRow(row.key, {height_cm: e.target.value})} /></label>
          {row.type !== "BUNDLE_OVERRIDE" && <>
            <label>Đường kính ngoài (mm)<input aria-label="Đường kính ngoài (mm)" inputMode="decimal" placeholder={hint(group?.outside_diameter_mm)} value={row.outside_diameter_mm} onChange={e => editRow(row.key, {outside_diameter_mm: e.target.value})} /></label>
            <label>Độ dày thành (mm)<input aria-label="Độ dày thành (mm)" inputMode="decimal" placeholder={hint(group?.wall_thickness_mm)} value={row.wall_thickness_mm} onChange={e => editRow(row.key, {wall_thickness_mm: e.target.value})} /></label>
            <label className="check-row"><input type="checkbox" aria-label="Cảnh báo kích thước" checked={warning} onChange={e => editRow(row.key, {warning: e.target.checked, warningTouched: true})} />Đánh dấu cảnh báo kích thước</label>
          </>}
        </div>
        {rows.length > 1 && <button type="button" className="button secondary" aria-label={`Xóa thay đổi ${i + 1}`} onClick={() => setRows(rs => rs.filter(r => r.key !== row.key))}>Xóa thay đổi {i + 1}</button>}
      </fieldset>;
    })}
    <button type="button" className="button secondary" disabled={rows.length >= 500} onClick={() => setRows(rs => [...rs, blankRow()])}>Thêm thay đổi</button>
    <button type="button" className="button secondary" disabled={busy || !latestId} onClick={() => void doPreview()}>Xem trước lô cập nhật</button>
    <button type="button" className="button primary" disabled={!canCreate} onClick={() => void doCreate()}>Tạo revision</button>
    {!canCreate && <p>Nút Tạo revision chỉ bật sau khi xem trước hợp lệ đúng nội dung lô cập nhật hiện tại.</p>}

    {message && <p role="status" data-testid="revision-message">{message}</p>}
    {actionError && <p role="alert" data-testid="revision-action-error">{actionError}</p>}
    {shownProblems.length > 0 && <ul data-testid="revision-errors" aria-label="Lỗi lô cập nhật">{shownProblems.map((p, i) => <li key={i}>{problemLine(p)}</li>)}</ul>}
    {pv && pv.valid && <div data-testid="revision-preview">
      <h3>Xem trước lô cập nhật</h3>
      <p>Hợp lệ{pv.parent_is_latest ? "" : `; nhưng revision cha không còn là mới nhất (${pv.latest_revision_id})`}. Kết quả: {pv.group_count ?? "—"} nhóm · {pv.bundle_count ?? "—"} bó · {totalText(pv.total_mass_g)}.</p>
      <ul>{pv.change_summaries.map(c => <li key={c.index}>Thay đổi {c.index + 1} · {typeLabels[c.type] ?? c.type} · {c.target}: {c.text}</li>)}</ul>
      {ids("Bó thêm", pv.added_bundle_ids)}{ids("Bó bỏ", pv.removed_bundle_ids)}{ids("Bó đổi", pv.changed_bundle_ids)}
    </div>}
  </section>;
}
