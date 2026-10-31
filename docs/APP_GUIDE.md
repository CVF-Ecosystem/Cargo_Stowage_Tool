# SCST M1 — Hướng dẫn chạy và kiểm

SCST M1 là bản demo synthetic trên máy cá nhân. Hầm BOX mục tiêu luôn trống; hàng đã có trên tàu nằm ngoài hầm và chỉ trừ vào giới hạn chuyến. Không sử dụng kết quả này để lập hoặc phê duyệt phương án thực. Không có AI, dịch vụ ngoài hoặc dữ liệu thật.

## Chạy trên Windows

Cần Python 3.11 và Node.js 22 trong PATH. Nhấp đôi `Start-SCST.cmd`. Lần đầu launcher tạo `.venv`, cài các package công khai theo lock, build frontend và mở trang local. Lần sau chạy không cần mạng nếu môi trường và build còn sẵn. Cửa sổ launcher phải để mở; Ctrl+C để dừng. Nếu cổng 8765 bận, chạy `powershell -ExecutionPolicy Bypass -File tooling/start-local.ps1 -Port 8766`.

Sau khi sửa source, chạy `powershell -ExecutionPolicy Bypass -File tooling/setup.ps1` để cài và build lại. Với kiểm thử browser, chạy `powershell -ExecutionPolicy Bypass -File tooling/setup.ps1 -Dev` để cài Chromium Playwright nếu chưa có.

## Thao tác

Chọn bó trong bảng, 3D hoặc mặt bằng. Sửa khối lượng, X/Y, góc hoặc ba giới hạn; giao diện đánh dấu `STALE` ngay và tiếp tục hiện kết quả đã kiểm trước. Nhấn **Áp dụng & kiểm lại**: khi backend trả về, kết quả mới hiển thị. Nếu dữ liệu sai hoặc mất mạng, bản nháp và kết quả trước được giữ để sửa và thử lại. **Bản trước** quay lại kết quả đã kiểm trước đó. Tải lại/đóng tab làm mất thay đổi; M1 không lưu bền.

Giới hạn chứng nhận và chuyến phải dương; hàng đã có trên tàu có thể bằng 0. Giới hạn chuyến không vượt chứng nhận, hàng đã có không vượt giới hạn chuyến. Lượng xếp thêm bằng giới hạn chuyến trừ hàng đã có. Khối lượng nhập kg với tối đa 3 số thập phân, tọa độ mm là số nguyên.

`DRAFT` có lỗi hình học; `GEOMETRY_FEASIBLE` còn lỗi quy tắc; `RULES_CHECKED` chỉ nói các kiểm trong M1 đã chạy đạt. Danh sách chưa kiểm luôn có, bao gồm kê/chèn/chằng, nhiều tầng, ổn định, tải cục bộ và hàng cũ trong hầm. 3D hỗ trợ kéo xoay, cuộn zoom, chọn và đặt lại; khi WebGL không khả dụng giao diện chuyển sang 2D và bảng.

## Kiểm nhà phát triển

```powershell
.venv/Scripts/python.exe -m pytest tests/backend -q
.venv/Scripts/python.exe tooling/export_contract.py
npm.cmd --prefix apps/frontend run contract
npm.cmd --prefix apps/frontend run build
npm.cmd --prefix apps/frontend run test:e2e
```

Cây thực: `services/backend/app/domain/{model,geometry,rules}` chứa contract và kiểm; `services/backend/app/api` phục vụ API; `apps/frontend/src/{api,features,viewer-3d}` là giao diện; `contracts/openapi.json` và `apps/frontend/src/api/generated/api.ts` được sinh; `tests/backend`, `tests/browser` chứa kiểm; `tooling/` và `Start-SCST.cmd` khởi chạy.

Ngoài phạm vi: xếp tự động, nhập manifest, lưu/mở, xuất báo cáo, nhiều tầng, dữ liệu thực và AI.
