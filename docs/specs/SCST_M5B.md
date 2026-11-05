# SCST — M5b sao lưu tự động local

Status: APPROVED_FOR_EXECUTION

## Authority and design

M5a đóng ngày 05-11-2026 ([review](../reviews/SCST_M5A_REVIEW.md)): có sao lưu và khôi phục thủ công. Rủi ro còn lại là owner quên bấm sao lưu. App chạy khi owner mở, không chạy nền theo lịch, nên "tự động" ở đây có nghĩa là **tự sao lưu khi app khởi động** (nếu đã đủ lâu kể từ bản trước) và **sao lưu ngay khi bấm nút**.

Tên mốc: **M5b** là sao lưu tự động. **Bộ cài đặt** tách thành **M5c**, vì cần chạy thử trên Windows nên không giao cloud.

Thực hiện:

- Claude Cloud làm IMPLEMENTATION_WORKER.
- Claude local làm REVIEWER độc lập và merge theo quyền owner đã giao.
- Risk R2.

Các nguyên tắc DA áp dụng:

- **DA02:** dữ liệu hiện có không bao giờ mất hay đổi; định dạng lưu trữ không đổi; sao lưu tự động không bao giờ làm app không khởi động được.
- **DA03:** ghi rõ chưa có lịch chạy nền, mã hóa, bản sao ngoài máy.
- **DA04:** tái dùng `backup_export.write_archive`, `backup_check.check` và định dạng `scst.backup.v1` của M5a.
- **DA05:** có luồng dùng được trên giao diện.

### D1. Sao lưu tự động

D1.1. Mô-đun `adapters/backup_auto.py`. Bản tự động nằm ở `<SCST_DATA_DIR>/backups/auto/auto-<UTC>.scstbak`, đúng định dạng `scst.backup.v1`. Không đổi gì ở định dạng, schema hay `backup_export`/`backup_check` ngoài việc tái dùng.

D1.2. **Điều kiện chạy khi khởi động:**

- App chạy `run_if_due()` ở một luồng nền khi khởi động; không chặn việc khởi động.
- Mọi lỗi bị nuốt, ghi vào trạng thái `last_error` bằng một lời tiếng Việt cố định, không chứa đường dẫn.
- Chỉ sao lưu khi **có dữ liệu**: DB đã tồn tại và có ít nhất một phương án hoặc một revision, hoặc có ít nhất một hồ sơ tàu.
- Chỉ sao lưu khi bản tự động gần nhất **cũ hơn 20 giờ**, hoặc chưa có bản nào.
- Không tạo DB, thư mục `vessels` hay bất kỳ tệp dữ liệu nào chỉ vì sao lưu.
- Biến môi trường `SCST_AUTO_BACKUP=0` tắt sao lưu khi khởi động. Nút "Sao lưu ngay" vẫn dùng được.

D1.3. **Ghi bản sao lưu:**

- Ghi qua tệp tạm, `fsync`, rồi đưa vào tên cuối, không bao giờ ghi đè.
- Chỉ tính là thành công khi bản mới qua `backup_check.check`.
- Nếu không qua, xóa bản mới và báo lỗi.

D1.4. **Giữ tối đa 10 bản tự động:**

- Sau khi bản mới thành công, xóa các bản tự động cũ nhất ngoài 10 bản.
- Không bao giờ xóa `pre-restore-*`, bản thủ công hay bất kỳ tệp nào không khớp mẫu `auto-<UTC>.scstbak`.
- Khi bản mới thất bại, không xóa gì.

D1.5. **Đồng thời:**

- Dùng một khóa trong tiến trình để không chạy hai lần cùng lúc.
- Không giữ khóa kho hồ sơ lâu hơn `backup_export` hiện có.

### D2. API

Chỉ thêm endpoint, không đổi endpoint cũ. API chỉ trả **tên tệp**, không bao giờ trả đường dẫn.

- `GET /api/backup/auto` trả:
  - `enabled`;
  - `interval_hours` (20);
  - `keep` (10);
  - `files`: danh sách `{name, created_utc, size_bytes}`, mới nhất trước;
  - `last_error`: chuỗi hoặc null.
- `POST /api/backup/auto/run` chạy ngay, bỏ qua điều kiện "cũ hơn 20 giờ" nhưng vẫn cần có dữ liệu.
  - Trả bản vừa tạo.
  - Khi không có dữ liệu thì trả lỗi 409 với lời tiếng Việt.
- `GET /api/backup/auto/{name}` tải một bản.
  - `name` phải khớp đúng mẫu `auto-<UTC>.scstbak`.
  - Mọi tên khác, gồm `..`, `/`, `\` hay tên khác mẫu, trả 404.

### D3. Giao diện

D3.1. Trong mục "Sao lưu và khôi phục" thêm khối "Sao lưu tự động":

- Dòng trạng thái: bản gần nhất lúc nào, đang giữ bao nhiêu bản, `last_error` nếu có.
- Danh sách tối đa 10 bản, mỗi bản có nút "Tải".
- Nút "Sao lưu ngay".
- Ghi chú: "Bản tự động nằm cùng máy với dữ liệu. Hãy tải một bản và cất ra ngoài máy (USB, ổ mạng). Chưa có sao lưu theo lịch khi app đang đóng, chưa mã hóa."

D3.2. Khôi phục từ một bản tự động dùng luồng khôi phục hiện có: tải bản về rồi chọn tệp. Không thêm nút khôi phục mới.

D3.3. Dùng được ở 390px. Sinh lại `contracts/openapi.json` và `api.ts`.

### D4. Ngoài phạm vi M5b

- Bộ cài (M5c).
- Chạy theo lịch khi app đang đóng.
- Mã hóa.
- Bản sao ngoài máy hay đồng bộ đám mây.
- Đổi số lượng giữ lại hay chu kỳ trên giao diện.
- Đổi định dạng sao lưu.

## M5b acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| M5B-01 | Logic theo D1. Test cho từng nhánh: đủ điều kiện, chưa đủ 20 giờ, không có dữ liệu (không tạo gì), tắt bằng `SCST_AUTO_BACKUP=0`, giữ tối đa 10 và xóa đúng bản cũ nhất, không xóa `pre-restore-*` hay bản thủ công, bản mới lỗi thì không xóa gì, không ghi đè, hai lần chạy đồng thời chỉ tạo một bản. Khởi động app không bị chặn hay lỗi khi sao lưu thất bại (tiêm lỗi). |
| M5B-02 | Mỗi bản tự động qua `backup_check.check`; xuất bản tự động rồi khôi phục bằng luồng M5a trả đúng từng byte các hàng `snapshots`, `cargo_revisions` và các tệp `vessels/**`. |
| M5B-03 | API theo D2: danh sách, chạy ngay (có và không có dữ liệu), tải; tên tệp sai hoặc cố thoát thư mục trả 404; không đường dẫn nào lộ trong phản hồi hay lỗi. Contract chỉ thêm. |
| M5B-04 | Giao diện theo D3 và luồng: lưu một phương án → "Sao lưu ngay" → bản hiện trong danh sách → tải về → lưu thêm phương án thứ hai → khôi phục từ tệp đã tải → chỉ còn phương án đầu. Dùng được ở 390px. Mọi test backend và browser cũ đạt; `tooling/integration_check_pre_m2d.py` 29/29; chạy browser không đổi tệp đã commit dưới `docs/reviews/`. |

## Verification and checkpoint

Mốc: `main` tại `f4c02fa`, có 878 test backend và 57 ca browser.

Worker phải:

- chạy toàn bộ test backend;
- sinh lại contract và kiểu TypeScript;
- chạy `npm run build`;
- viết `tests/browser/m5b.spec.ts`;
- chạy toàn bộ browser suite, kịch bản tích hợp và gate worker-return.

Lưu ý Windows: root review trên Windows/NTFS. Mọi tên tệp dùng dấu thời gian không có dấu hai chấm, đường dẫn thử có dấu cách và tiếng Việt, và không giữ kết nối SQLite mở khi thay đổi tệp.

Ngân sách: worker 70 phút trên cloud, root review 45 phút, không reset khi sửa.
