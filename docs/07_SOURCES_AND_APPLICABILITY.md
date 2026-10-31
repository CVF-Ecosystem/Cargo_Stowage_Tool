# Nguồn và phạm vi áp dụng của vòng R3

Ngày đối chiếu: 31-10-2026. Nguồn được phân loại theo khả năng chứng minh, không gom thành một mức uy tín chung.

## 1. Nguồn của dự án

| ID | Nguồn | Chứng minh được | Không chứng minh |
|---|---|---|---|
| P01 | V0.2 release ZIP nguyên bytes trong history | Spec/schema/reference/test được phát hành ở snapshot đã pin | App/CVF/solver sản xuất đã triển khai |
| P02 | R2 audit gốc trong inputs | Các nhận định và kết quả do reviewer R2 báo cáo | Chúng tôi đã trực tiếp thấy mọi file ở phiên R2; đặc biệt variant DOCX |
| P03 | 1.jpg | Quan sát vật thể/không gian nhìn thấy từ góc ảnh | Kích thước, khối lượng, máy đang hoạt động hoặc tải xích đã kiểm |
| P04 | 2.jpg | Nhóm hình dạng/tầng nhìn thấy | Packing unit chính xác, cùng tàu/chuyến với ảnh khác hoặc đủ profile |
| P05 | 3.jpg | Tương quan các nhóm hàng ở phần nhìn thấy | Tiếp xúc dưới tầng bị che, vật liệu/lashing đạt, toàn hầm |
| P06 | Receipt/log R3 | Kết quả lệnh/probe và hash đầu vào có thật | Test backend/auth/CVF/field chưa chạy |

Tên file, kích thước, SHA và bản gốc nằm trong source register. Ảnh giữ nguyên, không biến thành mesh/số đo hoặc case benchmark giả. Trích đoạn owner gửi trong chat là yêu cầu review; phần machine/source evidence dùng các tệp gốc.

## 2. Nguồn kỹ thuật công khai đã kiểm

### W01 — IMO, CSS Code

URL: https://www.imo.org/en/ourwork/safety/pages/css-code.aspx

Nguồn trực tiếp của IMO. Dùng để đối chiếu nguyên tắc chất xếp/chằng buộc gắn với lập kế hoạch, thực hiện, giám sát và người đủ năng lực. Không lấy trang giới thiệu làm bộ thông số kê/chồng hoặc kết luận áp dụng pháp lý tự động cho mọi sà lan của owner.

### W02 — CSS Code, Annex 7 qua cổng cơ quan hàng hải Hà Lan

URL: https://puc.overheid.nl/nsi/doc/PUC_2092_14/

Bản công bố trên Netherlands Regulatory Framework – Maritime; trang hiển thị phiên bản có lịch sử. Tham khảo phần heavy metal products về giới hạn tải boong/tank top và phân bố hàng. Đây không phải lời xác nhận đã kiểm mọi sửa đổi mới nhất hoặc quy chuẩn Việt Nam; local/chuyên môn phải xác định bản nguồn và phạm vi thật khi đăng ký rule.

### W03 — DNV, Steel Load Planner

URL: https://www.dnv.com/services/ship-classification-fleet-in-service/steel-load-planner/

Nguồn trực tiếp của đơn vị phát triển. Trang nêu việc đánh giá tải dùng mô hình kết cấu theo tàu; sản phẩm có phạm vi local-strength riêng và vẫn tách chằng buộc/thao tác. Dùng làm ví dụ cho việc phần mềm phải khai rõ lớp bài toán đã đánh giá. Không coi đây là đề nghị mua, mô tả tính năng SCST hoặc nguồn thông số cho bó thanh/ống.

## 3. Cách dùng nguồn trong quyết định thiết kế

Những đề nghị như integer grams, source registry, field confirmation, role model, profile templates, TP/MVP và UI là quyết định thiết kế của vòng review, được đánh giá bằng logic và evidence dự án. Chúng không được trình bày như yêu cầu của IMO/DNV.

Ví dụ AABB đối với tiết diện tròn là nhận xét hình học về mô hình: bao chữ nhật có thể giao nhau khi hình tròn bên trong không giao nhau. Không cần suy một khoảng cách hoặc dạng xếp cụ thể từ ảnh để nhận ra hạn chế này. Việc hạn chế đó có ảnh hưởng pilot hay không vẫn cần manifest và case thật.

Không thêm hệ số ma sát, khoảng kê, chiều dày gỗ, tải cho phép hoặc số tầng mặc định từ tài liệu tham khảo. Mọi giới hạn operational phải có nguồn, phạm vi, phiên bản, người review và điều kiện áp dụng trong registry của dự án.
