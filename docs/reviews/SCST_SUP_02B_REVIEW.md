# SCST — SUP-02B: review độc lập của root

Status: ACCEPTED_TECHNICAL
Risk: R2
Worker: Claude Cloud implementation worker
Reviewer: root-independent-implementation-reviewer

- Người review là Claude local (root REVIEWER). Phiên này không tham gia implement; worker là Claude Cloud.
- PR: #2, nhánh `claude/sup-02b-vessel-profile`.
  - Head lúc worker trả về là `94cb628`, base `ab0ae69`.
  - Root sửa tại chỗ thêm commit `9f8969e`.
- Review chạy trong worktree riêng `../SCST_review_sup02b`. DB thử dùng `SCST_DATA_DIR` tạm, cổng 8766. Không chạm DB người dùng hay cổng 8765.
- Owner xem lại sáng 05-11 rồi quyết định merge. Root merge PR #2 bằng `gh pr merge --merge --match-head-commit 9f8969e`, tạo merge commit `de2aeea` trên `main`.

## Chạy lại tại máy (Windows, config gốc của repo)

| Kiểm | Kết quả |
|---|---|
| `python -m pytest` tại `94cb628` | **1 lỗi**, 501 pass. `test_temp_dirs_and_junk_ignored` chỉ lỗi trên Windows; xem R1. |
| `python -m pytest` tại `9f8969e` sau khi sửa | 503 pass: 502 test cũ và 1 test mới của root. |
| `python tooling/export_contract.py` | Không có diff so với `contracts/openapi.json` đã commit. |
| `npm ci`, `npm run contract`, `npm run build` | Đạt. `api.ts` chỉ khác ở EOL. |
| Playwright toàn bộ (config gốc, cổng 8766, DB tạm) | 42 passed: 39 ca cũ và 3 ca `sup02b.spec.ts`. |
| `git status` sau khi chạy browser (S2B-06) | Không file nào dưới `docs/reviews/` thay đổi. O1 đã được sửa thật. |
| Gate `worker-return` | PASS, 7/7 |
| Gate `reviewer-fast` | PASS, 8/8 |
| CI của PR | SUCCESS |
| `services/backend/data/**` | Không đổi byte nào (`git diff --quiet`). |

## Phạm vi và vùng file

28 file, tất cả trong vùng worker được giao, gồm cả D8 (`tests/browser/evidence.ts` và đường dẫn ảnh trong `sup02a.spec.ts`).

Không có thay đổi ở:

- `services/backend/data/**`
- `.cvf/**`
- `scripts/cvf_gates/**`
- `.github/**`
- requirements, package files

Không thêm phụ thuộc: GLB được đọc bằng `struct`/`json` của thư viện chuẩn, không có `python-multipart`. Không có secret hay lệnh gọi mạng.

## Đối chiếu D1–D8

- **D1:** Contract `scst.vessel-profile.v1` dùng pydantic, lỗi theo từng trường bằng tiếng Việt. VINAFCO268 v1 được dẫn xuất chỉ đọc từ `profile.json` gốc. Ba route `/api/vessels/vinafco268` được giữ byte-identical: worker so hash response với bản gốc `ab0ae69`, và có test.
- **D2:** Phép đổi tọa độ thuần với yaw ∈ {0, 90, 180, 270}.
  - Bốn điểm mốc góc sàn hầm VINAFCO đạt PASS. Sai số lớn nhất 0,375 mm theo trục rộng, đúng bằng phần lõm vào hai bên có trong số liệu gốc (10,34375 m so với 10 343 mm).
  - Hộp bao của `model.glb` thật sau phép đổi chứa hộp hầm.
  - Nếu FAIL thì không lưu.
- **D3:**
  - Kho file chỉ ghi thêm: ghi thư mục tạm rồi đổi tên một lần, ghi file bằng chế độ `xb`, kiểm sha256 khi đọc, không tự sửa.
  - Sai version hoặc trùng built-in trả 409.
  - Giới hạn: profile JSON 256 KiB, GLB 20 MiB, thân yêu cầu 28 MiB, tối đa 50 version và 50 id.
- **D4:**
  - `VesselReference` có thêm `profile_version` và `profile_sha256`, bị bỏ khỏi JSON khi trống, nên phương án VINAFCO vẫn byte-identical.
  - `plan_binding.bind()` gọi `check_reference` ở mọi điểm vào: kiểm sha, hầm, case và giới hạn tải. Model pydantic chỉ kiểm cấu trúc.
- **D5:** Có đủ 6 endpoint mới, kể cả endpoint dựng phương án theo case dùng chung với route VINAFCO.
- **D6:**
  - Khung chọn tàu và case, biểu mẫu nhập JSON + GLB có xem trước (sai số từng landmark, hộp bao). "Tạo profile" chỉ bật khi lần xem trước hợp lệ đúng nội dung đang có.
  - `Scene.tsx` đã bỏ các hằng VINAFCO; tên mesh thân tàu, vị trí GLB và mốc mớn nước lấy từ khối `viewer` do server trả.
- **D8:** Ảnh test ghi vào `SCST_EVIDENCE_DIR` hoặc thư mục tạm theo từng lần chạy. Không assertion nào đổi.

## Sửa tại chỗ của root

**R1 — Windows, sửa ở commit `9f8969e`.**

- **Lỗi:** `os.rename` ghi được lên một thư mục `vN` rỗng sót lại trên POSIX nhưng báo lỗi trên Windows. Trên máy owner, một thư mục như vậy sẽ chặn vĩnh viễn việc tạo version N: báo "phiên bản kế tiếp phải là N", nhưng tạo bản N luôn lỗi.
- **Vì sao cloud không thấy:** test cloud chạy trên Linux nên pass.
- **Cách sửa:** thư mục sót lại *rỗng* (không phải một version) được xóa một lần rồi đổi tên lại. Thư mục không rỗng không bao giờ bị đụng tới và vẫn trả xung đột; có test mới cho trường hợp này.
- **Kết quả:** backend Windows 503/503.

## Quyết định root cho các điểm worker hỏi

1. **Quy ước gốc GLB tổng quát** (gốc ở sống tàu, giữa chiều dài, đường tâm; X dọc tàu, Y lên, Z ngang): CHẤP NHẬN cho SUP-02B, với giới hạn đã ghi.
   - Mốc mớn nước của một GLB có gốc khác có thể lệch mà vẫn qua kiểm điểm mốc và hộp bao.
   - Ghi vào SPEC sau, khi nhận profile tàu thật thứ hai.
2. **Băm lại profile và GLB ở mỗi lần bind:** CHẤP NHẬN cho công cụ local một người dùng. Thêm bộ nhớ đệm là việc sau.
3. **Built-in đứng cuối danh sách, sau profile người dùng mới nhất:** CHẤP NHẬN.

## Quan sát (không chặn merge)

- **O6:** Khóa giữa các tiến trình dùng `fcntl`, không có trên Windows. Trên Windows chỉ có khóa luồng cộng với quy tắc đổi tên không ghi đè. Như vậy đủ cho một tiến trình uvicorn local.
- **O7:** Ảnh bằng chứng chụp cả trang, mỗi ảnh khoảng 0,8–0,9 MB.

## Kết luận

- S2B-01..S2B-06 đạt về kỹ thuật sau sửa R1.
- Owner xem và quyết định merge PR #2 trước, rồi đến PR SUP-03 xếp chồng.
- Nghiệm thu nghiệp vụ, số đo hầm thực và profile tàu thật thứ hai thuộc owner.
