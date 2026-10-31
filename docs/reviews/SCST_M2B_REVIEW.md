# SCST M2b — Xếp thử một lớp và làm tròn hiển thị

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra-6.1-High + Sol-Medium
Reviewer: root-orchestrator

## Kết quả

Đủ sáu tiêu chí kỹ thuật và luồng sử dụng trong [SPEC](../specs/SCST_M2B.md). Người dùng có thể nạp list, chọn hầm/giới hạn, **Xếp thử tự động → Áp dụng xếp thử**, thấy các bó trên tàu, chỉnh tay/undo và lưu/mở. Giao diện đưa tới viewer sau áp dụng, có lý do cho từng bó chưa đặt. Tổng nguồn1125551030g hiện **1.125,55tấn**; số tính/lưu và inputkg vẫn chính xác.

## Acceptance và bằng chứng

| ID | Kết quả kỹ thuật | Bằng chứng |
|---|---|---|
| M2B-01 | VERIFIED — deterministic guillotine một lớp0/90, exactgram capacity, conservative mm grid/exactµm validator, chỉ đổi placements | Planner source, backend tests, [oracle độc lập](SCST_M2B_EVIDENCE/root-independent.json) |
| M2B-02 | VERIFIED — ưu tiên required, excluded không đặt; mọi ID accounted, đúng một lý do remaining; required missing vẫn bị rule báo |40manifests ngẫu nhiên×3, boundary reasons/mass/priority/yaw,1076source kiểm độc lập |
| M2B-03 | VERIFIED — preview giữ workspace, apply qua validator/history đưa actualmeshes lên VINAFCO/2D; undo, selection, capacity giữ đúng; viewer có hướng dẫn và tự cuộn sau apply | [Fullbrowser](SCST_M2B_EVIDENCE/root-browser.log), [167bó trên tàu](SCST_M2B_EVIDENCE/browser/root-vinafco-167-placed.png), [repair review độc lập](SCST_M2B_EVIDENCE/local-repair-review.md) |
| M2B-04 | VERIFIED — STALE/late/failure giữ checkedplan/draft; reasons không gán stale,50bó/trang, mobilefallback; save/reload/restart giữ positions/provenance | [Browserreturn](SCST_M2B_EVIDENCE/browser-return.md), [restart hai tiến trình](SCST_M2B_EVIDENCE/root-restart.log), [mobile](SCST_M2B_EVIDENCE/browser/planned-mobile-scene.png) |
| M2B-05 | VERIFIED — mass và CBM display gọn, hai basis vẫn riêng; input/API/DB không làm tròn;1g hiện<0,01tấn với0.001kg input | Browser precision/source assertions, planner mass equality/off-by1 boundary, summary/API evidence |
| M2B-06 | VERIFIED —98backend/22browser/build/types/OpenAPI/restart và rootoracle đạt, metadata/ship/source giữ nguyên, guide/roadmap/truth cập nhật | [Backend](SCST_M2B_EVIDENCE/root-backend.log), [build](SCST_M2B_EVIDENCE/root-build.log), [source manifest](SCST_M2B_EVIDENCE/reviewed-source-manifest.json), [live167mesh](SCST_M2B_EVIDENCE/root-live.json) |

## Review độc lập và giới hạn phiên bản

Root đọc planner/model/geometry/rules/API, workspace transaction/reason state, formatters, viewer và assertions; kiểm ảnh desktop22bó, full167bó trên thân tàu và mobile2D. Root tự chạy98backend (4,72s), build/types, restart bằng hai server riêng và8.941assertions độc lập:40manifests×3, independent integerµm bounds/overlap/mass/accounting/metadata, priority/rotation/dimension/mass boundary, source tamper và isolated snapshot roundtrip. Không dùng output heuristic làm oracle cho tính hợp lệ. Không kiểm tối ưu packing.

Với nguồn1076bó, hầm VINAFCO và giới hạn VR-SII đầy đủ:167bó/217741190g được đặt,909còn lại, preview khoảng0,102s trong oracle. Với giới hạn chuyến32t vẫn giữ từ mẫu:22bó/31,83t. Đây là kết quả thuật toán hiện tại, không phải năng lực tối ưu của hầm hay chứng minh không thể xếp thêm theo cách khác. Allplaced không có overlap/out-of-bounds/overweight/layer issues; optional remaining không biến thành required hoặc bị xóa. Nguồn16envelopes cảnh báo vẫn giữ.

Sol focused đầu3/4 bị lỗi testhelper chờ POST ở endpoint mở snapshot bằng GET; helper sửa và thêm case1g, đạt5/5. Root full đầu21/22: camera drag test lấy boundingbox khi canvas dưới viewport. Root thực hiện [reviewer-local repair](SCST_M2B_EVIDENCE/local-repair-review.md), Sol review độc lập, root build và chạy lại **22/22 đạt46,7s**. [Lượt lỗi đầu](SCST_M2B_EVIDENCE/root-browser-initial-failed.log) được giữ. Không sửa assertions camera/picking để bỏ lỗi; chỉ cuộn đến canvas. Bốn expectation hiển thị cũ đổi theo chỉ đạo rounding của owner, các kiểm integergram/geometry/async còn nguyên.

Root chỉ sửa một statement runtime cuộn tới viewer sau explicitapply; backend/heuristic là Terra, source và phần này được root review độc lập; statement của root được Sol review độc lập. Backend không đổi sau98/restart/oracle nên không lặp kiểm không bị ảnh hưởng. Live smoke cuối trên8765 xác nhận167meshes thật và label1.125,55tấn, viewer trong viewport, không lưu test snapshot vào DB người dùng. Helper bổ sung assertionviewport ban đầu sai tên Python encoding; đã sửa và chạy riêng thành công, không dùng invocation lỗi làm proof.

## Usability, dữ liệu và phần còn lại

Luồng đã được đội phát triển chạy từ app thật trước owner feedback: chọnVINAFCO → nạp1076bó → khai báo giới hạn → xem trước → áp dụng → nhìn cargo/remainingreasons → chỉnh/undo → save/reload/open. Input và nguồn/hash/requirement giữ nguyên; mỗi bó đặt đúng một lần. Preview không tự gán tàu/nâng tải hay ghi DB. Reasons chỉ ở lượt gợi ý trong tab; sau mở/chỉnh chạy lại để có lý do mới. Source/profile/GLB/workbook và schemaDB/dependencies/launcher không đổi; proof cài/chạy trước được tái sử dụng.

Heuristic một lớp, không backtracking/tối ưu, không kê/chèn/chằng/multi-layer hoặc stability/strength/floorload. Hold vẫn BOX ước tính;16khối bao cần xác minh. Số lưới ceilmm không phải khoảng kê nghiệp vụ. M2c so sánh đầy đủ và M2d export chưa triển khai; M3/domainverification và business/operational acceptance vẫn riêng. Không có provider call hoặc tuyên bố CVF điều khiển AI runtime. Cảnh báo httpx/TestClient, Threechunk và NO_COLOR/FORCE_COLOR còn nguyên.

## Bàn giao

Chạy [app local](http://127.0.0.1:8765), reload để lấy giao diện mới, rồi **Xếp thử tự động → Áp dụng xếp thử** sau nạp hàng. [APP_GUIDE](../APP_GUIDE.md) ghi rõ giới hạn mặc định32t và cách thao tác. Runtime session21770/PID34300; predecessor8774/PID41676 đã dừng bình thường. SQLite người dùng không bị thêm snapshot thử. Đóng work order kỹ thuật, giữ ownerbusinessfeedback và checkpoint SPEC M2c; chỉ commit local, không push dữ liệu mới.
