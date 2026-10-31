# Bằng chứng kiểm tra vòng R3

**Phạm vi:** kiểm tính toàn vẹn nguồn, tái lập contract reference v0.2 và các nhận định R2. Không chạy backend/solver/UI/CVF production hoặc review kỹ thuật thực địa.

## 1. Kết quả đã quan sát

Lần chạy dùng bản v0.3 giải nén ở thư mục độc lập. Wrapper tiếp tục giải nén v0.2 nguyên bytes trong history vào vùng output riêng, kiểm checksum rồi chạy suite và probes. Mã wrapper/probe được băm trong receipt; bản phát hành cuối không đổi hai mã đã chạy này.

| Hạng mục | Actual |
|---|---|
| Thời gian bắt đầu/kết thúc UTC | 2026-10-31T07:17:42.794124+00:00 / 2026-10-31T07:17:44.403723+00:00 |
| Python / jsonschema | 3.12.14 / 4.26.0 |
| Platform | Linux-6.18.57-x86_64-with-glibc2.39 |
| V0.2 checksum | 65/65 tệp được liệt kê khớp |
| V0.2 reference suite | 86 tests, 0 failures, 0 errors, 0 skipped |
| Thời gian suite | 1.221 giây trên fixtures nhỏ; không là benchmark ứng dụng |
| Schema probes R3 | 4 probe; schema nhận 3, từ chối 1 như dự kiến |
| Quan sát default reference | operationalEligible=false |
| File R1 đã đối chiếu riêng | 7 vị trí hiện có cùng bytes/hash; variant R2 nói tới chưa có |

**Không cộng thành “91 test ứng dụng”.** 86 là suite tham chiếu; 5 là các quan sát probe về ranh giới schema/reference. Các mã LAT/ADM/ER/MB là yêu cầu nghiệm thu tương lai.

## 2. Probe results và cách hiểu

| Probe | Actual | Ý nghĩa |
|---|---|---|
| testOnly=false manifest có nguồn/mass synthetic | SCHEMA_ACCEPTED | Cần invariant admission/backend; chưa chứng minh runtime bypass |
| testOnly=false vessel có evidence synthetic | SCHEMA_ACCEPTED | Schema không đối chiếu registry hoặc nguồn thật |
| Đổi sourceLineId/giá trị/tổng theo kiểu hợp schema nhưng không có field binding | SCHEMA_ACCEPTED | Chưa có resolver/confirmation chain trong schema đó |
| massKg = 2000.5 | SCHEMA_REJECTED | Contract integer kg đang hoạt động đúng policy cũ |
| validate_bundle không fixture mode | operationalEligible=false | Reference không có đường production cấp điều kiện vận hành |

## 3. File bằng chứng

- `review_replay_receipt.json`: exact commands, cwd, thời gian, SHA wrapper/probe và logs của từng bước.
- `v02_checksum.log`: output checksum của v0.2 nguyên bytes.
- `v02_reference_tests.log`, `v02_contract_checks.log`: output suite.
- `v02_contract_check_receipt.json`: từng test, môi trường, hash inputs và giới hạn.
- `r2_contract_probes.log`, `r2_contract_probe_receipt.json`: từng quan sát và input hashes.
- `available_provenance_receipt.json`: đối chiếu bảy bản R1/v0.1/v0.2 tại các vị trí thật đã quan sát.
- `SOURCE_REGISTER.json`: hash/kích thước input R2, ảnh và ZIP v0.2 được đóng gói không biến đổi.

Đường dẫn tuyệt đối trong receipt là nơi lệnh thực sự đã chạy; không phải đường dẫn người nhận phải tạo giống. Dùng các lệnh portable bên dưới tại thư mục giải nén của mình. Lần chạy này dùng cùng môi trường Linux/dependency đã có, không phải chứng nhận cài mới trên Windows/macOS.

## 4. Cách chạy lại

Tại thư mục gốc v0.3:

```text
python tooling/verify_package.py
python -m venv ../scst-review-env
```

Chọn interpreter của môi trường vừa tạo: Windows thường `..\scst-review-env\Scripts\python.exe`; Linux/macOS thường `../scst-review-env/bin/python`. Dùng interpreter đó thay `python` dưới đây:

```text
python -m pip install -r requirements_review.txt
python tooling/replay_review_checks.py --output ../scst-review-run-001
```

Output phải là thư mục mới, nằm ngoài package. Wrapper không ghi đè evidence cũ, không sửa ZIP/schema/fixtures v0.2 và không tạo app. Nếu dependency không thể cài trong môi trường, ghi blocker cụ thể; không bỏ kiểm rồi ghi PASS. Python 3.12 là môi trường đã được quan sát; tool checksum chỉ cần stdlib.

Wrapper pin SHA của ZIP v0.2. Nó kiểm đường dẫn archive, giải nén vào output rồi chạy lần lượt checksum, suite và probes. Lỗi ở bước nào phải đọc log bước đó; không diễn giải lỗi dependency thành lỗi nghiệp vụ.

## 5. Giới hạn và trạng thái nghiệm thu

TP ứng dụng, MVP-NV, field approval, CVF runtime, source authenticity và actor authentication thực vẫn NOT_EVALUATED/NOT_GRANTED tương ứng. Lần này không tạo schema operational v0.3 hoặc migration. Những yêu cầu mới được viết ở mức SPECIFIED_FOR_REVIEW, để local xác minh trước freeze.

Checksum phát hành cuối nằm ở `FILE_CHECKSUMS.sha256`, ngoại trừ chính file checksum. Nó chứng minh bytes so với danh sách đóng gói, không là chữ ký tác giả hoặc bằng chứng dữ liệu đúng thực tế. Bản cuối bổ sung evidence/tài liệu đóng gói sau replay; mã kiểm/probe và ZIP v0.2 được đối chiếu hash để bảo đảm vẫn đúng snapshot đã chạy.
