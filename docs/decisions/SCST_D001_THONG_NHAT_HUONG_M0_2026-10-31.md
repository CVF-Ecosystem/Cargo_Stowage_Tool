# SCST-D001 — Thống nhất hướng tổng thể (M0)

Status: ACTIVE

**Ngày:** 31-10-2026. **Người quyết định:** owner SCST. **Người ghi:** local agent (SPEC_AUTHOR / SESSION_SYNC_STEWARD).

## Quyết định

Owner trả lời "Đồng ý, thống nhất" sau khi xem bản đánh giá roadmap đề xuất v0.1. Hai nội dung được thống nhất:

1. Hướng tổng thể: local-first, một người dùng chính, ranh giới nghiệp vụ; đầu ra và thứ tự M1–M5 với M4 (AI) là nhánh tùy chọn; một repository FE/BE với các lớp trách nhiệm như treeview.
2. Áp dụng các góp ý của bản đánh giá vào roadmap:
   - chia M2 thành M2a–M2d theo thứ tự;
   - contract có z, lớp và chỗ cho quan hệ đỡ từ M1;
   - lấy một manifest mẫu và một bộ số đo hầm thật trong M2a, trước khi đầu tư M2b;
   - thêm mục rủi ro, gồm license CVF;
   - SPEC M1 bắt đầu bằng đối chiếu bản thử trong archive;
   - thêm nhãn trạng thái phương án, làm rõ các loại giới hạn tải, tách `rules` khỏi `planner`, gọn câu chữ CVF.

Kết quả: [roadmap v0.2](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md).

## Không bao gồm

- Chưa có SPEC M1, tiêu chí nghiệm thu từng mốc hay bản đồ tiêu chí (`docs/milestone-coverage-authority.json`).
- Chưa cấp quyền BUILD. Bản thử M1 trong archive vẫn không phải quyền tiếp tục.
- Không có capability app nào được nghiệm thu.

## Bước tiếp theo

Soạn SPEC M1 là phần kế tiếp. BUILD cần WORK_ORDER riêng được cho phép.
