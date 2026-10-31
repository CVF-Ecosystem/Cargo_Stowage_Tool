# 10 — MVP UI/UX Workflows v0.1

**Status:** `DRAFT`. Không có mockup tương tác đã lập trình; đây là luồng UI bắt buộc để FE và BE không tách rời nghiệp vụ.

## Screen map

1. **Data Library** — Tàu/sà lan, manifest, loading cases, plan versions; tìm số đăng ký, ngày và trạng thái; đọc-only plan cũ.
2. **Vessel Intake Wizard** — upload chứng từ, danh sách trường extracted nằm cạnh ảnh/PDF source, đánh dấu mâu thuẫn/hết hạn, bắt buộc người dùng xác nhận; không tự điền tải trọng nếu mơ hồ.
3. **Manifest Intake Wizard** — upload Excel/CSV, phân tích từng sheet, preview rows/units, tổng trọng lượng và chênh lệch manifest; xem lỗi theo dòng, sửa và xác nhận.
4. **Hold Editor** — nhập length/width/height hữu dụng, box hoặc trapezoid, clearance, chướng ngại cơ bản, nhãn “ước tính”.
5. **Loading Case** — chọn versions của Vessel/Hold/Manifest, xác nhận giới hạn hàng cho chuyến và hàng đã có; xem báo cáo readiness trước khi nút Optimize được bật.
6. **Plan Workspace** — trái: danh sách cargo/filters; giữa: 3D rotate/zoom/top/front/section/hide layers; phải: rules coverage và unplaced reasons; dưới: plan versions, solver run status.
7. **Review & Export** — so sánh phương án, chấp nhận đề xuất của user với hash, báo kỹ thuật chưa kiểm, xuất report; tuyệt đối không in nhãn “approved safe”.
8. **Settings & Backup** — backup, verify restore, local AI enable/disable, rule set versions, quyền truy cập.

## UX state principles

- Mỗi nút “Optimize” phải hiển thị số lượng cargo units/tổng kg và **preflight check**; không chạy nếu required fields chưa xác nhận.
- `BLOCKED` kèm nguyên nhân cụ thể và đường dẫn trực tiếp đến trường bị lỗi, không chỉ mã lỗi.
- `NEEDS_REVIEW`/`NOT_EVALUATED` luôn hiển thị khi xem 3D và xuất báo cáo; không che bằng màu xanh chung.
- Khi người dùng kéo một cargo unit, frontend preview ngay nhưng backend là nơi duy nhất tính hợp lệ và commit; optimistic UI phải rollback nếu Backend reject.
- Hàng 3D được chọn phải liên kết đúng `cargoUnitId` trong manifest, không mất nhận diện khi đổi góc nhìn hoặc reload.
- Không thiết kế thao tác AI tự động “apply now” trên phương án chất xếp; chỉ `Propose`, `Explain`, `Request revision`.
- Keyboard accessible cho bảng dữ liệu và các lệnh chính; dùng được không có GPU mạnh bằng chế độ 2D/text fallback; lỗi WebGL không làm mất manifest/plan.
- Các giá trị đo phải hiển thị rõ mm/m/tấn/kg, đồng thời nội bộ chỉ dùng mm/kg; locale/decimal separators được xác minh trước convert.

## User journeys tối thiểu

**Journey A:** giấy chứng nhận có hai tên khác nhau → AI báo xung đột → user xác minh chứng từ hiện hành → tạo VesselProfileVersion mới → lưu bản gốc và lý do.

**Journey B:** manifest 1.003 tấn, cargo limit xác minh 995 tấn → tối ưu được tập phù hợp giới hạn hoặc báo dư lượng; không bao giờ chọn tất cả 1.003 tấn; user nhìn thấy danh sách chưa xếp và không cần điều phối xe.

**Journey C:** user kéo bó ra ngoài biên hầm → UI preview màu cảnh báo → Backend từ chối lưu `RULES_CHECKED` → hiện rule fail; plan cũ vẫn tồn tại.

**Journey D:** tắt AI → vẫn nhập thủ công, kiểm tra khối lượng, xem 3D và export report; quyền human approval không bị giảm.
