# Steel Cargo Stowage Tool — SCST

Owner đã **thống nhất hướng tổng thể** ngày 31-10-2026. Phần tiếp theo là SPEC M1. Việc triển khai app vẫn tạm dừng đến khi có work order được cho phép.

## Đọc từ đây

| Tài liệu | Vai trò |
|---|---|
| [Trạng thái project](docs/project/PROJECT_STATUS.md) | Việc đã có, phần chưa chốt và thứ tự tiếp tục |
| [Roadmap tổng thể + treeview đề xuất](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) | Roadmap v0.2 đã thống nhất: phạm vi, đầu ra từng mốc, rủi ro và treeview dự kiến |
| [Roadmap ban đầu — Tool First](docs/project/SCST_Roadmap_Ban_Dau_Tool_First.md) | Thông tin gốc để thảo luận; chưa phải roadmap final |
| [Tài liệu tham khảo](docs/reference/README.md) | Thiết kế v0.1, nghiệp vụ, dữ liệu và ảnh còn dùng |
| [Bản đồ sắp xếp file](docs/project/FILE_ORGANIZATION.md) | Cấu trúc hiện tại và vị trí các tài liệu đã chuyển |
| [Kho lưu trữ](archive/README.md) | Hồ sơ review cũ và bản M1 tạm dừng |

## Cấu trúc hiện tại

```text
Cargo_Stowage_Tool/
├── README.md                   # cửa vào project
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

Đây là cây **hồ sơ đang có**, chưa phải treeview kiến trúc app tương lai. Các tệp cấu hình CVF/Git ở root và thư mục ẩn được giữ nguyên chức năng.

Thứ tự tiếp tục: soạn SPEC M1 → owner thống nhất SPEC → WORK_ORDER cho phép triển khai phần đó theo CVF. Nội dung cũ trong tài liệu nguồn hoặc archive không tự cấp quyền tiếp tục code.
