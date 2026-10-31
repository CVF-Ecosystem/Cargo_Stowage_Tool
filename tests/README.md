# Kiểm thử

**Trách nhiệm:** Ca kiểm nghiệp vụ (tải, biên, va chạm, sửa phương án), tích hợp và luồng dùng theo từng mốc.

**Dùng từ mốc:** M1+.

**Dữ liệu kiểm thử:**

- **Fixture giả lập** (M1+): dữ liệu tự tạo, ghi nhãn synthetic/demo; được commit vào Git.
- **Case thực** (từ M3): chỉ dùng bộ case owner đã cho phép, ưu tiên bản ẩn danh; ghi nguồn và phạm vi được phép. Chỉ commit bản đã ẩn danh khi owner đồng ý.
- **Chứng từ gốc nhạy cảm** (manifest, giấy tờ tàu, tệp khách hàng): lưu ngoài Git, ví dụ trong `runtime-data/` (không commit) hoặc nơi lưu do owner chỉ định; test chỉ tham chiếu, không sao chép vào repository.

**Không thuộc thư mục này:** Không trình bày kết quả trên fixture giả lập như kết quả đã kiểm với hầm/chuyến thật.

Đã có kiểm M1 backend, browser, launcher/cold-start và guard offline chỉ dùng khi test. Xem docs/APP_GUIDE.md và docs/reviews/SCST_M1_REVIEW.md để chạy/đọc bằng chứng; chưa có dữ liệu thực.
