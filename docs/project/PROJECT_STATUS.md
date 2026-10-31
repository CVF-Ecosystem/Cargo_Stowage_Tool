# Trạng thái project

Cập nhật: **31-10-2026**.

## VINAFCO 268 — lát cắt bổ sung đã kiểm kỹ thuật

Owner cung cấp gói đăng kiểm/mô hình và yêu cầu đánh giá, dùng được thì tích hợp. Đã thêm chế độ **Xem VINAFCO 268**: thân theo hồ sơ77,8 ×13,24 ×5,2m, hầm/cabin/tuyến hình ước tính, hàng synthetic. Có GLB mờ/ẩn-hiện, chọn VR-SI/VR-SII, marker mớn và profile do backend ràng buộc. Mẫu M1 vẫn mặc định; giới hạn chuyến đang có được giữ khi chuyển chế độ.

[Assessment](../reviews/SCST_VINAFCO268_ASSESSMENT.md) và [review](../reviews/SCST_VINAFCO268_REVIEW.md) ghi nguồn/giới hạn; 63 backend, 9 browser và109 kiểm độc lập đạt. Work order VINAFCO268 đóng phần kỹ thuật, nghiệm thu nghiệp vụ còn chờ. Đây là phần viewer được cho làm sớm, không hoàn tất M2c/M2/M3. PDF/gói gốc giữ local ngoài Git; chưa push các artifact mới lên GitHub.

## Chỉ đạo và phần đã làm

Owner thống nhất hướng M0 (SCST-D001), chọn tận dụng M1 có chọn lọc và chỉ đạo tiếp tục bằng root orchestrator/reviewer, Terra 6.1 High worker và Sol-Medium cho phần khó ([SCST-D002](../decisions/SCST_D002_M1_REUSE_EXECUTION.md)).

Đã chuyển source theo [SPEC M1 v0.2](../specs/SCST_M1.md) và [WORK_ORDER M1](../work_orders/SCST_M1_REUSE.md). Root review khác hai worker của lượt này; [báo cáo M1](../reviews/SCST_M1_REVIEW.md) xác minh đủ 9 tiêu chí kỹ thuật. Owner chưa nghiệm thu nghiệp vụ; M2 tổng thể chưa được giao thi công, chỉ có lát cắt VINAFCO268 riêng phía trên.

## M1 hiện có

Demo synthetic BOX một lớp, bảng/3D/2D cùng dữ liệu, giới hạn chứng nhận/chuyến/onboard, kiểm tải/biên/va chạm/hàng bắt buộc, draft/STALE, sửa–kiểm lại–undo và fallback WebGL. Khởi chạy bằng `Start-SCST.cmd`; xem [APP_GUIDE](../APP_GUIDE.md). Không lưu bền; refresh mất thay đổi.

51 backend test, 5 browser test và 498 kiểm độc lập đạt. Cold setup/launcher, chạy với chặn truy cập ngoài loopback, schema/types regeneration và archive identity có evidence. Xem giới hạn kiểm và cảnh báo còn lại trong review; không sử dụng demo cho phương án thực.

## Source cũ và nguồn tham khảo

[Archive M1](../../archive/2026-10-31/paused-m1/README.md) giữ nguyên 50 file; chỉ lấy thành phần đã chọn và sửa trên cây mới. Test/log/ảnh cũ không được dùng làm nghiệm thu bản mới. [Đánh giá tái sử dụng](../reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) lưu căn cứ và lịch sử recheck.

[Roadmap gốc](SCST_Roadmap_Ban_Dau_Tool_First.md), [roadmap tổng thể](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) và [tài liệu tham khảo](../reference/README.md) tiếp tục làm nguồn định hướng. Lỗi authority work order khung đã sửa bằng snapshot revision dispatch; gate kiểm trực tiếp đạt.

## Bước tiếp theo

Owner đồng ý bổ sung hình tàu minh họa vào roadmap v0.3; sau đó cho phép tích hợp VINAFCO268 có chọn lọc. Lớp này đã có, backend vẫn kiểm theo hầm BOX ước tính; hiệu chỉnh theo số đo hầm/tuyến hình thực vẫn thuộc M3.

Owner xem demo và phản hồi về hướng dùng. M2 nhập/import/lưu/xếp sơ bộ/export chỉ chi tiết hóa khi được chọn; nhiều tầng và case thực ở M3, AI tùy chọn M4, vận hành M5. Không tự suy diễn kiểm kỹ thuật M1 thành nghiệm thu nghiệp vụ hoặc quyền làm mốc tiếp theo.
