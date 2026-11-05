# SCST — M5a sao lưu và khôi phục dữ liệu local

Status: APPROVED_FOR_EXECUTION

## Authority and design

M3a đóng ngày 05-11-2026 ([review](../reviews/SCST_M3A_REVIEW.md)): MVP xếp nhiều tầng được giao owner dùng thử. Khi owner bắt đầu nhập và lưu dữ liệu thật vào máy, khoảng trống lớn nhất còn lại không cần dữ liệu owner là **an toàn dữ liệu local**.

Hiện chưa có cách nào để:

- chép toàn bộ phương án đã lưu, revision dữ liệu hàng và hồ sơ tàu sang chỗ khác;
- khôi phục lại khi máy hỏng, cài lại, hoặc lỡ thao tác sai.

Đã có sẵn:

- **SQLite:** `<SCST_DATA_DIR>/scst.sqlite3`, gồm bảng `snapshots` và `cargo_revisions`, có kiểm schema trong `adapters/storage.py`.
- **Hồ sơ tàu:** `<SCST_DATA_DIR>/vessels/<id>/v<n>/{profile.json, model.glb, manifest.json}`.
  - Chỉ ghi thêm, không ghi đè.
  - Có khóa liên tiến trình trong `adapters/vessel_profile_store.py` (flock / `msvcrt`).

M5 trong roadmap tổng gồm bộ cài và sao lưu. **M5a** chỉ là phần sao lưu và khôi phục, làm được ngay, không cần dữ liệu owner.

Thực hiện:

- Claude Cloud làm IMPLEMENTATION_WORKER.
- Claude local làm REVIEWER độc lập và merge theo quyền owner đã giao.
- Risk R2.

Các nguyên tắc DA áp dụng:

- **DA02:** dữ liệu hiện có không bao giờ mất hay bị đổi khi thao tác lỗi. Định dạng lưu trữ không đổi.
- **DA03:** ghi rõ những gì chưa có: sao lưu tự động theo lịch, mã hóa, khôi phục gộp.
- **DA04:** tái dùng kiểm schema, `Plan.model_validate`, kiểm hồ sơ tàu và khóa hiện có.
- **DA05:** phải có luồng dùng được trên giao diện.

### D1. Tệp sao lưu `scst.backup.v1`

D1.1. Mỗi tệp sao lưu là một ZIP (stdlib `zipfile`), phần mở rộng `.scstbak`, gồm:

- `manifest.json`, chứa:
  - `format: "scst.backup.v1"`;
  - `created_utc`;
  - số phương án, số revision, số phiên bản hồ sơ tàu;
  - danh sách mọi tệp kèm `size` và `sha256`.
- `scst.sqlite3`: bản chép nhất quán bằng `sqlite3.Connection.backup`, không chép tệp đang mở.
- `vessels/**`: toàn bộ hồ sơ tàu người dùng, chép trong khi giữ khóa của kho hồ sơ.

D1.2. Không đưa vào tệp sao lưu:

- `services/backend/data/**`;
- mã nguồn;
- các tệp `.bak` hay `.tmp`;
- bất kỳ đường dẫn tuyệt đối nào.

API không bao giờ trả đường dẫn hệ thống tệp.

D1.3. `GET /api/backup/export` trả tệp sao lưu với tên `scst-backup-YYYYMMDD-HHMMSS.scstbak` (giờ UTC). Khi DB chưa có thì vẫn xuất được một bản sao lưu rỗng hợp lệ.

### D2. Kiểm tệp sao lưu trước khi khôi phục

`POST /api/backup/restore/preview` nhận thân yêu cầu là tệp `.scstbak`. Endpoint chỉ đọc, không ghi gì.

Giới hạn riêng, kiểm cả trước khi đọc hết thân:

- tối đa 256 MiB;
- tối đa 20 000 mục;
- tổng kích thước giải nén tối đa 1 GiB.

Phải từ chối, kèm lời tiếng Việt, khi:

- **D2.1.** ZIP hỏng, hoặc có mục với đường dẫn tuyệt đối, `..`, ký tự ổ đĩa, symlink, tên trùng, hay tệp ngoài danh sách cho phép (zip-slip và zip-bomb).
- **D2.2.** Thiếu `manifest.json`, sai `format`, hoặc `size`/`sha256` của bất kỳ tệp nào không khớp.
- **D2.3.** SQLite không qua `PRAGMA integrity_check`, hoặc cấu trúc bảng khác đúng cấu trúc mà `storage._prepare` chấp nhận.
- **D2.4.** Một phương án bất kỳ không qua `Plan.model_validate`, hoặc revision dữ liệu hàng không qua kiểm phát lại hiện có (chuỗi cha–con, `content_sha256`).
- **D2.5.** Một phiên bản hồ sơ tàu bất kỳ không qua kiểm đọc hiện có của kho hồ sơ (manifest, sha256 của `profile.json` và `model.glb`).

Kết quả preview gồm:

- số phương án, revision và hồ sơ tàu trong tệp, so với dữ liệu hiện tại;
- thời điểm tạo tệp;
- `backup_sha256` (sha256 của toàn bộ tệp) để làm mã xác nhận.

### D3. Khôi phục

D3.1. `POST /api/backup/restore/apply?confirm=<backup_sha256>` nhận lại đúng tệp đó.

- `confirm` không khớp sha256 của thân yêu cầu thì từ chối.
- Kiểm lại toàn bộ D2 trước khi làm gì.

D3.2. Chế độ duy nhất là **thay toàn bộ**: DB và thư mục `vessels` hiện có được thay bằng nội dung của tệp sao lưu. Khôi phục gộp nằm ngoài phạm vi.

D3.3. Trước khi thay, tự động tạo bản sao lưu dữ liệu hiện tại:

- vị trí `<SCST_DATA_DIR>/backups/pre-restore-<UTC>.scstbak`, cùng định dạng D1;
- không bao giờ ghi đè một tệp đã có.

D3.4. Thay theo kiểu nguyên tử và có hoàn tác:

- giải nén và kiểm vào một thư mục tạm trong `SCST_DATA_DIR`;
- giữ khóa của kho hồ sơ trong suốt thao tác;
- đóng mọi kết nối SQLite trước khi thay;
- thay `scst.sqlite3` bằng `os.replace`;
- đổi tên thư mục `vessels` cũ sang chỗ tạm rồi đưa thư mục mới vào.

Lỗi ở **bất kỳ bước nào** phải đưa dữ liệu hiện tại về đúng từng byte như trước. Test phải tiêm lỗi vào từng bước để chứng minh. Thư mục tạm được dọn dẹp.

D3.5. Sau khi thay xong:

- các API hiện có (danh sách phương án, mở phương án, revision, hồ sơ tàu) đọc dữ liệu mới mà không cần khởi động lại;
- cache phát lại của HARDEN-01 không được trả dữ liệu cũ.

### D4. Giao diện

D4.1. Thêm mục "Sao lưu và khôi phục" vào khu lưu và mở phương án hiện có:

- nút "Tải bản sao lưu";
- ô chọn tệp "Khôi phục từ bản sao lưu".

Sau khi chọn tệp, giao diện hiện:

- tóm tắt preview;
- cảnh báo "Toàn bộ dữ liệu hiện có sẽ được thay bằng bản sao lưu; một bản sao lưu dữ liệu hiện tại sẽ được tạo tự động trước khi thay.";
- nút "Khôi phục".

Lỗi kiểm hiện bằng lời tiếng Việt và không thay đổi gì.

D4.2. Sau khi khôi phục, danh sách phương án đã lưu và hồ sơ tàu được nạp lại. Bản nháp chưa lưu đang mở trong tab được giữ, có thông báo rằng nó chưa thuộc dữ liệu đã khôi phục.

D4.3. Dùng được ở 390px. Sinh lại `contracts/openapi.json` và `api.ts`.

### D5. Ngoài phạm vi M5a

- Sao lưu tự động theo lịch.
- Khôi phục gộp hoặc chọn từng phần.
- Mã hóa hoặc mật khẩu.
- Đồng bộ đám mây.
- Bộ cài.
- Xóa phương án hay hồ sơ tàu.
- Đổi định dạng lưu trữ hay schema.

## M5a acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| M5A-01 | Xuất theo D1: manifest đúng size/sha256; bản chép DB nhất quán, kể cả khi có ghi đồng thời; không có đường dẫn tuyệt đối hay tệp ngoài danh sách; xuất rồi khôi phục cho các hàng `snapshots`, `cargo_revisions` và tệp `vessels/**` giống hệt từng byte; DB rỗng vẫn xuất được. |
| M5A-02 | Kiểm theo D2: mỗi trường hợp từ chối D2.1–D2.5 có test riêng (zip-slip, zip-bomb, vượt giới hạn, sha256 lệch, sai format, SQLite hỏng, sai schema, phương án không hợp lệ, chuỗi revision gãy, hồ sơ tàu hỏng); preview không ghi gì và dữ liệu hiện tại giữ nguyên byte. |
| M5A-03 | Khôi phục theo D3: `confirm` sai bị từ chối; bản sao lưu trước khôi phục được tạo và mở lại được; tiêm lỗi ở từng bước thay đều để lại dữ liệu hiện tại giữ nguyên byte; sau khi khôi phục, các API đọc dữ liệu mới, cache không trả dữ liệu cũ; thao tác ghi hồ sơ đồng thời được khóa tuần tự. |
| M5A-04 | Giao diện theo D4: tải bản sao lưu, chọn tệp, preview, cảnh báo, khôi phục, nạp lại; lỗi hiện tiếng Việt; dùng được ở 390px; `contracts/openapi.json` và `api.ts` sinh lại. |
| M5A-05 | Luồng: lưu hai phương án (một nhiều tầng) và một revision → tải sao lưu → lưu thêm phương án thứ ba → khôi phục → chỉ còn hai phương án ban đầu, mở được và đúng nội dung → bản sao lưu trước khôi phục chứa cả ba. Mọi test backend và browser cũ đạt; `tooling/integration_check_pre_m2d.py` 29/29; chạy browser không đổi tệp đã commit dưới `docs/reviews/`. |

## Verification and checkpoint

Mốc: `main` sau khi đóng M3a, có 734 test backend và 55 ca browser.

Worker phải:

- chạy toàn bộ test backend;
- sinh lại contract và kiểu TypeScript;
- chạy `npm run build`;
- viết `tests/browser/m5a.spec.ts`;
- chạy toàn bộ browser suite, kịch bản tích hợp và gate worker-return.

Root review tại máy Windows, gồm test thay tệp thật trên NTFS (Windows không cho thay tệp đang mở).

Ngân sách: worker 150 phút trên cloud, root review 60 phút, không reset khi sửa.
