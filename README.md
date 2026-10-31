# Steel Cargo Stowage Tool — SCST

Project đang ở bước **chuẩn bị và thống nhất kế hoạch**. Chưa có roadmap final hoặc kiến trúc được owner chốt. Việc triển khai app đang tạm dừng theo yêu cầu của owner.

## Đọc từ đây

| Tài liệu | Vai trò |
|---|---|
| [Trạng thái project](docs/project/PROJECT_STATUS.md) | Việc đã có, phần chưa chốt và thứ tự tiếp tục |
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
│   └── ...                     # vùng hồ sơ CVF; chưa có kế hoạch app được chốt
├── archive/                    # lịch sử, review và bản thử tạm dừng
├── CVF_SESSION/                # bàn giao và trạng thái phiên
├── scripts/                    # công cụ quản lý CVF
└── knowledge/                  # vùng knowledge của CVF
```

Đây là cây **hồ sơ đang có**, chưa phải treeview kiến trúc app tương lai. Các tệp cấu hình CVF/Git ở root và thư mục ẩn được giữ nguyên chức năng.

Thứ tự tiếp tục: làm rõ ý định → đề xuất roadmap và treeview → owner xem, điều chỉnh và chốt → triển khai từng phần. Nội dung cũ trong tài liệu nguồn hoặc archive không tự cấp quyền tiếp tục code.
