# Mẫu thu thập case nghiệp vụ

Mẫu chưa điền. Dùng khi có nguồn thật; không cần owner trả lời toàn bộ để local bắt đầu review package. Không lấy kích thước/tải trọng từ ảnh.

## 1. Công việc cần làm

1. Công việc thường gặp là lập phương án mới từ hầm trống, hay bổ sung/điều chỉnh hầm đã có hàng? Ghi ví dụ một chuyến.
2. Một dòng manifest là một bó, một ống, nhiều bó/ống hay một lô? Ví dụ: dòng ghi 10 bó thì có khối lượng/kích thước từng bó không?
3. Những loại nào bắt buộc giải trong pilot: bó thanh, bó ống, từng ống, cuộn, loại khác? Nếu ngoài phạm vi, có được chọn case khác thực sự đại diện không?
4. Có cần đặt nhóm này lên nhóm khác không? Nêu quan hệ đang dùng thực tế; chưa có hồ sơ kê/chồng thì ghi chưa có.
5. Thiết bị có đi/làm việc trên hàng trong quy trình của case này không? Ở bước nào, có hồ sơ/quy trình đã duyệt nào? Không tự nhập một tải ước đoán từ ảnh.

## 2. Nguồn đính kèm

| Dữ liệu | Nguồn cần có | Tình trạng |
|---|---|---|
| Manifest | File gốc, đơn vị, IDs, số kiện, mass/dimensions theo đơn vị và tổng | CHƯA_CÓ |
| Phương tiện/chuyến | Identity, cargo limit nguồn có thẩm quyền, thời gian/phạm vi, voyage allowance đúng basis | CHƯA_CÓ |
| Hầm | Bản vẽ/số đo, phương pháp, frame, vật cản, khoảng hở, miệng hầm/điều kiện tiếp cận | CHƯA_CÓ |
| Kê/chồng | Profile hoặc hướng dẫn có nguồn/phạm vi, cách kê, quan hệ trên-dưới, giới hạn, người review | CHƯA_CÓ |
| Bố trí tham chiếu | Bản vẽ/ghi chép/ảnh có liên hệ tới cùng manifest; mức review đã thực hiện | CHƯA_CÓ |
| Vai trò | Ai nhập/xác nhận/chọn; ai review kỹ thuật; hồ sơ bên ngoài hoặc tài khoản riêng | CHƯA_CÓ |
| Máy/quy mô | PC/OS, quyền cài, số unit thường/lớn, thời gian làm hiện tại, yêu cầu chờ/phản hồi | CHƯA_CÓ |

## 3. Điều kiện case được dùng nghiệm thu

Nguồn phải liên hệ cùng case; ảnh, manifest và profile không được ghép từ các chuyến khác mà không ghi rõ. Case mới/ẩn danh giữ mapping và lineage phù hợp. Dữ liệu giả lập dùng test kỹ thuật phải được ghi TEST_ONLY.

Người vận hành và reviewer thống nhất trước: tập hàng cần xếp, phần được loại, các constraints áp dụng, kết quả tối thiểu cần đạt và những review ngoài phạm vi tính toán. Không xem việc một phương án từng được làm là tự động có chứng nhận an toàn.
