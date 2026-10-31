# Quyết định giữ, sửa, hoãn sau R2 và ảnh

**SCST-REVIEW-0.3.** `SỬA` ở đây là thay yêu cầu review baseline, không có nghĩa backend/schema mới đã được triển khai. `HOÃN` không cho phép nghiệm thu case còn phụ thuộc chức năng ấy. Owner chưa ký chấp nhận phạm vi pilot thu hẹp.

## 1. Đối chiếu tám nhận định R2

| ID | Kết luận và quyết định | Lý do/căn cứ | Kiểm chứng tiếp theo |
|---|---|---|---|
| R2-01 | SỬA mốc nghiệm thu; GIỮ BOX/empty như phương án prototype và đề nghị pilot có điều kiện | V0.2 đã thu hẹp đầu bài để có contract kiểm được; chưa có căn cứ owner chấp nhận đó là toàn bộ MVP. Ảnh final không xác nhận initial state | G0, MB-01/03/04/06; owner xác nhận new loading và case đại diện |
| R2-02 | SỬA admission invariant và test criteria | Hai schema probes synthetic với testOnly=false được tái lập; reference vẫn không cấp operational eligibility | ADM-01…05/10/11 trên backend thật, registry và dependency graph; conditional schema chỉ là lớp chặn sớm |
| R2-03 | SỬA đề nghị role model | V0.2 FIELD_REVIEW chỉ biểu diễn reviewer đã auth trong app; chưa có đường rõ cho operator ghi hồ sơ bên ngoài | Đề nghị one operator + external review tách reviewer/recorder/verifier; owner xác nhận quy trình; ER-01…09 |
| R2-04 | SỬA thành quyết định precision trước freeze; đề nghị grams | Integer kg loại 2000.5 kg đúng contract; chưa có manifest thật chứng minh precision cần thiết | Lấy mẫu, exact conversion/overflow/migration; PROPOSED_INTEGER_GRAMS chưa phải schema đã đổi |
| R2-05 | SỬA thành điều kiện MVP bắt buộc, GIỮ mô hình tham chiếu ở phạm vi của nó | FULL_BASE_SUPPORT không chứng minh contact/capacity; không có approved profile thật; ảnh gợi yêu cầu nhiều tầng/mixed support | Profile đủ cho mọi quan hệ sử dụng, ít nhất hai case nghiệp vụ độc lập; MB-04/05/06 |
| R2-06 | GIỮ issue truy vết ở trạng thái chờ đối chứng variant, giới hạn lại tuyên bố byte-exact | Bảy bản R1 truy cập được đều cùng hash. Bản khác mà R2 nói có trong phiên của họ chưa được cung cấp ở đây | Cần bytes hoặc SHA của variant; không suy đoán re-export. Không chặn review logic/ảnh |
| R2-07 | GIỮ ranh giới evidence; bổ sung TP/MVP rõ hơn | 86 tests là contract reference; các runtime/field gates chưa chạy | Evidence checklist và MB/LAT; không tính acceptance tables là test đã chạy |
| R2-08 | SỬA chain provenance tới từng giá trị | sourceLineId tự do không resolve draft/source span/confirmation; probe thay giá trị/source locator vẫn schema-valid | ConfirmationReceipt -> target/draft/field claims; immutable source registry; ADM-04/06/07/10/12 |

## 2. Quyết định từ ảnh và phản biện nghiệp vụ

| ID | Giữ/sửa/hoãn | Quyết định và tiêu chí |
|---|---|---|
| D3-01 | GIỮ | Tool-first, local, FE/BE tách module, CVF cho Agent actions; kiểm core AI-off và authority backend |
| D3-02 | SỬA | Technical Proof và MVP-NV là hai mốc; một tầng synthetic không đủ MVP; TP ứng dụng cũng chưa đạt chỉ từ 86 checks |
| D3-03 | SỬA | Nhiều tầng/nhiều nhóm thành giá trị phải chứng minh; nếu case cần thanh/bó trên ống thì cần đúng mixed-support profile, không thay bằng đặt cạnh nhau |
| D3-04 | GIỮ CÓ ĐIỀU KIỆN | BOX có thể làm inner usable envelope; giữ nếu nguồn/containment/fidelity/giá trị đủ; nếu không, geometry contract cần đổi trước MVP |
| D3-05 | CHỜ XÁC NHẬN | New loading từ hầm trống là đề nghị pilot; không suy nhu cầu incremental loading từ ảnh hầm đã xếp |
| D3-06 | SỬA | Tách cargo form, packaging, handling unit và group; không ép single pipe/cuộn thành BUNDLED_PIPE; MB-02 |
| D3-07 | SỬA | Tách collision envelope, support/contact và visual representation. AABB false rejection cần được đo trên case; không chữa bằng allow-overlap |
| D3-08 | GIỮ HƯỚNG, SỬA TIÊU CHÍ | 3D có layer/section/group/filter/unit/support/error tasks; 2D fallback và cùng dữ liệu PDF/XLSX; MB-09/10 |
| D3-09 | HOÃN THUẬT TOÁN, GIỮ ĐIỀU KIỆN CASE | Không xây đường đi/tải động máy. Nếu máy trên hàng thuộc scenario đang xét, cần khai báo và review phù hợp trước handoff; MB-13 |
| D3-10 | HOÃN CÓ BLOCKER RÕ | Coil optimizer, occupied hold, nhiều hầm và cơ học tổng quát ngoài MVP đề nghị. Nếu case pilot bắt buộc thì phải change scope trước nghiệm thu, không lược hàng khỏi manifest |
| D3-11 | SỬA | Vòng local hiện tại REVIEW_ONLY, ghi đè permission triển khai của work order v0.2; roadmap/treeview sau review |
| D3-12 | GIỮ | Khối lượng/budget, source validity, immutable hashes, independent validator, manual revision, required/optional và fail-closed core đã có giá trị; không viết lại vô cớ |

## 3. Mức đóng vấn đề

V0.3 đóng phần **phát hiện và yêu cầu xử lý** của R2-02/03/08 ở mức review baseline. Chưa đóng bằng backend test. R2-01/04/05 cần dữ liệu/quyết định nghiệp vụ; R2-06 cần variant để đối chứng; R2-07 được giữ như nguyên tắc bằng chứng xuyên suốt. Không có mục nào được ghi operational-ready từ ảnh hoặc từ kết quả schema.
