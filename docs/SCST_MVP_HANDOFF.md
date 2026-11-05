# SCST — Bàn giao MVP để dùng thử

Ngày bàn giao: 05-11-2026 · Bản: `main` sau M5a · Dành cho: owner và người dùng thử.

Đây là bản **MVP để dùng thử và góp ý**, chưa phải công cụ lập phương án chính thức. Kết quả dựa trên hầm **ước tính** và chưa kiểm các yếu tố an toàn ở mục 4. Không dùng kết quả để lập hoặc phê duyệt phương án xếp hàng thực.

## 1. Khởi động

1. Mở thư mục `Cargo_Stowage_Tool`, nhấp đôi **`Start-SCST.cmd`**. Lần đầu cần mạng để cài thư viện và build; các lần sau chạy offline.
2. Trình duyệt tự mở `http://127.0.0.1:8765`. Giữ cửa sổ launcher mở trong lúc dùng; **Ctrl+C** để dừng.
3. Lần đầu mở trên bản này, app tự sao lưu một lần cơ sở dữ liệu cũ thành `runtime-data/scst.sqlite3.pre-sup02a.bak` rồi nâng cấp. Không xóa tệp này.

Nếu cổng 8765 bận, xem mục khởi chạy trong [README](../README.md).

## 2. Thử luồng chính (khoảng 10 phút)

1. Bấm **Xem VINAFCO 268**. Giới hạn chuyến tự theo cấp VR-SII (3.517,5 tấn); thông báo cho biết có thể chỉnh trong **Giới hạn chuyến (kg)**.
2. **Xem trước list ống** → **Nạp list vào phương án hiện tại**: 31 nhóm, 1.076 bó.
3. Ở **Xếp thử tự động**, ô **Cách xếp thử** đã chọn sẵn **Nhiều tầng theo cột (thử nghiệm)** → bấm **Xếp thử tự động**.
   - Xem trước: đặt được **1.076/1.076 bó**, khoảng 98 cột, cao tối đa 18 tầng, kiểm hình học không lỗi.
   - Có thể chọn **Một tầng (như cũ)** để so sánh: chỉ đặt được 167 bó vì hết diện tích sàn.
4. **Áp dụng xếp thử**. Xem trên 3D, mặt bằng 2D (nhãn "×N" là số tầng của cột) và bảng hàng (cột **Tầng**). Chọn một bó để thấy tầng, cao độ Z và bó đỡ.
5. Đặt tên → **Lưu phương án**. Tải lại trang → mở lại từ **Phương án đã lưu**.
6. **Xuất báo cáo** để xem trang in và tải tệp XLSX. Báo cáo ghi rõ đây là phương án nhiều tầng chưa kiểm tải chồng, tải sàn, chằng buộc và ổn định.

## 3. Sao lưu dữ liệu — làm trước khi nhập dữ liệu thật

Ở mục **Sao lưu và khôi phục**:

- **Tải bản sao lưu**: tải một tệp `.scstbak` chứa mọi phương án đã lưu, revision dữ liệu hàng và hồ sơ tàu đã nhập. Cất tệp ở nơi khác máy (USB, ổ mạng).
- **Khôi phục từ bản sao lưu**: chọn tệp → app kiểm toàn bộ tệp và cho xem số liệu trước → bấm **Khôi phục**. Khôi phục **thay toàn bộ** dữ liệu hiện có. Trước khi thay, app tự tạo một bản sao lưu dữ liệu hiện tại trong `runtime-data/backups/`. Nếu có lỗi giữa chừng, dữ liệu cũ được giữ nguyên.
- **Sao lưu tự động:** khi bạn mở app, nếu đã có dữ liệu và bản tự động gần nhất cũ hơn 20 giờ thì app tự tạo một bản trong `runtime-data/backups/auto/` (giữ tối đa 10 bản). Có nút **Sao lưu ngay** và nút **Tải** cho từng bản.
- Bản tự động **nằm cùng máy** với dữ liệu, nên không cứu được khi hỏng ổ hay mất máy. Hãy tải một bản và cất ra ngoài máy sau mỗi buổi làm việc quan trọng. Chưa có sao lưu theo lịch khi app đóng, chưa mã hóa.

## 4. Giới hạn cần biết

| Nội dung | Tình trạng |
|---|---|
| Hầm VINAFCO 268 (56,4 × 10,34 × 5,41 m) | **Ước tính** từ hồ sơ, chưa đo thực tế |
| Xếp nhiều tầng | Chỉ chồng các bó **cùng kích thước** thành cột thẳng đứng; kiểm đỡ ≥ 90% diện tích đáy và tâm đáy nằm trên bó đỡ |
| Tải chồng cho phép trên bó, tải sàn hầm | **Chưa kiểm**: chưa có dữ liệu |
| Kê, chèn, chằng buộc; ổn định và sức bền tàu | **Chưa kiểm** |
| Khe giữa các tầng | Dưới 1 mm do làm tròn lưới, chưa phải khoảng kê gỗ |
| Khối lượng list ống | Tính từ kg/ống × số ống, chưa cân; lệch 31,03 kg so với tổng nguồn |
| 16 bó (dòng 22, 31, 32) | Khối bao cần xác minh |
| Bộ xếp thử | Heuristic tất định, không phải tối ưu |

Kết quả 1.076/1.076 bó chỉ có nghĩa: **các khối bao vừa hầm ước tính về hình học**. Đây chưa phải phương án xếp an toàn.

## 5. Góp ý cần từ owner

Sau khi dùng thử, ghi lại (một dòng mỗi ý là đủ):

1. Luồng thao tác nào khó hiểu hoặc thiếu bước?
2. Cách chồng cột có giống thực tế xếp ống ở cảng không? Bó nào không được chồng lên nhau?
3. Báo cáo XLSX/trang in còn thiếu cột hoặc thông tin gì để dùng trong công việc?
4. Cần thêm tính năng gì trước khi dùng cho một chuyến thật?

Để làm bước tiếp theo **M3b** (case thực), team cần owner cung cấp:

- số đo hầm thực tế;
- một vài chuyến đã xếp thực tế để đối chiếu;
- tải chồng cho phép trên bó và tải sàn hầm, nếu có;
- xác minh kích thước 16 bó còn cảnh báo.

## 6. Tình trạng kỹ thuật

- Đã kiểm trên Windows: 878 test backend, 57 kịch bản trình duyệt, kiểm tích hợp 29/29.
- Mỗi tranche có review độc lập:
  - [M3a xếp nhiều tầng](reviews/SCST_M3A_REVIEW.md);
  - [M5a sao lưu và khôi phục](reviews/SCST_M5A_REVIEW.md);
  - [M2d báo cáo](reviews/SCST_M2D_REVIEW.md);
  - [HARDEN-01](reviews/SCST_HARDEN_01_REVIEW.md).
- Ngày 05-11 đã chạy thử `tooling/start-local.ps1` trên một **bản chép** dữ liệu của owner: app khởi động, nâng cấp cơ sở dữ liệu cũ, xếp nhiều tầng và sao lưu đều chạy. Dữ liệu gốc không bị chạm.
- Chưa làm, là các tranche tùy chọn về sau:
  - bộ cài đặt (M5c);
  - sao lưu theo lịch khi app đóng;
  - xếp lẫn kích thước trong một cột;
  - AI hỗ trợ (M4).
