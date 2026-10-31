# Trạng thái project

Cập nhật: **31-10-2026**.

## Chỉ đạo hiện hành

Ngày 31-10-2026 owner đã **thống nhất hướng tổng thể (M0)**, ghi tại [quyết định SCST-D001](../decisions/SCST_D001_THONG_NHAT_HUONG_M0_2026-10-31.md). [Roadmap v0.2](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) là căn cứ giữ hướng, đã áp dụng các góp ý của bản đánh giá.

Đã tạo **khung thư mục M1** theo treeview (11 thư mục, mỗi thư mục có README ghi trách nhiệm, chưa có code) theo [work order SCST_M1_SKELETON](../work_orders/SCST_M1_SKELETON.md), đã đóng. Thống nhất hướng và khung thư mục chưa phải nghiệm thu mốc app nào; chưa có quyền viết code app.

## Phần còn sử dụng

- [Roadmap ban đầu](SCST_Roadmap_Ban_Dau_Tool_First.md): giữ nguyên bytes, là đầu vào thảo luận về mục tiêu tool-first và các mốc M1–M5.
- [Nguồn tham khảo](../reference/README.md): thiết kế gốc v0.1, mô hình nghiệp vụ, vấn đề dữ liệu và ảnh quan sát.
- Bộ CVF tại `.cvf/`, `AGENTS.md`, `CVF_SESSION/`, `scripts/` và catalog: tiếp tục dùng để quản lý công việc sau khi thống nhất kế hoạch.

## Phần chưa được chốt

- [SPEC M1 v0.2](../specs/SCST_M1.md): đã hoàn tất soạn và recheck, vẫn là DRAFT chờ owner thống nhất danh mục tái sử dụng, tải/hầm mục tiêu trống và trạng thái/draft.
- Phiên bản stack, endpoint, schema chi tiết và thuật toán; chốt trong SPEC của từng phần.
- Tiêu chí nghiệm thu các mốc sau M1.

Các lựa chọn từng được agent ghi trong SPEC/work order M1 chưa được xem là những quyết định đã chốt với owner.

## Bản M1 đã viết

Đã chuyển nguyên source, contract, tests, hướng dẫn và bằng chứng chạy vào [archive/2026-10-31/paused-m1](../../archive/2026-10-31/paused-m1/README.md). Đây là bản thử bị tạm dừng, không phải bản M1 đã được nghiệm thu. Những kết quả test cũ chỉ phản ánh bản thử tại thời điểm chạy.

Ở root hiện chỉ có khung thư mục M1 (README, chưa có code); không có server demo được khởi chạy. `IMPLEMENTATION_STATUS.json` không ghi nhận capability ứng dụng đã được chấp nhận.

## Bước tiếp theo

Owner đã chọn tận dụng M1 cũ có chọn lọc. Claude đã recheck và cập nhật SPEC v0.2; Codex tiếp quản, kiểm lại và hoàn tất bàn giao. [Báo cáo nguồn → đích, mục 9](../reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md#9-kết-quả-recheck-và-tiếp-quản) ghi kết quả từng nhóm và phần còn lại. Chưa chuyển source.

Lỗi hash nguồn tiêu chí của work order khung đã được sửa bằng snapshot của revision dispatch; kiểm trực tiếp work order hiện đạt. Đây là sửa hồ sơ lịch sử, không phải nghiệm thu M1.

Owner chốt SPEC v0.2/phần được lấy; agent đăng ký acceptance và soạn WORK_ORDER M1. Chỉ tiếp tục triển khai khi được cho tiếp tục theo SPEC và WORK_ORDER phù hợp. Không dùng work order M1 trong archive để tự nối lại BUILD.
