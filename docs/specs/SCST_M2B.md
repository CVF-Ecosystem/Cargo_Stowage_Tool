# SCST M2b — Xếp thử tự động một lớp

Status: APPROVED_FOR_EXECUTION

## Authority and outcome

Ngày01-11-2026, owner phản hồi chưa thấy hàng trên hình tàu, yêu cầu làm tròn khối lượng khi thể hiện, và chọn rõ **“Bắt đầu phần xếp thử tự động theo roadmap M2b”**. Mở đúng M2b kế tiếp: gợi ý vị trí một lớp, xem/apply và lý do hàng chưa xếp. Root orchestrator/spec author/reviewer, Terra6.1High implementation, Sol-Medium browser. R2, local-only, không push nguồn hàng, không sửa sà lan. M2a và PIPE-LIST đã có model/validator/preview/snapshots/viewer; chỉ thiếu heuristic, nối preview/apply và trình bày gọn.

Kết quả người dùng: sau khi nạp hàng và chọn hầm/giới hạn, bấm **Xếp thử tự động**, xem số bó/khối lượng xếp được và lý do còn lại; **Áp dụng xếp thử** đưa các bó lên 3D/2D, chỉnh tay và lưu/mở như hiện tại. Chưa xếp không có mesh trong hầm. Hiển thị khối lượng tối đa2số lẻ tấn, ví dụ1.125,55103→1.125,55tấn; nguồn và tính/lưu vẫn gram chính xác.

## Design and contracts

D1 — Input/output: POST `/api/planner/preview` nhận Plan hiện hành (M1/M2a/PIPE-LIST), trả `PlannerPreview` gồm `evaluation` của candidate, `unplaced` lý do theo từng unit chưa đặt (kể cả excluded), và tên/version thuật toán. Giữ units, metadata, requirement, hold, limits, vessel, source và contract; chỉ thay placements. Không tự nạp list, gán tàu hoặc nâng giới hạn chuyến. Mọi placement cũ được dựng lại trong candidate; preview không đổi input/workspace/DB. API không nhận đường dẫn/chạy code/solver ngoài. Backend validate/re-evaluate candidate độc lập với packer; không tin status heuristic.

D2 — Heuristic đơn giản, deterministic, bounded: guillotine free rectangles, một lớp Z0/layer0/no support; yaw0/90. required trước optional; thứ tự diện tích footprint giảm dần, ID làm tie-break, excluded bỏ qua. Với mỗi unit, kiểm height và footprint hai hướng trên hold ban đầu, rồi khối lượng còn được xếp = voyage−onboard−placed. Tìm free rectangle theo thứ tự ổn định, lựa chọn hướng bằng tiêu chí best-fit/tie-break ghi trong code. Đặt tại góc rectangle, tách thành hai rectangle không chồng nhau: dải phải cao bằng bó và phần phía trên rộng bằng rectangle. Không backtracking hoặc cam kết tối ưu.

D3 — Precision: source dimensions_um giữ nguyên cho validator/viewer. Planner dự trữ footprint trên lưới mm nguyên bằng ceil mỗi chiều từ µm (khe kỹ thuật dưới1mm/chiều); tọa độ đầu ra mm nguyên, yaw90°. Không sửa kích thước nguồn hay coi khe lưới là kê/chèn theo nghiệp vụ. Hold BOX vẫn qua geometry adapter hiện có. Mass dùng integergrams; không làm tròn để quyết định nhận bó. Mỗi bó một lần, không vượt biên/overlap/tải còn lại. N=1076 có budget kiểm≤15s trên môi trường local hiện tại, không thêm dependency.

D4 — Accounting/reasons: mọi ID đúng một trong placed hoặc unplaced. Mỗi unplaced một lý do có code và diễn giải tiếng Việt, ưu tiên EXCLUDED → TOO_HIGH/FOOTPRINT_TOO_LARGE (không vừa hold ban đầu ở cả2hướng) → MASS_LIMIT → HEURISTIC_NO_SPACE. Mã cuối nghĩa là heuristic chưa tìm được vị trí ở trạng thái hiện tại, không chứng minh không có phương án khác. required chưa xếp vẫn là vi phạm rule; không đổi requirement để tạo trạng thái đạt. Cảnh báo source16bó và dữ liệu hầm ước tính vẫn có. Không khẳng định toàn bộlist phải xếp vừa hoặc đủ điều kiện vận hành.

D5 — UI transaction: Xếp thử chỉ tạo preview với cảnh báo sẽ thay vị trí cũ, số bó/khối lượng/remaining và lý do. Áp dụng rõ mới request validate/transition, đưa kết quả lên mesh thật, giữ bản trước để undo. STALE chặn preview/apply, pending và response cũ không ghi đè draft/selection/context mới; lỗi mạng giữ bản trước. Preview key bao gồm checkedplan và revision hiện có. Không autoapply khi chọn tàu/nạp list. Bảng hiện lý do đúng với candidate hoặc checkedplan đã apply; lọc/phân trang lý do tối đa50 để1076units dùng được. Sau manual/context thay đổi, bỏ nhãn lý do cũ hoặc ghi lịch sử rõ; không gán lý do stale cho kết quả hiện tại.

D6 — Persistence: Plan đã áp dụng lưu/mở giữ placements/metadata như M2a; heuristic reasons thuộc lượt gợi ý trong tab, không thêm schemaDB hoặc sửa savedPlan contract. UI nói rõ chạy lại Xếp thử để lấy lý do mới sau mở/chỉnh; không hứa lưu kết quả phân tích riêng. Bản trước/đổi cấp/reset/new/CSV vẫn đúng. Viewer có thông báo chưa có bó được đặt và chỉ dẫn chạy Xếp thử/đặt tay, tránh hiểu nhầm dữ liệu đã có là đã bố trí.

D7 — Display: formatter tấn tối đa2chữ số thập phân, cùng quy tắc ở stats/table/counters/preview/source summary. Các tổng khác0 nhưng quá nhỏ để hiện2số lẻ dùng nhãn `<0,01 tấn` thay vì0; giá trị0 thật vẫn0. Input sửa kg và plan/API/DB không đổi precision. CBM source/computed trên giao diện làm tròn2số lẻ, vẫn phân biệt hai basis và cảnh báo; tài liệu kiểm tính/nguồn giữ số đầy đủ. Thông báo ngắn hiển thị làm tròn, tính/lưu chính xác. Điều chỉnh tối thiểu expectation hiển thị ở test cũ được phép do owner đổi yêu cầu, giữ các assertion integergrams/STALE/geometry.

## M2b acceptance

| ID | Đầu ra và bằng chứng |
|---|---|
| M2B-01 | Planner deterministic cho0–200generic và1076source units; geometry/mass chính xác, yaw0/90/singlelayer, metadata/requirements giữ nguyên; input không bị mutate và candidate được validator kiểm |
| M2B-02 | Mọi unit accounted placed hoặc một lý do unplaced, excluded không đặt; required ưu tiên và missing vẫn bị rule báo; height/footprint/mass/heuristic-no-space đúng, không tuyên bố tối ưu hoặc impossibility |
| M2B-03 | Preview không đổi workspace; apply rõ đưa cargo lên actualThree/2D/VINAFCO, counters khớp, chọn/chỉnh/undo; chưa đặt được giải thích ngay trong viewer; không nâng giới hạn hay tự đổi tàu |
| M2B-04 | STALE/pending/late/error giữ draft/context, lý do không stale; table/filter/pagination và mobile/fallback dùng được; save/reload/restart giữ appliedplacements/source, reasons có nhãn chỉ ở lượt gợi ý |
| M2B-05 | Khối lượng display tối đa2số lẻ tấn, tổng1125551030g hiện1.125,55tấn; số nhỏ không bị thể hiện thành0, input/API/storage/source mass vẫn chính xác; CBM display gọn và giữhai basis |
| M2B-06 | Generic boundary/rotation/priority/capacity/height/fullsource1076/performance, browser packagedflow và hồi quy đạt; root oracle/review độc lập, ảnh actualship+cargo, hướng dẫn/roadmap/truth cập nhật |

## Checkpoint and owned remainder

Chọn sáu tiêu chí;180phút implementation +60phút review/support, không reset budget khi sửa. Preparation: canonical scan/doctor28checks và read-only design review; elapsed trước marker chưa đo chính xác, billing UNKNOWN. Reuse M2a/PIPE-LIST proof, validators/storage/viewer; preview hiện có chưa tạo vị trí nên không đủ cho yêu cầu mới. Heuristic nhỏ bổ sung đúng gap, không viết lại renderer/importer. Stop ở proof/scope/240min boundary, không tự mở mốc kế tiếp.

M2c so sánh đầy đủ và M2d export do orchestrator giữ tại checkpoint roadmap sau M2b. Nhiều tầng/kê chồng, dữ liệu hầm đo thực,16source envelopes, ổn định/sức bền/tải sàn và nghiệp vụ thuộc M3/owner/domainverification, không chặn xếp thử có nhãn trên BOX hiện có vì thuật toán không tuyên bố tính đúng cho hầm thực. Không đổi source mass, ship/profile, locks/dependencies, schemaDB, AI hoặc externalprovider. Technical verification và developer-owned usableflow trước owner business acceptance; không suy diễn từ request này thành nghiệm thu phương án thực.
