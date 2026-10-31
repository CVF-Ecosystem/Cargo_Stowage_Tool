# Bản đồ sắp xếp file

Ngày: **31-10-2026**. Phạm vi: dọn hồ sơ theo yêu cầu owner, giữ việc xây app ở trạng thái tạm dừng.

## Tài liệu đang dùng

| Nhóm | Vị trí |
|---|---|
| Thông tin xuất phát điểm | `docs/project/SCST_Roadmap_Ban_Dau_Tool_First.md` |
| Trạng thái và thứ tự tiếp tục | `docs/project/PROJECT_STATUS.md` |
| Package thiết kế v0.1 và bốn tài liệu dễ đọc được trích nguyên bytes | `docs/reference/design-v0.1/` |
| Mô hình nghiệp vụ và yêu cầu dữ liệu từ review v0.3 | `docs/reference/domain/` |
| Ba ảnh gốc và ghi chú quan sát | `docs/reference/photos/` |
| Quy tắc, trạng thái và công cụ CVF | Giữ các đường dẫn chuẩn `.cvf/`, `AGENTS.md`, `CVF_SESSION/`, `scripts/`, `docs/catalog/` |

Nguồn tham khảo không tự trở thành quyết định thiết kế. Roadmap ban đầu được giữ nguyên nội dung; các đường dẫn `docs/06_ROADMAP_GATED.md` và `docs/07_ARCHITECTURE_TREEVIEW.md` trong nội dung gốc chỉ tài liệu bên trong package v0.1. Bản dễ đọc hiện ở `docs/reference/design-v0.1/`.

## Tài liệu đã lưu trữ

| Trước đây | Hiện tại |
|---|---|
| README/START_HERE/MASTER/DECISION_LOG/REVIEW_R3 của gói review; docs 01–07; evidence, history, inputs, probes, templates, tooling review | `archive/2026-10-31/review-v0.3/`, giữ nguyên cây tương đối |
| LOCAL_REVIEW_REPORT và LOCAL_REVIEW_EVIDENCE | Cùng bộ `archive/2026-10-31/review-v0.3/` |
| DOCX R1, ZIP R4, ZIP review v0.3 và các bản nhận trùng | `archive/2026-10-31/received-packages/` |
| apps, services, contracts, tests và launcher/tooling M1 | `archive/2026-10-31/paused-m1/`, chỉ giữ source và kết quả liên quan |
| SPEC/work order, authority M1, APP_GUIDE và evidence M1 | Cùng bộ `archive/2026-10-31/paused-m1/docs/` |
| Trạng thái/memory/handoff/catalog trước dọn dẹp | `archive/2026-10-31/pre-cleanup-state/` |

Source và tài liệu được chuyển nguyên bytes. Những tài liệu nghiệp vụ/ảnh còn cần đọc được sao chép có đối chiếu hash từ bộ review nguyên gốc sang `docs/reference/`. Package review giữ nguyên đủ nội dung để chạy lại verifier checksum.

Hai bản nhận trùng — ZIP v0.2 và audit R2 — vẫn được giữ trong `received-packages`; bản thuộc package gốc vẫn nằm trong `review-v0.3`. Manifest ghi hash để nhận diện trùng, không tự coi chúng là hai nguồn độc lập.

## Dependency và cache local

`.venv`, `node_modules`, frontend build, test cache và các thư mục nguồn đã trống được đưa vào `.cvf/runtime/paused-m1-local/` hoặc `.cvf/runtime/cleanup-empty-directories/`. Đây là dữ liệu local bị Git ignore, không phải source hay cấu trúc app đang dùng. Chúng được giữ ngoài cây làm việc chính; chưa xóa vĩnh viễn dữ liệu trong lượt này.

Log server cũ ở `archive/2026-10-31/paused-m1/runtime-data/`. PID và đường dẫn máy trong log/receipt là thông tin lịch sử, không chứng minh process đang chạy hoặc tạo quyền triển khai.

## Kiểm tra

- [Manifest vị trí và SHA-256](../../archive/2026-10-31/ORGANIZATION_MANIFEST.json): đối chiếu trước/sau chuyển và các bản trích/copy.
- [Kết quả kiểm dọn dẹp](ORGANIZATION_VERIFICATION.json): số tệp đã kiểm, checksum package và các liên kết đang dùng.
- Các verifier/gate CVF chỉ kiểm đúng phạm vi ghi trong log; việc dọn hồ sơ không phải nghiệm thu M1 hoặc chứng minh quản trị AI.
