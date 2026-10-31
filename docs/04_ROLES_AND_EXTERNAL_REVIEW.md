# Vai trò và ghi nhận review chuyên môn bên ngoài

**Package:** `SCST-REVIEW-0.3`  
**Trạng thái:** `REVIEW_ONLY` / `NOT_FINAL`  
**Phạm vi tài liệu:** đề xuất contract nghiệp vụ để local agent phản biện và đối chiếu quy trình thực; chưa phải chức năng đã triển khai hoặc quyền sử dụng phương án thực.

## 1. Quyết định thiết kế đề xuất

Mô hình mặc định của bản local là **một operator sử dụng tool và ghi nhận hồ sơ review chuyên môn được thực hiện bên ngoài tool**. Người review không bắt buộc có account trong app. Không tạo một tài khoản reviewer giả, không dùng session của operator để diễn đạt rằng người review đã đăng nhập.

Một người dùng app không có nghĩa chỉ có một người chịu mọi trách nhiệm nghiệp vụ. Người xác nhận nguồn, người chọn phương án và người có thẩm quyền review kỹ thuật có thể khác nhau. Nếu một người thực tế được giao nhiều vai trò, phải ghi nhận căn cứ phân công; việc họ là operator duy nhất không tự cấp các vai trò còn lại.

Luồng reviewer đăng nhập trực tiếp có thể được xem xét sau nếu đơn vị cần. Luồng `FIELD_REVIEW` với `SERVER_AUTHENTICATED_EVENT` trong contract v0.2 chỉ mô tả hướng đó. Nó được giữ trong phần tham chiếu kỹ thuật lịch sử; không dùng nguyên nghĩa ấy cho hồ sơ review bên ngoài.

Local cần đối chiếu đề xuất này với quy trình thực trước khi chốt contract triển khai. Không mở thêm quy trình điều hành cảng, cổng ký số, hệ thống quản lý nhân sự hay cloud multi-user chỉ để hoàn thành bước review.

## 2. Ba chủ thể phải được phân biệt

| Chủ thể | Việc thực hiện | Tool có thể xác nhận điều gì |
|---|---|---|
| **Reviewer chuyên môn** | Xem xét nội dung thuộc thẩm quyền và đưa ra kết luận trong hồ sơ ngoài app | Tool lưu danh tính được khai trong nguồn, căn cứ thẩm quyền, kết luận và hồ sơ. Tên trong payload không tự chứng minh danh tính. |
| **Recorder — người ghi nhận** | Operator đang đăng nhập nhập/tải hồ sơ và liên kết nó với đối tượng được review | Backend xác thực được sự kiện ghi nhận của operator theo cơ chế local đã triển khai. |
| **Verifier — người đối chiếu hồ sơ** | Kiểm nguồn, danh tính/thẩm quyền reviewer, binding tới nội dung, hiệu lực và thông tin thu hồi theo quy trình được giao | Tool lưu cách kiểm, kết quả, người kiểm và bằng chứng. Hành động này không biến verifier thành người đưa ra kết luận kỹ thuật. |

Recorder và verifier có thể là cùng một người nếu quy trình đơn vị cho phép và người đó được giao nhiệm vụ. Không giả một người thứ hai để tạo vẻ độc lập. Khi quy trình yêu cầu hai người, bản local phải ghi điều kiện chưa đáp ứng thay vì tự bỏ qua.

AI/Agent không được trở thành reviewer, recorder được quyền chấp nhận hồ sơ, hoặc verifier có thẩm quyền chỉ bằng lời tự khai. CVF ALLOW không thay quyền backend hay kết luận của các chủ thể trên.

## 3. Hai nội dung và một sự kiện đối chiếu riêng

Các tên dưới đây mô tả contract đích cần local rà soát. Chúng không tuyên bố schema/runtime đã được dựng.

### 3.1 Hồ sơ kết luận bên ngoài — ExternalReviewStatement

Hồ sơ giữ nguyên nội dung được review và kết luận của reviewer, gồm tối thiểu:

- Loại đối tượng: plan cụ thể, support profile hoặc một phạm vi kỹ thuật khác được định danh rõ. Các loại review không thay thế nhau.
- Ref/hash của đối tượng thực sự được review. Với plan, phải có plan content hash cùng case/validation/rules và các dependency đã pin tương ứng.
- Danh tính/tên reviewer, đơn vị và căn cứ được giao thẩm quyền; phạm vi thẩm quyền cần phù hợp nội dung kết luận.
- Kết luận, điều kiện kèm theo, các rule hoặc vấn đề kỹ thuật được xem xét và các phần không được xem xét.
- Ngày thực hiện, phạm vi chuyến/địa điểm/điều kiện áp dụng, thời hạn hoặc quy tắc hết hiệu lực và tái đánh giá được nêu rõ.
- Ref/hash file gốc và vị trí trong nguồn có kết luận/chữ ký/binding. Nội dung OCR chỉ là bản trích xuất để hỗ trợ đối chiếu.

Nếu nguồn không nêu ngày hết hiệu lực, không tự đặt một ngày hoặc suy ra hiệu lực vĩnh viễn. Cần ghi đúng điều kiện áp dụng/tái đánh giá theo nguồn và quy trình được xác nhận.

### 3.2 Sự kiện ghi nhận — ExternalReviewRegistration

Backend tạo sự kiện bất biến, pin hồ sơ statement và ghi:

- Principal của operator đang đăng nhập, thời gian ghi nhận và authentication event của **việc ghi nhận**.
- File đã nhận trong store, hash tính từ bytes thực và liên kết tới đối tượng đề nghị review.
- Nguồn nhận hồ sơ và trạng thái ban đầu là đã ghi nhận/chờ đối chiếu.
- Authority diễn đạt đúng nghĩa, ví dụ `SERVER_AUTHENTICATED_RECORDING_OF_EXTERNAL_EVIDENCE`.

Không điền authentication event của operator vào trường được hiểu là reviewer đã xác thực trong app. Không thay tên actor trong một receipt v0.2 rồi coi đó là migration hợp lệ.

### 3.3 Kết quả đối chiếu — ExternalReviewVerification

Kết quả riêng pin statement/registration, người được giao đối chiếu, thời gian, phương thức, bằng chứng và từng phần đạt/chưa đủ/từ chối:

1. File và nguồn được nhận đúng, bytes/hash khớp.
2. Danh tính và thẩm quyền reviewer đã được đối chiếu bằng cách nào.
3. Đúng nội dung/hash được review; đúng phạm vi, phiên bản, điều kiện và rule coverage.
4. Hiệu lực tại hành động đang xét; thời hạn hoặc điều kiện tái đánh giá.
5. Tình trạng thu hồi/thay thế và nguồn/thời điểm kiểm thông tin đó.

Không có nguồn để kiểm thu hồi thì ghi chưa xác minh, không suy ra “chưa bị thu hồi”. Tiêu chí độ mới của lần kiểm phải do quy trình áp dụng xác định; package không tự đặt một thời hạn chung cho mọi loại hồ sơ.

## 4. Binding tới plan phải có trong bằng chứng được review

Một attachment không trở thành review của plan hiện tại chỉ vì operator chọn plan trong danh sách. Bằng chứng được reviewer chấp nhận phải chỉ rõ đúng nội dung được xem xét, chẳng hạn hồ sơ xuất từ tool có plan hash được reviewer xác nhận hoặc một xác nhận bổ sung có binding tương đương theo quy trình đơn vị.

File thiếu binding vẫn được lưu để tra cứu nhưng giữ trạng thái chờ làm rõ. Bằng chứng duyệt support profile chỉ áp dụng cho profile/phạm vi của nó; không tự cấp chấp nhận cho mọi plan sử dụng profile đó.

Sửa tay, thay case/rules/profile hoặc thay tham số liên quan có thể làm review cũ không còn áp dụng. Hệ thống giữ review cũ cho lịch sử, đánh giá tác động và yêu cầu review/binding mới khi cần; không sửa ref trong hồ sơ cũ để chuyển nó sang nội dung mới.

## 5. Ghi nhận không tự tạo chấp nhận vận hành

| Mốc | Ý nghĩa được phép hiển thị |
|---|---|
| Đã nhận file | Có attachment trong store; chưa nói về danh tính, hiệu lực hoặc kết luận áp dụng |
| Đã ghi nhận hồ sơ ngoài app | Operator đã đăng ký một hồ sơ; vẫn có thể chờ đối chiếu |
| Đã đối chiếu bằng chứng | Các mục được ghi rõ đã được kiểm bằng phương thức và phạm vi đã nêu |
| Review có thể áp dụng cho hành động đang xét | Đúng hash/scope/coverage, còn hiệu lực, thông tin thu hồi đủ theo policy và các điều kiện tương ứng đã đáp ứng |
| Hết hiệu lực/thu hồi/không còn khớp | Giữ lịch sử, không dùng review đó để chấp nhận hành động mới |

Một kết luận chỉ được sử dụng cho việc chấp nhận có ý nghĩa vận hành khi có đủ nguồn, chủ thể/thẩm quyền, scope, hash, điều kiện hiệu lực và kiểm tra thu hồi hiện tại theo policy; đồng thời các điều kiện độc lập của plan và chuyến vẫn phải đáp ứng. Review bên ngoài không vô hiệu hóa hard constraints, user selection không thay review chuyên môn và CVF receipt không thay hai loại bằng chứng ấy.

Nếu là scan chữ ký trên giấy, UI ghi đúng “hồ sơ ký ngoài app, đã đối chiếu theo phương thức …”. Chỉ ghi “chữ ký số đã xác minh” khi thật sự có cơ chế kiểm tương ứng và evidence. Hash file chứng minh bytes khớp, không tự chứng minh chữ ký hoặc thẩm quyền.

## 6. Ca nghiệm thu phải bổ sung sau khi contract được chốt

| ID | Trường hợp | Kết quả cần chứng minh |
|---|---|---|
| ER-01 | Operator tải hồ sơ do reviewer ngoài app ký | Reviewer/recorder/verifier không bị nhập làm một actor; không phát sinh reviewer login giả |
| ER-02 | Agent gửi cùng payload và tự khai role operator | Backend từ chối hành động không được cấp; CVF ALLOW không bỏ qua quyền |
| ER-03 | File không có binding tới plan hoặc binding sai hash | Chỉ lưu hồ sơ chờ xử lý; không dùng cho chấp nhận plan hiện tại |
| ER-04 | Chỉ có review profile | Không tự đánh dấu plan đã được review hiện trường |
| ER-05 | Plan được sửa tay sau review | Review cũ giữ đúng nội dung cũ; bản mới phải đánh giá lại phạm vi áp dụng |
| ER-06 | Có scan chữ ký nhưng không có kiểm chữ ký số | UI/export nêu đúng phương thức và giới hạn bằng chứng |
| ER-07 | Thẩm quyền reviewer, thời hạn hoặc tình trạng thu hồi chưa được đối chiếu | Điều kiện yêu cầu bằng chứng đó vẫn chưa đủ; không mặc định chấp nhận |
| ER-08 | Một người vừa recorder vừa verifier được quy trình cho phép | Ghi đúng cùng người và hai hành động; không tuyên bố có review độc lập của người thứ hai |
| ER-09 | Restore một hồ sơ từng hợp lệ | Giữ lịch sử, kiểm điều kiện hiện tại trước hành động mới; không tự khôi phục quyền/hiệu lực cũ |

Các mã ER là yêu cầu nghiệm thu tương lai, không phải test đã chạy. Vòng local kế tiếp cần phản biện contract này, đối chiếu quy trình của đơn vị và chỉ rõ điều kiện cần owner/chuyên môn xác nhận trước khi triển khai.
