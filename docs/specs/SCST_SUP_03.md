# SCST — SUP-03 cách nhìn bó/ống chi tiết dẫn xuất từ dữ liệu

Status: APPROVED_FOR_EXECUTION

## Authority and design

Ngày 04-11-2026 owner yêu cầu dựng spec dài hạn để cloud làm tiếp qua đêm, sáng 05-11 owner review trước khi merge.

- SUP-03 là mục cuối của roadmap bổ sung. Nội dung: khối bao, bó giản lược và bó/ống chi tiết là các cách nhìn của cùng một thực thể; packing gắn nguồn và trạng thái; khi đủ đầu vào thì tự dựng chi tiết và kiểm số lượng, OD, kích thước; khi thiếu hoặc mâu thuẫn thì giữ khối bao và cảnh báo.
- SUP-03 xếp chồng lên SUP-02B: nhánh cloud tạo từ head nhánh `claude/sup-02b-vessel-profile`, PR trỏ vào nhánh đó. Root review từng PR. Merge theo thứ tự SUP-02B rồi SUP-03, sau khi owner xem.
- Thực hiện: Claude Cloud làm IMPLEMENTATION_WORKER; Claude local làm REVIEWER độc lập và COMMIT_STEWARD.
- Risk R2, vì có hiển thị mới trên dữ liệu nghiệp vụ và hiệu năng viewer.

Các nguyên tắc DA áp dụng:

- **DA01:** µm và mm nguyên; OD từ chuỗi thập phân đổi sang µm chính xác.
- **DA02:** không đổi persistence.
- **DA03:** packing dẫn xuất ghi rõ là DERIVED, không phải số đo thực.
- **DA04:** tái dùng revision, derive_units, Scene, các chế độ hiển thị và bảng.
- **DA05:** phải có luồng dùng được.

Bất biến:

- `baltimore.json`, R0000 và hash của mọi revision không đổi.
- Không thêm trường nào vào lô cập nhật hay revision của SUP-02A.
- Packing không làm đổi ID, số lượng, khối lượng, kích thước bó hay pose; chỉ là cách nhìn.

### D1. Mô hình packing thuần

D1.1. `domain/packing` là một hàm thuần. Đầu vào là nhóm của một revision: `pieces_per_bundle`, `outside_diameter_mm`, `dimensions_um` (dài, rộng, cao). Đầu ra cho mỗi nhóm:

| Trường | Ý nghĩa |
|---|---|
| `status` | DETAILED hoặc ENVELOPE_ONLY |
| `layout` | RECT hoặc HEX |
| `columns`, `rows` | kích thước lưới |
| `od_um` | OD tính bằng µm |
| `pipe_centres_um` | tâm từng ống trên mặt cắt (y, z), số nguyên µm, gốc ở góc dưới mạn trái của mặt cắt bó |
| `slack_um` | phần dư theo rộng và cao |
| `checks` | kết quả các kiểm của D2 |
| `reasons` | mã lý do và lời nhắc tiếng Việt |

D1.2. Thuật toán tất định:

1. Đổi OD sang µm bằng phép đổi chuỗi chính xác. Chuỗi không hợp lệ hoặc OD ≤ 0 thì ENVELOPE_ONLY với lý do `OD_MISSING`.
2. Thử lưới RECT: số cột = floor(rộng / OD), số hàng = floor(cao / OD). Nếu số cột × số hàng ≥ số ống thì đặt đủ số ống theo hàng từ dưới lên, mỗi hàng từ trái sang phải.
3. Nếu RECT không đủ chỗ thì thử HEX:
   - bước hàng là OD·√3/2, làm tròn xuống µm;
   - hàng lẻ lệch nửa OD;
   - số ống mỗi hàng tính theo bề rộng còn lại.
4. Nếu cả hai đều không đủ chỗ thì ENVELOPE_ONLY với lý do `PIECES_DO_NOT_FIT`, kèm số ống tối đa vừa.

D1.3. Mọi tọa độ là số nguyên µm. Phép làm tròn chỉ dùng cho hình hiển thị, không là dữ liệu nghiệp vụ.

D1.4. Tối đa 10 000 ống mỗi bó (bằng giới hạn `pieces_per_bundle`). Bó lớn hơn ngưỡng hiển thị ở D4 vẫn tính được, nhưng viewer có thể giữ khối bao.

### D2. Kiểm và trạng thái

D2.1. Mỗi nhóm có các kiểm:

- **`count`:** số ống đặt được bằng `pieces_per_bundle`.
- **`od_fit`:** OD ≤ rộng và OD ≤ cao.
- **`envelope_fit`:** mọi ống nằm trong mặt cắt bó.
- **`slack`:** chỉ để thông tin, không chặn. Phần dư ≥ 1 OD theo một chiều thì gắn lý do `ENVELOPE_LOOSE` (khối bao lớn hơn cách xếp chặt).

D2.2. Nhóm có `dimension_warning` hoặc issue code hiện có thì giữ lý do từ dữ liệu nguồn (`SOURCE_WARNING`).

D2.3. Thiếu hoặc mâu thuẫn chỉ ảnh hưởng nhóm đó; các nhóm khác vẫn DETAILED.

D2.4. Thống kê toàn dataset gồm:

- số nhóm và số bó theo trạng thái;
- tổng ống dẫn xuất so với tổng ống nguồn (số bó × số ống mỗi bó).

### D3. API

D3.1. `GET /api/cargo-revisions/{revision_id}/packing` trả packing của mọi nhóm trong revision và thống kê D2.4. Chỉ đọc; revision lỗi toàn vẹn thì từ chối như SUP-02A.

D3.2. Đơn vị phương án `scst.pipe-list.v1/v2` không đổi JSON. Packing là dữ liệu tra theo `group_id` và revision, không nhúng vào Plan hay snapshot.

### D4. Ba cách nhìn trong viewer

D4.1. Có bộ chọn "Cách nhìn hàng" với ba lựa chọn:

| Cách nhìn | Hiển thị | Mặc định |
|---|---|---|
| "Khối bao" | như hiện nay | có |
| "Bó giản lược" | khối bao mờ, cộng các vòng tròn đầu ống ở hai mặt đầu bó, dùng InstancedMesh | |
| "Chi tiết ống" | từng ống là hình trụ rỗng theo OD và độ dày thành nếu có, dùng InstancedMesh, cùng pose với bó | |

D4.2. Bó ENVELOPE_ONLY luôn hiện khối bao, có viền cảnh báo.

D4.3. Đổi cách nhìn không đổi:

- bó đang chọn và ID bắt được khi nhấp chuột (picking vẫn trả ID bó);
- camera;
- bảng, số liệu và trạng thái lưu.

Không tạo lại scene hay GLB. Tái dùng vòng đời scene của SUP-01.

D4.4. Giới hạn hiệu năng:

- Tổng instance ống ở chế độ chi tiết tối đa 60 000.
- Vượt giới hạn thì chỉ dựng chi tiết cho bó đang chọn và các bó trong khung nhìn đến hết hạn mức; phần còn lại giữ bó giản lược. Giao diện báo rõ số bó đang hiện chi tiết.
- Đo thời gian dựng trên 1076 bó, ghi trong worker return, không tuyên bố FPS khi chưa đo.

D4.5. Dùng được ở 390px và khi WebGL không có (2D giữ như cũ, có thêm cột trạng thái packing). Không thêm thư viện.

### D5. Bảng và chi tiết bó

D5.1. Bảng hàng và panel chi tiết bó hiện:

- trạng thái packing;
- cách xếp (RECT/HEX, số cột × số hàng);
- số ống đặt được so với số ống nguồn;
- phần dư theo cm;
- lý do và lời nhắc tiếng Việt, ví dụ "Kiểm lại OD, số ống mỗi bó hoặc kích thước bó trong revision".

D5.2. Lọc được theo trạng thái. Nhấn lý do thì mở nhóm tương ứng trong panel "Dữ liệu hàng" của SUP-02A.

### D6. Ngoài phạm vi SUP-03

- Nhập cách xếp thực tế do người dùng khai (cần SPEC revision mới).
- Va chạm giữa ống.
- Trọng tâm.
- Xếp nhiều tầng (M3).
- Xuất báo cáo (M2d).
- AI.
- Đổi engine.

## SUP-03 acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| S3-01 | Packing thuần theo D1: test cho RECT, HEX, không vừa, OD thiếu hoặc sai, OD lớn hơn mặt cắt; tọa độ nguyên µm, tất định; tổng ống dẫn xuất của R0000 khớp số liệu nguồn cho mọi nhóm DETAILED; có bảng số liệu 31 nhóm Baltimore trong worker return. |
| S3-02 | Trạng thái và lý do theo D2: mỗi mã lý do có ca kiểm; mâu thuẫn ở một nhóm không chặn nhóm khác; nhóm cảnh báo nguồn giữ lý do; thống kê toàn dataset đúng. |
| S3-03 | API theo D3: endpoint chỉ đọc, revision lỗi bị từ chối như SUP-02A; JSON của Plan và snapshot không đổi (có ca hồi quy byte); R0000 hash không đổi. |
| S3-04 | Viewer theo D4: ba cách nhìn; đổi qua lại giữ bó chọn, camera và scene (cùng một đối tượng scene và GLB, kiểm bằng diagnostics opt-in của SUP-01); picking ở chế độ chi tiết trả ID bó; hạn mức 60 000 instance và thông báo; số đo thời gian dựng 1076 bó. |
| S3-05 | Bảng và luồng theo D5: `contracts/openapi.json` và `api.ts` sinh lại; `npm run build` đạt; luồng nội bộ: mở list ống → chọn "Chi tiết ống" → chọn một bó DETAILED và một bó ENVELOPE_ONLY → xem lý do → mở nhóm trong "Dữ liệu hàng" → tạo revision sửa OD → packing của nhóm đổi theo revision mới → phương án cũ "Cần kiểm lại" như SUP-02A; desktop và 390px; mọi test backend và browser cũ đạt; chạy browser không đổi file đã commit dưới `docs/reviews/`. |

## Verification and checkpoint

Mốc: head nhánh SUP-02B khi bắt đầu. Worker ghi số test backend và browser của mốc đó.

Worker phải:

- chạy toàn bộ test backend;
- sinh lại contract và kiểu TypeScript;
- chạy `npm run build`;
- viết `tests/browser/sup03.spec.ts`;
- chạy toàn bộ browser suite và gate worker-return nếu chạy được;
- nếu không chạy được, ghi lệnh và lỗi, không làm yếu kiểm.

Root review tại máy:

- chạy lại backend, build, toàn bộ browser trên cổng 8766 và các gate;
- soát diff theo D1–D6 và vùng file;
- tự đi luồng S3-05.

Sau đó root làm bước kiểm tra tích hợp trước M2d của roadmap: đối chiếu một phương án qua bảng, viewer, kiểm tra, lưu/mở và revision.

Nghiệm thu nghiệp vụ, số đo hầm thực, cách xếp thực tế và M2d vẫn thuộc owner.

Ngân sách: worker 240 phút trên cloud, root review 90 phút, không reset khi sửa.
