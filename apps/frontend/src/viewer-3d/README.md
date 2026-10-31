# Viewer 3D

**Trách nhiệm:** Hiển thị 3D từ cùng dữ liệu phương án (unit ID, tọa độ, kích thước) mà backend trả về.

**Dùng từ mốc:** M1+.

**Không thuộc thư mục này:** Không đánh giá an toàn hàng hóa và không tự tính lại tọa độ; chỉ là hình chiếu của phương án.

Đã có viewer Three.js và mặt bằng SVG M1, chọn đồng bộ, orbit/zoom/reset, WebGL fallback. Dữ liệu quan sát mesh chỉ đọc phục vụ kiểm; viewer không kiểm quy tắc hoặc phê duyệt.
