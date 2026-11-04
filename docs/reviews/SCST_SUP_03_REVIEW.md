# SCST — SUP-03: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

- Người review là Claude local (root REVIEWER), không tham gia implement.
- PR: #3, nhánh `claude/sup-03-packing-views` (head `0d8bdff`), xếp chồng lên PR #2 (`claude/sup-02b-vessel-profile`).
- Worker là hai phiên Claude Cloud.
  - Phiên đầu dừng lúc 15:06Z vì chạm giới hạn sử dụng 5 giờ của tài khoản; phần chưa commit bị mất, chỉ còn `f669e67`.
  - Root tạo routine chạy tiếp lúc 17:50Z. Phiên đó merge bản sửa root `9f8969e` của SUP-02B, rồi commit và push theo từng mốc.
- Review chạy trong worktree riêng `../SCST_review_sup03`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.
- Owner xem lại sáng 05-11 rồi quyết định merge. Root đổi base PR #3 sang `main`, xác nhận tree sau merge trùng tree đã test (`e66c2cc`), CI pass, rồi merge với `--match-head-commit 0d8bdff`, tạo merge commit `164dce5`.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | Kết quả |
|---|---|
| `python -m pytest` | 597 passed |
| `python tooling/export_contract.py` | Không có diff so với `contracts/openapi.json` đã commit. |
| `npm ci`, `npm run contract`, `npm run build` | Đạt. `api.ts` chỉ khác ở EOL. |
| Playwright toàn bộ (config gốc, cổng 8766, DB tạm) | 46 passed: 42 ca cũ và 4 ca `sup03.spec.ts`. |
| `git status` sau khi chạy browser | Sạch: không file nào dưới `docs/reviews/` thay đổi. |
| Gate `worker-return` | PASS, 7/7 |
| Gate `reviewer-fast` | PASS, 8/8 |
| CI của PR | SUCCESS |
| Vùng cấm so với admission `80ee61e` | Không thay đổi: `services/backend/data`, `.cvf`, `scripts`, `.github`, specs, work orders, CVF_SESSION |

## Đối chiếu D1–D6

- **D1:**
  - `domain/packing` là hàm thuần, toàn bộ là số nguyên µm.
  - OD được đổi từ chuỗi thập phân bằng phép đổi chính xác.
  - Kiểm nằm trong mặt cắt bằng số nguyên nhân đôi, nên OD lẻ không cần làm tròn.
  - Bước hàng HEX dùng `isqrt`. Hai hàng HEX kề nhau có thể chồng nhau dưới 1 µm do làm tròn; worker đã ghi rõ, và đây chỉ là hình hiển thị.
- **D2:**
  - Có đủ các kiểm `count`, `od_fit`, `envelope_fit`, `slack_loose`.
  - Mã lý do có `OD_MISSING`, `OD_EXCEEDS_SECTION` (worker thêm, hợp lý), `PIECES_DO_NOT_FIT` kèm số ống tối đa vừa, `INPUT_INVALID`, `ENVELOPE_LOOSE` và `SOURCE_WARNING`. `SOURCE_WARNING` không đổi trạng thái, tức là giữ dữ liệu.
  - Một nhóm mâu thuẫn không chặn các nhóm khác.
- **Kết quả R0000:**
  - 28/31 nhóm và 1060/1076 bó ở trạng thái DETAILED; mọi nhóm DETAILED có số ống dẫn xuất bằng số ống nguồn.
  - 3 nhóm còn lại (R022, R031, R032, gồm 16 bó) là ENVELOPE_ONLY: 5 ống OD 219,1 mm không vừa mặt cắt 438,2 mm vuông, tối đa 4 ống.
  - Đây chính là 16 bó roadmap đã ghi "cần xác minh envelope", tức là kết quả dẫn xuất khớp độc lập với cảnh báo nguồn.
- **D3:** `GET /api/cargo-revisions/{id}/packing` chỉ đọc. Revision lỗi toàn vẹn bị từ chối như SUP-02A. JSON của Plan và snapshot cùng hash R0000 không đổi; có test so byte.
- **D4:**
  - Ba cách nhìn dùng InstancedMesh.
  - Chỉ nhóm `s.pack` được dựng lại. Renderer, scene, GLB, camera, bó đang chọn và mesh khối bao giữ nguyên uuid (kiểm bằng diagnostics).
  - Giới hạn 60 000 ống, có thông báo khi vượt.
  - Nhấp chuột trả về ID bó.
  - Thời gian dựng đo được (`sup03-timing.json`): chế độ chi tiết 36 ms cho 1060 bó, 21 146 ống; chế độ giản lược 55 ms. Không có tuyên bố về FPS.
- **D5:** Bảng có thêm cột packing và bộ lọc trạng thái; có panel chi tiết bó. Nhấn lý do thì mở nhóm trong "Dữ liệu hàng".

## Quyết định root cho các điểm worker hỏi

1. **Revision chỉ sửa OD không làm phương án cũ "Cần kiểm lại".** CHẤP NHẬN, và sửa lại cách hiểu của SPEC.
   - Lý do: OD không thuộc dữ liệu đơn vị của Plan (chỉ có kích thước và khối lượng bó). Phương án vẫn hợp lệ về hình học và khối lượng; chỉ cách nhìn packing đổi.
   - Luồng S3-05 trong test đã đổi thành sửa OD kèm khối lượng bó; worker đã ghi rõ thay đổi này.
   - Muốn sửa OD cũng đánh dấu cần kiểm lại thì phải có SPEC revision mới, vì sẽ đổi hash của đơn vị.
2. **Quy ước yaw của trục mặt cắt** (xoay ngược chiều kim đồng hồ quanh góc nhỏ nhất của khối bao): CHẤP NHẬN. Quy ước này chỉ ảnh hưởng vị trí hiển thị của cách xếp không đối xứng bên trong khối bao.
3. **`ENVELOPE_LOOSE` tính cả trường hợp dư đúng bằng 1 OD** (R002, R003): CHẤP NHẬN, vì đúng chữ của SPEC D2.1 ("≥ 1 OD").

## Quan sát (không chặn merge)

- **O8:** Ống được dựng với 12 đoạn tròn. Đủ cho cách nhìn tổng thể; khi soi gần có thể thấy cạnh gãy.
- **O9:** Cả hai phiên cloud dùng Sonnet cho phần khó, như đã cho phép. Lần chạy tiếp sau khi chạm giới hạn làm tốn thêm usage. Bài học: worker phải commit theo mốc ngay từ đầu.

## Kết luận

- S3-01..S3-05 đạt về kỹ thuật. Không có finding chặn và không cần sửa tại chỗ.
- Thứ tự merge: PR #2 (SUP-02B) trước, sau đó PR #3. Sau khi PR #2 vào main, root đổi base của PR #3 sang main (`gh pr edit 3 --base main`), chạy lại CI rồi mới merge.
- Sau merge, root làm bước kiểm tra tích hợp trước M2d theo roadmap.
- Nghiệm thu nghiệp vụ, cách xếp thực tế và M2d thuộc owner.
