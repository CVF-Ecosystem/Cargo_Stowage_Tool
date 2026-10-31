# Work order: vòng local REVIEW_ONLY

**Đầu vào chính:** SCST-REVIEW-0.3. **Mục tiêu:** phản biện và xác minh trước khi chốt Final Baseline, roadmap, treeview và triển khai.

## 1. Phạm vi được thực hiện

- Đọc package, ảnh, R2, baseline/reference lịch sử và quy định của workspace/repo có thật.
- Khảo sát OS/runtime/dependencies/repo/CVF bằng thao tác không thay đổi ứng dụng.
- Kiểm checksum, chạy suite và probes có sẵn trong vùng thử riêng; có thể viết probe kiểm chứng giới hạn cụ thể khi cần, ghi rõ mã/lệnh và giới hạn.
- Tạo báo cáo, log, inventory dữ liệu còn thiếu, đề nghị chỉnh contract và tiêu chí nghiệm thu.

Chưa triển khai skeleton ứng dụng, schema DB/migration, UI, production solver, CVF mutation hoặc thay repo core. Chưa chốt roadmap/treeview; có thể nêu tác động kiến trúc và đề nghị để vòng sau quyết định. Nếu có repo sẵn, mô tả cây thực đang có và commit; không tạo cây mới để làm đầy báo cáo.

## 2. Thứ tự review

1. Kiểm checksum v0.3. Xác nhận v0.2 ZIP lịch sử đúng SHA trong source register; không sửa nó.
2. Đọc README/MASTER/REVIEW_R3/DECISION_LOG và docs. Chỉ dẫn triển khai trong v0.2 history không có hiệu lực trong vòng này.
3. Xem ảnh theo tên tệp 1.jpg, 2.jpg, 3.jpg. Phân biệt dữ kiện thấy được, điều phải hỏi và điều không thể suy ra. Ảnh không là manifest hoặc bộ kích thước.
4. Chạy `tooling/replay_review_checks.py` theo evidence report; giữ kết quả ngoài package. Báo đúng các schema gaps đã tái lập; không gọi đó là lỗ hổng runtime.
5. Đối chiếu CVF ở commit được baseline v0.2 yêu cầu `ebf31b9f5c42e4de58f40a434409c3441a5d8383` nếu nguồn có sẵn. Ghi actual SHA, license, API/export/dependency và khác biệt. Nếu không có repo, ghi BLOCKED_BY_SOURCE, không suy ra API canonical hoặc sửa core.
6. Xác minh xem các case nghiệp vụ cần cargo units/profile/geometry/precision nào. Dùng mẫu CASE_INTAKE; chưa có mẫu thì ghi thiếu, không tự tạo profile thật từ ảnh.
7. Phản biện các đề nghị v0.3, đặc biệt boundary TP/MVP, grams, external review, critical-field provenance và hình học/support.

## 3. Đầu ra cần trả

| Đầu ra | Nội dung |
|---|---|
| LOCAL_REVIEW_REPORT.md | Kết luận từng R2-01…08 và quyết định v0.3; file/line/commit hoặc data evidence, ảnh hưởng, đề nghị |
| ENVIRONMENT_AND_CVF_REPORT.md | Môi trường thực, repo thật, CVF compatibility; phần chưa truy cập phải ghi rõ |
| CONTRACT_DELTA_REVIEW.md | Các schema/domain/persistence/API cần đổi trước freeze; phân biệt yêu cầu đã có với phần mới; không phải code đã triển khai |
| OPEN_DECISIONS.md | Câu hỏi owner/chuyên môn, lựa chọn, bằng chứng và mốc bị chặn; không hỏi lựa chọn routine không ảnh hưởng nghiệp vụ |
| ACCEPTANCE_REVIEW.md | Mapping TP/MVP và LAT/ADM/ER/MB; case thật cần có, oracle, tham số hiệu năng/capacity fidelity cần thống nhất trước test |
| EVIDENCE/ | Exact commands, timestamp, source/build/input hashes, expected/actual/log và giới hạn |

Dùng `templates/LOCAL_REVIEW_RESPONSE.md`. Một kết luận không có bằng chứng phải được ghi là nhận định hoặc đề nghị. Schema nhận một chuỗi actor không chứng minh identity. Hash khớp không chứng minh nguồn là thật. 86 tests đạt không thay các test backend/solver/UI/CVF chưa chạy.

## 4. Điểm dừng của vòng này

Trả báo cáo và danh sách quyết định để owner cùng Web Agent xử lý. Sau khi phản biện được giải quyết mới chốt Final Baseline, roadmap và treeview dự kiến. Không tự đổi từ review-only sang triển khai vì work order cũ trong v0.2 nói được phép dựng skeleton.
