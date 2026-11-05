import { useEffect, useRef, useState } from "react";
import {
  ProfileApiError,
  createVesselProfile,
  getVesselProfile,
  listVesselProfiles,
  previewVesselProfile,
  profileBody,
  type ProfileDetail,
  type ProfileError,
  type ProfileListItem,
  type ProfilePreview,
} from "../api/client";
import { fmt, tonnes } from "./model";

// Vietnamese labels for the provenance status of every number (DA03).
const FIELD_STATUS_LABEL: Record<string, string> = { ESTIMATED: "ước tính", SOURCED: "theo nguồn", MEASURED: "đã đo" };
export const fieldStatusLabel = (status: string | null | undefined) => (status && FIELD_STATUS_LABEL[status]) || "chưa rõ";

const MAX_GLB_BYTES = 20 * 1024 * 1024;
const keyOf = (item: { id: string; version: number }) => `${item.id}@${item.version}`;
const messageOf = (e: unknown, fallback: string) => (e instanceof Error && e.message ? e.message : fallback);

// Base64 of a byte array built in chunks, so large GLB files do not exceed the argument limit.
export function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  return btoa(binary);
}

function statusLine(item: ProfileListItem): string {
  if (item.status === "UNAVAILABLE") return `Không dùng được: ${item.integrity_error ?? "hồ sơ không qua kiểm toàn vẹn."}`;
  const fs = item.field_status;
  const sources = item.source_documents.map((s) => s.title).join("; ");
  return `Số liệu: thân ${fieldStatusLabel(fs?.dimensions_m)} · hầm ${fieldStatusLabel(fs?.hold)} · trường hợp tải ${fieldStatusLabel(fs?.cases)}. Nguồn: ${sources || "chưa ghi"}. Kiểm tọa độ: ${item.verification ?? "chưa có"}.`;
}

type Previewed = { jsonText: string; glbBase64: string; result: ProfilePreview };
type Issue = { message: string; errors: ProfileError[] };
export type OpenCurrent = { id: string; version: number; caseId: string } | null;
type Props = { busy: boolean; current: OpenCurrent; onOpen: (id: string, version: number, caseId: string) => void; reloadToken?: number };

export default function VesselProfilePanel({ busy, current, onOpen, reloadToken = 0 }: Props) {
  const [items, setItems] = useState<ProfileListItem[] | null>(null);
  const [listError, setListError] = useState("");
  const [selectedKey, setSelectedKey] = useState("");
  const [detail, setDetail] = useState<{ key: string; data: ProfileDetail } | null>(null);
  const [detailError, setDetailError] = useState("");
  const [caseId, setCaseId] = useState("");

  const [jsonText, setJsonText] = useState<string | null>(null);
  const [glbBase64, setGlbBase64] = useState<string | null>(null);
  const [previewed, setPreviewed] = useState<Previewed | null>(null);
  const [issue, setIssue] = useState<Issue | null>(null);
  const [created, setCreated] = useState("");
  const [importBusy, setImportBusy] = useState(false);
  const jsonInput = useRef<HTMLInputElement>(null);
  const glbInput = useRef<HTMLInputElement>(null);
  const jsonToken = useRef(0);
  const glbToken = useRef(0);
  // Latest file contents, read after an await so a result for replaced files is never shown or armed.
  const contents = useRef<{ jsonText: string | null; glbBase64: string | null }>({ jsonText: null, glbBase64: null });
  contents.current = { jsonText, glbBase64 };

  const currentKey = current ? keyOf(current) : "";
  const currentCase = current?.caseId ?? "";

  // Mount: load the list and select the profile of the open plan when there is one, else the first usable entry.
  useEffect(() => {
    let live = true;
    listVesselProfiles()
      .then((list) => {
        if (!live) return;
        setItems(list);
        setListError("");
        const first = list.find((i) => i.status === "AVAILABLE");
        setSelectedKey((prev) => prev || (first ? keyOf(first) : ""));
      })
      .catch((e) => { if (live) setListError(messageOf(e, "Không đọc được danh sách tàu.")); });
    return () => { live = false; };
  }, []);

  // Reload when the parent bumps reloadToken (after a backup restore). Keeps the current selection only if it still exists.
  useEffect(() => {
    if (!reloadToken) return;
    let live = true;
    listVesselProfiles()
      .then((list) => {
        if (!live) return;
        setItems(list);
        setListError("");
        const first = list.find((i) => i.status === "AVAILABLE");
        setSelectedKey((prev) => (list.some((i) => keyOf(i) === prev) ? prev : (first ? keyOf(first) : "")));
      })
      .catch((e) => { if (live) setListError(messageOf(e, "Không đọc được danh sách tàu.")); });
    return () => { live = false; };
  }, [reloadToken]);

  // Follow the open plan's profile when it changes elsewhere (switch, reopen, rebase).
  useEffect(() => {
    if (currentKey) setSelectedKey(currentKey);
  }, [currentKey]);

  // Fetch the chosen profile's detail for its case list; the built-in and stored profiles are both fetched the same way.
  useEffect(() => {
    const item = items?.find((i) => keyOf(i) === selectedKey);
    if (!item || item.status !== "AVAILABLE") {
      setDetail(null);
      setCaseId("");
      return;
    }
    let live = true;
    setDetailError("");
    getVesselProfile(item.id, item.version)
      .then((data) => {
        if (!live) return;
        const cases = profileBody(data).cases;
        const preferred = currentKey === selectedKey ? currentCase : "";
        setDetail({ key: selectedKey, data });
        setCaseId(cases.some((c) => c.id === preferred) ? preferred : (cases[0]?.id ?? ""));
      })
      .catch((e) => {
        if (!live) return;
        setDetail(null);
        setDetailError(messageOf(e, "Không đọc được hồ sơ tàu."));
      });
    return () => { live = false; };
  }, [selectedKey, items]);

  // A case switched from the Workspace becomes the selected case of the same profile.
  useEffect(() => {
    if (detail && currentKey === detail.key && profileBody(detail.data).cases.some((c) => c.id === currentCase)) setCaseId(currentCase);
  }, [currentKey, currentCase, detail]);

  const refresh = async (select?: string) => {
    try {
      const list = await listVesselProfiles();
      setItems(list);
      setListError("");
      if (select) setSelectedKey(select);
    } catch (e) {
      setListError(messageOf(e, "Không đọc được danh sách tàu."));
    }
  };

  const detailNow = detail && detail.key === selectedKey ? detail.data : null;
  const selected = items?.find((i) => keyOf(i) === selectedKey);
  const openable = !busy && !!detailNow && !!caseId && selected?.status === "AVAILABLE";

  const clearPreview = () => { setPreviewed(null); setIssue(null); setCreated(""); };
  const pickJson = async (file: File | undefined) => {
    const token = ++jsonToken.current;
    clearPreview();
    setJsonText(null);
    if (!file) return;
    try {
      const text = await file.text();
      if (token === jsonToken.current) setJsonText(text);
    } catch {
      if (token === jsonToken.current) setIssue({ message: "Không đọc được tệp profile JSON.", errors: [] });
    }
  };
  const pickGlb = async (file: File | undefined) => {
    const token = ++glbToken.current;
    clearPreview();
    setGlbBase64(null);
    if (!file) return;
    if (file.size > MAX_GLB_BYTES) {
      setIssue({ message: "Tệp GLB vượt 20 MiB; chưa gửi lên.", errors: [] });
      return;
    }
    try {
      const bytes = new Uint8Array(await file.arrayBuffer());
      if (token === glbToken.current) setGlbBase64(bytesToBase64(bytes));
    } catch {
      if (token === glbToken.current) setIssue({ message: "Không đọc được tệp GLB.", errors: [] });
    }
  };

  const runPreview = async () => {
    if (importBusy) return;
    const j = jsonText, g = glbBase64;
    if (j === null || g === null) {
      setIssue({ message: "Chọn cả tệp profile JSON và tệp GLB trước khi xem trước.", errors: [] });
      return;
    }
    let profile: Record<string, unknown>;
    try {
      profile = JSON.parse(j) as Record<string, unknown>;
    } catch {
      setPreviewed(null);
      setIssue({ message: "Tệp profile không phải JSON hợp lệ; chưa kiểm gì.", errors: [] });
      return;
    }
    setImportBusy(true);
    setIssue(null);
    setCreated("");
    try {
      const result = await previewVesselProfile({ profile, glb_base64: g });
      if (contents.current.jsonText === j && contents.current.glbBase64 === g) setPreviewed({ jsonText: j, glbBase64: g, result });
    } catch (e) {
      setPreviewed(null);
      setIssue({ message: messageOf(e, "Không xem trước được profile tàu."), errors: e instanceof ProfileApiError ? e.errors : [] });
    } finally {
      setImportBusy(false);
    }
  };

  // Create is armed only by a valid preview of exactly the current file contents.
  const canCreate = !!previewed && previewed.result.valid && jsonText === previewed.jsonText && glbBase64 === previewed.glbBase64 && !importBusy;
  const runCreate = async () => {
    if (!previewed || !canCreate) return;
    let profile: Record<string, unknown>;
    try {
      profile = JSON.parse(previewed.jsonText) as Record<string, unknown>;
    } catch {
      setPreviewed(null);
      setIssue({ message: "Tệp profile không phải JSON hợp lệ; chưa ghi gì.", errors: [] });
      return;
    }
    setImportBusy(true);
    setIssue(null);
    setCreated("");
    try {
      const item = await createVesselProfile({ profile, glb_base64: previewed.glbBase64 });
      setPreviewed(null);
      setJsonText(null);
      setGlbBase64(null);
      if (jsonInput.current) jsonInput.current.value = "";
      if (glbInput.current) glbInput.current.value = "";
      setCreated(`Đã tạo profile ${item.id} v${item.version}.`);
      await refresh(keyOf(item));
    } catch (e) {
      // A failed create drops the preview so the user must check again against the current store (e.g. a new version number).
      setPreviewed(null);
      setIssue({ message: messageOf(e, "Không tạo được profile tàu; chưa ghi gì."), errors: e instanceof ProfileApiError ? e.errors : [] });
      if (e instanceof ProfileApiError && e.status === 409) await refresh();
    } finally {
      setImportBusy(false);
    }
  };

  const result = previewed?.result ?? null;
  const verification = result?.verification ?? null;
  const nextVersion = (result?.latest_version ?? 0) + 1;

  return <section className="editor-card m2a-card vessel-profile-panel" aria-label="Tàu và hầm">
    <h2>Tàu và hầm</h2>
    <p>Chọn tàu dựng sẵn hoặc profile đã nhập, rồi chọn trường hợp tải. Mỗi số liệu ghi rõ là ước tính, theo nguồn hay đã đo. Không xác nhận an toàn hoặc điều kiện vận hành.</p>
    {listError && <p role="alert">{listError}</p>}
    <div className="vessel-profile-row">
      <label>Chọn tàu<select aria-label="Chọn tàu" value={selectedKey} disabled={busy || !items} onChange={(e) => setSelectedKey(e.target.value)}>
        {!items && <option value="">Đang đọc danh sách…</option>}
        {items?.map((i) => <option key={keyOf(i)} value={keyOf(i)} disabled={i.status === "UNAVAILABLE"}>
          {`${i.name} · v${i.version}${i.builtin ? " · dựng sẵn" : ""}${i.status === "UNAVAILABLE" ? " · không dùng được" : ""}`}
        </option>)}
      </select></label>
      <label>Trường hợp tải<select aria-label="Trường hợp tải" value={caseId} disabled={busy || !detailNow} onChange={(e) => setCaseId(e.target.value)}>
        {detailNow && profileBody(detailNow).cases.map((c) => <option key={c.id} value={c.id}>{`${c.id} · ${tonnes(c.cargo_mass_g)} tấn · mớn ${fmt(c.draft_m)} m`}</option>)}
      </select></label>
      <button type="button" className="button primary" disabled={!openable} onClick={() => detailNow && onOpen(detailNow.id, detailNow.version, caseId)}>Mở tàu và trường hợp</button>
    </div>
    {selected && <p data-testid="vessel-profile-status">{statusLine(selected)}</p>}
    {detailError && <p role="alert">{detailError}</p>}

    <section className="vessel-import" aria-label="Nhập profile tàu">
      <h3>Nhập profile tàu</h3>
      <p>Chọn tệp profile JSON và tệp GLB (mét, trục Y lên). Xem trước để kiểm sai số landmark và hộp bao; chỉ khi kết quả hợp lệ đúng nội dung này mới tạo được phiên bản mới.</p>
      <div className="vessel-profile-row">
        <label className="profile-file">Tệp profile JSON<input ref={jsonInput} type="file" accept=".json,application/json" aria-label="Tệp profile JSON" disabled={importBusy} onChange={(e) => void pickJson(e.target.files?.[0])} /></label>
        <label className="profile-file">Tệp GLB<input ref={glbInput} type="file" accept=".glb,model/gltf-binary" aria-label="Tệp GLB" disabled={importBusy} onChange={(e) => void pickGlb(e.target.files?.[0])} /></label>
      </div>
      <div className="vessel-profile-row">
        <button type="button" className="button secondary" disabled={importBusy || jsonText === null || glbBase64 === null} onClick={() => void runPreview()}>Xem trước kiểm</button>
        <button type="button" className="button primary" disabled={!canCreate} onClick={() => void runCreate()}>Tạo profile</button>
      </div>
      {issue && <div role="alert">
        <p>{issue.message}</p>
        {issue.errors.length > 0 && <ul aria-label="Lỗi nhập profile">{issue.errors.map((e, i) => <li key={i}>{e.field}: {e.message}</li>)}</ul>}
      </div>}
      {created && <p role="status">{created}</p>}

      {previewed && result && <section className="vessel-preview" aria-label="Kết quả xem trước">
        <p>{result.valid ? `Xem trước hợp lệ: ${result.id} v${result.version}. Bấm Tạo profile để lưu.` : "Chưa thể tạo profile; sửa các lỗi dưới đây rồi xem trước lại."}</p>
        {result.errors.length > 0 && <ul aria-label="Lỗi hồ sơ tàu">{result.errors.map((e, i) => <li key={i}>{e.field}: {e.message}</li>)}</ul>}
        {verification && <>
          <p>Kết quả kiểm: <strong>{verification.result}</strong></p>
          <div className="table-wrap vessel-table-wrap">
            <table className="vessel-table" aria-label="Sai số landmark">
              <thead><tr><th>Landmark</th><th>Sai số X (mm)</th><th>Sai số Y (mm)</th><th>Sai số Z (mm)</th><th>Đạt</th></tr></thead>
              <tbody>{verification.landmarks.map((l, i) => <tr key={i}>
                <td>{l.name}</td>
                {l.error_mm.map((n, k) => <td key={k}>{fmt(n)}</td>)}
                <td>{l.pass ? "Đạt" : "Không đạt"}</td>
              </tr>)}</tbody>
            </table>
          </div>
          <p>Hộp bao GLB chứa hầm: {verification.bounds.contains_hold ? "có" : "không"}</p>
        </>}
        {result.builtin_conflict && <p>Mã {result.id} thuộc hồ sơ tàu dựng sẵn; không tạo thêm phiên bản.</p>}
        {!result.builtin_conflict && result.id && result.version !== null && !result.version_ok && <p>Phiên bản {result.version} không phải phiên bản kế tiếp; phải là {nextVersion} (mới nhất hiện có: {result.latest_version ?? 0}).</p>}
        {verification?.result === "FAIL" && <p>Kiểm landmark hoặc hộp bao không đạt; profile này không được lưu.</p>}
      </section>}
    </section>
  </section>;
}
