# SCST M1 — Khung chạy local

Nguồn: `SCST_Roadmap_Ban_Dau_Tool_First.md`, mục 3–8. Quyền triển khai: yêu cầu owner ngày 31-10-2026. Roadmap này thay điều kiện REVIEW_ONLY cũ cho lát cắt M1. Các tài liệu baseline cũ giữ nguyên để tra cứu.

## Intake và quyết định thiết kế

Một người sử dụng, dữ liệu synthetic, chạy loopback, không provider AI. Rủi ro R1 cho demo; trần workspace R2. Không chứng minh an toàn vận hành hoặc cơ chế quản trị AI. Chuỗi INTAKE → DESIGN → SPEC → WORK_ORDER dùng chung hồ sơ nhỏ này và work order, kế thừa review đã có.

React/TypeScript + Vite, Three.js; Python/FastAPI. Backend là nguồn kiểm duy nhất, stateless. Frontend dùng contract sinh từ OpenAPI. Không database khi chưa có lưu bền. Một server phục vụ API và frontend đã build; dev mode qua Vite proxy. Cài dependency lần đầu cần internet, chạy tool sau đó không cần mạng.

Đơn vị integer gram/mm, từng bó giữ ID riêng. BOX một lớp, yaw bội 90 độ, tọa độ góc nhỏ nhất sau xoay. Chạm mặt được phép; giao phần thể tích dương là va chạm. Required chưa xếp là lỗi kiểm, optional chưa xếp là thông tin, excluded không được xếp. Tổng tải chỉ cộng các bó đã xếp. Dữ liệu structural sai bị API từ chối; bố trí vượt tải/biên được trả về cùng lỗi để sửa.

Thay đổi qua nút kiểm lại: giữ bản trước trong phiên, chỉ nhận kết quả sau backend validation; lỗi mạng không thay phương án đang xem. Refresh mất thay đổi của M1, hiển thị rõ. Không hỗ trợ dữ liệu thật, tối ưu, kê/chồng, ổn định, tải cục bộ hoặc xuất file trong M1.

## M1 acceptance

| ID | Kết quả cần chứng minh | Bằng chứng dự kiến |
|---|---|---|
| M1-01 | Khởi động local, UI gọi API thật, core không AI | Launcher, health, browser smoke |
| M1-02 | Hầm/hàng/plan synthetic; bảng và viewer cùng ID, kích thước, khối lượng từ API | API assertions và UI integration |
| M1-03 | Sửa mass/vị trí/giới hạn tải → kiểm backend, cập nhật bảng/viewer; quay lại bản trước trong phiên | Browser edit, invalid plan, undo, network failure |
| M1-04 | Tải, biên, va chạm, required/optional/excluded và dữ liệu sai được kiểm; đúng sát biên gram/mm | Domain/API tests |
| M1-05 | Viewer 3D có chọn bó, zoom/orbit/reset; mặt bằng 2D và bảng dùng được khi không có WebGL | Browser test và ảnh |
| M1-06 | Hướng dẫn chạy, treeview, phạm vi chưa có và bằng chứng kiểm dễ tiếp tục | docs/APP_GUIDE.md và review |

## Phần tiếp theo

M2 bắt đầu bằng nhập tay manifest/hold và lưu/mở SQLite; sau đó import, heuristic và xuất. M3 cần dữ liệu thực cùng profile kê/chồng; M4 chỉ mở khi có tác vụ AI cụ thể; M5 hoàn thiện cài đặt/backup. Các mốc này chưa được tuyên bố hoàn thành và chưa chi tiết hóa trong M1.
