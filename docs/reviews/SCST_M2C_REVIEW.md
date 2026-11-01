# SCST M2c — Giữ gốc, so sánh và khôi phục

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra-6.1-High + Sol-Medium
Reviewer: root-orchestrator

## Kết quả

Đủ sáu tiêu chí kỹ thuật trong [SPEC M2c](../specs/SCST_M2C.md). Người dùng có thể giữ bản A từ phương án hiện tại hoặc bản lưu, chỉnh/kiểm B, xem đầy đủ thay đổi và khôi phục A. B vẫn ở **Bản trước**; snapshot đã lưu không bị ghi đè. Baseline trong tab có nhãn chưa tự lưu, mất khi reload và có thể chọn lại từ bản lưu.

## Đối chiếu acceptance

| ID | Kết quả | Bằng chứng |
|---|---|---|
| M2C-01 | VERIFIED — typed API, canonical defaults, context và unit/placement theo ID; bốn trạng thái, source mismatch, thứ tự arrays không tạo diff; không mutate hoặc ghi DB | [Backend](SCST_M2C_EVIDENCE/root-backend.log), [oracle riêng](SCST_M2C_EVIDENCE/root-independent.py), [kết quả](SCST_M2C_EVIDENCE/root-independent.json) |
| M2C-02 | VERIFIED — kiểm A/B riêng, delta B−A nguyên, full issue count không dùng danh sách cắt; chi tiết 1 g/1 mm/µm; khác điều kiện không tự xếp hạng | 40 cặp ngẫu nhiên và 40 lần đảo thứ tự; full 578.351 lỗi; source/provenance và one-gram cases |
| M2C-03 | VERIFIED — pin/load A giữ B, chi tiết/lọc/tìm/phân trang 50, chọn ID trong B đồng bộ editor/viewer; 1.076 bó và mobile fallback | [28 browser test](SCST_M2C_EVIDENCE/root-browser.log), [browser return](SCST_M2C_EVIDENCE/browser-return.md), [desktop](SCST_M2C_EVIDENCE/browser/compare-desktop.png), [mobile](SCST_M2C_EVIDENCE/browser/compare-mobile-fallback.png) |
| M2C-04 | VERIFIED — restore qua validation/history, undo về B; save UUID mới và A immutable, reload/restart giữ dữ liệu; nhãn memory rõ | Browser pin/save/edit/restore/undo/save/open; [hai tiến trình server](SCST_M2C_EVIDENCE/root-restart.log), [live source](SCST_M2C_EVIDENCE/root-live.json) |
| M2C-05 | VERIFIED — STALE/pending/late/error giữ draft, lựa chọn và baseline; comparison gắn revision, không hiện như kết quả hiện hành sau edit; guard cũ còn | Sáu browser journey mới cùng 22 luồng cũ, không đổi assertions cũ; lỗi mạng/late baseline/compare/restore và phục hồi được thực thi |
| M2C-06 | VERIFIED — 104 backend, 28 browser, 902 đối chiếu riêng, build/contracts/restart, packaged flow và docs đồng bộ | [Build](SCST_M2C_EVIDENCE/root-build.log), [contract](SCST_M2C_EVIDENCE/root-contract.log), [source manifest](SCST_M2C_EVIDENCE/reviewed-source-manifest.json), [integrity](SCST_M2C_EVIDENCE/root-integrity.json) |

## Review độc lập và bằng chứng phiên bản

Admission `bc14dee`, BUILD acknowledgment `92a00c9`, nền M2b `e5a8b74b86ae5dc2530ca45a276cbb72ae354524`. Terra viết runtime/backend tests, Sol viết browser tests. Root đọc source, hợp đồng, test và ảnh; không viết runtime M2c. Root tự chạy toàn bộ **104 backend đạt 16,62 s**, **28 browser đạt 2,4 phút**, build `index-D1j1nlxy.js`, sinh types, so runtime OpenAPI và restart. [Worker return](SCST_M2C_WORKER_RETURN.md) tách phần worker với kết luận reviewer.

Root oracle dùng dictionary/set và phép tính hình học integer-µm riêng cho kỳ vọng, không gọi helper compare/evaluate của app để tạo đáp án. 902 assertions gồm 40 cặp phương án, đảo thứ tự arrays, added/removed/field/context/delta, source 1.076 bó, chênh 1 gram, immutable inputs/SQLite, malformed/tampered data và tính lại issue count. Trường hợp mọi bó cùng gốc có **578.351 lỗi**, API giữ full count; mất khoảng **4,813 s** tại máy này, trong ngưỡng SPEC 15 s. Không suy rộng hiệu năng sang máy khác hoặc khẳng định tối ưu xếp hàng.

Review hợp nhất trước freeze yêu cầu worker sửa wrap hash/tên dài, nhãn enum tiếng Việt, dấu phân cách ID, xóa alert cũ khi restore và delta khối lượng bằng gram có dấu. Các sửa này nằm trong scope cũ; build và mọi kiểm cuối chạy sau sửa. Không có test lỗi hoặc runtime repair của root trong lượt M2c. Log chỉ chuẩn hóa newline và bỏ khoảng trắng cuối dòng để đưa vào Git, không sửa kết quả. 17 ảnh hồi quy mới được sao vào evidence M2c, bản lịch sử trả nguyên byte; [bảng bảo toàn](SCST_M2C_EVIDENCE/regression-preservation.json).

Gate receipts ghi các kiểm cơ học đã INVOKED và kết quả trong [gates](SCST_M2C_EVIDENCE/gates/README.md); không tuyên bố hermetic, hosted CI hoặc CVF điều khiển AI runtime. Doctor 28/28 chỉ có phạm vi được liệt kê. Không gọi provider API, không có tuyên bố governance AI cần chứng minh live; Web evidence bridge không cần trong lượt này.

## Nghiệm thu nội bộ của đội phát triển

1. **Công việc và ranh giới:** owner yêu cầu tiếp roadmap, mở phần M2c giữ/so sánh/khôi phục. Tái dùng Plan, evaluate, editor/history 20, một viewer và snapshot SQLite; chỉ bổ sung phần thiếu. Không thay nguồn hàng, tàu, schema DB, thuật toán xếp hay dependencies; không mở M2d.
2. **Chuẩn đầu ra trước kiểm:** SPEC có sáu tiêu chí và hợp đồng g/mm/µm, provenance, bốn trạng thái ID, baseline không đổi B, source mismatch, STALE/error/late guards. So sánh mô tả dữ liệu và kiểm hiện hành, không kết luận bản tốt hơn hoặc cấp điều kiện vận hành.
3. **Kỳ vọng/đối chiếu:** nguồn derivative có hash hiện tại, fixture giả lập có nhãn và oracle tính riêng; actual API/UI/restart/version manifest ở trên. Windows/Python 3.11.9/Node 22.17/Chromium đã kiểm; hệ điều hành/trình duyệt khác NOT_TESTED. Chưa xác minh hầm thật hoặc tính phù hợp nghiệp vụ.
4. **Giá trị thêm:** history cũ chỉ quay lại, không giữ baseline riêng hoặc chỉ rõ trường nào đổi. Luồng mới chứng minh load A không thay B, một bó đổi còn 1.075 bó không đổi, xem 1 gram và phục hồi/undo đúng cả plan. Không dựng lại version database hoặc thêm viewer thứ hai.
5. **Artifact và luồng giao:** build hiện tại phục vụ qua launcher/backend local. Trên app 8765, root thực hiện VINAFCO → nạp 1.076 bó → xếp 167 bó → pin A → chỉnh yêu cầu B → compare → restore A → undo B; [ảnh so sánh](SCST_M2C_EVIDENCE/browser/root-live-comparison.png), [167 bó khôi phục](SCST_M2C_EVIDENCE/browser/root-live-restored-167.png). Plan khôi phục bằng A, undo bằng B, nguồn/hash và nhãn **1.125,55 tấn** giữ đúng; byte SQLite người dùng không đổi. Browser suite riêng dùng DB cô lập thực thi save/new UUID/reload/open; hai tiến trình xác minh snapshot qua restart. Cài mới/launcher đã có bằng chứng ở M1 và không đổi trong lượt này, không nhận là đã cài mới lại.

## Giới hạn và bàn giao

Chỉ so sánh dữ liệu/kiểm một lớp; chưa có dual scene/overlay, bulk edit, xuất báo cáo, nhiều tầng, kê/chèn/chằng, ổn định, sức bền hoặc tải sàn. Baseline và kết quả compare không tự lưu; snapshot mới giữ Plan theo luồng cũ. Hầm BOX ước tính và 16 khối bao nguồn chưa xác minh; cùng ID khác nguồn chưa chứng minh cùng bó vật lý. Chưa tổ chức hoặc tự nhận chứng nhận chuyên môn cho phương án thực. Những thiếu hụt này chặn kết luận dùng vận hành, không ảnh hưởng phép đối chiếu hai Plan đã validate.

Nội bộ kỹ thuật và luồng sản phẩm M2c đã kiểm; nghiệm thu nghiệp vụ còn PENDING. Đóng work order kỹ thuật, phần tiếp theo M2d cần SPEC/WORK_ORDER riêng khi được chọn. App [http://127.0.0.1:8765](http://127.0.0.1:8765), session 99168/PID 480; reload để lấy build mới. Chỉ commit local, không push hoặc triển khai ngoài. Cảnh báo TestClient/httpx, Three chunk và biến màu console cũ còn nguyên; không làm hỏng kết quả kiểm.
