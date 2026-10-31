# Steel Cargo Stowage Tool · SCST

Công cụ hỗ trợ lập phương án xếp hàng thép trong hầm tàu, chạy local với giao diện tiếng Việt. SCST hướng tới luồng **nhập hàng và hầm → đề xuất xếp → xem 3D → chỉnh và kiểm lại → lưu, so sánh, xuất báo cáo**.

**Hiện tại: demo M1 đã đạt kiểm kỹ thuật, đang chờ phản hồi nghiệp vụ.** Bản đang có dùng dữ liệu giả lập, hầm dạng hộp (BOX) và hàng một lớp. Nhập manifest, xếp tự động, lưu/mở và xuất báo cáo thuộc các mốc tiếp theo.

## Bản hiện tại làm được gì?

- Xem bó hàng và vị trí xếp trên bảng, mô hình 3D và mặt bằng 2D; chọn hàng đồng bộ giữa các góc nhìn.
- Sửa khối lượng, tọa độ X/Y và góc xoay; áp dụng thay đổi và kiểm lại qua backend.
- Khai báo giới hạn tải theo chứng nhận, theo chuyến và lượng hàng đã có trên tàu.
- Kiểm tải, vượt biên hầm, giao nhau giữa các bó và hàng bắt buộc chưa xếp.
- Đánh dấu dữ liệu đã sửa là `STALE`, giữ kết quả đã kiểm trước và quay lại bản trước.
- Chuyển sang bảng/2D khi trình duyệt không hỗ trợ WebGL.

> M1 dùng để xem và đánh giá luồng thao tác. Thay đổi mất khi tải lại hoặc đóng tab. Kết quả kiểm chưa bao gồm nhiều tầng, kê/chèn/chằng, ổn định tàu hoặc tải cục bộ; không dùng demo để lập hay phê duyệt phương án thực.

## Chạy trên Windows

### Yêu cầu

- Python **3.11** và Node.js **22**, có trong `PATH`.
- Trình duyệt hiện đại; WebGL để xem 3D.
- Kết nối mạng ở lần đầu để cài thư viện. Khi môi trường và bản build đã có, demo chạy local không cần dịch vụ ngoài hoặc API key.

### Khởi chạy

Clone repository, sau đó chạy launcher:

```powershell
git clone https://github.com/CVF-Ecosystem/Cargo_Stowage_Tool.git
cd Cargo_Stowage_Tool
.\Start-SCST.cmd
```

Hoặc mở thư mục project và nhấp đôi **`Start-SCST.cmd`**. Lần đầu, launcher tạo môi trường Python, cài dependencies, build frontend rồi mở trình duyệt.

| Địa chỉ mặc định | Nội dung |
|---|---|
| http://127.0.0.1:8765 | Giao diện SCST |
| http://127.0.0.1:8765/docs | Tài liệu API tương tác |
| http://127.0.0.1:8765/api/health | Trạng thái backend |

Giữ cửa sổ launcher mở trong lúc sử dụng; nhấn **Ctrl+C** để dừng. Nếu cổng `8765` đang bận, chọn cổng khác:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tooling/start-local.ps1 -Port 8766
```

Sau khi cập nhật source, cài/build lại rồi khởi chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tooling/setup.ps1
.\Start-SCST.cmd
```

Xem cách thao tác, đơn vị nhập liệu và ý nghĩa trạng thái trong [hướng dẫn sử dụng](docs/APP_GUIDE.md).

## Kiến trúc

Frontend dùng **React, TypeScript và Three.js**. Backend dùng **Python/FastAPI**, quản lý dữ liệu và kiểm quy tắc. Bản chạy local phục vụ frontend đã build và API trên cùng một cổng.

```text
Cargo_Stowage_Tool/
├── Start-SCST.cmd                  # Launcher Windows
├── apps/frontend/src/
│   ├── features/                   # Workspace, bảng và thao tác chỉnh/kiểm
│   ├── viewer-3d/                  # Hiển thị hầm/hàng, góc nhìn và chọn hàng
│   └── api/                        # API client và types sinh từ contract
├── services/backend/app/
│   ├── main.py                     # FastAPI, phục vụ API và frontend đã build
│   ├── api/                        # Health, dữ liệu demo, kiểm phương án
│   ├── domain/
│   │   ├── model/                  # Mô hình dữ liệu và đơn vị tính
│   │   ├── geometry/               # Biên hầm, tọa độ và giao nhau
│   │   └── rules/                  # Kiểm quy tắc nghiệp vụ
│   └── adapters/                   # Dự kiến lưu/import/export; chưa triển khai
├── contracts/                      # OpenAPI contract
├── tests/                          # Backend, browser và kiểm khởi chạy
├── tooling/                        # Cài đặt, build, chạy local, sinh contract
├── docs/                           # Roadmap, SPEC, quyết định, hướng dẫn, review
└── archive/                        # Tài liệu lịch sử và bản thử cũ
```

Frontend hiển thị kết quả từ backend; chỉnh sửa cần được kiểm lại. M1 chưa có bộ xếp tự động, database hoặc tích hợp AI. Cây kiến trúc tương lai nằm trong [roadmap tổng thể](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md).

## Lộ trình phát triển

| Mốc | Kết quả hướng tới | Trạng thái |
|---|---|---|
| M0 — Thống nhất hướng | Phạm vi, thứ tự phát triển và kiến trúc tổng thể | Đã thống nhất |
| M1 — Demo chạy được | Hầm BOX, hàng giả lập, bảng/3D, sửa và kiểm cơ bản | Đạt kiểm kỹ thuật; chờ phản hồi nghiệp vụ |
| M2 — Tool trọn luồng | Nhập/import, lưu/mở, xếp sơ bộ, chỉnh/so sánh, xuất PDF/XLSX; hình tàu minh họa ở M2c | Chưa triển khai |
| M3 — Case thực | Hình học phù hợp dữ liệu thực, nhiều tầng, profile kê/chồng; hiệu chỉnh hình tàu | Chưa triển khai |
| M4 — AI hỗ trợ | Hỗ trợ tác vụ có nhu cầu rõ; core vẫn chạy khi tắt AI | Nhánh tùy chọn |
| M5 — Sử dụng ổn định | Đóng gói, lưu trữ bền, backup/restore và hiệu năng | Chưa triển khai |

Hình tàu minh họa đã được thống nhất trong roadmap v0.3; **chưa có trong demo M1**. Các mốc xa giữ ở mức tổng thể; chỉ chi tiết hóa phần sắp làm khi được chọn. Xem [phạm vi, đầu ra và phụ thuộc từng mốc](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md).

## Phát triển và kiểm thử

Chuẩn bị môi trường phát triển, gồm Chromium cho Playwright:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tooling/setup.ps1 -Dev
```

Các lệnh chính, chạy từ thư mục gốc:

```powershell
# Kiểm backend
.venv/Scripts/python.exe -m pytest tests/backend -q

# Sinh lại OpenAPI và TypeScript types khi contract thay đổi
.venv/Scripts/python.exe tooling/export_contract.py
npm.cmd --prefix apps/frontend run contract

# Kiểm TypeScript, build và kiểm luồng trình duyệt
npm.cmd --prefix apps/frontend run build
npm.cmd --prefix apps/frontend run test:e2e
```

Bản M1 đã được kiểm với 51 backend test, 5 browser test và 498 kiểm độc lập. Phạm vi bằng chứng, điều kiện chạy và giới hạn nằm trong [review M1](docs/reviews/SCST_M1_REVIEW.md); các kết quả này thuộc phiên bản được review.

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [Hướng dẫn sử dụng](docs/APP_GUIDE.md) | Khởi chạy, thao tác và giới hạn demo |
| [Trạng thái project](docs/project/PROJECT_STATUS.md) | Phần đã làm và bước tiếp theo |
| [Roadmap tổng thể v0.3](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) | Phạm vi, đầu ra từng mốc và kiến trúc dự kiến |
| [SPEC M1](docs/specs/SCST_M1.md) | Hành vi và tiêu chí kỹ thuật M1 |
| [Review M1](docs/reviews/SCST_M1_REVIEW.md) | Kết quả đối chiếu tiêu chí và bằng chứng |
| [Đánh giá tái sử dụng M1](docs/reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) | Căn cứ chọn source và kết quả thực hiện |
| [Mục lục tài liệu](docs/INDEX.md) | Điều hướng hồ sơ project |
| [Kho lưu trữ](archive/README.md) | Lịch sử, tài liệu cũ và bản thử đã dừng |

Project áp dụng CVF để quản lý quá trình phát triển. Agent và người tiếp quản đọc [AGENTS.md](AGENTS.md) cùng [session memory](CVF_SESSION_MEMORY.md) trước khi thay đổi project. Cấu hình CVF phục vụ quy trình phát triển; app M1 không tích hợp AI hoặc CVF runtime.
