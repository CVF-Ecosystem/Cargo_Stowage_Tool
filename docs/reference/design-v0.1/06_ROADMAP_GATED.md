# 06 — Gated Roadmap v0.1 (không cam kết thời lượng)

**State:** `PROPOSED`, chưa khóa phạm vi triển khai. Roadmap ưu tiên các gate theo bằng chứng; không chuyển gate vì đến lịch dự kiến.

| Stage | Work package | Deliverables | Exit gate |
|---|---|---|---|
| G0 | Scope & sample selection | 2 cargo types được hỗ trợ, 1 loại hold đơn giản, giới hạn khẳng định; signoff product/technical | Scope Freeze |
| G1 | Data foundation | schemas, vessel/doc/hold/manifest/case, SQLite migrations, import/confirm UI, immutable snapshots, backup/restore | Data Contract PASS |
| G2 | Safety contract & deterministic validator | rule catalog, source matrix, mass invariant, geometric bounds, support rule profiles, run reports, engineering unknowns | Safety Contract PASS |
| G3 | Packing/optimization prototype | 2.5D solver, hard constraints, objective options, reproducible reports, golden cases, timeout behavior | Solver Evidence PASS |
| G4a | Interactive 3D/UI | manifest and hold screens, plan viewer, select/move/revalidate, unplaced/issues, status labels | UI/E2E PASS |
| G4b | AI + CVF bounded integration | AI intake clarification, restricted tools, CVF bridge spike and fail-closed integration, audit/approval binding | Governance PASS |
| G5 | Field pilot | compare 2–3 real completed shipments (with redacted data) and reviewer feedback; refine supported profiles | Field Review decision |

G4a có thể bắt đầu sớm bằng mock/stub geometry khi API contract của G1 ổn định; G4b không cần chặn tool offline core. G3 chỉ chạy bằng dữ liệu giả lập/anonymized cho đến khi kỹ sư xác nhận test basis.

## Work ordering tối ưu

1. G0 → G1 data and precision → G2 hard constraints.
2. Song song: 3D spike với hình hộp đơn giản và solver spike synthetic, **không** gọi đó là sản phẩm.
3. G3 optimizer chính sau khi G1/G2 có test.
4. G4a frontend nối API khi dữ liệu ổn định; G4b agent integration chỉ sau khi chính sách/backend đã có.
5. G5 expert field pilot; scope mở rộng nếu evidence đạt.

## Những rủi ro bắt buộc review trước khi tiến tiếp

- Rủi ro dữ liệu tải cho chuyến khác với giấy chứng nhận.
- Hình học hầm gần đúng bỏ sót chướng ngại / mặt cắt / giới hạn đáy.
- Kê đỡ, chêm lót và dịch chuyển hàng không chứng minh được bằng box packing.
- Solver cho plan nhìn đẹp nhưng vi phạm điều kiện kỹ thuật chưa encode.
- AI extraction và untrusted documents tạo giả định sai.
- CVF guard có mặt trong code không bảo đảm integrated behavior.

## Quyền khóa gate

- G0: owner.
- G1–G4: kỹ thuật + reviewer độc lập, lưu test evidence.
- G2/G5: chuyên gia có năng lực chịu trách nhiệm về phạm vi kiểm tra kỹ thuật và điều kiện vận hành.
- Không phải mọi gate đều cần cùng một cá nhân; tên và vai trò phải được điền thật tại runtime.

## Tuyên bố tiến độ tại ngày soạn

Chỉ có **bản thiết kế dự thảo**. Không có bằng chứng rằng G0...G5 đã PASS. Không tự nâng trạng thái sang BUILD_READY/INTEGRATED vì đã viết xong tài liệu.
