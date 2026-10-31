# V1.1 — Kiểm cách tính và quyết định tích hợp

Status: SOURCE_REVIEWED

Gói dùng được cho luồng đặt thử từng **bó ống thép**. Mô hình sà lan không đổi: GLB trong gói mới giống từng byte với asset đã tích hợp. Kiểm manifest đạt 22/22 file; không chỉnh workbook, dữ liệu chuẩn hóa hay mô hình gốc. Phạm vi kiểm là cách tính và ánh xạ cần cho app, theo yêu cầu owner; không kiểm toán lại toàn bộ Excel.

## Kết quả đối soát

| Nội dung | Kết quả |
|---|---|
| Nhóm nguồn | 31, giữ riêng theo Sheet1 và dòng 2–32; không dùng STT làm khóa duy nhất |
| Bó / ống | 1.076 bó / 21.226 ống |
| Tổng O trong Excel | 1.125,52 tấn |
| Tổng tính từ K × L × M | 1.125,55103 tấn |
| Chênh lệch | 31,03 kg, tương ứng làm tròn khối lượng theo dòng |
| CBM nguồn | 1.130,96964733156 m³ |
| Tổng khối bao I × P × Q × M | 1.157,54318105797 m³ |
| Chênh CBM | 26,57353372641 m³; R23:R26 chưa nhân số bó |
| Kiểm công thức được importer hỗ trợ | 174, không lệch cached value quá 10⁻⁹ |
| Kích thước nguồn | 93 giá trị I/P/Q đổi chính xác sang µm nguyên; 55 giá trị có phần lẻ mm |

[Receipt tính toán](SCST_PIPE_LIST_EVIDENCE/calculation-receipt.json) ghi hash workbook, đối chiếu raw XML các cột cần thiết, quy tắc 15 chữ số có nghĩa và kết quả từng nhóm. Chạy lại importer với precision 40 như CLI cho kết quả trùng normalized JSON cung cấp. Quy tắc này loại đuôi nhị phân của Excel, không phải thay số đo nguồn.

## Cách dùng trong app

- **Khối lượng bó = K (kg/ống) × L (ống/bó)**, lưu số nguyên gram. Giữ tổng O để so sánh. Đây là khối lượng tính từ list, chưa phải khối lượng cân từng bó. Không dùng mặc định O/M của gói: phân bổ tổng làm tròn không cần thiết khi đã có K và L; ở một số nhóm còn tạo phần lẻ gram.
- Khối bao dùng I/P/Q chính xác; lưu µm nguyên để không làm tròn kích thước khi kiểm giao nhau hoặc dựng 3D. Trường mm tương thích chỉ là giá trị làm tròn lên; geometry nguồn dùng µm. Tọa độ đặt vẫn nhập mm.
- Sinh ID từ dòng nguồn và số thứ tự bó, khởi đầu chưa bố trí. List chưa gắn với tàu/chuyến cụ thể; owner nạp rõ vào phương án đang chọn. Chỉ dựng mesh của các bó đã đặt.
- Giữ cảnh báo nguồn. 16 bó thuộc dòng 22/31/32 có 5 ống nhưng khối bao vuông chỉ rộng/cao 2 đường kính; cần xác minh bố trí hoặc kích thước. Không tự sửa khối bao. J17 là hằng số, giữ nguyên; nhãn inch có cảnh báo vẫn giữ. Chưa có packing sketch để dựng từng ống.

## Ranh giới

[SPEC](../specs/SCST_PIPE_LIST.md) và [work order](../work_orders/SCST_PIPE_LIST.md) giới hạn lần này ở nhập list đã chuẩn hóa, chọn/đặt/bỏ/xoay từng bó, kiểm và lưu/mở. Không xây importer Excel tổng quát, planner, nhiều tầng hoặc sửa mô hình tàu. Hầm vẫn là ước tính theo profile cũ; tổng thể tích hoặc tổng khối lượng không chứng minh toàn bộ list xếp vừa. Kết quả triển khai và nghiệm thu kỹ thuật được ghi riêng trong review sau BUILD; nghiệm thu nghiệp vụ/vận hành chưa có.
