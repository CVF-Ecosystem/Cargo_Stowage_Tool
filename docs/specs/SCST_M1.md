# SCST M1 — Khung chạy được

Status: DRAFT

**Bản v0.2 · 31-10-2026 · Chờ owner thống nhất.** SPEC này chưa cấp quyền thi công; BUILD chỉ bắt đầu khi có WORK_ORDER riêng. Căn cứ: [roadmap v0.2](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) (dòng M1, nguyên tắc xuyên suốt) và [quyết định SCST-D001](../decisions/SCST_D001_THONG_NHAT_HUONG_M0_2026-10-31.md).

**Thay đổi so với v0.1:**

- làm rõ hầm mục tiêu trống;
- thêm miền giá trị cho các trường tải và các ca kiểm tương ứng;
- thêm cơ chế bản nháp/STALE (D7);
- sửa mô tả phần sinh tự động: chỉ kiểu TS được sinh, request viết tay;
- thêm yêu cầu đối chiếu tọa độ/kích thước 3D với API;
- gắn bảng tái sử dụng nguồn → đích.

Nguồn góp ý:

- [đánh giá tái sử dụng M1](../reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) và phần recheck;
- hai lượt review của owner.

## Mục tiêu M1

Chứng minh **khung và luồng dữ liệu**: chạy local, backend trả hầm/hàng/phương án synthetic, giao diện hiện bảng và 3D cùng một dữ liệu, người dùng sửa một giá trị và backend kiểm lại. M1 không lập phương án tự động, không lưu bền và không dùng dữ liệu thật.

**Người dùng M1:** owner hoặc người được owner giao, xem demo để xác nhận hướng trước M2.

## Đối chiếu bản thử M1 trong archive

Nguồn: [archive/2026-10-31/paused-m1](../../archive/2026-10-31/paused-m1/README.md), Git tree `e4004e274fc28aa143ce0e300b6c060d1cb1e5a0` (50 file). Đã đọc SPEC cũ, hướng dẫn chạy, source domain/API/frontend và test. Kết quả test cũ (27 backend, 3 browser) thuộc bản thử, **không tính là nghiệm thu**.

| Hạng mục | Bản thử đã có | So với M1 mới | Việc cần làm |
|---|---|---|---|
| Khởi chạy local | `Start-SCST.cmd`, một server phục vụ API + frontend đã build, AI tắt | Khớp | Dùng lại; kiểm lại trên bản mới, kể cả chạy không mạng |
| Stack | React/TS + Vite, Three.js; Python 3.11/FastAPI/Pydantic; **kiểu TS** sinh từ OpenAPI (`openapi-typescript`), request gọi API viết tay; có lock file | Khớp roadmap | Dùng lại; lock file là điểm xuất phát, kiểm khi cài |
| Đơn vị, định danh | Integer mm/gram, từng bó có ID/kích thước/khối lượng, từ chối số không nguyên và trường lạ | Khớp nguyên tắc | Dùng lại |
| Nhập liệu frontend | `parseKg` đổi chính xác bằng BigInt nhưng **từ chối 0** | Lệch D2 (hàng đã có có thể bằng 0) | Tách cách nhận 0 cho hàng đã có khỏi khối lượng bó/giới hạn |
| Cấu trúc domain | Ba file phẳng `models.py`, `validation.py`, `demo.py`; hình học và quy tắc trộn trong một hàm | **Lệch** cây mới (`model/`, `geometry/`, `rules/`) | Tách theo cây; không đổi kết quả kiểm |
| Giới hạn tải | Một trường `cargo_limit_g` gắn với hầm | **Thiếu** ba loại giới hạn và miền giá trị | Mở rộng contract (D2) |
| Chừa trường nhiều tầng | Có `z_mm`; `z ≠ 0` bị báo `LAYER_UNSUPPORTED` | **Thiếu** trường lớp và quan hệ đỡ | Thêm trường dự trữ, không thêm logic (D3) |
| Nhãn trạng thái | `basic_checks_passed` + `operational_eligible=false` | **Thiếu** bốn nhãn | Thêm (D4) |
| Sửa và kiểm lại | Form giữ giá trị riêng; chỉ thay phương án khi API thành công; giữ 20 bản trước trong tab; lỗi mạng giữ bản đang xem | Khớp phần bảo toàn dữ liệu; **thiếu** STALE | Thêm bản nháp/STALE (D7) |
| Kiểm cơ bản | Vượt tải (đúng tới 1 gram), vượt biên toàn khối (đúng tới 1 mm), va chạm thể tích dương, xoay 90°, required/optional/excluded | Khớp | Dùng lại, chuyển vào `rules/` + `geometry/` |
| Bảng + 3D + 2D | Cùng ID từ API, chọn đồng bộ, orbit/zoom/reset, mặt bằng 2D khi không có WebGL, lọc/tìm. Test cũ chỉ đối chiếu ID/chữ trong bảng và một tọa độ 2D | Khớp hành vi; **thiếu** bằng chứng đối chiếu tọa độ/kích thước 3D | Dùng lại; thêm hiển thị trạng thái/tải và test đối chiếu 3D |
| Hướng dẫn, bằng chứng | `APP_GUIDE.md`, log test, ảnh màn hình | Nội dung cũ | Viết lại cho bản mới, chạy lại toàn bộ kiểm |

**Kết luận đối chiếu:** bản thử đã có nền cho phần lớn hành vi M1, nhưng chưa được chứng minh trên bản mới; không ước tính phần trăm tiết kiệm. Đề xuất **dùng lại có chọn lọc** theo [Phụ lục](#phụ-lục--nguồn--đích-khi-dùng-lại) thay vì viết lại (D1).

## Quyết định thiết kế đề xuất

Các quyết định dưới đây chờ owner xác nhận cùng SPEC. Chi tiết kỹ thuật thông thường (tên hàm, bố cục file con) do agent quyết trong BUILD.

- **D1 — Dùng lại có chọn lọc.** Sao chép (không di chuyển) từng thành phần từ archive vào khung hiện tại theo Phụ lục. Archive giữ nguyên bytes. Không mang `.venv`, cache, log, PID, SPEC/work order hay authority cũ. Archive không được nạp lúc chạy.
- **D2 — Giới hạn tải và hầm mục tiêu trống.**
  - Phương án có nhóm `limits` gồm `certificate_cargo_limit_g` (theo giấy chứng nhận), `voyage_cargo_limit_g` (theo chuyến) và `cargo_onboard_g` (hàng đã có trên tàu).
  - **Miền giá trị:** cả ba là số nguyên (không nhận số thập phân, chuỗi hay boolean). Hai giới hạn phải lớn hơn 0; `cargo_onboard_g` lớn hơn hoặc bằng 0, mặc định 0. Cả ba không vượt trần chung **1.000.000.000.000 g** (giống trần khối lượng mỗi bó). Frontend và backend dùng cùng quy định.
  - **Quan hệ:** `voyage_cargo_limit_g` ≤ `certificate_cargo_limit_g` và `cargo_onboard_g` ≤ `voyage_cargo_limit_g`.
  - **Lượng được xếp thêm** = `voyage_cargo_limit_g` − `cargo_onboard_g`. Theo miền trên, lượng này không bao giờ âm và không bao giờ lớn hơn giới hạn theo chuyến.
  - **Vi phạm miền hoặc quan hệ** là dữ liệu sai và bị API từ chối. Ví dụ hàng đã có là số âm bị từ chối, không làm tăng lượng được xếp.
  - Không có trường "trọng tải toàn phần".
  - **Hầm mục tiêu trống:** M1 luôn lập bố trí trong hầm mục tiêu đang trống. `cargo_onboard_g` là hàng nằm **ngoài** hầm mục tiêu và chỉ dùng để trừ khối lượng; nó không chiếm chỗ trong hầm mục tiêu. Trường hợp hàng cũ nằm ngay trong hầm mục tiêu thì M1 chưa hỗ trợ (cần mô hình hóa chỗ hàng cũ chiếm, thuộc M3).
  - Mọi giá trị M1 đều synthetic.
- **D3 — Trường nhiều tầng dự trữ.** Mỗi vị trí đặt có `z_mm` (mặc định 0), `layer` (số nguyên ≥ 0, mặc định 0) và `supported_by` (danh sách ID, mặc định rỗng). M1 chỉ chấp nhận giá trị mặc định cho kiểm. Giá trị khác được trả về với lỗi `LAYER_UNSUPPORTED`, mỗi trường có ca kiểm riêng. Không có logic kê/chồng.
- **D4 — Nhãn trạng thái của kết quả kiểm.** Ưu tiên từ trên xuống khi có nhiều lỗi:
  - `DRAFT`: còn ít nhất một lỗi hình học (vượt biên, va chạm, tầng chưa hỗ trợ);
  - `GEOMETRY_FEASIBLE`: không còn lỗi hình học nhưng còn lỗi quy tắc khác (vượt tải, thiếu hàng required);
  - `RULES_CHECKED`: đạt toàn bộ kiểm trong phạm vi M1; danh sách "chưa kiểm" vẫn hiện.

  Không dùng "SAFE", "đã duyệt" hay tương đương; `operational_eligible` luôn `false`.
- **D5 — Phiên bản contract.** Contract đổi thành `scst.m1.v1`. OpenAPI snapshot sinh từ backend mới vào `contracts/`. Kiểu TS sinh lại từ snapshot vào `apps/frontend/src/api/generated/`. Lời gọi API viết tay kiểm phiên bản contract. Sinh lại lần hai không được tạo khác biệt.
- **D6 — Không lưu bền.** Lịch sử bản trước chỉ trong tab; refresh mất thay đổi và giao diện nói rõ điều đó. Lưu/mở thuộc M2a.
- **D7 — Bản nháp và STALE.**
  - Giao diện tách **bản đã kiểm** (kết quả backend gần nhất) với **bản nháp** (đang sửa).
  - Ngay khi bản nháp khác bản đã kiểm, giao diện hiện `STALE`: kết quả đang thấy là của bản trước, chưa kiểm cho thay đổi.
  - `STALE` chỉ hết khi backend trả kết quả cho đúng bản nháp đó.
  - API từ chối dữ liệu sai hoặc lỗi mạng: giữ bản đã kiểm, giữ bản nháp để người dùng sửa tiếp, báo rõ bản nháp chưa được kiểm.
  - `STALE` là trạng thái giao diện, không do backend trả về.

## Hành vi yêu cầu

**Dữ liệu và contract**

- Hầm BOX, kích thước mm, nhãn SYNTHETIC hiện rõ.
- Hàng: từng bó có các thông tin sau. Không suy khối lượng từ tổng manifest.
  - ID duy nhất;
  - loại: bó thép thanh hoặc bó thép ống;
  - yêu cầu: required, optional hoặc excluded;
  - kích thước mm;
  - khối lượng gram, số nguyên lớn hơn 0 và không vượt trần.
- Vị trí đặt: ID bó, x/y/z mm, góc xoay 0/90/180/270°, các trường dự trữ theo D3. Mỗi bó đặt tối đa một lần; bó excluded không được đặt.
- Giới hạn tải theo D2.
- **API từ chối kèm lý do** khi dữ liệu sai cấu trúc:
  - ID trùng hoặc không tồn tại;
  - số không nguyên;
  - trường lạ;
  - giá trị ngoài miền;
  - vi phạm quan hệ giới hạn.
- **API trả về kèm lỗi để sửa, không từ chối:** bố trí vượt tải, vượt biên hoặc va chạm.
- Tổng số nguyên luôn an toàn ở frontend: tối đa 200 bó × trần mỗi bó, nhỏ hơn giới hạn số nguyên an toàn của JavaScript.

**Kiểm tra (backend là nguồn kiểm duy nhất)**

- `geometry/`:
  - khối bao sau khi xoay;
  - nằm trọn trong hầm, kiểm toàn khối chứ không chỉ tâm;
  - va chạm khi giao nhau có thể tích dương; chạm mặt không tính là va chạm;
  - so sánh bằng số nguyên, không dùng sai số.
- `rules/`:
  - vượt tải so với lượng được xếp thêm theo D2, chỉ cộng các bó đã đặt;
  - thiếu hàng required;
  - phân loại optional chưa đặt (chỉ để thông tin) và excluded;
  - tầng chưa hỗ trợ theo D3;
  - gán nhãn theo D4;
  - danh sách "chưa kiểm": kê/chèn/chằng, nhiều tầng, ổn định, tải cục bộ đáy hầm, hàng cũ trong hầm mục tiêu.
- `rules/` không phụ thuộc bộ xếp. Kiểm có tính xác định: cùng đầu vào cho cùng kết quả, không sửa dữ liệu đầu vào.

**Giao diện**

- Bảng hàng, mô hình 3D và mặt bằng 2D đọc cùng một kết quả từ API: cùng ID, tọa độ, kích thước, khối lượng. Chọn bó ở một nơi thì nơi khác cũng chọn theo. Phép chiếu kích thước sau xoay ở frontend chỉ để hiển thị, không thay bộ kiểm backend.
- Tóm tắt gồm:
  - khối lượng toàn manifest, đã xếp, lượng được xếp thêm theo D2;
  - ba giá trị giới hạn;
  - số bó đã xếp và chưa xếp;
  - nhãn trạng thái, hoặc `STALE` theo D7;
  - danh sách lỗi và "chưa kiểm".
- Hàng chưa xếp vẫn hiện trong bảng kèm lý do (optional chưa đặt, excluded).
- Sửa vị trí, khối lượng hoặc giới hạn tải rồi kiểm lại, theo D7. Có nút quay lại bản đã kiểm trước đó.
- 3D: chọn bó, xoay, zoom, đặt lại góc nhìn. Không có WebGL thì tự chuyển sang mặt bằng 2D và bảng.
- Giao diện tiếng Việt, ngày dd-mm-yyyy nếu có hiển thị ngày.

**Chạy local**

- Một lệnh/nhấp đôi để khởi chạy trên Windows. Lần đầu cài dependency (cần internet); sau đó chạy không cần mạng. Không dùng AI, API key hay dịch vụ ngoài.

## Ngoài phạm vi M1

- **M2:** nhập tay/import manifest, lưu/mở, so sánh bền, xuất PDF/XLSX; bộ xếp tự động `planner/` (M2b).
- **M3:** dữ liệu thật, nhiều tầng, kê/chồng, hàng cũ trong hầm mục tiêu, hình học hầm khác BOX.
- **M4:** AI và tích hợp CVF trong app.
- **M5:** bộ cài, backup.
- Không tạo `runtime-data/` trong M1.

## M1 acceptance

| ID | Kết quả cần chứng minh | Bằng chứng dự kiến |
|---|---|---|
| M1-01 | Khởi chạy local bằng một lệnh; UI gọi API thật; AI tắt; chạy không cần mạng sau lần cài đầu | Log launcher, health API, browser smoke có ngắt mạng |
| M1-02 | Contract `scst.m1.v1`: integer mm/gram, ID từng bó, ba giới hạn tải với miền và quan hệ theo D2, trường dự trữ D3; dữ liệu sai bị từ chối, gồm số âm, số 0 (mỗi trường), số không nguyên, vượt trần, vi phạm từng quan hệ, `cargo_onboard_g` âm; `cargo_onboard_g = 0` được nhận; OpenAPI và kiểu TS sinh lại không có khác biệt | Test API/contract theo từng ca; kiểm sinh lại contract |
| M1-03 | Domain tách `model/`, `geometry/`, `rules/` theo cây; `rules/` không phụ thuộc bộ xếp; kiểm xác định, không sửa đầu vào | Review cấu trúc, test domain |
| M1-04 | Vượt tải đúng tới 1 gram so với lượng được xếp thêm (có ca `cargo_onboard_g` > 0), vượt biên đúng tới 1 mm, va chạm thể tích dương (chạm mặt hợp lệ), xoay 90°, required/optional/excluded, `LAYER_UNSUPPORTED` riêng cho `z_mm`, `layer`, `supported_by` | Test domain/API có ca sát biên |
| M1-05 | Nhãn DRAFT / GEOMETRY_FEASIBLE / RULES_CHECKED đúng định nghĩa và thứ tự ưu tiên D4 khi có nhiều lỗi; không có nhãn kiểu "SAFE"; `operational_eligible=false`; danh sách "chưa kiểm" luôn hiện | Test API |
| M1-06 | Bảng, 3D và mặt bằng 2D cùng ID/tọa độ/kích thước/khối lượng từ API, gồm đối chiếu vị trí và kích thước mesh 3D (sau xoay) với API; chọn đồng bộ; tóm tắt theo D2; hàng chưa xếp hiện kèm lý do | Browser test đối chiếu dữ liệu render với phản hồi API |
| M1-07 | D7: sửa → `STALE` ngay → kiểm lại → hết `STALE` chỉ khi kết quả khớp bản nháp; API từ chối và lỗi mạng giữ bản đã kiểm, giữ bản nháp, báo chưa kiểm; quay lại bản trước; thông báo refresh mất thay đổi | Browser test |
| M1-08 | 3D chọn/xoay/zoom/đặt lại; không có WebGL thì dùng được 2D và bảng; nhãn SYNTHETIC hiện rõ | Browser test, ảnh màn hình (ảnh không thay cho đối chiếu dữ liệu) |
| M1-09 | Hướng dẫn chạy và kiểm, phạm vi chưa có, treeview thật; toàn bộ test chạy lại trên bản M1 mới và lưu log/ảnh; archive không bị sửa | `docs/APP_GUIDE.md`, review M1, so sánh tree archive |

**Trước khi xin owner phản hồi**, nhóm phát triển tự chứng minh đủ M1-01 đến M1-09 trên đúng phiên bản bàn giao. Owner chỉ cần xem demo và quyết định nghiệp vụ, không phải kiểm kỹ thuật.

## Điểm owner cần xác nhận

1. **Dùng lại có chọn lọc theo D1 và Phụ lục.** Bản đánh giá tái sử dụng ghi owner đã chọn hướng này; nếu đúng, chỉ cần xác nhận danh mục.
2. **Ba loại giới hạn tải và miền giá trị theo D2.** Có đúng cách đơn vị đang dùng không?
3. **Hầm mục tiêu trống.** Hàng đã có trên tàu được coi là nằm ngoài hầm mục tiêu.
4. **Ba nhãn trạng thái theo D4 và STALE theo D7.**

## Bước tiếp theo

1. Owner thống nhất SPEC.
2. Đăng ký mục "M1 acceptance" vào `docs/milestone-coverage-authority.json`.
3. Soạn WORK_ORDER M1, ghim nguồn archive bằng tree ở trên và nêu đường dẫn, ngân sách, điều kiện dừng.
4. BUILD khi được cho phép, theo thứ tự: backend + contract trước, rồi frontend, launcher và bằng chứng.

## Phụ lục — nguồn → đích khi dùng lại

Nguồn tính từ `archive/2026-10-31/paused-m1/`; đích tính từ root project. Chi tiết và lý do ở [bản đánh giá tái sử dụng](../reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) mục 3. Đã recheck với source.

| Nguồn | Xử lý | Đích |
|---|---|---|
| `services/backend/app/domain/models.py` | Sửa: giữ strict model, thêm `limits`, D3, D4, đổi version | `services/backend/app/domain/model/` |
| `validation.py`: footprint, containment, overlap | Giữ thuật toán | `services/backend/app/domain/geometry/` |
| `validation.py`: evaluate, tải, phân loại, summary | Sửa theo D2–D4 | `services/backend/app/domain/rules/` |
| `domain/demo.py` | Sửa fixture: giữ 13 bó/12 vị trí, thêm `limits` | `services/backend/app/demo.py` (dữ liệu, không phải domain) |
| `api/routes.py`, `main.py` | Sửa wiring, giữ health/demo/validate và phục vụ frontend | `services/backend/app/` |
| `apps/frontend/src/Viewer.tsx` | Giữ cơ chế render, sửa import | `apps/frontend/src/viewer-3d/` |
| `apps/frontend/src/App.tsx` | Tách bảng/editor/lịch sử vào features, thêm D2/D4/D7 | `apps/frontend/src/features/` + `App.tsx` |
| `model.ts`: định dạng, `parseKg`, `parseMm` | Giữ có sửa: cho phép 0 với hàng đã có | Helper trong features |
| `model.ts`: `requestEvaluation` | Sửa version contract, giữ timeout/xử lý lỗi | `apps/frontend/src/api/` |
| `styles.css`, `index.html`, `main.tsx`, cấu hình Vite/TS, `package*.json` | Giữ làm nền; kiểm lại override `minimatch` khi cài | `apps/frontend/` |
| `requirements*.txt`, `pytest.ini` | Giữ làm ứng viên, kiểm khi cài | Vị trí tương ứng |
| `contracts/openapi.json`, `src/generated/api.ts` | Sinh lại; bản cũ chỉ để so sánh | `contracts/`, `apps/frontend/src/api/generated/` |
| `tooling/*`, `Start-SCST.cmd` | Giữ/sửa đường dẫn; kiểm chạy lần đầu và không mạng | `tooling/`, root |
| `tests/backend/`, `tests/browser/`, `playwright.config.ts` | Giữ kịch bản, sửa payload; thêm ca D2/D3/D7 và đối chiếu 3D | `tests/backend/`, `tests/browser/` |
| `docs/APP_GUIDE.md` | Viết lại | `docs/APP_GUIDE.md` |
| README/SPEC/work order/authority cũ, evidence, `runtime-data/` | Để lại archive | — |
