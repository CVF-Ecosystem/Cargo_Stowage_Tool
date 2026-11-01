# SCST — SUP-01 viewer thực dụng và giữ trạng thái

Status: APPROVED_FOR_EXECUTION

## Authority and design

Owner đã chốt roadmap bổ sung và yêu cầu tiếp tục sau khi áp dụng phần CVF mới. SUP-01 nằm trước
SUP-02/03/M2d, không mở toàn bộ roadmap. Nền code 6f8fa9f và user transfer chưa commit được giữ nguyên.
Risk R2, root orchestrator/spec author, Terra implementation worker, Sol browser worker, root independent
implementation reviewer và commit steward. Không gắn vai trò cố định vào provider trong sản phẩm.

CVF common baseline: core c4c8767, profile1.2; supplement operator-local có hash admission riêng.
Áp dụng SCST-DA01 (exact data/practical units), DA04 (reuse/receipt/claim), DA05 (internal usable flow).
DA02 là ranh giới: không đổi persistence và dùng DB thử tách biệt; DA03 giữ geometry/profile/nguồn hiện có,
không thêm dung sai hay dùng hình minh họa để nghiệm thu stability/strength.
Continuation CVF-DEV theo [review](../reviews/SCST_CVF_DEV_APPLICATION_RECONCILIATION.md), không phải nghiệm thu toàn adoption.

D1. Giữ renderer, scene, controls và canvas qua cập nhật Plan cùng tàu/hầm, selection, case và ẩn/hiện tàu.
GLB tải theo identity asset/profile/transform, không tải lại khi case/visibility/cargo đổi. Cập nhật cargo theo ID,
giữ đối tượng không đổi khi phù hợp; dispose tài nguyên thay/xóa. Callback dùng giá trị mới nhất. Tách identity
hold/profile khỏi object identity React; đổi tàu/hầm có chủ đích cập nhật geometry và căn khung. Asset load cũ
đến muộn phải bị bỏ/dispose; bỏ reference profile phải xóa hull/marker/status cũ. Resize giữ hướng, không tự reset orbit.

D2. Thêm nút “Vừa khung”, “Nhìn trên”, “Nhìn mạn”, “Tập trung bó”; giữ reset “Đặt lại góc nhìn” về toàn cảnh.
Fit tính từ bounds thực và FOV/aspect với khoảng thở, gồm hầm/hàng và tàu khi hiện. Preset top/side không làm
mất selection; focus dùng envelope chính xác của bó đã đặt, không lấy đai trang trí làm nguồn nghiệp vụ.
Focus disabled khi chưa có selected placement; bounds rỗng/asset fail vẫn fit hầm. Điều chỉnh clipping và
control distances theo cảnh; finite camera tại desktop/mobile. Không thay Plan bởi lệnh camera/material.

D3. Giữ vật liệu gốc của GLB; chế độ “Thân mờ” mặc định chỉ giảm opacity/depthWrite cho các mesh vỏ che hầm
đã nhận diện trên VINAFCO. Chế độ “Vật liệu gốc” phục hồi đúng thuộc tính; cabin và vật khác giữ nguyên.
Clone/own material cần thay để tránh lan qua vật liệu shared; dispose clone khi thay asset/unmount. Asset lạ
giữ vật liệu gốc với safe fallback. Tách ẩn tàu khỏi material mode, cargo/floor không chịu opacity thân tàu.

D4. Render on demand hiện có được giữ. Heavy per-mesh bounds/projection/JSON diagnostics mặc định tắt;
chỉ bật bằng query rõ `?viewerDiagnostics=1`, không đưa dữ liệu kỹ thuật vào luồng người dùng thường.
Khi bật, giữ data-meshes/projected-meshes/camera/vessel-bounds/draft-marker cho exact assertions; thêm counters
tối thiểu phục vụ lifecycle/resource proof nếu cần, không làm source truth. Khi tắt không traverse/serialize mọi
mesh mỗi orbit. Không dùng timers/animation loop idle mới, không thêm thư viện/engine/instancing trước bằng chứng cần thiết.

## SUP-01 acceptance

| ID | Đầu ra và kiểm bắt buộc |
|---|---|
| S1-01 | Cùng canvas/GLB/camera khi orbit rồi sửa/apply/undo/case/visibility; cargo và marker đúng dữ liệu mới. Đổi context, load muộn, xóa asset và cleanup không giữ hull/selection callback cũ. |
| S1-02 | Fit/top/side/focus/reset dùng được desktop và 390px, bounds nằm trong camera khi yêu cầu fit; focus có guard, picking/table/2D chọn cùng ID; asset/context loss vẫn có luồng fallback. |
| S1-03 | Ghost có chọn lọc và phục hồi vật liệu; visibility không reload/reset; exact dimensions/translation/mass/Plan/history/save/reopen và kg/cm/m giữ. Không sửa backend/profile/GLB/source/contracts. |
| S1-04 | Diagnostics mặc định off, opt-in giữ exact assertions; build/browser regression và flow nội bộ đạt; đo cùng browser/máy cho synthetic và list1076 với số bó thực đã đặt, ghi thời gian/tài nguyên và giới hạn, không công bố FPS/tăng tốc không có baseline. |

## Verification and checkpoint

Giữ toàn bộ exact geometry assertions cũ, bật diagnostics có chủ đích trong test cần dùng; di chuyển output
test sang evidence SUP-01 để không ghi đè evidence lịch sử. Baseline đo trước build mới, candidate đo cùng môi trường;
timing là quan sát với sample/range, không threshold hiệu năng tùy ý. List1076 thường chỉ đặt được một phần trong
hầm/tải hiện có; ghi rõ số placed/unplaced, không dựng đủ1076 trong hầm rồi nhận là phương án hợp lệ.
Ghi browser/device/viewport, GLB request/canvas persistence, render/resource counters trong scope, thao tác/picking,
camera và bounds. Preserve exact source µm/mm và transform(-.9725,-.832,0); không round-trip từ nhãn cm.

Luồng nội bộ: mở synthetic → chọn/orbit/sửa/kiểm → đổi góc → undo → lưu/mở trên DB thử; mở VINAFCO/list →
xếp thử/áp dụng → chọn/focus/ghost/ẩn hiện → case → 2D/fallback; bảng/3D/cảnh báo khớp. Chứng minh lỗi/load muộn/
resource cleanup bằng case hợp lý, giữ failed attempts. Không chạy backend suite không đổi trừ có named gap.
Một full browser regression sau freeze, focused repair khi có nguyên nhân; không chạy suite song song trên port8766.

120 phút gồm prep/worker/browser/review, không reset khi repair; có thể bàn giao chưa đủ nếu gặp budget boundary,
không đổi mandatory acceptance thành optional. Worker return và root review nêu evidence/version/limits.
Checkpoint chỉ chốt kỹ thuật và usable flow của SUP-01; business acceptance và public push riêng. SUP-02/03,
M2d/M3/M4 cùng hầm đo thực và16 envelopes có owner trong roadmap, không tự mở.
