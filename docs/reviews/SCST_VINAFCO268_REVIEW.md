# VINAFCO 268 — Review tích hợp có chọn lọc

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra-6.1-High + Sol-Medium
Reviewer: root-orchestrator

## Kết luận

Đủ sáu tiêu chí kỹ thuật của [SPEC](../specs/SCST_VINAFCO268.md). Mô hình dùng được cho hiển thị và thử bố trí hàng synthetic trong hầm ước tính, giữ mẫu M1 mặc định. Chưa có nghiệm thu nghiệp vụ, hình học hầm đo thực hoặc điều kiện sử dụng phương án thực. Đây là một lát cắt được owner cho làm sớm, không đóng M2c/M2/M3.

Root đọc source thay đổi, kiểm nguồn scan và GLB, đọc các assertion browser, tự chạy lại 63 backend test và 9 browser test; thêm109 kiểm độc lập. Root không viết source runtime của lượt tích hợp; worker Terra và Sol khác root. Root chỉ soạn authority, hồ sơ đánh giá, docs, custody và closure. Không có provider call hoặc tuyên bố kiểm runtime CVF governance.

## Đối chiếu tiêu chí

| ID | Kết quả | Bằng chứng |
|---|---|---|
| VF-01 | VERIFIED — 16 file nguồn giữ hash, PDF được đối chiếu, profile chỉ lấy trường kỹ thuật và null/ước tính; PDF/URL cá nhân không vào runtime | [Assessment](SCST_VINAFCO268_ASSESSMENT.md), [source check](SCST_VINAFCO268_EVIDENCE/source-asset-validation.json), profile và `.gitignore` |
| VF-02 | VERIFIED — profile/case/model endpoints, strict mixed binding và chuyển đơn vị bảo thủ, cả hai overage mẫu và hồi quy M1 | [63 backend tests](SCST_VINAFCO268_EVIDENCE/backend-tests.log), [109 root checks](SCST_VINAFCO268_EVIDENCE/reviewer-independent.json) |
| VF-03 | VERIFIED — GLB Y-up tịnh tiến đúng, 12 cargo mesh khớp plan, orbit/zoom/reset/pick và mờ/ẩn hình tàu | [Actual geometry](SCST_VINAFCO268_EVIDENCE/browser-geometry.json), [browser proof](SCST_VINAFCO268_EVIDENCE/browser-proof.md), source Viewer.tsx |
| VF-04 | VERIFIED — SI/SII đúng mức hàng/mớn/TTTP, giữ giới hạn chuyến thấp hơn; STALE/history/case race giữ dữ liệu; vượt2,5/17,5t kiểm đúng | Backend tests, root checks, browser case/history/race assertions |
| VF-05 | VERIFIED — nhãn nguồn/ước tính/null, lỗi network/GLB, 2D fallback và390px không tràn trang | [Mobile](SCST_VINAFCO268_EVIDENCE/browser-vessel-mobile-fallback.png), [asset failure](SCST_VINAFCO268_EVIDENCE/browser-vessel-model-failure.png), browser proof |
| VF-06 | VERIFIED — build/types/OpenAPI khớp, backend63 và browser9 đạt, root review độc lập; hướng dẫn cập nhật | [Build](SCST_VINAFCO268_EVIDENCE/frontend-build.log), [contract](SCST_VINAFCO268_EVIDENCE/contract-check.log), [root browser rerun](SCST_VINAFCO268_EVIDENCE/reviewer-browser.log), [APP_GUIDE](../APP_GUIDE.md) |

## Bằng chứng và giới hạn

- GLB227984byte, 31mesh/3506tamgiác; bbox thân từ asset khớp77,8 ×13,24 ×5,2m trong sai số float32. Toàn cảnh cao hơn vì có cabin. Boong không che lỗ hầm. Khi vào viewer, bbox toàn cảnh x[-39,8725;37,9275], y[-0,832;8,568], z[-6,62;6,62]m.
- Hầm nguồn56,405 ×10,34375 ×5,408m. Kiểm dùng56405 ×10343 ×5408mm; biên ngang nằm trong biên nguồn0,375mm mỗi phía. Hình học đó vẫn là ước tính, chưa biến thành hầm đo thực.
- Root kiểm độc lập109 điều kiện: hash nguồn, profilebinding, onboard0/1g/18,5t, biên tải±1g, strictmass, API không phục vụ nguồn và OpenAPI hiện hành. 63 backend test rerun đạt; browser9/9 rerun đạt17,0s, gồm M1 cũ5/5. Không lặp lại cold install vì dependency/launcher không đổi.
- Root đã xem ảnh desktop/mobile. Mô hình toàn tàu nhìn được và cargo nằm trong hầm; vùng bảng mobile cuộn riêng, không tràn ngang toàn trang. Mớn là marker tham chiếu, không tính nổi; màu GLB4,85m được giải thích.
- Browser lỗi đầu tiên8/9 do thông báo mạng tiếng Anh; worker đã sửa tiếng Việt, build và chạy lại9/9. Source/asset validation lần gọi đầu sai tên hàm (`validate` thay vì `validate_model`), chưa chạy phép kiểm; sửa invocation rồi validator đạt. Các lần đó không được nhận là PASS.
- Cảnh báo còn lại: Starlette TestClient/httpx deprecation; chunkThree.js lớn; NO_COLOR/FORCE_COLOR khi test. Không đổi dependency chỉ để xóa cảnh báo. Không có nghiên cứu hoặc kiểm ổn định/sức bền/hiệu lực pháp lý đăng kiểm.
- Browser test cũ ghi đè bốn ảnh M1; root giữ ảnh hồi quy mới dưới VINAFCO evidence và khôi phục byte ảnh lịch sử từ HEAD. `knowledge/_index.json` sinh khi bootstrap được giữ trong runtime bị ignore. Không nhận ảnh/test cũ thành bằng chứng mới.

## Dùng và bàn giao

Chạy `Start-SCST.cmd`, mở app rồi chọn **Xem VINAFCO 268**. Chọn cấp tham chiếu và dùng **Ẩn tàu / Hiện tàu**; cargo và các kiểm vẫn qua backend. Giới hạn chuyến32t ban đầu được giữ từ mẫu; chỉnh nó nếu muốn thử mức lớn hơn, tối đa mức hàng tham chiếu. Áp dụng nháp trước khi đổi cấp hoặc undo.

Source mới không phụ thuộc thư mục bàn giao gốc khi runtime. PDF gốc ở local, không commit/push. Source/app/docs được commit local sau gate; không công bố thêm bộ dữ liệu thật trong lượt này. Owner xem bản chạy và quyết định phản hồi nghiệp vụ; M1 và các mốc khác giữ checkpoint riêng.
