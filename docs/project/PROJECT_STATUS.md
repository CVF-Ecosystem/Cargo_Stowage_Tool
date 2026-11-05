# Trạng thái project

Cập nhật: **05-11-2026**.

## MVP bàn giao để dùng thử (05-11-2026)

Bắt đầu từ [trang bàn giao MVP](../SCST_MVP_HANDOFF.md).

| Tranche | Kết quả | Review |
|---|---|---|
| SUP-02A/02B/03 | Revision dữ liệu hàng, hồ sơ tàu tổng quát, packing và ba cách nhìn | `docs/reviews/SCST_SUP_0*_REVIEW.md` |
| M2d | Báo cáo XLSX và trang in; owner đã mở được XLSX mẫu | [review](../reviews/SCST_M2D_REVIEW.md) |
| HARDEN-01 | Phân trang khi rebase, cache phát lại, giới hạn body, khóa Windows | [review](../reviews/SCST_HARDEN_01_REVIEW.md) |
| M3a | Xếp nhiều tầng theo cột: 1076/1076 bó trên hầm VINAFCO ước tính, 0,05 s | [review](../reviews/SCST_M3A_REVIEW.md) |
| M5a | Sao lưu/khôi phục local có kiểm, tự sao lưu trước khi khôi phục, hoàn tác khi lỗi | [review](../reviews/SCST_M5A_REVIEW.md) |

- **Kiểm trên Windows:** 878 backend, 57 browser, kiểm tích hợp 29/29.
- **Chạy thử launcher:** `start-local.ps1` đã chạy trên một bản chép dữ liệu của owner; dữ liệu gốc không đổi.

**Chờ owner:**
- dùng thử MVP và góp ý;
- nghiệm thu nghiệp vụ;
- số đo hầm thực, case thực và tải chồng (M3b);
- xác minh 16 khối bao.

**Tùy chọn về sau:** bộ cài (M5b), sao lưu tự động, AI (M4).

Các mục bên dưới là lịch sử trước ngày 05-11.

## SUP-01 đã giao kỹ thuật

[Review SUP-01](../reviews/SCST_SUP_01_REVIEW.md): giữ scene/camera/GLB qua cập nhật cùng hầm, fit/top/side/focus, ghost thân/vách chọn lọc và diagnostics mặc định tắt. Build index-D-_1-kxf.js,36/36 browser và5/5 focused đạt; hai focused kiểm lại nơi xuất artifact sau sửa đường dẫn. Nguồn1076 có167 đặt/909 chưa đặt trong flow tải thực đã kiểm. Backend/source/profile/GLB/API và SQLite người dùng được giữ. App đang chạy chỉ cần reload để nhận frontend mới; chỉ commit local.

CVF-DEV đã đối chiếu nguồn/hash và reviewer cho continuation giới hạn, mapping DA01/04/05 nằm trong brief/test/review. Full adoption/live governance/hosted CI còn riêng. Lỗi xuất27 artifact ra ngoài project đã thu hồi và sửa helper, receipt/giới hạn nằm trong review. Bước kế tiếp khi được chọn: SPEC SUP-02; chưa tự mở phần sau.

## Kế hoạch 3D đã chốt — chưa thi công

[Roadmap bổ sung](../roadmaps/SCST_ROADMAP_BO_SUNG_3D_VA_DU_LIEU.md) chèn ba phần trước M2d: SUP-01 viewer rõ/mượt; SUP-02 dữ liệu hàng cập nhật theo revision và profile tàu/tọa độ; SUP-03 dựng packing/bó/ống chi tiết theo dữ liệu có thể bổ sung. [Review](../reviews/SCST_3D_SUPPLEMENT_ROADMAP_REVIEW.md) phân biệt kế hoạch với phần đang chạy. SUP-01 đã giao kỹ thuật; work order đã đóng kỹ thuật, SPEC SUP-02 chỉ mở khi được chọn. Tọa độ VINAFCO đã kiểm đúng, không có lỗi translation còn chờ sửa.

## Đơn vị hiển thị kg/cm/m được giữ

Đã sửa theo góp ý owner: số tổng bằng tấn tối đa hai số lẻ, chi tiết bằng kg nguyên, kích thước/tọa độ bằng cm nguyên hoặc m hai số lẻ. Ô nhập hiển thị gọn nhưng chỉ trường thực sự sửa mới cập nhật số gốc; sửa góc/yêu cầu không làm tròn các dữ liệu khác. So sánh nhỏ hơn mức hiển thị có nhãn rõ, không bị coi bằng nhau. Không đổi dung sai hình học/khối lượng.

[Review đơn vị hiển thị](../reviews/SCST_DISPLAY_UNITS_REVIEW.md): 31 browser, 6.837 đối chiếu riêng, build và live VINAFCO 167 bó đạt; lưu/mở/undo/STALE/fallback giữ. Backend và dữ liệu nguồn không đổi, tái sử dụng 104 backend test đã có. App http://127.0.0.1:8765, reload để dùng bản mới; chỉ commit local. M2d chưa mở và nghiệm thu nghiệp vụ/vận hành còn chờ.

## M2c đạt kiểm kỹ thuật

Theo chỉ đạo tiếp tục roadmap, đã bổ sung **giữ gốc A → chỉnh/kiểm B → so sánh → khôi phục**, trên editor, một viewer và SQLite hiện có. Chọn A từ bản hiện tại hoặc bản lưu không thay B. So sánh đủ context và mọi ID, lọc/tìm/phân trang 50 bó, chi tiết chính xác g/mm/µm; khôi phục giữ B trong Bản trước và snapshot cũ không bị ghi đè. Baseline bộ nhớ không tự lưu qua reload.

[SPEC](../specs/SCST_M2C.md), [review độc lập](../reviews/SCST_M2C_REVIEW.md): 104 backend, 28 browser, 902 đối chiếu độc lập, build/contracts và hai tiến trình server đạt. Luồng đóng gói trên VINAFCO có 167 bó được kiểm giữ/sửa/so sánh/khôi phục/undo; SQLite người dùng không đổi. App ở http://127.0.0.1:8765; chỉ commit local, chưa push dữ liệu mới.

M2c đóng phần kỹ thuật, chưa nghiệm thu nghiệp vụ hoặc vận hành. M2d xuất báo cáo chưa mở; hầm đo thực và 16 khối bao vẫn chờ xác minh. Không tự mở phần tiếp theo.

## M2b — xếp thử tự động đạt kiểm kỹ thuật

Owner yêu cầu hiện hàng trên hình tàu/làm tròn khối lượng và chọn bắt đầu M2b. [SPEC](../specs/SCST_M2B.md) và [review độc lập](../reviews/SCST_M2B_REVIEW.md) xác minh đủ6tiêu chí: heuristic một lớp, preview/apply rõ, actualcargo meshes trên VINAFCO, mọiremainingunit có lý do, async/undo/lưu-mở giữ nguồn, massdisplay2decimals và exactgram calculations.98backend/22browser46,7s/8941independentassertions/build/contracts/restart đạt. Root UIscrollline đượcSol review độc lập, lỗiđầu vàsửa được ghi rõ.

App8765 đã cập nhật: Xếp thử tự động → Áp dụng xếp thử. Giới hạn32t từ mẫu giữ nguyên,22bó được đặt; ở fullVR-SIIlimit,167bó/217,74t và909còn lại. Đây là heuristic một lớp, không tối ưu hoặc phương án vận hành; hầm/16khối bao nguồn còn cần xác minh. Khối lượng hiển thị1.125,55tấn, tính/lưu giữ1125551030g. Localcommitonly, chưa push dữ liệu mới.

## Nguồn list ống V1.1 — đạt kiểm kỹ thuật

Owner cung cấp list thực đã chuẩn hóa, yêu cầu kiểm cách tính và giữ mô hình sà lan. Slice riêng theo [SPEC](../specs/SCST_PIPE_LIST.md) và [work order](../work_orders/SCST_PIPE_LIST.md):31 nhóm,1.076 bó,21.226 ống, ban đầu chưa bố trí; chọn/đặt/bỏ/xoay thủ công, đối soát khối lượng/số bó/ống toàn bộ và từng nhóm, lưu/mở giữ provenance. Không mở planner. [Đánh giá nguồn](../reviews/SCST_PIPE_LIST_ASSESSMENT.md) ghi31,03kg chênh giữa tổng nguồn với K×L và CBM cần đối chiếu. 16bó khối bao cần xác minh, hầm vẫn ước tính. [Review độc lập](../reviews/SCST_PIPE_LIST_REVIEW.md) xác minh92backend/17browser (57,1s), build/contracts/restart và222kiểm độc lập. Sáu tiêu chí kỹ thuật đạt; chưa nghiệm thu nghiệp vụ hoặc vận hành. Demo8765 đã cập nhật, dữ liệu chỉ commit local.

## M2a — đạt kiểm kỹ thuật ở lượt trước

Owner yêu cầu tiếp tục roadmap và xác nhận **“Chưa có, tiếp tục với mẫu có nhãn”** đối với manifest/số đo hầm thực. Đã làm M2a theo [SPEC](../specs/SCST_M2A.md): tạo phương án rỗng; nhập/sửa/xóa từng bó và hầm BOX; đặt/bỏ vị trí; CSV UTF-8 có preview/lỗi dòng-trường; lưu snapshot SQLite immutable và mở lại sau reload/restart. Mẫu M1/VINAFCO được giữ.

[Review M2a](../reviews/SCST_M2A_REVIEW.md):79 backend test,13 browser test và kiểm qua hai tiến trình server đạt. Dữ liệu SQLite tại `runtime-data/scst.sqlite3` ngoài Git; rawdraft chưa lưu vẫn có thể mất khi đóng trang. Source chỉ commit local, chưa push dữ liệu mới. Chưa xác minh manifest/hầm thật hoặc cấp điều kiện vận hành.

## VINAFCO 268 — lát cắt bổ sung đã kiểm kỹ thuật

Owner cung cấp gói đăng kiểm/mô hình và yêu cầu đánh giá, dùng được thì tích hợp. Đã thêm chế độ **Xem VINAFCO 268**: thân theo hồ sơ77,8 ×13,24 ×5,2m, hầm/cabin/tuyến hình ước tính, hàng synthetic. Có GLB mờ/ẩn-hiện, chọn VR-SI/VR-SII, marker mớn và profile do backend ràng buộc. Mẫu M1 vẫn mặc định; giới hạn chuyến đang có được giữ khi chuyển chế độ.

[Assessment](../reviews/SCST_VINAFCO268_ASSESSMENT.md) và [review](../reviews/SCST_VINAFCO268_REVIEW.md) ghi nguồn/giới hạn; 63 backend, 9 browser và109 kiểm độc lập đạt. Work order VINAFCO268 đóng phần kỹ thuật, nghiệm thu nghiệp vụ còn chờ. Đây là phần viewer được cho làm sớm, không hoàn tất M2c/M2/M3. PDF/gói gốc giữ local ngoài Git; chưa push các artifact mới lên GitHub.

## Chỉ đạo và phần đã làm

Owner thống nhất hướng M0 (SCST-D001), chọn tận dụng M1 có chọn lọc và chỉ đạo tiếp tục bằng root orchestrator/reviewer, Terra 6.1 High worker và Sol-Medium cho phần khó ([SCST-D002](../decisions/SCST_D002_M1_REUSE_EXECUTION.md)).

Đã chuyển source theo [SPEC M1 v0.2](../specs/SCST_M1.md) và [WORK_ORDER M1](../work_orders/SCST_M1_REUSE.md). Root review khác hai worker của lượt này; [báo cáo M1](../reviews/SCST_M1_REVIEW.md) xác minh đủ 9 tiêu chí kỹ thuật. Owner chưa nghiệm thu nghiệp vụ; M2 tổng thể chưa được giao thi công, chỉ có lát cắt VINAFCO268 riêng phía trên.

## M1 hiện có

Demo synthetic BOX một lớp, bảng/3D/2D cùng dữ liệu, giới hạn chứng nhận/chuyến/onboard, kiểm tải/biên/va chạm/hàng bắt buộc, draft/STALE, sửa–kiểm lại–undo và fallback WebGL. Khởi chạy bằng `Start-SCST.cmd`; xem [APP_GUIDE](../APP_GUIDE.md). Không lưu bền; refresh mất thay đổi.

51 backend test, 5 browser test và 498 kiểm độc lập đạt. Cold setup/launcher, chạy với chặn truy cập ngoài loopback, schema/types regeneration và archive identity có evidence. Xem giới hạn kiểm và cảnh báo còn lại trong review; không sử dụng demo cho phương án thực.

## Source cũ và nguồn tham khảo

[Archive M1](../../archive/2026-10-31/paused-m1/README.md) giữ nguyên 50 file; chỉ lấy thành phần đã chọn và sửa trên cây mới. Test/log/ảnh cũ không được dùng làm nghiệm thu bản mới. [Đánh giá tái sử dụng](../reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md) lưu căn cứ và lịch sử recheck.

[Roadmap gốc](SCST_Roadmap_Ban_Dau_Tool_First.md), [roadmap tổng thể](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) và [tài liệu tham khảo](../reference/README.md) tiếp tục làm nguồn định hướng. Lỗi authority work order khung đã sửa bằng snapshot revision dispatch; gate kiểm trực tiếp đạt.

## Bước tiếp theo

M2c và đơn vị hiển thị đã giao kỹ thuật. CVF-DEV đã cho continuation giới hạn và SUP-01 đã giao kỹ thuật. Tiếp theo khi được chọn là SPEC SUP-02, rồi SUP-03 và checkpoint tích hợp trước M2d. M3 nhiều tầng/case thực, M4 AI tùy chọn và M5 vận hành giữ riêng; dữ liệu thiếu có đường bổ sung, nghiệm thu nghiệp vụ/vận hành vẫn chờ.
