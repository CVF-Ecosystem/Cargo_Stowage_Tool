# SCST — Tích hợp tham chiếu VINAFCO 268

Status: APPROVED_FOR_EXECUTION

## Authority and boundary

Owner cung cấp `VINAFCO268_LOCAL_HANDOFF` và yêu cầu đánh giá, dùng được thì tích hợp. Đây là lát cắt được cho phép sớm của lớp hiển thị M2c và dữ liệu tham chiếu M3; không mở toàn bộ M2, không nghiệm thu nghiệp vụ M1. Root orchestrator/reviewer; Terra 6.1 High implementation; Sol-Medium kiểm browser. R2 do có dữ liệu phương tiện thật; ceiling R2. Local-only; không push tài liệu đăng kiểm hoặc dữ liệu mới lên GitHub trong lượt này.

Nguồn local giữ nguyên byte, không commit PDF, dữ liệu chủ phương tiện hoặc URL thư viện cá nhân. Chỉ bản tham số kỹ thuật đã chọn và GLB được đưa vào cây app. PDF trang 1,4,5,6 được root đối chiếu trực quan; chưa xác minh hiệu lực pháp lý hiện tại và không đưa ra kết luận đó.

## Design and contract

Giữ mẫu M1 làm mặc định; thêm chế độ VINAFCO 268. Đọc profile từ backend; GLB local. Giữ React/Three/FastAPI và rules đang có, không cài dependency dựng mesh vào runtime. GLB là tài sản phát sinh, JSON tham số là nguồn; không dùng ảnh nhãn làm đầu vào tính.

Plan mở rộng cộng thêm `source=MIXED_REFERENCE`, nhận dạng phương tiện và operating case có kiểu; `scst.m1.v1` và đường mẫu cũ giữ tương thích. Backend bắt buộc ràng buộc phương tiện/case/hold/giới hạn chứng nhận từ profile; không cho client tự nâng mức hàng theo hồ sơ. Voyage có thể hạ, onboard không âm, giữ quan hệ cũ. Cargo vẫn synthetic; hold BOX ước tính. Giới hạn là mức hàng tham chiếu theo bộ dữ liệu, chưa phải chứng nhận sử dụng phương án thực.

Thân 77,8 × 13,24 × 5,2m. SI/SII: lượng hàng 3282,5/3517,5t; TTTP 3301/3536t hiển thị riêng; mớn tham chiếu 4,60/4,85m; mạn khô giấy 612/362mm giữ riêng D-d. Ghép cặp tải theo thứ tự trình bày, giữ ghi chú. Trang5 có điều kiện container mớn tối đa4,17m; không hỗ trợ xếp container trong lát cắt này. Lightship và tải sàn `null` là chưa có dữ liệu. Không tính thủy tĩnh, trọng tâm toàn tàu, trim, ổn định hoặc sức bền.

Hầm từ JSON: 56,405 × 10,34375 × 5,408m, floor z0,832m. Backend integer-mm dùng 56405 × 10343 × 5408, bề rộng giảm0,75mm, đặt giữa hầm gốc (mỗi mạn lùi0,375mm); UI nêu chuyển đổi này. Không làm tròn lên. GLB Y-up đã đổi trục; chuyển nhóm(-0,9725,-0,832,0) về hệ viewer lấy tâm hầm/sàn làm gốc; cargo local +Y sang GLB +Z (starboard). Giữ mesh chưa scale/rotate thêm.

Hiện đầy đủ thân với vật liệu mờ mặc định, ẩn/hiện vỏ, orbit/zoom/reset và chọn hàng. Marker mớn theo case; màu thân GLB cố định tại4,85m có nhãn riêng. GLB lỗi thì bảng/hầm/chỉnh/kiểm tiếp tục dùng được. Chuyển case giữ hàng và draft hợp lệ, lịch sử gắn đúng case; lỗi/request cũ không ghi đè edit mới. Empty manifest nằm ngoài lượt này vì schema M1 yêu cầu ít nhất1unit; không tạo unit giả để lách.

## VIN acceptance

| ID | Kết quả và bằng chứng bắt buộc |
|---|---|
| VF-01 | Có đánh giá nguồn/manifest/mesh; profile chọn lọc giữ số thực, ước tính, null và ghi chú tải; PDF/personalURL không vào Git hoặc API |
| VF-02 | Backend trả case/profile/asset; integer g/mm, hold bảo thủ, mass limit cargo khác TTTP; từ chối sửa giả nguồn/case/hold/certificate; mặc định M1 hồi quy đạt |
| VF-03 | GLB nạp đúng tỷ lệ/trục, cargo/hold thực tế mesh cùng backend; camera thấy toàn tàu, orbit/zoom/reset/picking và mờ/ẩn vỏ dùng được; chứng cứ bbox/world transform |
| VF-04 | SI/SII đổi đúng tải, mớn marker và nhãn; hàng/draft/history giữ đúng ngữ cảnh; kiểm ví dụ3520t vượt2,5t và3300t vượt17,5t; màu cố định được giải thích |
| VF-05 | UI tiếng Việt phân biệt số theo hồ sơ/hình học ước tính/cargo synthetic; lỗi GLB/network, STALE, fallback2D và mobile không mất dữ liệu hoặc tràn ngang |
| VF-06 | Backend/browser/build/contract checks có kết quả từ source mới, root review độc lập và hướng dẫn dùng; M1 acceptance nghiệp vụ và mốc còn lại vẫn pending |

## Remaining scope and checkpoint

Owner phản hồi sau khi đội phát triển tự chứng minh mô hình/cargo/case chạy được. Orchestrator giữ M2a/b/d và chức năng chỉnh/lưu/so sánh đầy đủ ở roadmap, tái nhập khi owner chọn SPEC tương ứng. Số đo hầm/tuyến hình thật ở M3, owner cung cấp khi có; thiếu đó không chặn minh họa có nhãn. Trần120phút implementation +45phút review/repair, không reset bằng nhãn mới; dừng khi hết trần hoặc thay đổi scope/risk.
