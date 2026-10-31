# SCST — Hướng dẫn chạy và kiểm

SCST chạy local với mẫu synthetic, chế độ tham chiếu VINAFCO, nhập tay/CSV và nguồn list ống thép chuẩn hóa. Hầm BOX mục tiêu luôn trống; hàng đã có trên tàu nằm ngoài hầm và chỉ trừ vào giới hạn chuyến. Không sử dụng kết quả này để lập hoặc phê duyệt phương án thực. Không có AI hoặc dịch vụ ngoài; dữ liệu list thực vẫn có thông số chưa xác minh.

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

Hầm nguồn rộng10,34375m; kiểm integer-mm dùng10,343m và lùi0,375mm mỗi mạn. Đây là chuyển đơn vị bảo thủ trên hầm ước tính. Mạn khô nguồn612/362mm giữ riêng D−d600/350mm; chênh lệch12mm chưa giải thích. Tải sàn và khối lượng tàu không chưa có dữ liệu. Chưa hỗ trợ container (giấy có điều kiện mớn riêng4,17m) hoặc ổn định/sức bền. M2a đã hỗ trợ manifest rỗng. Lỗi tải GLB vẫn dùng được bảng/hầm/kiểm; WebGL lỗi chuyển2D.

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

Ở lượt M2a, owner chưa có manifest/số đo hầm thực và chọn mẫu có nhãn. Sau đó owner cung cấp list ống V1.1 bên dưới; số đo hầm vẫn chưa có. Hàng/hầm tự nhập là dữ liệu khai báo chưa xác minh; GLB VINAFCO và các giới hạn sử dụng ở trên vẫn áp dụng. Xem [SPEC](specs/SCST_M2A.md) và [review](reviews/SCST_M2A_REVIEW.md).

## Nguồn list ống V1.1

1. Chọn hầm/phương án muốn dùng. **Xem VINAFCO 268** mở hầm tham chiếu ước tính; nạp list không tự đổi phương tiện hoặc nâng giới hạn chuyến. Mặc định giới hạn chuyến 32t từ mẫu vẫn được giữ, bạn khai báo giới hạn phù hợp rồi kiểm lại.
2. **Xem trước list ống** để xem nguồn: 31 nhóm, 1.076 bó, 21.226 ống. **Nạp list vào phương án hiện tại** thay manifest và xóa các placement cũ; có thể quay về **Bản trước**. Mọi bó ban đầu chưa xếp, yêu cầu mặc định **Tùy chọn**, vì nguồn chưa xác nhận toàn bộ list bắt buộc cho một chuyến.
3. Trong **Danh sách hàng**, lọc **Nhóm nguồn** theo dòng Excel (`Sheet1-R002` là dòng 2) và dùng **Trang trước/Trang sau**, tối đa 50 bó/trang. ID `PIPE-R002-B0001` là bó thứ nhất ở dòng 2, không dùng STT nguồn làm khóa.
4. Chọn bó → **Đặt bó** tại gốc hầm, sửa X/Y/góc → **Áp dụng & kiểm lại**. Đặt tiếp tại cùng gốc sẽ báo giao nhau; app không tự tìm vị trí. **Bỏ vị trí** đưa bó về chưa xếp. Số bó/ống/khối lượng đã xếp và còn lại có cho toàn list lẫn nhóm đang lọc. Bó **Loại trừ** vẫn thuộc tồn hàng nguồn nhưng không được đặt; số liệu còn lại bao gồm các bó này.
5. Các trường khối lượng/kích thước/ID nguồn cố định. Có thể đổi yêu cầu và vị trí; muốn thay danh sách bằng dữ liệu tự nhập dùng **Phương án mới** hoặc CSV. **Dùng hầm tự nhập** giữ list và bỏ liên kết tàu, cho sửa hầm BOX chưa xác minh. Đổi VR-SI/VR-SII và lưu/mở giữ provenance/placement của list.
6. Lưu snapshot như phần M2a. Reload → mở bản đã lưu; rawdraft vẫn không tự lưu. Sửa nháp phải kiểm lại trước khi nạp list/đổi phương án; phản hồi đến muộn không ghi đè thay đổi mới.

Khối lượng bó = K (kg/ống) × L (ống/bó), lưu gram nguyên. Tổng tính **1.125,55103t**, tổng O nguồn **1.125,52t**, lệch **31,03kg**; không phải dữ liệu cân từng bó. CBM nguồn **1.130,96964733156m³**, khối bao tính lại **1.157,54318105797m³** (R23:R26 nguồn chưa nhân số bó). Thể tích khối bao có khoảng rỗng, không chứng minh khả năng xếp vừa. Kích thước nguồn giữ chính xác µm, giao diện mm có phần lẻ; tọa độ đặt dùng mm nguyên.

16 bó ở dòng 22/31/32 có khối bao cần xác minh; app giữ cảnh báo và không tự sửa kích thước hoặc vẽ từng ống. Chỉ các bó đã đặt mới có mesh trong hầm. Nếu có quá nhiều lỗi, danh sách chỉ hiện 200 lỗi nhưng tổng đếm và các bó bị ảnh hưởng vẫn đầy đủ. Ship GLB/profile không đổi. Workbook/gói nguồn V1.1 giữ local ngoài Git; runtime dùng derivative có hash, không cần mở Excel. [Đánh giá cách tính](reviews/SCST_PIPE_LIST_ASSESSMENT.md), [SPEC](specs/SCST_PIPE_LIST.md).

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
