# SCST — M5a: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

- Người review là Claude local (root REVIEWER), không tham gia implement.
- PR: #7, nhánh `claude/m5a-backup-restore` (base `3396555`).
  - Vòng 0 review tại head `7475718`.
  - Vòng sửa review tại head `2883456`, rồi `9d34d3a`.
- Root merge theo quyền owner giao, sau khi chạy lại đầy đủ tại máy: `gh pr merge --merge --match-head-commit 9d34d3a`, tạo merge commit `9c9cdb5` trên `main`.
- Review chạy trong worktree riêng `../SCST_review_m5a`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | `7475718` | `2883456` | `9d34d3a` (merge) |
|---|---|---|---|
| `python -m pytest` | 797 passed, 3 failed, 67 errors (chỉ test M5a, xem R3) | 875 passed, 1 failed (xem R4) | **878 passed** |
| `python tooling/export_contract.py` | Không có diff | Không có diff | Không đổi (R4 chỉ sửa test) |
| `npm ci`, `npm run contract`, `npm run build` | Đạt | Đạt | Không đổi |
| Playwright toàn bộ (config gốc, cổng 8766, DB tạm) | 57 passed: 55 ca cũ và 2 ca `m5a.spec.ts` | 57 passed | Không đổi |
| `git status` sau khi chạy browser | Sạch | Sạch | — |
| `tooling/integration_check_pre_m2d.py` | 29/29 PASS | 29/29 PASS | — |
| Gate `worker-return` / `reviewer-fast` | PASS 7/7, 8/8 | PASS 7/7, 8/8 | PASS 7/7, 8/8 |
| CI của PR | SUCCESS | SUCCESS | SUCCESS |

Phạm vi diff không đụng `services/backend/data`, `.cvf`, `scripts`, `.github`, specs/work orders, tooling, requirements/package, định dạng lưu trữ hay schema. Không sửa test cũ. Không thêm dependency, chỉ dùng stdlib `zipfile`, `hashlib`, `sqlite3`. Contract chỉ thêm ba endpoint `/api/backup/*` và các model của chúng.

### Kiểm độc lập của root trên NTFS

Script riêng gọi qua API, với `SCST_DATA_DIR` có dấu cách và tiếng Việt (`…\Dữ liệu thử\runtime data`), giống đường dẫn thật của owner:

| Bước | Kết quả tại `2883456` |
|---|---|
| Lưu 2 phương án (một tầng; nhiều tầng Baltimore 1076 vị trí), xuất | 200, tệp `scst-backup-YYYYMMDD-HHMMSS.scstbak`; không có đường dẫn tuyệt đối nào trong archive |
| Lưu thêm phương án thứ ba, preview | 200; trong tệp 2 phương án, hiện tại 3 |
| Khôi phục khi đang có một kết nối SQLite mở trên DB thật | 400 "Khôi phục thất bại; dữ liệu hiện tại đã được giữ nguyên"; mọi tệp dữ liệu giữ nguyên byte, không sót `.lock` |
| `confirm` sai | 409, dữ liệu giữ nguyên byte |
| Khôi phục thật | 200; còn đúng 2 phương án; phương án nhiều tầng mở lại là `COLUMNS_V1`, 1076 vị trí, `RULES_CHECKED` |
| Bản sao lưu trước khôi phục | Preview được, chứa đủ 3 phương án |
| Thư mục làm việc `.restore-*` | Không còn sót |

Tại `7475718` script cũng đạt các bước trên. Riêng ca khôi phục bị từ chối thì để lại một tệp rỗng `vessels/.lock`, vì thư mục `vessels` do chính lần gọi đó tạo ra; R3 đã sửa.

### Đọc code lõi

- **`backup_check.py` (D2):**
  - Đọc ZIP theo luồng và đếm byte giải nén thật, không tin header; có danh sách tên được phép; chặn symlink, mục mã hóa, tên trùng không phân biệt hoa thường.
  - Manifest phải khớp tập tệp, `size` và `sha256`.
  - SQLite mở chỉ đọc; `integrity_check`; chặn đối tượng lạ trong DB; cấu trúc bảng phải đúng như `storage`.
  - `Plan.model_validate` cho từng phương án; revision phát lại bằng `cr.replay`; hồ sơ tàu kiểm bằng `vstore.read(base=…)` và `validate_profile`. Thay đổi duy nhất ở kho hồ sơ là thêm tham số `base` tùy chọn.
- **`backup_restore.py` (D3):**
  - Ghi nhật ký mỗi lần di chuyển trước khi làm; hoàn tác theo thứ tự ngược, có kiểm tồn tại.
  - Giữ khóa trong luồng xử lý và khóa liên tiến trình của kho hồ sơ suốt thao tác.
  - Không đổi tên chính thư mục `vessels`, vì trên Windows tệp `.lock` của nó đang mở; chỉ di chuyển các mục con.
  - Bản sao lưu trước khôi phục ghi qua tệp tạm, rồi `os.link` hoặc tạo độc quyền, không bao giờ ghi đè.
  - Xóa cache phát lại của HARDEN-01 cả khi thành công lẫn khi thất bại.

## Vòng sửa (gửi qua comment PR, cùng ngân sách, không reset; cả bốn mục do Haiku 5.5 high làm)

- **R1, D1.2:** khi xuất lỗi, API trả một lời cố định, không chèn nội dung exception (vốn có thể chứa đường dẫn). Có test tiêm `OSError` chứa đường dẫn.
- **R2:** preview và apply chạy qua `run_in_threadpool`; hành vi, mã trạng thái và contract giữ nguyên.
- **R3, chỉ xảy ra trên Windows:** khóa `msvcrt` tạo tệp `vessels/.lock`; trên Linux là `flock` trên thư mục nên không có tệp. Container cloud vì vậy không thấy lỗi.
  - Test M5a khi liệt kê tệp chỉ loại đúng `vessels/.lock`.
  - Khi `apply()` tự tạo `vessels/` thì dọn lại thư mục đó cùng tệp `.lock` rỗng sau khi nhả khóa, cả khi thành công lẫn thất bại. Có test giả lập bố cục Windows để Linux cũng chạy nhánh này.
- **R4, chỉ sửa test:** trên Windows, `zipfile` của CPython đổi `\` thành `/` khi đọc tên mục, nên kiểm dấu gạch ngược không được chạm tới. Mục vẫn bị từ chối.
  - Test chỉ kiểm lời "gạch ngược" khi `os.sep == '/'`; mọi nền tảng đều kiểm bị từ chối và không có gì ghi ra ngoài thư mục làm việc.
  - Thêm test `..\..\evil` và `C:\evil` bị từ chối trên mọi nền tảng.
  - Root kiểm an toàn trên Windows: `..\` thành `../` bị kiểm `..` chặn, `C:\` bị kiểm ổ đĩa chặn.

## Đối chiếu M5A-01..05

| ID | Kết luận | Căn cứ |
|---|---|---|
| M5A-01 | VERIFIED | Manifest đúng `size`/`sha256`; DB chép bằng `sqlite3.backup`; vòng xuất rồi khôi phục giữ nguyên byte các hàng và tệp `vessels/**` (test của worker); không có đường dẫn tuyệt đối (root kiểm trên NTFS); DB rỗng vẫn xuất được. |
| M5A-02 | VERIFIED | Mỗi trường hợp D2.1–D2.5 có test riêng; preview không ghi gì; dữ liệu hiện tại giữ nguyên byte. Có thêm ca thoát thư mục trên mọi nền tảng (R4). |
| M5A-03 | VERIFIED | `confirm` sai trả 409; bản sao lưu trước khôi phục mở lại được; tiêm lỗi ở từng bước giữ nguyên byte (ma trận trong worker return); root kiểm rollback thật trên NTFS khi có kết nối mở; cache được xóa; khóa tuần tự. |
| M5A-04 | VERIFIED | Mục "Sao lưu và khôi phục": tải bản sao lưu, chọn tệp, preview, cảnh báo, khôi phục, nạp lại; lỗi tiếng Việt; ghi chú phạm vi (DA03); chạy được ở 390px; contract và `api.ts` đã sinh lại. |
| M5A-05 | VERIFIED | Luồng 2 phương án → sao lưu → phương án thứ ba → khôi phục → còn 2, mở đúng nội dung → bản trước khôi phục chứa 3. Đạt trong `m5a.spec.ts` và trong script của root. Toàn bộ test cũ đạt; kiểm tra tích hợp 29/29; `docs/reviews/` không đổi khi chạy browser. |

Nghiệm thu nghiệp vụ không áp dụng cho tính năng hạ tầng này; owner dùng thử như một phần của MVP.

## Quan sát còn mở (không chặn)

- **O-M5A-1:** khung lỗi trên giao diện lặp lại cùng một câu, ở dòng tiêu đề và ở mục danh sách.
- **O-M5A-2:** một lần lưu phương án chạy song song với khôi phục được an toàn trên Windows, vì Windows không cho thay tệp đang mở nên khôi phục bị từ chối và hoàn tác. Trên POSIX, lần lưu đó có thể ghi vào DB cũ đã bị đưa sang chỗ khác. App chỉ chạy local, một người dùng; ghi nhận để xét khi có bộ cài (M5b).
- **Ngoài phạm vi, thuộc owner hoặc tranche sau:** sao lưu tự động theo lịch, mã hóa, khôi phục gộp, bộ cài.
