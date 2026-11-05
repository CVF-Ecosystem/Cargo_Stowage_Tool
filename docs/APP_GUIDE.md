# SCST — Hướng dẫn chạy và kiểm

SCST chạy local với mẫu synthetic, chế độ tham chiếu VINAFCO, nhập tay/CSV và nguồn list ống thép chuẩn hóa. Hầm BOX mục tiêu luôn trống; hàng đã có trên tàu nằm ngoài hầm và chỉ trừ vào giới hạn chuyến. Không sử dụng kết quả này để lập hoặc phê duyệt phương án thực. Không có AI hoặc dịch vụ ngoài; dữ liệu list thực vẫn có thông số chưa xác minh.

## Chạy trên Windows

Cần Python 3.11 và Node.js 22 trong PATH. Nhấp đôi `Start-SCST.cmd`. Lần đầu launcher tạo `.venv`, cài các package công khai theo lock, build frontend và mở trang local. Lần sau chạy không cần mạng nếu môi trường và build còn sẵn. Cửa sổ launcher phải để mở; Ctrl+C để dừng. Nếu cổng 8765 bận, chạy `powershell -ExecutionPolicy Bypass -File tooling/start-local.ps1 -Port 8766`.

Sau khi sửa source, chạy `powershell -ExecutionPolicy Bypass -File tooling/setup.ps1` để cài và build lại. Với kiểm thử browser, chạy `powershell -ExecutionPolicy Bypass -File tooling/setup.ps1 -Dev` để cài Chromium Playwright nếu chưa có.

## Thao tác

Chọn bó trong bảng, 3D hoặc mặt bằng. Sửa khối lượng, X/Y, góc hoặc ba giới hạn; giao diện đánh dấu `STALE` ngay và tiếp tục hiện kết quả đã kiểm trước. Nhấn **Áp dụng & kiểm lại**: khi backend trả về, kết quả mới hiển thị. Nếu dữ liệu sai hoặc mất mạng, bản nháp và kết quả trước được giữ để sửa và thử lại. **Bản trước** quay lại kết quả đã kiểm trước đó. M2a bổ sung lưu/mở bên dưới; tải lại/đóng tab vẫn làm mất bản nháp chưa lưu.

Giới hạn chứng nhận và chuyến phải dương; hàng đã có trên tàu có thể bằng 0. Giới hạn chuyến không vượt chứng nhận, hàng đã có không vượt giới hạn chuyến. Lượng xếp thêm bằng giới hạn chuyến trừ hàng đã có. Giao diện dùng kg và cm, hiển thị làm tròn để dễ thao tác; tổng khối lượng dùng tấn tối đa hai số lẻ. Mặc định hiển thị tròn đến kg/cm. Vẫn có thể nhập kg tối đa 3 số lẻ, cm tối đa 1 số lẻ khi cần giữ dữ liệu cũ chính xác. Ô chưa sửa giữ nguyên số gốc; số làm tròn chỉ được áp vào trường bạn thực sự nhập lại.

`DRAFT` có lỗi hình học; `GEOMETRY_FEASIBLE` còn lỗi quy tắc; `RULES_CHECKED` chỉ nói các kiểm hiện có đã chạy đạt. Danh sách chưa kiểm luôn có, bao gồm kê/chèn/chằng, tải chồng (phương án nhiều tầng) hoặc nhiều tầng (phương án một tầng), ổn định, tải cục bộ và hàng cũ trong hầm. 3D hỗ trợ kéo xoay, cuộn zoom, chọn và đặt lại; khi WebGL không khả dụng giao diện chuyển sang 2D và bảng.

## Chế độ tham chiếu VINAFCO 268

Chọn **Xem VINAFCO 268**. Thân dùng kích thước theo hồ sơ 77,8 × 13,24 × 5,2m; hầm/cabin/tuyến hình ước tính, hàng synthetic. Chọn VR-SI/VR-SII để xem mức hàng 3282,5/3517,5t và mớn tham chiếu4,60/4,85m; TTTP3301/3536t hiển thị riêng. Chưa tính mớn theo tổng hàng. Màu thân GLB cố định tại4,85m; khung xanh là marker theo cấp đang chọn.

Từ M3a, khi chọn VINAFCO 268 hoặc đổi cấp, giới hạn chuyến lấy theo mức hàng tham chiếu của cấp đó (VR-SII: 3.517,5t), kèm thông báo; không còn giữ 32t của mẫu. Có thể chỉnh lại giới hạn chuyến bằng kg; mức hàng theo hồ sơ chỉ đọc. Khi có STALE, áp dụng và kiểm lại trước khi đổi cấp, khôi phục mẫu hoặc undo. Hàng đã có vẫn được tính ngoài hầm mục tiêu; nếu vượt mức cấp mới thì không chuyển cấp và giữ dữ liệu.

Hầm nguồn rộng10,34375m; kiểm integer-mm dùng10,343m và lùi0,375mm mỗi mạn. Đây là chuyển đơn vị bảo thủ trên hầm ước tính. Mạn khô nguồn612/362mm giữ riêng D−d600/350mm; chênh lệch12mm chưa giải thích. Tải sàn và khối lượng tàu không chưa có dữ liệu. Chưa hỗ trợ container (giấy có điều kiện mớn riêng4,17m) hoặc ổn định/sức bền. M2a đã hỗ trợ manifest rỗng. Lỗi tải GLB vẫn dùng được bảng/hầm/kiểm; WebGL lỗi chuyển2D.

Tài liệu nguồn local trong `VINAFCO268_LOCAL_HANDOFF/`, bị loại khỏi Git; app chỉ đọc profile kỹ thuật chọn lọc và GLB trong `services/backend/data/vessels/vinafco268/`. Không cần gói gốc để chạy app sau khi đã tích hợp. Xem [review](reviews/SCST_VINAFCO268_REVIEW.md).

## M2a — Nhập tay, CSV và lưu/mở

**Nhập tay:** chọn **Phương án mới** (hầm BOX, chưa có hàng). Sửa tên/kích thước hầm và các giới hạn rồi **Áp dụng & kiểm lại**. Điền **Thêm bó hàng**, mỗi bó có ID riêng, tên, loại, yêu cầu, kích thước cm và khối lượng kg. Chọn bó để sửa, **Đặt bó** tại gốc hầm rồi đổi X/Y/góc, hoặc **Bỏ vị trí / Xóa bó**. Loại trừ bó sẽ bỏ placement của nó. Danh sách rỗng hiện DRAFT/EMPTY_MANIFEST; không tự sinh hàng; dùng M2b bên dưới để xếp thử. Với VINAFCO, hầm và mức nguồn khóa; **Dùng hầm tự nhập** bỏ liên kết phương tiện, giữ nhãn chưa xác minh.

**CSV:** dùng [mẫu giả lập](examples/manifest_m2a_synthetic.csv), UTF-8 có/không BOM, dấu phẩy phân cách, một dòng một bó. Header chính xác:

```csv
id,name,kind,requirement,length_mm,width_mm,height_mm,mass_kg
```

Loại `BAR_BUNDLE`/`PIPE_BUNDLE`; yêu cầu `required`/`optional`/`excluded`. Kích thước nguyên dương mm; kg dùng dấu chấm, tối đa3chữ số thập phân; không có quantity hoặc suy khối lượng từ tổng. Tối đa200bó/1MiB. Chọn file hoặc dán nội dung → **Kiểm CSV** → xem tổng/lỗi dòng-trường → **Áp dụng CSV**. Một lỗi chặn toàn bộ, workspace cũ được giữ. Áp dụng thay manifest và bỏ tất cả vị trí xếp cũ; phải đặt lại các bó. Sửa input/context sau preview thì kiểm CSV lại. Chưa import XLSX/PDF/OCR.

**Lưu/mở:** áp dụng nháp trước, đặt tên1–100ký tự rồi **Lưu phương án**. Có thể lưu cả phương án DRAFT đã được backend đánh giá; việc lưu không đổi kết quả thành đạt. Mỗi lần lưu tạo UUID/bản mới, không ghi đè. Reload hoặc khởi động lại app → chọn bản ở **Phương án đã lưu** → **Mở phương án**, backend kiểm lại theo rules/profile hiện tại. Danh sách100bản mới nhất, không tự lưu nháp, không có xóa/ghi đè/so sánh phiên bản đầy đủ trong M2a.

SQLite mặc định: `runtime-data/scst.sqlite3`, ngoài Git. Giữ thư mục này nếu muốn giữ các bản lưu; không xóa để xử lý lỗi. `SCST_DATA_DIR` dành cho cấu hình server và test cô lập, không nhận qua API. File/record/phiên bản/timestamp lỗi được báo, không reset DB; bản đang mở giữ nguyên. Nếu một record timestamp hỏng, danh sách chưa dùng được cho tới khi sửa dữ liệu; record tốt vẫn còn, không bị bỏ hoặc sửa ngầm. Sao lưu/khôi phục thủ công có từ M5a (xem mục M5a bên dưới); sao lưu tự động theo lịch chưa có.

Ở lượt M2a, owner chưa có manifest/số đo hầm thực và chọn mẫu có nhãn. Sau đó owner cung cấp list ống V1.1 bên dưới; số đo hầm vẫn chưa có. Hàng/hầm tự nhập là dữ liệu khai báo chưa xác minh; GLB VINAFCO và các giới hạn sử dụng ở trên vẫn áp dụng. Xem [SPEC](specs/SCST_M2A.md) và [review](reviews/SCST_M2A_REVIEW.md).

## Nguồn list ống V1.1

1. Chọn hầm/phương án muốn dùng. **Xem VINAFCO 268** mở hầm tham chiếu ước tính, giới hạn chuyến theo mức hàng tham chiếu của cấp. Nạp list không tự đổi phương tiện hoặc giới hạn chuyến.
2. **Xem trước list ống** để xem nguồn: 31 nhóm, 1.076 bó, 21.226 ống. **Nạp list vào phương án hiện tại** thay manifest và xóa các placement cũ; có thể quay về **Bản trước**. Mọi bó ban đầu chưa xếp, yêu cầu mặc định **Tùy chọn**, vì nguồn chưa xác nhận toàn bộ list bắt buộc cho một chuyến.
3. Trong **Danh sách hàng**, lọc **Nhóm nguồn** theo dòng Excel (`Sheet1-R002` là dòng 2) và dùng **Trang trước/Trang sau**, tối đa 50 bó/trang. ID `PIPE-R002-B0001` là bó thứ nhất ở dòng 2, không dùng STT nguồn làm khóa.
4. Chọn bó → **Đặt bó** tại gốc hầm, sửa X/Y/góc → **Áp dụng & kiểm lại**. Đặt tiếp tại cùng gốc sẽ báo giao nhau; nút Đặt bó không tự tìm vị trí; dùng M2b bên dưới để xếp thử. **Bỏ vị trí** đưa bó về chưa xếp. Số bó/ống/khối lượng đã xếp và còn lại có cho toàn list lẫn nhóm đang lọc. Bó **Loại trừ** vẫn thuộc tồn hàng nguồn nhưng không được đặt; số liệu còn lại bao gồm các bó này.
5. Các trường khối lượng/kích thước/ID nguồn cố định. Có thể đổi yêu cầu và vị trí; muốn thay danh sách bằng dữ liệu tự nhập dùng **Phương án mới** hoặc CSV. **Dùng hầm tự nhập** giữ list và bỏ liên kết tàu, cho sửa hầm BOX chưa xác minh. Đổi VR-SI/VR-SII và lưu/mở giữ provenance/placement của list.
6. Lưu snapshot như phần M2a. Reload → mở bản đã lưu; rawdraft vẫn không tự lưu. Sửa nháp phải kiểm lại trước khi nạp list/đổi phương án; phản hồi đến muộn không ghi đè thay đổi mới.

Khối lượng bó = K (kg/ống) × L (ống/bó), lưu gram nguyên. Tổng tính **1.125,55103t**, tổng O nguồn **1.125,52t**, lệch **31,03kg**; không phải dữ liệu cân từng bó. CBM nguồn **1.130,96964733156m³**, khối bao tính lại **1.157,54318105797m³** (R23:R26 nguồn chưa nhân số bó). Thể tích khối bao có khoảng rỗng, không chứng minh khả năng xếp vừa. Kích thước nguồn giữ chính xác trong dữ liệu; mô hình/bảng hiển thị cm nguyên hoặc m hai số lẻ, khối lượng chi tiết theo kg nguyên. Đây là làm tròn hiển thị; hình học kiểm và vị trí lưu không bị thay đổi.

16 bó ở dòng 22/31/32 có khối bao cần xác minh; app giữ cảnh báo và không tự sửa kích thước hoặc vẽ từng ống. Chỉ các bó đã đặt mới có mesh trong hầm. Nếu có quá nhiều lỗi, danh sách chỉ hiện 200 lỗi nhưng tổng đếm và các bó bị ảnh hưởng vẫn đầy đủ. Ship GLB/profile không đổi. Workbook/gói nguồn V1.1 giữ local ngoài Git; runtime dùng derivative có hash, không cần mở Excel. [Đánh giá cách tính](reviews/SCST_PIPE_LIST_ASSESSMENT.md), [SPEC](specs/SCST_PIPE_LIST.md).

## M2b — Xếp thử tự động một lớp

1. Chọn hầm và nạp hàng; để xem trên thân tàu, chọn **Xem VINAFCO 268**. Áp dụng nháp trước nếu đang STALE. Chọn **Xếp thử tự động** gần khu vực thống kê/viewer.
2. Xem số bó/tổng khối lượng được gợi ý, sức chở còn lại và lý do các bó chưa đặt. Workspace/mesh hiện tại chưa đổi. Lượt này dựng lại mọi vị trí cũ trong candidate, không khóa giữ từng bó đã đặt.
3. **Áp dụng xếp thử** để đưa kết quả lên tàu/hầm 3D và mặt bằng. **Bản trước** khôi phục trước áp dụng. Chọn bó đã đặt để sửa X/Y/góc rồi kiểm lại; có thể bỏ vị trí hoặc đổi yêu cầu như trước.
4. Phần lý do phân trang50bó, lọc theo loại. `Loại trừ`: requirement không cho đặt; `Vượt chiều cao`: bó cao hơn hầm; `Khối bao quá lớn`: cả2hướng không vừa hầm; `Giới hạn khối lượng`: không đủ tải còn lại; `Chưa tìm được chỗ`: heuristic chưa có vị trí, có thể có cách xếp khác. Hàng bắt buộc chưa đặt vẫn được rule báo, không tự đổi thành tùy chọn.
5. Lưu/mở giữ placements và nguồn chính xác; lý do heuristic không lưu trong snapshot. Sau chỉnh hoặc mở phương án, chạy lại xếp thử để tính lý do mới. Lỗi mạng/preview đến muộn không ghi đè edit mới.

Xếp thử không tự tăng giới hạn chuyến đang khai báo. Với list nguồn 1076 bó trên hầm tham chiếu ở mức VR-SII, cách **Một tầng** đặt 167 bó (217,74t), còn 909 bó vì hết diện tích sàn. Cách nhiều tầng ở mục M3a dưới đây đặt đủ 1076 bó. Không khẳng định tối ưu; chưa tính kê/chèn/chằng, tải chồng, tải sàn, ổn định/sức bền. Bó cần xác minh và hầm ước tính vẫn giữ nhãn.

Khối lượng ở bảng/thống kê hiển thị tối đa2số lẻ tấn: **1.125,55tấn** thay cho1.125,55103; số nhỏ khác0 hiện **<0,01tấn**. Tính/lưu bằng gram, ô nhập kg không làm tròn. Hai CBM hiển thị gọn1.130,97/1.157,54m³, số đầy đủ vẫn ở [đánh giá nguồn](reviews/SCST_PIPE_LIST_ASSESSMENT.md). Heuristic dùng lưới mm làm tròn lên để dự trữ khối bao, geometry kiểm/vẽ vẫn chính xác µm; khe lưới chưa phải khoảng kê/chèn nghiệp vụ.

## M3a — Xếp nhiều tầng theo cột

1. Ô **Cách xếp thử** cạnh nút **Xếp thử tự động** có hai lựa chọn:
   - **Nhiều tầng theo cột (thử nghiệm)**: mặc định khi phương án là list ống.
   - **Một tầng (như cũ)**: mặc định cho phương án khác.

   Lựa chọn bạn đổi được giữ trong tab.
2. Nhiều tầng: các bó **cùng kích thước** chồng thành cột thẳng đứng trên một vị trí sàn. Cột dừng khi tầng kế tiếp vượt chiều cao hầm hoặc hết khối lượng cho phép.
   - Xem trước ghi "Nhiều tầng: N cột · tối đa M tầng · đã xếp … bó · chưa xếp … bó".
   - Lý do chưa xếp có thêm **Hết chiều cao cột**.
3. Sau **Áp dụng xếp thử**:
   - bảng hàng có cột **Tầng**;
   - chi tiết bó ghi "Tầng N · Z … cm · Bó đỡ: …";
   - mặt bằng 2D ghi "×N" cho cột nhiều tầng;
   - 3D đặt từng bó đúng cao độ.
4. App kiểm đỡ cho mọi bó ở trên đáy hầm:
   - có bó đỡ;
   - mặt trên bó đỡ khớp cao độ;
   - phủ ≥ 90% diện tích đáy;
   - tâm đáy nằm trên bó đỡ;
   - đúng chỉ số tầng.

   Nếu bạn chỉnh tay X/Y một bó tầng trên mà làm mất đỡ, kiểm lại sẽ báo lỗi có tên bó và bó đỡ.
5. Khi dữ liệu hàng có revision mới và bạn tạo bản theo dữ liệu mới: bó bị bỏ hoặc đổi kéo theo các bó nằm trên nó, được ghi **Mất đỡ** trong danh sách vị trí bị bỏ.
6. Báo cáo của phương án nhiều tầng có cột tầng/bó đỡ, tổng số tầng và cảnh báo "Phương án nhiều tầng: chưa kiểm tải chồng, tải sàn, chằng buộc và ổn định".

Giới hạn:
- Chưa xếp lẫn kích thước trong một cột, chưa có gỗ kê.
- Khe giữa các tầng dưới 1 mm do làm tròn lưới, chưa phải khoảng kê.
- Chưa có dữ liệu tải chồng cho phép.

Xem [SPEC](specs/SCST_M3A.md) và [review](reviews/SCST_M3A_REVIEW.md).

## M5a — Sao lưu và khôi phục

1. Mục **Sao lưu và khôi phục** nằm trong khu lưu/mở phương án.
2. **Tải bản sao lưu** tải tệp `scst-backup-YYYYMMDD-HHMMSS.scstbak`:
   - gồm mọi phương án đã lưu, revision dữ liệu hàng và hồ sơ tàu đã nhập;
   - kèm `manifest.json` có sha256 từng tệp;
   - không chứa đường dẫn trên máy.

   Cất tệp ra ngoài máy.
3. **Khôi phục từ bản sao lưu** → chọn tệp. App kiểm toàn bộ trước khi làm gì:
   - cấu trúc ZIP an toàn;
   - mã sha256;
   - cơ sở dữ liệu;
   - từng phương án;
   - chuỗi revision;
   - từng hồ sơ tàu.

   Sau đó app hiện số liệu trong tệp so với dữ liệu hiện tại. Tệp lỗi được báo bằng tiếng Việt và không thay đổi gì.
4. Bấm **Khôi phục** để **thay toàn bộ** dữ liệu.
   - Trước khi thay, app tự tạo `runtime-data/backups/pre-restore-<thời điểm>.scstbak` từ dữ liệu hiện tại.
   - Nếu lỗi giữa chừng, ví dụ tệp đang bị chương trình khác mở, dữ liệu cũ được giữ nguyên từng byte.
   - Bản nháp chưa lưu trong tab vẫn còn, nhưng không thuộc dữ liệu vừa khôi phục.

Chưa có: sao lưu tự động theo lịch, mã hóa, khôi phục gộp hoặc chọn từng phần. Xem [SPEC](specs/SCST_M5A.md) và [review](reviews/SCST_M5A_REVIEW.md).

## M2c — Giữ bản gốc và so sánh

1. Khi bản nháp đã áp dụng, chọn **Giữ bản hiện tại làm gốc** để giữ A trong tab. Hoặc chọn một **Bản lưu làm gốc → Dùng bản lưu làm gốc**; thao tác này không thay B đang mở hoặc lựa chọn bó. Baseline không tự thay khi mở phương án khác hay chạy xếp thử.
2. Chỉnh B bằng các ô đang có, rồi **Áp dụng & kiểm lại**. Bấm **So sánh với bản gốc**. Bảng đầu cho tổng khối lượng, đã xếp/còn tải, số bó và số lỗi kiểm riêng A/B; chênh lệch B−A dùng kg, kích thước/vị trí dùng cm/m. Tổng A/B vẫn làm tròn tối đa hai số lẻ tấn. Chênh khác không nhưng dưới mức hiển thị có nhãn “dưới 1 kg” hoặc “dưới 1 cm”, không báo bằng 0. Dữ liệu so sánh vẫn giữ đầy đủ để không bỏ sót thay đổi.
3. Lọc **Chỉ thay đổi / Tất cả / Thêm / Đã bỏ / Thay đổi / Không đổi**, tìm ID và chuyển trang tối đa 50 bó. **Chi tiết thay đổi** ghi trước/sau từng trường; **Chọn bó trong B** đồng bộ editor/viewer hiện tại. Bó chỉ còn trong A không có nút chọn vào B. Hai bản khác nguồn/giới hạn/hầm có cảnh báo, không tự xếp hạng. ID trùng nhưng nguồn khác không xác nhận cùng bó vật lý.
4. **Khôi phục bản gốc** kiểm lại A trước khi đổi workspace. B được giữ trong **Bản trước**, có thể quay lại rồi lưu riêng; snapshot A không bị ghi đè. Tên/thời gian/ID của baseline đã lưu tách biệt với bản đang mở.
5. Baseline trong bộ nhớ chưa tự lưu và mất khi reload; để dùng lại, lưu A trước và chọn lại bản đã lưu. Không tự lưu nháp hoặc kết quả so sánh. STALE chặn chọn/so sánh/khôi phục cho tới khi áp dụng nháp; lỗi mạng hoặc phản hồi đến muộn giữ dữ liệu hiện có. Khi chỉnh dữ liệu, kết quả so sánh cũ không được trình bày như kết quả hiện hành.

Luồng dùng một viewer của B, không có hai cảnh 3D song song. So sánh là đối chiếu dữ liệu và các kiểm hiện hành, chưa kiểm kê/chèn/chằng, nhiều tầng, ổn định hay tải sàn. Hầm ước tính và 16 khối bao cần xác minh vẫn giữ nguyên. [SPEC](specs/SCST_M2C.md), [review và bằng chứng](reviews/SCST_M2C_REVIEW.md).

## Đơn vị hiển thị theo thực tế

- Chi tiết bó và chênh khối lượng: kg nguyên; thống kê tổng: tấn tối đa hai số lẻ.
- Kích thước và tọa độ: cm nguyên; thông số tàu/hầm có thể dùng m tối đa hai số lẻ.
- Các số đã làm tròn là xấp xỉ. Sửa góc/yêu cầu không làm thay đổi khối lượng hoặc vị trí chưa sửa; nhập lại một số làm tròn vào chính ô đó là thay đổi chủ động.
- Đây không phải dung sai cho phép vượt hầm hoặc quá tải. Kiểm hình học, khối lượng và dữ liệu nguồn vẫn dùng số gốc.
- CSV là định dạng trao đổi riêng: header vẫn ghi `length_mm,width_mm,height_mm,mass_kg`; dùng đúng đơn vị ghi trong file. Không đổi số trong CSV sang cm mà giữ header mm.

Xem [SPEC đơn vị hiển thị](specs/SCST_DISPLAY_UNITS.md).

## SUP-01 — Quan sát 3D và giữ góc nhìn

- **Vừa khung** hoặc nút **Đặt lại góc nhìn** căn hầm/hàng và phần tàu đang hiện vào khung. **Nhìn trên** và **Nhìn mạn** đổi hướng quan sát; **Tập trung bó** dùng cho bó đã chọn và đã đặt.
- Khi chỉnh/kiểm lại hàng, đổi trạng thái tham chiếu hoặc ẩn/hiện tàu trong cùng hầm, góc nhìn đang dùng được giữ. Thay hầm/phương tiện sẽ căn khung theo cảnh mới.
- Trên VINAFCO, **Vật liệu gốc / Thân mờ** đổi cách thấy vỏ và vách hầm; **Ẩn tàu / Hiện tàu** điều khiển lớp tàu riêng. Các nút quan sát không đổi số liệu hoặc phương án.
- **Mặt bằng** và chọn ID vẫn dùng được khi WebGL hoặc asset tàu gặp lỗi. Khi asset lỗi, hầm và hàng còn hiển thị; khi WebGL lỗi, app chuyển sang mặt bằng.

## Kiểm nhà phát triển

```powershell
.venv/Scripts/python.exe -m pytest tests/backend -q
.venv/Scripts/python.exe tooling/export_contract.py
npm.cmd --prefix apps/frontend run contract
npm.cmd --prefix apps/frontend run build
npm.cmd --prefix apps/frontend run test:e2e
```

Cây thực: `services/backend/app/domain/{model,geometry,rules,planner,comparison}` chứa contract và kiểm; `services/backend/app/api` phục vụ API; `apps/frontend/src/{api,features,viewer-3d}` là giao diện; `contracts/openapi.json` và `apps/frontend/src/api/generated/api.ts` được sinh; `tests/backend`, `tests/browser` chứa kiểm; `tooling/` và `Start-SCST.cmd` khởi chạy.

Đã có: nhập tay/CSV, lưu/mở local, revision dữ liệu hàng, hồ sơ tàu, xếp thử một tầng và nhiều tầng theo cột, xuất báo cáo XLSX/trang in, sao lưu/khôi phục.

Ngoài phạm vi hiện tại:
- xếp tối ưu, xếp lẫn kích thước trong cột;
- tải chồng, tải sàn, chằng buộc, ổn định;
- import XLSX/PDF tổng quát;
- xác minh manifest/hầm đo thực (M3b);
- bộ cài, sao lưu tự động;
- AI.

Bắt đầu dùng thử từ [trang bàn giao MVP](SCST_MVP_HANDOFF.md).
