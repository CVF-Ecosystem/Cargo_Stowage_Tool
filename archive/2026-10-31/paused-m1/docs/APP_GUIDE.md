# Chạy SCST M1

Đây là cửa vào **ứng dụng đang phát triển**. `README.md` và `START_HERE_LOCAL_REVIEW.md` ở root thuộc gói review cũ, được giữ nguyên. Hướng phát triển hiện hành: `SCST_Roadmap_Ban_Dau_Tool_First.md`.

## Mở tool

Trên Windows đã có Python 3.11+ và Node.js 22 LTS: nhấp đôi **Start-SCST.cmd**. Lần đầu script cài dependency và build; cần internet. Các lần sau server chạy local tại **http://127.0.0.1:8765** và mở trình duyệt sau khi API sẵn sàng. Giữ cửa sổ server mở; Ctrl+C để dừng. Không dùng AI hoặc API key.

Nếu trình duyệt chưa mở, truy cập địa chỉ trên. Nếu cổng đang bận, dùng cửa sổ SCST đã chạy, hoặc chạy:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tooling/start-local.ps1 -Port 8767
```

Sau khi thay source hoặc kéo thay đổi mới, build lại trước khi mở:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tooling/setup.ps1
```

## Thử một vòng

1. Mẫu có 13 bó, 12 bó đã xếp, 1 bó tùy chọn chưa xếp. Khối lượng đã xếp 26,1 tấn; giới hạn hàng 32 tấn. Toàn manifest 27,95 tấn.
2. Chọn ST-001 trong bảng hoặc mô hình. Đổi X từ 500 thành **8001 mm**, bấm **Áp dụng & kiểm lại**: backend trả lỗi vượt biên, mô hình và bảng cập nhật cùng tọa độ.
3. **Bản trước** quay lại phương án đã kiểm trước đó. Đổi giới hạn hàng thành **26100 kg**, mass ST-001 thành **2500.001 kg** để thấy vượt tải đúng 1 gram.
4. **Mặt bằng** xem 2D và chọn bằng Tab/Enter. Khi WebGL không khả dụng, ứng dụng tự chuyển sang mặt bằng. Trong 3D: kéo xoay, cuộn zoom, nút ↺ đặt lại góc nhìn.
5. Tìm ID/tên, lọc đã xếp/chưa xếp. Chọn PP-013 để thấy hàng tùy chọn chưa xếp vẫn có trong manifest.

M1 giữ tối đa 20 phương án trước **trong bộ nhớ của tab**; refresh/đóng tab sẽ mất thay đổi. Không có nút lưu bền hoặc xuất file giả. Nút “Khôi phục mẫu” cũng giữ bản đang xem vào lịch sử phiên để có thể quay lại.

## Phạm vi hiện có

Hầm BOX, một lớp Z=0, yaw 0/90/180/270°, từng bó là khối bao. Tải cộng từ các bó đã xếp; kiểm biên, va chạm thể tích dương và thiếu hàng required. Chạm mặt không tính là va chạm. API từ chối ID trùng/không tồn tại, placement trùng, excluded được xếp, số gram/mm không nguyên, trường lạ và cấu trúc ngoài contract. Không làm tròn để lọt giới hạn.

Mọi fixture mang nhãn SYNTHETIC. **Đạt kiểm cơ bản chưa là phương án dùng thực tế.** Chưa có kê/chồng/chèn/chằng, ổn định, tải cục bộ; chưa có importer, solver, lưu/mở, so sánh bền hoặc PDF/XLSX. Các phần này đi theo M2–M5.

## Treeview đang dùng

```text
Cargo_Stowage_Tool/
├── Start-SCST.cmd               # mở ứng dụng local
├── apps/frontend/
│   ├── src/App.tsx              # workspace, bảng, editor, kết quả
│   ├── src/Viewer.tsx           # Three.js + mặt bằng SVG
│   ├── src/model.ts             # API client, đổi đơn vị chính xác
│   └── src/generated/api.ts     # sinh từ OpenAPI
├── services/backend/app/
│   ├── api/routes.py            # health, demo, validate
│   ├── domain/models.py         # contract strict, ID và giới hạn
│   ├── domain/validation.py     # tải / biên / va chạm / required
│   ├── domain/demo.py           # dữ liệu synthetic
│   └── main.py                  # API + phục vụ frontend đã build
├── contracts/openapi.json       # schema API hiện hành
├── tests/backend/              # kiểm domain và API
├── tests/browser/              # luồng UI trên API thật
├── tooling/                    # setup, launcher, sinh contract
├── docs/specs/SCST_M1.md        # yêu cầu / acceptance
├── docs/work_orders/SCST_M1.md  # phạm vi thi công và coverage
├── docs/reviews/               # kết quả kiểm / screenshots
├── CVF_SESSION/                # trạng thái và bàn giao
└── .cvf/                       # binding + policy, core ở ngoài project
```

`runtime-data/`, SQLite và adapters sẽ được tạo khi bắt đầu lưu bền ở M2; không dựng module rỗng trước nhu cầu.

## Kiểm và phát triển

```powershell
# Cài browser chỉ khi cần chạy kiểm UI
powershell -NoProfile -ExecutionPolicy Bypass -File tooling/setup.ps1 -Dev
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe tooling/export_contract.py
Push-Location apps/frontend
npm run contract
npm run build
npm run test:e2e
Pop-Location
```

Playwright tự mở backend trên cổng 8766 rồi dừng, chạy Chromium headless. API test dùng cùng domain thực, không provider mock. `requirements-lock.txt` và `package-lock.json` khóa dependency. Lock Python được chốt trên Python 3.11 Windows. `minimatch` được override 11.0.1 trong tooling sinh contract để xử lý advisory quan sát khi cài, đã kiểm lại generator.

Dev mode: terminal 1 chạy `.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir services/backend --host 127.0.0.1 --port 8765 --reload`; terminal 2 chạy `npm run dev` trong `apps/frontend`. Vite proxy `/api` về backend. Bản chạy thường dùng một server tại 8765, không cần Vite.

## Bước kế tiếp

Lát cắt M2 đầu: nhập tay hầm/manifest + lưu/mở SQLite + giữ phiên bản trước khi sửa. Chốt contract và acceptance cho lát cắt này trước BUILD. Sau đó mới import mẫu, heuristic, so sánh và xuất PDF/XLSX. Chỉ lấy format manifest thực khi viết importer; profile kê/chồng cần trước phần nhiều tầng M3.
