# Trạng thái project

Cập nhật: **31-10-2026**.

## Chỉ đạo và phần đã làm

Owner thống nhất hướng M0 (SCST-D001), chọn tận dụng M1 có chọn lọc và chỉ đạo tiếp tục bằng root orchestrator/reviewer, Terra 6.1 High worker và Sol-Medium cho phần khó ([SCST-D002](../decisions/SCST_D002_M1_REUSE_EXECUTION.md)).

Đã chuyển source theo [SPEC M1 v0.2](../specs/SCST_M1.md) và [WORK_ORDER M1](../work_orders/SCST_M1_REUSE.md). Root review khác hai worker của lượt này; [báo cáo M1](../reviews/SCST_M1_REVIEW.md) xác minh đủ 9 tiêu chí kỹ thuật. Owner chưa nghiệm thu nghiệp vụ; không mở M2.

## M1 hiện có

Demo synthetic BOX một lớp, bảng/3D/2D cùng dữ liệu, giới hạn chứng nhận/chuyến/onboard, kiểm tải/biên/va chạm/hàng bắt buộc, draft/STALE, sửa–kiểm lại–undo và fallback WebGL. Khởi chạy bằng `Start-SCST.cmd`; xem [APP_GUIDE](../APP_GUIDE.md). Không lưu bền; refresh mất thay đổi.

51 backend test, 5 browser test và 498 kiểm độc lập đạt. Cold setup/launcher, chạy với chặn truy cập ngoài loopback, schema/types regeneration và archive identity có evidence. Xem giới hạn kiểm và cảnh báo còn lại trong review; không sử dụng demo cho phương án thực.

## Source cũ và nguồn tham khảo

[Archive M1](../../archive/2026-10-31/paused-m1/README.md) giữ nguyên 50 file; chỉ lấy thành phần đã chọn và sửa trên cây mới. Test/log/ảnh cũ không được dùng làm nghiệm thu bản mới. [Đánh giá tái sử dụng](../reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) lưu căn cứ và lịch sử recheck.

[Roadmap gốc](SCST_Roadmap_Ban_Dau_Tool_First.md), [roadmap tổng thể](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) và [tài liệu tham khảo](../reference/README.md) tiếp tục làm nguồn định hướng. Lỗi authority work order khung đã sửa bằng snapshot revision dispatch; gate kiểm trực tiếp đạt.

## Bước tiếp theo

Owner xem demo và phản hồi về hướng dùng. M2 nhập/import/lưu/xếp sơ bộ/export chỉ chi tiết hóa khi được chọn; nhiều tầng và case thực ở M3, AI tùy chọn M4, vận hành M5. Không tự suy diễn kiểm kỹ thuật M1 thành nghiệm thu nghiệp vụ hoặc quyền làm mốc tiếp theo.
