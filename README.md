# Steel Cargo Stowage Tool — SCST

**M1 đã chuyển có chọn lọc và đạt kiểm kỹ thuật**, sẵn để owner xem demo synthetic local. Có bảng/3D/2D, sửa–STALE–kiểm lại–undo và ba giới hạn tải theo SPEC v0.2. Chưa có planner, nhập manifest, lưu bền, export hoặc nhiều tầng.

**Chạy:** nhấp đôi `Start-SCST.cmd`; xem [hướng dẫn](docs/APP_GUIDE.md). Sau khi sửa source, build lại theo hướng dẫn. Thay đổi chỉ giữ trong tab và mất khi refresh.

## Đọc từ đây

| Tài liệu | Vai trò |
|---|---|
| [Hướng dẫn chạy M1](docs/APP_GUIDE.md) | Chạy local, thao tác và các giới hạn |
| [Review M1](docs/reviews/SCST_M1_REVIEW.md) | Đối chiếu đủ M1-01…09 và bằng chứng mới |
| [Trạng thái project](docs/project/PROJECT_STATUS.md) | Việc đã có, phần chưa chốt và thứ tự tiếp tục |
| [Roadmap tổng thể + treeview đề xuất](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) | Roadmap v0.2 đã thống nhất: phạm vi, đầu ra từng mốc, rủi ro và treeview dự kiến |
| [Đánh giá tái sử dụng M1 và kết quả recheck](docs/reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) | Nguồn → đích, ánh xạ acceptance và kết quả tiếp quản ở mục 9; chưa chuyển code |
| [Roadmap ban đầu — Tool First](docs/project/SCST_Roadmap_Ban_Dau_Tool_First.md) | Thông tin gốc để thảo luận; chưa phải roadmap final |
| [Tài liệu tham khảo](docs/reference/README.md) | Thiết kế v0.1, nghiệp vụ, dữ liệu và ảnh còn dùng |
| [Bản đồ sắp xếp file](docs/project/FILE_ORGANIZATION.md) | Cấu trúc hiện tại và vị trí các tài liệu đã chuyển |
| [Kho lưu trữ](archive/README.md) | Hồ sơ review cũ và bản M1 tạm dừng |

## Cấu trúc hiện tại

```text
Cargo_Stowage_Tool/
├── README.md                   # cửa vào project
├── apps/frontend/src/          # giao diện M1
│   ├── features/               # nhập hàng/hầm, phương án, chỉnh/so sánh
│   ├── viewer-3d/              # hiển thị cùng dữ liệu phương án
│   └── api/                    # giao tiếp backend theo contract
├── services/backend/app/       # backend M1
│   ├── api/                    # nhận thao tác, trả dữ liệu/kết quả kiểm
│   ├── domain/
│   │   ├── model/              # hàng, hầm, phương án, đơn vị tính
│   │   ├── geometry/           # biên, va chạm, tọa độ
│   │   └── rules/              # bộ kiểm tra, độc lập với bộ xếp
│   └── adapters/               # lưu local, import/export (dùng từ M2)
├── contracts/                  # dữ liệu/API, đơn vị tính, phiên bản
├── tests/                      # kiểm nghiệp vụ, tích hợp, luồng dùng
├── tooling/                    # lệnh chạy local
├── docs/
│   ├── project/                # trạng thái và đầu vào định hướng
│   ├── reference/              # nguồn còn dùng để tham khảo
│   ├── catalog/                # mục lục CVF
│   ├── roadmaps/               # roadmap tổng thể đã thống nhất
│   ├── decisions/              # quyết định của owner
│   └── ...                     # vùng hồ sơ CVF khác (specs, work_orders, reviews)
├── archive/                    # lịch sử, review và bản thử tạm dừng
├── CVF_SESSION/                # bàn giao và trạng thái phiên
├── scripts/                    # công cụ quản lý CVF
└── knowledge/                  # vùng knowledge của CVF
```

Đây là cây **đang có trên đĩa**. Source M1 đã được chuyển/sửa theo [SPEC v0.2](docs/specs/SCST_M1.md); các README module ghi phạm vi đang có. `domain/planner/` và `runtime-data/` được tạo ở M2, phần đóng gói ở M5. Các tệp cấu hình CVF/Git ở root và thư mục ẩn được giữ nguyên chức năng.

Thứ tự tiếp tục: owner xem demo M1 và phản hồi; chỉ chi tiết hóa phần M2 sắp làm khi được chọn. Không tự mở mốc kế tiếp từ kết quả test M1.
