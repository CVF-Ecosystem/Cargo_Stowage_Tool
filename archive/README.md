# Kho lưu trữ SCST

Kho này giữ lịch sử để tra cứu, không là nguồn cấp quyền tiếp tục triển khai. Trạng thái hiện hành ở [README project](../README.md) và [PROJECT_STATUS](../docs/project/PROJECT_STATUS.md).

| Bộ hồ sơ | Nội dung |
|---|---|
| [review-v0.3](2026-10-31/review-v0.3/README.md) | Package review nguyên cấu trúc, kèm phản hồi local và evidence |
| [received-packages](2026-10-31/received-packages/) | DOCX R1, ZIP R4, ZIP v0.3 và các bản nhận riêng |
| [paused-m1](2026-10-31/paused-m1/README.md) | Bản M1 được viết trước khi thống nhất kế hoạch, đã tạm dừng |
| [pre-cleanup-state](2026-10-31/pre-cleanup-state/) | Snapshot trạng thái/memory/handoff/catalog trước khi phân loại |
| [ORGANIZATION_MANIFEST.json](2026-10-31/ORGANIZATION_MANIFEST.json) | Đường dẫn gốc, vị trí mới và SHA-256 |

Tài liệu cũ có thể ghi trạng thái và lệnh tại thời điểm tạo; không ghi đè chúng để làm lịch sử trông như trạng thái hiện nay. Các đường dẫn máy trong receipt/log là lịch sử.

Kiểm lại tính toàn vẹn package review mà không chạy app:

```powershell
python -B archive/2026-10-31/review-v0.3/tooling/verify_package.py
```

Lệnh trên chỉ đối chiếu 35 file của package, không nghiệm thu phần mềm. Source tham khảo v0.1 và các tài liệu nghiệp vụ còn dùng đã được phân loại tại [docs/reference](../docs/reference/README.md).
