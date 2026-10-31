# SCST M1 — Đánh giá và đề xuất tái sử dụng có chọn lọc

Status: ADMITTED_FOR_M1

**Ngày:** 31-10-2026. **Người lập ban đầu:** Codex, agent đã dựng bản thử M1; đánh giá ban đầu là tự đánh giá. **Người nhận:** owner SCST và Claude. Claude đã recheck và đưa kết quả vào SPEC v0.2 tại `0f307b6`; Codex tiếp quản, xác minh và hoàn tất bàn giao ở mục 9. SPEC và danh mục vẫn chờ owner thống nhất.

## 1. Kết luận đề xuất

**Tái sử dụng nền tảng M1 cũ theo từng thành phần**, giữ các phép tính/luồng hiển thị phù hợp, sửa phần phụ thuộc contract và tổ chức lại theo kiến trúc mới. Phần thiếu tập trung ở mô hình tải, trạng thái phương án, cấu trúc module và bằng chứng nghiệm thu mới. Không có căn cứ để ước tính phần trăm tiết kiệm hoặc khẳng định source có thể chạy nguyên trạng sau khi chuyển.

Chỉ đạo mới của owner đã chọn hướng tận dụng có chọn lọc. Câu hỏi còn lại là **chọn những phần nào và sửa ra sao**; không cần hỏi lại owner có muốn tái sử dụng hay viết lại toàn bộ. Mục 2–8 giữ căn cứ/lượt đánh giá ban đầu; mục 9 ghi kết quả recheck và phần hoàn tất sau đó. Chưa chuyển source, cài dependency hoặc chạy demo.

## 2. Căn cứ và giới hạn đánh giá

- Nguồn cũ: [paused-m1](../../archive/2026-10-31/paused-m1/README.md), 50 file, tại commit `819565330fbac6476157cfe40c338cef4a96a5de`; Git tree của toàn thư mục: `e4004e274fc28aa143ce0e300b6c060d1cb1e5a0`.
- Hướng đích: [roadmap v0.2](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md), SHA-256 chuẩn hóa LF: `ba0d594e6f76707304f810451c52cacf6bec6fc8e5cec01761a11f9ae7da8ff1`.
- Yêu cầu đích: [SPEC M1 v0.1 — DRAFT](../specs/SCST_M1.md), Git blob `39db70103f3a4818e1997420a125b26b6102e3df`; SHA-256 chuẩn hóa LF: `8ebd0796677251e0ac9a49fef11f048b07e81e33301db42b0c99f4b36efb4cba`.
- Đã đọc source domain/API, model/client frontend, workspace/editor, viewer 3D/2D, test backend/browser, launcher/setup/generator, cấu hình build và hướng dẫn cũ. CSS được rà phần nền/bố cục/responsive và phụ thuộc ngoài; package-lock được đối chiếu metadata. Không coi đây là audit đầy đủ dependency hoặc kiểm tra hình ảnh/runtime mới.
- Kiểm tra tĩnh: parse AST 11 file Python thành công, không import/chạy chúng. Lock NPM v3 khớp dependency trực tiếp trong package.json. Log cũ ghi 27 backend/3 browser test đạt; chưa chạy lại và không dùng kết quả ấy để đánh dấu M1 mới VERIFIED.

**Phạm vi kết luận:** độ phù hợp để tái sử dụng theo source đang có. Chưa xác nhận khả năng cài lại lock, hiển thị trên máy mới, chạy offline hoặc đáp ứng acceptance mới. Nếu Claude sửa roadmap/SPEC/source sau commit trên, cần đối chiếu lại phần thay đổi trước khi dùng đề xuất.

## 3. Danh mục lấy gì và đưa vào đâu

Mọi đường dẫn ở cột **Nguồn** tính từ `archive/2026-10-31/paused-m1/`. Đường dẫn **Đích** tính từ root project; đây là đề xuất cho WORK_ORDER sau này, chưa tạo file app. Nhóm **GIỮ** cũng cần sửa import nếu đổi vị trí và kiểm lại.

| Nguồn | Xử lý đề xuất | Đích / điều kiện |
|---|---|---|
| `domain/models.py` dưới `services/backend/app/` | **SỬA**: giữ StrictInt, extra=forbid, ID, kích thước, mass, yaw và kiểm định danh; thay giới hạn tải, version; thêm trường dự trữ và trạng thái | `services/backend/app/domain/model/`; giữ giới hạn số lượng/giá trị để tổng integer an toàn ở frontend; cargo_onboard phải nhận được 0 |
| `domain/validation.py`: `footprint`, khối bao, containment, overlap | **GIỮ thuật toán**, tách khỏi điều phối quy tắc | `services/backend/app/domain/geometry/`; toàn khối trong BOX, giao thể tích dương, chạm mặt hợp lệ; chưa mở hình học hoặc nhiều tầng mới |
| `domain/validation.py`: `evaluate`, tải, required/optional/excluded, summary/unchecked | **SỬA**: giữ cách đối soát unit; thay công thức tải, thêm layer/support và nhãn trạng thái theo SPEC | `services/backend/app/domain/rules/`; gọi geometry, không phụ thuộc planner; giữ hàm xác định và không sửa đầu vào |
| `domain/demo.py` | **SỬA fixture**: giữ bộ 13 bó/12 placement làm mẫu chuẩn; thêm limits và giá trị dự trữ đúng contract mới | Đề xuất `services/backend/app/demo.py` để fixture synthetic tách logic domain; fixture không phải thuật toán xếp |
| `api/routes.py`, `main.py`, các `__init__.py` rỗng | **SỬA wiring**: giữ health/demo/validate và phục vụ frontend cùng server; sửa import/metadata, kiểm lại đường dẫn static | Giữ trong `services/backend/app/`; không nạp module từ archive lúc chạy |
| `apps/frontend/src/Viewer.tsx` | **GIỮ phần lớn cơ chế render**: Three.js, orbit/reset/picking, SVG, bàn phím, WebGL fallback và cleanup; sửa import theo cây mới | `apps/frontend/src/viewer-3d/`; kiểm phép chiếu mm→m, x/y/z và yaw; không đưa kiểm nghiệp vụ vào viewer |
| `apps/frontend/src/App.tsx`: bảng, editor, chọn đồng bộ, issue list, lịch sử, lỗi mạng | **SỬA/TÁCH**: giữ hành vi hữu ích; đưa workspace/editor/bảng vào features, App chỉ lắp ghép | `apps/frontend/src/features/` + `App.tsx`; bổ sung STALE/draft, ba trường tải, nhãn SYNTHETIC và kết quả chưa kiểm; không mở nhập manifest mới |
| `apps/frontend/src/model.ts`: fmt, tonnes, kgInput, parseKg, parseMm | **GIỮ có sửa**: giữ đổi đơn vị chính xác bằng chuỗi/BigInt; tách khỏi fetch và type import | Helper trong feature hoặc file tiện ích nhỏ đang thực sự dùng; tách cách nhận onboard=0 khỏi mass bó/giới hạn phải dương; không làm tròn |
| `apps/frontend/src/model.ts`: `requestEvaluation` | **SỬA**: giữ fetch/timeout/xử lý lỗi và bảo vệ version; đổi `scst.demo.v1` sang contract mới | `apps/frontend/src/api/`; mã cũ sinh **kiểu dữ liệu**, còn request viết tay, chưa phải client thao tác được sinh tự động |
| `src/styles.css`, `index.html`, `src/main.tsx` | **GIỮ làm nền**; chỉ chỉnh cho module/nhãn mới và wiring | `apps/frontend/`; giữ HTML tiếng Việt/responsive; chưa thiết kế lại UI hoặc chuyển sang R3F chỉ vì roadmap liệt kê lựa chọn đó |
| `package.json`, `package-lock.json`, `tsconfig.json`, `vite.config.ts` | **GIỮ ứng viên cấu hình**; sửa lệnh/path sinh contract, xác minh tương thích khi thi công | `apps/frontend/`; không tự nâng hàng loạt version; override minimatch cũ cần kiểm lại lý do/tương thích, chưa khẳng định còn cần hay đã đủ |
| `services/backend/requirements.txt`, `requirements-dev.txt`, `requirements-lock.txt` | **GIỮ ứng viên dependency**; đối chiếu runtime/dev/transitive khi cài lại | Cùng vị trí tương ứng; lock cũ là điểm xuất phát, không là bằng chứng cài được hiện tại. Không mang theo `.venv`/cache máy cũ |
| `contracts/openapi.json`, `src/generated/api.ts` | **SINH LẠI**, chỉ dùng bản cũ để so sánh thay đổi | OpenAPI vào `contracts/`; kiểu TS đề xuất vào `apps/frontend/src/api/generated/`; cập nhật mọi import và lệnh generator cho cùng vị trí |
| `tooling/export_contract.py` | **SỬA rồi dùng lại**: giữ cách xuất schema từ API mới | `tooling/`; snapshot phải sinh từ backend mới, không dùng backend archive để phát sinh contract cho app mới |
| `Start-SCST.cmd`, `tooling/setup.ps1`, `start-local.ps1`, `run_local.py` | **GIỮ/SỬA cần thiết**: local loopback, dựng dependency/build, chờ API rồi mở trình duyệt | Cùng vị trí; kiểm cold start và chạy offline sau setup; hiện start-local chỉ kiểm venv/dist tồn tại nên hướng dẫn phải nói rõ build lại sau khi sửa source |
| `tests/backend/test_validation.py`, `pytest.ini` | **GIỮ kịch bản, SỬA payload/assert/import**; thêm test contract mới | `tests/backend/`; các con số oracle cũ chỉ giữ nếu fixture mới giữ đúng mass/placement; không sửa kỳ vọng để hợp thức hóa sai lệch |
| `tests/browser/workspace.spec.ts`, `playwright.config.ts` | **GIỮ kịch bản, SỬA/BỔ SUNG**: cùng API thật, lỗi mạng, fallback, undo; sửa nhãn/limits/status/đường dẫn evidence | `tests/browser/` và config frontend; kiểm port/build của bản mới; không coi so ảnh pixel tuyệt đối giữa các máy là oracle duy nhất |
| `docs/APP_GUIDE.md` cũ | **VIẾT LẠI nội dung hiện hành**, dùng cách chạy/thao tác cũ làm tham khảo | `docs/APP_GUIDE.md`; cây thật, contract, ba giới hạn tải, trạng thái và phần chưa có của bản bàn giao |
| README, SPEC/work order/authority cũ trong bộ archive | **ĐỂ LẠI ARCHIVE** | Không ghi đè hồ sơ mới, không sao chép quyền thi công, không thay root README bằng README cũ |
| `docs/reviews/SCST_M1_EVIDENCE/**`, `runtime-data/**` | **ĐỂ LẠI ARCHIVE**: log/ảnh/XML/PID là lịch sử | Chạy và tạo evidence mới sau thi công; không khôi phục PID/log/server, không tạo runtime-data trong M1 |

Giữ README trách nhiệm của khung hiện tại, cập nhật khi source mới thực sự nằm đúng chỗ. Không chép đè cả thư mục `apps`, `services`, `docs` hoặc cấu hình Git/CVF. Không khôi phục dependency/build cache đang được giữ ở `.cvf/runtime/paused-m1-local/` vào cây app.

## 4. Khoảng thiếu thấy trực tiếp trong source

1. **Contract tải và parser phải sửa cùng nhau.** [Models cũ](../../archive/2026-10-31/paused-m1/services/backend/app/domain/models.py) chỉ có `hold.cargo_limit_g`; [parseKg cũ](../../archive/2026-10-31/paused-m1/apps/frontend/src/model.ts) từ chối 0. Sao chép nguyên sẽ không đáp ứng D2 với onboard mặc định 0. Đề xuất giới hạn chứng nhận/chuyến dương, onboard không âm, strict integer, ràng buộc thứ tự và trần số an toàn nhất quán FE/BE. Phần này cần bổ sung vào SPEC trước khi giao việc.
2. **Phải chốt ngữ nghĩa hầm trống.** Đề xuất M1 luôn lập bố trí từ hầm mục tiêu trống; cargo_onboard nếu khác 0 là khối lượng ở ngoài hầm mục tiêu. Hàng cũ trong chính hầm đó chưa được mô hình hóa; không lấy một số gram thay occupied geometry. Đây là đề xuất làm rõ D2, chưa phải quyết định nghiệp vụ được tự nhận là đã duyệt.
3. **STALE là phần mới.** [Editor/App cũ](../../archive/2026-10-31/paused-m1/apps/frontend/src/App.tsx) giữ giá trị form riêng, chỉ thay phương án sau API thành công; status dựa vào boolean, chưa đánh dấu ngay khi nhập. Đề xuất giữ bản đã kiểm riêng với draft chỉnh sửa; đánh dấu STALE ngay khi thay đổi, hết STALE chỉ sau khi kết quả kiểm khớp draft đó. API từ chối/lỗi mạng vẫn giữ bản đã kiểm và thông báo draft chưa kiểm; không phủ nhận ưu điểm bảo toàn dữ liệu cũ.
4. **Layer/support chưa có.** Chỉ có z trong source cũ; thêm layer/support theo D3 và báo LAYER_UNSUPPORTED khi khác mặc định. Cần ca thử riêng cho từng trường. Không xây quan hệ đỡ, tính tải tầng hoặc solver trong M1.
5. **Độ phủ test giao diện còn thiếu.** [Ba browser test cũ](../../archive/2026-10-31/paused-m1/tests/browser/workspace.spec.ts) đã kiểm ID bảng, một tọa độ SVG, picking/orbit/reset và fallback; chưa đối chiếu đầy đủ tọa độ/kích thước 3D với API, chưa kiểm STALE/ba loại tải hoặc layer/support. Khi thi công cần kiểm phép chiếu vào mesh và luồng lựa chọn thực; screenshot/ảnh canvas thay đổi không tự chứng minh đúng hình học. Hàm footprint ở frontend được giữ làm phép chiếu hiển thị, không trở thành bộ kiểm thay backend.

Các nhận định trên dựa vào source, không là lỗi runtime đã tái hiện trong lượt này. `RULES_CHECKED` làm theo định nghĩa D4 của SPEC đang chờ chốt; không tự đổi semantics sang phê duyệt hoặc an toàn vận hành.

## 5. Ánh xạ sang toàn bộ acceptance M1

**Trạng thái chung:** M1 mới chưa triển khai (NOT_STARTED); từng phần cũ chỉ là ứng viên tái sử dụng, chưa VERIFIED cho phiên bản mới. Local-development chịu trách nhiệm các khoảng thiếu dưới đây, đích xử lý là WORK_ORDER M1 sau khi SPEC được thống nhất. Bảng này đối chiếu SPEC draft, không đăng ký tiêu chí đã duyệt hoặc cấp quyền dispatch.

| ID | Phần cũ tận dụng | Khoảng còn phải làm/chứng minh |
|---|---|---|
| M1-01 | Launcher, API/static frontend, health | Cài/build trên cây mới; một lệnh cold start; chạy lại khi ngắt mạng sau setup; không gọi dịch vụ ngoài |
| M1-02 | Strict model, ID, integer, version check, generator | D2/D3/D5 và miền số; lỗi cấu trúc; snapshot/client sinh lại, không diff khi tái sinh |
| M1-03 | Phép tính và evaluate thuần; test deterministic/non-mutation | Tách model/geometry/rules, sửa imports; kiểm độc lập planner, không thay oracle hình học |
| M1-04 | Các ca tải 1g, biên 1mm, overlap/chạm mặt, yaw, required/excluded | Payload tải mới; ca layer/support không mặc định; kiểm miền số/giới hạn; giữ cả ca hợp lệ và không hợp lệ |
| M1-05 | operational_eligible=false, unchecked, issue list | Toàn bộ phân loại DRAFT/GEOMETRY_FEASIBLE/RULES_CHECKED và STALE frontend theo D4; kiểm ưu tiên trạng thái khi có nhiều lỗi |
| M1-06 | Bảng/viewer dùng cùng result; lựa chọn đồng bộ | Ba giới hạn/tổng hợp đúng D2; đối chiếu ID/tọa độ/kích thước/mass, phép chiếu 3D/2D, lý do mọi unit chưa xếp/loại trừ |
| M1-07 | Undo theo phiên, giữ bản khi API lỗi, khóa request | Draft/STALE; lỗi cấu trúc, lỗi mạng và retry; undo không mất bản đã kiểm; cảnh báo refresh rõ |
| M1-08 | Orbit/zoom/reset, SVG/bàn phím, WebGL fallback | Chạy lại lựa chọn/camera/fallback trên bản mới; thêm nhãn SYNTHETIC rõ; ảnh mới theo đúng build |
| M1-09 | Cấu trúc hướng dẫn và bộ test cũ | Hướng dẫn/cây mới; log/ảnh mới, bộ test đã chuyển chạy lại; đối chiếu archive không đổi bytes |

Không mở planner, import manifest, lưu bền, export, dữ liệu thật hoặc nhiều tầng để lấp khoảng thiếu M1. Các phần đó tiếp tục theo M2–M5 trong roadmap.

## 6. Trình tự chuyển có chọn lọc sau khi được phép

1. **Chốt trước khi copy:** recheck đã hoàn tất và SPEC v0.2 đã tiếp nhận các điểm cần sửa (xem mục 9). Owner thống nhất danh mục nguồn/đích và SPEC; sau đó đăng ký acceptance đã thống nhất và lập WORK_ORDER có phạm vi rõ. Giữ nguồn archive bất biến.
2. **Chuyển backend + contract trước:** model/geometry/rules, fixture và API; chuyển các ca test tương ứng, kiểm oracle; sinh OpenAPI/types mới. Frontend chỉ nối sau khi contract mới nhất quán. Đây là thứ tự công việc trong M1, không tự tạo thêm mốc hay giấy phép.
3. **Chuyển UI + launcher + kiểm bàn giao:** viewer/feature/client/helper, trạng thái và tải mới; kiểm tích hợp, contract, browser, local/offline; viết hướng dẫn và evidence mới. Chỉ báo M1 đạt khi đủ M1-01…09; owner xem giá trị/nghiệp vụ sau khi development tự kiểm đủ.

WORK_ORDER nên ràng buộc nguồn bằng commit/tree nêu trên; mỗi nhóm chuyển ghi nguồn → đích → phần sửa → test chứng minh. Phần sinh tự động có lệnh tái tạo; phần giữ archive không xuất hiện trong source runtime hoặc authority hiện hành.

## 7. Checklist đã giao Claude recheck

Các mục dưới đây là yêu cầu của lượt ban đầu; kết quả hiện hành nằm ở mục 9.

- Kiểm lại bảng chọn lọc với source thật: có nhóm nào bị chọn nhầm/bỏ sót, đích có đúng cây đã thống nhất, hay có lý do tốt hơn để thay một thành phần. Chỉ đề nghị viết lại phần có khoảng thiếu cụ thể.
- Đối chiếu từng M1-01…09 với phần tái sử dụng và bằng chứng mới cần thêm; phản hồi theo mục **đồng ý / cần sửa / chưa đủ bằng chứng**, kèm file/đoạn nguồn và đề xuất sửa.
- Kiểm ba điểm cần chốt trong SPEC: giới hạn số, hầm mục tiêu trống/onboard, cơ chế draft/STALE khi kiểm thất bại; không kéo M2/M3 vào M1.
- Xác minh dependency/lock là ứng viên, generated API phải sinh lại và cache/log/PID/authority cũ không được phục hồi; không đổi stack chỉ để tổ chức lại code.
- Hồ sơ cũ có vấn đề riêng: gate trực tiếp cho `docs/work_orders/SCST_M1_SKELETON.md` đã lỗi `COV_AUTHORITY_STALE` vì roadmap đổi. Cần cách giữ nguồn tiêu chí tại revision dispatch phù hợp validator; không thay hash để tự nhận lại bằng chứng cũ, không sửa/bypass gate. Việc này không phải lý do mở thêm chức năng app.
- Trả kết luận về **đề xuất tái sử dụng**, không tự coi recheck là owner nghiệm thu SPEC, quyền thi công hoặc M1 đã đạt. Sau recheck, owner chốt lựa chọn/phạm vi trước BUILD.

## 8. Phạm vi lượt đánh giá và trạng thái bàn giao

Ủy quyền hiện tại: đánh giá source cũ và viết đề xuất cho Claude; R1 tài liệu, phase SPEC, không có app work order đang hoạt động. Câu hỏi hữu hạn: thành phần nào phù hợp roadmap/SPEC mới và thiếu gì để tái sử dụng. Đầu ra: báo cáo này và liên kết/trạng thái tiếp tục. Agent chịu trách nhiệm; trần bổ sung 45 phút gồm đọc/ghi/kiểm tài liệu; dừng tại báo cáo và kiểm hoặc hết trần, không tự mở nghiên cứu/thi công tiếp. Tận dụng các lần review trước; chi phí trước đó không đo, không suy diễn thời lượng chạy lại app.

Ở lượt ban đầu, đã kiểm tĩnh source như mục 2; doctor đạt 28/28 trước khi viết. Các kiểm tra được ghi ở handoff. Kết luận khi đó là chờ Claude recheck và owner chốt. Kết quả hiện hành cập nhật ở mục 9; không tuyên bố live AI governance, test runtime mới hoặc acceptance M1 mới.

## 9. Kết quả recheck và tiếp quản

**Nguồn tiếp quản:** hai commit Claude `0f307b6` (SPEC v0.2 + snapshot repair) và `6beeea4` (session memory). Worktree sạch khi tiếp quản, không có file đang sửa dở hoặc source app mới. Theo chỉ đạo owner "check phần nó làm dang dở để tiếp tục", Codex hoàn tất các phần bàn giao còn thiếu; không suy diễn thành owner đã nghiệm thu SPEC hoặc cho BUILD.

| Nội dung được giao recheck | Kết quả hiện tại | Căn cứ / phần còn lại |
|---|---|---|
| Giữ geometry, viewer, luồng sửa/undo; tổ chức lại module | Đồng ý đưa vào danh mục chờ owner chốt | Phụ lục SPEC v0.2 giữ đúng nhóm nguồn/đích; các thuật toán không bị thay chỉ vì đổi folder |
| Ba loại giới hạn tải, parser onboard=0, hầm mục tiêu trống | Góp ý đã được đưa vào SPEC | D2 quy định strict integer, miền, trần, quan hệ và nghĩa onboard nằm ngoài hầm; M1-02/04 có ca kiểm tương ứng. Chưa chạy test bản mới |
| Draft/STALE, lỗi API/mạng | Góp ý đã được đưa vào SPEC | D4/D7 và M1-05/07 tách trạng thái backend với UI, giữ bản đã kiểm/draft. Hành vi vẫn cần hiện thực và chứng minh |
| Types-only generation và test 3D còn thiếu | Góp ý đã được đưa vào SPEC | D5 và M1-06 yêu cầu sinh kiểu từ backend mới và đối chiếu mesh với API; không nhận ảnh cũ là bằng chứng mới |
| Lock/dependency, generated files, hồ sơ/cache/log cũ | Phân loại tái sử dụng phù hợp | Phụ lục ghi lock là ứng viên, sinh lại contract/types và để hồ sơ cũ trong archive; tương thích cài đặt chưa được chứng minh |
| Lỗi nguồn tiêu chí work order khung | Đã sửa và kiểm lại đạt | Snapshot tại f2b688e có nguyên phần tiêu chí/hash `560ba09f…`; registry/work order cùng trỏ nguồn frozen. Coverage của roadmap hiện hành, snapshot và work order đều đạt |
| Quyết định owner chọn tái sử dụng | Đã có chỉ đạo, không cần hỏi lại | Tin nhắn owner "Tôi muốn tận dụng những gì bạn đã dựng trong M1… nhưng phải có chọn lọc theo roadmap và spec mới". Chỉ danh mục chi tiết/SPEC và quyền thi công còn chờ chốt |

**Phần Codex hoàn tất:** bỏ câu hỏi lặp lại quyết định tận dụng; làm rõ đầy đủ đường dẫn nguồn trong phụ lục SPEC và đích `playwright.config.ts`; đồng bộ README/status/catalog/index/memory/state/handoff với việc recheck đã xong. Giữ nguyên phạm vi D2–D7 và các ID M1-01…M1-09; không mở thêm chức năng hoặc nhận thay owner quyết định nghiệp vụ.

**Đối chiếu lúc tiếp quản:** 50/50 file archive khớp raw Git blob; cây app chỉ có README; phần tiêu chí snapshot trùng revision dispatch, giữ nguyên SHA-256 `560ba09fe9210eb31ab58f858f89c4a007a397014507192fc5d1ae22f35794bb`; đủ 9 acceptance ID. Doctor 28/28, gate review trên phần Claude đổi và gate trực tiếp work order cũ đều đạt. Đây là kiểm tài liệu/source identity, không là test runtime app. Kiểm sau chỉnh sửa và commit được ghi ở handoff.

**Bước tiếp theo:** owner thống nhất SPEC v0.2 và danh mục tái sử dụng; sau đó agent đăng ký acceptance và soạn WORK_ORDER M1 có phạm vi nguồn/đích. Kết luận sản phẩm vẫn PENDING, completedCapabilities rỗng; chưa chuyển code. Không cần thêm một vòng recheck cùng nội dung nếu không phát sinh thay đổi hoặc bằng chứng mới.

## 10. Tiếp tục theo authority mới và kết quả chuyển

Owner chỉ đạo tiếp tục M1 với root orchestrator/reviewer, Terra 6.1 High worker và Sol-Medium cho phần khó; [SCST-D002](../decisions/SCST_D002_M1_REUSE_EXECUTION.md) và [WORK_ORDER M1](../work_orders/SCST_M1_REUSE.md) ghi authority/phạm vi. Source đã chuyển/sửa theo Phụ lục SPEC. Căn cứ và kết luận pending ở các mục trước là lịch sử, không ghi đè trạng thái mới này.

[Review M1](SCST_M1_REVIEW.md) ghi đủ 9 tiêu chí kỹ thuật và bằng chứng mới; archive 50 file nguyên vẹn. M1 sẵn cho owner xem demo, chưa nghiệm thu nghiệp vụ hoặc mở M2.
