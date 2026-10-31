# SCST — Hướng dẫn chạy và kiểm

SCST M1 là bản demo synthetic trên máy cá nhân. Hầm BOX mục tiêu luôn trống; hàng đã có trên tàu nằm ngoài hầm và chỉ trừ vào giới hạn chuyến. Không sử dụng kết quả này để lập hoặc phê duyệt phương án thực. Không có AI, dịch vụ ngoài hoặc dữ liệu thật.

## Chạy trên Windows

Cần Python 3.11 và Node.js 22 trong PATH. Nhấp đôi `Start-SCST.cmd`. Lần đầu launcher tạo `.venv`, cài các package công khai theo lock, build frontend và mở trang local. Lần sau chạy không cần mạng nếu môi trường và build còn sẵn. Cửa sổ launcher phải để mở; Ctrl+C để dừng. Nếu cổng 8765 bận, chạy `powershell -ExecutionPolicy Bypass -File tooling/start-local.ps1 -Port 8766`.

Sau khi sửa source, chạy `powershell -ExecutionPolicy Bypass -File tooling/setup.ps1` để cài và build lại. Với kiểm thử browser, chạy `powershell -ExecutionPolicy Bypass -File tooling/setup.ps1 -Dev` để cài Chromium Playwright nếu chưa có.

## Thao tác

Chọn bó trong bảng, 3D hoặc mặt bằng. Sửa khối lượng, X/Y, góc hoặc ba giới hạn; giao diện đánh dấu `STALE` ngay và tiếp tục hiện kết quả đã kiểm trước. Nhấn **Áp dụng & kiểm lại**: khi backend trả về, kết quả mới hiển thị. Nếu dữ liệu sai hoặc mất mạng, bản nháp và kết quả trước được giữ để sửa và thử lại. **Bản trước** quay lại kết quả đã kiểm trước đó. M2a bổ sung lưu/mở bên dưới; tải lại/đóng tab vẫn làm mất bản nháp chưa lưu.

Giới hạn chứng nhận và chuyến phải dương; hàng đã có trên tàu có thể bằng 0. Giới hạn chuyến không vượt chứng nhận, hàng đã có không vượt giới hạn chuyến. Lượng xếp thêm bằng giới hạn chuyến trừ hàng đã có. Khối lượng nhập kg với tối đa 3 số thập phân, tọa độ mm là số nguyên.

`DRAFT` có lỗi hình học; `GEOMETRY_FEASIBLE` còn lỗi quy tắc; `RULES_CHECKED` chỉ nói các kiểm trong M1 đã chạy đạt. Danh sách chưa kiểm luôn có, bao gồm kê/chèn/chằng, nhiều tầng, ổn định, tải cục bộ và hàng cũ trong hầm. 3D hỗ trợ kéo xoay, cuộn zoom, chọn và đặt lại; khi WebGL không khả dụng giao diện chuyển sang 2D và bảng.

## Chế độ tham chiếu VINAFCO 268

Chọn **Xem VINAFCO 268**. Thân dùng kích thước theo hồ sơ 77,8 × 13,24 × 5,2m; hầm/cabin/tuyến hình ước tính, hàng synthetic. Chọn VR-SI/VR-SII để xem mức hàng 3282,5/3517,5t và mớn tham chiếu4,60/4,85m; TTTP3301/3536t hiển thị riêng. Chưa tính mớn theo tổng hàng. Màu thân GLB cố định tại4,85m; khung xanh là marker theo cấp đang chọn.

Giới hạn chuyến cũ được giữ hoặc hạ theo mức mới, không tự nâng từ32t của mẫu lên mức hàng tham chiếu. Có thể chỉnh giới hạn chuyến bằng kg; mức hàng theo hồ sơ chỉ đọc. Khi có STALE, áp dụng và kiểm lại trước khi đổi cấp, khôi phục mẫu hoặc undo. Hàng đã có vẫn được tính ngoài hầm mục tiêu; nếu vượt mức cấp mới thì không chuyển cấp và giữ dữ liệu.

Hầm nguồn rộng10,34375m; kiểm integer-mm dùng10,343m và lùi0,375mm mỗi mạn. Đây là chuyển đơn vị bảo thủ trên hầm ước tính. Mạn khô nguồn612/362mm giữ riêng D−d600/350mm; chênh lệch12mm chưa giải thích. Tải sàn và khối lượng tàu không chưa có dữ liệu. Chưa hỗ trợ container (giấy có điều kiện mớn riêng4,17m), ổn định/sức bền hoặc empty manifest. Lỗi tải GLB vẫn dùng được bảng/hầm/kiểm; WebGL lỗi chuyển2D.

Tài liệu nguồn local trong `VINAFCO268_LOCAL_HANDOFF/`, bị loại khỏi Git; app chỉ đọc profile kỹ thuật chọn lọc và GLB trong `services/backend/data/vessels/vinafco268/`. Không cần gói gốc để chạy app sau khi đã tích hợp. Xem [review](reviews/SCST_VINAFCO268_REVIEW.md).

## M2a — Nhập tay, CSV và lưu/mở

**Nhập tay:** chọn **Phương án mới** (hầm BOX, chưa có hàng). Sửa tên/kích thước hầm và các giới hạn rồi **Áp dụng & kiểm lại**. Điền **Thêm bó hàng**, mỗi bó có ID riêng, tên, loại, yêu cầu, kích thước mm và khối lượng kg. Chọn bó để sửa, **Đặt bó** tại gốc hầm rồi đổi X/Y/góc, hoặc **Bỏ vị trí / Xóa bó**. Loại trừ bó sẽ bỏ placement của nó. Danh sách rỗng hiện DRAFT/EMPTY_MANIFEST; không tự sinh hàng hoặc xếp tự động. Với VINAFCO, hầm và mức nguồn khóa; **Dùng hầm tự nhập** bỏ liên kết phương tiện, giữ nhãn chưa xác minh.

**CSV:** dùng [mẫu giả lập](examples/manifest_m2a_synthetic.csv), UTF-8 có/không BOM, dấu phẩy phân cách, một dòng một bó. Header chính xác:

```csv
id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg
```

Loại `BAR_BUNDLE`/`PIPE_BUNDLE`; yêu cầu `required`/`optional`/`excluded`. Kích thước nguyên dương mm; kg dùng dấu chấm, tối đa3chữ số thập phân; không có quantity hoặc suy khối lượng từ tổng. Tối đa200bó/1MiB. Chọn file hoặc dán nội dung → **Kiểm CSV** → xem tổng/lỗi dòng-trường → **Áp dụng CSV**. Một lỗi chặn toàn bộ, workspace cũ được giữ. Áp dụng thay manifest và bỏ tất cả vị trí xếp cũ; phải đặt lại các bó. Sửa input/context sau preview thì kiểm CSV lại. Chưa import XLSX/PDF/OCR.

**Lưu/mở:** áp dụng nháp trước, đặt tên1–100ký tự rồi **Lưu phương án**. Có thể lưu cả phương án DRAFT đã được backend đánh giá; việc lưu không đổi kết quả thành đạt. Mỗi lần lưu tạo UUID/bản mới, không ghi đè. Reload hoặc khởi động lại app → chọn bản ở **Phương án đã lưu** → **Mở phương án**, backend kiểm lại theo rules/profile hiện tại. Danh sách100bản mới nhất, không tự lưu nháp, không có xóa/ghi đè/so sánh phiên bản đầy đủ trong M2a.

SQLite mặc định: `runtime-data/scst.sqlite3`, ngoài Git. Giữ thư mục này nếu muốn giữ các bản lưu; không xóa để xử lý lỗi. `SCST_DATA_DIR` dành cho cấu hình server và test cô lập, không nhận qua API. File/record/phiên bản/timestamp lỗi được báo, không reset DB; bản đang mở giữ nguyên. Nếu một record timestamp hỏng, danh sách chưa dùng được cho tới khi sửa dữ liệu; record tốt vẫn còn, không bị bỏ hoặc sửa ngầm. Backup/restore tự động thuộc M5.

Owner chưa có manifest/số đo hầm thực và đã chọn tiếp tục với mẫu có nhãn. Hàng/hầm tự nhập là dữ liệu khai báo chưa xác minh; GLB VINAFCO và các giới hạn sử dụng ở trên vẫn áp dụng. Xem [SPEC](specs/SCST_M2A.md) và [review](reviews/SCST_M2A_REVIEW.md).

## Kiểm nhà phát triển

```powershell
.venv/Scripts/python.exe -m pytest tests/backend -q
.venv/Scripts/python.exe tooling/export_contract.py
npm.cmd --prefix apps/frontend run contract
npm.cmd --prefix apps/frontend run build
npm.cmd --prefix apps/frontend run test:e2e
```

Cây thực: `services/backend/app/domain/{model,geometry,rules}` chứa contract và kiểm; `services/backend/app/api` phục vụ API; `apps/frontend/src/{api,features,viewer-3d}` là giao diện; `contracts/openapi.json` và `apps/frontend/src/api/generated/api.ts` được sinh; `tests/backend`, `tests/browser` chứa kiểm; `tooling/` và `Start-SCST.cmd` khởi chạy.

Ngoài phạm vi hiện tại: xếp tự động, import XLSX/PDF, xuất báo cáo, nhiều tầng, xác minh manifest/hầm đo thực và AI. M2a có nhập tay/CSV và lưu/mở local; VINAFCO 268 bổ sung thông số thân và trạng thái tham chiếu theo hồ sơ.
