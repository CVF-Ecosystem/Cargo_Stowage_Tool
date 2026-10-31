# SCST M1 — Technical review and owner demo handoff

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra-6.1-High + Sol-Medium
Reviewer: root-orchestrator

Ngày: 31-10-2026. Phạm vi: [WORK_ORDER M1](../work_orders/SCST_M1_REUSE.md), [SPEC v0.2](../specs/SCST_M1.md), M1-01…M1-09; acceptance section hash `effb7d0b340f5e3e8313eb5f12df019c06e4f60ec1935f17c4ee9146202fa282`. Chỉ demo synthetic BOX, một lớp, local; owner chưa nghiệm thu nghiệp vụ. Không chuyển sang M2.

## Kết luận kỹ thuật

**Đủ bằng chứng kỹ thuật cho 9 tiêu chí M1, sẵn sàng để owner xem demo.** Đã tái sử dụng có chọn lọc geometry/viewer và luồng hữu ích; model/rules/client/workspace được sửa theo contract/limits/states mới, OpenAPI/types sinh lại. Source mới độc lập archive; toàn bộ 50 file archive khớp raw Git blob của tree `e4004e274fc28aa143ce0e300b6c060d1cb1e5a0`.

Root review khác với hai worker của lượt này, đã đọc source, test và kết quả; root từng viết bản thử archive, công khai quan hệ đó. Các sửa cục bộ của reviewer được ghi riêng bên dưới. [Worker return](SCST_M1_WORKER_RETURN.md) không thay thế quyết định review hoặc owner acceptance.

## Acceptance ledger

VERIFIED dưới đây là kiểm kỹ thuật trên candidate mới; không phải chứng nhận vận hành hoặc owner nghiệm thu.

| ID | Kết quả review | Bằng chứng |
|---|---|---|
| M1-01 | VERIFIED — launcher cold/warm, UI/API và luồng runtime khi chặn kết nối ngoài loopback | [Cold start](SCST_M1_EVIDENCE/cold-start.log), [launcher](SCST_M1_EVIDENCE/launcher-smoke.log), [browser cuối do reviewer chạy](SCST_M1_EVIDENCE/reviewer-browser.log) |
| M1-02 | VERIFIED — strict integer/identity, miền/quan hệ limits, onboard=0, D3 và schema/types khớp | [51 backend tests](SCST_M1_EVIDENCE/reviewer-pytest.log), [regeneration hashes](SCST_M1_EVIDENCE/contract-hashes.txt), [source identity/checks](SCST_M1_EVIDENCE/reviewer-source-manifest.json) |
| M1-03 | VERIFIED — model/geometry/rules tách trách nhiệm, không planner, kiểm xác định/không mutation | Source `services/backend/app/domain/`; [backend oracle độc lập](SCST_M1_EVIDENCE/reviewer-backend.json) và backend tests |
| M1-04 | VERIFIED — 1g/1mm, onboard>0, containment/overlap/yaw, required/optional/excluded, từng trường D3 | Backend tests; oracle 160 case voxel với seed cố định, tổng 498 kiểm độc lập; large-layer >1.000.000 trả LAYER_UNSUPPORTED thay vì một trần không có trong SPEC |
| M1-05 | VERIFIED — ba trạng thái backend, ưu tiên lỗi hình học, operational_eligible=false và unchecked | Backend tests và source rules/model |
| M1-06 | VERIFIED — API/table/SVG/actual Three mesh đối chiếu số; chọn đồng bộ và ba limits/summary khi onboard>0 | [Browser proof](SCST_M1_EVIDENCE/browser-proof.md), reviewer-browser.log; mesh position/geometry/worldMatrix đọc từ đối tượng render, không chỉ sao chép JSON input |
| M1-07 | VERIFIED — STALE tức thời; 422, lỗi mạng, retry/undo và sửa tiếp khi response đang pending giữ đúng checked/draft | Browser cuối 5/5; [ảnh STALE](SCST_M1_EVIDENCE/browser-2d-stale.png) |
| M1-08 | VERIFIED — picking/orbit/zoom/reset; fallback WebGL, bàn phím/mobile, nhãn synthetic | [3D](SCST_M1_EVIDENCE/browser-3d-yaw.png), [mobile](SCST_M1_EVIDENCE/browser-mobile-fallback.png), [cuộn bảng](SCST_M1_EVIDENCE/browser-mobile-table-scrolled.png); root đã xem ảnh cuối |
| M1-09 | VERIFIED — hướng dẫn/cây và evidence mới; archive giữ nguyên | [APP_GUIDE](../APP_GUIDE.md), reviewer-source-manifest.json; không dùng log/ảnh cũ làm bằng chứng bản mới |

## Kiểm độc lập và sửa cục bộ

- Root chạy API/geometry review với oracle tập voxel riêng: 498 kiểm, gồm 160 case và xác định/không mutation. Sau thay đổi D3 cuối, kiểm thêm large layer và so `app.openapi()` với snapshot; đạt.
- Root chạy lại backend trên source cuối: 51 passed, exit 0. Root build lại sau sửa bố cục rồi chạy suite browser dưới guard: 5/5 passed, exit 0, 13.5 giây test time. Hai worker có log riêng trước đó; các kết quả không bị nhập nhằng thành một lượt chạy.
- Reviewer-local sửa nhãn loại/yêu cầu hàng sang tiếng Việt; sửa CSS còn thừa rail gutter, grid ba thống kê, nhãn/value, padding và vùng cuộn bảng; thêm assertion mobile full width. Lần sửa CSS đầu còn bỏ sót width calc kế thừa, đã sửa width100%, build và kiểm lại đạt. Không đổi domain/API/draft semantics.
- Cập nhật README module còn ghi “chỉ có khung”; đây là sửa hồ sơ sau runtime verification. Manifest nguồn cuối bao gồm các README này. Không lặp lại cold install chỉ vì CSS/tài liệu; evidence cold có nêu thời điểm snapshot, setup/launcher không đổi.

## Phạm vi bằng chứng và phần còn lại

- Offline: browser route chặn ngoài loopback và guard Python DNS/socket hoạt động trong tiến trình API; probe có kiểm việc chặn. Không khẳng định firewall toàn OS hoặc cài dependency không cần mạng.
- Cài dependency mới từ lock thành công. Npm audit 0 là kết quả tại lượt cài, không là chứng nhận an toàn toàn diện. Còn cảnh báo Starlette/httpx deprecation và chunk Three.js >500 kB; chưa cần đổi stack/phạm vi để xử lý trong M1.
- Lượt test đầu có lỗi encoding khi in log cold start và assertion/race trong test browser; worker sửa rồi chạy lại, đã ghi trong worker return. Không dùng các lượt đó làm PASS.
- Kiểm workspace-container riêng báo REPAIR_REQUIRED, được giữ ở handoff; doctor và các gate project áp dụng cho M1 được kiểm riêng. Không sửa container/core, không tuyên bố đã giải quyết tình trạng container.
- Chưa có planner/import/lưu bền/export/nhiều tầng/dữ liệu thật/AI. Thay đổi mất khi refresh. Hàng onboard luôn được hiểu nằm ngoài hầm mục tiêu. Demo không là quyết định vận hành.

## Bàn giao và quyền quyết định

Đóng phần thi công M1 sau commit/range checks theo work order; owner xem demo và phản hồi nghiệp vụ. Tranche kỹ thuật hoàn tất, kết luận chấp nhận sản phẩm/nghiệp vụ vẫn PENDING. Không tự mở M2. Cách chạy: [APP_GUIDE](../APP_GUIDE.md), nhấp đôi `Start-SCST.cmd` hoặc mở server local nếu orchestrator đã khởi động.

Commit vật liệu và kiểm sau commit ghi ở [handoff hiện hành](../../CVF_SESSION/handoffs/SCST_M1_REUSE_HANDOFF.md). Các gate chỉ có giá trị trong phạm vi đã invoke; không có provider/live AI-governance proof trong M1.
