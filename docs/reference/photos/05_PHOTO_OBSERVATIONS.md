# Đối chiếu ba ảnh nghiệp vụ với baseline

**Package:** SCST-REVIEW-0.3. **Trạng thái:** REVIEW_BASELINE_FOR_LOCAL_VERIFICATION; chưa phải Final Baseline.

Ảnh là nguồn tham khảo để nhận diện dạng bài toán và thiết kế acceptance. Chúng không phải manifest, bản đo hầm, hồ sơ chịu tải, profile kê/đỡ đã duyệt hoặc bằng chứng một cách xếp cụ thể an toàn. Phân tích này không suy kích thước, khối lượng, hệ số lấp đầy hay rating từ pixels.

## 1. Nhận diện đúng ảnh

Tên file là khóa đối chiếu, không dùng thứ tự ảnh trong khung chat. **Thiết bị bánh xích xuất hiện ở 1.jpg**, không phải 3.jpg như đoạn khuyến nghị được trích dẫn. Không đủ dữ liệu khẳng định các ảnh cùng tàu, cùng chuyến hoặc cùng giai đoạn xếp.

Ba ảnh không đồng nghĩa ba case nghiệm thu. Một case nghiệm thu cần manifest, mô hình hầm, thông số/profile, nguồn xác minh và expected/checklist độc lập. Có thể dùng ảnh để giúp người vận hành giải thích case, nhưng không tạo các giá trị còn thiếu bằng suy đoán.

## 2. Ảnh 1.jpg

### Quan sát được

- Có nhiều nhóm vật dài theo chiều dọc khung hình, ràng/bó thành các nhóm; hai bên và trung tâm có ngoại hình khác nhau.
- Có vật liệu kê nhìn thấy theo hướng ngang và nhiều vùng bị hàng che khuất.
- Phía dưới ảnh có các vật thể dạng cuộn/bó vòng, khác hình thức với các nhóm hàng dài.
- Thiết bị bánh xích nằm trong vùng hàng; có tấm/vật liệu kê bên dưới hoặc gần vùng bánh xích.
- Thành hầm có sườn và các phần biên; ảnh phối cảnh không cung cấp hình học đo được.

### Chưa xác định

Không biết loại hàng/đơn vị manifest của từng nhóm, số lượng đầy đủ, mass, số tầng bị che, cấu hình tiếp xúc bên dưới, đặc tính vật kê hoặc trạng thái vận hành của thiết bị. Không xác định được tải thiết bị, diện tích chịu tải, đường truyền lực, khả năng đỡ của hàng hoặc đáy hầm.

### Hệ quả yêu cầu

- Không ép mọi vật thể thành một trong hai cargo enums v0.2; cần đối chiếu manifest và danh mục pilot.
- Cần hiển thị theo nhóm và lớp, đồng thời cho xem support relations có nguồn dữ liệu.
- Scenario có thiết bị/tải tạm cần được khai báo và review đúng phạm vi. Không lấy một final cargo layout làm chứng cứ cho thiết bị hoạt động trên hàng.
- Các vật thể ngoài phạm vi vẫn phải được đối soát; không bỏ khỏi cảnh tính toán nhưng trình kết quả như phương án toàn hầm.

## 3. Ảnh 2.jpg

### Quan sát được

- Có nhiều tầng/cao độ, với vùng các đầu ống tròn màu vàng xen giữa nhiều nhóm bó/tiết diện khác.
- Có vật kê nhìn thấy tại một số vị trí; mặt trước khối hàng không là một mặt phẳng đồng nhất.
- Có các vật thể dạng cuộn ở phía dưới ảnh.
- Vùng miệng hầm và vùng hàng phía dưới có các phần biên khác nhau trong phối cảnh.

### Chưa xác định

Không xác định mọi nhóm là thép thanh, ống, tiết diện định hình hay loại khác. Ảnh không đủ cho biết một đầu ống tương ứng một CargoUnit riêng hay thành phần của bó. Không suy ra được chiều dài, đường kính/thành ống, khối lượng, số tầng đầy đủ, khoảng đỡ, nesting chính xác hoặc biên hầm theo cao độ.

### Hệ quả yêu cầu

- MVP phải được kiểm trên hàng nhiều kích thước/nhóm và nhiều tầng, có dữ liệu thật hoặc dữ liệu đã ẩn danh nhưng được đối chiếu.
- Cần phân biệt hỗ trợ nhiều nhóm cạnh nhau với hỗ trợ các nhóm khác profile chồng lên nhau. Nếu pilot cần kiểu thứ hai, phải có cặp template được duyệt và ca thử tương ứng.
- Cần đánh giá mức hữu ích của collision envelopes trên cấu hình ống thật; không tự mở hình trụ/lồng khe chỉ để ảnh 3D giống mẫu.
- BOX có thể giữ làm vùng nội tiếp được xác minh. Nếu xấp xỉ ấy không đáp ứng case đại diện thì cần đổi model trước khi MVP được nghiệm thu.

## 4. Ảnh 3.jpg

### Quan sát được

- Các bó/nhóm thanh dài ở phía trên có đầu nhỏ tập trung thành từng bó; phía dưới là nhiều hàng các vật thể ống tròn.
- Có các lớp khác nhau, vật kê/ràng nhìn thấy và vùng dưới bị khuất.
- Nhìn rõ sự khác biệt giữa bao ngoài của một nhóm bó với các vật tròn ở vùng bên dưới.

### Chưa xác định

Không biết bó trên tựa vào những ống/bó/vật kê nào, phần tiếp xúc khuất ra sao, cấu hình chống lăn và rating được duyệt là gì. Không đủ chứng cứ để xác nhận quan hệ đỡ, chiều dày kê, số tầng cho phép hoặc tính hợp lệ của cách xếp trong ảnh.

### Hệ quả yêu cầu

- AABB chỉ mô tả chiếm chỗ; không được coi toàn diện tích đáy AABB là tiếp xúc chịu lực thật.
- Cần cấu hình kê/xếp được chấp thuận, có phạm vi trên/dưới và điều kiện dữ liệu kiểm được.
- Viewer cần cho người vận hành kiểm lớp và quan hệ support từ model, đồng thời phân biệt phần chưa được đánh giá; không vẽ mũi tên lực hoặc nhãn tải có vẻ xác định khi chưa có dữ liệu.
- Mẫu nhiều tầng của Technical Proof cần được nối tới case pilot có nguồn; ảnh này không tự cung cấp profile hay expected “an toàn”.

## 5. Những điều ảnh làm thay đổi và những điều ảnh không quyết định

| Chủ đề | Kết luận đối chiếu |
|---|---|
| Đích nghiệm thu | Cần tách Technical Proof và MVP nghiệp vụ; không nhận bản một tầng/BOX synthetic như hoàn thành nhu cầu nhiều tầng được người dùng nêu. |
| Hàng khác kích thước | V0.2 đã có dimensions từng unit. Cần nghiệm thu trên case đại diện, không nhận định sai rằng contract bắt mọi hộp giống nhau. |
| Support | V0.2 có model nhiều tầng có gate; vẫn thiếu profile thật và chứng minh model bao phủ cấu hình pilot. |
| Hầm đang có hàng | Ảnh chỉ cho thấy trạng thái đã xếp. Điều kiện initial empty hay incremental planning cần hỏi theo công việc thực. |
| Loại hàng | Ảnh phát hiện khả năng ngoài scope, không cho phép tự gắn nhãn commodity hoặc tự đổi đơn vị bó/ống riêng. |
| Hình học thật | Ảnh đủ để yêu cầu kiểm xấp xỉ hầm; chưa đủ chọn mesh, polygon, góc nghiêng hoặc số đo. |
| Máy trên hàng | Là tín hiệu phải quản lý phạm vi tải tạm trong scenario; chưa có dữ liệu cho phép tính hoặc chấp thuận hoạt động đó. |
| Giá trị 3D | Cần thao tác xem lớp/nhóm/đỡ và đối soát theo ID; mức đẹp của ảnh render không phải bằng chứng nghiệp vụ hoặc kỹ thuật. |

## 6. Dữ liệu đi kèm cần thu cho case nghiệm thu

Một bộ case cần manifest đầy đủ và đơn vị hàng rõ; số đo/bản vẽ vùng sử dụng và exclusions; trạng thái ban đầu; profiles/templates áp dụng; các hạn mức và basis khối lượng; phạm vi thiết bị/tải tạm nếu có; người cung cấp và người đối chiếu; mục tiêu required/optional; kết quả/checklist mong đợi được xác lập độc lập.

Nếu tái dựng một bố trí lịch sử để so sánh, phải ghi đó là bố trí quan sát/tham khảo. Không mặc nhiên dùng việc “đã từng xếp như vậy” làm kết luận hợp lệ hoặc an toàn. Tool có thể phát hiện dữ liệu thiếu hoặc điều kiện ngoài mô hình trong chính bố trí lịch sử đó.

Các nội dung này được chuyển thành mô hình và điều kiện kiểm trong `02_OPERATIONAL_MODEL.md` cùng tài liệu acceptance của baseline. Chưa có dữ liệu/tham số được tự điền thêm vào schema v0.2 từ ba ảnh.
