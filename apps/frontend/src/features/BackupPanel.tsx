import { useEffect, useRef, useState } from "react";
import { BackupApiError, applyBackup, autoBackupStatus, downloadAutoBackup, exportBackup, previewBackup, runAutoBackup, type AutoBackupStatus, type BackupPreview, type BackupRestoreResult } from "../api/client";

const WARNING = "Toàn bộ dữ liệu hiện có sẽ được thay bằng bản sao lưu; một bản sao lưu dữ liệu hiện tại sẽ được tạo tự động trước khi thay.";
const LIMITS = "Chưa có sao lưu tự động theo lịch, mã hóa hay khôi phục gộp; khôi phục luôn thay toàn bộ.";
const AUTO_NOTE = "Bản tự động nằm cùng máy với dữ liệu. Hãy tải một bản và cất ra ngoài máy (USB, ổ mạng). Chưa có sao lưu theo lịch khi app đang đóng, chưa mã hóa.";
const AUTO_LIST_MAX = 10;

type Props = {
  busy: boolean;
  lock: { current: boolean };
  setBusy: (value: boolean) => void;
  // Called after a successful restore so the Workspace reloads the saved-plan list and the vessel profile list.
  onRestored: (result: BackupRestoreResult) => void;
};
type Failure = { message: string; errors: { field: string; message: string }[] };

function timeText(value: string): string {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "Thời gian không hợp lệ";
  const parts = new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(date);
  const part = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${part("day")}-${part("month")}-${part("year")} ${part("hour")}:${part("minute")}`;
}

function failureOf(e: unknown, fallback: string): Failure {
  if (e instanceof BackupApiError) return { message: e.message || fallback, errors: e.errors };
  return { message: e instanceof Error && e.message ? e.message : fallback, errors: [] };
}

function sizeText(bytes: number): string {
  return `${Math.max(1, Math.round(bytes / 1024)).toLocaleString("vi-VN")} KB`;
}

export default function BackupPanel({ busy, lock, setBusy, onRestored }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<BackupPreview | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [result, setResult] = useState("");
  const [working, setWorking] = useState<"" | "export" | "check" | "restore">("");
  const input = useRef<HTMLInputElement>(null);
  const token = useRef(0);
  const [auto, setAuto] = useState<AutoBackupStatus | null>(null);
  const [autoRunning, setAutoRunning] = useState(false);
  const [autoFailure, setAutoFailure] = useState("");
  const [autoResult, setAutoResult] = useState("");

  const clearChoice = () => {
    setFile(null);
    setPreview(null);
    if (input.current) input.current.value = "";
  };

  const download = async () => {
    if (lock.current) return;
    lock.current = true; setBusy(true); setWorking("export"); setFailure(null); setResult("");
    try {
      const { blob, filename } = await exportBackup();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setResult(`Đã tải bản sao lưu ${filename}.`);
    } catch (e) {
      setFailure(failureOf(e, "Không tạo được bản sao lưu."));
    } finally {
      lock.current = false; setBusy(false); setWorking("");
    }
  };

  const pick = async (picked: File | undefined) => {
    const mine = ++token.current;
    setFile(null); setPreview(null); setFailure(null); setResult("");
    if (!picked) return;
    if (lock.current) { setFailure({ message: "Đang xử lý dữ liệu khác; chọn lại tệp sau khi xong.", errors: [] }); clearChoice(); return; }
    setFile(picked);
    lock.current = true; setBusy(true); setWorking("check");
    try {
      const checked = await previewBackup(picked);
      if (mine === token.current) setPreview(checked);
    } catch (e) {
      if (mine === token.current) { setFailure(failureOf(e, "Không kiểm được bản sao lưu.")); clearChoice(); }
    } finally {
      lock.current = false; setBusy(false); setWorking("");
    }
  };

  const restore = async () => {
    if (!file || !preview || lock.current) return;
    lock.current = true; setBusy(true); setWorking("restore"); setFailure(null); setResult("");
    try {
      const restored = await applyBackup(file, preview.backup_sha256);
      const c = restored.counts;
      setResult(`Đã khôi phục từ bản sao lưu (${c.plans} phương án, ${c.revisions} revision, ${c.vessel_profile_versions} phiên bản hồ sơ tàu). Bản sao lưu dữ liệu cũ: ${restored.pre_restore_backup}. Phương án đang mở trong tab chưa thuộc dữ liệu đã khôi phục; hãy lưu lại nếu cần.`);
      clearChoice();
      onRestored(restored);
    } catch (e) {
      clearChoice();
      setFailure(failureOf(e, "Không khôi phục được bản sao lưu."));
    } finally {
      lock.current = false; setBusy(false); setWorking("");
    }
  };

  const loadAuto = async () => {
    try {
      setAuto(await autoBackupStatus());
    } catch (e) {
      setAutoFailure(failureOf(e, "Không đọc được trạng thái sao lưu tự động.").message);
    }
  };

  useEffect(() => { void loadAuto(); }, []);

  // Writes a new automatic backup on the server (same lock as export and restore), then refreshes the list.
  const runAuto = async () => {
    if (lock.current) return;
    lock.current = true; setBusy(true); setAutoRunning(true); setAutoFailure(""); setAutoResult("");
    try {
      const entry = await runAutoBackup();
      setAutoResult(`Đã sao lưu ngay: ${timeText(entry.created_utc)} (${entry.name}).`);
    } catch (e) {
      setAutoFailure(failureOf(e, "Không sao lưu được ngay.").message);
    } finally {
      lock.current = false; setBusy(false); setAutoRunning(false);
      await loadAuto();
    }
  };

  // Downloads one automatic backup as a file; restoring from it uses the existing file picker above.
  const fetchAuto = async (name: string) => {
    setAutoFailure(""); setAutoResult("");
    try {
      const blob = await downloadAutoBackup(name);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = name;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setAutoResult(`Đã tải ${name}.`);
    } catch (e) {
      setAutoFailure(failureOf(e, "Không tải được bản sao lưu tự động.").message);
    }
  };

  const newest = auto?.files[0];
  const statusLine = !auto
    ? (autoFailure ? "Chưa đọc được trạng thái sao lưu tự động." : "Đang đọc trạng thái sao lưu tự động…")
    : !auto.enabled ? "Sao lưu tự động đang tắt trên máy này."
    : newest ? `Bản gần nhất: ${timeText(newest.created_utc)} · đang giữ ${auto.files.length}/${auto.keep} bản.`
    : "Chưa có bản tự động nào.";

  return <section className="editor-card m2a-card backup-panel" aria-label="Sao lưu và khôi phục" data-testid="backup-panel">
    <h2>Sao lưu và khôi phục</h2>
    <p>Tải toàn bộ dữ liệu local (phương án đã lưu, revision dữ liệu hàng, hồ sơ tàu nhập) thành một tệp .scstbak. Khôi phục đọc tệp đó và thay toàn bộ dữ liệu hiện có.</p>
    <p className="backup-limits">{LIMITS}</p>
    <div className="backup-row">
      <button type="button" className="button secondary" disabled={busy} onClick={() => void download()}>{working === "export" ? "Đang chuẩn bị…" : "Tải bản sao lưu"}</button>
    </div>
    <div className="backup-row">
      <label className="backup-file">Khôi phục từ bản sao lưu<input ref={input} type="file" accept=".scstbak" aria-label="Khôi phục từ bản sao lưu" disabled={busy} onChange={(e) => void pick(e.target.files?.[0])} /></label>
    </div>
    {working === "check" && <p role="status">Đang kiểm bản sao lưu…</p>}
    {failure && <div className="backup-error" role="alert" data-testid="backup-error">
      <p>{failure.message}</p>
      {failure.errors.length > 0 && <ul aria-label="Lỗi bản sao lưu">{failure.errors.map((err, i) => <li key={i}>{err.field}: {err.message}</li>)}</ul>}
    </div>}
    {preview && file && <section className="backup-preview" aria-label="Tóm tắt bản sao lưu" data-testid="backup-preview">
      <p>Tệp: tạo lúc {timeText(preview.created_utc)} · mã SHA-256 {preview.backup_sha256.slice(0, 12)}…</p>
      <div className="backup-table-wrap">
        <table className="backup-table" aria-label="So sánh số lượng">
          <thead><tr><th>Dữ liệu</th><th>Trong bản sao lưu</th><th>Hiện tại</th></tr></thead>
          <tbody>
            <tr><th scope="row">Phương án đã lưu</th><td>{preview.counts.plans}</td><td>{preview.current.plans}</td></tr>
            <tr><th scope="row">Revision dữ liệu hàng</th><td>{preview.counts.revisions}</td><td>{preview.current.revisions}</td></tr>
            <tr><th scope="row">Phiên bản hồ sơ tàu</th><td>{preview.counts.vessel_profile_versions}</td><td>{preview.current.vessel_profile_versions}</td></tr>
          </tbody>
        </table>
      </div>
      <p className="backup-warning">{WARNING}</p>
      <button type="button" className="button primary" disabled={busy} onClick={() => void restore()}>Khôi phục</button>
    </section>}
    {result && <p role="status" data-testid="backup-result">{result}</p>}
    <section className="backup-auto" aria-label="Sao lưu tự động" data-testid="backup-auto">
      <h3>Sao lưu tự động</h3>
      <p data-testid="backup-auto-status">{statusLine}</p>
      {auto?.last_error && <p className="backup-error" role="alert" data-testid="backup-auto-last-error">Lần sao lưu gần nhất lỗi: {auto.last_error}</p>}
      <p className="backup-limits">{AUTO_NOTE}</p>
      <div className="backup-row">
        <button type="button" className="button secondary" disabled={busy || autoRunning} onClick={() => void runAuto()}>Sao lưu ngay</button>
      </div>
      {auto && auto.files.length > 0 && <ul aria-label="Các bản sao lưu tự động" style={{ listStyle: "none", padding: 0, margin: "8px 0" }}>
        {auto.files.slice(0, AUTO_LIST_MAX).map((f) => <li key={f.name} data-testid={`auto-backup-${f.name}`} className="backup-row" style={{ alignItems: "center", margin: "4px 0" }}>
          <span style={{ flex: "1 1 14rem", minWidth: 0, overflowWrap: "anywhere" }}>{timeText(f.created_utc)} · {sizeText(f.size_bytes)} · {f.name}</span>
          <button type="button" className="button secondary" disabled={busy || autoRunning} onClick={() => void fetchAuto(f.name)}>Tải</button>
        </li>)}
      </ul>}
      {autoResult && <p role="status" data-testid="backup-auto-result">{autoResult}</p>}
      {autoFailure && <p className="backup-error" role="alert" data-testid="backup-auto-error">{autoFailure}</p>}
    </section>
  </section>;
}
