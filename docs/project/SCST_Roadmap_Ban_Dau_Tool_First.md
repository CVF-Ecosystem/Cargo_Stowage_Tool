# SCST — Roadmap ban đầu: tạo tool, hoàn thiện dần

**Ngày:** 31-10-2026.  
**Tài liệu gốc:** Steel Cargo Stowage Tool — Design Baseline v0.1 của agent web.  
**Mục đích:** hướng dẫn thứ tự làm và giữ đúng phạm vi; cập nhật dần khi có dữ liệu và kết quả chạy.

## 1. Chỉ đạo triển khai được điều chỉnh

Theo yêu cầu mới của owner: **dựng khung và làm tool trước; bổ sung thông tin ở bước cần dùng; mở rộng thành app sau khi tool có giá trị.** Roadmap và cấu trúc dự kiến được lập ngay. Không chờ hoàn tất mọi phản biện hoặc hồ sơ nghiệp vụ mới bắt đầu.

Bản v0.1 đã có roadmap tại `docs/06_ROADMAP_GATED.md` và kiến trúc tại `docs/07_ARCHITECTURE_TREEVIEW.md`. Giữ hướng đó; đưa khung chạy thử lên đầu, chia việc thành phần nhỏ. Các điều kiện “chưa được dựng roadmap/treeview” trong bàn giao R4 đã được chỉ đạo mới này thay thế.

V0.2, v0.3 và R4 là tài liệu tra cứu để sửa đúng vấn đề khi đến phần liên quan. Không yêu cầu local thực hiện toàn bộ đề nghị trong các bản review trước khi dựng khung. Những yêu cầu kiểm dữ liệu thật và sử dụng phương án thực vẫn áp dụng ở đúng chức năng cần chúng.

## 2. Mục đích tool giữ nguyên từ bản đầu

**Nhập danh sách hàng + thông tin phương tiện/hầm → lập phương án sơ bộ → thấy hàng đã xếp/chưa xếp và tổng khối lượng → xem 3D → chỉnh, lưu, so sánh và xuất kết quả.**

- Local-first, một người dùng chính, core hoạt động khi tắt AI.
- Một project, frontend/backend tách module và API.
- Bắt đầu với bó thép thanh và bó thép ống có kích thước bao rõ; giữ từng bó nguyên vẹn. Những ống rời/cuộn hoặc cấu hình khác bổ sung theo nhu cầu thật.
- Hầm BOX đơn giản làm điểm khởi đầu. Mô hình hình thang hoặc chi tiết hơn được bổ sung khi case cho thấy cần.
- UI/tooltip tiếng Việt; tổng quan rồi xem chi tiết; ngày dd-mm-yyyy; kết quả có PDF và Excel.
- Giữ phạm vi lập phương án chất xếp. Điều phối cảng, xe/cẩu, ERP/WMS và mô phỏng cơ học tổng quát nằm ngoài mục tiêu này.

## 3. Roadmap làm việc ban đầu

Đây là các mốc đầu ra, không phải cam kết thời lượng. Mỗi mốc có thể chia thành nhiều phần việc nhỏ; chỉ chuẩn bị chi tiết đủ cho phần việc đang làm.

| Mốc | Làm gì | Kết quả nhìn thấy được | Thông tin bổ sung khi cần |
|---|---|---|---|
| **M1 — Khung chạy được** | Tạo FE/BE theo cấu trúc v0.1 rút gọn; API tối thiểu; một bộ hàng và hầm mẫu có nhãn demo; backend trả dữ liệu cho màn hình 3D/bảng | Khởi chạy local, nhìn thấy cùng unit ID và số liệu từ API trên giao diện; kiểm đơn giản một trường hợp vượt tải hoặc vượt biên | Dùng fixture thử nghiệm đang có hoặc fixture nhỏ ghi rõ synthetic; chưa cần hồ sơ chuyến thật |
| **M2 — Tool cơ bản** | Nhập tay trước, thêm import theo mẫu; dữ liệu hầm/manifest; kiểm khối lượng và hình học; heuristic xếp sơ bộ; danh sách chưa xếp; chỉnh và kiểm lại; lưu/mở/so sánh; xuất PDF/XLSX | Người dùng đi được toàn luồng nhập → gợi ý → xem → chỉnh → lưu → xuất, trong phạm vi mô hình đã hỗ trợ | Mẫu file khi làm importer; trường input nào cần cho phép kiểm thì bổ sung đúng trường đó |
| **M3 — Hoàn thiện tool cho hàng thực tế** | Đưa case thực vào thử; bổ sung nhiều tầng, nhóm kích thước khác nhau, profile kê/chồng và geometry cần thiết; sửa UX từ thao tác thật | Tool giải được công việc đại diện trong phạm vi đã xác nhận; nhận diện rõ phần chưa hỗ trợ | Manifest, kích thước hầm, cách xếp/kê và người có thể đối chiếu. Thu dần theo cấu hình đang làm |
| **M4 — AI hỗ trợ, nếu cần** | Hỏi bổ sung, hỗ trợ trích xuất/giải thích và đề xuất chỉnh; nối các Agent actions qua CVF và quyền backend | AI giúp bớt thao tác; người dùng quyết định; tool vẫn chạy khi AI tắt | Xác định tác vụ AI cụ thể rồi mới tích hợp/kiểm đúng tác vụ đó |
| **M5 — Nâng thành app hoàn chỉnh** | Hoàn thiện bộ cài, độ bền lưu trữ, backup/restore, lịch sử/quyền/quy trình review theo nhu cầu; tối ưu hiệu năng | Dễ cài, dễ dùng và duy trì; mở rộng từ tool đã được dùng thử | Nhiều người, cloud hoặc tích hợp hệ thống khác chỉ mở khi có nhu cầu được xác nhận |

**M3 vẫn thuộc quá trình hoàn thiện tool.** Một demo BOX một lớp ở M1 chưa đại diện cho nhu cầu chất xếp nhiều tầng; roadmap giữ đích đó và thực hiện từng phần.

Lưu/mở và giữ bản trước khi sửa có từ M2; M5 hoàn thiện cơ chế vận hành, không phải đến M5 mới bảo vệ dữ liệu. Với solver, làm cách xếp đơn giản có kiểm tra trước, cải thiện chất lượng sau; không yêu cầu chứng minh tối ưu toàn cục để có tool đầu tiên.

## 4. Khung thư mục tối thiểu bám v0.1

Chỉ tạo các phần đang dùng; không dựng sẵn toàn bộ module tương lai.

| Đường dẫn dự kiến | Nhiệm vụ |
|---|---|
| `apps/frontend/` | Màn hình nhập liệu, bảng hàng, workspace phương án, viewer 3D và hiển thị kết quả |
| `services/backend/app/api/` | API nhận dữ liệu và trả kết quả |
| `services/backend/app/domain/` | Dữ liệu nghiệp vụ, kiểm quy tắc, geometry và thuật toán xếp; tách file theo nhu cầu thực |
| `services/backend/app/adapters/` | Lưu dữ liệu local, import/export; thêm AI/CVF adapter khi đến phần tích hợp |
| `contracts/` | Cấu trúc dữ liệu/API đang thực sự dùng, đơn vị tính và version |
| `tests/` | Các ca nhỏ kiểm chức năng đang xây, nhất là tải, biên, va chạm và sửa phương án |
| `docs/` | Roadmap này, hướng dẫn chạy, các quyết định và việc còn thiếu |
| `tooling/` | Lệnh khởi chạy và công cụ hỗ trợ local |
| `runtime-data/` | Dữ liệu người dùng trên máy, không commit vào Git |

Giữ gợi ý stack của bản đầu: React/TypeScript cho FE, Python/FastAPI cho BE, SQLite khi cần lưu bền và Three.js/R3F cho viewer. Local xác minh phiên bản tương thích khi thiết lập. Một tool chạy local; chưa cần tách thành nhiều dịch vụ độc lập.

## 5. Chỉ giữ những nguyên tắc cần ngay

1. Đơn vị hàng có ID, dimensions và mass rõ; không tự chia tổng manifest để bịa mass từng bó. Chuẩn hóa đơn vị nhất quán, không làm tròn xuống để lọt giới hạn. Lỗi precision đã phát hiện được sửa khi hiện thực lớp dữ liệu.
2. Kiểm giới hạn hàng hóa đúng nghĩa, không dùng nhầm gross/deadweight; phân biệt hàng required, optional và excluded. Đủ required là mục tiêu riêng, không bỏ hàng required để tăng điểm.
3. Backend kiểm tải, biên và va chạm của phạm vi đang hỗ trợ. Sửa bố trí phải kiểm lại và giữ bản trước; viewer đọc cùng tọa độ/unit ID với backend.
4. Dữ liệu giả lập giữ nhãn demo; thiếu dữ liệu thật thì lưu draft hoặc nêu phần chưa kiểm. Một cấu hình chưa hỗ trợ không làm mất dòng hàng khỏi danh sách.
5. Giao diện nêu kết quả tính sơ bộ và phần chưa kiểm; người dùng quyết định. AI không tự xác nhận thông số hoặc phê duyệt phương án.

Các cơ chế provenance, receipt, review lifecycle và quản trị chi tiết trong R4 được lấy ra khi chức năng liên quan cần. Ghi nguồn đầu vào và lịch sử thay đổi đơn giản từ đầu là đủ để bắt đầu phát triển; bổ sung mức kiểm soát tương ứng trước khi dùng dữ liệu/phương án thật ở phạm vi đó.

## 6. Xử lý thiếu thông tin mà vẫn tiến lên

Mỗi mục thiếu chỉ cần ghi **thiếu gì — ảnh hưởng phần nào — khi nào cần bổ sung**. Không biến danh sách này thành điều kiện dừng cả project.

| Chưa có | Cách tiến hành |
|---|---|
| Manifest thật hoặc format import | Dựng bảng nhập tay/fixture; lấy mẫu khi viết importer và thử case thật |
| Số đo hầm thật | Dựng Hold Editor và renderer bằng hầm demo; bổ sung trước khi tính phương án cho hầm đó |
| Profile kê/chồng cho một cấu hình | Làm phần geometry/luồng dữ liệu độc lập; cấu hình nhiều tầng đó chờ profile phù hợp |
| Quy trình review hiện trường đầy đủ | Dựng luồng planning và export sơ bộ; hoàn thiện review khi đưa vào dùng thực tế |
| AI/provider hoặc adapter CVF trong app | Làm core AI-off; bổ sung ở M4. CVF quản lý agent phát triển trong workspace vẫn dùng từ đầu |

## 7. Đối chiếu CVF mới: điểm tác động trực tiếp

Đã đọc `README.md`, `START_HERE.md` và `LICENSE` tại HEAD của `main` được quan sát ngày 31-10-2026: **`8cbdd21ca0b01d7ef9e9423ce687af86ada8666d`**.

README hướng dẫn đặt project cạnh public CVF core trong workspace. Vì vậy local có public checkout không tự là sai nguồn bố trí. Tài liệu cũng cho phép từng phần việc kế thừa nội dung đã chấp nhận. Đề nghị áp dụng cho SCST: giao việc nhỏ theo roadmap, dùng governance workspace hiện có; kiểm adapter khi bật AI trong tool.

Nguồn đọc: [README tại commit đã kiểm](https://github.com/Blackbird081/Controlled-Vibe-Framework-CVF-Provenance/blob/8cbdd21ca0b01d7ef9e9423ce687af86ada8666d/README.md), [START_HERE](https://github.com/Blackbird081/Controlled-Vibe-Framework-CVF-Provenance/blob/8cbdd21ca0b01d7ef9e9423ce687af86ada8666d/START_HERE.md), [LICENSE](https://github.com/Blackbird081/Controlled-Vibe-Framework-CVF-Provenance/blob/8cbdd21ca0b01d7ef9e9423ce687af86ada8666d/LICENSE).

Đã xác minh đọc được nguồn hiện tại; chưa chạy CVF hoặc chứng minh adapter SCST. Giữ CVF core riêng, không sửa để phù hợp app. License tại revision này ghi CC BY-NC-ND 4.0; điều kiện tích hợp/phân phối xử lý khi có phương án sử dụng cụ thể, không chặn việc viết roadmap và khung độc lập.

## 8. Phần việc đầu tiên giao local agent

**Thực hiện M1 trong phạm vi project SCST theo quy trình workspace hiện có:**

- Bám mục tiêu và module của bản v0.1 cùng roadmap này; chỉ dùng các review sau để sửa lỗi liên quan đến phần đang làm.
- Khảo sát project hiện có, dựng FE/BE tối thiểu, API và fixture demo.
- Nối một luồng nhỏ: backend trả hầm/hàng/plan mẫu → giao diện hiện bảng và 3D → đổi một dữ liệu → backend trả kết quả kiểm cơ bản.
- Trả bản chạy được, cách khởi động, hình màn hình và kết quả kiểm đúng phần đã làm; ghi ngắn những phần chưa có.
- Sau đó thực hiện lát cắt M2 kế tiếp. Chỉ hỏi thông tin thực sự cần cho phần việc đang tới; không mở lại toàn bộ review trước khi dựng khung.

Roadmap này là căn cứ khởi động và giữ hướng. Khi thử tool thấy cần thay đổi, cập nhật đúng mốc/module liên quan và tiếp tục.
