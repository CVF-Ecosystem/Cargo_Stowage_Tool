# SCST M2a — Review nhập liệu/import/lưu-mở

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra-6.1-High + Sol-Medium
Reviewer: root-orchestrator

## Kết quả

Đủ bảy tiêu chí kỹ thuật M2a. Người dùng có thể tạo phương án rỗng, nhập hàng/hầm BOX, xem trước CSV có lỗi dòng/trường, áp dụng manifest và lưu/mở snapshot SQLite local. Chế độ M1/VINAFCO vẫn chạy; không mở bộ xếp tự động M2b, so sánh đầy đủ M2c hoặc báo cáo M2d.

Owner xác nhận chưa có manifest/số đo hầm thực và cho tiếp tục với mẫu có nhãn. Kết quả này chưa nghiệm thu importer trên manifest thật hoặc hình học hầm thật. Nhập tay/CSV không biến dữ liệu thành được xác minh, và lưu phương án không cấp điều kiện vận hành.

## Acceptance và bằng chứng

| ID | Kết quả kỹ thuật | Bằng chứng |
|---|---|---|
| M2A-01 | VERIFIED — empty v2 DRAFT/EMPTY_MANIFEST, CRUD từng bó, đặt/bỏ/xóa và history/selection đúng | `tests/backend/test_m2a.py`, `tests/browser/m2a.spec.ts`, [manual](SCST_M2A_EVIDENCE/browser-manual-saved.png) |
| M2A-02 | VERIFIED — custom BOX/limits nhập chính xác, nguồn chưa xác minh; reference khóa và detach rõ; v1 giữ tương thích | Backend/model validators, browser reference/custom tests, [backend rerun](SCST_M2A_EVIDENCE/reviewer-backend.log) |
| M2A-03 | VERIFIED — CSV UTF8/BOM/quoted names, integer g/mm, preview và apply atomic; header/row/precision/size/duplicate errors không partial | CSV adapter, backend tests, [CSV](SCST_M2A_EVIDENCE/browser-csv-import.png), [independent checks](SCST_M2A_EVIDENCE/reviewer-independent.json) |
| M2A-04 | VERIFIED — UUID snapshots immutable, list100/open/re-evaluate, reload và hai server riêng; DB/record/schema/timestamp lỗi giữ dữ liệu | [Restart](SCST_M2A_EVIDENCE/reviewer-restart.log), storage tests, independent checks |
| M2A-05 | VERIFIED — rawSTALE, empty/selection/history, stale preview, pending save/open và transport failures giữ edit mới; mobile/2D dùng được | [Browser proof](SCST_M2A_EVIDENCE/browser-proof.md), [root rerun](SCST_M2A_EVIDENCE/reviewer-browser.log), [mobile](SCST_M2A_EVIDENCE/browser-mobile-reference-fallback.png) |
| M2A-06 | VERIFIED — probe nguồn được ghi, owner chọn mẫu có nhãn, không lấy hầm giả làm hầm thực; no operational approval | [SPEC](../specs/SCST_M2A.md), provenance/UI/source guard và APP_GUIDE |
| M2A-07 | VERIFIED — build/OpenAPI/types,79 backend/13 browser/restart checks đạt; root review độc lập | [Build](SCST_M2A_EVIDENCE/frontend-build.log), [contract](SCST_M2A_EVIDENCE/contract-check.log), root rerun logs và [hướng dẫn](../APP_GUIDE.md) |

## Review độc lập và các sửa đã xử lý

Root đọc source/model/adapter/workspace và assertions browser; tự chạy lại79 backend test,13 browser test (29,3s) và smoke qua hai tiến trình. Bài browser dùng API/SQLite thật trên loopback và thư mục dữ liệu test riêng, không ghi vào DB người dùng. Root xem ảnh desktop/mobile, kiểm luồng có bảng/3D/selection cùng checked snapshot, khu vực bảng mobile cuộn riêng.

Root bổ sung190 kiểm độc lập: oracle mass đến1g và trần, CSV không partial/200–201dòng/BOM/duplicate, v1/v2 empty guard,103snapshot không ghi đè, list100 nhưng mở ID cũ được, recordJSON lỗi không hỏng record khác, SQL parameters và đường dẫn API. Lượt190 này chạy trước sửa timestamp được phát hiện ở review; phần sửa đó có test riêng và toàn bộ79 backend/13 browser/restart được chạy lại sau sửa. Không gán proof cũ cho hành vi chưa được kiểm.

Những điểm được sửa trước chốt: import/storage đặt đúng `adapters/`; đường root DB sau di chuyển; form/enum/đơn vị tiếng Việt; header-onlyCSV; số dòng vật lý với quoted newline; dữ liệu source hỗn hợp; list mount lỗi nonfatal; request revision/selection bảo toàn; không tự tạo schema vào DB có cấu trúc lạ; timestamp lưu hỏng không được làm crash date formatter, ngày hiển thị dd-mm-yyyy. Root chỉ ra các lỗi, Terra sửa source; Sol viết browser tests, root độc lập review/rerun. Root không sửa runtime trong lượt này.

Root có một lỗi test-helper: dùng sqlite context manager mà chưa đóng connection trước cleanup thư mục tạm trên Windows. Lượt đó lỗi cleanup, không được tính PASS. Đã sửa helper bằng `contextlib.closing`, chạy190 kiểm đạt và dọn đúng thư mục tạm đã tạo. App adapter vốn đóng connection trong finally. Browser fixture đầu có dòng trống thừa bị parser từ chối; đã sửa fixture và chạy lại, không nới parser. Worker ghi các invocation lỗi trong worker return.

## Giới hạn còn lại

- CSV là format import đầu tiên; chưa XLSX/PDF/OCR/quantity expansion. Tối đa200bó/1MiB, chưa importer cho manifest thật chưa được cung cấp.
- Chỉ BOX/một lớp; chưa heuristic, ổn định/tải sàn/sức bền. Phần tự nhập là khai báo, phần VINAFCO hầm/cabin/tuyến hình vẫn ước tính.
- Lưu checked snapshot, không auto-save rawdraft; mỗi lần lưu tạo bản mới. History trong tab chưa là so sánh phiên bản M2c. Danh sách chỉ100bản mới nhất; không delete/overwrite/backup/restore UI.
- Nếu timestamp một record hỏng, list báo lỗi cho tới khi dữ liệu được sửa; app không skip/reset hoặc tự sửa DB. Record tốt vẫn còn và có thể mở bằng ID qua API. Không có công cụ sửa DB/restore trong M2a; M5 giữ nhiệm vụ độ bền vận hành.
- Cảnh báo TestClient/httpx deprecation và chunkThree.js lớn còn; launcher/dependencies không thay, không lặp cold install. Không có provider call hoặc tuyên bố CVF runtime governance.

## Bàn giao

Chạy `Start-SCST.cmd`; **Phương án mới → thêm/import → đặt/chỉnh → kiểm lại → Lưu phương án → reload → Mở phương án**. Có [CSV mẫu giả lập](../examples/manifest_m2a_synthetic.csv). SQLite tại `runtime-data/scst.sqlite3` ngoài Git; giữ thư mục đó để giữ bản lưu. Bước kế tiếp là SPEC M2b; chưa dispatch M2b. Source/tài liệu chỉ commit local trong lượt này, không push thêm dữ liệu thật.
