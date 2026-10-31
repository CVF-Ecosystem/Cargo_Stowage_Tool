# SCST — Review tích hợp list ống V1.1

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra-6.1-High + Sol-Medium
Reviewer: root-orchestrator

## Kết quả

Đủ sáu tiêu chí kỹ thuật trong [SPEC](../specs/SCST_PIPE_LIST.md). Có thể xem trước và nạp 31 nhóm thành 1.076 bó chưa bố trí, chọn/đặt/xoay/bỏ từng bó, theo dõi số bó/ống/khối lượng toàn bộ và từng nhóm, rồi lưu/mở lại. Mô hình sà lan, profile và workbook gốc giữ nguyên. Không mở planner M2b hoặc nghiệm thu vận hành.

## Acceptance và bằng chứng

| ID | Kết quả kỹ thuật | Bằng chứng |
|---|---|---|
| PIPE-01 | VERIFIED — 31 nhóm, 1.076 bó, 21.226 ống; K×L chính xác gram; tổng nguồn/CBM giữ riêng, 93 kích thước chính xác µm; 16 bó cần xác minh | [Đánh giá tính toán](SCST_PIPE_LIST_ASSESSMENT.md), [receipt](SCST_PIPE_LIST_EVIDENCE/calculation-receipt.json) và [script đối chiếu](SCST_PIPE_LIST_EVIDENCE/calculation-check.py) |
| PIPE-02 | VERIFIED — preview không đổi workspace; nạp rõ ràng giữ hầm/giới hạn, tạo đủ IDs duy nhất, optional và chưa xếp; nguồn chưa gán sẵn tàu | API/registry, backend test và browser journey thứ nhất |
| PIPE-03 | VERIFIED — đặt/xoay/bỏ cập nhật số bó/ống/mass; geometry và Three mesh dùng µm chính xác; các trường vật lý nguồn cố định | [222 kiểm độc lập](SCST_PIPE_LIST_EVIDENCE/root-independent-checks.json), browser journey thứ hai kiểm mesh/world matrix; [bó đã đặt trên VINAFCO](SCST_PIPE_LIST_EVIDENCE/browser/root-vinafco-pipe-placed.png) |
| PIPE-04 | VERIFIED — source tamper bị từ chối, v1/v2 vẫn giới hạn200; case/detach/undo/snapshot giữ provenance, new/CSV clear nguồn; STALE/preview đến muộn giữ edit | Backend/CSV guards, browser journey thứ ba, [hai server riêng](SCST_PIPE_LIST_EVIDENCE/root-restart-smoke.log), kiểm DB không bị ghi khi source bị sửa |
| PIPE-05 | VERIFIED — 31 nhóm/50 hàng mỗi trang, counters toàn bộ/nhóm, cảnh báo tiếng Việt; mobile/fallback dùng được; 578.350 overlap đếm đầy đủ, chỉ trả200 nhưng giữ1076 affectedIDs/status | [Desktop](SCST_PIPE_LIST_EVIDENCE/browser/pipe-list-desktop.png), [mobile](SCST_PIPE_LIST_EVIDENCE/browser/pipe-list-mobile-fallback.png), stress trong kiểm độc lập |
| PIPE-06 | VERIFIED — 92 backend/17 browser/build/restart/contracts đạt; source review độc lập, hướng dẫn cập nhật, nguồn/ship không đổi | [Backend](SCST_PIPE_LIST_EVIDENCE/root-backend-tests.log), [browser](SCST_PIPE_LIST_EVIDENCE/root-browser-tests.log), [build](SCST_PIPE_LIST_EVIDENCE/root-frontend-build.log), [live smoke](SCST_PIPE_LIST_EVIDENCE/live-smoke.json), [source manifest](SCST_PIPE_LIST_EVIDENCE/reviewed-source-manifest.json) |

## Review độc lập, lỗi và sửa

Root đọc source model/registry/geometry/rules/CSV/workspace/viewer, kiểm assertions và xem ảnh desktop/mobile. Root không sửa runtime. Các điểm review sớm được Terra sửa trong cùng scope: giữ nguyên group ID nguồn; generator kiểm hash và tổng trước khi ghi; nhãn hàng theo list ở cả hầm giả lập/tự nhập; detach vẫn sửa hầm được mà không mất contract; sau đặt vẫn chọn đúng bó; cảnh báo nguồn có diễn giải tiếng Việt, hai chênh lệch mass/CBM hiện rõ.

Root kiểm độc lập 222 điều kiện: mỗi nhóm so với receipt raw XML, source tamper qua validate/save và DB không đổi, 30 bố trí ngẫu nhiên ×18 bó đối chiếu hình hộp bằng số nguyên µm, toàn bộ1.076 bó chồng nhau, snapshot roundtrip. Trường hợp stress dùng mức VINAFCO nên chỉ có578.350 overlap, payload639.672bytes, khoảng1,699s; worker dùng giới hạn mẫu32t nên có thêm1 lỗi overweight. Cả hai giữ200 lỗi hiển thị, tất cả1.076 affectedIDs, DRAFT và basic_checks_passed=false. Không che lỗi bằng cắt danh sách. [Script độc lập](SCST_PIPE_LIST_EVIDENCE/root-independent-checks.py) giữ cách tái lập; script tính nguồn cần gói local ngoàiGit.

Root chạy lại92backend (6,09s), build và smoke hai tiến trình trên backend đã freeze. Sol chạy4/4 luồng mới, rồi bộ17 ban đầu đạt16/17: formatter chung đổi `6000` thành `6.000` làm một test M1 không đạt. Terra sửa riêng bảng legacy, không sửa test; root build và chạy lại **17/17 đạt (57,1s)**. [Log lượt lỗi](SCST_PIPE_LIST_EVIDENCE/browser/pipe-list-playwright.log) và [bàn giao browser](SCST_PIPE_LIST_EVIDENCE/browser-return.md) được giữ. Các kiểm backend222/92/restart trước sửa formatter vẫn đúng với backend cuối vì sửa chỉ nằm ở hiển thị frontend. Không lặp các kiểm không bị ảnh hưởng.

Root kiểm thêm app đang chạy trên8765: HTML/OpenAPI khớp contract, API31nhóm, nạp list vào VINAFCO rồi đặt bó đầu tại1000/1000mm; actual Three mesh đúng6,401 ×0,3376 ×0,2954m, thân GLB hiển thị. Không lưu snapshot thử vào DB người dùng. Ảnh bằng chứng các tranche cũ do test sinh lại được lưu riêng vào thư mục regression của lượt này rồi khôi phục bytes gốc; không dùng chúng để sửa lịch sử nghiệm thu.

## Khả năng sử dụng và phần còn lại

Người dùng có đường vào rõ: chọn hầm → Xem trước list ống → Nạp list vào phương án hiện tại → lọc nhóm/chọn bó → Đặt bó → chỉnh/kiểm lại → lưu/mở. Tổng K×L **1.125,55103t** khác tổng dòng O **1.125,52t** đúng31,03kg; không phân bổ O/M hoặc gắn nhãn đã cân. Counters còn lại bao gồm bó loại trừ, có nhãn rõ. Lưu snapshot không lưu rawdraft. Chỉ bó đã đặt được dựng trong hầm; không giả vờ cảlist đã xếp.

16 bó có khối bao cần xác minh; các kích thước khối bao còn lại cũng chưa phải số đo xác nhận. Hầm vẫn ước tính, BOX/một lớp. Chưa chứng minh cảlist vừa hầm; chưa ổn định, sức bền, tải sàn, kê/chèn/chằng, nhiều tầng. CSV phổ thông200bó/1MiB; adapter nguồn riêng hỗ trợ1076, chưa phải importer XLSX tổng quát. Business acceptance thuộc owner; các checkpoint M2b-d/M3 giữ trong roadmap, chưa dispatch tiếp.

Launcher/dependencies/locks giữ nguyên, tái sử dụng proof setup trước; không cài lạnh lại. Cảnh báo httpx/TestClient, chunkThree.js và NO_COLOR/FORCE_COLOR vẫn còn. Không có provider call hoặc tuyên bố CVF quản trị AI ở runtime. Gate receipts là bằng chứng các control đã gọi, không chứng minh mọi lệnh shell bị chặn hay gate hermetic.

## Bàn giao local

[APP_GUIDE](../APP_GUIDE.md) và README có thao tác nguồn list. Demo được khởi động lại bằng launcher hiện có tại http://127.0.0.1:8765, managed session8774/PID41676; bản99663/PID26620 dừng bình thường. SQLite người dùng giữ nguyên; gói nguồn V1.1 bị loại khỏi Git. Source và evidence chỉ commit local, không push dữ liệu mới. Đóng work order phần kỹ thuật; owner phản hồi nghiệp vụ trước khi chi tiết hóa phần kế tiếp.
