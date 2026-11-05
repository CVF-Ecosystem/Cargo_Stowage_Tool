# SCST — M5b: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

- Người review là Claude local (root REVIEWER), không tham gia implement.
- PR: #8, nhánh `claude/m5b-auto-backup` (base `82f8356`, head `debafa6`). Không cần vòng sửa.
- Root merge theo quyền owner giao, sau khi chạy lại đầy đủ tại máy: `gh pr merge --merge --match-head-commit debafa6`, tạo merge commit `23a9395` trên `main`.
- Review chạy trong worktree riêng `../SCST_review_m5b`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | Kết quả |
|---|---|
| `python -m pytest` | **909 passed** (878 cũ và 31 test M5b) |
| `python tooling/export_contract.py` | Không có diff. Contract chỉ thêm ba endpoint `/api/backup/auto*` và model của chúng. |
| `npm ci`, `npm run contract`, `npm run build` | Đạt; `api.ts` chỉ khác EOL |
| Playwright toàn bộ (config gốc, cổng 8766, DB tạm) | **59 passed**: 57 ca cũ và 2 ca `m5b.spec.ts` |
| `git status` sau khi chạy browser | Sạch |
| `tooling/integration_check_pre_m2d.py` | 29/29 PASS |
| Gate `worker-return` / `reviewer-fast` | PASS 7/7, 8/8 |
| CI của PR | SUCCESS |

Phạm vi diff không đụng `services/backend/data`, `.cvf`, `scripts`, `.github`, specs/work orders, tooling, requirements/package, định dạng `scst.backup.v1` hay schema. Không sửa test cũ, không thêm dependency. Thay đổi ở `main.py` chỉ là hook khởi động, được work order cho phép.

### Kiểm độc lập của root trên NTFS

Script riêng gọi qua API, với `SCST_DATA_DIR` có dấu cách và tiếng Việt (`…\Dữ liệu thử\runtime data`):

| Bước | Kết quả |
|---|---|
| Khởi động app khi **chưa có dữ liệu** | Không tạo tệp hay thư mục nào |
| "Sao lưu ngay" khi chưa có dữ liệu | 409 "Chưa có dữ liệu để sao lưu."; không tạo gì |
| Lưu 2 phương án (một trong số đó là nhiều tầng 1076 vị trí), "Sao lưu ngay" | 200; tệp `auto-<UTC>.scstbak` không có dấu hai chấm; qua kiểm preview của M5a (2 phương án); không có đường dẫn tuyệt đối trong tệp |
| Tải bản tự động | 200, đúng tên tệp |
| 6 tên cố thoát thư mục hoặc sai mẫu (`..%2F`, `..\`, `scst.sqlite3`, URL mã hóa, tên đúng mẫu nhưng không tồn tại…) | Đều 404; phản hồi không chứa đường dẫn |
| 15 lần "Sao lưu ngay" liên tiếp | Còn đúng **10** bản, bản mới nhất được giữ; `backups/pre-restore-*` và một tệp lạ trong `backups/auto/` không bị xóa; không sót tệp `.auto-*.tmp` |
| Lưu thêm phương án thứ ba rồi khôi phục từ bản tự động bằng luồng M5a | 200; còn đúng 2 phương án ban đầu; các bản tự động vẫn còn nguyên (10) |
| Khởi động khi có dữ liệu và chưa có bản tự động | Hook nền tạo đúng **1** bản |
| Khởi động lần hai | Vẫn 1 bản (chưa đến 20 giờ) |
| `SCST_AUTO_BACKUP=0` | Không tạo bản khi khởi động; trạng thái `enabled: false` |

### Đọc code lõi

- **`backup_auto.py` (D1):**
  - Mọi thao tác dùng một khóa trong tiến trình. Hai lần chạy cùng lúc không tạo hai bản; `run_if_due` kiểm lại điều kiện 20 giờ bên trong khóa.
  - `has_data()` chỉ đọc, mở SQLite ở chế độ `mode=ro`, và `vstore.list_ids()` chỉ liệt kê thư mục. Tệp `vessels/.lock` rỗng của Windows không bị tính là hồ sơ tàu.
  - Ghi qua tệp tạm, `fsync`, rồi `os.link`; không bao giờ ghi đè (hậu tố `-1`, `-2`). Nếu hệ tệp không hỗ trợ liên kết cứng thì tạo độc quyền và sao chép.
  - Bản mới phải qua `backup_check.check` trước khi được tính là thành công; nếu không qua thì bị xóa.
  - Việc cắt bớt chỉ chạy **sau khi** bản mới thành công, chỉ chạm tệp khớp đúng mẫu tên, và không bao giờ xóa bản vừa tạo (kể cả khi đồng hồ bị lùi). Lỗi xóa bị nuốt.
  - `run_if_due` không bao giờ ném lỗi; lỗi được ghi ra `last_error` bằng một câu cố định không có đường dẫn.
  - Hook ở `main.py` chạy trong luồng nền kiểu daemon và bọc `try/except`, nên khởi động không bị chặn hay hỏng.
- **API (D2):** tên tệp phải khớp đúng `NAME_PATTERN` (dùng `fullmatch`) trước khi ghép đường dẫn. Mọi phản hồi chỉ có tên tệp. "Sao lưu ngay" chạy trong `run_in_threadpool`, nên không chặn vòng lặp sự kiện.
- **Giao diện (D3):** ảnh của worker cho thấy khối "Sao lưu tự động" có trạng thái bản gần nhất, danh sách có nút "Tải", nút "Sao lưu ngay" và ghi chú phạm vi (cùng máy, chưa chạy lịch khi app đóng, chưa mã hóa). Giờ hiển thị dùng múi giờ của trình duyệt, nên owner thấy giờ Việt Nam (ảnh hiện giờ UTC vì chụp trong container).

## Đối chiếu M5B-01..04

| ID | Kết luận | Căn cứ |
|---|---|---|
| M5B-01 | VERIFIED | Test cho từng nhánh D1 (đủ điều kiện, chưa đủ 20 giờ, không dữ liệu, tắt, giữ 10, bản được bảo vệ, bản mới lỗi, không ghi đè, đồng thời) cùng tiêm lỗi ở khởi động. Root xác nhận trên NTFS với đường dẫn có dấu cách và tiếng Việt. |
| M5B-02 | VERIFIED | Mỗi bản tự động qua `backup_check.check`; khôi phục từ bản tự động bằng luồng M5a trả lại đúng dữ liệu (root thử thật). |
| M5B-03 | VERIFIED | Danh sách, chạy ngay (có và không có dữ liệu) và tải đều đúng; 6 tên xấu trả 404; không lộ đường dẫn; contract chỉ thêm. |
| M5B-04 | VERIFIED | Giao diện và luồng đạt trong `m5b.spec.ts`, ở desktop và 390px; toàn bộ test cũ, kiểm tra tích hợp 29/29 và `docs/reviews/` không đổi khi chạy browser. |

## Quan sát còn mở (không chặn)

- **O-M5B-1:** nếu trong `backups/auto/` có tệp tên đúng mẫu nhưng ngày không hợp lệ (ví dụ tháng 13), `_parse` ném `ValueError` làm danh sách báo lỗi. Chỉ xảy ra khi có người đặt tay tệp như vậy; nên bắt lỗi và bỏ qua tệp đó ở lần chỉnh sau.
- **O-M5B-2:** bản tự động nằm cùng ổ với dữ liệu, nên không bảo vệ khi hỏng ổ hay mất máy. Giao diện đã nhắc owner cất một bản ra ngoài máy.
- **Ngoài phạm vi, thuộc tranche sau hay owner:** bộ cài (M5c), chạy theo lịch khi app đóng, mã hóa, bản sao ngoài máy.
