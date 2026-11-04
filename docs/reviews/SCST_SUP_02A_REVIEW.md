# SCST — SUP-02A: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

Owner quyết định merge ngày 04-11-2026. Root merge PR #1 bằng `gh pr merge --merge --match-head-commit 4f91202`, tạo merge commit `569c7ee` trên `main`.

- Người review là Claude local (root REVIEWER). Phiên này không tham gia implement; worker là Claude Cloud.
- PR: #1, nhánh `claude/sup-02a-cargo-revisions`, head `4f91202`, base `a9038c8`. Gồm 5 commit và 25 file.
- Review chạy trong worktree riêng `../SCST_review_sup02a`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | Kết quả |
|---|---|
| `python -m pytest` (backend, `SCST_DATA_DIR` tạm) | 222 passed. Baseline trước SUP-02A là 104. |
| `python tooling/export_contract.py` | Không có diff so với `contracts/openapi.json` đã commit. |
| `npm ci`, `npm run contract` | `api.ts` sinh lại khác bản commit chỉ ở EOL (autocrlf); nội dung giống hệt. |
| `npm run build` | Đạt. Chỉ có cảnh báo chunk > 500 kB, có sẵn từ trước. |
| Playwright toàn bộ (`playwright.config.ts` gốc, cổng 8766, DB tạm) | 39 passed: 36 ca cũ và 3 ca `sup02a.spec.ts`. |
| Gate `worker-return` | PASS, 7 control, 0 fail. |
| Gate `reviewer-fast` | PASS, 8 control, 0 fail. |
| CI của PR (`cvf-downstream-gates`) | SUCCESS |

## Phạm vi và vùng file

- Mọi path nằm trong vùng worker được giao.
- Không có thay đổi ở các vùng sau:
  - `services/backend/data/**`
  - `.cvf/**`
  - `scripts/cvf_gates/**`
  - `.github/**`
  - requirements, package files
  - các browser spec cũ
- Không thêm phụ thuộc.
- Không có secret hay lệnh gọi mạng/provider trong sản phẩm.
- Diff `openapi.json` dài (~3000 dòng) là nội dung thật, không phải đổi định dạng. Phần thêm gồm 18 schema mới và 5 endpoint mới; `Plan` và `CargoUnit` được mở rộng. Không schema nào bị xóa.

## Đối chiếu D1–D8

- **D1:** R0000 được dẫn xuất và không lưu. Hash là JSON chuẩn hóa đúng SPEC. Bảng chỉ thêm, ghi bằng `BEGIN IMMEDIATE`. Khi đọc, hệ thống phát lại và so hash; sai parent trả 409 và không ghi gì.
- **D2/D3:** Ba loại thay đổi đều đúng SPEC. ID bó không cấp lại vì có `next_bundle_index`. `dimension_warning` chỉ tắt khi CONFIRMED. Đủ các giới hạn, lỗi theo từng thay đổi bằng tiếng Việt. Số nguyên phải là int thật: bool và float bị từ chối.
- **D4:** Provenance có ở từng trường và từng bó ghi đè. Đơn vị dẫn xuất mang `revision_id` và trạng thái xác nhận.
- **D5:**
  - `plan_binding.bind()` là cổng chung, được gọi ở validate, lưu, mở snapshot, hai phía compare, planner, pipe-list preview, CSV preview, plan-preview và rebase.
  - Contract cũ không mở DB. Plan cũ không bị ghi lại `cargo_revision`, vì serializer bỏ trường này khi trống.
  - Giới hạn 2000 bó chỉ có hiệu lực với v2. Đã thử: m1/m2a vẫn bị chặn ở 200, pipe v1 vẫn phải đủ đúng 1076.
- **D6:** Có đủ trạng thái CURRENT, NEEDS_RECHECK, NOT_APPLICABLE. Rebase giữ vị trí bó không đổi kích thước/khối lượng, liệt kê vị trí bị bỏ, tái dùng `domain/comparison` và không ghi gì.
- **D7:** Sao lưu một lần bằng sqlite backup API (ghi file tạm rồi đổi tên, không ghi đè bản đã có). Cột được kiểm; cấu trúc lạ bị từ chối mà không reset.
- **D8:** Panel "Dữ liệu hàng", lịch sử, chi tiết provenance, form lô cập nhật và nhãn "Cần kiểm lại" đều có, kèm nút "Tạo bản theo dữ liệu mới" và so sánh. Chuyển kg/cm sang g/µm bằng chuỗi/BigInt nên chính xác tới 1 g và 1 µm. Đã xem ảnh desktop và 390px từ lần chạy tại máy: 390px không tràn ngang.

## Quyết định root cho ba điểm worker hỏi

1. **Trạng thái `REVISION_UNAVAILABLE`:** CHẤP NHẬN. Đây là lựa chọn giữ dữ liệu. Danh sách vẫn dùng được, và revision lỗi toàn vẹn không bao giờ bị tự sửa.
2. **`placed_affected` đếm mọi thay đổi** (kể cả số ống, cờ cảnh báo, xác nhận), trong khi rebase chỉ bỏ vị trí khi kích thước/khối lượng đổi: CHẤP NHẬN cho SUP-02A.
   - Số này nghiêng về thận trọng: báo nhiều hơn chứ không báo thiếu.
   - Nên làm rõ nhãn trong giao diện ở tranche sau.
3. **Dấu provenance `created` cho bó thêm do tăng `bundle_count`:** CHẤP NHẬN, vì đúng tinh thần DA03.

## Quan sát (không chặn merge)

- **O1:** Chạy toàn bộ browser suite ghi đè ảnh trong `docs/reviews/SCST_SUP_01_EVIDENCE/browser` (do `tests/browser/evidence.ts`). Đây là lỗi có từ trước SUP-02A.
  - Đề xuất sửa: một tranche nhỏ cho phép đổi helper để ghi ra thư mục chưa đóng.
  - Review này không commit ảnh bị ghi đè.
- **O2:** Màn rebase desktop liệt kê toàn bộ vị trí bị bỏ nên trang rất dài (~9600 px). Danh sách ID trong panel revision đã giới hạn 50, nhưng danh sách vị trí bị bỏ thì chưa. Nên phân trang hoặc thu gọn sau.
- **O3:** Provenance (văn bản nguồn) không nằm trong hash. Sửa tay DB chỉ bị phát hiện khi làm record không hợp lệ. Hash cấp record là quyết định SPEC cho sau.
- **O4:** Mỗi điểm vào v2 phát lại từ R0000. Với vài chục revision thì ổn; chưa có cache giữa các request.
- **O5:** Endpoint tạo/xem trước revision kiểm 1 MiB sau khi FastAPI đã parse body. Với công cụ local một người dùng thì chấp nhận được.

## Kết luận

- S2-01..S2-06 đạt về kỹ thuật, dựa trên test backend, browser chạy lại tại máy và đọc code theo D1–D8.
- Không có finding chặn và không cần sửa tại chỗ.
- Luồng S2-06 được kiểm qua `sup02a.spec.ts` chạy tại máy cùng ảnh kết quả. Root chưa tự bấm tay trên UI 8765 của người dùng.
- Nghiệm thu nghiệp vụ và quyết định merge thuộc owner.
- Sau merge, root cập nhật work order, coverage, handoff, state và memory trong một commit đồng bộ.
- SUP-02B, SUP-03 và M2d không tự mở.
