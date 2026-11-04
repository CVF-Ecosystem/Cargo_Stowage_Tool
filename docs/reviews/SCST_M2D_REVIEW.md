# SCST — M2d: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

- Người review là Claude local (root REVIEWER), không tham gia implement.
- PR: #4, nhánh `claude/m2d-report-export` (head `fb23c7d`, base `6883dfd`).
- Đêm 05-11 owner giao quyền: root (orchestrator) được merge trên GitHub sau review độc lập, và chủ động điều phối phiên kế tiếp. Root merge sau khi chạy lại đầy đủ tại máy.
- Review chạy trong worktree riêng `../SCST_review_m2d`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | Kết quả |
|---|---|
| `python -m pytest` | 650 passed |
| `python tooling/export_contract.py` | Không có diff so với contract đã commit. |
| `npm ci`, `npm run contract`, `npm run build` | Đạt. `api.ts` chỉ khác ở EOL. |
| Playwright toàn bộ (config gốc, cổng 8766, DB tạm) | 50 passed: 46 ca cũ và 4 ca `m2d.spec.ts`, kể cả `page.pdf()`. |
| `git status` sau khi chạy browser | Sạch. |
| `tooling/integration_check_pre_m2d.py` | 29/29 PASS |
| Gate `worker-return` | PASS, 7/7 |
| Gate `reviewer-fast` | PASS, 8/8 |
| CI của PR | SUCCESS |
| Vùng cấm | Không thay đổi: `services/backend/data`, `.cvf`, `scripts`, `.github`, specs, work orders, CVF_SESSION |
| Thư viện mới | Không có. XLSX ghi bằng `zipfile`/XML của thư viện chuẩn. Không tạo PDF ở server. |

## Kiểm riêng file XLSX

Root kiểm chặt file mẫu `sample-vinafco-baltimore-report.xlsx` bằng một script độc lập:

- zip nguyên vẹn;
- thứ tự phần tử sheet đúng schema (`dimension`, `sheetViews`, `sheetFormatPr`, `cols`, `sheetData`);
- dòng và ô tăng dần, tham chiếu ô khớp dòng;
- chỉ số style hợp lệ;
- số là số hữu hạn ≤ 2^53;
- không có ký tự điều khiển;
- tên sheet hợp lệ;
- `dimension` khớp dữ liệu (sheet Hàng là A1:AD1077).

Kết quả: **0 lỗi**.

**Chưa kiểm bằng Excel thật.** Excel có trên máy nhưng COM ở phiên không tương tác này lỗi ngay cả khi tự lưu một workbook do chính nó tạo (`0x800A03EC`), nên đây không phải bằng chứng file hỏng. **Việc cho owner:** mở `docs/reviews/SCST_M2D_EVIDENCE/sample-vinafco-baltimore-report.xlsx` bằng Excel và báo lại nếu Excel đòi sửa file.

## Đối chiếu D1–D5

- **D1:**
  - `scst.plan-report.v1` dẫn xuất thuần từ snapshot đã lưu, có `plan_sha256` và `report_sha256` (bỏ thời điểm tạo).
  - Đối soát nội bộ D1.5 (đếm, khối lượng, trùng `evaluate`) có ca lệch giả lập trả lỗi.
  - Đủ cảnh báo bắt buộc: chưa xác minh hình học, phương án một tầng, packing dẫn xuất, cần kiểm lại, cảnh báo nguồn.
- **D2:** `/api/snapshots/{id}/report` và `/report.xlsx` chỉ đọc. Tên file có bản ASCII và `filename*` UTF-8. Snapshot hoặc revision lỗi bị từ chối.
- **D3:**
  - 4 sheet đúng tên.
  - Cột hiển thị đi kèm cột chính xác g/mm/µm.
  - File tất định từng byte.
  - Có test 1076 và 2000 đơn vị; thời gian ghi trong worker return.
- **D4:**
  - Trang "Báo cáo" có:
    - cảnh báo nổi bật;
    - bảng tổng;
    - hình chiếu 2D SVG cùng vị trí;
    - ảnh 3D chụp từ viewer, có chú thích "ảnh minh họa";
    - các bảng hàng, chưa xếp, kiểm tra;
    - CSS in A4;
    - nút "In / Lưu PDF" và "Tải XLSX".
  - Không có WebGL thì có ghi chú thay ảnh. 390px không tràn ngang (đã xem ảnh).
- **D5:** Không có việc ngoài phạm vi bị làm.
- **Browser spec:** dùng một backend riêng ở cổng 8768 với `SCST_DATA_DIR` tạm cho luồng cần dữ liệu R0000 sạch. Không đụng cổng 8765 hay dữ liệu người dùng: chấp nhận.

## Quan sát (không chặn merge)

- **O10:** chưa kiểm XLSX bằng Excel thật (xem trên).
- **O11:** file bằng chứng mẫu (XLSX 122 KB, PDF 218 KB) được commit vào `docs/reviews`. Chấp nhận, vì work order cho phép.

## Kết luận

- M2D-01..M2D-05 đạt về kỹ thuật. Không có finding chặn và không cần sửa tại chỗ.
- Root merge theo quyền owner đã giao: `gh pr merge --merge --match-head-commit fb23c7d`, tạo merge commit `690fcc7` trên `main`.
- M2 đủ luồng nhập → gợi ý → xem/chỉnh → lưu/mở → xuất.
- Nghiệm thu nghiệp vụ nội dung báo cáo và M3 (nhiều tầng, hầm thực) thuộc owner.
