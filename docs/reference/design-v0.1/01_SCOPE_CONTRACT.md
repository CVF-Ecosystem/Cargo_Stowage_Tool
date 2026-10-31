# 01 — Scope Contract v0.1

**Status:** `DRAFT_FOR_LOCAL_REVIEW`; **Owner:** Product owner + technical reviewer.

## Mục tiêu

Từ manifest hàng hóa + hồ sơ tàu/sà lan + vùng hầm hữu dụng ước tính: kiểm tra thông tin đầu vào, đề xuất **phương án sơ bộ** sắp xếp các bó thép, xác định tổng lượng hàng được chọn/xếp/chưa xếp, hiển thị 3D tương tác, lưu và so sánh các phương án; AI có thể hỗ trợ giải thích và hỏi thông tin thiếu.

Không xây hệ thống điều phối khai thác cảng. Không thay thế tính toán/duyệt ổn định, sức bền, chằng buộc của người có chuyên môn.

## Ranh giới MVP

**In-scope**
- Import tài liệu phương tiện ảnh/PDF và manifest Excel/CSV; xử lý mâu thuẫn/hỏi lại; xác nhận thông số trọng yếu.
- Vessel Profile, Hold Profile dạng hộp hoặc hình thang đơn giản, Loading Case và giới hạn tải của chuyến.
- Thép thanh **đóng bó** (`BUNDLED_REBAR`) và thép ống **đóng bó** (`BUNDLED_PIPE`) nếu đã khai báo chính xác hình khối bao ngoài, giới hạn đặt/chồng và điều kiện kê đỡ; nhóm khác là `UNSUPPORTED` cho đến khi bổ sung profile đã được review.
- Kiểm tra hard constraints đã có đủ dữ liệu; mô hình 2.5D phục vụ solver; hiển thị 3D từ cùng dữ liệu tọa độ.
- Nhiều lần chạy solver với mục tiêu rõ và giới hạn thời gian; báo lý do hàng chưa xếp.
- Chỉnh phương án thủ công, **revalidate qua backend**; lịch sử, approval, audit, backup/restore.
- AI tùy chọn: hỏi bổ sung, giải thích, gọi công cụ được cấp quyền; vẫn dùng được khi AI offline.

**Out-of-scope**
- ERP/WMS, điều phối xe/cẩu/nhà máy, lịch bến, lập sơ đồ móc cẩu, điều khiển thiết bị.
- Tự chứng nhận trim/list, ổn định, sức bền vỏ, tải cục bộ, lực chằng buộc khi không có dữ liệu/hồ sơ thẩm định.
- Camera detection, mô phỏng cơ học vật rắn chi tiết, 3D CAD kết cấu hầm, hàng rời; thép cuộn chưa được hỗ trợ ở v0.1.
- Mở nhiều người truy cập, cloud service, microservices.

## Định nghĩa trạng thái không gây hiểu lầm

- `DRAFT`: dữ liệu/phương án chưa đủ kiểm tra.
- `GEOMETRY_FEASIBLE`: phương án trong hình học khai báo, không giao cắt; **không** phải chứng nhận an toàn.
- `RULES_CHECKED`: đã chạy toàn bộ rules áp dụng có thể kiểm tra bằng dữ liệu hiện có; report có PASS/FAIL/NEEDS_REVIEW/NOT_EVALUATED/NOT_APPLICABLE.
- `USER_SELECTED`: người dùng chọn phương án, có dấu vết chấp thuận; không mặc định được phép thi công.
- `FIELD_HANDOFF_RECORDED`: đã đính kèm chứng nhận rà soát tại hiện trường của người có trách nhiệm theo quy trình đơn vị; Tool không tự phát hành giấy phép vận tải.
- `STALE`: đầu vào hay rule snapshot thay đổi, cần tính/kiểm tra lại trước khi sử dụng.

Không sử dụng từ `SAFE`, `CERTIFIED` hoặc `EXECUTION_READY` chỉ vì solver báo khả thi.

## Quy tắc quyền hạn

- User/đơn vị chuyên môn quyết định phương án trước khi triển khai; không phê duyệt được một plan vượt hard constraints.
- AI không tự thay hồ sơ hợp lệ, trích xuất không tương đương xác nhận, không gọi approval dưới danh nghĩa user.
- Backend duy nhất kiểm soát ghi, xác nhận và tính toán, frontend chỉ hiển thị.

## Điều kiện đầu vào tối thiểu để khởi chạy solver

1. Vessel identity và giấy chứng nhận chính đã xác minh; hiệu lực phù hợp thời điểm lập chuyến.
2. `certificateCargoLimitKg` được xác minh từ trường *lượng hàng* hoặc hồ sơ hợp lệ; không dùng nhầm `trọng tải toàn phần`.
3. `voyageCargoLimitKg` được người có trách nhiệm xác nhận theo chuyến, có nguồn/giải thích; không vượt giới hạn chứng nhận.
4. `cargoAlreadyOnboardKg` được xác nhận.
5. Kích thước vùng hầm hữu dụng + dự phòng an toàn hình học, nguồn đo/ước tính.
6. Manifest có cargo units và các trường thiết yếu, hỗ trợ profile xếp/chồng phù hợp.
7. Rule set active có phiên bản; các rule cần thiết cho phạm vi tính sơ bộ có dữ liệu áp dụng.

Chưa đủ: lưu intake DRAFT và hỏi lại; **không chạy solver với số đo AI tự đoán**.

## Phương pháp diễn giải sai số

Sai số cho phép *khi diễn giải hình học sơ bộ* chỉ theo dung sai đã khai báo; dùng **biên an toàn bảo thủ** (thu nhỏ không gian xếp, nới kích thước bao ngoài kiện nếu cần), không tự cộng dung sai dương vào tải trọng tối đa. Khối lượng tổng tính bằng integer kg; không làm tròn xuống để vượt giới hạn.

## Boundary test bắt buộc

- Tắt AI: nhập manifest, chọn hồ sơ, chạy validator/solver, xem 3D, lưu phương án vẫn hoạt động.
- Nút phê duyệt frontend hoặc API không thể làm chuyển trạng thái khi thiếu kiểm tra hoặc approval actor thật.
- Tài liệu quy định tham khảo không tự trở thành một `hard rule` cho phương tiện nội địa nếu chưa có rà soát về hiệu lực và phạm vi.
