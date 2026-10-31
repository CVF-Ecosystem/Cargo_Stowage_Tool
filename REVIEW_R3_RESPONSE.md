# Phản hồi R2 và ba ảnh chất xếp — vòng web R3

**Ngày:** 31-10-2026. **Kết luận:** `REVISE_REVIEW_BASELINE_BEFORE_LOCAL_REVIEW`.

R2 nêu các khoảng trống đáng xử lý trước freeze. Ảnh bổ sung căn cứ nghiệp vụ để làm rõ tiêu chí MVP. Vì vậy phát hành SCST-REVIEW-0.3 làm đầu vào review local, giữ nguyên v0.2 như snapshot kỹ thuật/lịch sử. Chưa gắn nhãn Final Baseline và chưa xây roadmap/treeview triển khai ở vòng này.

## 1. Kết luận chính

V0.2 đã sửa nhiều vấn đề contract nhưng chưa đủ để chứng minh mô hình giải được bài toán chất xếp đại diện của owner. Chỗ cần sửa là **ranh giới nghiệm thu sản phẩm và những điều kiện nối dữ liệu/mô hình với thực tế**. Không có lý do bỏ toàn bộ kiến trúc hoặc viết lại các kiểm tra hash, partition, mass và status đã có.

Tôi tiếp nhận nhận định của R2 rằng phạm vi một BOX/hầm trống cần được owner đối chiếu với công việc thật, và phải giữ riêng Technical Proof với MVP nghiệp vụ. V0.3 đưa nhiều tầng, nhiều nhóm hàng, fidelity của hầm/support và thao tác kiểm tra 3D thành các tiêu chí MVP bắt buộc trong phạm vi case được chấp nhận. Thiếu profile thật làm mốc nghiệp vụ còn chờ; không hạ tiêu chí để nhận một lớp synthetic là MVP.

Đồng thời cần mô tả v0.2 công bằng: schema đã có kích thước riêng từng unit, trường/profile cho nhiều tầng và compatibility. Nó không bắt mọi bó là các hộp giống nhau, cũng không hoàn toàn thiếu mô hình nhiều tầng. Những thứ chưa có là nguồn/profile thật, đối chứng case đại diện, fidelity và runtime thực thi các yêu cầu đó.

## 2. Ảnh cho thấy gì và chưa cho biết gì

Đánh số theo tên tệp, tránh nhầm thứ tự chèn trong chat:

| Tệp | Quan sát có thể dùng | Hệ quả thiết kế | Giới hạn |
|---|---|---|---|
| 1.jpg | Các nhóm hàng dài/bó, vật thể dạng cuộn ở phần gần ảnh, các thanh/tấm xen giữa và thiết bị bánh xích ở trên khu vực hàng | Cần phân biệt hàng thuộc scope, support/kê và tải tạm của thao tác; xem được vùng/nhóm | Không biết máy đang hoạt động, model/mass, contact area, tấm bên dưới có tác dụng chịu lực thế nào |
| 2.jpg | Nhiều tầng; các tiết diện tròn và nhóm bó khác nhau xen theo chiều cao; vật thể dạng cuộn phía thấp | Cần manifest mapping, nhiều tầng và kiểm compatibility cho quan hệ trên-dưới thực sự dùng | Không xác định được mọi đơn vị là một ống hay một bó; không biết hồ sơ/chuyến/số đo |
| 3.jpg | Nhóm hàng dài đóng bó ở phần trên các hàng ống tròn; nhiều phần bị che | Mixed vertical support có thể là yêu cầu pilot; cần xem lớp/mặt cắt và support graph | Không thấy đầy đủ kê/điểm tiếp xúc/tầng dưới; không thể xác nhận cách xếp an toàn |

Thiết bị bánh xích nằm trong **1.jpg**, khác cách gọi “ảnh thứ ba” trong đoạn chuyển tiếp. Đây chỉ là sửa nhận diện file. Không khẳng định ba ảnh là ba chuyến hoặc ba case độc lập, cũng không khẳng định chúng cùng một tàu.

Ảnh giúp nhận ra câu hỏi phải giải. Ảnh không cung cấp giá trị để điền mặc định cho chiều dài, đường kính, số tầng cho phép, khối lượng hoặc khả năng chịu tải. Các chi tiết dạng cuộn/ống cũng chưa tự trở thành cargo types mới đã được owner chốt.

## 3. Hai điều của v0.2 vẫn có thể giữ

### 3.1 BOX là lựa chọn mô hình, không phải khẳng định hình dạng hầm

Không cần xây ngay mesh thân tàu đầy đủ để tạo giá trị. Một inner usable envelope dạng BOX có thể đủ cho một pilot nếu nó nằm trong miền xếp được xác minh ở toàn chiều cao sử dụng và vẫn cho phương án hữu ích. Mặt bằng miệng hầm hoặc góc chụp không xác nhận điều kiện ấy.

Nếu BOX loại quá nhiều không gian cần dùng, hoặc không mô tả được các vùng thật ảnh hưởng case, đó là lý do kỹ thuật phải mở geometry contract trước nghiệm thu. Có thể cần các mặt cắt/miền có giới hạn; chưa có số đo nên vòng này không tự chọn polygon, mesh hoặc hàm biên cụ thể. Tính chính xác mô hình được kiểm theo case, không theo mức độ đẹp của renderer.

### 3.2 Hầm trống là trạng thái đầu bài

Ảnh hàng đã xếp là trạng thái sau một quá trình. Nó không chứng minh công việc của owner bắt buộc là bổ sung vào hầm đang có hàng. Nếu chủ yếu lập phương án trước khi xếp, new loading từ hầm trống vẫn là scope hợp lý để xem xét. Nếu công việc thường xuyên là replan/adding cargo, cần occupied regions/fixed placements, mass và support tương ứng; số kg hàng cũ đơn lẻ không đủ.

V0.3 giữ đây là đề nghị cần xác nhận tại G0, không coi owner đã đồng ý giảm phạm vi chỉ vì package đã ghi như vậy.

## 4. Những yêu cầu nghiệp vụ cần nâng rõ

### 4.1 Đơn vị hàng đúng nguồn

Một dòng manifest có thể đại diện đơn vị xử lý khác nhau; cần đọc mẫu thực. V0.2 có hai enum BUNDLED_REBAR/BUNDLED_PIPE. Nếu hàng là từng ống, cuộn hoặc loại tiết diện ngoài hai nhóm đó, không được đổi tên để ép hợp schema. Gom một lô thành một box cũng không được làm mất unit con, mass và điều kiện xếp.

Phân biệt cargo form, packaging/handling unit và grouping. Hàng ngoài scope vẫn phải xuất hiện trong đối soát. Nếu nó là phần bắt buộc của chuyến, ứng dụng phải báo thiếu khả năng mô hình, không báo “đã xếp toàn bộ” cho phần còn lại. Giữ coils ngoài solver là lựa chọn có thể chấp nhận cho pilot phù hợp, không phải lý do bỏ coils khỏi total hay dùng nó làm nền đỡ không khai báo.

### 4.2 Nhiều loại nằm cạnh nhau khác nhiều loại đỡ nhau

Ảnh 2/3 gợi yêu cầu quan hệ khác loại theo chiều cao. Một demo đặt hai loại cạnh nhau chưa chứng minh giải được case cần bó phía trên ống. Profile phải chỉ ra cặp trên-dưới, phạm vi kích thước/kiểu bó, hướng, cách kê và giới hạn đã được review.

Hướng cần local đánh giá là sinh phương án trong **các cấu hình kê-chồng được chấp thuận**, mở rộng hữu hạn theo case. Không yêu cầu công cụ phải tự phát minh mọi cách xếp hoặc giải cơ học tổng quát mới có MVP. Nhưng nếu cấu hình thực chưa được mô tả/duyệt, không được tự cấp thông số để chạy cho có kết quả.

### 4.3 Collision, support và visualization là ba lớp

Envelope hộp thuận tiện kiểm va chạm bảo thủ. Nó không mô tả contact thực của ống/bó hoặc dây bó. FULL_BASE_SUPPORT chỉ đủ trong giả định mà profile chấp nhận; không biến footprint thành diện tích truyền tải.

Một giới hạn hình học riêng: với ống tròn xếp lệch hàng, các tiết diện tròn có thể không giao nhau trong khi hộp bao của chúng giao nhau. Khi pilot thật cần cấu hình đó, kiểm non-overlap AABB theo từng ống có thể từ chối phương án khả dụng. Không sửa bằng epsilon hoặc cho overlap tùy ý. Local cần so case rồi đề nghị geometry phù hợp hoặc arrangement template vẫn giữ units, mass và constraints đầy đủ.

### 4.4 Thiết bị trên hàng là điều kiện theo scenario

Không có số đo để tính tải bánh xích, tải tấm lót, tải động hoặc khả năng chịu lực từ 1.jpg. V0.3 hoãn thuật toán các phần đó. Tuy nhiên, nếu case đang đề nghị dùng ngoài hiện trường có máy làm việc trên hàng, case phải khai báo trạng thái ấy và có review tương ứng trước bàn giao. Không được coi nó là “tính năng tương lai” rồi bỏ khỏi giới hạn sử dụng của phương án hiện tại.

Thời điểm tải tạm và tải chuyến cuối khác nhau; không mặc định cộng mọi thiết bị vào cargo mass cuối chuyến hoặc loại thiết bị khỏi mọi đánh giá. Cách biểu diễn phụ thuộc quy trình và dữ liệu thật, cần người có trách nhiệm xác nhận.

### 4.5 3D cần đo bằng thao tác của người dùng

MVP phải cho tìm đúng unit/nhóm, ẩn/hiện lớp hoặc mặt cắt, đọc mass/dimensions/source, xem quan hệ đỡ và vị trí lỗi, chỉnh rồi thấy validation mới. Cùng unit và tổng phải khớp 2D, 3D, PDF, XLSX. Màu hoặc hình vẽ không được làm mất hàng unsupported/unplaced. 2D/text fallback vẫn cần cho máy không render được 3D.

## 5. R2-02 và R2-08: khoảng trống contract có thể tái lập

Đã tái lập việc JSON Schema nhận manifest/vessel có testOnly=false nhưng nguồn/mass synthetic. Probe bổ sung cũng cho thấy một sourceLineId không resolve và giá trị thay đổi vẫn có thể qua schema nếu kiểu và tổng nhất quán. Reference vẫn luôn operationalEligible=false; không có backend production để kết luận xảy ra vượt quyền.

Giải pháp yêu cầu trong v0.3 là registry nguồn do backend quản lý, xét mọi dependency của snapshot, confirmation receipt bind đúng target/draft/field claims, source spans có kiểu và coverage theo policy. SourceType do client gửi không tự chứng minh nguồn. Những giá trị suy ra phải pin input và phép tính. Receipt trỏ target content, không làm target trỏ ngược hash receipt rồi tạo cycle.

Schema có thể thêm conditional như lớp chặn sớm, nhưng không tự đọc chứng từ, xác minh actor hoặc thực thi transaction. Các ca ADM cần test API/persistence thật tại local. Không “sửa” reference bằng cách thêm một nhánh cấp operationalEligible=true.

## 6. R2-03 và R2-04: cần chốt mô hình trước freeze

**Vai trò:** đề nghị một operator local ghi nhận hồ sơ chuyên môn bên ngoài. Reviewer, người ghi nhận và người đối chiếu hồ sơ là các vai trò khác nhau. Scan chữ ký không tự thành chữ ký số; auth event của operator chỉ chứng minh hành động ghi nhận. Hồ sơ phải bind đúng plan/scope/conditions, còn hiệu lực và có quy trình xác minh phù hợp. Nếu lựa chọn reviewer đăng nhập app, cần mô hình account/role thật; không gán quyền kỹ sư cho operator để làm hợp schema cũ.

**Khối lượng:** v0.2 từ chối kg lẻ đúng policy của nó. Chưa có manifest thật để nói độ chính xác đó đủ hoặc thiếu. Đề nghị cho contract nghiệp vụ kế tiếp là integer grams, parse decimal exact và đổi toàn bộ mass/limit/reserve thống nhất, có overflow/migration/hash mới. Giữ raw và draft khi mơ hồ hoặc dưới độ chính xác đã chọn. Đổi đơn vị không giải quyết thiếu mass của từng đơn vị.

## 7. R2-06: điều xác minh được và phần còn thiếu

Đã so bảy bản R1 DOCX hiện truy cập được, kể cả trong ZIP lồng: tất cả cùng 59,296 bytes và SHA-256 `adf11a5682ea541d01a5b3ed348c6274938532a45ced23c49e91fa6ea6a08d8f`. Baseline v0.1 lồng trong v0.2 khớp upload gốc. Chi tiết vị trí/hashes ở docs/06 và receipt.

R2 nói họ có một DOCX khác raw bytes nhưng cùng đoạn/bảng. Bản đó chưa có trong nguồn của vòng này. Vì vậy chưa thể xác định nguyên nhân hoặc kết luận R2 sai; không bịa lịch sử re-export. Trạng thái là `PENDING_ALTERNATE_SOURCE_BYTES_OR_SHA`. Nó không ngăn tiếp tục phản biện nghiệp vụ/contract.

## 8. Đối chiếu nguồn chuyên ngành

IMO mô tả chất xếp/chằng buộc gắn với lập kế hoạch, thực hiện, giám sát và người đủ năng lực; điều này phù hợp việc tách tính toán phần mềm với review thực tế. [W01, docs/07]

Bản CSS Annex 7 trên cổng cơ quan hàng hải Hà Lan đặt vấn đề phân bố hàng và giới hạn tải boong/tank top. Không thể thay lớp đánh giá đó chỉ bằng việc các vật thể 3D không chồng lấn. [W02, docs/07]

Ví dụ sản phẩm Steel Load Planner của DNV công bố dùng mô hình kết cấu theo tàu cho phạm vi tải cục bộ; nó cũng tách những quy trình khác. Đây là căn cứ tham khảo để khai rõ phạm vi SCST, không là bộ tham số hoặc tính năng SCST đã có. [W03, docs/07]

Không suy các nguồn trên tự áp dụng pháp lý cho mọi phương tiện của owner. Vòng này không tạo profile kỹ thuật hoặc ngưỡng chịu tải thật.

## 9. Bản bàn giao sau vòng này

V0.3 có master hiện hành ở mức review, log giữ/sửa/hoãn, điều kiện TP/MVP, mô hình nghiệp vụ, admission/provenance, roles, ảnh gốc, R2 gốc, v0.2 nguyên bytes và probes/evidence. Schema/reference v0.2 không bị đổi; v0.3 chưa có schema/backend operational mới.

Local nhận nhiệm vụ REVIEW_ONLY, trả các khác biệt có bằng chứng và câu hỏi còn cần quyết định. Sau khi xử lý review mới chốt Final Baseline, roadmap và treeview dự kiến. Cách đi này giữ mục tiêu một công cụ có giá trị nghiệp vụ, đồng thời tránh đóng băng các giả định ảnh và các contract chưa đối chứng.
