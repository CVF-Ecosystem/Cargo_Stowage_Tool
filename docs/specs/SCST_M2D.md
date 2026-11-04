# SCST — M2d xuất báo cáo phương án (XLSX và PDF qua trang in)

Status: APPROVED_FOR_EXECUTION

## Authority and design

M2d là bước cuối của M2 theo roadmap tổng: người dùng hoàn tất luồng nhập → gợi ý → xem/chỉnh → lưu/mở lại → **xuất**, với dữ liệu bảng, 3D và báo cáo khớp nhau.

- Ngày 05-11-2026, checkpoint tích hợp trước M2d ([review](../reviews/SCST_INTEGRATION_CHECK_PRE_M2D.md)) đạt 29/29, không có lỗi chặn.
- Owner đã cho root làm tiếp roadmap mà không cần hỏi lại, và review trước mỗi lần merge.
- Thực hiện: Claude Cloud làm IMPLEMENTATION_WORKER trên nhánh riêng, trả về bằng pull request. Claude local làm REVIEWER độc lập và COMMIT_STEWARD.
- Risk R2, vì đây là đầu ra người dùng đem ra ngoài tool.

Các nguyên tắc DA áp dụng:

- **DA01:** số trong báo cáo lấy từ g và mm nguyên; hiển thị kg/cm/m/t; cột số nguyên chính xác luôn đi kèm.
- **DA02:** không đổi persistence.
- **DA03:** báo cáo ghi rõ trạng thái nguồn (ESTIMATED / SOURCED / DERIVED / chưa xác nhận), "chưa xác minh hình học" và "phương án một tầng".
- **DA04:** tái dùng Evaluation, rules, comparison, recheck, packing và viewer; chỉ thêm phần thiếu.
- **DA05:** phải có luồng dùng được.

Ràng buộc:

- Không thêm thư viện, cả Python lẫn npm. XLSX ghi bằng `zipfile` và XML của thư viện chuẩn.
- PDF do trình duyệt tạo từ trang báo cáo in được ("In / Lưu PDF"), không tạo PDF ở server. Muốn hiện đúng dấu tiếng Việt khi tạo PDF ở server thì phải nhúng font, việc này nằm ngoài phạm vi.

### D1. Mô hình báo cáo chung

D1.1. Mô hình báo cáo `scst.plan-report.v1` được dẫn xuất thuần từ một **snapshot đã lưu**. Chỉ snapshot đã lưu mới xuất được, để báo cáo tái lập được. Bản nháp phải lưu trước khi xuất.

D1.2. Mô hình gồm:

- **`header`:** tên phương án, id snapshot, thời điểm lưu, `contract_version`, `plan_sha256` (SHA-256 của `plan_json` đã lưu), thời điểm tạo báo cáo.
- **`vessel`:** id, tên, case, profile version và sha (nếu có), trạng thái từng nhóm số liệu (ESTIMATED/SOURCED/MEASURED).
- **`hold`:** kích thước mm, trạng thái.
- **`limits`:** các giới hạn tải (g) theo case.
- **`cargo`:**
  - dataset, revision ghim, sha;
  - trạng thái kiểm lại theo revision mới nhất (CURRENT / NEEDS_RECHECK / NOT_APPLICABLE / REVISION_UNAVAILABLE) kèm các số đếm của SUP-02A.
- **`totals`:**
  - tổng đơn vị, đã xếp, chưa xếp, bị loại trừ;
  - khối lượng manifest, khối lượng đã xếp, sức chứa còn lại (g);
  - thể tích khối bao (mm³ nguyên) nếu có sẵn.
- **`units`:** mỗi đơn vị gồm id, tên, nhóm, revision và xác nhận, kích thước mm và µm, khối lượng g, trạng thái xếp, x/y/z mm, góc xoay, packing (trạng thái, cách xếp, số ống) nếu là list ống.
- **`unplaced`:** đơn vị chưa xếp kèm lý do nếu có.
- **`issues`:** kết quả kiểm của rules.
- **`notices`:** danh sách cảnh báo tiếng Việt bắt buộc ở D1.3.

D1.3. Danh sách `notices` bắt buộc có:

- "Chưa xác minh hình học" khi hầm không phải MEASURED;
- "Phương án một tầng (xếp sơ bộ, chưa tối ưu)";
- "Packing là dẫn xuất, không phải số đo thực" khi có list ống;
- "Phương án cần kiểm lại theo dữ liệu mới" khi NEEDS_RECHECK;
- cảnh báo của dữ liệu nguồn (các nhóm có `dimension_warning`).

D1.4. `report_sha256` là SHA-256 của JSON chuẩn hóa của mô hình, **bỏ thời điểm tạo báo cáo**. Cùng một snapshot và cùng revision mới nhất thì cho cùng hash.

D1.5. Kiểm đối soát nội bộ trước khi trả:

- đã xếp + chưa xếp + bị loại trừ = tổng đơn vị;
- khối lượng đã xếp bằng tổng khối lượng các đơn vị đã xếp;
- số liệu trùng `evaluate(plan)`.

Lệch thì trả lỗi 500 có thông điệp rõ, không xuất báo cáo sai.

### D2. API

D2.1. `GET /api/snapshots/{id}/report` trả mô hình D1 dạng JSON.

D2.2. `GET /api/snapshots/{id}/report.xlsx` trả file XLSX:

- `Content-Disposition` có tên file an toàn ASCII kèm `filename*` UTF-8;
- MIME là `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

D2.3. Cả hai chỉ đọc. Không đổi snapshot hay DB. Snapshot không mở được, hoặc revision ghim lỗi toàn vẹn, thì từ chối như các điểm vào hiện có.

### D3. XLSX

D3.1. Workbook tối giản hợp lệ theo Office Open XML: `[Content_Types].xml`, `_rels`, `workbook.xml`, `styles.xml`, các sheet và `sharedStrings` hoặc inline string. Có 4 sheet:

| Sheet | Nội dung |
|---|---|
| "Tổng quan" | header, tàu, hầm, giới hạn, revision, trạng thái kiểm lại, tổng số, `report_sha256`, danh sách `notices` |
| "Hàng" | mỗi đơn vị một dòng. Cột hiển thị (kg 3 số lẻ, cm, m) kèm cột chính xác (g, mm, µm) là số nguyên. Có trạng thái xếp, vị trí, packing |
| "Chưa xếp" | đơn vị chưa xếp hoặc bị loại trừ, kèm lý do |
| "Kiểm tra" | issues của rules |

D3.2. Quy tắc định dạng:

- Chuỗi tiếng Việt giữ đúng Unicode; XML được escape đúng.
- Dòng tiêu đề in đậm, cố định khung (freeze) dòng đầu.
- Số là kiểu số, không phải chuỗi.
- Ghi tất định: cùng mô hình thì cho cùng byte, kể cả thời điểm trong file zip (cố định từ thời điểm lưu snapshot).

D3.3. Giới hạn 2000 đơn vị (bằng giới hạn Plan). File phải mở được bằng thư viện chuẩn: unzip và parse XML. Worker ghi rõ trong worker return là chưa kiểm bằng Excel thật; root kiểm tại máy nếu có.

### D4. Trang báo cáo in được (PDF)

D4.1. Route giao diện "Báo cáo" mở từ một phương án đã lưu (nút "Xuất báo cáo") và hiển thị mô hình D1:

- tiêu đề và thông tin;
- các cảnh báo bắt buộc in nổi bật;
- bảng tổng;
- hình chiếu bằng 2D dạng SVG của hầm và hàng đã xếp, dùng cùng dữ liệu vị trí;
- **một ảnh 3D** chụp từ viewer hiện có, cùng phương án, ở góc nhìn đã chọn, có chú thích "ảnh minh họa";
- bảng hàng có phân trang khi in;
- bảng chưa xếp;
- bảng kiểm tra.

D4.2. CSS `@media print` khổ A4: lề hợp lý, không cắt dòng bảng giữa trang nếu tránh được, lặp tiêu đề bảng. Nút "In / Lưu PDF" gọi `window.print()`. Nút "Tải XLSX" tải file từ D2.2.

D4.3. Khi WebGL không có, bỏ ảnh 3D và ghi chú lý do; phần còn lại vẫn đủ. Dùng được ở 390px để xem. Bản in theo khổ A4.

D4.4. Số trên trang lấy từ mô hình D1, không tính lại ở frontend. Hiển thị có làm tròn nhưng luôn kèm hoặc dẫn được tới số chính xác.

### D5. Ngoài phạm vi M2d

- Tạo PDF ở server.
- Mẫu báo cáo tùy biến.
- Logo, chữ ký.
- Gửi email.
- Báo cáo nhiều phương án.
- Ngôn ngữ khác.
- Nhiều tầng (M3).
- AI (M4).

## M2d acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| M2D-01 | Mô hình báo cáo theo D1: dẫn xuất thuần từ snapshot đã lưu; có ca kiểm cho m1, m2a, pipe-list v1, v2 ghim revision cũ (NEEDS_RECHECK), VINAFCO và tàu người dùng; đủ các cảnh báo bắt buộc; đối soát D1.5 có ca kiểm, kể cả ca lệch giả lập trả lỗi; `report_sha256` ổn định; snapshot và DB không đổi byte. |
| M2D-02 | API theo D2: chỉ đọc; tên file an toàn; snapshot lỗi hoặc revision lỗi toàn vẹn bị từ chối; `contracts/openapi.json` và `api.ts` sinh lại bằng công cụ hiện có. |
| M2D-03 | XLSX theo D3: unzip được và mọi phần XML parse được; 4 sheet đúng tên; số là kiểu số; giá trị chính xác g/mm/µm khớp mô hình cho mọi đơn vị; Unicode tiếng Việt đúng; tất định byte; có ca 1076 và 2000 đơn vị trong giới hạn thời gian ghi rõ. |
| M2D-04 | Trang in theo D4: số trên trang khớp mô hình (test đối chiếu); có ảnh 3D khi có WebGL, có ghi chú khi không; hình 2D dùng cùng vị trí; bản in A4 (Playwright `page.pdf` tạo được PDF có chứa các cảnh báo bắt buộc và tên phương án); dùng được ở 390px. |
| M2D-05 | Luồng nội bộ: mở list ống trong hầm VINAFCO → xếp thử → lưu → xuất báo cáo → tải XLSX → In/Lưu PDF → tạo revision mới → báo cáo của phương án cũ hiện "cần kiểm lại"; `npm run build` đạt; toàn bộ test backend và browser cũ đạt; chạy browser không đổi file đã commit dưới `docs/reviews/`. |

## Verification and checkpoint

Mốc: `main` tại thời điểm dispatch, có 597 test backend và 46 ca browser.

Worker phải:

- chạy toàn bộ test backend;
- sinh lại contract và kiểu TypeScript;
- chạy `npm run build`;
- viết `tests/browser/m2d.spec.ts`;
- chạy toàn bộ browser suite và gate worker-return;
- nếu không chạy được, ghi lệnh và lỗi.

Root review tại máy trên Windows:

- chạy lại toàn bộ;
- mở file XLSX bằng Excel nếu có trên máy, nếu không thì ghi rõ;
- in thử PDF;
- tự đi luồng M2D-05.

Nghiệm thu nghiệp vụ về nội dung, mẫu báo cáo và M3 thuộc owner.

Ngân sách: worker 240 phút trên cloud, root review 90 phút, không reset khi sửa.
