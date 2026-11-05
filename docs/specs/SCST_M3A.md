# SCST — M3a xếp nhiều tầng theo cột đồng nhất (MVP trên hầm ước tính)

Status: APPROVED_FOR_EXECUTION

## Authority and design

Ngày 05-11-2026 owner nhắc nguyên tắc: đội dev phải ra được Prototype/MVP trước khi chờ feedback của user. Kiểm tra tích hợp trước M2d ([review](../reviews/SCST_INTEGRATION_CHECK_PRE_M2D.md)) cho thấy khoảng trống lớn nhất của MVP:

- Bộ xếp một tầng chỉ đặt được 167/1076 bó Baltimore vào hầm VINAFCO.
- Giới hạn không nằm ở khối lượng (1125 t so với giới hạn 3517 t) mà ở diện tích sàn.
- Hầm cao 5408 mm trong khi bó cao khoảng 300 mm.

M3 trong roadmap tổng gồm nhiều tầng, case thực và hầm đã đo. **M3a** là phần kỹ thuật làm được ngay:

- Chất xếp nhiều tầng có kiểm đỡ, trên hầm ước tính, gắn nhãn chưa xác minh — đúng điều kiện roadmap cho trường hợp chưa có dữ liệu thật.
- Đối chiếu case thực và số đo hầm vẫn là M3b, thuộc owner.

Thực hiện:

- Claude Cloud làm IMPLEMENTATION_WORKER.
- Claude local làm REVIEWER độc lập, merge theo quyền owner đã giao.
- Risk R2.

Các nguyên tắc DA áp dụng:

- **DA01:** tọa độ mm nguyên, kiểm hình học bằng µm nguyên.
- **DA02:** snapshot cũ không đổi.
- **DA03:** ghi rõ những gì chưa kiểm (tải chồng, tải sàn, chằng buộc, ổn định).
- **DA04:** tái dùng Placement (`z_mm`, `layer`, `supported_by` đã có từ M1), rules, planner, viewer và báo cáo.
- **DA05:** phải có luồng dùng được.

Hai quyết định kỹ thuật kèm theo, root chốt luôn để không treo chờ owner:

- **(a) Revision chỉ sửa OD:** giữ CURRENT. OD không làm đổi kích thước hay khối lượng đơn vị, chỉ đổi cách nhìn packing.
- **(b) Provenance nguồn không đưa vào hash.** Đưa vào sẽ đổi hash của mọi revision đã lưu. Toàn vẹn được bảo vệ bằng việc phát lại có kiểm hợp lệ; sửa tay DB vẫn bị phát hiện khi làm record sai.

Hai quyết định này ghi vào review M3a.

### D1. Chế độ xếp chồng trong Plan

D1.1. Thêm trường tùy chọn `stacking` vào Plan:

- Giá trị là `"SINGLE_LAYER"` hoặc `"COLUMNS_V1"`.
- Thiếu hoặc `SINGLE_LAYER` thì hành vi y như hiện nay, kể cả lỗi `LAYER_UNSUPPORTED` khi z khác 0.
- Trường bị bỏ khỏi JSON khi trống (như `cargo_revision`), nên mọi Plan và snapshot cũ giữ nguyên byte.

D1.2. `COLUMNS_V1` hợp lệ với mọi contract hiện có có hầm BOX.

### D2. Quy tắc kiểm `COLUMNS_V1`

Áp dụng trong `domain/rules` khi `stacking = COLUMNS_V1`, thay cho `LAYER_UNSUPPORTED`. Mọi vị trí z > 0 phải thỏa:

- **D2.1.** `supported_by` khác rỗng. Mọi đơn vị đỡ phải đã được đặt và có mặt trên đúng bằng `z_mm`, so bằng µm.
- **D2.2.** Hợp diện tích mặt trên của các đơn vị đỡ phủ ≥ 90% diện tích đáy của đơn vị được đỡ, tính bằng số nguyên µm².
- **D2.3.** Tâm đáy của đơn vị được đỡ nằm trên mặt trên của ít nhất một đơn vị đỡ.
- **D2.4.** `layer` = số tầng tính từ đáy: 0 khi z = 0; ngược lại bằng max(`layer` của đơn vị đỡ) + 1.

Vị trí z = 0 thì `supported_by` phải rỗng và `layer` = 0.

Mọi kiểm cũ vẫn áp dụng: trong hầm theo cả chiều cao, không giao nhau, giới hạn khối lượng.

D2.5. Mã lỗi mới, kèm lời tiếng Việt chỉ rõ bó và bó đỡ:

- `SUPPORT_MISSING`
- `SUPPORT_LEVEL_MISMATCH`
- `SUPPORT_AREA_LOW` (kèm phần trăm phủ)
- `SUPPORT_CENTRE_UNSUPPORTED`
- `LAYER_INDEX_INVALID`

D2.6. Danh sách "chưa kiểm" của phương án `COLUMNS_V1` thay "Chất xếp nhiều tầng" bằng:

- "Tải chồng cho phép trên bó (chưa có dữ liệu)";
- "Tải cục bộ đáy hầm";
- "Kê, chèn và chằng buộc";
- "Ổn định phương tiện".

### D3. Bộ xếp `columns-v1`

D3.1. Bộ xếp mới `columns-v1`, tất định và thận trọng, không tối ưu toàn cục:

1. Gom các đơn vị cần xếp thành nhóm có cùng kích thước lưới mm (dài, rộng, cao); với list ống thì gần như theo nhóm nguồn.
2. Mỗi nhóm được đặt thành các **cột**. Một cột là một vị trí sàn chọn bằng guillotine như bộ xếp hiện có (best area fit, yaw 0/90). Trong cột, các đơn vị cùng nhóm chồng thẳng đứng, z tăng bằng chiều cao µm làm tròn lên mm của đơn vị dưới; `supported_by` = đơn vị ngay dưới; `layer` tăng dần.
3. Cột dừng khi tầng kế tiếp vượt chiều cao hầm, hết đơn vị của nhóm, hoặc hết khối lượng cho phép.
4. Thứ tự:
   - bắt buộc trước, tùy chọn sau;
   - nhóm theo diện tích đáy giảm dần;
   - trong nhóm theo ID.

D3.2. Đơn vị không xếp được có lý do. Dùng lại các mã cũ, thêm `STACK_HEIGHT` khi không còn tầng nào vừa.

D3.3. Bộ xếp chỉ đưa ra ứng viên: không ghi gì, áp dụng qua luồng xem trước/áp dụng hiện có. Kết quả phải qua `evaluate` không lỗi hình học.

D3.4. API:

- `POST /api/planner/preview` nhận thêm tham số tùy chọn `algorithm` trong query, giá trị `guillotine-single-layer-v1` (mặc định, giữ hành vi cũ) hoặc `columns-v1`.
- Với `columns-v1`, ứng viên có `stacking = COLUMNS_V1`.
- Thời gian xếp 1076 bó phải dưới 2 giây trên máy cloud, ghi trong worker return.

### D4. Giao diện và báo cáo

D4.1. Nút xếp thử có lựa chọn:

- "Một tầng (như cũ)";
- "Nhiều tầng theo cột (thử nghiệm)", là lựa chọn mặc định cho list ống.

Hiện số tầng tối đa, số cột, số bó đã xếp và chưa xếp kèm lý do.

D4.2. Bảng hàng có cột "Tầng". Panel chi tiết bó hiện tầng, z và bó đỡ.

D4.3. Viewer 3D hiển thị đúng z (đã có), không đổi vòng đời scene. Hình 2D hiện số tầng của mỗi cột, ví dụ "×16".

D4.4. Báo cáo M2d:

- cột tầng và z;
- tổng số tầng;
- cảnh báo "Phương án nhiều tầng: chưa kiểm tải chồng, tải sàn, chằng buộc và ổn định";
- bỏ cảnh báo "phương án một tầng" khi `stacking = COLUMNS_V1`.

### D5. Ngoài phạm vi M3a

- Xếp lẫn kích thước khác nhau trong cùng cột.
- Gác/kê, chèn gỗ.
- Tải chồng cho phép.
- Trọng tâm và ổn định.
- Nhiều hầm.
- Hầm không phải BOX.
- Chỉnh tay kéo thả 3D theo tầng.
- Đối chiếu case thực (M3b).

## M3a acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| M3A-01 | Chế độ theo D1: `stacking` tùy chọn, bỏ khỏi JSON khi trống; mọi contract cũ, snapshot cũ và JSON trả về giữ nguyên byte (ca hồi quy); `SINGLE_LAYER` vẫn báo `LAYER_UNSUPPORTED` như cũ. |
| M3A-02 | Quy tắc theo D2: mỗi mã lỗi mới có ca dương và ca âm; phủ 90% tính chính xác bằng µm²; tâm đáy; chiều cao hầm; không giao nhau giữa các tầng; mọi điểm vào đã có (validate, lưu, mở, so sánh, báo cáo) dùng cùng quy tắc. |
| M3A-03 | Bộ xếp theo D3: tất định (chạy hai lần cho cùng kết quả); mọi ứng viên qua `evaluate` không lỗi hình học; với list Baltimore trong hầm VINAFCO VR-SII đặt được **ít nhất 900/1076 bó** hoặc ghi rõ lý do giới hạn bằng số liệu; thời gian dưới 2 giây; đơn vị không xếp có lý do. |
| M3A-04 | Giao diện và báo cáo theo D4: chọn cách xếp, cột tầng, panel bó đỡ, 3D đúng z, 2D số tầng, báo cáo có cảnh báo nhiều tầng; dùng được ở 390px; `contracts/openapi.json` và `api.ts` sinh lại. |
| M3A-05 | Luồng: mở list ống trong hầm VINAFCO → xếp thử nhiều tầng → áp dụng → kiểm không lỗi hình học → lưu → mở lại → xuất báo cáo → tạo revision mới → cần kiểm lại và tạo bản mới vẫn đúng với vị trí nhiều tầng (bó bị bỏ kéo theo bó tầng trên mất đỡ thì cũng bị bỏ hoặc báo lỗi đỡ, ghi rõ cách chọn). Mọi test backend và browser cũ đạt; `tooling/integration_check_pre_m2d.py` 29/29; chạy browser không đổi file đã commit dưới `docs/reviews/`. |

## Verification and checkpoint

Mốc: `main` 07c6e85, có 679 test backend và 52 ca browser.

Worker phải:

- chạy toàn bộ test backend;
- sinh lại contract và kiểu TypeScript;
- chạy `npm run build`;
- viết `tests/browser/m3a.spec.ts`;
- chạy toàn bộ browser suite, kịch bản tích hợp và gate worker-return.

Root review tại máy trên Windows, tự xếp thử list Baltimore và xem 3D.

Nghiệm thu nghiệp vụ, số đo hầm, case thực và tải chồng thuộc M3b của owner.

Ngân sách: worker 240 phút trên cloud, root review 90 phút, không reset khi sửa.
