# SCST — Đơn vị hiển thị thực tế

Status: APPROVED_FOR_EXECUTION

## Authority and design

Owner 01-11-2026 yêu cầu số liệu thể hiện phù hợp thực tế kg/cm, không tập trung 1 g/1 mm. Đây là lượt sửa UI trên M2c (base232807d), không mở M2d hay thay tiêu chí lịch sử. Root ORCHESTRATOR/SPEC_AUTHOR/WORK_ORDER_AUTHOR và independent REVIEWER; Terra implementation, Sol browser. R2 ceiling, local-only.

D1. Thống kê tổng giữ tấn tối đa 2 số lẻ; chi tiết bó và compare khối lượng kg nguyên; kích thước/tọa độ cm nguyên, kích thước tàu/hầm có thể m tối đa2số lẻ (1cm). Dùng định dạng vi-VN, nhãn đơn vị ở bảng/legend/editor/detail rõ. Ví dụ 911400g→911kg, 6401000µm→640cm, 337600µm→34cm. Đây là xấp xỉ hiển thị; không đổi mesh, không làm tròn geometry để lọt biên/tải.

D2. Ô nhập/thêm/sửa dùng kg và cm, mặc định hiển thị tròn đến1kg/1cm; lưu mm/g qua chuyển đổi chính xác. Được nhập phần lẻ biểu diễn được (cm tối đa1số lẻ, kg tối đa3) cho dữ liệu cũ/nguồn, không ép xuống lưới hay cấm precision đã có. Giá trị hiện gọn được tách với underlying Plan: chỉ trường người dùng thực sự sửa mới áp lại, kể cả khi nhập lại cùng chuỗi làm tròn. Sửa yaw/requirement/name/limit không được làm tròn khối lượng/tọa độ/kích thước nguyên bản chưa sửa. STALE/selection/undo/baseline/save/reopen/late guards giữ. Source physical fields readonly, không sửa registry/µm.

D3. Compare backend và trạng thái từng ID vẫn chính xác, UI detail/delta quy về kg/cm/m. Chênh khác0 dưới1kg/1cm hiện chữ dưới mức hiển thị, không in1g/µm hoặc báo0/không đổi; hai số trước/sau làm tròn bằng nhau có chú thích rõ. Đổi điều kiện/provenance/cảnh báo/issue counts vẫn hiện. Không tự bỏ các diff nhỏ hoặc chấp nhận dung sai nghiệp vụ.

D4. CSV/API/DB tiếp tục hợp đồng mm/g/µm, CSV giữ header/dữ liệu có nhãn định dạng rõ. Không đổi source/profile/GLB/model/rules/planner/storage/contracts/locks/core. Chỉ UI/nhãn/hướng dẫn và kiểm bị ảnh hưởng; geometry, attributes evidence và dữ liệu saved unchanged giữ exact. Đừng đổi geometry helper dimensions/footprint đang phục vụ vẽ thành rounded display. Không thêm dependencies, provider hoặc push.

## Display acceptance

| ID | Đầu ra và kiểm |
|---|---|
| DU-01 | Mô hình, bảng, editor và compare dùng kg/cm/m dễ đọc; totals t2decimals; vi-VN, không phơi g/mm/µm như đơn vị thao tác thường ngày ngoài contract CSV có nhãn |
| DU-02 | Chỉ explicit edits đổi Plan; unchanged 2500001g/501mm/exactµm giữ qua yaw/requirement/context edits, undo/save/reopen; kg/cm nhập convert chính xác, lỗi không mất draft |
| DU-03 | Compare dưới1kg/1cm có nhãn thay vì0 hoặc emphasis gram/µm, counts/context/provenance và APIexact không đổi; stale/late guards giữ |
| DU-04 | Build, focused units và browser regression/actual packaged VINAFCO cargo chứng minh dễ đọc lẫn underlying unchanged; source/model/planner/storage/API immutable, guide/continuity/review cập nhật |

## Checkpoint and owned remainder

100min gồm implementation60/review40, preparation doctor28+read-only preflight đã thực hiện, billing/elapsed partlyUNKNOWN. Tái sử dụng UI/Plan/history/SQLite; điểm thiếu là lớp trình bày và edit tracking để không ghi số rounded vào dữ liệu chưa sửa. Ưu tiên focused checks, một full browser run sau freeze, không chạy lại backend không đổi khi không có lý do. Root review có oracle integer chuyển đơn vị và byte/hash preservation, usable packaged flow trước feedback. Kết luận riêng technical readiness/business acceptance/external publication. Hầm thực/16envelopes/M2d/M3 vẫn chờ riêng, không nhận là tolerances đã xác minh.
