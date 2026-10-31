# SCST M1 — Khung chạy được

Status: DRAFT

**Bản v0.1 · 31-10-2026 · Chờ owner thống nhất.** SPEC này chưa cấp quyền thi công; BUILD chỉ bắt đầu khi có WORK_ORDER riêng. Căn cứ: [roadmap v0.2](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) (dòng M1, nguyên tắc xuyên suốt) và [quyết định SCST-D001](../decisions/SCST_D001_THONG_NHAT_HUONG_M0_2026-10-31.md).

## Mục tiêu M1

Chứng minh **khung và luồng dữ liệu**: chạy local, backend trả hầm/hàng/phương án synthetic, giao diện hiện bảng và 3D cùng một dữ liệu, người dùng sửa một giá trị và backend kiểm lại. M1 không lập phương án tự động, không lưu bền và không dùng dữ liệu thật.

**Người dùng M1:** owner hoặc người được owner giao, xem demo để xác nhận hướng trước M2.

## Đối chiếu bản thử M1 trong archive

Nguồn: [archive/2026-10-31/paused-m1](../../archive/2026-10-31/paused-m1/README.md). Đã đọc SPEC cũ, hướng dẫn chạy, source domain/API và danh sách test. Kết quả test cũ (27 backend, 3 browser) thuộc bản thử, **không tính là nghiệm thu**.

| Hạng mục | Bản thử đã có | So với M1 mới | Việc cần làm |
|---|---|---|---|
| Khởi chạy local | `Start-SCST.cmd`, một server phục vụ API + frontend đã build, AI tắt | Khớp | Dùng lại; kiểm lại trên bản mới |
| Stack | React/TS + Vite, Three.js; Python 3.11/FastAPI/Pydantic; OpenAPI → client TS sinh tự động; có lock file | Khớp roadmap | Dùng lại; kiểm phiên bản khi cài |
| Đơn vị, định danh | Integer mm/gram, từng bó có ID/kích thước/khối lượng, từ chối số không nguyên và trường lạ | Khớp nguyên tắc | Dùng lại |
| Cấu trúc domain | Ba file phẳng `models.py`, `validation.py`, `demo.py`; hình học và quy tắc trộn trong một hàm | **Lệch** cây mới (`model/`, `geometry/`, `rules/`) | Tách theo cây; không đổi kết quả kiểm |
| Giới hạn tải | Một trường `cargo_limit_g` gắn với hầm | **Thiếu** phân biệt giới hạn giấy chứng nhận / theo chuyến / hàng đã có trên tàu | Mở rộng contract (xem D2) |
| Chừa trường nhiều tầng | Có `z_mm`; `z ≠ 0` bị báo `LAYER_UNSUPPORTED` | **Thiếu** trường lớp và quan hệ đỡ | Thêm trường dự trữ, không thêm logic (xem D3) |
| Nhãn trạng thái | `basic_checks_passed` + `operational_eligible=false` | **Thiếu** nhãn DRAFT / GEOMETRY_FEASIBLE / RULES_CHECKED / STALE | Thêm (xem D4) |
| Kiểm cơ bản | Vượt tải (đúng tới 1 gram), vượt biên toàn khối (đúng tới 1 mm), va chạm thể tích dương, xoay 90°, required/optional/excluded | Khớp | Dùng lại, chuyển vào `rules/` + `geometry/` |
| Bảng + 3D + 2D | Cùng ID/tọa độ từ API, chọn đồng bộ, orbit/zoom/reset, mặt bằng 2D khi không có WebGL, lọc/tìm | Khớp | Dùng lại; thêm hiển thị nhãn trạng thái và giới hạn tải |
| Sửa và kiểm lại | Sửa mass/vị trí/giới hạn → backend kiểm; giữ 20 bản trước trong tab; lỗi mạng giữ bản đang xem | Khớp | Dùng lại |
| Hướng dẫn, bằng chứng | `APP_GUIDE.md`, log test, ảnh màn hình | Khớp dạng; nội dung cũ | Viết lại cho bản mới, chạy lại toàn bộ kiểm |

**Kết luận đối chiếu:** bản thử đã phủ phần lớn hành vi M1. Đề xuất **dùng lại có kiểm soát** thay vì viết lại (D1). Phần việc chính của M1 là: tách domain theo cây mới, mở rộng contract (giới hạn tải, trường nhiều tầng, nhãn trạng thái), cập nhật giao diện tương ứng, rồi chạy lại toàn bộ kiểm trên bản mới.

## Quyết định thiết kế đề xuất

Các quyết định dưới đây chờ owner xác nhận cùng SPEC. Chi tiết kỹ thuật thông thường (tên hàm, bố cục file con) do agent quyết trong BUILD.

- **D1 — Dùng lại bản thử.** Sao chép (không di chuyển) source, contract, test, tooling từ archive vào khung thư mục hiện tại; archive giữ nguyên bytes. README của khung được giữ hoặc cập nhật. Phần nào không còn phù hợp thì sửa, không mang theo SPEC/work order cũ.
- **D2 — Ba loại giới hạn tải.** Phương án có nhóm `limits` gồm: `certificate_cargo_limit_g` (theo giấy chứng nhận), `voyage_cargo_limit_g` (theo chuyến, không vượt giới hạn giấy chứng nhận), `cargo_onboard_g` (hàng đã có trên tàu, mặc định 0). Lượng được xếp thêm = giới hạn theo chuyến − hàng đã có. Giới hạn theo chuyến lớn hơn giới hạn giấy chứng nhận, hoặc hàng đã có lớn hơn giới hạn theo chuyến, là dữ liệu sai và bị API từ chối. Không có trường "trọng tải toàn phần". Giá trị M1 đều synthetic.
- **D3 — Trường nhiều tầng dự trữ.** Mỗi vị trí đặt có `z_mm` (mặc định 0), `layer` (mặc định 0) và `supported_by` (danh sách ID, mặc định rỗng). M1 chỉ chấp nhận giá trị mặc định cho kiểm; giá trị khác được trả về với lỗi `LAYER_UNSUPPORTED`, không có logic kê/chồng.
- **D4 — Nhãn trạng thái.** Mỗi kết quả kiểm có một nhãn:
  - `DRAFT`: còn lỗi hình học (vượt biên, va chạm, tầng chưa hỗ trợ);
  - `GEOMETRY_FEASIBLE`: không còn lỗi hình học nhưng còn lỗi quy tắc khác (vượt tải, thiếu hàng required);
  - `RULES_CHECKED`: đạt toàn bộ kiểm trong phạm vi M1; danh sách "chưa kiểm" vẫn hiện;
  - `STALE`: giao diện tự gán khi người dùng đã sửa nhưng chưa bấm kiểm lại.

  Không dùng "SAFE", "đã duyệt" hay tương đương; `operational_eligible` luôn `false`.
- **D5 — Phiên bản contract.** Contract đổi tên thành `scst.m1.v1` vì có trường mới; OpenAPI snapshot và client TS được sinh lại, kiểm khớp.
- **D6 — Không lưu bền.** Lịch sử bản trước chỉ trong tab; refresh mất thay đổi và giao diện nói rõ điều đó. Lưu/mở thuộc M2a.

## Hành vi yêu cầu

**Dữ liệu và contract**

- Hầm BOX: kích thước trong mm, nhãn SYNTHETIC hiện rõ trên giao diện.
- Hàng: từng bó có ID duy nhất, loại (bó thép thanh / bó thép ống), yêu cầu (required / optional / excluded), kích thước mm, khối lượng gram. Không suy khối lượng từ tổng manifest.
- Vị trí đặt: ID bó, x/y/z mm, góc xoay 0/90/180/270°, trường dự trữ theo D3. Mỗi bó đặt tối đa một lần; bó excluded không được đặt.
- Dữ liệu sai cấu trúc (ID trùng hoặc không tồn tại, số không nguyên, trường lạ, giới hạn tải mâu thuẫn) bị API từ chối kèm lý do. Bố trí vượt tải/vượt biên/va chạm **không** bị từ chối mà được trả về kèm lỗi để người dùng sửa.

**Kiểm tra (backend là nguồn kiểm duy nhất)**

- `geometry/`: khối bao sau xoay, nằm trọn trong hầm (toàn khối, không chỉ tâm), va chạm khi giao thể tích dương; chạm mặt không tính va chạm. So sánh số nguyên, không dùng sai số.
- `rules/`: vượt tải theo D2 (chỉ cộng bó đã đặt), thiếu hàng required, phân loại optional chưa đặt (thông tin) và excluded, tầng chưa hỗ trợ theo D3, gán nhãn D4, danh sách "chưa kiểm" (kê/chèn/chằng, nhiều tầng, ổn định, tải cục bộ đáy hầm).
- Kiểm có tính xác định: cùng đầu vào cho cùng kết quả, không sửa dữ liệu đầu vào.

**Giao diện**

- Bảng hàng, mô hình 3D và mặt bằng 2D đọc cùng một kết quả từ API: cùng ID, tọa độ, kích thước, khối lượng; chọn ở một nơi thì nơi khác cùng chọn.
- Tóm tắt: khối lượng toàn manifest, đã xếp, còn được xếp theo D2; số bó đã/chưa xếp; nhãn trạng thái; danh sách lỗi và "chưa kiểm".
- Hàng chưa xếp vẫn hiện trong bảng kèm lý do (optional chưa đặt, excluded).
- Sửa vị trí, khối lượng hoặc giới hạn tải → nhãn chuyển `STALE` → bấm kiểm lại → backend trả kết quả mới. Có nút quay lại bản đã kiểm trước đó. Lỗi mạng không làm mất bản đang xem.
- 3D: chọn bó, xoay, zoom, đặt lại góc nhìn. Không có WebGL thì tự chuyển sang mặt bằng 2D và bảng.
- Giao diện tiếng Việt, ngày dd-mm-yyyy nếu có hiển thị ngày.

**Chạy local**

- Một lệnh/nhấp đôi để khởi chạy trên Windows; lần đầu cài dependency (cần internet), sau đó chạy không cần mạng. Không dùng AI, API key hay dịch vụ ngoài.

## Ngoài phạm vi M1

Nhập tay/import manifest, lưu/mở, so sánh bền, xuất PDF/XLSX (M2); bộ xếp tự động `planner/` (M2b); dữ liệu thật, nhiều tầng, kê/chồng, hình học hầm khác BOX (M3); AI và tích hợp CVF trong app (M4); bộ cài, backup (M5). Không tạo `runtime-data/` trong M1.

## M1 acceptance

| ID | Kết quả cần chứng minh | Bằng chứng dự kiến |
|---|---|---|
| M1-01 | Khởi chạy local bằng một lệnh; UI gọi API thật; AI tắt; chạy không cần mạng sau lần cài đầu | Log launcher, health API, browser smoke |
| M1-02 | Contract `scst.m1.v1`: đơn vị integer mm/gram, ID từng bó, ba loại giới hạn tải (D2), trường nhiều tầng dự trữ (D3); dữ liệu sai cấu trúc bị từ chối; OpenAPI và client TS khớp | Test API/contract, kiểm sinh lại contract không có khác biệt |
| M1-03 | Domain tách `model/`, `geometry/`, `rules/` theo cây; `rules/` không phụ thuộc bộ xếp; kiểm xác định, không sửa đầu vào | Review cấu trúc, test domain |
| M1-04 | Kiểm vượt tải đúng tới 1 gram, vượt biên đúng tới 1 mm, va chạm thể tích dương (chạm mặt hợp lệ), xoay 90°, required/optional/excluded, `LAYER_UNSUPPORTED` | Test domain/API có ca sát biên |
| M1-05 | Nhãn DRAFT / GEOMETRY_FEASIBLE / RULES_CHECKED / STALE đúng ý nghĩa D4; không có nhãn kiểu "SAFE"; `operational_eligible=false`; danh sách "chưa kiểm" luôn hiện | Test API, browser test |
| M1-06 | Bảng, 3D và mặt bằng 2D cùng ID/tọa độ/kích thước/khối lượng từ API; chọn đồng bộ; tóm tắt theo D2; hàng chưa xếp hiện kèm lý do | Browser test đối chiếu với API |
| M1-07 | Sửa vị trí/khối lượng/giới hạn → STALE → kiểm lại → cập nhật; quay lại bản trước; lỗi mạng giữ bản đang xem; thông báo refresh mất thay đổi | Browser test |
| M1-08 | 3D chọn/xoay/zoom/đặt lại; không có WebGL thì dùng được 2D và bảng; nhãn SYNTHETIC hiện rõ | Browser test, ảnh màn hình |
| M1-09 | Hướng dẫn chạy và kiểm, phạm vi chưa có, treeview thật; toàn bộ test chạy lại trên bản M1 mới và lưu log/ảnh; archive không bị sửa | `docs/APP_GUIDE.md`, review M1, so sánh checksum archive |

**Trước khi xin owner phản hồi**, nhóm phát triển tự chứng minh đủ M1-01 đến M1-09 trên đúng phiên bản bàn giao. Owner chỉ cần xem demo và quyết định nghiệp vụ, không phải kiểm kỹ thuật.

## Điểm owner cần xác nhận

1. Dùng lại bản thử theo D1 (đề xuất) hay viết lại từ đầu.
2. Mô hình ba loại giới hạn tải theo D2 có đúng cách đơn vị đang dùng không.
3. Bốn nhãn trạng thái theo D4.

## Bước tiếp theo

Owner thống nhất SPEC → đăng ký mục "M1 acceptance" vào `docs/milestone-coverage-authority.json` → soạn WORK_ORDER M1 (đường dẫn, ngân sách, điều kiện dừng) → BUILD khi được cho phép.
