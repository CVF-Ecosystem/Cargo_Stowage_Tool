import { useEffect, useState } from "react";
import type { RebaseResult } from "../api/client";
import { formatCm } from "./model";

const PAGE_SIZE = 50;
type DropFilter = "ALL" | "REMOVED" | "CHANGED";

export default function RebaseDropped({ result, name }: { result: RebaseResult; name: string }) {
  const [filter, setFilter] = useState<DropFilter>("ALL");
  const [page, setPage] = useState(0);
  useEffect(() => { setFilter("ALL"); setPage(0); }, [result]);

  const dropped = result.dropped_placements;
  const total = dropped.length;
  const removedCount = dropped.filter(d => d.reason === "REMOVED").length;
  const changedCount = dropped.filter(d => d.reason === "CHANGED").length;
  const rows = filter === "ALL" ? dropped : dropped.filter(d => d.reason === filter);
  const count = rows.length;
  const pages = Math.max(1, Math.ceil(count / PAGE_SIZE));
  const current = Math.min(page, pages - 1);
  const start = current * PAGE_SIZE;
  const end = Math.min(count, start + PAGE_SIZE);
  const visible = rows.slice(start, end);

  if (total === 0) return <p>Không có vị trí nào bị bỏ.</p>;

  return (
    <div className="rebase-dropped-body" role="group" aria-label={`Vị trí bị bỏ của ${name}`}>
      <label className="rebase-dropped-filter">
        <span>Lọc vị trí bị bỏ</span>
        <select aria-label="Lọc vị trí bị bỏ" value={filter} onChange={e => { setFilter(e.target.value as DropFilter); setPage(0); }}>
          <option value="ALL">{`Tất cả (${total})`}</option>
          <option value="REMOVED">{`Bỏ (${removedCount})`}</option>
          <option value="CHANGED">{`Đổi (${changedCount})`}</option>
        </select>
      </label>
      {count === 0 ? <p>Không có vị trí nào theo bộ lọc.</p> : <>
        <ul data-testid="rebase-dropped-list">
          {visible.map((d, i) => <li key={`${d.unit_id}-${start + i}`} data-testid="rebase-dropped-item"><strong>{d.unit_id}</strong> · {d.reason === "REMOVED" ? "Bỏ" : "Đổi"} · vị trí cũ {formatCm(d.x_mm)}, {formatCm(d.y_mm)} cm · {d.yaw_deg}°</li>)}
        </ul>
        <p className="rebase-dropped-page" data-testid="rebase-dropped-page">{`Trang ${current + 1}/${pages} · dòng ${start + 1}–${end} trên tổng ${count}`}</p>
        {count > PAGE_SIZE && <div className="rebase-dropped-pager">
          <button type="button" className="button secondary" onClick={() => setPage(current - 1)} disabled={current === 0}>Trang vị trí trước</button>
          <button type="button" className="button secondary" onClick={() => setPage(current + 1)} disabled={current >= pages - 1}>Trang vị trí sau</button>
        </div>}
      </>}
    </div>
  );
}
