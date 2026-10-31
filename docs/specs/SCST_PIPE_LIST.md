# SCST — List ống thép đóng bó V1.1

Status: APPROVED_FOR_EXECUTION

## Authority and design

Owner cung cấp VINAFCO268_LOCAL_HANDOFF_V1_1, yêu cầu kiểm cách tính, giữ nguyên mô hình sà lan, dùng list đã được web agent xử lý để nhập31nhóm, sinh bó chưa bố trí, chọn/đặt thủ công và cập nhật khối lượng/số bó. Đây là slice đầu vào thực bổ sung M2a; không mở planner M2b. Root orchestrator/reviewer; Terra6.1High implementation, Sol-Medium browser. R2, local-only, không push nguồn/hàng mới. Không kiểm toán lại toàn bộ Excel hay chỉnh workbook.

Reuse: normalized data, source importer/formula definitions, current validator, snapshots, viewer and reference hull. Native importer default phân bổ O/M không dùng trong app: khối lượng tính mỗi bó = K(kg/ống) × L(ống/bó), sang g nguyên. Giữ O nguồn để đối soát:1125.52t so với1125.55103t tính, lệch31.03kg do làm tròn dòng. Không gắn nhãn đã cân. Tổng31nhóm/1076bó/21226ống. Giữ hàng theo sheet+row, STT trùng không được gộp. R23:R26 thiếu nhân số bó; source CBM1130.96964733156m³ và envelope CBM1157.54318105797m³ riêng biệt. J17 constant giữ nguyên.16bó rows22/31/32 có khối bao cần xác minh, không tự sửa hay vẽ ống chi tiết.

D1 — Contract `scst.pipe-list.v1`: đúng registry1076IDs một lần mỗi bó, stable uppercase row+bundle IDs; source workbook SHA/sheet/row/group/index/dimensions/mass được bind phía server. Cargo source DOCUMENT_CALCULATED, dataset unassigned tại thư viện. V1/v2 vẫn giới hạn200 và cấm provenance/precision giả. Chỉ requirement/placement được sửa ở nguồn này; không thêm/xóa/sửa vật lý bó gốc. Default optional vì list chưa xác nhận bắt buộc toàn bộ cho một chuyến; user đổi yêu cầu rõ ràng được. Không tự gán tàu hoặc tự xếp.

D2 — Kích thước I/P/Q được chuẩn hóa15chữ số có nghĩa theo importer nguồn, đủ chính xác µm nguyên cho93giá trị. `dimensions_um` là kích thước hình học chính xác; trường mm legacy là ceil phục vụ tương thích, không dùng để vẽ/tính geometry nguồn. Bounds/overlap dùng integerµm, placement vẫn integermm, yaw90°, chạm mặt được phép. Viewer và bảng hiển thị kích thước nguồn. GLB/profile nguồn và tham chiếu hầm giữ nguyên.

D3 — Thư viện31nhóm có preview và nút nạp rõ vào hold/context hiện tại, thay manifest và reset placements về0; giữ history và STALE protection. Dùng nhóm/filter/pagination tối đa50hàng mỗi trang, counters toàn bộ và nhóm (bó/ống/khối lượng đã xếp-còn lại). Chọn bó/đặt/bỏ/xoay dùng luồng hiện tại, không dựng1076meshes trước khi đặt. Cảnh báo kích thước/chưa đo và mass/CBM comparison nhìn thấy được. Không tuyên bố cảlist vừa hầm.

D4 — Save/open/case/detach/undo không mất contract/provenance/dimensions. Newplan và CSV thaymanifest phải clear dataset và trở lại v2 có giới hạn200. Async preview/apply/open không ghi đè edit mới; selection/empty/error giữ được. Bind tất cả dữ liệu nhập qua API/save/open, không tin client metadata. Source workbook/rawpackage ở ngoàiGit, app chỉ dùng derivative kỹ thuật có provenance local.

D5 —1076placement có thể tạo578350cặp; bound returned issues200, đếm đầy đủ tổnglỗi và giữ toàn bộ affectedIDs; status/basic_checks dựa tất cảlỗi, không dựa phần cắt. Tránh tìm unit lặp tuyến tính. Kiểm tình huống tất cả trùng origin với budget thực thi hữu hạn và payload gọn. Cảnh báo nguồn độc lập với geometry status; operational_eligible luônfalse.

## Pipe list acceptance

| ID | Đầu ra và bằng chứng |
|---|---|
| PIPE-01 | Focused calculation receipt:31groups/1076bundles/21226pipes, K×L integergrams, sourceO/CBM so sánh riêng,93exactµm,16dimension-conflict bundles, nguồn/GLB hashes khớp; không audit lại Excel |
| PIPE-02 | Preview/apply list vào context hiện tại rõ ràng;1076unique unplaced registry-bound units, optional mặc định, row grouping/provenance/cảnh báo chính xác; không tự gán tàu/xếp |
| PIPE-03 | Đặt/bỏ/xoay/chọn bó cập nhật counters/mass/pipe counts toàn bộ và nhóm; exactµm render/geometry và chạm mặt đúng; không sửa vật lý sourceunit |
| PIPE-04 | Contract/source tamper bị từ chối; v1/v2 caps và kiểm cũ giữ; save/open/restart/case/detach/history/new/CSV giữ hoặc clear source đúng; STALE/async không mất edit |
| PIPE-05 |31groups/pagination50/selection/mobile/fallback usable; warnings16bó và hai mass/CBM bases rõ; full1076 bounds diagnostics tổng/affectedIDs/status đúng và payload hữu hạn |
| PIPE-06 | Contracts/build/backend/browser regression M1+VINAFCO+M2a và luồng mới pass; source/asset gốc không đổi, root independent review bằng source/assertions/screenshots; hướng dẫn đủ để owner dùng |

## Checkpoint and remainder

Selected all6criteria;180min worker +60min review/support, no automatic successor. Prior M2a evidence reused, actual elapsed/cost from preceding resumed context UNKNOWN (read-only review/calculation completed); keep total240min ceiling for this integration, no reset on repair. Cheaper direct genericCSV blocked by200cap and fractional-mm source geometry/provenance, so bounded source adapter needed. Measured hold/pipe envelope verification and business/operational acceptance remain owner checkpoint. M2b-d/M3 remain roadmap owner responsibility, concrete re-entry via next bounded SPEC after this review; no detail beyond that.
