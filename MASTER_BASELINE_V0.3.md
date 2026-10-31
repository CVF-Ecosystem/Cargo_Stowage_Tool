# Baseline yêu cầu v0.3 cho vòng review local

**SCST-REVIEW-0.3 — SPECIFIED_FOR_REVIEW — 31-10-2026**

## 1. Mục tiêu không thay đổi

Xây một công cụ hỗ trợ người lập phương án chất xếp hàng thép trong hầm tàu/sà lan: từ dữ liệu nguồn có thể truy vết, tạo/so sánh/chỉnh phương án, kiểm các ràng buộc có đủ dữ liệu, xem bố trí theo lớp/nhóm và xuất báo cáo để đối chiếu. Công cụ phải có ích với các case nghiệp vụ đại diện được xác định trước nghiệm thu.

Tool-first: core nhập dữ liệu, kiểm tra, tạo phương án, lưu và xuất phải hoạt động khi AI tắt. Frontend/backend có module và API tách biệt trong một repo local; giữ React/TypeScript/viewer và Python/backend như đề xuất v0.2, để local kiểm phiên bản/dependency. Không mở thành phần mềm điều hành cảng, điều phối ca, xe, bến hoặc cẩu.

CVF kiểm soát các hành động Agent thuộc phạm vi được bật; backend vẫn xác thực và kiểm nghiệp vụ. CVF ALLOW không biến dữ liệu thiếu hoặc phương án vi phạm thành hợp lệ. Không sửa CVF core để làm cho một kiểm tra đi qua.

## 2. Hai mốc nghiệm thu phải tách riêng

### Technical Proof

Chứng minh các thành phần kỹ thuật làm đúng trong mô hình đã công bố: import/draft, hash/ref, validator, solver nhỏ có oracle, UI/API và quan hệ các trạng thái. BOX và một lớp là fixture phù hợp để bắt đầu kiểm từng phần. Bộ 86 tests v0.2 chỉ là bằng chứng contract tham chiếu; chưa tự hoàn thành Technical Proof của ứng dụng vì chưa có runtime ứng dụng.

### MVP nghiệp vụ

Phải hoàn thành quy trình lập phương án trên case thực tế trong phạm vi đã chấp nhận: nhiều tầng, nhiều nhóm hàng/kích thước, profile kê đỡ phù hợp, vùng hầm đại diện đủ dùng, nguồn dữ liệu có thể truy vết, điều chỉnh có kiểm lại, viewer hỗ trợ kiểm tra và báo cáo đối soát. Chưa có profile hoặc chưa có case phù hợp thì mốc này còn chờ; không đổi tên một demo BOX một tầng thành MVP đạt nghiệp vụ.

Chi tiết và trạng thái nằm trong docs/01. Việc đạt MVP sản phẩm không tự cấp phép dùng mọi phương án ngoài hiện trường; từng phương án/chuyến vẫn có điều kiện và review riêng.

## 3. Phạm vi đề nghị cho MVP và điều kiện xác nhận

| Nội dung | V0.3 yêu cầu/đề nghị | Điểm cần đối chiếu local |
|---|---|---|
| Môi trường | PC local, một người thao tác chính | Máy/OS, quyền cài đặt, quy mô manifest; không mặc định đã có auth |
| Bài toán ban đầu | Đề nghị lập phương án mới cho một hầm mục tiêu bắt đầu trống | Owner xác nhận đây có phải công việc thường gặp; ảnh sau xếp không chứng minh nhu cầu bổ sung vào hầm đang có hàng |
| Hầm | Vùng xếp đại diện cho hầm thật, có căn cứ và giới hạn xấp xỉ | BOX chỉ được giữ cho MVP nếu vùng khả dụng bảo thủ và giá trị sử dụng được chứng minh; nếu không, cần contract mặt cắt/miền hình học thích hợp trước freeze |
| Hàng | Hai nhóm bó thép thanh/bó thép ống vẫn là điểm xuất phát; phải đối chiếu đúng đơn vị trong manifest | Từng ống, bó, loại tiết diện khác hoặc cuộn không được gán nhãn giả để vừa enum cũ; quyết định phạm vi theo mẫu thật |
| Nhiều tầng | Năng lực bắt buộc ở MVP nghiệp vụ cho các profile đã duyệt | Ít nhất một case đại diện nhiều tầng; đủ profile cho mọi quan hệ đỡ được dùng |
| Phối hợp | Nhiều nhóm trong cùng hầm; compatibility giữa profile có chiều và có nguồn | Mixed support khác profile chỉ khi có chấp thuận cụ thể; nếu case đại diện cần quan hệ đó thì chưa có profile sẽ chặn mốc MVP |
| Hàng ngoài phạm vi | Nhận diện và đối soát với manifest; không âm thầm bỏ khỏi báo cáo | Cuộn/kiện chưa hỗ trợ phải được báo rõ; nếu bắt buộc đi cùng mà không có mô hình, không tuyên bố đáp ứng toàn chuyến |
| Thiết bị thao tác | Ghi nhận điều kiện cần review nếu xuất hiện trong kịch bản mục tiêu | Không tính tải xích/contact/path từ ảnh; nếu thiết bị làm việc trên hàng là điều kiện của case, review đó cần có trước bàn giao case |

Các lựa chọn còn cần owner xác nhận được đánh dấu ở template CASE_INTAKE. Chúng không chặn agent đọc, chạy kiểm hoặc đề xuất sửa có căn cứ. Không yêu cầu owner tự quyết thuật toán, serializer hoặc cấu trúc repo.

## 4. Yêu cầu chức năng hiện hành

### 4.1 Intake và nguồn

Nhận ảnh/PDF, Excel/CSV và nhập tay. Giữ bản nguồn, raw value, đơn vị, vị trí trong nguồn và phép chuẩn hóa. OCR/AI chỉ tạo candidate. Giao diện cho sửa/xác nhận cạnh nguồn, giải thích rõ điều gì thiếu hoặc mâu thuẫn; không bắt người dùng nhập lại các tổng đã tính được.

Final snapshot phải nối được từng giá trị quan trọng đến draft/source span/confirmation receipt. Source registry, quyền xác nhận, transaction và coverage được local hiện thực/kiểm; schema-valid không có nghĩa confirmed operational. SYNTHETIC và dependency test đã biết không được vào record thật bằng cách đổi cờ/nhãn.

Khối lượng nghiệp vụ: đề nghị integer grams để giữ phần kg lẻ chính xác; chưa đổi contract kg của v0.2. Trước khi pin schema vận hành, local kiểm manifest và chốt độ chính xác, conversion, overflow và migration theo docs/03. Không làm tròn xuống, không tự chia mass tổng line đều cho các bó.

### 4.2 Dữ liệu hàng và hình học

Một đơn vị được solver đặt phải có ID, mass, bao hình học, hình thức đóng gói và profile đúng nguồn. Nhóm hiển thị, nhóm phải đi đủ và đơn vị xử lý vật lý là ba khái niệm riêng; gom nhiều unit để tăng tốc phải giữ truy ngược unit con và tổng mass.

Mô hình va chạm có thể dùng envelope bảo thủ. Mô hình tiếp xúc/kê đỡ cần dữ liệu riêng; không lấy diện tích đáy hình hộp làm diện tích truyền tải thực. Nếu envelope làm mất các phương án thực dùng thường xuyên, đó là vấn đề fidelity cần giải quyết, không được báo rằng hàng chắc chắn không xếp được ngoài thực tế.

Vùng hầm phải dùng cùng frame, chiều cao, clearance và excluded regions trong solver, validator, viewer và export. Xấp xỉ phải nằm trong vùng khả dụng đã xác minh trên toàn chiều cao liên quan. Không tự suy kích thước, margin hoặc dung sai từ ảnh. Các excluded regions hình học không thay kiểm tải của cargo đang có nếu sau này hỗ trợ occupied hold.

### 4.3 Kê đỡ và cấu hình nhiều tầng

Ưu tiên đánh giá cách tạo phương án trong các cấu hình/profile kê-chồng đã được chấp thuận. Profile mô tả phạm vi hàng/kích thước, quan hệ trên-dưới, hướng, support pattern, kê, giới hạn và nguồn. Chỉ thêm mô hình shape-aware hoặc template arrangement khi case thật chứng minh cần; không mặc định phải xây bộ mô phỏng cơ học tổng quát.

FULL_BASE_SUPPORT v0.2 giữ làm mô hình tham chiếu có giới hạn. Nó không chứng minh tiếp xúc của ống, chống lăn, chịu lực dây bó hoặc chia tải giữa các kê. Phép gán toàn bộ distinct descendant cargo mass cho từng supporter trong v0.2 là kiểm bảo thủ của contract cũ; không được thay thế tính tải chuyên môn khi các điều kiện của mô hình không đúng.

Đặt hàng vào vị trí nhìn vừa 3D chưa đủ để hoàn thành kiểm kê đỡ. Điều kiện thiếu phải hiện cụ thể và ảnh hưởng đúng tới validation/selection/handoff.

### 4.4 Tạo phương án và chỉnh sửa

Giữ hai mode ALL_REQUIRED và MAXIMIZE_OPTIONAL; required không được bị loại để tăng tấn optional. Mục tiêu optional vẫn là tổng khối lượng đã xếp trong contract đã chốt. Cần tự động tạo được đề xuất cho case thuộc phạm vi; chỉ nhập tọa độ thủ công rồi dựng hình chưa hoàn thành mục tiêu sản phẩm.

Giữ phân hoạch placed/unplaced/excluded và lý do cho mỗi unit chưa xếp. Đồ hình/recipe phải mở được thành các unit thật để đối soát. Kiểm sau solver độc lập với thuật toán sinh và AI. Chưa tìm thấy do heuristic, timeout hoặc mô hình bảo thủ không là proof vô nghiệm thực tế.

Sửa tay tạo version và validation mới, pin parent/case, không sửa origin run và không kế thừa proof. Candidate lỗi được lưu chẩn đoán; chọn sơ bộ chỉ khi các điều kiện core bắt buộc đủ. Không trộn lựa chọn của operator với review chuyên môn.

### 4.5 Viewer và báo cáo

Tiếng Việt; ngày dd-mm-yyyy; summary mở được chi tiết. 3D cần: ẩn/hiện lớp hoặc dải cao độ, lọc nhóm/lot/profile, chọn unit để đọc ID/mass/dimensions/source, xem support liên quan và lỗi, top/front/side hoặc mặt cắt, legend rõ. Nhóm hiển thị không làm mất unit chưa xếp hoặc hàng ngoài phạm vi. Hình học chi tiết mang tính minh họa phải được phân biệt với geometry kiểm.

Giữ 2D/text fallback khi 3D không dùng được. PDF và XLSX bắt buộc, CSV tùy chọn; xuất tổng và chi tiết khớp snapshot, version/hash, coverage, điều kiện và phần chưa đánh giá. UI/export không tự gắn SAFE/CERTIFIED/EXECUTION_READY.

### 4.6 Quyền, lưu trữ và khôi phục

Đề nghị mặc định một operator local đăng ký hồ sơ review chuyên môn bên ngoài; tách danh tính reviewer khỏi người nhập hồ sơ. Hồ sơ chỉ có ý nghĩa cho đúng plan/scope/điều kiện và phải được đối chiếu theo quy trình có người chịu trách nhiệm. Không tạo auth event giả cho reviewer ngoài app. Nhánh reviewer có tài khoản riêng chỉ dùng nếu mô hình vận hành thực chọn và kiểm nó.

Giữ immutable content, receipt/lifecycle riêng, SQLite/file store, migration, atomicity, backup/restore và kiểm hiệu lực hiện tại trước hành động mới. Không restore credential/session như dữ liệu nghiệp vụ. Việc owner hoặc operator sử dụng app không tự có nghĩa họ có thẩm quyền kỹ thuật xác nhận profile.

## 5. Nguyên tắc v0.2 được giữ

| V0.2 | Cách áp dụng ở v0.3 |
|---|---|
| GT/DWT/cargo limit riêng; budget cargo + kê mới | Giữ ý nghĩa và chống tính hai lần; chuyển toàn bộ đơn vị nhất quán nếu chọn grams |
| Version/hash, DAG và thuật toán canonical | Giữ STOWAGE-JSON-0.2 cho reference; contract mới phải version/hash và có vectors; không đổi ngầm field cũ |
| Ngày hoạt động/hiệu lực inclusive | Giữ; local xác minh loại chứng từ và phạm vi nguồn thật |
| Required/optional/excluded; run status đa trục | Giữ; proof chỉ có nghĩa trong model/input/objective được pin |
| HARD/HARD_GATE/GOVERNANCE fail/unknown chặn theo policy | Giữ; không dùng score, AI, CVF hoặc external review để override hard fail |
| G0/G1/G2/G3/G4a/G4b/G5 | Giữ như các nhóm bằng chứng; thêm mapping Technical Proof/MVP, không dùng gate đơn lẻ thay product acceptance |
| Core local, FE/BE, CVF adapter độc lập | Giữ; source CVF pinned vẫn phải kiểm ở local |
| V0.2 official work order cho phép skeleton | Được thay ở vòng này bằng REVIEW_ONLY theo START_HERE v0.3 |

Các doc/schema bên trong v0.2 không tự thay đổi trạng thái; những đề nghị mới trong v0.3 chưa có schema vận hành tương ứng. Local phải liệt kê delta cần reconcile trước implementation freeze; không copy schema cũ rồi chỉ đổi version string.

## 6. Giới hạn phạm vi hiện tại

Chưa mở: tối ưu nhiều hầm đồng thời, xếp thêm vào hầm đang có hàng, solver tổng quát cho cuộn/ống đơn/tiết diện mới, tính ổn định/sức bền/contact mechanics tổng quát, lập đường chạy thiết bị, lập trình tự thao tác được chứng nhận, cloud/multiuser hoặc quản lý cảng. Nếu case đại diện bắt buộc một mục chưa hỗ trợ thì ghi scope blocker và quyết định mở rộng; không loại dữ liệu khó khỏi case rồi tuyên bố MVP đạt.

Nguồn tham khảo quốc tế hỗ trợ lý luận về giới hạn mô hình. Phạm vi pháp lý/tiêu chuẩn cụ thể cho tàu/sà lan và chuyến của owner cần xác minh riêng. Không tự lấy ảnh hoặc tài liệu tham khảo làm profile được phê duyệt.

## 7. Bước tiếp theo

Local phản biện và xác minh trước; trả evidence và đề nghị. Owner/reviewer xử lý các điểm còn mở. Sau đó mới chốt contract vận hành, Final Baseline, roadmap và treeview dự kiến, rồi giao triển khai. Không coi tên phiên bản v0.3 là sự phê duyệt trước cho các lựa chọn còn chờ xác nhận.
