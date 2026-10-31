# SCST M2a — Nhập liệu, import và lưu/mở local

Status: APPROVED_FOR_EXECUTION

## Authority and outcome

Owner nói “ok. tiếp tục roadmap”, rồi “tiếp”, sau bàn giao VINAFCO268. Chọn đúng phần kế tiếp M2a trong roadmap đã thống nhất: nhập hàng/hầm, import có kiểm tra và lưu/mở. Đây là quyền tiếp tục phần này theo SPEC/WORK_ORDER trước BUILD, không phải nghiệm thu nghiệp vụ/điều kiện vận hành của các bản trước. Root orchestrator/reviewer, Terra6.1High worker, Sol-Medium browser. Risk R2, ceiling R2, local một người dùng, không push dữ liệu thật.

Kết quả: tạo phương án riêng với hầm BOX và từng bó hàng, biết lỗi nhập ở dòng/trường, kiểm khối lượng/hình học bằng backend, lưu phương án local và mở lại sau reload hoặc khởi động lại server. Giữ mẫu M1 và chế độ VINAFCO; không cần dữ liệu thật mới xây được luồng có nhãn.

## Decisions for this slice

- D1 — Contract: thêm `scst.m2a.v1`, client/server tiếp tục nhận `scst.m1.v1`. V1 giữ mặc định và tối thiểu1unit; v2 nhận0–200unit. V2 có nguồn USER_ENTERED cho hầm BOX tự nhập và provenance hàng SYNTHETIC/USER_ENTERED; mixed VINAFCO giữ identity/case/hold/certificate ràng buộc profile. Nhập tay/import không biến thông số thành đã xác minh; không có nguồn REAL/SAFE.
- D2 — Empty: phương án mới có0hàng/0placement, tổng0, trạng thái DRAFT với lỗi EMPTY_MANIFEST; không bịa unit, không chia0. Hầm/khoảng tải vẫn cần hợp lệ. Chỉnh trạng thái required/optional/excluded; excluded không giữ placement. Không làm logic nhiều tầng.
- D3 — Nhập tay: thêm/sửa/xóa từng bó với ID, tên, loại, yêu cầu, kích thước mm, khối lượng kg tối đa3số thập phân; ID duy nhất. Đặt/bỏ bó trong hầm là thao tác rõ, không tự xếp. Chỉnh hầm BOX tự nhập (dài/rộng/cao mm và tên), giữ limits như hiện tại. Hầm reference khóa, muốn custom phải bỏ liên kết phương tiện bằng thao tác rõ; không kéo giãn GLB để giả số đo thật. Sửa không hợp lệ giữ form/bản trước; đổi lựa chọn không mất rawdraft.
- D4 — Import đầu tiên là CSV UTF-8, dấu phẩy, có thể BOM, header đúng `id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg`. Một dòng là một bó; loại BAR_BUNDLE/PIPE_BUNDLE, yêu cầu required/optional/excluded. Kích thước số nguyên dương; mass dùng dấu chấm thập phân, tối đa3chữ số, đổi chính xác sang g; không exponent/thousands/quantity/ước lượng. Hỗ trợ quoting tên, không đoán đơn vị. Max200dòng/1MiB UTF8. Saiheader/thiếu/thừa/dòng lỗi/ID trùng/giá trị sai báo dòng+trường và chặn toàn bộ áp dụng, không import một phần. Không có XLSX/PDF/OCR trong lượt này; cung cấp CSV mẫu để Excel lưu ra được.
- D5 — Preview/import: gửi CSV+plan hiện hành lên backend để xem số bó/tổngkhối lượng và lỗi; chưa thay workspace. Áp dụng preview hợp lệ rõ ràng, thay manifest và đặt placements rỗng (nhãn hàng chưa xếp), giữ hold/limits/reference. Nếu context hoặc edit thay đổi sau preview, vô hiệu preview/yêu cầu kiểm lại; không để response cũ ghi đè dữ liệu mới.
- D6 — Storage: SQLite stdlib tại `runtime-data/scst.sqlite3` (ngoài Git); `SCST_DATA_DIR` chỉ là cấu hình server/test, không nhận đường dẫn từ API. Lưu tên1–100ký tự, UUID server sinh, UTCtime, schema `scst.saved-plan.v1`, plan snapshot immutable; lưu lần sau tạo bản mới, không ghi đè. List/open theo ID, không delete API. Dùng SQL parameters/transaction. Lưu checked snapshot kể cả lỗi bố trí đã đánh giá, chặn rawSTALE. Mở lại validate/re-evaluate theo domain hiện tại, không tin status đã lưu. File/record lỗi/không tương thích trả lỗi tiếng Việt và giữ workspace; không âm thầm sửa file nguồn hoặc reset database. Bound list max100 gần nhất, nói rõ giới hạn. Reload có danh sách mở lại; không hứa auto-save/rawdraft tồn tại sau đóng tab. Không lưu PDF/dữ liệu gốc vàoDB.
- D7 — Bảo toàn: các lệnh thay workspace (mới/import/open/case/reset/undo) giữ bản trước vào history hiện có và chặn khi rawSTALE; async edit mới không bị mất. Save đang chạy lưu snapshot đã chụp, không đánh dấu nháp phát sinh sau đó là đã lưu. Selection/empty/history không crash; profile được nạp lại khi mở saved VINAFCO trực tiếp sau reload. Dữ liệu bảng/3D/summary cùng checked snapshot; UI thông báo chưa lưu và cách mở lại. Không mở M2c so sánh phiên bản đầy đủ.

## Early real-data probe

Đã tìm trong docs/reference, archive M1 và gói VINAFCO268: chưa có manifest hàng thực/CSV/XLSX; JSON gói nói hầm ước tính. Root hỏi owner vị trí dữ liệu qua câu hỏi text; owner trả lời **“Chưa có, tiếp tục với mẫu có nhãn”**. Hiện dùng fixture có nhãn theo chỉ đạo đó, không yêu cầu đo hoặc xử lý QA để chặn phát triển. Có dữ liệu thì đối chiếu format/đơn vị/BOX trước khi nói importer hỗ trợ manifest đó. Owner cung cấp khi có, orchestrator giữ checkpoint M3 và điều kiện dòngM2 của roadmap. Thiếu nguồn thực độc lập với nhập theo schema được khai báo và persistence, không cấp quyền dùng hầm thật.

## M2a acceptance

| ID | Đầu ra và kiểm chứng |
|---|---|
| M2A-01 | Tạo phương án rỗng; thêm/sửa/xóa hàng, đặt/bỏ vị trí, required/optional/excluded và tổng khối lượng/đối soát đúng; lỗi nhập không mất dữ liệu |
| M2A-02 | Nhập/sửa hầm BOX và limits qua backend; reference VINAFCO vẫn khóa/chặt, custom không giả đã đo; dữ liệu mm/g chính xác, source/provenance đúng |
| M2A-03 | ImportCSV mẫu UTF8/BOM/quotedname đúng, preview mass/count khớp; lỗi dòng+field/duplicate/header/size/rowlimit/precision chặn toàn bộ, giữ workspace và không bịa mass |
| M2A-04 | Lưu snapshot immutable SQLite ngoàiGit; list/open sau reload và server restart, backend kiểm lại; tên/ID/path/DB lỗi và phiên bản lạ không phá bản đang có; dữ liệu reference/cargo/placements khớp |
| M2A-05 | STALE, selection/empty/history, preview cũ, save/open/import đang chờ và lỗi mạng không ghi đè edit mới; mobile/WebGL fallback vẫn dùng được |
| M2A-06 | Probe nguồn thực được ghi nhận, fixture/CSV/hầm có nhãn, API/UI không tuyên bố vận hành; manifest và geometry chưa xác minh được giữ checkpoint đúng |
| M2A-07 | Build/contracts/backend/browser hồi quy M1+VINAFCO và luồng M2a đạt, proof persistence bằng server mới đọc DB cũ; root review độc lập, hướng dẫn cập nhật |

## Boundaries, remainder and checkpoint

Kế thừa model/geometry/rules, GLB, workspace checked/draft/history và launcher; archive giữ nguyên. Không có adapter import/storage phù hợp đã chạy trong source/archive, vì vậy bổ sung mới với stdlib, không viết lại validator. CSV là format đầu tiên được công bố, hỗ trợ một manifest khác cần đối chiếu khi có dữ liệu. M2b heuristic/unplacedreasons, M2c so sánh đầy đủ, M2d PDF/XLSX và M3 dữ liệu thực do orchestrator giữ trong roadmap, chỉ mở khi tới lượt. No cloud/multiuser/AI/OS-dialog arbitrary filesystem API.

Checkpoint worker return hoặc hết180phút implementation +60phút review gồm support. Root kiểm nội bộ đủ trước owner feedback, không giao owner làm QA kỹ thuật. Stop khi vượt scope/risk/budget, không tự đổi acceptance hoặc resetbudget. M2a technical completion không đồng nghĩa hoàn tất M2 hay dùng thực.
