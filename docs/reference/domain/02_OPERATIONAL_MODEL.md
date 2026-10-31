# Mô hình nghiệp vụ cần kiểm chứng ở local

**Package:** SCST-REVIEW-0.3. **Trạng thái:** REVIEW_BASELINE_FOR_LOCAL_VERIFICATION; chưa phải Final Baseline.

Tài liệu này quy định cách hiểu bài toán nghiệp vụ và phần phải được cụ thể hóa/đối chiếu trước khi freeze implementation. Những khái niệm được bổ sung ở đây chưa đồng nghĩa schema hoặc reference code v0.2 đã hiện thực chúng. Local agent phải ghi mapping, khoảng thiếu và đề xuất contract/test; không chỉ đổi nhãn phiên bản dữ liệu.

## 1. Đầu bài của tool

Tool hỗ trợ lập, kiểm tra và điều chỉnh phương án chất xếp theo manifest, mô hình hầm sử dụng và các cấu hình kê/xếp được chấp thuận. Người vận hành cần biết từng đơn vị hàng nằm ở đâu, thuộc nhóm/lớp nào, dựa trên cấu hình đỡ nào, lượng hàng đáp ứng yêu cầu chuyến và lý do phần chưa xếp được. Giao diện 3D, 2D và báo cáo phải giải thích cùng một phương án đã pin.

Giữ hướng tool local, frontend/backend tách module, validator xác định độc lập solver/AI, CVF kiểm soát Agent actions. Công cụ không mở thành hệ thống điều hành cầu bến, xe, nhân lực hoặc phân ca.

Ảnh nghiệp vụ chứng minh cần xem xét nhiều tầng, nhiều nhóm hàng và quan hệ đỡ; ảnh không cung cấp được các thông số đủ để tính phương án. Danh sách trường và điều kiện dưới đây là yêu cầu thu nhận/kiểm chứng dữ liệu, không phải giá trị kỹ thuật được suy ra từ ảnh.

## 2. Hai mức mô hình và điều kiện nhận giá trị

| Nội dung | Technical Proof | MVP nghiệp vụ cần hướng tới |
|---|---|---|
| Dữ liệu | Synthetic fixtures có chủ đích | Case đại diện do người vận hành cung cấp/đối chiếu, có nguồn và tham số được người có thẩm quyền xác nhận |
| Hầm | BOX, empty initial state để tạo oracle rõ | Vùng sử dụng có quan hệ được kiểm với hầm thật; BOX chỉ đủ khi xấp xỉ đó phục vụ được case đại diện |
| Hàng | Mẫu nhỏ kiểm primitive và ID/mass | Nhiều kích thước, nhiều nhóm hàng thuộc danh mục pilot đã xác nhận; mọi đơn vị và hàng ngoài phạm vi được đối soát |
| Xếp | Một tầng hoặc mẫu nhiều tầng để kiểm logic | Nhiều tầng có cấu hình đỡ phù hợp; mixed vertical bắt buộc nếu đó là điều kiện của pilot đã chốt |
| Kết quả | Chứng minh các phép tính/luồng dữ liệu đã chạy | Tạo được candidate hữu ích, sửa/kiểm lại được và giải thích được vị trí, phần chưa xếp cùng giới hạn |
| Quan sát | Renderer dựng đúng tọa độ | Người dùng tìm được đơn vị hàng, lớp, nhóm và quan hệ đỡ; dữ liệu tổng quan–chi tiết và export nhất quán |

Đạt Technical Proof không tự làm MVP nghiệp vụ đạt. MVP nghiệp vụ đạt cũng không tự phê duyệt mọi phương án/chuyến thật. Điều kiện nghiệm thu phần mềm, profile kỹ thuật và quyền chấp thuận phương án phải được ghi riêng.

V0.2 đã có dimensions riêng cho từng CargoUnit, nhiều tầng có gate, compatibility profile và lớp xem/cắt lớp. Sửa đổi v0.3 là làm rõ **đích nghiệm thu và độ phù hợp của mô hình**, không phủ nhận những cấu trúc đó đã tồn tại trong tài liệu v0.2.

## 3. Đơn vị hàng, nhóm hàng và phạm vi manifest

### 3.1 Đơn vị nguyên vẹn

Đơn vị mà solver được đặt/chọn phải khớp đơn vị được khai trong manifest và thực sự được quản lý. Bó thép, bó ống và một ống riêng không mặc nhiên là cùng một kiểu. Ảnh thấy các đầu ống không xác nhận chúng là các CargoUnit độc lập hay thành phần của một bó.

V0.2 chỉ có BUNDLED_REBAR và BUNDLED_PIPE. Nếu pilot cần ống riêng hoặc dạng tiết diện khác, local phải đề xuất loại/shape/unit semantics phù hợp và regression tests trước khi mở hỗ trợ. Không đổi tên một ống riêng thành BUNDLED_PIPE để vượt schema. Không tự tách một bó hoặc chia đều mass của một line cho các kiện khi nguồn không cho phép.

### 3.2 Nhóm/lớp không làm mất đơn vị con

Nhóm theo lô, theo chiều dài, vùng xếp hoặc lớp là cách tổ chức thông tin. Nhóm không tự trở thành một đơn vị hàng có thể chia/cộng tùy ý. Nếu triển khai một arrangement/template gộp nhiều unit để kiểm nhanh hoặc hiển thị, phải giữ đầy đủ IDs con, khối lượng, placement, kiểu hàng và ràng buộc của các unit đó. Tổng mass phải đối soát được xuống từng đơn vị; không tạo “khối hàng tương đương” mất nguồn hoặc mất part được yêu cầu xếp.

### 3.3 Bao quát toàn manifest

Mọi dòng/đơn vị đầu vào phải có kết quả đối soát: được mô hình hóa, thiếu dữ liệu hoặc ngoài phạm vi hỗ trợ. Sau khi case hợp lệ, các tập required/optional/excluded và placed/unplaced phải tuân thủ contract đã chốt. Hàng ngoài phạm vi không được tự chuyển thành optional/excluded, biến mất khỏi total hoặc bị báo “không đủ chỗ” khi thực chất model không hỗ trợ.

Các vật thể dạng cuộn và nhóm tiết diện khác xuất hiện trong ảnh là tín hiệu cần hỏi manifest. Chúng không tự mở phạm vi thành steel-coil planner. Nếu các nhóm này ở ngoài pilot, báo cáo phải nói rõ phương án chỉ bao phủ phần nào; không trình nó như phương án cho toàn bộ cảnh ảnh. Khi hàng ngoài phạm vi có vị trí/tải hoặc quan hệ đỡ ảnh hưởng trực tiếp hầm mục tiêu, không được bỏ qua để tiếp tục như một case rỗng hợp lệ.

## 4. Hầm thật và vùng sử dụng

### 4.1 BOX là một lựa chọn mô hình cần chứng minh phù hợp

Không cần dựng mesh tàu phức tạp chỉ vì ảnh có góc nhìn không vuông. Một BOX nội tiếp có thể được giữ nếu nguồn đo/bản vẽ và người có thẩm quyền xác nhận nó nằm trong vùng sử dụng, exclusions/margins phản ánh giới hạn cần thiết, và benchmark trên case đại diện chứng minh vùng đó còn hữu ích cho nghiệp vụ.

Nếu BOX bỏ mất phần không gian cần thiết đến mức tool không giải quyết được pilot, đó là lý do kỹ thuật phải thay đổi contract hình học trước nghiệm thu MVP. Local đề xuất mô hình phù hợp từ dữ liệu thật và oracle độc lập; không tự suy shape, góc nghiêng, độ cong hoặc tolerance từ ảnh.

Điều kiện kiểm cần bao phủ toàn occupied envelope của placement trong volume hợp lệ; kiểm tâm hay một tập điểm không đủ căn cứ không được thay bài toán containment. Solver, validator, viewer và export phải dùng cùng frame, biên/exclusions và đơn vị. Mesh chỉ để minh họa không được làm người dùng tưởng validator đã kiểm theo mesh đó.

### 4.2 Trạng thái hầm lúc bắt đầu

EMPTY_TARGET_HOLD là điều kiện đầu bài, không có nghĩa phương án cuối chỉ một lớp hoặc luôn trống. Ảnh đã xếp hàng không chứng minh người dùng cần thuật toán xếp bổ sung vào hầm đang có hàng.

Lập kế hoạch từ hầm trống là phạm vi pilot khả dĩ nếu owner xác nhận nó phù hợp công việc thực. Nếu pilot phải cập nhật hầm đã có hàng, local cần contract cho fixed placements/occupied regions, mass, provenance và quan hệ đỡ; không dùng một số kg hoặc excluded zones để âm thầm mô phỏng toàn bộ hàng cũ.

## 5. Ba mô hình phải phân biệt

| Mô hình | Vai trò | Không được suy ra từ nó |
|---|---|---|
| Bao chiếm chỗ/collision envelope | Kích thước và vùng hàng chiếm dụng, containment/overlap/clearance | Bề mặt tiếp xúc thật, rating đỡ, chống lăn hoặc sức bền |
| Cấu hình kê/đỡ được chấp thuận | Xác định cấu hình nào được phép dùng, điều kiện trên/dưới, vật kê, hạn mức và cách validator kiểm | Không suy được rating từ diện tích box hoặc từ cách xếp thấy trong ảnh |
| Hình hiển thị | Giúp nhận diện loại hàng, nhóm, lớp và vị trí | Không tạo thêm tính năng/capability của solver hoặc validator |

FULL_BASE_SUPPORT trong v0.2 là phép kiểm envelope với cấu hình được review. Nó chưa chứng minh tiếp xúc của bó ống hoặc đủ cho mọi cách kê thực. Nếu case thật có khoảng trống giữa gối, nhô đầu, điểm tựa không đồng phẳng hoặc nesting ngoài mô hình, phải báo model không bao phủ và đề xuất extension; không lén đổi hệ số phủ hoặc epsilon để làm PASS.

Một tình huống cần thử trước khi chốt geometry: các ống tròn được xếp lệch hàng theo một cấu hình được chấp thuận có thể không giao nhau trong khi AABB của chúng giao nhau. Non-overlap AABB có thể bảo thủ quá mức đối với case ấy. Không sửa bằng cách cho phép overlap hộp tùy ý. Cần đánh giá mô hình hiện tại có còn hữu ích cho pilot; nếu không, đề xuất shape-aware geometry hoặc approved arrangement với đầy đủ unit con và điều kiện. Không tự tạo thuật toán xếp lục giác/hollow/ellipse từ ảnh hoặc từ giả định về loại hàng.

## 6. Profile và template kê/xếp nhiều tầng

MVP hướng tới nhiều tầng và nhiều nhóm. Việc cùng hỗ trợ hai cargo types không đồng nghĩa cho phép mọi tổ hợp xếp chồng. Cần phân biệt hàng nằm cạnh nhau với hàng khác profile nằm trên nhau; quan hệ tương thích trên/dưới có hướng và không tự đối xứng.

Thay cho một bộ tính cơ học tổng quát, phạm vi phù hợp là **cấu hình kê/xếp hữu hạn đã được người có thẩm quyền chấp thuận**, có phiên bản và nguồn. Local cần đối chiếu khả năng biểu diễn ít nhất các nội dung sau trước khi freeze contract:

- Loại/đơn vị hàng, dải kích thước/khối lượng và phạm vi áp dụng của cấu hình.
- Profile trên và dưới, hướng đặt/yaw, mẫu bố trí, số tầng và chiều cao cho phép.
- Vật kê/chèn/chống lăn, vị trí hoặc quy luật bố trí được phép, cao độ và các điều kiện kiểm được bằng dữ liệu.
- Cách xác định support relations; các dạng khe/nhô đầu/multi-support được hoặc không được mô hình bao phủ.
- Allowance và basis tải, giới hạn của từng support hoặc stack theo nguồn chuyên môn; cách cộng hàng và kê không trùng.
- Nguồn, người review, phiên bản, thời hạn/phạm vi và điều kiện khiến template cần kiểm lại.
- Oracle/ca chấp nhận/ca từ chối đã thống nhất để kiểm implementation.

Không tự gán những tham số này. Một trường APPROVED, một ảnh hoặc một giá trị hash không chứng minh reviewer thật đã chấp thuận profile. Template phải có chuỗi bằng chứng và phạm vi cụ thể theo contract review.

Reference v0.2 kiểm tải descendants theo cách bảo thủ: mỗi lower supporter chịu toàn bộ cargo descendants tương ứng. Khi case có nhiều support, điều đó không là mô hình phân phối lực thực. Nếu cách chặn này làm mất khả năng phục vụ pilot, local phải đưa vấn đề ra cùng reviewer; không tự chia đều tải cho các support để giảm số tính.

## 7. Thiết bị và tải tạm trong hầm

1.jpg có thiết bị bánh xích và vật liệu/tấm kê trong vùng hàng. Ảnh không cho biết nó đang chạy hay đỗ, tải trọng hoặc đường truyền lực. Điều này đủ để bổ sung câu hỏi phạm vi, không đủ để cấp allowance cho hoạt động đó.

Với mỗi pilot/plan, phải làm rõ phạm vi đánh giá là final cargo layout hay có bao gồm trạng thái thi công/tải tạm. Nếu thiết bị lên hàng hoặc một trạng thái thao tác tương tự nằm trong scenario đang được đánh giá, phải ghi trạng thái ấy và yêu cầu review chuyên môn riêng cho tải/đỡ/vùng thao tác cần thiết trước khi bàn giao sử dụng cho scenario đó. Không gắn nhãn “tính sau” để bỏ qua tải tạm đang ảnh hưởng quyết định hiện tại.

Có thể giữ tối ưu đường đi, điều khiển thiết bị và tính tải động ngoài tool. Khi đó, kết quả cargo layout không được trình bày như quyền cho thiết bị hoạt động trên hàng; review/điều kiện sử dụng cần nói đúng phần chưa được giải quyết. Không tự lấy công suất máy, footprint nhìn trên ảnh hoặc một tỷ lệ tải giả để tính.

## 8. Người vận hành phải làm được gì trong 2D/3D

- Từ tổng quan mở đúng nhóm/lớp/đơn vị hàng; biết ID, kích thước, mass, profile, supporters và lý do lỗi/thiếu dữ liệu.
- Ẩn/hiện lớp, cắt lớp, chọn nhóm và xem mặt bằng/mặt cắt; thao tác hiển thị không làm mất unit khỏi totals hoặc validator.
- Nhận ra nhóm/loại hàng và khoảng trống; nhãn/màu có chú giải và không phụ thuộc màu để hiểu trạng thái.
- Chỉnh vị trí/yaw trong phạm vi cho phép, nhận lý do invalid cụ thể và tạo version/validation mới theo backend; không tự có proof tối ưu từ run trước.
- Đối chiếu cùng một unit và tổng số lượng/mass giữa bảng, 2D, 3D, PDF và XLSX theo đúng plan version/hash.
- Tiếp tục nhập/kiểm/lưu/xuất bằng bảng/2D khi WebGL lỗi; không mất dữ liệu.

Nghiệm thu cần một nhiệm vụ thực do người dùng hoàn thành, ví dụ tìm bó thuộc nhóm cần kiểm, xem nó được đỡ bởi những đơn vị nào, sửa vị trí và xác định tác động lên phần hàng còn lại. Một screenshot có nhiều hộp màu không đủ làm bằng chứng thao tác này.

## 9. Những đầu vào phải đối chiếu trước khi chốt MVP pilot

1. Pilot bắt đầu từ hầm trống hay cần điều chỉnh khi đã có hàng?
2. Danh mục hàng và đơn vị nguyên vẹn nào bắt buộc có trong pilot? Cần manifest mẫu, không suy từ ảnh.
3. Mixed vertical là điều kiện bắt buộc hay chỉ nhiều nhóm ở vùng khác nhau? Nếu bắt buộc, cần cặp cấu hình được chấp thuận.
4. Nguồn số đo vùng sử dụng, exclusions và người chịu trách nhiệm xác nhận là gì?
5. Ai/cơ sở nào cung cấp profile kê/xếp, và những trạng thái tải tạm/thiết bị nào nằm trong scenario cần sử dụng?

Các câu này là đầu vào cho vòng local verification. Local có thể khảo sát và đề xuất contract/tests trong lúc chờ nguồn; không được điền fixture thay dữ liệu thật hoặc đánh dấu MVP nghiệp vụ đạt khi thông tin quyết định phạm vi vẫn còn thiếu.
