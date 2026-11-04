# SCST — SUP-02B profile tàu tổng quát, phép đổi tọa độ có kiểm chứng

Status: APPROVED_FOR_EXECUTION

## Authority and design

Ngày 04-11-2026, sau khi SUP-02A được merge (`569c7ee`) và đóng (`dd61bee`), owner giao root tiếp tục roadmap mà không cần hỏi lại. Phạm vi gồm:

- SUP-02B là phần còn lại của SUP-02 theo roadmap bổ sung: "Profile lưu nguồn, GLB, hầm và phép đổi tọa độ có kiểm chứng; không cố định sản phẩm vào một tàu".
- Kèm theo một việc hỗ trợ là sửa quan sát O1 của review SUP-02A (xem S2B-06).

Thực hiện:

- Claude Cloud làm IMPLEMENTATION_WORKER trên nhánh riêng.
- Claude local làm REVIEWER độc lập và COMMIT_STEWARD.
- Risk R2, vì có contract dữ liệu mới, lưu file người dùng và đổi viewer.

Nền code là `dd61bee`, có 222 test backend và 39 ca browser.

Các nguyên tắc DA áp dụng:

- **DA01:** đơn vị nội bộ giữ chính xác. Hầm dùng mm nguyên; GLB và profile nguồn dùng mét.
- **DA02:** lưu trữ mới chỉ ghi thêm, test trên `SCST_DATA_DIR` tạm.
- **DA03:** mỗi số liệu của tàu ghi trạng thái ESTIMATED, SOURCED hoặc MEASURED kèm nguồn.
- **DA04:** tái dùng VesselReference, các route tàu, viewer và luồng phương án; chỉ thêm phần thiếu.
- **DA05:** phải có luồng dùng được trước khi xin phản hồi.

Nguồn giữ bất biến: `services/backend/data/vessels/vinafco268/profile.json`, `model.glb`, `baltimore.json`. VINAFCO 268 trở thành profile dựng sẵn (built-in) đầu tiên, được dẫn xuất từ các file này mà không sửa byte nào.

### D1. Contract `scst.vessel-profile.v1`

D1.1. Model pydantic tổng quát, bỏ hằng `Literal["VINAFCO268"]` ở contract mới. Model gồm các trường:

| Trường | Ràng buộc |
|---|---|
| `id` | `^[A-Z0-9][A-Z0-9-]{1,31}$` |
| `version` | số nguyên từ 1 trở lên |
| `name` | 1–100 ký tự |
| `registration` | tối đa 50 ký tự, có thể rỗng |
| `dimensions_m` | `length`, `beam`, `depth`; số thực > 0 và ≤ 500 |
| `hold` | `id`, `name`, `length_mm`, `width_mm`, `height_mm` là số nguyên mm > 0 và ≤ 500 000, kèm `status` |
| `cases` | 1–20 trường hợp tải, mỗi trường hợp có `id` (`^[A-Z0-9][A-Z0-9-]{0,31}$`), `cargo_mass_g` nguyên > 0, `draft_m` > 0 và các trường tùy chọn `deadweight_t`, `freeboard_mm` |
| `notes` | danh sách tối đa 10 chuỗi, mỗi chuỗi tối đa 500 ký tự |
| `provenance` | xem D1.2 |
| `transform` | xem D2 |
| `landmarks` | xem D2 |

D1.2. `provenance` gồm `source_documents` (1–10 mục, mỗi mục có `title` và `sha256` tùy chọn) và `field_status`. `field_status` là map từ `dimensions_m`, `hold`, `cases` sang ESTIMATED, SOURCED hoặc MEASURED.

D1.3. Profile JSON tối đa 256 KiB. Mọi lỗi trả theo từng trường bằng tiếng Việt.

D1.4. Dẫn xuất VINAFCO268:

- VINAFCO268 v1 được dẫn xuất bằng một adapter từ `profile.json` hiện có.
- Hầm, cases, các ghi chú, provenance và hash nguồn giữ nguyên giá trị.
- Phép đổi tọa độ dẫn xuất phải cho ra đúng vị trí viewer hiện tại: dịch `[-0.9725, -0.832, 0]` m, không xoay, scale 1.

### D2. Phép đổi tọa độ có kiểm chứng

D2.1. `transform` khai báo cách đưa GLB (mét, Y-up) về hệ tọa độ cảnh của viewer hiện tại:

- `translation_m` gồm 3 số.
- `yaw_deg` thuộc {0, 90, 180, 270}.
- Scale cố định bằng 1.

D2.2. Một hàm thuần duy nhất ở backend áp phép đổi. Frontend chỉ dùng giá trị server trả về, không tự xoay, scale hoặc căn tâm thêm.

D2.3. `landmarks` có 3–20 điểm. Mỗi điểm gồm `name`, `glb_m` (tọa độ trong GLB) và `hold_mm` (tọa độ mong đợi trong hệ hầm, mm nguyên).

D2.4. Kiểm chứng gồm hai việc:

- Áp phép đổi cho từng landmark rồi so với `hold_mm`, dung sai tuyệt đối ≤ 1 mm mỗi trục.
- Đọc min/max của accessor POSITION trong GLB bằng thư viện chuẩn để dựng hộp bao. Hộp bao GLB sau phép đổi (cùng hệ với hầm) phải chứa hộp hầm.

Kết quả kiểm trả từng landmark (sai số mm) và kết luận PASS hoặc FAIL. FAIL thì không lưu.

D2.5. Với VINAFCO268, root khai báo landmark từ các góc hầm trong `geometry` của profile gốc. Worker tính và ghi rõ trong worker return. Nếu số liệu gốc không cho PASS thì dừng phần đó và báo, không nới dung sai.

### D3. Kho profile

D3.1. Built-in đọc từ `services/backend/data/vessels/*/profile.json`, chỉ đọc. Hiện chỉ có VINAFCO268.

D3.2. Profile người dùng lưu ở `SCST_DATA_DIR/vessels/<id>/v<version>/`, gồm `profile.json`, `model.glb` và `manifest.json` (sha256 của hai file, thời điểm tạo, kết quả kiểm).

D3.3. Quy tắc ghi:

- Chỉ ghi thêm: không có API sửa hay xóa.
- Ghi vào thư mục tạm rồi đổi tên một lần.
- Không ghi đè version đã có.
- Một version mới của cùng `id` phải có `version` = version mới nhất + 1. Nếu không, trả 409 và không ghi.
- Không được tạo `id` trùng với built-in.

D3.4. Khi đọc, kiểm sha256 của các file. Lệch thì báo không phục vụ được và không tự sửa.

D3.5. Giới hạn:

- GLB ≤ 20 MiB, phải có magic `glTF`, phiên bản 2 và chunk JSON hợp lệ.
- Tối đa 50 version cho mỗi `id` và 50 `id`.
- GLB gửi bằng base64 trong body JSON. Body tối đa 28 MiB, kiểm trước khi parse nếu được. Không thêm `python-multipart` hay phụ thuộc mới.

D3.6. Có endpoint xem trước (không ghi) trả lỗi, kết quả kiểm landmark và hộp bao.

### D4. Tham chiếu trong phương án

D4.1. `VesselReference` mở rộng `vessel_id` theo pattern của D1, thêm `profile_version` và `profile_sha256` tùy chọn.

D4.2. Phương án dùng VINAFCO268 không có hai trường mới:

- Giữ hành vi và JSON byte-identical. Hai trường bị bỏ khỏi JSON khi trống, cùng cách `cargo_revision` của SUP-02A.
- Các kiểm hiện có trong model (hầm, giới hạn theo case) giữ nguyên.

D4.3. Phương án dùng profile người dùng phải có đủ hai trường. Ràng buộc được kiểm ở một tầng dịch vụ dùng chung, cùng chỗ với `plan_binding.bind()` của SUP-02A, ở mọi điểm vào nhận Plan:

- profile tồn tại và sha khớp;
- hầm trùng profile;
- case thuộc profile;
- giới hạn tải bằng `cargo_mass_g` của case.

Không đưa truy cập file vào model pydantic.

D4.4. Snapshot đã lưu không bao giờ bị sửa.

### D5. API

D5.1. Endpoint mới:

| Method | Đường dẫn | Việc |
|---|---|---|
| GET | `/api/vessel-profiles` | danh sách built-in và người dùng, mới nhất trước, kèm trạng thái và kết quả kiểm |
| GET | `/api/vessel-profiles/{id}/{version}` | chi tiết profile |
| GET | `/api/vessel-profiles/{id}/{version}/model` | file GLB |
| POST | `/api/vessel-profiles/preview` | kiểm, không ghi |
| POST | `/api/vessel-profiles` | tạo version |
| GET | `/api/vessel-profiles/{id}/{version}/cases/{case_id}/plan` | dựng phương án tham chiếu như route VINAFCO hiện có |

D5.2. Ba route `/api/vessels/vinafco268...` giữ nguyên response từng byte.

### D6. Giao diện

D6.1. Khung "Tàu và hầm" trong luồng phương án tham chiếu cho phép chọn tàu (built-in hoặc đã nhập) rồi chọn case. Mỗi tàu hiện trạng thái số liệu và nguồn.

D6.2. Biểu mẫu nhập profile:

- Người dùng chọn file JSON và file GLB, xem trước kết quả kiểm (lỗi, sai số từng landmark, hộp bao), rồi tạo version.
- Nút "Tạo profile" chỉ bật sau khi xem trước hợp lệ đúng nội dung đó.

D6.3. Viewer nhận `transform` và URL GLB từ profile đang chọn. Phải bỏ các hằng VINAFCO trong `Scene.tsx`:

- hộp mốc mớn nước 77,8 × 13,24 lấy từ `dimensions_m`;
- dịch lấy từ `transform`;
- vị trí mốc mớn nước lấy từ `draft_m` của case và phép đổi;
- chế độ ghost chỉ áp danh sách tên mesh thân tàu khi profile khai báo `hull_mesh_names` (tùy chọn). VINAFCO268 dẫn xuất ra danh sách hiện có.

Hành vi VINAFCO hiện tại không đổi: các spec browser vinafco/sup01 cũ phải đạt mà không sửa.

D6.4. Giao diện bằng tiếng Việt, kg/cm/m khi hiển thị, dùng được ở 390px, không thêm thư viện.

### D7. Ngoài phạm vi SUP-02B

- Sửa hoặc xóa profile.
- Profile nhiều hầm.
- Tuyến hình, mớn và tính ổn định.
- Tải sàn.
- Container.
- Tự dựng GLB.
- Nhập PDF.
- AI.
- SUP-03.
- M2d.

### D8. Việc hỗ trợ O1

`tests/browser/evidence.ts` ghi ảnh vào thư mục từ biến môi trường `SCST_EVIDENCE_DIR` khi có. Nếu không có, ghi vào thư mục tạm của hệ điều hành theo từng lần chạy. Không ghi vào thư mục bằng chứng đã đóng nữa.

Cho phép sửa đúng file `tests/browser/evidence.ts` và đường dẫn ghi ảnh trong `tests/browser/sup02a.spec.ts`. Không đổi assertion nào.

## SUP-02B acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| S2B-01 | Contract và dẫn xuất theo D1: VINAFCO268 v1 được dẫn xuất từ file gốc, các file gốc không đổi byte; mọi giới hạn D1 có ca kiểm với lỗi tiếng Việt; ba route VINAFCO cũ trả response byte-identical (có ca so byte). |
| S2B-02 | Kiểm chứng tọa độ theo D2: hàm đổi tọa độ thuần có test cho mọi yaw và dịch; landmark VINAFCO268 PASS ≤ 1 mm; landmark lệch hoặc hầm ra ngoài hộp bao GLB thì FAIL và không lưu; đọc hộp bao GLB không dùng thư viện mới; vị trí GLB của VINAFCO trong viewer không đổi (spec cũ đạt). |
| S2B-03 | Kho profile theo D3: xem trước không ghi; tạo version chỉ ghi thêm và ghi nguyên tử; sai version hoặc trùng built-in trả 409 không ghi; sha lệch thì từ chối phục vụ; GLB và JSON sai định dạng, quá giới hạn đều có ca kiểm; mọi test dùng `SCST_DATA_DIR` tạm. |
| S2B-04 | Tham chiếu phương án theo D4: phương án với profile người dùng bị từ chối khi profile không tồn tại, sha lệch, hầm hoặc case sai, ở mọi điểm vào; phương án VINAFCO và snapshot cũ mở, kiểm và lưu như trước, JSON byte-identical (có ca hồi quy); snapshot không bị sửa. |
| S2B-05 | Giao diện và hợp đồng theo D5–D6: `contracts/openapi.json` và `api.ts` sinh lại bằng công cụ hiện có; `npm run build` đạt; luồng nội bộ: mở tàu VINAFCO → nhập một profile thử (JSON + GLB tổng hợp nhỏ do test tạo) → xem trước có sai số landmark → tạo → chọn tàu đó và một case → hầm, mốc mớn và GLB hiển thị đúng phép đổi → lưu phương án → mở lại; desktop và 390px; mọi test backend và browser cũ đạt. |
| S2B-06 | Việc hỗ trợ O1 theo D8: chạy toàn bộ browser suite không làm đổi file nào đã commit dưới `docs/reviews/` (kiểm bằng `git status` sau khi chạy); không assertion nào thay đổi. |

## Verification and checkpoint

Mốc trước BUILD: 222/222 test backend và 39/39 ca browser trên `dd61bee`.

Worker phải:

- chạy toàn bộ test backend;
- sinh lại contract và kiểu TypeScript;
- chạy `npm run build`;
- viết `tests/browser/sup02b.spec.ts` cho luồng S2B-05;
- chạy browser suite và gate worker-return nếu chạy được;
- nếu không chạy được, ghi lệnh và lỗi, không làm yếu kiểm.

Root review tại máy:

- chạy lại backend, build, toàn bộ browser trên DB thử cổng 8766 và các gate;
- soát diff theo D1–D8 và vùng file;
- kiểm không có secret hay phụ thuộc mới;
- tự đi luồng S2B-05.

Lỗi cục bộ có bằng chứng được sửa tại chỗ và công bố; thay đổi thiết kế thì trả lại worker. Checkpoint chỉ chốt kỹ thuật. Nghiệm thu nghiệp vụ, số đo hầm thực, SUP-03 và M2d vẫn thuộc owner.

Ngân sách: worker 240 phút trên cloud, root review 90 phút, không reset khi sửa.
