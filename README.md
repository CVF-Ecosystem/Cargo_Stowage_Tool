# Steel Cargo Stowage Tool · SCST

Công cụ hỗ trợ lập phương án xếp hàng thép trong hầm tàu, chạy local với giao diện tiếng Việt. SCST hướng tới luồng **nhập hàng và hầm → đề xuất xếp → xem 3D → chỉnh và kiểm lại → lưu, so sánh, xuất báo cáo**.

**Hiện tại là MVP để dùng thử**, gồm:

- xếp thử tự động **một tầng hoặc nhiều tầng theo cột**: list 1.076 bó xếp vừa hầm VINAFCO ước tính;
- revision dữ liệu hàng và hồ sơ tàu;
- xuất báo cáo XLSX và trang in;
- **sao lưu/khôi phục dữ liệu local**;
- nhập liệu, CSV, lưu/mở, giữ gốc và so sánh phương án.

Hầm vẫn dạng hộp (BOX) và là ước tính. Tải chồng, tải sàn, chằng buộc và ổn định chưa được kiểm. **Bắt đầu từ [trang bàn giao MVP](docs/SCST_MVP_HANDOFF.md).**

## Bản hiện tại làm được gì?

- Xem bó hàng và vị trí xếp trên bảng, mô hình 3D và mặt bằng 2D; chọn hàng đồng bộ giữa các góc nhìn.
- Sửa khối lượng, tọa độ X/Y và góc xoay; áp dụng thay đổi và kiểm lại qua backend.
- Khai báo giới hạn tải theo chứng nhận, theo chuyến và lượng hàng đã có trên tàu.
- Kiểm tải, vượt biên hầm, giao nhau giữa các bó và hàng bắt buộc chưa xếp.
- Đánh dấu dữ liệu đã sửa là `STALE`, giữ kết quả đã kiểm trước và quay lại bản trước.
- Chuyển sang bảng/2D khi trình duyệt không hỗ trợ WebGL.
- Tạo phương án rỗng, thêm/sửa/xóa bó và chỉnh hầm BOX tự nhập; đặt/bỏ vị trí từng bó.
- Import CSV UTF-8 có xem trước số bó, tổng khối lượng và lỗi theo dòng/trường; áp dụng toàn bộ khi hợp lệ.
- Lưu các bản phương án riêng bằng SQLite local và mở lại sau tải trang hoặc khởi động lại server.
- Giữ bản gốc A, chỉnh bản B, so sánh từng bó/vị trí/giới hạn và khôi phục A; các bản đã lưu không bị ghi đè.
- Xếp thử nhiều tầng theo cột, có kiểm đỡ: phủ ≥ 90% đáy, tâm đáy nằm trên bó đỡ, đúng cao độ và chỉ số tầng.
- Ghi revision dữ liệu hàng; báo phương án nào cần kiểm lại và tạo bản theo dữ liệu mới.
- Nhập hồ sơ tàu kèm mô hình GLB.
- Xuất báo cáo XLSX và trang in.
- Tải bản sao lưu toàn bộ dữ liệu local và khôi phục có kiểm.

> Nhấn **Lưu phương án** để giữ bản đã kiểm; nháp chưa lưu mất khi tải lại/đóng tab. Kết quả kiểm chưa bao gồm tải chồng, tải sàn, kê/chèn/chằng hoặc ổn định tàu. Dữ liệu mẫu và hình học chưa xác minh chưa dùng cho phương án thực.

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

### Xem sà lan VINAFCO 268

Trong app, chọn **Xem VINAFCO 268** để mở mô hình thân tàu, hầm và hàng. Có thể xoay, phóng to, ẩn/hiện hình tàu mờ và chọn cấp tham chiếu **VR-SI / VR-SII**. Kích thước thân theo hồ sơ: **77,8 × 13,24 × 5,2 m**; hầm, cabin và tuyến hình vẫn là ước tính có nhãn. Marker mớn theo cấp, không tính từ lượng hàng đang xếp.

Khi chọn VINAFCO 268 hoặc đổi cấp, giới hạn chuyến lấy theo mức hàng tham chiếu của cấp đó (VR-SII: 3.517,5 tấn), kèm thông báo. Có thể chỉnh lại trong **Giới hạn chuyến (kg)**. Mức hàng này tách riêng với trọng tải toàn phần. Hãy áp dụng bản nháp trước khi đổi cấp hoặc quay lại bản trước.

Xem [đánh giá nguồn](docs/reviews/SCST_VINAFCO268_ASSESSMENT.md) và [review tích hợp](docs/reviews/SCST_VINAFCO268_REVIEW.md). PDF đăng kiểm gốc được giữ local, không nằm trong source app hoặc API.

## Nhập hàng và lưu phương án

1. Chọn **Phương án mới** để bắt đầu với hầm BOX và danh sách hàng rỗng, hoặc giữ chế độ VINAFCO hiện có.
2. Nhập từng bó ở **Thêm bó hàng**, hoặc chọn [CSV mẫu giả lập](docs/examples/manifest_m2a_synthetic.csv) trong **Nhập CSV UTF-8** → **Kiểm CSV** → xem trước → **Áp dụng CSV**. Import thay toàn bộ manifest và bỏ các vị trí xếp cũ; các bó mới ở trạng thái chưa xếp.
3. Chọn bó → **Đặt bó** → sửa vị trí → **Áp dụng & kiểm lại**. Hoặc dùng Xếp thử tự động M2b ở phần dưới.
4. Điền tên → **Lưu phương án**. Sau reload, chọn bản trong **Phương án đã lưu** → **Mở phương án**; backend kiểm lại trước khi hiển thị.

CSV gồm một dòng cho mỗi bó, tối đa 200 bó/1 MiB; kích thước bằng mm, khối lượng kg dùng dấu chấm thập phân với tối đa 3 số lẻ. Chưa nhận XLSX/PDF. Mỗi lần lưu tạo một bản mới, không ghi đè; dữ liệu nằm tại `runtime-data/scst.sqlite3` ngoài Git, danh sách hiện 100 bản gần nhất.

## List ống thép Baltimore — nguồn V1.1

Gói local bổ sung **31 nhóm, 1.076 bó, 21.226 ống**. Chọn **Xem VINAFCO 268** nếu muốn dùng hầm tham chiếu, rồi **Xem trước list ống** → **Nạp list vào phương án hiện tại**. Nạp thay danh sách hàng và bỏ vị trí cũ; tất cả bó bắt đầu chưa xếp. Lọc **Nhóm nguồn**, chọn bó → **Đặt bó**, chỉnh X/Y/góc rồi **Áp dụng & kiểm lại**. Có thể **Bỏ vị trí** và lưu/mở như phương án khác. Dùng Xếp thử tự động M2b ở phần dưới để bố trí thử.

Khối lượng bó tính từ **kg/ống × số ống/bó**: tổng hiển thị **1.125,55 tấn** (giữ chính xác1.125,55103t khi tính/lưu), so với tổng dòng nguồn **1.125,52 tấn**, chênh **31,03 kg**. App giữ cả hai để đối chiếu. Kích thước khối bao theo nguồn, không tự sửa; 16 bó có cảnh báo cần xác minh. Các trường vật lý nguồn cố định, yêu cầu và vị trí được chỉnh. List chưa gán sẵn tàu/chuyến, không khẳng định toàn bộ list vừa hầm. Giới hạn CSV phổ thông vẫn là 200 bó; đây là adapter riêng cho nguồn đã chuẩn hóa, chưa phải importer XLSX tổng quát.

Xem [kiểm cách tính và quyết định tích hợp](docs/reviews/SCST_PIPE_LIST_ASSESSMENT.md). Workbook/gói gốc giữ local ngoài Git, mô hình sà lan giữ nguyên.

## Xếp thử tự động và xem hàng trên tàu

Sau khi nạp hàng/chọn hầm, bấm **Xếp thử tự động** → xem số bó/khối lượng và lý do chưa xếp → **Áp dụng xếp thử**. Các bó được bố trí sẽ hiện trong hầm 3D/2D, có thể chọn/chỉnh tay và lưu/mở. Xem trước chưa đổi vị trí cũ; áp dụng giữ **Bản trước** để quay lại. Khi chưa có placement, viewer chỉ dẫn luồng này.

Ô **Cách xếp thử** có hai lựa chọn:

- **Nhiều tầng theo cột (thử nghiệm)**: mặc định cho list ống. Các bó cùng kích thước chồng thành cột thẳng đứng, có kiểm đỡ.
- **Một tầng (như cũ)**: mặc định cho phương án khác.

Cả hai xét xoay 0/90°, ưu tiên hàng bắt buộc và tuân theo giới hạn chuyến trừ hàng đã có. Với list 1.076 bó trên hầm VINAFCO ước tính ở mức VR-SII:

- nhiều tầng đặt **1.076/1.076 bó**, 98 cột, cao tối đa 18 tầng, trong khoảng 0,05 giây;
- một tầng chỉ đặt 167 bó, vì giới hạn nằm ở diện tích sàn.

Mặt bằng 2D ghi "×N" cho số tầng của mỗi cột; bảng hàng có cột **Tầng**; chi tiết bó ghi cao độ và bó đỡ. Đây là kết quả heuristic, không phải tối ưu. Kết quả chỉ chứng minh khối bao vừa hầm ước tính về hình học, chưa xét tải chồng, tải sàn, chằng buộc hay ổn định. Xem [review M3a](docs/reviews/SCST_M3A_REVIEW.md).

Khối lượng **hiển thị tối đa2số lẻ**, ví dụ **1.125,55 tấn**; tính/lưu và ô nhập kg vẫn giữ chính xác. Lý do xếp thử chỉ ở lượt phân tích trong tab, sau mở/chỉnh phương án chạy lại để có lý do mới. [SPEC M2b](docs/specs/SCST_M2B.md) và [hướng dẫn](docs/APP_GUIDE.md).

## Giữ gốc, so sánh và khôi phục

Bấm **Giữ bản hiện tại làm gốc**, hoặc chọn **Bản lưu làm gốc → Dùng bản lưu làm gốc**. Việc chọn A giữ nguyên phương án B đang mở. Chỉnh B và **Áp dụng & kiểm lại**, rồi **So sánh với bản gốc** để xem bó thêm/bỏ/đổi/không đổi, khối lượng, số bó, số lỗi và điều kiện thay đổi. Có lọc, tìm ID, phân trang 50 bó và chi tiết trường; chênh lệch khối lượng dùng kg, kích thước/vị trí dùng cm/m; tổng A/B vẫn gọn hai số lẻ tấn. Chênh dưới mức hiển thị có nhãn, dữ liệu gốc không bị làm tròn.

**Khôi phục bản gốc** kiểm lại A rồi đưa vào workspace; B vẫn còn trong **Bản trước**. Mỗi lần lưu tạo bản mới. Baseline chỉ giữ trong tab và không tự lưu; muốn dùng sau reload, lưu phương án rồi chọn lại bản đã lưu. Chênh lệch giữa hai bản không tự chứng minh bản nào tốt hơn hoặc đủ điều kiện vận hành. Xem [SPEC M2c](docs/specs/SCST_M2C.md) và [review](docs/reviews/SCST_M2C_REVIEW.md).

## Báo cáo, sao lưu và khôi phục

**Xuất báo cáo** mở trang in A4 và cho tải tệp XLSX của phương án đã lưu. Phương án nhiều tầng có thêm cột tầng/bó đỡ, tổng số tầng và cảnh báo các phần chưa kiểm.

Mục **Sao lưu và khôi phục**:

- **Tải bản sao lưu** tạo một tệp `.scstbak`, gồm toàn bộ phương án đã lưu, revision dữ liệu hàng và hồ sơ tàu đã nhập, kèm mã kiểm sha256.
- **Khôi phục từ bản sao lưu** kiểm toàn bộ tệp trước, cho xem số liệu, rồi **thay toàn bộ** dữ liệu hiện có. Trước khi thay, app tự lưu dữ liệu hiện tại vào `runtime-data/backups/`. Nếu lỗi giữa chừng, dữ liệu cũ được giữ nguyên.
- Chưa có sao lưu tự động theo lịch, mã hóa hay khôi phục gộp. Xem [review M5a](docs/reviews/SCST_M5A_REVIEW.md).

Số liệu trên mô hình/bảng dùng **kg, cm hoặc m**, làm tròn phù hợp thao tác thực tế. Dữ liệu chưa sửa giữ nguyên; làm tròn hiển thị không tạo dung sai vượt biên hoặc quá tải. Ô nhập dùng kg/cm; CSV vẫn theo đơn vị ghi trong header. Xem [quy ước](docs/APP_GUIDE.md).

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
│   │   ├── rules/                  # Kiểm quy tắc nghiệp vụ
│   │   ├── planner/                # Heuristic xếp thử một tầng và nhiều tầng theo cột, lý do chưa xếp
│   │   └── comparison/             # So sánh chính xác, kiểm riêng hai phương án
│   └── adapters/                   # Import CSV, snapshot SQLite, revision, hồ sơ tàu, sao lưu/khôi phục
├── contracts/                      # OpenAPI contract
├── tests/                          # Backend, browser và kiểm khởi chạy
├── tooling/                        # Cài đặt, build, chạy local, sinh contract
├── docs/                           # Roadmap, SPEC, quyết định, hướng dẫn, review
└── archive/                        # Tài liệu lịch sử và bản thử cũ
```

Frontend hiển thị kết quả từ backend; chỉnh sửa cần được kiểm lại. Backend dùng SQLite cho snapshot local, có heuristic xếp thử một tầng và nhiều tầng, chưa tích hợp AI. Cây kiến trúc tương lai nằm trong [roadmap tổng thể](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md).

## Lộ trình phát triển

Đã đối chiếu [CVF-DEV — áp dụng CVF tại project](docs/project/SCST_CVF_DEVELOPMENT_ADOPTION.md) và dùng mapping trong SPEC/WORK_ORDER, kiểm và review SUP-01. Full adoption và bằng chứng hành vi agent chưa được nghiệm thu.

Roadmap bổ sung **SUP-01 viewer 3D → SUP-02A/B dữ liệu hàng và hồ sơ tàu theo phiên bản → SUP-03 packing → M2d xuất báo cáo** đã giao kỹ thuật. Tiếp theo là HARDEN-01, **M3a xếp nhiều tầng** và **M5a sao lưu/khôi phục**, tất cả đã có review độc lập trong `docs/reviews/`. Xem [roadmap bổ sung](docs/roadmaps/SCST_ROADMAP_BO_SUNG_3D_VA_DU_LIEU.md) và [trang bàn giao MVP](docs/SCST_MVP_HANDOFF.md).

| Mốc | Kết quả hướng tới | Trạng thái |
|---|---|---|
| M0 — Thống nhất hướng | Phạm vi, thứ tự phát triển và kiến trúc tổng thể | Đã thống nhất |
| M1 — Demo chạy được | Hầm BOX, hàng giả lập, bảng/3D, sửa và kiểm cơ bản | Đạt kiểm kỹ thuật; chờ phản hồi nghiệp vụ |
| M2 — Tool trọn luồng | Nhập/import, lưu/mở, xếp sơ bộ, chỉnh/so sánh, xuất PDF/XLSX; hình tàu minh họa ở M2c | Đạt kiểm kỹ thuật (M2a–M2d); chờ nghiệm thu nghiệp vụ |
| M3 — Case thực | Hình học phù hợp dữ liệu thực, nhiều tầng, profile kê/chồng; hiệu chỉnh hình tàu | **M3a** (nhiều tầng theo cột trên hầm ước tính) đạt kiểm kỹ thuật; **M3b** (case thực, hầm đo, tải chồng) chờ dữ liệu owner |
| M4 — AI hỗ trợ | Hỗ trợ tác vụ có nhu cầu rõ; core vẫn chạy khi tắt AI | Nhánh tùy chọn |
| M5 — Sử dụng ổn định | Đóng gói, lưu trữ bền, backup/restore và hiệu năng | **M5a** (sao lưu/khôi phục) đạt kiểm kỹ thuật; bộ cài và sao lưu tự động chưa làm |

Theo yêu cầu bổ sung của owner, lớp hình tàu VINAFCO 268 được tích hợp sớm thành một phần riêng của viewer. MVP đang được giao owner dùng thử; nghiệm thu nghiệp vụ và M3b cần owner. Các mốc xa giữ ở mức tổng thể; chỉ chi tiết hóa phần sắp làm khi được chọn. Xem [phạm vi, đầu ra và phụ thuộc từng mốc](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md).

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

Sau tích hợp VINAFCO 268, bộ kiểm hiện tại đạt **63 backend test, 9 browser test và 109 kiểm độc lập bổ sung**; xem [review VINAFCO 268](docs/reviews/SCST_VINAFCO268_REVIEW.md).

Sau M2a, bộ kiểm đạt **79 backend test, 13 browser test và kiểm lưu/mở qua hai lần chạy server riêng biệt**. Xem [review M2a](docs/reviews/SCST_M2A_REVIEW.md) và [SPEC M2a](docs/specs/SCST_M2A.md).

Bản M2c đạt **104 backend test, 28 browser test và 902 đối chiếu độc lập**, cùng kiểm hai tiến trình server, build và contract. Xem [review M2c](docs/reviews/SCST_M2C_REVIEW.md); nghiệm thu nghiệp vụ vẫn riêng.

Lượt chỉnh đơn vị hiển thị đã đạt **31 browser test**; dữ liệu tính và các phương án chưa sửa được giữ nguyên. Xem [review đơn vị hiển thị](docs/reviews/SCST_DISPLAY_UNITS_REVIEW.md).

Sau M5a (05-11-2026), bộ kiểm đạt **878 backend test, 57 browser test và kiểm tích hợp 29/29** khi chạy lại trên Windows. Xem [review M3a](docs/reviews/SCST_M3A_REVIEW.md) và [review M5a](docs/reviews/SCST_M5A_REVIEW.md).

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [Bàn giao MVP](docs/SCST_MVP_HANDOFF.md) | Bắt đầu tại đây: thử luồng chính, sao lưu, giới hạn, góp ý cần owner |
| [Hướng dẫn sử dụng](docs/APP_GUIDE.md) | Khởi chạy, thao tác và giới hạn demo |
| [Trạng thái project](docs/project/PROJECT_STATUS.md) | Phần đã làm và bước tiếp theo |
| [Roadmap tổng thể v0.3](docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) | Phạm vi, đầu ra từng mốc và kiến trúc dự kiến |
| [SPEC M1](docs/specs/SCST_M1.md) | Hành vi và tiêu chí kỹ thuật M1 |
| [Review M1](docs/reviews/SCST_M1_REVIEW.md) | Kết quả đối chiếu tiêu chí và bằng chứng |
| [Đánh giá tái sử dụng M1](docs/reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) | Căn cứ chọn source và kết quả thực hiện |
| [Mục lục tài liệu](docs/INDEX.md) | Điều hướng hồ sơ project |
| [Kho lưu trữ](archive/README.md) | Lịch sử, tài liệu cũ và bản thử đã dừng |

Thiết kế [áp dụng CVF trong quá trình dựng tool](docs/project/SCST_CVF_DEVELOPMENT_ADOPTION.md) phân biệt bộ kit hiện có, điểm gọi đã có receipt và phần chưa được chứng minh. Agent và người tiếp quản đọc [AGENTS.md](AGENTS.md) cùng [session memory](CVF_SESSION_MEMORY.md) trước khi thay đổi project. Cấu hình CVF phục vụ quy trình phát triển; app hiện tại chưa tích hợp AI hoặc CVF runtime.
