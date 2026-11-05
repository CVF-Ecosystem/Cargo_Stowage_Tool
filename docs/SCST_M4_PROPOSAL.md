# SCST — M4: đề xuất AI hỗ trợ (để owner chọn)

Ngày: 05-11-2026 · Trạng thái: **ĐỀ XUẤT, chưa triển khai** · Người quyết: owner.

Theo [roadmap tổng thể](roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md), M4 là nhánh **tùy chọn**. Chỉ làm khi owner xác nhận một tác vụ cụ thể cần AI. Trang này giúp owner chọn hoặc bỏ. Hiện app **không có AI** và vẫn dùng đầy đủ không cần AI.

## 1. Nguyên tắc nếu làm

1. **AI chỉ đề xuất, không tự ghi.** Mọi thay đổi vào phương án hay dữ liệu hàng phải qua bước xem trước và người dùng bấm xác nhận.
2. **Backend vẫn là người kiểm.** Mọi đề xuất của AI đi qua đúng các kiểm hiện có (hình học, đỡ, khối lượng, revision). AI không được vượt các kiểm này.
3. **Tắt được hoàn toàn.** Khi AI tắt, mất kết nối hoặc không có key, mọi chức năng hiện có chạy y như bây giờ.
4. **Không gửi dữ liệu ra ngoài khi chưa được phép.** Dữ liệu hàng, hầm và phương án là dữ liệu kinh doanh. Chỉ gửi ra dịch vụ ngoài khi owner đã bật, thấy rõ gửi gì, và có thể xem lại.
5. **Gắn nhãn rõ.** Nội dung do AI tạo luôn có nhãn "AI đề xuất, chưa xác minh". Kết quả AI không được dùng làm bằng chứng kiểm của app.

## 2. Bốn tác vụ ứng viên

Xếp theo mức ích lợi so với rủi ro, theo hiểu biết hiện tại về luồng làm việc.

| # | Tác vụ | Hiện tại thiếu gì | AI giúp gì | Rủi ro |
|---|---|---|---|---|
| A | **Đọc list hàng từ Excel hoặc PDF** | Chỉ nhận CSV tối đa 200 bó; list Baltimore phải nạp qua bộ chuyển riêng | Trích bảng hàng từ tệp Excel/PDF của chủ hàng, đưa về dạng CSV chuẩn để owner xem trước và sửa | Trích sai số liệu; vì vậy luôn có bước xem trước từng dòng, và đối chiếu tổng khối lượng với tổng ghi trong tệp |
| B | **Giải thích vì sao bó không xếp được** | Chỉ có mã lý do cố định, ví dụ "Chưa tìm được chỗ", "Hết chiều cao cột" | Giải thích bằng lời, nêu bó nào, thiếu bao nhiêu diện tích hay chiều cao | Thấp: chỉ diễn giải số liệu app đã có |
| C | **Đề xuất chỉnh sau khi báo lỗi** | Khi một bó mất đỡ hay quá tải, người dùng phải tự tìm cách sửa | Gợi ý dời hoặc đổi bó nào; app kiểm lại gợi ý bằng các quy tắc hiện có trước khi cho áp dụng | Trung bình: gợi ý có thể không tối ưu; vì vậy chỉ hiện gợi ý đã qua kiểm |
| D | **Tóm tắt phương án cho báo cáo** | Báo cáo chỉ có bảng số | Viết đoạn tóm tắt: số bó, tải, điểm cần lưu ý, phần chưa kiểm | Thấp, nhưng phải ghi rõ là bản nháp để người ký duyệt |

**Gợi ý của team dev:** nếu chọn một việc thì chọn **A**, vì nó bỏ được thao tác tay lớn nhất, là nhập list hàng. **B** là bước khởi đầu rẻ nhất và an toàn nhất. C chỉ nên làm sau khi có dữ liệu hầm thật (M3b), vì khi hầm còn là ước tính thì gợi ý chỉnh chưa đáng tin.

## 3. Cần owner quyết trước khi làm

1. **Có cần AI không?** Làm tay hiện nay có đủ nhanh không? Nếu không có tác vụ nào đáng làm thì bỏ M4.
2. **Chọn tác vụ** trong A–D (hoặc nêu tác vụ khác).
3. **Dữ liệu có được gửi ra ngoài máy không?**
   - **Mô hình chạy trên máy:** không gửi gì ra ngoài, nhưng cần máy đủ mạnh và chất lượng thường thấp hơn.
   - **Dịch vụ AI trên mạng:** chất lượng tốt hơn, nhưng dữ liệu hàng rời khỏi máy. Cần owner đồng ý rõ, và cần chính sách của công ty.
4. **Nhà cung cấp và key.** Owner chọn nhà cung cấp, tự giữ key. Team dev không nhận key và không đưa key vào mã nguồn hay Git.
5. **Chi phí:** ai trả, hạn mức mỗi tháng.
6. **License CVF.** CVF dùng giấy phép CC BY-NC-ND 4.0, hạn chế việc tích hợp hay phân phối. Roadmap yêu cầu xử lý điều này trước khi đưa CVF vào app. Có thể phương án M4 không cần tích hợp CVF vào app, mà chỉ dùng AI qua backend riêng của SCST.
7. **Mẫu dữ liệu thật** cho tác vụ A: vài tệp Excel/PDF list hàng thật mà owner thường nhận, đã bỏ thông tin nhạy cảm nếu cần.

## 4. Nếu owner chọn làm

Cách làm đề xuất, mỗi bước là một tranche nhỏ có review độc lập như các tranche trước:

1. **M4-0 (khung AI an toàn, chưa có tác vụ):**
   - công tắc bật/tắt, mặc định **tắt**;
   - màn hình cho thấy chính xác dữ liệu nào sẽ gửi đi;
   - nhật ký các lần gọi AI, chỉ lưu local;
   - kiểm chứng app chạy y như cũ khi tắt hoặc mất mạng.
2. **M4-1:** tác vụ đầu tiên owner chọn, kèm xem trước và xác nhận.
3. Các tác vụ sau chỉ làm khi M4-1 thực sự có ích.

Mỗi bước phải chạy thử với một lời gọi AI thật, trong phạm vi được bật, trước khi nhận là xong. Việc này cần key và cách gọi mạng do owner cấp. Cloud worker hiện không có quyền đó, nên các bước gọi AI thật sẽ chạy ở máy local với key của owner.

## 5. Chưa làm gì cả

Trang này không đổi mã, không thêm phụ thuộc, không gọi AI. Hiện chưa có tranche M4 nào được mở.
