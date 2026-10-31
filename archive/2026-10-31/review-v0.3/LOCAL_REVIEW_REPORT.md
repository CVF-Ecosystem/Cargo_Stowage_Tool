# Phản biện local gửi Web Agent về baseline chất xếp hàng thép

Ngày: **31-10-2026**, timezone **Asia/Saigon (UTC+07:00)**. Đầu vào: **SCST-REVIEW-0.3**. Người thực hiện: Codex local agent. Chưa có kết luận của reviewer chuyên môn.

**Kết luận: tiếp tục phản biện và bổ sung căn cứ trước khi chốt Final Baseline. Hiện chưa dựng roadmap, chưa dựng treeview ứng dụng và chưa triển khai.** Hướng kiến trúc có cơ sở; khả năng giải được case nghiệp vụ đại diện còn chưa được chứng minh.

File này là phản hồi tổng hợp để owner chuyển cho Web Agent tìm hiểu thêm, theo cấu trúc `templates/LOCAL_REVIEW_RESPONSE.md`. Đây chưa phải toàn bộ bộ báo cáo tách riêng được liệt kê trong work order. Các đề nghị dưới đây chưa trở thành quyết định của owner hoặc contract đã chốt.

## 1. Nhận diện nguồn và trạng thái thực tế

| Nội dung | Quan sát local |
|---|---|
| Thư mục được review | `Cargo_Stowage_Tool/` trong CVF-Workspace |
| Repo/commit ứng dụng | Thư mục này chưa là Git repository; không có application commit để ghi nhận |
| Thành phần hiện có | Tài liệu yêu cầu/review, ảnh, ZIP lịch sử, schema/reference trong ZIP, tooling/probes/evidence |
| Backend/solver/schema vận hành mới | Chưa có trong package; `PACKAGE_MANIFEST.json:29–31` xác nhận |
| Môi trường thực | Windows 11 Home Single Language 64-bit, build 26200; RAM 16,849,293,312 bytes; Python 3.11.9; Node 22.17.0; npm 10.9.2 |
| Dependency review | Python mặc định có jsonschema 4.23.0; lần replay dùng venv riêng với jsonschema **4.26.0** đúng yêu cầu |
| TP ứng dụng / MVP nghiệp vụ | `NOT_EVALUATED`; chưa có runtime ứng dụng để nghiệm thu |
| Chấp thuận phương án hiện trường | `NOT_GRANTED` |
| Roadmap / treeview ứng dụng | **CHƯA_DỰNG**. Việc mô tả thành phần đang có không phải cây ứng dụng dự kiến |

Checksum v0.3 khớp **35/35 tệp được liệt kê**. ZIP v0.2 có SHA-256 `6f587938f48b24daef5eaf0ba3fcab7532ec0397c3d2f7a39ca2caf686da44df`, khớp source register. Checksum chỉ xác nhận bytes so với danh sách, không xác nhận tác giả hoặc tính đúng nghiệp vụ.

Local đã đọc README, MASTER, REVIEW_R3_RESPONSE, DECISION_LOG, docs 01–07, R2 audit, mẫu phản hồi/case intake; xem trực tiếp ba ảnh; đọc các phần contract/reference liên quan trong ZIP v0.2 và chạy wrapper review. Không sửa tài liệu baseline, schema/reference lịch sử hoặc CVF core.

## 2. Các điểm có cơ sở và các khoảng thiếu chính

### 2.1 Những nguyên tắc nên giữ

- Core chạy khi AI tắt; backend authorization, cargo validator và CVF action control có trách nhiệm riêng.
- Tách Technical Proof, MVP nghiệp vụ và chấp thuận một phương án/chuyến cụ thể.
- Snapshot bất biến, hash/version, phân hoạch toàn manifest và validation mới sau sửa tay.
- Tách collision envelope, cấu hình kê/đỡ và hình hiển thị; giữ 2D/text fallback và đối soát PDF/XLSX.
- Không biến UNKNOWN thành PASS bằng score, AI, nhãn APPROVED hoặc attachment chưa đối chiếu.

Đây là nhận định thiết kế dựa trên MASTER mục 1–5 và docs 01–04, chưa phải kết luận runtime.

### 2.2 Khoảng thiếu cần xử lý trong vòng phản biện

**Case thật và mô hình hàng:** `templates/CASE_INTAKE.md:17–23` chưa có manifest, số đo, profile và bố trí tham chiếu. Chưa biết đơn vị solver phải đặt là bó, từng ống hay một đơn vị khác. Chưa đủ dữ liệu xác định BOX hoặc envelope hiện tại có phục vụ pilot hay không.

**Contract mới:** yêu cầu v0.3 về source registry, field claims, confirmation receipt, external review và grams chưa có schema/backend tương ứng. Cần reconcile domain, wire format, lifecycle và persistence trước freeze. Chỉ đổi version string của schema cũ sẽ không hiện thực các yêu cầu đó.

**Kê/chồng và sinh phương án:** cấu hình được chuyên môn chấp thuận là đầu vào quan trọng của cả solver lẫn validator. Việc mô tả một profile và việc tự động tạo được candidate theo profile là hai nghĩa vụ khác nhau. Cần làm rõ dữ liệu nào đủ cho từng cấu hình và có oracle độc lập để kiểm kết quả. Chưa có căn cứ cam kết thuật toán hoặc thời gian giải.

**Tính thực dụng của external review:** docs 04 đã có cấu trúc hợp lý nhưng chưa xác định quy trình thật để kiểm thẩm quyền, binding, hiệu lực, thu hồi và độ mới của lần kiểm trong môi trường local. Một workflow luôn chờ bằng chứng không có nguồn cung sẽ khó dùng; phải chỉ rõ phần nào chờ và công việc nào vẫn được phép thực hiện.

**Độ chính xác:** grams giải quyết biểu diễn khối lượng tới gram; không giải quyết thiếu mass từng unit, sai số cân hoặc số đo geometry. Đề nghị bổ sung cách ghi độ chính xác/phương pháp đo và margin có nguồn, phân biệt chúng với độ phân giải của phần mềm. Đây là đề nghị local cần phản biện, chưa phải yêu cầu đã được duyệt.

**Hiệu năng và fidelity:** chưa có quy mô thường/lớn, thời gian chờ hoặc mức mất khả năng xếp chấp nhận được do xấp xỉ. Chưa nên đưa số hiệu năng, phần trăm tận dụng hay thời hạn triển khai từ fixtures nhỏ.

### 2.3 Đối chiếu ảnh

| Ảnh | Quan sát trực tiếp có thể dùng | Giới hạn |
|---|---|---|
| `inputs/photos/1.jpg` | Nhóm hàng dài, vật thể dạng cuộn, vật kê và thiết bị bánh xích trong vùng hàng | Chưa xác định máy đang chạy/đỗ, tải, đường truyền lực, kích thước hoặc từng đơn vị manifest |
| `inputs/photos/2.jpg` | Nhiều cao độ, nhóm tiết diện tròn xen với nhóm bó và vật thể dạng cuộn phía thấp | Chưa xác định mọi loại hàng, quan hệ đỡ khuất hoặc số unit độc lập |
| `inputs/photos/3.jpg` | Nhóm bó hàng dài phía trên các hàng tiết diện tròn | Chưa đủ bằng chứng về contact, chống lăn hoặc tính hợp lệ của cấu hình |

Local đồng ý cách giới hạn suy luận của docs 05. Không xác nhận ba ảnh cùng chuyến hoặc là ba case độc lập; không tạo thông số kỹ thuật từ ảnh.

## 3. Phản hồi từng nhận định R2 và quyết định v0.3

Đường dẫn `v0.2::...` dưới đây chỉ tệp bên trong ZIP lịch sử đã pin, không phải source ứng dụng đã triển khai. Bằng chứng chạy thật nằm trong mục 6.

### 3.1 R2

| ID | Kết luận local | Căn cứ | Đề nghị và điều kiện đóng |
|---|---|---|---|
| R2-01 | Đồng ý; còn chờ quyết định phạm vi | MASTER mục 2–3; docs 01:34–38; CASE_INTAKE còn trống | Owner xác nhận công việc hầm trống/occupied, danh mục hàng và case đại diện. Không lấy ảnh final làm initial state |
| R2-02 | Đã tái lập schema gap; chưa đóng bằng runtime | Probes `R2-02-MANIFEST`, `R2-02-VESSEL` đều schemaAccepted=true | Giữ admission invariant; cần schema/domain/API/DB enforcement và ADM tests sau khi contract được chốt. Không gọi đây là runtime bypass |
| R2-03 | Đồng ý hướng sửa; chưa chốt quy trình | docs 04; `v0.2::docs/04_CVF_AND_LOCAL_AUTH.md` | Chốt ý nghĩa reviewer/recorder/verifier, nguồn thẩm quyền và binding. Không migration bằng cách thay actor name trên receipt cũ |
| R2-04 | Grams hợp lý để tiếp tục đánh giá; chưa đủ dữ liệu chốt | Probe fractional kg bị từ chối đúng; docs 03 mục 5 | Lấy manifest mẫu; chốt miền số, conversion, tổng/trung gian, wire/hash và migration. Không tự chia mass line cho unit |
| R2-05 | Giữ vấn đề mở cho MVP nghiệp vụ | docs 02:72–90; CASE_INTAKE thiếu profile | Có đủ profile cho các quan hệ dùng trong CASE-A/B, gồm mixed vertical nếu pilot bắt buộc; đối chứng model và negative cases |
| R2-06 | Chờ variant; không kết luận R2 sai | Hai bản R1 trong ZIP trực tiếp/lồng cùng 59,296 bytes và hash `adf11a56…`; v0.1 ZIP khớp hash đăng ký | Cần bytes/SHA của variant R2. Local chỉ tự đối chiếu hai bản R1 nói trên; không nâng thành tự xác minh cả bảy vị trí của receipt web |
| R2-07 | Đồng ý; giữ ranh giới bằng chứng | Replay local 86/86, reference scope; chưa có app runtime | LAT/ADM/ER/MB vẫn là tiêu chí tương lai. Chỉ đóng gate bằng runtime và đúng vai trò nghiệm thu |
| R2-08 | Đã tái lập thiếu field binding ở schema; chưa đóng bằng runtime | Probe `R2-08-NO-FIELD-LINK` được schema nhận; docs 03 mục 4 | Field claims bind target/draft/value/source; coverage có version; transaction và stale/replay tests tại backend |

### 3.2 D3

| ID | Kết luận local | Căn cứ và điều kiện còn lại |
|---|---|---|
| D3-01 | Giữ | MASTER mục 1; cần chứng minh core AI-off và quyền backend khi có runtime |
| D3-02 | Đồng ý tách TP/MVP | docs 01; cả hai chưa được nghiệm thu từ suite reference |
| D3-03 | Giữ yêu cầu nhiều tầng/nhiều nhóm trong phạm vi đã xác nhận | docs 02 mục 6; cần case và profile đúng quan hệ; đặt cạnh nhau chưa chứng minh mixed support |
| D3-04 | Giữ BOX có điều kiện | docs 02 mục 4; cần containment trên chiều cao sử dụng và benchmark giá trị case |
| D3-05 | Chờ owner xác nhận | Hầm trống là đề nghị pilot; ảnh không xác định công việc thường gặp |
| D3-06 | Đồng ý tách form/packaging/unit/group | docs 02 mục 3; cần mẫu manifest để pin semantics và reconciliation |
| D3-07 | Giữ tách ba mô hình | docs 02 mục 5; mức false rejection của AABB chưa đo trên case pilot |
| D3-08 | Giữ hướng viewer theo nhiệm vụ | docs 02 mục 8; chưa có UI, benchmark thao tác hoặc kiểm export |
| D3-09 | Đồng ý hoãn thuật toán có điều kiện scenario | docs 02 mục 7; thiết bị trong 1.jpg chưa có dữ liệu tải/review |
| D3-10 | Giữ ngoài scope có blocker rõ | MASTER mục 6; cần xác nhận pilot vẫn đại diện khi chưa hỗ trợ các phần đó |
| D3-11 | Áp dụng REVIEW_ONLY | START_HERE mục 1/4; **chưa dựng roadmap/treeview và chưa thi công** |
| D3-12 | Giữ các bất biến kế thừa | MASTER mục 5; cần reconcile khi đổi đơn vị/record, bảo toàn lineage và giới hạn bằng chứng |

## 4. Contract delta cần Web Agent phản biện

Các dòng dưới đây là phân tích và đề nghị trước freeze, chưa phải schema, migration hoặc API đã viết.

| Thành phần | V0.2 có thật / khoảng thiếu | V0.3 yêu cầu và câu hỏi cần giải quyết | Compatibility và kiểm chứng sau này |
|---|---|---|---|
| Admission | Schema cho synthetic độc lập với testOnly; reference không cấp operational eligibility | Registry authoritative, kiểm mọi dependency, actor server-side; xác định đường draft/confirm/reject và transaction boundary | ADM-01…05/10/11; không đổi fixture thành record thật bằng sửa nhãn |
| Provenance | sourceLineId và prose chưa chứng minh binding từng trường | SourceArtifact/ManualEntryEvent, IntakeDraft, FieldClaim, ConfirmationReceipt; cần coverage policy và resolver có kiểu | ADM-04/06/07/12; chống vòng hash; correction và derived aggregate giữ lineage |
| External review | FIELD_REVIEW cũ gắn authenticated reviewer trong app | Statement/registration/verification; tách thẩm quyền kỹ thuật và hành động ghi nhận; bind plan/case/rules/dependencies | ER-01…09; schema/version mới khi semantics đổi; không chuyển auth operator thành auth reviewer |
| Mass | Integer kg; canonical số nguyên trong miền JS-safe | Đề nghị integer grams cho mọi mass/limit/reserve, exact decimal parsing và policy locale | ADM-09, LAT-003/006/016; lineage/hash/receipt mới khi chuyển đơn vị; ngưỡng vượt nhỏ nhất cần reconcile sang đơn vị mới |
| Cargo units | Hai cargo enums; unit có dimensions riêng | Pin form, packaging, handling unit, grouping và cách xử lý unsupported tại intake | MB-02; không làm mất dòng hoặc đổi unsupported thành excluded ngầm |
| Hold geometry | BOX/exclusions/frame có contract | Có thể giữ inner BOX nếu có nguồn và fidelity; nếu thiếu, cần chọn model dựa case | LAT-009, MB-03/06; cùng geometry cho solver/validator/viewer/export; precision số đo cần làm rõ |
| Support/arrangement | FULL_BASE_SUPPORT, compatibility có hướng và tải descendants bảo thủ | Profile/template hữu hạn, điều kiện kê/chồng, children IDs, mass và nguồn review; cần biết dữ liệu nào validator kiểm được | LAT-010/011, MB-04/05; không tự phân lực đều hoặc cho overlap tùy ý |
| Solver/run/manual edit | Mode/status/proof và lineage đã mô tả | Contract generation theo profile phải đủ cho tự động sinh candidate; sửa tay giữ parent và validation riêng | LAT-013…017, MB-07/08; oracle độc lập; timeout và heuristic không chứng minh vô nghiệm |
| Persistence/API | Immutable records/receipts/lifecycle và atomicity đã là yêu cầu | Cụ thể hóa cùng DB/file store, idempotency, optimistic concurrency, error/recovery semantics | LAT-021, ADM-10/11, ER-09; chưa có DB/API hiện thực để đối chiếu |

Trước khi chốt, cần một bảng thống nhất: loại record → trạng thái/lifecycle → hành động được phép → principal → preconditions → bằng chứng → transaction → lỗi/khôi phục. Web Agent đề nghị contract ở mức review; Local kiểm khả năng thực thi khi được giao vòng tiếp theo. Không cần owner lựa chọn serializer, thuật toán hoặc cấu trúc repo.

## 5. Nghiệm thu và dữ liệu còn thiếu

### 5.1 Mapping tiêu chí

| Nhóm | Mốc và mapping | Bằng chứng hiện có | Phần chưa có |
|---|---|---|---|
| Dữ liệu/nguồn/mass | TP rồi MVP; LAT-001…006/016/025; ADM-01…12; MB-02/11 | Schema/reference checks và probes trên synthetic | API/session/source registry/persistence và case thật |
| Scope/hầm/support | TP rồi MVP; LAT-007…011; MB-01/03…06/13 | Contract tham chiếu và quan sát ảnh | Geometry có nguồn, profiles, bố trí đối chứng, dữ liệu scenario tải tạm |
| Solver | TP rồi MVP; LAT-013…015; MB-07/08/14 | Run/status contract tham chiếu | Solver chạy thật, oracle nhỏ độc lập, benchmark case đại diện |
| UI/quyền/review | TP rồi MVP; LAT-012/017/018/022…024; ER-01…08; MB-09/10/12 | Yêu cầu đã viết | Luồng người dùng, auth, binding, export và đối chiếu chuyên môn |
| Recovery | TP và điều kiện MVP; LAT-021; ADM-10/11; ER-09 | Yêu cầu đã viết | Crash/race/restore trên DB/files thực |
| CVF Agent actions | G4b nếu phạm vi sau này bật; LAT-019/020 và phần Agent của LAT-018 | Biết nguồn local khác baseline | Pinned source, API mapping, guard coverage và bridge/runtime tests |

Mapping này không tuyên bố mọi acceptance case đã được review chi tiết hoặc chạy. Không cộng số ID thành số tests đạt.

### 5.2 Case và oracle

- **CASE-A:** manifest đầy đủ, hầm có nguồn, nhiều tầng/nhiều kích thước, profile áp dụng và bố trí đối chứng đã được rà soát.
- **CASE-B:** hồ sơ độc lập, nhiều nhóm; nếu mixed vertical là nhu cầu bắt buộc thì phải có đúng cặp support được chấp thuận.
- **CASE-C:** thiếu nguồn/profile, loại hàng ngoài scope hoặc điều kiện review chưa đủ; expected phải chỉ rõ giữ draft, từ chối hoặc chờ bước nào.
- **TP:** fixtures nhỏ có expected được tính/kiểm độc lập; dữ liệu synthetic luôn giữ nhãn test.

Đội phát triển chuẩn bị kỹ thuật kiểm thử, oracle và bằng chứng; owner cung cấp quyết định nghiệp vụ và nguồn sẵn có. Reviewer chuyên môn xác nhận phần thuộc thẩm quyền. Không chuyển nghĩa vụ thiết kế test kỹ thuật sang owner.

Quy mô thường/lớn, time budget, thao tác viewer, thời gian parse/solve/revalidate/export và ngưỡng fidelity còn **PENDING**. Chỉ thống nhất thông số phù hợp case trước lần test tương ứng; chưa tự đặt số để đóng acceptance.

## 6. Evidence local và giới hạn

Bản sao log/receipt của lần chạy trước và các observations bổ sung nằm trong [LOCAL_REVIEW_EVIDENCE_2026-10-31](LOCAL_REVIEW_EVIDENCE_2026-10-31/). Các receipt giữ nguyên đường dẫn tuyệt đối/cwd nơi đã chạy. Không chỉnh receipt để làm như đã chạy trong thư mục bàn giao.

| Kiểm chứng | Expected | Actual | Phạm vi |
|---|---|---|---|
| `python -B tooling/verify_package.py` | Tệp được liệt kê khớp checksum | 35/35 khớp | Integrity các tệp release được liệt kê |
| Wrapper `tooling/replay_review_checks.py --output <external-dir>` | 3 bước hoàn thành | completed=true; cả 3 exitCode=0 | Review/reference |
| V0.2 checksum | Khớp release manifest | 65/65 khớp | Integrity ZIP lịch sử đã giải nén |
| V0.2 suite | Không lỗi fixture contract | 86 tests, 0 failures, 0 errors, 0 skipped | CONTRACT_REFERENCE_ONLY |
| Bốn schema probes | Nhận/nhận/nhận/từ chối | `[true, true, true, false]` | JSON_SCHEMA_ONLY |
| Reference mặc định | Không cấp operational eligibility | operationalEligible=false | Không phải backend production |

Replay bắt đầu **16:07:24.739826**, kết thúc **16:07:27.395279 ngày 31-10-2026 UTC+07:00**. Wrapper/probe/input/log hashes và exact commands có trong receipt; thời gian này không là benchmark ứng dụng.

R1 trong ZIP trực tiếp và ZIP handoff lồng đều có SHA-256 `adf11a5682ea541d01a5b3ed348c6274938532a45ced23c49e91fa6ea6a08d8f`. ZIP v0.1 lồng có SHA-256 `511bd790a07b880c734df5d8e730c3a5a71c00f1affc64c01a92159a76ceda9e`, khớp giá trị đăng ký; bản upload độc lập không có tại project này để so lại cặp bytes.

### 6.1 CVF

- Baseline v0.2 yêu cầu `Blackbird081/Controlled-Vibe-Framework-CVF-Provenance`, SHA `ebf31b9f5c42e4de58f40a434409c3441a5d8383`.
- Checkout trong workspace là `.Controlled-Vibe-Framework-CVF`, origin `https://github.com/Blackbird081/Controlled-Vibe-Framework-CVF.git`, SHA quan sát `15e39450853184eb65dbde73398c69c3171a6241`; working tree sạch tại lần kiểm.
- `git cat-file -t <pinned-sha>` không tìm thấy object trong clone hiện có. Đây là giới hạn nguồn local; không chứng minh commit không tồn tại ở nơi khác.
- `LICENSE` của checkout public ghi **CC BY-NC-ND 4.0**. Đây chưa là license của nguồn Provenance còn thiếu và chưa phải kết luận quyền sử dụng/tích hợp cho dự án.
- Root `package.json` public có devDependency `@types/node: ^25.3.0`; đây là inventory cấp root, chưa phải dependency/runtime matrix của engine cần tích hợp.
- API/export/guard contract của **đúng pinned source**: **NOT_VERIFIED / BLOCKED_BY_SOURCE**. Chưa có mapping hay runtime integration được kiểm. Không lấy protocol do SCST đề xuất làm API canonical của CVF.

Local chưa chạy backend, production solver, UI, DB recovery, bridge CVF hoặc đánh giá kỹ thuật hiện trường. Các nguồn chuyên ngành công khai trong docs 07 chưa được local tái xác minh trên web ở vòng này; phần nghiên cứu bổ sung thuộc mục 7.

## 7. Các câu hỏi và yêu cầu nghiên cứu gửi Web Agent

### 7.1 Câu hỏi nghiệp vụ cần owner hoặc chuyên môn xác nhận

| ID | Câu hỏi | Người có thông tin/thẩm quyền | Ảnh hưởng và mốc bị chặn |
|---|---|---|---|
| OD-01 | Công việc pilot là lập trước từ hầm trống hay bổ sung/điều chỉnh khi hầm có hàng? | Owner/người lập phương án | G0 và phạm vi initial-state/geometry/support |
| OD-02 | Những loại hàng nào bắt buộc có; một dòng manifest đại diện đơn vị gì; có mass/dimensions từng unit không? | Owner/đơn vị cung cấp manifest | G0, cargo semantics, precision, MB-02 |
| OD-03 | Case bắt buộc có mixed vertical support nào; hồ sơ kê/chồng và ai chịu trách nhiệm xác nhận? | Người vận hành và chuyên môn | Profile/geometry; MB-04/05 |
| OD-04 | Có bản đo/bản vẽ hầm và bố trí tham chiếu liên hệ cùng manifest không? | Đơn vị quản lý phương tiện/chuyên môn | MB-03/06; lựa chọn BOX hay model khác |
| OD-05 | Quy trình thực có thiết bị lên hàng ở giai đoạn nào; phạm vi review nào đã có? | Người vận hành/chuyên môn | MB-13 và điều kiện sử dụng scenario |
| OD-06 | Ai review, ai ghi nhận/đối chiếu; hồ sơ nhận từ đâu và kiểm hiệu lực/thu hồi bằng cách nào? | Đơn vị chịu trách nhiệm quy trình | External review contract; MB-12, ER |
| OD-07 | Số unit thường/lớn và thời gian làm hiện tại; người dùng cần phản hồi trong khoảng nào? | Owner/người dùng | Đội kỹ thuật chuyển thành benchmark; G3, MB-14 |

Không yêu cầu owner trả lời tất cả mới tiếp tục nghiên cứu độc lập. Thiếu nguồn/chuyên môn chỉ chặn kết luận và phần việc phụ thuộc.

### 7.2 Nội dung Web Agent cần tìm hiểu thêm

| ID | Vấn đề nghiên cứu | Kết quả cần trả |
|---|---|---|
| W-01 | Mô hình hóa manifest và handling unit cho đúng dạng hàng pilot | Các lựa chọn semantics, ví dụ dữ liệu có nguồn hoặc ví dụ synthetic ghi nhãn rõ; danh sách trường còn phải lấy từ owner. Không tự tạo manifest thật |
| W-02 | Profile/template kê/chồng hữu hạn | Phân biệt dữ liệu hình học kiểm được và kết luận chuyên môn; mẫu nội dung profile, phạm vi trên/dưới, kê/chống lăn, limits, coverage và ca từ chối. Không tự cấp rating |
| W-03 | BOX/AABB so với mô hình cần cho case | Phân tích cách đánh giá containment, mất khả năng xếp do envelope và lựa chọn arrangement/geometry; chỉ ra điều kiện cần số đo. Không chọn model chỉ theo ảnh |
| W-04 | External review vận hành được trên máy local | Luồng nhận–ghi nhận–đối chiếu–sử dụng–hết hiệu lực/thu hồi, bằng chứng binding và cách xử lý khi thiếu nguồn kiểm. Nêu công việc vẫn làm được ở trạng thái chờ |
| W-05 | Admission/provenance và contract grams | Phản biện bảng delta mục 4; xác định record, field coverage, authoritative actor, transaction, migration, số nguyên và precision. Tách yêu cầu kế thừa khỏi đề nghị mới |
| W-06 | Nguồn CVF và điều kiện dùng đúng bản | Xác định nguồn/commit mà baseline thực sự muốn dùng, đường tiếp cận hợp lệ và license tại đúng revision. Nếu Web không truy cập source riêng thì giữ BLOCKED_BY_SOURCE; không suy API từ tài liệu hoặc public checkout khác |
| W-07 | Căn cứ nghiệm thu, fidelity và hiệu năng | Đề nghị cách chọn CASE-A/B/C, oracle, rubric nhiệm vụ người dùng và phương pháp đặt ngưỡng dựa dữ liệu thật. Chưa chốt con số khi chưa có case |
| W-08 | Phạm vi nguồn chuyên ngành | Kiểm lại các nguồn gốc trong docs 07, phiên bản/ngày/phạm vi áp dụng. Phân biệt hướng dẫn chung với dữ liệu/profile của phương tiện và yêu cầu pháp lý thực sự áp dụng; không tự tuyên bố áp dụng cho mọi tàu/sà lan |

Với nội dung kỹ thuật, ưu tiên tài liệu gốc, tiêu chuẩn/nguồn chính thức và source đúng revision. Mỗi phát hiện cần URL hoặc file/section/revision, ngày kiểm, phát biểu được nguồn hỗ trợ, giới hạn và tác động tới yêu cầu. Bài giới thiệu sản phẩm hoặc một bố trí lịch sử không thay profile được chấp thuận. Không dùng sự đồng ý giữa các AI làm oracle độc lập.

### 7.3 Hình thức phản hồi cần nhận lại

Đề nghị Web Agent trả **bản phản hồi review**, gồm disposition từng R2/D3/W, evidence, contract delta được đề xuất, câu hỏi còn phụ thuộc owner/chuyên môn và trạng thái từng điều kiện đóng. Với nguồn chưa truy cập được, ghi rõ chưa xác minh; không điền giả để hoàn thiện bảng.

**Vòng này chưa yêu cầu dựng roadmap, treeview hoặc thi công.** Sau khi các phản biện được xử lý và owner quyết định phạm vi, mới xem xét chốt Final Baseline rồi xây roadmap/treeview ở vòng được giao tiếp theo. Việc nhận file phản biện này không tự cấp quyền triển khai.
