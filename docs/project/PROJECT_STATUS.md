# Trạng thái project

Cập nhật: **31-10-2026**.

## Chỉ đạo hiện hành

Owner đã yêu cầu dừng triển khai để thống nhất thứ tự và kế hoạch. Chỉ đạo mới nhất cho phép soạn roadmap tổng thể gọn, treeview dự kiến, phạm vi và đầu ra từng mốc. Chỉ chi tiết hóa phần sắp làm sau khi thống nhất hướng đó.

Đã có [bản đề xuất v0.1](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md), trạng thái **DRAFT**, đang ở DESIGN. Đây chưa phải roadmap final hoặc quyền tiếp tục xây app.

## Phần còn sử dụng

- [Roadmap ban đầu](SCST_Roadmap_Ban_Dau_Tool_First.md): giữ nguyên bytes, là đầu vào thảo luận về mục tiêu tool-first và các mốc M1–M5.
- [Nguồn tham khảo](../reference/README.md): thiết kế gốc v0.1, mô hình nghiệp vụ, vấn đề dữ liệu và ảnh quan sát.
- Bộ CVF tại `.cvf/`, `AGENTS.md`, `CVF_SESSION/`, `scripts/` và catalog: tiếp tục dùng để quản lý công việc sau khi thống nhất kế hoạch.

## Phần chưa được chốt

- Roadmap final, phạm vi và đầu ra được owner thống nhất cho từng mốc.
- Treeview kiến trúc ứng dụng tương lai.
- Quyết định thiết kế/stack và acceptance để giao triển khai.

Các lựa chọn từng được agent ghi trong SPEC/work order M1 chưa được xem là những quyết định đã chốt với owner.

## Bản M1 đã viết

Đã chuyển nguyên source, contract, tests, hướng dẫn và bằng chứng chạy vào [archive/2026-10-31/paused-m1](../../archive/2026-10-31/paused-m1/README.md). Đây là bản thử bị tạm dừng, không phải bản M1 đã được nghiệm thu. Những kết quả test cũ chỉ phản ánh bản thử tại thời điểm chạy.

Không có cây app đang hoạt động ở root và không có server demo được khởi chạy trong lượt dọn dẹp. `IMPLEMENTATION_STATUS.json` không ghi nhận capability ứng dụng đã được chấp nhận.

## Bước tiếp theo

Owner xem và điều chỉnh bản đề xuất; sau khi thống nhất hướng mới viết chi tiết cho phần M1 sắp làm. Chỉ tiếp tục triển khai khi được cho tiếp tục theo SPEC và WORK_ORDER phù hợp. Không dùng work order M1 trong archive để tự nối lại BUILD.
