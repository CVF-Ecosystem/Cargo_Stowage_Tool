# Technical Proof và MVP nghiệp vụ

**SCST-REVIEW-0.3 — tiêu chí SPECIFIED_FOR_REVIEW.** Các ca dưới đây chưa phải kết quả thực thi.

## 1. Hai mốc khác nhau

| Nội dung | Technical Proof (TP) | MVP nghiệp vụ (MVP-NV) |
|---|---|---|
| Mục tiêu | Kiểm chứng thành phần và mô hình đã khai báo | Hoàn thành công việc lập phương án có ích trên case đại diện |
| Đầu vào | Synthetic/fixture nhỏ có oracle | Manifest, số đo và profile có nguồn của case được phép dùng |
| Hầm | BOX/biên biết chính xác để kiểm lỗi | Miền xếp đại diện hầm thật; inner BOX chỉ khi xác minh được fidelity và giá trị sử dụng |
| Hàng | Đơn vị/hình học được fixture định nghĩa | Đúng loại, đóng gói, kích thước và khối lượng từng đơn vị; nhận diện mọi hàng ngoài phạm vi |
| Tầng | Một lớp đủ để kiểm một bước; nhiều lớp synthetic dùng kiểm thuật toán | Nhiều tầng và nhiều nhóm theo profile được duyệt; không hạ thành một tầng vì thiếu profile |
| Support | Contract đơn giản, biết giới hạn | Profile/quan hệ trên-dưới phù hợp case; thiếu review thì giữ blocker |
| Solver | Oracle nhỏ độc lập, trạng thái/proof đúng | Tạo được phương án đáp ứng mục tiêu case, có chỉnh sửa và kiểm lại; đo trên máy/quy mô thật |
| Viewer | Geometry/transform/render đúng | Người dùng tìm/kiểm từng unit, nhóm, lớp, quan hệ đỡ và lỗi, đối soát được báo cáo |
| Kết luận | Đúng trong mô hình và phạm vi đã kiểm | Đạt tiêu chí sản phẩm cho phạm vi/case được nghiệm thu |

Không tự nâng một mốc bằng cách đổi nhãn. `CONTRACT_REFERENCE_TESTS_PASS` v0.2 chưa là TP ứng dụng vì còn thiếu backend/solver/UI chạy thật. TP đạt chưa đủ MVP-NV. MVP-NV đạt không làm mọi plan/chuyến được chấp thuận hiện trường; review phương án cụ thể vẫn xét hồ sơ, phạm vi, thời gian và điều kiện.

## 2. Mapping với gates v0.2

- G0 chốt phạm vi/case/đơn vị hàng/vai trò và tiêu chí trước nghiệm thu; hiện chưa có owner sign-off cho phạm vi thu hẹp.
- G1/G2/G3/G4a cung cấp bằng chứng kỹ thuật của dữ liệu, validator, solver, core UI/API. Synthetic checks chỉ đóng đúng phần được test.
- G4b bắt buộc trước khi bật Agent/CVF actions; core AI-off có thể chạy ở phạm vi đã tắt capability và có evidence.
- G5 cùng các tiêu chí MB bên dưới chứng minh mức phù hợp nghiệp vụ trên dữ liệu/điều kiện được review.

Trạng thái lúc bàn giao v0.3: TP ứng dụng `NOT_EVALUATED`, MVP-NV `NOT_EVALUATED`, chấp thuận từng plan `NOT_GRANTED`. Evidence cũ chỉ là reference contract; chưa có quyền ghi PASS cho các gate sản phẩm.

## 3. Bộ case tối thiểu đề nghị

Đây là ngưỡng kiểm chứng của dự án để local/owner xác nhận, không phải quy định chuyên ngành:

1. **CASE-A:** manifest thật hoặc đã ẩn danh có chuỗi nguồn, một hầm đại diện, nhiều tầng và nhiều kích thước trong nhóm hàng pilot; có bố trí tham chiếu cùng review/profile phù hợp.
2. **CASE-B:** một case được lập hồ sơ độc lập có nhiều nhóm hàng trong cùng hầm. Nếu nghiệp vụ yêu cầu chồng khác profile như tình huống ảnh gợi ra, case phải có đúng quan hệ ấy và profile chấp thuận; hai loại đặt cạnh nhau không thay mixed vertical support.
3. **CASE-C:** ca từ chối/chờ đúng, ví dụ thiếu profile, loại hàng chưa hỗ trợ, unit chưa xác minh hoặc trạng thái tải tạm chưa được review; phải giải thích nguyên nhân và không nâng nhãn.

Hai ảnh cùng góc/chuyến không được tự tính là hai case. Ảnh gốc hiện có chỉ là tham khảo nghiệp vụ; không đủ manifest, geometry, dates, masses và profile để chạy CASE-A/B. Nếu target pilot là new loading từ hầm trống, phải xác nhận trước khi dùng bộ case; nếu thường xuyên replanning hầm đã có hàng thì cần sửa scope/contract trước freeze.

## 4. Tiêu chí nghiệm thu MVP-NV

| ID | Điều kiện cần chứng minh | Oracle/bằng chứng |
|---|---|---|
| MB-01 | Phạm vi pilot phù hợp công việc owner thực làm | G0/case intake đã xác nhận, không suy từ ảnh |
| MB-02 | Toàn manifest được đối soát, đơn vị nguyên vẹn, hàng ngoài scope rõ | Unit IDs, mass totals, ba tập placed/unplaced/excluded; phân loại unsupported tại intake/preflight phải được xử lý rõ, không mất dòng khó |
| MB-03 | Vùng hầm và margin có căn cứ, placement không vượt vùng thật đã được duyệt | Measurement/drawing refs, mapping geometry và đối chứng độc lập ở các cao độ liên quan |
| MB-04 | Nhiều tầng hoạt động trong profile áp dụng | Case nhiều tầng, support graph/template, limits/source/scope, negative missing-support/profile tests |
| MB-05 | Phối hợp nhóm đúng mục tiêu, mixed support chỉ khi được duyệt | Profile compatibility có chiều, case phù hợp; reject cặp không cho phép |
| MB-06 | Mô hình có fidelity đủ để giải case | So với bố trí tham chiếu cùng constraints; các loại bỏ do envelope được giải thích. Không chấp nhận chỉ hiển thị một subset tùy ý của manifest |
| MB-07 | Tự động tạo được đề xuất và sửa tay có kiểm | Command/build/config/input; auto candidate, independent validation; sửa vị trí/tầng/yaw tạo version và receipt mới |
| MB-08 | Mục tiêu required/optional và trạng thái solver đúng | Oracle/benchmark được khai trước test; timeout không proof; thuật toán gần đúng không tuyên bố tối ưu nếu chưa có căn cứ |
| MB-09 | Viewer phục vụ người dùng thật | Người vận hành tìm đúng ID, cô lập nhóm/lớp, xem support/lỗi, đối chiếu cùng unit ở 2D/3D/bảng; ghi thao tác và lỗi thực |
| MB-10 | PDF/XLSX khớp snapshot | Unit/tổng/đơn vị/hash/coverage/review status khớp backend, mở được trên máy mục tiêu |
| MB-11 | Dữ liệu operational có nguồn và confirmation đủ | ADM acceptance qua backend/persistence; testOnly/synthetic/field-link thiếu bị chặn |
| MB-12 | Vai trò selection/review đúng | Operator và reviewer không bị nhập làm một; ER acceptance qua runtime thật; current validity và binding plan đúng |
| MB-13 | Case có thiết bị/tải tạm được xét đúng phạm vi | Ghi stage/phạm vi, hồ sơ review cần thiết; không dùng tải chuyến cuối để bỏ tải thao tác; thiếu thì không field handoff |
| MB-14 | Sử dụng được trên máy và quy mô mục tiêu | Máy/OS, số unit thường/lớn, time budget, parse/solve/revalidate/render/export và khả năng hủy/khôi phục được đo |

`unsupported` là phân loại/lỗi ở intake–preflight, không phải bucket thứ tư của PlanContent v0.2. Nó không tự trở thành excluded; case thiếu khả năng mô hình cho hàng bắt buộc phải được xử lý trước khi tạo/chọn phương án đáp ứng mục tiêu. Muốn thêm trạng thái dữ liệu mới phải chốt contract delta rõ.

Performance target và mức sai khác chấp nhận của approximation phải được thống nhất **trước** lần nghiệm thu tương ứng, dựa trên case thật. Chưa có các giá trị đó thì đánh dấu pending, không điền một số tùy ý rồi gọi PASS. Mục tiêu tối thiểu của case required là đáp ứng đúng tập hàng trong phạm vi và constraints đã khai; không tối ưu việc chọn case cho dễ đạt.

## 5. Báo cáo evidence

Mỗi test cần test ID, requirement ID, source commit/build, exact command, timestamp/timezone, runtime/dependencies, input/rules/profile/source hashes, expected, actual, verdict và log. Đánh giá thủ công ghi người làm, nhiệm vụ, quan sát và dữ liệu đối chiếu. Screenshot bổ trợ, không thay oracle hoặc thông số kỹ thuật.

LAT-001…025 của v0.2 vẫn là danh mục kiểm cần reconcile. ADM, ER và MB trong v0.3 bổ sung điều kiện; chúng là tiêu chí tương lai. Không cộng tất cả mã bảng vào số test đã chạy. Nếu có trùng mục tiêu, local mapping về một test đủ bằng chứng thay vì tạo nhiều test hình thức.

## 6. Chốt sau review local

Local trả phạm vi/case, contract delta, test mapping và các điểm còn phụ thuộc dữ liệu/chuyên môn. Sau khi owner/reviewer xử lý, mới chốt Final Baseline và xây roadmap/treeview triển khai. Vòng này không yêu cầu một roadmap hoàn chỉnh để thay cho bằng chứng phản biện.
