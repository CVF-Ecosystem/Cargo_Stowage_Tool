# SCST — Review đơn vị hiển thị thực tế

Status: REVIEWED_FOR_OWNER
Risk: R2
Worker: Terra-6.1-High + Sol-Medium
Reviewer: root-orchestrator

Đạt bốn tiêu chí [SPEC](../specs/SCST_DISPLAY_UNITS.md): mô hình, bảng, editor và so sánh dùng **kg/cm/m**, số tổng giữ tấn tối đa hai số lẻ. Ví dụ bó nguồn hiển thị **911 kg**, **640 × 34 × 30 cm**. Đây là làm tròn trình bày, không cấp dung sai hình học hoặc khối lượng.

| ID | Kết quả và bằng chứng |
|---|---|
| DU-01 | VERIFIED — nhãn/đơn vị/rounding đồng bộ; [mô hình](SCST_DISPLAY_UNITS_EVIDENCE/browser/root-live-restored-167.png), [so sánh](SCST_DISPLAY_UNITS_EVIDENCE/browser/root-live-comparison.png), [mobile](SCST_DISPLAY_UNITS_EVIDENCE/browser/source-mobile-fallback.png) |
| DU-02 | VERIFIED — chỉ trường thực sự sửa đổi Plan; số gốc chưa sửa giữ qua yaw/context/requirement/save/reopen, semantic revert/late rebase và thứ tự placements giữ; [oracle độc lập](SCST_DISPLAY_UNITS_EVIDENCE/root-numeric.json), [browser](SCST_DISPLAY_UNITS_EVIDENCE/root-browser.log) |
| DU-03 | VERIFIED — chênh dưới mức hiển thị có nhãn dưới 1 kg/cm, không giả thành bằng nhau; API/diff/count/provenance vẫn nguyên; [browser return](SCST_DISPLAY_UNITS_EVIDENCE/browser-return.md), [chi tiết](SCST_DISPLAY_UNITS_EVIDENCE/browser/compare-small-delta.png) |
| DU-04 | VERIFIED — build, 31 browser, packaged VINAFCO 167 bó và dữ liệu nguồn/SQLite nguyên; [build](SCST_DISPLAY_UNITS_EVIDENCE/root-build.log), [live](SCST_DISPLAY_UNITS_EVIDENCE/root-live.json), [integrity](SCST_DISPLAY_UNITS_EVIDENCE/root-integrity.json), [source manifest](SCST_DISPLAY_UNITS_EVIDENCE/reviewed-source-manifest.json) |

Admission `0fc26e6`, BUILD acknowledgment `adae04e`, base `232807d9568291c82f424900d83f2ae7ec24bb9c`. Root đọc source/đối chiếu test và ảnh, tự chạy **6.837 đối chiếu**: kỳ vọng BigInt độc lập cho rounding/conversion, 120 Plan có phần lẻ, untouched/exact edits/revert/in-flight rebase/rename/placement order và source 1.076 bó. Helper thực được trích nguyên bằng TypeScript AST, expected Plan là copy sửa đúng trường theo case; không dùng output AI làm oracle. [Script](SCST_DISPLAY_UNITS_EVIDENCE/root-numeric.cjs). Tính toán và kiểm backend không đổi; tái sử dụng 104 backend test của M2c, không nhận đã chạy lại trong lượt này.

Full browser **31/31 đạt 1,2 phút** trên build `index-DXRJy6j_.js`. Assertion source mới được siết từ hơn 100 sang đúng 167 sau lúc bắt đầu full run, nên root chạy riêng case đó trên file cuối, **1/1 đạt 8,3 s** ([log](SCST_DISPLAY_UNITS_EVIDENCE/root-source-final.log)). Sau review ảnh, root sửa đúng một text node trợ giúp editor để bỏ nhấn mạnh phần lẻ nhỏ; Sol review độc lập trong [local wording review](SCST_DISPLAY_UNITS_EVIDENCE/browser/local-wording-review.md). Logic không đổi. Root build cuối `index-Bgkupcoy.js`, chạy lại focused nhập/lưu/mở **1/1 đạt 8,6 s** ([log](SCST_DISPLAY_UNITS_EVIDENCE/root-wording-focused.log)) và live 167 bó. Không lặp toàn bộ kiểm không bị ảnh hưởng.

Worker phát hiện và xử lý rebase draft mới trong lúc validation chờ, để số làm tròn chưa sửa không ghi đè dữ liệu; [worker return](SCST_DISPLAY_UNITS_EVIDENCE/worker-return.md). Sol focused ban đầu 3/3, affected 10/11: một expectation đã lấy số của ST-001 để revert ST-002. Đã sửa đúng 2.500 kg của ST-002, giữ guard STALE và kiểm API, focused 2/2 đạt; log lỗi đầu giữ nguyên. Các thay đổi ở sáu test cũ chỉ cập nhật đơn vị nhập/hiển thị; geometry, API và transaction assertions còn. Worker oracle ban đầu lỗi harness module filename, đã sửa; root command focused đầu bị lỗi đường dẫn redirect và chưa chạy test, đã sửa lệnh; hai invocation này không được dùng làm proof. Log đưa vào Git chỉ chuẩn hóa newline/khoảng trắng cuối dòng.

Năm câu hỏi nghiệm thu nội bộ: (1) yêu cầu là đọc/thao tác với kg/cm phù hợp thực tế, không mở M2d; (2) chuẩn làm tròn và bảo toàn từng trường có trước BUILD trong SPEC; (3) oracle, real API/browser/build/source hashes ở trên kiểm cả lỗi và phục hồi, Windows/Python 3.11/Node 22/Chromium, nền tảng khác NOT_TESTED; (4) thêm lớp trình bày và edit tracking lên viewer/editor/history/SQLite sẵn có, không viết lại engine; (5) bản đóng gói ở 8765 đã chạy nạp source → xếp 167 bó → giữ A → sửa B → so sánh → restore/undo, byte SQLite người dùng không đổi, API/OpenAPI bằng contract. Browser DB cô lập thực thi save/reload/open và fallback. Cài mới/launcher được tái sử dụng từ bằng chứng M1, không nhận đã cài lại.

“Mặc định kg/cm” là độ phân giải hiển thị tròn; ô nhập vẫn nhận phần lẻ hợp lệ khi người dùng chủ động nhập, không thêm spinner hoặc HTML step-validation gây chặn dữ liệu cũ. CSV giữ định dạng mm/kg có nhãn riêng. Không đổi backend, nguồn/GLB, mesh coordinates, schema DB, contracts, dependencies hay lịch sử SPEC/review. [Bảo toàn ảnh lịch sử](SCST_DISPLAY_UNITS_EVIDENCE/regression-preservation.json). Các gate cơ học INVOKED được ghi trong [gates](SCST_DISPLAY_UNITS_EVIDENCE/gates/README.md); không nhận PROVEN_HERMETIC, hosted CI hoặc CVF điều khiển AI. Không provider call và không tuyên bố governance AI; không cần Web bridge.

Đóng phần sửa kỹ thuật, nghiệm thu nghiệp vụ/khả năng vận hành vẫn PENDING. Hầm ước tính và 16 khối bao còn chờ xác minh. App [http://127.0.0.1:8765](http://127.0.0.1:8765), reload để dùng bản mới; không ghi snapshot thử vào SQLite người dùng. Chỉ commit local, không push; M2d chưa mở. Cảnh báo Three chunk/console màu cũ không ảnh hưởng kết quả kiểm.
