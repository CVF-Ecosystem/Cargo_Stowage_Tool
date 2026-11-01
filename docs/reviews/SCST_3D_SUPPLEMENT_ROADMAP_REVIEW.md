# SCST — Review roadmap bổ sung 3D và dữ liệu

Status: REVIEWED_FOR_OWNER
Risk: R1
Worker: Terra-6.1-High
Reviewer: root-orchestrator

Ngày 01-11-2026, owner yêu cầu chốt roadmap bổ sung trước thi công. [Roadmap](../roadmaps/SCST_ROADMAP_BO_SUNG_3D_VA_DU_LIEU.md) đã được đối chiếu với các trao đổi về viewer, dữ liệu bổ sung từ nhà máy/khách hàng, packing và tọa độ. Kết quả lượt này là tài liệu định hướng; ba năng lực SUP vẫn **NOT_STARTED**, chưa có SPEC/WORK_ORDER triển khai mới.

## Các điểm đã chốt

| Nội dung | Kết luận review |
|---|---|
| Thứ tự và phạm vi | SUP-01 viewer → SUP-02 revision hàng/profile tàu → SUP-03 packing chi tiết → checkpoint tích hợp → M2d. M0–M5 giữ nguyên; M3 nhiều tầng, M4 AI tùy chọn và M5 vận hành vẫn riêng. |
| Tái sử dụng | Giữ React/Three/FastAPI, GLB, Plan, rules, history, SQLite và những luồng đã kiểm; không nhập lại gói nguồn hoặc đổi engine vì audit. |
| Dữ liệu phát triển theo thực tế | Nguồn gốc bất biến, revision làm việc có provenance và phạm vi cập nhật từng bó/nhóm/lô; bản lưu giữ revision cũ. Cảnh báo tạo đường bổ sung dữ liệu, không khóa toàn sản phẩm vào bộ Baltimore hoặc 16 bó hiện thiếu thông tin. |
| Packing và hình chi tiết | Đủ đầu vào thì dựng/kiểm chi tiết theo nguồn; thiếu/mâu thuẫn thì giữ biểu diễn phù hợp cho nhóm bị ảnh hưởng. Mức đồ họa không thay số bó, khối lượng hoặc kích thước nghiệp vụ. |
| Tọa độ | VINAFCO hiện đã đúng; mở rộng bằng profile có phép đổi được kiểm, không thêm lại translation/scale/đổi trục đang có. |
| Kiểm nội bộ và phần còn lại | Mỗi SUP có đầu ra, phụ thuộc, checkpoint và chủ sở hữu trong coverage. Đội phát triển chịu trách nhiệm kỹ thuật/luồng sản phẩm trước phản hồi nghiệp vụ. Thiếu chứng cứ chuyên môn vẫn giới hạn kết luận vận hành. |
| Quyền thi công | Owner chốt kế hoạch, không cấp BUILD trong lượt này. Bước kế tiếp khi được chọn chỉ chi tiết hóa SPEC SUP-01, sau đó mới WORK_ORDER; không tự mở đồng thời ba phần. |

Root độc lập đọc bản do worker soạn, kiểm nguồn và bổ sung làm rõ hai điểm: giữ scene/camera khi cùng tàu/hầm nhưng cập nhật có chủ đích khi đổi profile; cho nhận thông tin từ khách hàng và theo từng trường/nhóm/bó. Root viết coverage, liên kết và continuity. Terra đã đọc lại bản sau bổ sung của root và xác nhận không có điểm chặn; đã làm rõ phân biệt bản làm việc cần kiểm lại với snapshot cũ bất biến. Đây là công việc tài liệu R1; không có thay đổi runtime hoặc tuyên bố đã kiểm một tính năng SUP mới.

## Bằng chứng nền đã có

- [So sánh nguồn](SCST_3D_SUPPLEMENT_EVIDENCE/source-identity.json): 23 file chung giống từng byte, không file chung nào đổi; tài liệu audit mới thêm, cache Python sinh ở máy cũ không còn. 22 mục manifest đạt; GLB trùng asset runtime. Audit chỉ là đầu vào tham khảo, phần “triển khai” trong đó không thay thế chỉ đạo của owner.
- [Kiểm tọa độ](SCST_3D_SUPPLEMENT_EVIDENCE/coordinate-check.json), [probe tái lập](SCST_3D_SUPPLEMENT_EVIDENCE/coordinate-check.cjs): lượt kiểm chỉ đọc ngay trước roadmap đã đối chiếu sáu điểm mốc và 12 mesh hàng trên app 8765, SQLite người dùng không đổi. JSON `(40,1,2)` → GLB `(1.1,2,-1)` → cảnh hầm `(0.1275,1.168,-1)`; translation hiện có `(-0.9725,-0.832,0)` m. Không suy ra hầm đo thực từ phép kiểm căn chỉnh.
- Source được review ở nền `3b03aa6`: scene effect dựng lại theo Plan/hull visibility, diagnostic bounds/JSON theo mỗi render, camera cố định và material toàn tàu mờ là cơ sở chọn SUP-01. Đây là quan sát source; chưa có benchmark FPS hoặc mức tăng hiệu năng để công bố.
- Bằng chứng 31 browser/104 backend và các review trước thuộc runtime đã giao; không dùng chúng để đánh dấu SUP-01/02/03 đã triển khai. Không chạy lại bộ kiểm ứng dụng cho thay đổi tài liệu.

## Kiểm tài liệu và bàn giao

Lượt gate đầu phát hiện README điều hướng trong thư mục roadmap thiếu coverage riêng (`COV_BLOCK_REQUIRED`). Root phục hồi README đó về bản kế thừa; roadmap mới vẫn được dẫn từ README chính, roadmap tổng thể và index. Receipt thất bại được giữ lại; không sửa gate hoặc authority lịch sử để bỏ qua phát hiện.

Phạm vi kiểm cuối gồm toàn bộ ba dòng coverage và authority hash mới, bảo toàn bảng mốc/acceptance lịch sử, liên kết local, catalog, canonical state/handoff/memory/truth, source/runtime ngoài phạm vi không đổi và tập file commit. Receipt nằm trong [gói evidence](SCST_3D_SUPPLEMENT_EVIDENCE/gates/README.md). Các gate chỉ có phạm vi cơ học đã INVOKED; không phải proof AI governance, hermetic hay hosted CI. Không gọi provider API hoặc cần Web bridge cho lượt tài liệu này.

Kết quả: [18 kiểm tra toàn vẹn tài liệu](SCST_3D_SUPPLEMENT_EVIDENCE/document-integrity.json) đạt; catalog Check đạt; reviewer-fast 8/8 và pre-commit 7/7 control đạt, trong đó các control dispatch/work-order không áp dụng có lý do vì không mở lệnh thi công. Lượt thất bại ban đầu được giữ riêng, không tính là lần kiểm đạt. Commit chỉ gồm tài liệu và evidence của đợt này.

45 phút là trần riêng của lượt lập/review tài liệu, không phải ước lượng thi công ba SUP; elapsed/billing một phần UNKNOWN, không reset ngân sách khi sửa. Gói local mới vẫn ngoài tập commit. Chốt roadmap không đóng M2/M3 hoặc nghiệm thu sản phẩm; dữ liệu/packing cụ thể và contract đo được sẽ được đội phát triển chi tiết hóa đúng lượt.
