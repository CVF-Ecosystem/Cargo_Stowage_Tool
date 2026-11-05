# SCST — HARDEN-01: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

- Người review là Claude local (root REVIEWER), không tham gia implement.
- PR: #5, nhánh `claude/harden-01` (head `88c4fb6`, base `11dacda`).
- Root merge theo quyền owner giao đêm 05-11, sau khi chạy lại đầy đủ tại máy: `gh pr merge --merge --match-head-commit 88c4fb6`, tạo merge commit `c8b9c1c` trên `main`.
- Lần chạy đầu của worker chạm giới hạn sử dụng 5 giờ ngay khi khởi động, không làm được gì. Root hẹn chạy lại sau khi giới hạn reset; lần đó worker commit theo từng mốc.
- Review chạy trong worktree riêng `../SCST_review_h01`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | Kết quả |
|---|---|
| `python -m pytest` | 679 passed |
| Test khóa liên tiến trình H5 trên Windows thật | 5/5 passed, gồm hai test hai tiến trình chạy bằng `msvcrt`. |
| `python tooling/export_contract.py` | Không có diff. openapi chỉ thêm `placed_dropped_on_rebase_count`. |
| `npm ci`, `npm run contract`, `npm run build` | Đạt. |
| Playwright toàn bộ (config gốc, cổng 8766, DB tạm) | 52 passed: 50 ca cũ và 2 ca `harden01.spec.ts`. |
| `git status` sau khi chạy browser | Sạch. |
| `tooling/integration_check_pre_m2d.py` | 29/29 PASS |
| Gate `worker-return` | PASS, 7/7 |
| Gate `reviewer-fast` | PASS, 8/8 |
| CI của PR | SUCCESS |
| Test cũ | Không file test hay browser spec cũ nào bị sửa. Các test toàn vẹn SUP-02A đạt nguyên trạng. |

## Đối chiếu H1–H6

- **H1:**
  - Tạo `RebaseDropped.tsx`: danh sách vị trí bị bỏ chia trang 50 dòng, có tổng số và lọc Bỏ/Đổi.
  - Đã kiểm với 130 vị trí bị bỏ, ở cả desktop và 390px.
- **H2:**
  - Thêm `placed_dropped_on_rebase_count`, dùng chung hàm `_drop_reason` với `rebase`, nên một quy tắc duy nhất quyết định vị trí nào bị bỏ.
  - Có test chứng minh số này bằng số vị trí `rebase` thật sự bỏ.
  - Về nhãn, worker giữ nguyên chuỗi cũ "… N bó đã đặt bị ảnh hưởng" vì hai spec cũ không được sửa có kiểm đúng chuỗi đó, rồi giải thích ngay sau. Root chấp nhận vì cách này giữ hành vi cũ.
- **H3:**
  - Bộ nhớ đệm LRU tối đa 8 mục, khóa bằng SHA-256 của toàn bộ dòng thô (gồm cả `created_utc` và `parent_revision_id`).
  - Mỗi request vẫn đọc DB. View trả ra là bản sao, nên sửa view không làm bẩn bộ nhớ đệm. Lỗi toàn vẹn được nhớ lại và báo đúng revision.
  - Sửa tay DB sau khi đã cache vẫn bị phát hiện (có test).
  - Đo được: danh sách phương án 260 → 77 ms, bind 128 → 43 ms (20 revision).
- **H4:**
  - Một lớp route đọc thân yêu cầu trước khi parse: `Content-Length` lớn hơn 1 MiB bị từ chối ngay; không có thì đọc theo luồng và dừng khi vượt.
  - Thân không phải JSON mà quá lớn nay trả 400 lỗi kích thước (trước đây là 422 parse). Đây là hành vi SPEC yêu cầu.
  - Endpoint profile tàu vốn đã từ chối trước khi parse; nay có test giữ nguyên.
- **H5:**
  - POSIX dùng `flock` như cũ. Windows dùng `msvcrt.locking` trên `vessels/.lock`, thử lại tối đa 60 giây rồi báo "Kho hồ sơ tàu đang bận", và luôn mở khóa.
  - `.lock` không bị liệt kê thành profile.
- **H6:** Không làm việc nào ngoài phạm vi.

## Kết luận

- H-01..H-05 đạt về kỹ thuật. Không có finding chặn và không cần sửa tại chỗ.
- Các quan sát O2, O4, O5, O6 cùng quyết định 2 của review SUP-02A đã xử lý xong.
- Còn mở:
  - O3 (provenance trong hash);
  - chính sách OD-only recheck;
  - kiểm XLSX bằng Excel thật;
  - M3 cần dữ liệu owner.
