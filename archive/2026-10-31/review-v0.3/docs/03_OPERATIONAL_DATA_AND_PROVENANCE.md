# Dữ liệu vận hành, khối lượng và provenance — yêu cầu để local phản biện

**Package:** SCST-REVIEW-0.3. **Trạng thái yêu cầu:** `SPECIFIED_FOR_REVIEW`. **Các acceptance cases:** `FUTURE_LOCAL_ACCEPTANCE`.

Phạm vi: đánh giá package v0.2 có thật và xác định yêu cầu contract nghiệp vụ cần local đối chiếu. V0.2 được giữ nguyên trong ZIP lịch sử; đường dẫn schema/reference ở tài liệu này là đường dẫn bên trong v0.2. V0.3 chưa thay schema, chưa có backend vận hành và chưa phải IMPLEMENTATION_FREEZE. Đề nghị integer grams có trạng thái `PROPOSED_INTEGER_GRAMS`, chờ manifest mẫu và local chốt contract/migration trước khi triển khai.

## 1. Kết luận độc lập

| Nhận định | Kết luận | Căn cứ cụ thể |
|---|---|---|
| R2-02 — synthetic khi testOnly=false | Đồng ý. Cần invariant có thể kiểm ở tầng admission/persistence. | `manifest.schema.json` cho phép massBasis SYNTHETIC và common evidence cho phép sourceType SYNTHETIC độc lập với testOnly. `vessel_profile` dùng cùng evidence. |
| R2-08 — trace từng trường | Đồng ý. Hiện mới có prose và sourceLineId tự do. | Final manifest không pin intake draft, field claim hoặc confirmation receipt. Draft có path/rawText/locator nhưng không có source artifact ref/confirmation event cố định nối đến final value. |
| R2-04 — độ chính xác khối lượng | Đồng ý phải chốt trước khi pin contract nghiệp vụ. Chưa có manifest thật để kết luận 1 kg không đủ cho người dùng. | Schema dùng INTEGER_KG_NO_ROUNDING và integer massKg; thử 2000.5 kg bị từ chối đúng. Ba ảnh không chứng minh độ chính xác của manifest. |

**Mức độ:** hai probe R2-02 chứng minh schema nhận hình dạng dữ liệu; không chứng minh vượt quyền của ứng dụng. `reference/validator.py` chỉ có đường contract fixture và luôn trả `operationalEligible=false`. Prose hiện tại đã yêu cầu backend chống nâng nguồn synthetic bằng sửa cờ; thiếu phần machine contract và test integration thực thi yêu cầu đó.

## 2. Bằng chứng đã chạy

Script `probes/replay_r2_contract_probes.py` nhận `--package-root` trỏ thư mục v0.2 đã giải nén và `--output` ở ngoài package, chỉ đọc v0.2. Receipt ghi lệnh, runtime và hash các input; kết quả được tạo tại thư mục output được chọn. Bản evidence đã quan sát được đóng gói trong thư mục evidence theo manifest của release.

```text
python probes/replay_r2_contract_probes.py --package-root ../v02-extracted/Steel_Cargo_Stowage_Tool_v0.2_Local_Agent_Package --output ../r3-probe-evidence
```

Dùng dependency `jsonschema==4.26.0` trong môi trường riêng theo hướng dẫn package. Các probe cố ý chứa dữ liệu không hợp lệ nghiệp vụ để mô tả ranh giới schema; không nhập các record này vào luồng thật.

| Probe | Quan sát |
|---|---|
| Manifest VERIFIED, testOnly=false, source/mass synthetic | JSON Schema chấp nhận |
| Vessel testOnly=false, evidence cargo-limit synthetic | JSON Schema chấp nhận |
| Manifest đổi source thành DOCUMENT và mass thành DECLARED, dòng nguồn không thể resolve; sửa mass và tổng tương ứng | JSON Schema chấp nhận; chưa có binding tới nguồn/draft/confirmation |
| 2000.5 kg và tổng tương ứng | JSON Schema từ chối vì contract integer kg |
| validate_bundle mặc định, không fixture mode | operationalEligible=false; không có đường cấp quyền production |

Đây là 5 quan sát kiểm lại, không được cộng thành 5 bài nghiệm thu ứng dụng. Không thay schemas, fixtures hoặc mã của release v0.2.

## 3. Operational admission invariant

### 3.1 Tách ba khái niệm

1. Schema-valid: JSON có kiểu/trường/enum đúng.
2. Confirmed operational record: backend đã đối chiếu nguồn, provenance, actor và các điều kiện dữ liệu bắt buộc; đã ghi atomically nội dung cùng receipt.
3. Operationally eligible plan: còn phụ thuộc validator, profile, case hiện hành, quyền chọn/review và các điều kiện kỹ thuật. Trạng thái ở bước 2 không cấp bước 3.

Schema có thể bổ sung conditional cấm SYNTHETIC khi testOnly=false tại những trường nhìn thấy trực tiếp. Đây là lớp chặn sớm. Backend vẫn phải đi qua toàn bộ dependency graph vì schema không tự resolve authority, nội dung file hoặc lịch sử.

### 3.2 Điều kiện bắt buộc khi confirm nội dung thật

- `testOnly` và trạng thái môi trường được backend suy ra; không tin cờ gửi từ UI/agent/import.
- Mọi dependency cần cho record hiện hành phải có kind/ID/version/hash đúng, tồn tại, không thuộc TEST_ONLY hoặc registry nguồn synthetic. Không chỉ kiểm root manifest.
- Mọi nguồn phải resolve tới source registry do server quản lý. Nguồn DOCUMENT trỏ file có thật, bytes đúng hash; MANUAL_ENTRY trỏ sự kiện nhập/xác nhận thật. Không tạo document hash giả cho nguồn nhập tay.
- `sourceType`, `massBasis` hoặc metadata bị đổi từ SYNTHETIC sang DOCUMENT/DECLARED không thay provenance của bản ghi đã đăng ký. Đường nhập/confirm phải đối chiếu registry và test namespace gốc.
- Mọi giá trị quan trọng phải có field claim và confirmation coverage. Nguồn chưa resolve, thiếu, xung đột hoặc chưa xác nhận làm confirm thất bại và giữ draft.
- Actor lấy từ sự kiện xác thực server-side, đúng vai trò và đúng target/version/hash. `confirmedBy` do client gửi không là quyền.
- Confirmation receipt và snapshot được commit nhất quán. Crash, replay hoặc stale version không được để lại bản ghi VERIFIED thiếu receipt/bằng chứng.
- AI có thể trích xuất, đề xuất candidate và draft; không thực hiện confirm nghiệp vụ hoặc biến nguồn chưa kiểm thành nguồn verified.

Hệ thống chỉ có thể cấm nguồn mà registry đã biết là synthetic/test và bảo đảm quy trình xác nhận. Nó không có khả năng suy ra một tài liệu bị khai gian là thật chỉ từ nhãn DOCUMENT, hash hoặc ảnh. Xác minh sự thật của nguồn vẫn thuộc người có trách nhiệm.

### 3.3 Không tạo đường production giả trong reference

Giữ nguyên reference v0.2 ở chế độ synthetic, không thêm `fixture_mode=False => operationalEligible=true`. Nếu viết checker mô phỏng admission cho baseline kế tiếp, kết quả chỉ là `admissionContractChecksPass`, có phạm vi `SYNTHETIC_REFERENCE_ONLY`, operationalEligible vẫn false. Các test API/DB/session thật nằm ở local gate G1/G2/G4a.

## 4. Chuỗi provenance tối thiểu có thể kiểm

### 4.1 Các record và chiều tham chiếu

| Record | Trường hoặc quan hệ cần có |
|---|---|
| SourceArtifact / ManualEntryEvent | ID/version/hash; phân loại source/test do registry giữ; file bytes/hash hoặc event nhập tay; người nhập và thời điểm thật |
| IntakeDraft | ID/version/hash; mỗi trường có fieldId ổn định, raw text, unit/locale, candidate, source ref và source span có kiểu |
| Confirmed content | Các giá trị chuẩn hóa, schema version và immutable hash; không chứa hash ngược đến receipt xác nhận của chính nó |
| ConfirmationReceipt | targetRef đến đúng confirmed content; draftRef; actor/authentication event ref; timestamp; policy version; fieldClaims bao phủ các đường dẫn bắt buộc |
| FieldClaim trong receipt | target JSON Pointer, normalized value hoặc value hash, draft fieldId/ref, nguồn/span, phép chuẩn hóa, lựa chọn/correction reason khi có |
| Lifecycle/index | Liên kết receipt đã kiểm với targetRef; trạng thái hiển thị suy ra từ quan hệ hợp lệ |

**Chống vòng hash:** receipt trỏ targetRef. Target content không trỏ ngược receipt hash. Backend lưu quan hệ ngoài content hoặc lifecycle event. Nếu cần pin field-provenance vào content, tách thành record trước confirm chỉ chứa draft/source/value; receipt cuối vẫn trỏ target content, không đảo chiều.

JSON Pointer có thể dùng array index vì nó chỉ được resolve trong một snapshot đã pin hash; thay thứ tự array sẽ đổi hash. Khi diễn giải cho người dùng, dùng thêm cargoUnitId để tránh nhầm vị trí.

### 4.2 Source span có kiểu, không chỉ một chuỗi tự do

- PDF: file ref/hash, page index và vùng tọa độ có đơn vị/kích thước trang đã khai.
- Image: file ref/hash, pixel rectangle và kích thước ảnh/orientation. Nếu OCR dùng ảnh đã transform, pin artifact transform và phép ánh xạ về gốc.
- Spreadsheet: file ref/hash, sheet identifier/name, cell/range và row; xác minh địa chỉ tồn tại trong đúng phiên bản file.
- Manual: manual-entry event ref và câu hỏi/field nhập; không giả page hoặc cell.

`sourceLocator` vẫn có thể là nhãn dễ đọc, nhưng không đóng vai trò resolver hoặc bằng chứng duy nhất.

### 4.3 Danh sách trường quan trọng phải là policy có version

Bao gồm tối thiểu: identity/cargo limit và hiệu lực giấy; kích thước/phương pháp đo hầm và vật cản; ID/type/geometry/mass mỗi đơn vị hàng; profile và phạm vi áp dụng; trạng thái hầm, existing cargo, voyage limit, dunnage reserve; các thông số support/capacity dùng trong phép kiểm.

Các giá trị tính toán như tổng mass có thể dùng claim `DERIVED_AGGREGATE`, pin inputs và formula/policy version. Không yêu cầu người dùng xác nhận thủ công từng tổng đã được tính chính xác, nhưng không được mất đường truy về unit nguồn.

Phép chuẩn hóa phải thuộc danh sách được implement/test, chẳng hạn IDENTITY, UNIT_CONVERSION_EXACT hoặc DERIVED_AGGREGATE. Correction của người vận hành ghi rõ giá trị đã sửa, nguồn/quan sát mới hoặc lý do; không gọi một correction tùy ý là phép đổi đơn vị chính xác.

## 5. Đề nghị đơn vị mass cho contract nghiệp vụ kế tiếp

### 5.1 Đề nghị kỹ thuật — PROPOSED_INTEGER_GRAMS

Đề nghị dùng **integer grams** cho mọi khối lượng trong core tiếp theo (`massG`, `existingCargoG`, `voyageCargoLimitG`, `plannedDunnageMassG`, `maxSupportedMassG`...). UI và báo cáo vẫn hiển thị kg/tấn theo nhu cầu. Giữ v0.2 integer-kg reference làm lịch sử kỹ thuật; không âm thầm đổi ý nghĩa của field `massKg`.

Lý do đề nghị: biểu diễn chính xác phần kg lẻ tới 1 gram mà vẫn dùng số nguyên và giữ serialization đơn giản. Local phải lấy manifest mẫu, kiểm độ chính xác nguồn và ảnh hưởng migration/solver trước khi chốt đề nghị này. Nếu có nhu cầu dưới gram hoặc nguồn theo basis khác, local báo discrepancy thay vì tự làm tròn. Đây là lựa chọn độ chính xác của phần mềm, không phải khẳng định thiết bị cân hoặc hồ sơ thực có độ chính xác 1 gram.

### 5.2 Hợp đồng chuyển đổi

1. Lưu raw text, unit và locale/phân cách đã xác định từ nguồn; dấu phẩy/chấm mơ hồ giữ CONFLICT/NEEDS_CONFIRMATION.
2. Parse bằng decimal exact, không dùng binary float để tính giới hạn.
3. Đổi chính xác: t × 1,000,000; kg × 1,000; g × 1.
4. Chỉ confirm khi kết quả là integer gram và nằm trong miền cho phép. Nhỏ hơn gram không biểu diễn chính xác thì giữ draft, không truncate/down-round.
5. Mọi tổng, reserve, giới hạn và phép so sánh đều cùng đơn vị. Có kiểm overflow cho tổng/nhân trung gian và miền JS-safe của contract serialization.
6. Làm tròn chỉ được dùng cho hiển thị đã ghi rõ; không dùng con số hiển thị làm input vòng sau hoặc quyết định đạt/vượt.
7. Migration v0.2 dùng `oldKg × 1000`, phải kiểm overflow, đổi schema/field names, tạo snapshot/ref/hash mới và giữ lineage; receipt cũ không gắn sang hash mới.

Ví dụ theo locale thập phân phẩy đã được xác nhận: `2,0005 t` = `2,000,500 g` chính xác. Chuỗi `1,234 kg` chưa rõ là thập phân hay dấu tách nghìn thì không tự chọn cách hiểu. `0.0004 kg` = 0.4 g vẫn chưa hợp contract integer grams.

Không chia đều mass tổng line cho nhiều bó nếu nguồn không cho từng đơn vị hoặc chưa có quy tắc được chấp thuận. Đổi độ chính xác không giải quyết việc thiếu mass theo đơn vị solver.

## 6. Acceptance cases cần local triển khai

| ID | Ca thử | Expected |
|---|---|---|
| ADM-01 | Root testOnly=false nhưng nguồn/mass synthetic | Reject confirm; giữ draft, reason rõ |
| ADM-02 | Root sạch nhưng dependency profile/evidence testOnly | Reject khi duyệt graph; không chỉ kiểm root |
| ADM-03 | Sửa nhãn synthetic thành DOCUMENT trong payload | Registry gốc vẫn là test; reject |
| ADM-04 | Document hash sai bytes, nguồn/span không tồn tại | Reject bằng chứng và không tạo verified record |
| ADM-05 | Client giả confirmedBy/role; event không có thật | Server không cấp quyền; không commit confirmation |
| ADM-06 | Field claim thiếu một giá trị quan trọng hoặc normalized value không khớp | Reject coverage/value binding |
| ADM-07 | Đổi 1 g hoặc 1 mm sau confirmation | Hash đổi; receipt cũ không xác nhận bản mới |
| ADM-08 | Nhập tay có event thật và provenance đủ | Cho qua bước confirm dữ liệu nếu các điều kiện khác đủ, không đòi document hash giả |
| ADM-09 | Đổi đơn vị exact, chuỗi mơ hồ, phần sub-gram và overflow | Exact nhận; các trường hợp còn lại chặn/giữ draft với lý do |
| ADM-10 | Crash giữa snapshot và confirmation receipt | Không có verified record orphan; recovery nhất quán |
| ADM-11 | Replay/stale confirmation với target version khác | Từ chối hoặc yêu cầu review lại, không gắn tự động |
| ADM-12 | Một derived total khác tổng pinned inputs hoặc formula không biết | Reject; không tin total do client gửi |

Các ca này là tiêu chí đề nghị, chưa được triển khai trong backend. Không dùng probe script R3 thay thế chúng.

## 7. Hệ quả đối với vòng local kế tiếp

Vòng local đầu tiên nên xác minh đề nghị, kiểm khả năng map với source/DB/auth hiện có, lấy manifest mẫu và trả discrepancy. Chưa đóng implementation freeze hoặc viết app theo giả định source registry/receipt đã tồn tại. Sau khi chốt contract, mới pin schemas/migration cùng test integration và roadmap/treeview tương ứng.
