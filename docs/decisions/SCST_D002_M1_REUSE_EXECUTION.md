# SCST-D002 — Tiếp tục M1 theo SPEC và kế hoạch tái sử dụng

Status: ACTIVE

Ngày: 31-10-2026. Người quyết định phạm vi: owner SCST; người ghi: orchestrator.

Sau khi hỏi việc sửa ba góp ý và kế hoạch chuyển M1, owner chỉ đạo: "Bạn là orchestrator/reviewer; cho phép tạo subagent Terra 6.1 High, việc khó thì gọi Sol-Medium, để làm worker. Tiếp tục công việc".

Trong ngữ cảnh SPEC v0.2 và danh mục đã được giải thích/recheck, chỉ đạo này cho phép tiếp tục **M1 theo SPEC v0.2, D1–D7 và M1-01…M1-09**, với lựa chọn nguồn/đích ở Phụ lục. Orchestrator lập WORK_ORDER có giới hạn trước BUILD; Terra 6.1 High là worker, Sol-Medium chỉ gọi khi có phần khó cụ thể. Root giữ điều phối/review, không nhận công việc của worker là đã nghiệm thu.

Nguồn tái sử dụng: `archive/2026-10-31/paused-m1/`, tree `e4004e274fc28aa143ce0e300b6c060d1cb1e5a0`. Giữ archive nguyên bytes; không khôi phục hồ sơ thi công, dependency cache, log hoặc PID cũ vào app. Các phần sinh tự động phải sinh lại từ backend mới.

Ủy quyền bao gồm cài dependency công khai cần cho M1, build/test và chạy synthetic demo local để kiểm; local commit do orchestrator/commit steward giữ. Không gồm publish/push, AI/provider/key, dữ liệu thực, giải pháp nhiều tầng, solver, persistence hoặc phạm vi M2–M5. Các tính năng này chưa được cấp thêm quyền.

Đây là chấp thuận hướng/SPEC để thi công M1 trong phạm vi trên, chưa là nghiệm thu sản phẩm hoặc chấp thuận phương án chất xếp thực tế. Sau worker return, root review kỹ thuật và chứng minh đủ acceptance trước khi owner xem giá trị demo.
