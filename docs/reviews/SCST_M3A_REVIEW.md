# SCST — M3a: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

- Người review là Claude local (root REVIEWER), không tham gia implement.
- PR: #6, nhánh `claude/m3a-column-stacking` (base `6dac6bd`).
  - Vòng 0 review tại head `8d205ef`.
  - Vòng sửa 1 review tại head `1f8c26e`.
- Root merge theo quyền owner giao, sau khi chạy lại đầy đủ tại máy: `gh pr merge --merge --match-head-commit 1f8c26e`, tạo merge commit `9a98cb8` trên `main`.
- Review chạy trong worktree riêng `../SCST_review_m3a`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | Vòng 0 (`8d205ef`) | Vòng sửa 1 (`1f8c26e`) |
|---|---|---|
| `python -m pytest` | 726 passed | 734 passed |
| `python tooling/export_contract.py` | Không có diff | Không có diff |
| `npm ci`, `npm run contract`, `npm run build` | Đạt; `api.ts` chỉ khác EOL | Đạt; `api.ts` chỉ khác EOL |
| Playwright toàn bộ (config gốc, cổng 8766, DB tạm) | 55 passed | 55 passed |
| `git status` sau khi chạy browser | Sạch | Sạch |
| `tooling/integration_check_pre_m2d.py` | 29/29 PASS | 29/29 PASS |
| Gate `worker-return` | PASS, 7/7 | PASS, 7/7 |
| Gate `reviewer-fast` | — | PASS, 8/8 |
| CI của PR | SUCCESS | SUCCESS |

Phạm vi diff không đụng `services/backend/data`, `.cvf`, `scripts`, `.github`, specs/work orders, tooling, requirements/package, hash revision hay định dạng lưu trữ. Contract chỉ thêm trường mới.

### Kiểm độc lập của root (script riêng, gọi qua API)

**Baltimore 1076 bó trong VINAFCO VR-SII:**

| Bộ xếp | Đặt được | Cột | Tầng tối đa | Kết quả kiểm | Thời gian `preview` (vòng 0 → vòng 1) |
|---|---|---|---|---|---|
| `guillotine-single-layer-v1` | 167, còn 909 `HEURISTIC_NO_SPACE` (như trước) | 167 | 1 | `RULES_CHECKED`, 0 lỗi | 0,06 s → 0,03 s |
| `columns-v1` | **1076/1076** | 98 | 18 | `RULES_CHECKED`, 0 lỗi | 0,53–0,65 s → 0,05 s; HTTP 1,1 s → 0,1 s |

Chạy hai lần cho JSON giống hệt từng byte.

**Tấn công rule đỡ** trên một ứng viên hợp lệ:

| Ca | Kết quả |
|---|---|
| z ± 1 mm | `SUPPORT_LEVEL_MISMATCH` (kèm `OVERLAP`) |
| Bỏ bó đỡ, hoặc bó tự đỡ chính nó | `SUPPORT_MISSING` |
| Sai chỉ số tầng | `LAYER_INDEX_INVALID` |
| Xóa bó đỡ khỏi plan | `SUPPORT_MISSING` |
| Không có cờ `stacking`, hoặc `SINGLE_LAYER` | `LAYER_UNSUPPORTED`, như cũ |

**Plan cũ:** không có khóa `stacking`, và validate cho JSON giống hệt từng byte.

**3D trên Windows:** ảnh chụp của luồng M3A-05 cho thấy:
- 1.125,55 / 3.517,5 tấn đã xếp, `RULES_CHECKED`;
- khung nhìn phủ kín hầm theo cột;
- số mesh 3D bằng số vị trí, và bó tầng trên nằm đúng z.

Báo cáo, XLSX và danh sách "Mất đỡ" khi rebase cũng được kiểm trong cùng spec.

## Quyết định của root

- **(a) Revision chỉ sửa OD giữ CURRENT; (b) provenance nguồn nằm ngoài hash.** Ghi lại theo yêu cầu của SPEC, không đổi.
- **D2.1, mức đỡ:** chấp nhận quy tắc `(support_top_um + 999) // 1000 == z_mm`.
  - SPEC D2.1 (khớp theo µm) mâu thuẫn với D3.1 (z tăng bằng chiều cao làm tròn lên mm) khi chiều cao không chẵn mm, như bó Baltimore 504,9 mm.
  - Quy tắc này chính xác với đơn vị mm nguyên, để khe hở dưới 1 mm và không bao giờ cho bó lún vào nhau.
- **M3A-05, rebase:** chấp nhận cách bỏ dây chuyền với lý do `SUPPORT_LOST`.
  - Ứng viên rebase luôn đúng hình học đỡ và lưu được.
  - Số "bị bỏ khi rebase" ở danh sách khớp với rebase thật.
  - Plan một tầng không bị ảnh hưởng.
- **Vòng sửa 1** (gửi qua comment PR, cùng ngân sách, không reset):
  - **R1, D4.1:** list ống mặc định "Nhiều tầng theo cột (thử nghiệm)"; plan khác giữ "Một tầng (như cũ)"; lựa chọn của người dùng được giữ.
    - Root cho phép mở rộng phạm vi: thêm đúng một dòng `selectOption("guillotine-single-layer-v1")` trước bước xếp thử trong các spec cũ dựa trên mặc định cũ.
    - Các dòng đó: `display-units.spec.ts:123`, `m2b.spec.ts:87`, `m2b.spec.ts:193`, `m2d.spec.ts:170`, `sup01.spec.ts:146`.
    - Root kiểm lại: diff spec cũ chỉ gồm 5 dòng thêm, không đổi hay xóa assertion nào.
  - **R2, O-M3A-1:** khi đổi case hoặc phương tiện, Plan nhận giới hạn chuyến của chính case đó.
    - Có thông báo "Giới hạn chuyến theo cấp …: … tấn; vẫn có thể chỉnh…".
    - Chặn chuyển khi hàng đã có trên tàu vượt giới hạn chứng nhận hoặc giới hạn chuyến mới.
    - Trước đây trang mới giữ giới hạn demo 32 t nên chỉ xếp được 22/1076 bó. Nay trang mới xếp đủ 1076 bó mà không phải nhập tay.
    - Không spec cũ nào bị sửa cho R2.
  - **R3, tăng tốc phép kiểm giao nhau** (`af29e67`, Sonnet high):
    - Root đã hủy R3 sau khi đo lại lúc máy rảnh, nhưng lệnh hủy đến sau khi commit đã push. Worker revert ở `50292e0` rồi khôi phục ở `8d6021f`; root kiểm diff rỗng so với `af29e67`.
    - Root review và giữ lại vì phép quét theo x cho đúng tập cặp và thứ tự `(i, j)` của vòng lặp cũ (`max(lo) < min(hi)` trên từng trục).
    - Hộp rỗng bị bỏ qua đúng với định nghĩa `overlaps` cũ, vốn không bao giờ báo giao cho hộp rỗng.
    - `test_m3a_perf.py` so khớp từng byte với vòng lặp cũ trên Baltimore và dữ liệu ngẫu nhiên.
- **Phân công model** đúng chỉ định của owner: Haiku 5.5 high cho R1 và R2, Sonnet 5.5 high cho R3. Lead Opus 5.5 review trong phiên cloud.

## Đối chiếu M3A-01..05

| ID | Kết luận | Căn cứ |
|---|---|---|
| M3A-01 | VERIFIED | `stacking` tùy chọn, bỏ khỏi JSON khi trống; plan và báo cáo cũ giữ nguyên byte; `SINGLE_LAYER` và thiếu cờ vẫn báo `LAYER_UNSUPPORTED`. |
| M3A-02 | VERIFIED | Năm mã lỗi mới đều có ca dương và âm (33 test rules cộng tấn công của root). Phủ 90% tính bằng µm² nguyên. Mọi điểm vào đều dùng `evaluate`. |
| M3A-03 | VERIFIED | `columns-v1` tất định, đặt 1076/1076 không lỗi hình học, mất 0,05 s; đơn vị không xếp có lý do (`STACK_HEIGHT` mới). |
| M3A-04 | VERIFIED | Ô chọn cách xếp (mặc định nhiều tầng cho list ống), cột "Tầng", panel bó đỡ, 3D đúng z, 2D "×N", báo cáo và XLSX có cảnh báo nhiều tầng; chạy được ở 390px; contract và `api.ts` đã sinh lại. |
| M3A-05 | VERIFIED | Luồng mở list → xếp nhiều tầng → áp dụng → lưu → mở lại → báo cáo/XLSX → revision → cần kiểm lại → bản mới bỏ dây chuyền `SUPPORT_LOST`; toàn bộ test cũ đạt; kiểm tra tích hợp 29/29; `docs/reviews/` không đổi khi chạy browser. |

Nghiệm thu nghiệp vụ là phần riêng của owner.

## Quan sát còn mở (không chặn)

- **O-M3A-2:** 2D chỉ hiện bó trên cùng của mỗi cột, có nhãn "×N".
- **O-M3A-3:** khe hở dưới 1 mm giữa các tầng chưa được mô hình hóa thành kê chèn.
- **DA03:** tải chồng, tải sàn, chằng buộc và ổn định chưa kiểm; báo cáo và danh sách "chưa kiểm" đều ghi rõ.
- **M3b** (case thực, hầm đã đo, tải chồng) thuộc owner.
- **MVP:** sẵn sàng để owner dùng thử và góp ý.
