# SCST — Kiểm tra tích hợp trước M2d

Status: CHECKPOINT_TECHNICAL_PASS
Risk: R2
Worker: Claude Cloud implementation workers of SUP-02A/02B/03 (integrated product under check; no new implementation here)
Reviewer: root-independent-implementation-reviewer

Đây là checkpoint "Kiểm tra tích hợp trước M2d" của roadmap bổ sung, chạy sau khi SUP-01, SUP-02A, SUP-02B và SUP-03 đã vào `main`. Merge commit gần nhất là `164dce5`, closure là `52351e1`.

- Root (Claude local) tự viết và chạy kịch bản, không có worker tham gia.
- Kịch bản: [tooling/integration_check_pre_m2d.py](../../tooling/integration_check_pre_m2d.py). Kết quả: [integration-check-output.txt](SCST_INTEGRATION_PRE_M2D_EVIDENCE/integration-check-output.txt).
- Kịch bản dùng `SCST_DATA_DIR` tạm và gọi API thật qua TestClient. Không chạm DB người dùng.

## Kết quả: 29/29 PASS

Một mục ban đầu FAIL là do kỳ vọng root viết sai, không phải lỗi sản phẩm. Root đã giả định khai lại OD sẽ làm đổi provenance của đơn vị. Thực tế OD không thuộc dữ liệu đơn vị của Plan, đúng quyết định đã chấp nhận ở review SUP-03. Root sửa kỳ vọng rồi chạy lại.

| Nhóm | Đối chiếu | Kết quả |
|---|---|---|
| 1. Phương án A | VINAFCO VR-SII cùng list Baltimore v1, bộ xếp, lưu và mở lại | Giữ tàu và case, đủ 1076 đơn vị. Bộ xếp đặt 167 bó, 909 bó còn lại có lý do. Không vượt giới hạn chứng nhận. Mở lại khớp hoàn toàn. |
| 2. Revision R0001 | Khai lại OD, ghi đè khối lượng một bó đã đặt, bớt một bó | Xem trước và tạo khớp hash, số bó, khối lượng. Bó bị bỏ và bó bị đổi đúng ID. |
| 3. Kiểm lại | Danh sách phương án | A là NEEDS_RECHECK, ghim R0000; bỏ 1, đổi 1, 1 bó đã đặt bị ảnh hưởng. |
| 4. Packing R0001 so với Plan | Số bó, số ống, nhóm chỉ hiện khối bao | Số bó của packing bằng số đơn vị Plan và bằng revision (1075). Tổng ống nguồn 21 184 khớp tổng từ đơn vị; khớp cả từng đơn vị. Ba nhóm chỉ hiện khối bao trùng đúng ba nhóm có cảnh báo kích thước nguồn. |
| 5. Tạo bản mới, so sánh, lưu B | — | Chỉ bỏ vị trí của bó đổi khối lượng; giữ 166 vị trí. Ứng viên giữ tàu, case, giới hạn và qua cổng binding. So sánh cho chênh lệch khối lượng đã đặt −694,8 kg, đúng bằng bó bị bỏ. B là CURRENT. **Byte của snapshot A không đổi.** |
| 6. Tàu người dùng | Profile tổng hợp và list ghim R0001 | Profile qua kiểm landmark rồi được tạo. Ứng viên giữ tham chiếu profile (sha). Bộ xếp không vượt giới hạn của case. Lưu, mở lại và CURRENT. Sửa sha thì bị từ chối ở validate (422) và lưu (400). |
| 7. Revision R0002 | Thu nhỏ một bó đã đặt trên tàu người dùng | B và U đều chuyển NEEDS_RECHECK. Tạo bản mới cho U giữ tàu người dùng, chỉ bỏ đúng bó đó. Packing R0002 dựng riêng cho bó bị ghi đè. |
| 8. Nguồn | `baltimore.json`, profile và GLB của VINAFCO | Không đổi byte nào. |

Phần giao diện đã được kiểm ở toàn bộ browser suite trên `main` (46/46, xem review SUP-03):

- đổi cách nhìn vẫn giữ bó đang chọn và camera;
- nhấp chuột chọn được bó ở chế độ chi tiết;
- bảng và panel packing đúng với dữ liệu;
- dùng được ở 390px.

## Kết luận checkpoint

Về kỹ thuật, các phần đã khớp nhau: bảng, viewer, kiểm, lưu/mở, revision, profile tàu và packing. ID, revision, nguồn, vị trí, số lượng, khối lượng và cảnh báo nhất quán xuyên suốt. **Không có lỗi chặn M2d.**

Phần chưa đạt, mỗi phần đều có người phụ trách:

- **Bộ xếp một tầng chỉ đặt được 167/1076 bó Baltimore vào hầm VINAFCO ước tính.**
  - Đây là giới hạn đã biết của M2b: một tầng, heuristic.
  - Nhiều tầng thuộc M3, cần số đo hầm thật và case thực từ owner.
  - Một báo cáo M2d trên dữ liệu này chỉ phản ánh phương án một tầng.
- **Dữ liệu chưa xác minh:** hầm VINAFCO vẫn là ESTIMATED; 16 bó của R022/R031/R032 vẫn chỉ hiện khối bao; packing là DERIVED. Xác minh thuộc owner.
- **Quan sát còn mở:** O2–O9 trong các review SUP-02A, SUP-02B và SUP-03.

Theo thứ tự roadmap tổng (M2a → M2b → M2c → **M2d** → M3), bước kế tiếp là M2d: xuất báo cáo PDF/XLSX với dữ liệu bảng, 3D và báo cáo khớp nhau. Owner đã cho phép root làm tiếp không cần hỏi, nên root mở SPEC M2d có giới hạn.

- Báo cáo ghi rõ "chưa xác minh hình học" và phương án một tầng, đúng điều kiện roadmap cho trường hợp chưa có dữ liệu thật.
- M3 chờ owner cung cấp số đo hầm và case thực.
