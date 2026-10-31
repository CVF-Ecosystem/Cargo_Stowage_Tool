# Nguồn tài liệu và đối chiếu lịch sử

**Package:** `SCST-REVIEW-0.3`  
**Trạng thái:** `REVIEW_ONLY` / `NOT_FINAL`  
**Ngày đối chiếu:** 31-10-2026

## 1. Nguyên tắc

Tên file, hash bytes và nội dung trích xuất là các mức nhận diện khác nhau. Hai file cùng tên không mặc nhiên là cùng bản. Hai DOCX có văn bản trích xuất giống nhau không mặc nhiên trùng bytes. Hash chỉ chứng minh tính khớp của bytes được đối chiếu; không tự chứng minh tác giả, chữ ký, nguồn thẩm quyền hoặc độ đúng nghiệp vụ.

Bản v0.2 đã phát hành được giữ làm lịch sử/tham chiếu kỹ thuật. Nội dung hoặc phạm vi của các contract tham chiếu đó không được âm thầm đổi rồi trình bày như v0.2 nguyên gốc. Trạng thái và yêu cầu đang đề xuất cho vòng review v0.3 phải được đọc theo tài liệu ở cấp package hiện tại.

## 2. Phản biện R2 về R1 DOCX

R2 báo rằng R1 DOCX nằm trong v0.2 khác bytes so với một R1 DOCX được tải lên trong phiên review của họ, dù phần đoạn văn và bảng trích xuất tương đương. Báo cáo R2 hiện tại không kèm bytes hoặc SHA-256 của bản DOCX khác đó.

Trong vòng này, bản DOCX khác mà R2 nói tới **chưa được cung cấp**. Vì vậy không thể đối chiếu cặp file của R2 hoặc xác minh nguyên nhân. Không suy diễn rằng đã re-export, đã chỉnh nội dung, có lỗi đóng gói, hoặc R2 nhận định sai.

Disposition của phần chưa xác minh: **`PENDING_ALTERNATE_SOURCE_BYTES_OR_SHA`**. Giới hạn này được giữ công khai và không chặn việc phản biện các vấn đề nghiệp vụ/contract độc lập.

## 3. Những bytes thực sự đã đối chiếu

Bằng chứng máy đọc nằm ở `evidence/available_provenance_receipt.json`. Receipt ghi vị trí đã đọc, kích thước, hash và những điều chưa biết; các đường dẫn trong receipt là nguồn tại workspace thực hiện kiểm, không phải đường dẫn bắt buộc trên máy nhận package.

### R1 DOCX

Bảy vị trí R1 DOCX có thể truy cập trong workspace phát hành đều trùng bytes:

| Vị trí được đối chiếu | Kết quả |
|---|---|
| Deliverable R1 DOCX trực tiếp | Khớp hash chung |
| R1 DOCX trong thư mục local_handoff | Khớp hash chung |
| R1 DOCX trong history của package v0.2 | Khớp hash chung |
| R1 DOCX trong thư mục giải nén kiểm portability | Khớp hash chung |
| R1 DOCX bên trong R1 handoff ZIP | Khớp hash chung |
| R1 DOCX bên trong v0.2 release ZIP | Khớp hash chung |
| R1 DOCX bên trong R1 handoff ZIP lồng trong v0.2 | Khớp hash chung |

Kích thước của từng bản: **59,296 bytes**.

SHA-256 chung:

```text
adf11a5682ea541d01a5b3ed348c6274938532a45ced23c49e91fa6ea6a08d8f
```

Kết luận được phép: **bản R1 đã pin trong v0.2 khớp byte với các bản nguồn R1 hiện có và đã được đọc trong workspace phát hành**. Kết luận này không mở rộng sang mọi file mang cùng tên ở các phiên khác.

### Baseline v0.1

ZIP v0.1 nằm trong v0.2 đã được đọc và so sánh bytes với ZIP v0.1 upload gốc hiện có; chúng trùng nhau. SHA-256:

```text
511bd790a07b880c734df5d8e730c3a5a71c00f1affc64c01a92159a76ceda9e
```

### v0.2 release ZIP đã nhận diện

```text
6f587938f48b24daef5eaf0ba3fcab7532ec0397c3d2f7a39ca2caf686da44df
```

### Báo cáo R2 được dùng cho vòng này

`SCST_v0.2_INDEPENDENT_R2_AUDIT.md` có SHA-256:

```text
a64c1f3cc228bda0349fbf5bf3e143bd7aaad12e802d495aeaa7dd6ed3f1463a
```

Các hash trên nhận diện đúng các nguồn đã đọc; chúng không phải chữ ký của reviewer hoặc dấu chứng nhận nội dung.

## 4. Cách xử lý khi có bản R1 khác

Nếu bản DOCX mà R2 đã dùng được cung cấp sau này, giữ nó như một variant riêng kèm bytes/hash và nguồn nhận. Đối chiếu bytes, nội dung tài liệu và thông tin nguồn có thật; chỉ ghi việc chuyển đổi/re-export khi có bằng chứng về bước đó. Không ghi đè bản đã pin hoặc sửa provenance để làm mất dấu chênh lệch.

Nếu mới chỉ có hash, có thể xác định khớp/khác với bản đã pin nhưng chưa thể kết luận nội dung khác ở đâu. Kết quả trích xuất tương đương do R2 báo vẫn phải được ghi là kết quả R2 báo, không thay cho việc tự đọc cả hai file.

## 5. Ảnh nghiệp vụ và nguồn vận hành

Ba ảnh do người dùng cung cấp là nguồn tham khảo cho yêu cầu và các tình huống cần xét. Chúng không cung cấp tự động kích thước, khối lượng, tải cho phép, profile kê/chồng, danh tính tàu hoặc chứng nhận một cách xếp là an toàn. Khi trích một nhận xét, chỉ rõ file ảnh và vùng/đặc điểm quan sát được; tách quan sát khỏi suy luận và thông tin cần xác nhận.

Ảnh, báo cáo R1/R2 và fixtures tổng hợp có loại nguồn khác nhau. Không dùng ảnh hoặc báo cáo thiết kế để thay hồ sơ kỹ thuật thật; không đổi `testOnly` của fixture để biến nó thành đầu vào vận hành. Các nguồn thật sau này phải đi qua contract intake/provenance và quy trình xác nhận đã chốt.
