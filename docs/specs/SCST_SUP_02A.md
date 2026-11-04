# SCST — SUP-02A revision dữ liệu hàng, ghim revision và kiểm lại phương án

Status: APPROVED_FOR_EXECUTION

## Authority and design

Owner ngày 04-11-2026 chọn SUP-02 theo roadmap bổ sung và giao cho Claude Cloud thực hiện, Claude local
kiểm soát chất lượng. Root tách SUP-02 thành hai phần: **SUP-02A** (tài liệu này) gồm revision dữ liệu hàng
có provenance, phương án ghim revision và đánh dấu cần kiểm lại; **SUP-02B** gồm hợp đồng profile tàu/tọa độ
tổng quát, giữ nguyên trong roadmap với chủ sở hữu và SPEC riêng sau. SUP-02A không mở SUP-03, M2d hay AI.

Nền code `573d7fb` (đã đồng bộ `origin/main`). Risk R2 vì đổi persistence và dữ liệu nghiệp vụ.
Vai trò: root ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR, REVIEWER độc lập và COMMIT_STEWARD (Claude local);
IMPLEMENTATION_WORKER là Claude Cloud trên nhánh riêng. Vai trò là trách nhiệm, không gắn provider vào sản phẩm.

Áp dụng SCST-DA01 (giữ µm/g chính xác, giao diện kg/cm/m), DA02 (đổi persistence: DB thử tách biệt, phương án
tương thích/phục hồi, không reset DB lỗi), DA03 (phân biệt số có nguồn với số chưa xác nhận, revision có
provenance), DA04 (reuse Plan/registry/compare/SQLite hiện có, chỉ thêm phần thiếu), DA05 (luồng dùng nội bộ
trước khi xin phản hồi owner).

Nguồn gốc giữ bất biến: `services/backend/data/pipe_list/baltimore.json`, workbook gốc, GLB và profile tàu
không bị sửa. Dữ liệu hiện tại là cơ sở của revision đầu tiên.

D1. Revision. Revision gốc `BALTIMORE-PIPE-V1-1@R0000` được dẫn xuất từ `baltimore.json`, không lưu vào DB.
Mỗi lô cập nhật tạo đúng một revision kế tiếp `@R0001`, `@R0002`... theo dataset. `content_sha256` là SHA-256 của
JSON chuẩn hóa (sort_keys, separators `,`/`:`, UTF-8, không ASCII escape) của toàn bộ danh sách nhóm sau khi áp dụng.
Bảng SQLite mới `cargo_revisions` chỉ thêm, không có API sửa/xóa. Khi đọc, dựng lại nội dung bằng cách phát lại
từ R0000 và so `content_sha256`; lệch thì từ chối phục vụ revision đó và báo lỗi, không tự sửa. Tạo revision phải
gửi `parent_revision_id` bằng revision mới nhất; nếu không khớp trả 409 và không ghi (không tự gộp).

D2. Lô cập nhật. Mỗi lô gồm `source` (`kind` thuộc USER/FACTORY/CUSTOMER/OTHER, `reference` 1–200 ký tự,
`received_date` ngày ISO, `note` tối đa 500 ký tự) và 1–500 thay đổi. Loại thay đổi:
- `UPDATE_GROUP`: sửa một hoặc nhiều trường của nhóm hiện có trong {`bundle_count`, `pieces_per_bundle`,
  `dimensions_um`, `mass_g`, `outside_diameter_mm`, `wall_thickness_mm`, `dimension_warning`}. Giảm
  `bundle_count` bỏ các bó có chỉ số cao nhất; `bundle_count` = 0 nghĩa là nhóm rút khỏi manifest.
- `ADD_GROUP`: thêm nhóm mới; server cấp `group_id` dạng `ADD-001`… và ID bó `PIPE-A001-B0001`…
- `BUNDLE_OVERRIDE`: ghi đè `mass_g` và/hoặc `dimensions_um` của một bó cụ thể theo ID bó (ví dụ cân thực tế).
Mỗi thay đổi có `confirmation` UNVERIFIED hoặc CONFIRMED. `dimension_warning` chỉ được chuyển từ true sang false
khi thay đổi đó CONFIRMED. ID bó hiện có không bao giờ đổi nghĩa; ID đã bỏ không được cấp lại.

D3. Giới hạn và kiểm. Payload ≤ 1 MiB; ≤ 500 thay đổi/lô; ≤ 200 nhóm; tổng bó toàn dataset ≤ 2.000; mỗi nhóm
≤ 2.000 bó; `pieces_per_bundle` 1–10.000; kích thước µm > 0 và ≤ 10^9; khối lượng bó g > 0 và ≤ 10^12.
Giá trị nguyên chính xác như dữ liệu hiện tại, không làm tròn khi lưu. Lỗi trả theo từng thay đổi (vị trí, trường,
thông báo tiếng Việt) và không ghi gì khi còn lỗi. Có endpoint xem trước (không ghi) trả lỗi, tóm tắt thay đổi và
danh sách ID bó bị ảnh hưởng.

D4. Provenance. Revision và nhóm dẫn xuất cho biết với từng trường đã đổi: revision tạo ra giá trị, `source`
và `confirmation`; trường chưa đổi mang provenance R0000 (workbook). Ghi đè bó có provenance riêng. Đơn vị
dẫn xuất của bó ghi `revision_id` và trạng thái xác nhận; mesh/hiển thị không là nguồn ID, khối lượng hay pose.

D5. Ghim revision trong phương án. Thêm contract `scst.pipe-list.v2` với `cargo_revision`
(`dataset_id`, `revision_id`, `content_sha256`); `units` phải trùng chính xác các bó dẫn xuất của revision đó
(tối đa 2.000). Kiểm ràng buộc này ở một tầng dịch vụ dùng chung cho mọi điểm vào nhận Plan: validate, lưu,
mở snapshot, so sánh, xếp thử và preview list; không đưa truy cập DB vào model pydantic thuần.
Contract `scst.m1.v1`, `scst.m2a.v1`, `scst.pipe-list.v1` và snapshot cũ giữ nguyên hành vi; phương án
`scst.pipe-list.v1` được coi là ghim R0000 mà không ghi lại dữ liệu đã lưu.

D6. Cần kiểm lại và tạo bản mới. Danh sách phương án đã lưu cho biết `cargo_revision_id` và trạng thái
CURRENT / NEEDS_RECHECK / NOT_APPLICABLE (phương án không dùng list ống). NEEDS_RECHECK khi revision mới nhất
khác revision đã ghim ở bất kỳ bó nào của manifest (thêm, bỏ, đổi), kèm số bó thêm/bỏ/đổi và số bó **đã đặt**
bị ảnh hưởng. Snapshot đã lưu không bao giờ bị sửa. Thao tác "tạo bản theo dữ liệu mới" trả một Plan ứng viên ở
revision đích: dẫn xuất lại manifest, giữ `requirement` theo ID, giữ vị trí của bó còn tồn tại và không đổi
kích thước/khối lượng, bỏ và liệt kê vị trí của bó bị đổi/bỏ; trả kèm kết quả kiểm và so sánh (tái dùng
`domain/comparison`). Người dùng lưu ứng viên thành phương án mới.

D7. Lưu trữ và di trú. Giữ nguyên bảng `snapshots` và kiểm cột nghiêm ngặt hiện có. Lần đầu mở DB đã tồn tại mà
chưa có `cargo_revisions`: sao lưu một lần `scst.sqlite3.pre-sup02a.bak` (không ghi đè nếu đã có), rồi tạo bảng.
Bảng `cargo_revisions` có cột cố định và được kiểm như `snapshots`; cấu trúc lạ thì từ chối với lỗi rõ, không
xóa/reset. Ghi revision trong một giao dịch `BEGIN IMMEDIATE`. Hoàn tác: xóa bảng mới không ảnh hưởng snapshot cũ.

D8. Giao diện. Trong luồng list ống: khung "Dữ liệu hàng" cho biết revision đang dùng, lịch sử revision và nguồn;
biểu mẫu tạo lô cập nhật (chọn nhóm/bó, sửa trường, nhập nguồn, ngày, xác nhận), xem trước bó bị ảnh hưởng rồi
tạo revision. Danh sách phương án đã lưu hiện nhãn "Cần kiểm lại" với số bó, và nút "Tạo bản theo dữ liệu mới"
mở ứng viên cùng bảng so sánh hiện có. Tiếng Việt, kg/cm/m khi hiển thị, giữ giá trị chính xác khi gửi. Dùng được
ở 390px. Không thêm thư viện.

Ngoài phạm vi SUP-02A: profile tàu/tọa độ tổng quát và nhiều tàu (SUP-02B), dataset khác Baltimore, nhập Excel,
AI hỗ trợ nhập, xóa/gộp revision, nhiều người dùng/đăng nhập, packing chi tiết (SUP-03), xuất báo cáo (M2d).

## SUP-02A acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| S2-01 | Revision store theo D1–D3: R0000 dẫn xuất và hash ổn định; xem trước không ghi; tạo/list/đọc revision; chỉ thêm; phát lại kiểm hash; sai parent trả 409 không ghi; mọi giới hạn D3 có ca kiểm với lỗi tiếng Việt; `baltimore.json` và dữ liệu nguồn không đổi byte. |
| S2-02 | Provenance theo D2/D4: trường đổi và bó ghi đè có revision/nguồn/xác nhận; trường không đổi mang R0000; `dimension_warning` chỉ tắt khi CONFIRMED; ID bó ổn định và không cấp lại; API và giao diện hiển thị cùng thông tin. |
| S2-03 | Ghim revision theo D5: Plan `scst.pipe-list.v2` bị từ chối khi manifest khác revision ghim hoặc revision không tồn tại, ở mọi điểm vào đã liệt kê; ba contract cũ và snapshot đã lưu trước đây mở/kiểm/lưu như trước (ca hồi quy cho từng contract); µm/g giữ chính xác. |
| S2-04 | Kiểm lại và tạo bản mới theo D6: trạng thái CURRENT/NEEDS_RECHECK/NOT_APPLICABLE đúng cho v1/v2/không phải list; số bó thêm/bỏ/đổi và đã đặt bị ảnh hưởng đúng; ứng viên giữ vị trí bó không đổi, bỏ và liệt kê vị trí bị ảnh hưởng, kèm so sánh; snapshot đã lưu giữ nguyên byte sau mọi thao tác. |
| S2-05 | Di trú theo D7: DB chỉ có `snapshots` mở được, được sao lưu một lần rồi thêm bảng mới, hàng snapshot giữ nguyên byte; bảng `cargo_revisions` sai cấu trúc bị từ chối không reset; mọi test dùng `SCST_DATA_DIR` tạm, không chạm DB người dùng. |
| S2-06 | Giao diện và hợp đồng theo D8: `contracts/openapi.json` và `apps/frontend/src/api/generated/api.ts` sinh lại bằng công cụ hiện có; `npm run build` đạt; luồng nội bộ: mở list ống → lưu phương án → tạo lô cập nhật một nhóm có nguồn → phương án cũ hiện "Cần kiểm lại" → tạo bản theo dữ liệu mới → xem so sánh → lưu bản mới → mở lại cả hai bản; dùng được ở desktop và 390px; toàn bộ test backend và browser cũ vẫn đạt. |

## Verification and checkpoint

Mốc trước BUILD: 104/104 test backend đạt trên `573d7fb`; bộ browser cũ 36 ca theo review SUP-01.
Worker chạy toàn bộ test backend (cũ và mới), sinh lại contract/kiểu, `npm run build`, và viết
`tests/browser/sup02a.spec.ts` cho luồng S2-06. Nếu môi trường cloud không chạy được trình duyệt hoặc gate CVF
(thiếu core ẩn), ghi rõ lệnh và lỗi trong worker return, không bỏ qua hay làm yếu kiểm; root chạy lại tại máy.

Root review độc lập tại máy: chạy lại backend, build, toàn bộ browser (cũ + mới) trên DB thử cổng 8766, gate
worker-return/reviewer-fast, soát diff theo D1–D8 và vùng file được phép, kiểm không có secret/phụ thuộc mới,
và tự đi luồng nội bộ S2-06. Lỗi cục bộ có bằng chứng xác định được sửa tại chỗ và công bố; thay đổi thiết kế
trả lại worker. Checkpoint chỉ chốt kỹ thuật và luồng dùng của SUP-02A; nghiệm thu nghiệp vụ, SUP-02B, SUP-03,
M2d và xác minh 16 envelope vẫn thuộc chủ sở hữu trong roadmap.

Ngân sách: worker 240 phút trên cloud, root review 90 phút; không reset khi sửa. Có thể bàn giao chưa đủ khi
chạm ngân sách, nhưng không đổi tiêu chí bắt buộc thành tùy chọn.
