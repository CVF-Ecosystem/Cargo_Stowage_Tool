# SCST — HARDEN-01 gia cố sau SUP-02/03 (không cần dữ liệu owner)

Status: APPROVED_FOR_EXECUTION

## Authority and design

Đêm 05-11-2026 owner cho phép root (orchestrator) merge trên GitHub sau review độc lập và tự điều phối phiên kế tiếp. M3 cần số đo hầm và case thực của owner nên chưa mở. Root chọn một tranche gia cố, gom các quan sát đã ghi trong review SUP-02A, SUP-02B và SUP-03 mà không cần dữ liệu mới.

- Thực hiện: Claude Cloud làm IMPLEMENTATION_WORKER trên nhánh riêng. Claude local làm REVIEWER độc lập, merge sau khi chạy lại đầy đủ tại máy.
- Risk R2, vì có đụng lưu trữ và luồng revision.

Các nguyên tắc DA áp dụng:

- **DA01:** giữ số nguyên chính xác.
- **DA02:** không đổi cấu trúc DB hay file đã lưu; không reset.
- **DA03:** nhãn phản ánh đúng ý nghĩa dữ liệu.
- **DA04:** sửa tại chỗ, không viết lại.
- **DA05:** phải có luồng dùng được.

Bất biến:

- Hash R0000 và mọi revision không đổi.
- Plan, snapshot và contract hiện có không đổi; chỉ được thêm trường.
- `baltimore.json`, profile và GLB VINAFCO không đổi.
- Không thêm thư viện.

### H1. Danh sách vị trí bị bỏ khi tạo bản mới (O2)

Panel kết quả "Tạo bản theo dữ liệu mới" hiện tối đa 50 dòng, có phân trang hoặc nút "Xem thêm", kèm tổng số. Lọc được theo lý do (Bỏ / Đổi). Trang không còn dài quá màn hình khi có hàng trăm vị trí bị bỏ.

### H2. Nhãn "bó đã đặt bị ảnh hưởng" (quyết định 2 của review SUP-02A)

Danh sách phương án hiện hai số tách biệt:

- **"bó đã đặt có dữ liệu đổi":** giữ nguyên ý nghĩa `placed_affected_count` hiện có, gồm cả thay đổi chỉ về số ống, cờ cảnh báo hay xác nhận.
- **"vị trí sẽ bỏ khi tạo bản mới":** trường mới `placed_dropped_on_rebase_count`. Đó là số bó đã đặt mà sẽ bị bỏ (đã bị bỏ, hoặc đổi kích thước/khối lượng), tính bằng đúng quy tắc của `rebase`.

Trường mới chỉ được thêm vào `SnapshotListItem`. Có test bảo đảm số này bằng số vị trí `rebase` thực sự bỏ.

### H3. Bộ nhớ đệm phát lại revision (O4)

`plan_binding` giữ bộ nhớ đệm trong tiến trình cho kết quả phát lại, khóa bằng SHA-256 của toàn bộ dữ liệu thô các record đã đọc từ DB (`revision_id`, `source_json`, `changes_json`, `content_sha256`, theo thứ tự).

- Mỗi request vẫn đọc record từ DB. Chỉ bỏ qua phát lại khi khóa trùng.
- Record thay đổi (kể cả bị sửa tay) thì khóa đổi, phát lại và kiểm toàn vẹn như cũ.
- Bộ nhớ đệm giới hạn kích thước, ví dụ 8 mục.
- Các test toàn vẹn của SUP-02A, kể cả test sửa tay DB, vẫn đạt mà không sửa.

Đo và ghi thời gian danh sách phương án cùng bind với 20 revision, trước và sau.

### H4. Kiểm kích thước trước khi parse (O5)

Hai endpoint `POST /api/cargo-revisions` và `POST /api/cargo-revisions/preview` từ chối thân yêu cầu lớn hơn 1 MiB **trước** khi parse JSON:

- dựa vào `Content-Length` khi có;
- khi không có thì đọc theo luồng, dừng ngay khi vượt.

Mã lỗi và thông điệp tiếng Việt giữ như hiện tại. Cách làm tương tự cho hai endpoint profile tàu (28 MiB) nếu chúng chưa làm vậy. `contracts/openapi.json` chỉ được đổi nếu thật cần; nếu đổi thì nêu lý do.

### H5. Khóa liên tiến trình của kho profile trên Windows (O6)

`vessel_profile_store.append` dùng khóa file liên tiến trình trên cả hai nền:

- `fcntl.flock` trên POSIX;
- `msvcrt.locking` trên một file khóa trong `SCST_DATA_DIR/vessels/.lock` trên Windows.

Không thêm thư viện. Có test hai tiến trình (`multiprocessing`) cùng tạo một version: đúng một bên thành công, bên kia nhận VersionConflict.

### H6. Ngoài phạm vi

- Đưa provenance vào hash (O3).
- Chính sách OD-only recheck.
- Quy ước gốc GLB.
- Ảnh bằng chứng.
- Số đoạn tròn của ống.
- M3.
- Thay đổi giao diện khác.

## HARDEN-01 acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| H-01 | Theo H1: danh sách vị trí bị bỏ có phân trang và lọc; browser test với một revision bỏ hơn 100 vị trí đã đặt cho thấy tối đa 50 dòng mỗi trang, tổng số đúng; dùng được ở 390px. |
| H-02 | Theo H2: `placed_dropped_on_rebase_count` được thêm, không đổi các trường cũ; test chứng minh bằng số vị trí `rebase` bỏ cho các ca bỏ, đổi khối lượng, chỉ đổi xác nhận (0) và v1; nhãn giao diện tách hai số. |
| H-03 | Theo H3: bộ nhớ đệm đúng khóa; toàn bộ test toàn vẹn SUP-02A đạt không sửa; test mới: sửa tay một record sau khi đã cache thì lần đọc sau phát hiện; có số đo thời gian trước và sau với 20 revision. |
| H-04 | Theo H4: thân yêu cầu quá giới hạn bị từ chối trước khi parse, kiểm được bằng thân không phải JSON hợp lệ dài hơn giới hạn và trả đúng lỗi kích thước; có ca có và không có `Content-Length`; lỗi và mã giữ như cũ. |
| H-05 | Theo H5: khóa liên tiến trình trên cả hai nền; test hai tiến trình chạy đạt trên Linux (cloud) và Windows (root kiểm tại máy). Toàn bộ test backend và browser cũ đạt; `tooling/integration_check_pre_m2d.py` giữ 29/29; chạy browser không đổi file đã commit dưới `docs/reviews/`. |

## Verification and checkpoint

Mốc: `main` sau khi M2d được merge. Worker ghi số test của mốc.

Worker phải:

- chạy toàn bộ test backend;
- sinh lại contract và kiểu TypeScript;
- chạy `npm run build`;
- chạy toàn bộ browser suite và gate worker-return;
- chạy `tooling/integration_check_pre_m2d.py`.

Root review tại máy trên Windows và kiểm riêng H-05 trên Windows.

Ngân sách: worker 180 phút trên cloud, root review 60 phút, không reset khi sửa.
