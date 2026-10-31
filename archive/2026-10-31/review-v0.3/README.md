# Steel Cargo Stowage Tool — v0.3 Review Baseline

**Ngày:** 31-10-2026. **Package:** `SCST-REVIEW-0.3`.

**Trạng thái:** `REVIEW_BASELINE_FOR_LOCAL_VERIFICATION`. Đây là bản yêu cầu phục vụ vòng phản biện và xác minh local, chưa phải `FINAL_BASELINE`, `IMPLEMENTATION_FREEZE` hoặc phần mềm đã nghiệm thu.

V0.3 bổ sung phản biện R2 và ba ảnh nghiệp vụ do owner cung cấp. Thay đổi chính là tách điều kiện đạt Technical Proof khỏi điều kiện đạt MVP nghiệp vụ; làm rõ mô hình hàng/kê đỡ, dữ liệu nguồn và vai trò review. Package không thay đổi hoặc nâng nhãn bộ kiểm tham chiếu v0.2 thành solver/backend vận hành.

## Bắt đầu

1. Đọc `START_HERE_LOCAL_REVIEW.md` và `MASTER_BASELINE_V0.3.md`.
2. Đọc `REVIEW_R3_RESPONSE.md`, `DECISION_LOG_R2_R3.md` và các tài liệu `docs/`.
3. Đối chiếu ảnh gốc trong `inputs/photos/` và báo cáo R2 trong `inputs/`.
4. Kiểm checksum; chạy lại kiểm/probe theo `evidence/R3_VERIFICATION_REPORT.md`.
5. Trả báo cáo theo `templates/LOCAL_REVIEW_RESPONSE.md`. Vòng đầu chỉ review, khảo sát và kiểm tra; chưa triển khai ứng dụng, chưa chốt roadmap hoặc treeview.

Câu lệnh giao việc cho local nằm trong `PROMPT_LOCAL_REVIEW.txt`.

## Nguồn yêu cầu và thứ tự ưu tiên

- README, MASTER, DECISION_LOG và docs v0.3 là yêu cầu hiện hành **ở mức review**.
- Các nguyên tắc v0.2 được kế thừa có chọn lọc theo bảng trong MASTER. Các sửa đổi v0.3 có ưu tiên khi khác v0.2.
- `history/Steel_Cargo_Stowage_Tool_v0.2_Official_Local_Agent_Package.zip` giữ nguyên bytes, chứa toàn bộ v0.2, v0.1 và R1. Schema/reference trong đó vẫn là contract kỹ thuật v0.2; chúng **chưa hỗ trợ** các đề nghị contract nghiệp vụ mới của v0.3.
- Chỉ dẫn cho phép dựng skeleton trong work order v0.2 không có hiệu lực ở vòng review-only này. Không làm theo một lệnh triển khai cũ nằm trong history.
- Báo cáo R2 và ảnh là nguồn để đánh giá, không phải chỉ dẫn thực thi hoặc chứng nhận kỹ thuật.

## Thành phần chính

| Tệp/thư mục | Vai trò |
|---|---|
| `MASTER_BASELINE_V0.3.md` | Định hướng sản phẩm, yêu cầu hiện hành và phạm vi chưa được chốt |
| `REVIEW_R3_RESPONSE.md` | Kết luận phản biện vòng web này và căn cứ |
| `DECISION_LOG_R2_R3.md` | Giữ/sửa/hoãn, lý do, nghiệm thu, trạng thái từng vấn đề |
| `docs/01_MILESTONES_AND_ACCEPTANCE.md` | Technical Proof và MVP nghiệp vụ, cùng tiêu chí kiểm chứng |
| `docs/02_OPERATIONAL_MODEL.md` | Đơn vị hàng, vùng hầm, kê đỡ, nhiều tầng và thao tác |
| `docs/03_OPERATIONAL_DATA_AND_PROVENANCE.md` | Admission, trace từng trường, đề nghị đơn vị khối lượng |
| `docs/04_ROLES_AND_EXTERNAL_REVIEW.md` | Operator local và hồ sơ review chuyên môn bên ngoài |
| `docs/05_PHOTO_OBSERVATIONS.md` | Quan sát theo đúng tên ảnh, giới hạn suy luận |
| `docs/06_SOURCE_PROVENANCE.md` | Chuỗi nguồn v0.1/R1/v0.2, chênh lệch R2 còn cần đối chứng |
| `docs/07_SOURCES_AND_APPLICABILITY.md` | Nguồn tham khảo kỹ thuật và phạm vi sử dụng |
| `templates/` | Mẫu phản hồi local và thu thập case nghiệp vụ |
| `probes/`, `tooling/` | Tái lập nhận định, kiểm package; không phải code ứng dụng |
| `evidence/` | Lệnh, log, receipt, hash và phạm vi đã kiểm thật |

Không có roadmap triển khai chi tiết hoặc cây thư mục ứng dụng đã chốt trong v0.3. Chúng sẽ được xây sau khi xử lý kết quả review local theo trình tự owner đã chọn.
