# SCST — Roadmap tổng thể và kiến trúc dự kiến

Status: ACTIVE

**Bản v0.3 · cập nhật tiến độ 01-11-2026.** Owner đã thống nhất hướng, bổ sung hình tàu, M2a và nguồn list ống V1.1. M1, VINAFCO268, M2a, nguồn list ống, M2b và M2c đạt kiểm kỹ thuật; nghiệm thu nghiệp vụ và điều kiện dùng thực vẫn tách riêng. Phạm vi từng phần được giới hạn trong SPEC/WORK_ORDER.

## Mục tiêu và phạm vi

Tạo tool local cho một người dùng chính: **nhập hàng + hầm → lập phương án sơ bộ → xem bảng/3D → chỉnh và kiểm lại → lưu, so sánh, xuất PDF/Excel**. Core chạy được khi tắt AI. Giao diện và tooltip tiếng Việt, ngày dd-mm-yyyy.

Bắt đầu bằng bó thép thanh/bó thép ống có kích thước bao rõ, giữ nguyên từng bó; hầm BOX trước. Mở rộng nhiều tầng, nhóm hàng khác nhau và hình học hầm theo case thực ở M3. Điều phối cảng, xe/cẩu, ERP/WMS, mô phỏng cơ học tổng quát và cloud nhiều người dùng nằm ngoài phạm vi khởi đầu.

**Luồng chính:** M0 → M1 → M2 → M3 → M5. **M4 là nhánh tùy chọn**, xem xét sau khi core có ích; không phải điều kiện để làm M5. Các mốc mô tả kết quả, chưa cam kết thời lượng.

## Phạm vi và đầu ra từng mốc

| Mốc | Phạm vi | Đầu ra / điều kiện chuyển mốc | Phụ thuộc và thông tin cần đúng lúc |
|---|---|---|---|
| M0 — Thống nhất hướng | Chốt mục tiêu, ranh giới, thứ tự mốc và kiến trúc tổng thể trong bản này | **Đã đạt 31-10-2026:** owner thống nhất bản này; phần tiếp theo là SPEC M1 | Không dựng app trong M0 |
| M1 — Khung chạy được | FE/BE tối thiểu; hầm BOX và bó hàng synthetic; API nối bảng và 3D; thay một dữ liệu và kiểm cơ bản. Contract dữ liệu chừa trường z, lớp và quan hệ đỡ để mở rộng; M1 không triển khai logic nhiều tầng | Chạy local theo hướng dẫn; bảng/3D cùng unit ID, tọa độ và số liệu backend; thấy được một lỗi vượt tải hoặc vượt biên. Có bằng chứng chạy và giới hạn demo | SPEC M1 bắt đầu bằng đối chiếu bản thử trong archive với tiêu chí M1, sửa phần thiếu thay vì viết lại từ đầu. Dùng dữ liệu demo có nhãn |
| M2 — Tool cơ bản dùng trọn luồng | Làm theo thứ tự: **M2a** nhập tay/import, kiểm khối lượng/hình học, lưu/mở; **M2b** heuristic xếp sơ bộ, hàng chưa xếp và lý do; **M2c** chỉnh/kiểm lại, giữ bản trước, so sánh; **M2d** xuất PDF/XLSX | Người dùng hoàn tất luồng nhập → gợi ý → xem/chỉnh → lưu/mở lại → xuất. Mọi đơn vị hàng được đối soát; bản trước khi sửa được giữ; dữ liệu bảng, 3D và báo cáo khớp nhau | Khung M1 đạt yêu cầu. **Trong M2a:** xin một manifest mẫu và một bộ số đo hầm thật để kiểm importer và giả định BOX. **Nếu chưa có dữ liệu thật:** vẫn làm tiếp M2b–M2d trên hầm/hàng demo có nhãn, bộ xếp đọc hầm qua lớp `geometry` để không gắn chặt vào BOX, kết quả ghi "chưa xác minh hình học". Chờ số đo thật mới được chốt contract hình học, dùng phương án cho hầm thật hoặc nghiệm thu M2 là dùng được cho hầm thật. Nếu số đo thật cho thấy BOX không phù hợp, đổi contract hình học trước khi làm tiếp phần xếp. Mỗi phần có SPEC riêng khi đến lượt |
| M3 — Hoàn thiện tool với case thực | Case đại diện; nhiều tầng, nhóm kích thước khác nhau; profile kê/chồng, geometry cần thiết; cải thiện thao tác | Có case thực được đối chiếu, phạm vi sử dụng đã xác nhận và phần chưa hỗ trợ nêu rõ; người dùng thực hiện được công việc đại diện | Cần manifest, số đo hầm và profile phù hợp cho từng cấu hình; owner bố trí người hiểu nghiệp vụ đối chiếu. Agent chịu trách nhiệm kiểm kỹ thuật trước |
| M4 — AI hỗ trợ, nếu có ích | Tác vụ cụ thể như trích xuất, hỏi bổ sung, giải thích hoặc đề xuất chỉnh; actions qua quyền backend và CVF | Giảm thao tác ở tác vụ đã chọn; người dùng xác nhận thay đổi; core vẫn chạy khi AI tắt. Có kiểm chứng tích hợp thật trong phạm vi được bật | Owner xác nhận nhu cầu/tác vụ trước; lúc đó mới chọn provider, cách tích hợp và xử lý license CVF. Có thể hoãn hoặc bỏ nhánh này |
| M5 — Hoàn thiện để sử dụng ổn định | Bộ cài/khởi chạy, độ bền lưu trữ, backup/restore, hiệu năng; lịch sử/quyền/review theo nhu cầu đã xác nhận | Cài/chạy theo hướng dẫn, lưu dữ liệu bền, khôi phục được bản sao và vận hành ổn định trong phạm vi đã thử | Dựa trên tool đã được dùng thử ở M3; M4 không bắt buộc. Nhiều người dùng, cloud, tích hợp ngoài cần quyết định phạm vi riêng |

M1 chỉ chứng minh khung và luồng dữ liệu; **M3 mới xử lý nhu cầu thực tế nhiều tầng**. M1 chỉ chừa trường dữ liệu cho nhiều tầng để không phải đổi contract, không làm logic xếp/kiểm nhiều tầng. Lưu/mở và giữ bản trước đã thuộc M2; M5 hoàn thiện độ tin cậy khi vận hành. Chưa yêu cầu thuật toán chứng minh tối ưu toàn cục. Tiêu chí đo được của mỗi mốc chốt trong SPEC của mốc đó.

Mỗi mốc có một checkpoint khi đủ đầu ra hoặc phát hiện thay đổi ảnh hưởng phạm vi: agent cung cấp bản chạy/bằng chứng, kết quả kiểm và phần còn thiếu; owner quyết định tiếp tục, điều chỉnh hướng hoặc tạm dừng. Lỗi kỹ thuật trong phạm vi được giao do agent tự sửa và kiểm lại trước khi xin phản hồi nghiệp vụ.

## Hình tàu minh họa — hướng đã thống nhất

Owner đồng ý ngày 31-10-2026 bổ sung lớp hình tàu để nhìn vị trí hầm và hàng trong bối cảnh toàn tàu. Đây là phần hiển thị của M2, được tinh chỉnh ở M3; M1 hiện chỉ có hầm BOX và hàng synthetic.

**Lát cắt triển khai sớm:** sau khi owner cung cấp `VINAFCO268_LOCAL_HANDOFF` và yêu cầu đánh giá/tích hợp nếu phù hợp, chế độ VINAFCO 268 đã được tích hợp riêng theo [SPEC VINAFCO268](../specs/SCST_VINAFCO268.md), có [review kỹ thuật](../reviews/SCST_VINAFCO268_REVIEW.md). Giữ mặc định M1; thêm profile theo hồ sơ, hình tàu mờ, marker SI/SII và hàng synthetic trong hầm ước tính. Phần hiển thị này không hoàn tất M2c hoặc xác minh geometry hầm thực ở M3; các phần M2 khác chưa được giao thi công.

| Mốc | Phạm vi bổ sung | Đầu ra dự kiến |
|---|---|---|
| M2 — viewer, gắn với M2c | Vỏ tàu, boong, hướng mũi/đuôi và vị trí hầm mang tính minh họa; bật/tắt hoặc làm mờ vỏ để xem hàng | Nhìn được bối cảnh tàu mà vẫn chọn/xem hầm và hàng; bảng/3D giữ cùng ID, kích thước và tọa độ backend; hiện nhãn hình tàu giả lập |
| M3 — đối chiếu dữ liệu thực | Hiệu chỉnh hình tàu và vị trí hầm theo số đo/tài liệu được cung cấp, trong mức cần cho công việc đại diện | Phân biệt phần đã đối chiếu và phần còn minh họa; geometry hầm dùng để kiểm được xác minh riêng theo case thực |

`viewer-3d` sở hữu lớp hình tàu minh họa; backend `geometry` sở hữu hình học dùng để kiểm. Mô hình tàu không tự trở thành biên xếp hàng hoặc bằng chứng phương án hợp lệ. Trước khi có dữ liệu vị trí hầm trên tàu, vị trí hiển thị cũng phải ghi là giả lập. Chưa đưa CAD đóng tàu, thủy tĩnh/ổn định tàu hoặc mô phỏng động lực vào phạm vi này.

Orchestrator đưa phần M2 vào SPEC M2c khi đến lượt; agent chứng minh hiển thị/chọn hàng và đối chiếu số liệu trước checkpoint owner. M3 phụ thuộc dữ liệu tàu/hầm do owner cung cấp. Hiện chỉ chốt phạm vi/đầu ra; chưa chọn mesh, thư viện bổ sung hoặc danh sách file triển khai.

## Tiến độ phần đang làm — M2b

M2a và nguồn list ống đã có: nhập tay/CSV/lưu-mở,31nhóm/1076bó/21226ống, nguồn/provenance và khối bao chính xác được giữ. Xem [SPEC M2a](../specs/SCST_M2A.md), [review nguồn](../reviews/SCST_PIPE_LIST_REVIEW.md). Hầm vẫn ước tính,16bó nguồn cần xác minh khối bao; chưa nghiệm thu dùng thực.

Owner phản hồi chưa thấy hàng trên tàu và yêu cầu làm tròn khối lượng, rồi chọn **bắt đầu xếp thử tự động M2b** ngày01-11-2026. [SPEC M2b](../specs/SCST_M2B.md) và [review](../reviews/SCST_M2B_REVIEW.md) xác minh heuristic một lớp, preview/apply rõ, hàng hiện trên thân tàu sau áp dụng, mọi bó còn lại có lý do, lưu/mở giữ placement. Displaytấn tối đa2số lẻ; tính/lưu không làm tròn.98backend/22browser,8941assertions độc lập và restart đạt.

Bước tiếp theo là checkpoint owner và **SPEC M2c** cho chỉnh/so sánh đầy đủ; chưa dispatch tự động. M2d báo cáo và M3 nhiều tầng/case thực giữ thứ tự. M2b không chứng minh tối ưu, cảlist vừa hầm hoặc điều kiện vận hành; professionalverification và dữ liệu đo thực vẫn riêng.

## Rủi ro chính

| Rủi ro | Cách xử lý |
|---|---|
| Hầm BOX bỏ mất không gian cần thiết của hầm thật | Kiểm bằng số đo hầm thật ngay khi có; nếu không phù hợp thì đổi contract hình học trước khi làm tiếp phần xếp |
| Không có dữ liệu thật đúng lúc | Làm tiếp M2b–M2d bằng dữ liệu demo có nhãn theo điều kiện ở dòng M2; kết quả ghi "chưa xác minh hình học", chưa dùng cho hầm thật và chưa nghiệm thu M2 cho hầm thật |
| Heuristic cho phương án nhìn hợp lý nhưng vi phạm điều kiện chưa được đưa vào kiểm tra | Bộ kiểm tra độc lập với bộ xếp; báo cáo ghi rõ điều kiện nào chưa kiểm |
| Phải làm lại khi lên nhiều tầng | Contract chừa trường z, lớp và quan hệ đỡ từ M1; logic nhiều tầng làm ở M3 |
| License CVF (CC BY-NC-ND 4.0 tại revision đã đọc) hạn chế tích hợp/phân phối | Không đưa CVF vào app trước M4; xử lý điều kiện license trước khi tích hợp ở M4 hoặc đóng gói ở M5 |

## Treeview kiến trúc dự kiến

Một repository, một tool chạy local; frontend và backend tách trách nhiệm qua API. M1, lớp VINAFCO268 và M2a đã có code/kiểm kỹ thuật; nghiệm thu nghiệp vụ tách riêng. Cây dưới gồm cả tương lai. Import/storage nằm trong `adapters/`; SQLite tạo tại `runtime-data/` ngoài Git. `domain/planner/` đã có heuristic một lớp M2b.

```text
Cargo_Stowage_Tool/
├── apps/frontend/src/              # giao diện React/TypeScript dự kiến
│   ├── features/                   # nhập hàng/hầm, phương án, chỉnh/so sánh [M1–M3]
│   ├── viewer-3d/                  # hầm/hàng theo backend [M1]; lớp tàu minh họa [M2c], hiệu chỉnh [M3]
│   └── api/                        # giao tiếp backend theo contract [M1+]
├── services/backend/app/
│   ├── api/                        # nhận thao tác, trả dữ liệu/kết quả kiểm [M1+]
│   ├── domain/
│   │   ├── model/                  # hàng, hầm, phương án, đơn vị tính [M1+]
│   │   ├── geometry/               # biên, va chạm, tọa độ [M1+]
│   │   ├── rules/                  # bộ kiểm tra, độc lập với bộ xếp [M1+]
│   │   └── planner/                # bộ xếp tạo đề xuất [M2–M3]
│   └── adapters/                   # lưu local, import/export [M2]; AI/CVF nếu cần [M4]
├── contracts/                      # dữ liệu/API, đơn vị tính và phiên bản [M1+]
├── tests/                          # fixture giả lập; case thực đã được phép/ẩn danh từ M3
├── tooling/                        # chạy local [M1]; đóng gói/cài đặt [M5]
├── runtime-data/                   # dữ liệu local, không commit Git [M2+]
├── docs/                           # kế hoạch, quyết định, hướng dẫn và bằng chứng
├── archive/                        # lịch sử; bản thử M1 đang tạm dừng
├── scripts/                        # công cụ quản lý CVF hiện có
└── .cvf/ + CVF_SESSION/             # cấu hình, trạng thái và bàn giao CVF hiện có
```

**Luồng trách nhiệm:** giao diện → API → nghiệp vụ/kiểm tra → adapter lưu trữ hoặc xuất. `planner` tạo đề xuất rồi `rules` kiểm lại; bảng, viewer và báo cáo cùng đọc một phương án có ID/phiên bản. Frontend không ghi trực tiếp database; AI tùy chọn cũng đi qua API và quyền backend.

**Stack hiện có ở M1:** React/TypeScript; Python/FastAPI; Three.js. SQLite đã dùng cho snapshot local từ M2a; thư viện bổ sung được chốt khi tới SPEC tương ứng. Domain tách khỏi giao diện, database và provider để có thể kiểm độc lập.

## Nguyên tắc xuyên suốt

- Mỗi bó có ID, kích thước và khối lượng rõ; không chia tổng manifest để suy ra khối lượng từng bó. Đơn vị đo nhất quán, không làm tròn xuống để lọt giới hạn.
- Giới hạn tải tách rõ: giới hạn theo giấy chứng nhận, giới hạn theo chuyến và hàng đã có trên tàu; không dùng trọng tải toàn phần thay cho lượng hàng. Phân biệt required/optional/excluded và đối soát toàn bộ manifest. Hàng chưa xếp hoặc chưa hỗ trợ vẫn hiện cùng lý do.
- Backend kiểm quy tắc trong phạm vi hỗ trợ: tải, biên, va chạm và điều kiện kê/chồng khi được bổ sung. Mọi chỉnh sửa cần kiểm lại, giữ bản trước.
- Trạng thái phương án dùng nhãn không gây hiểu lầm như DRAFT, GEOMETRY_FEASIBLE, RULES_CHECKED, STALE; không dùng "SAFE" hay "đã duyệt" chỉ vì bộ xếp báo khả thi.
- Dữ liệu demo có nhãn; thiếu dữ liệu hoặc chưa kiểm được phải hiện rõ. Case thực chỉ dùng khi được phép, ưu tiên bản ẩn danh; chứng từ gốc nhạy cảm lưu ngoài Git. Phương án là kết quả tính sơ bộ; người dùng quyết định, AI không tự xác nhận thông số hoặc phê duyệt.

## Cách đi tiếp theo CVF

**M0 đã xong.** Owner thống nhất ngày 31-10-2026 ba điểm: (1) local-first, một người dùng và ranh giới nghiệp vụ; (2) đầu ra/thứ tự M1–M5, AI tùy chọn; (3) một repository với FE/BE và các lớp trách nhiệm như cây dự kiến.

**Hiện tại: REVIEW kỹ thuật M2c đã đạt**, với giữ gốc, so sánh đầy đủ và khôi phục theo [SPEC M2c](../specs/SCST_M2C.md), [review](../reviews/SCST_M2C_REVIEW.md). Các mốc trước có review riêng; nghiệm thu nghiệp vụ tách riêng. Phần kế tiếp là M2d xuất PDF/XLSX, chỉ chi tiết hóa SPEC/WORK_ORDER khi được chọn; chưa tự mở BUILD. Endpoint, schema và danh sách file nằm trong SPEC của từng phần.

Bản M1 trong archive là nguồn tham khảo; kết quả test cũ không tự trở thành nghiệm thu cho hướng mới.

## Nguồn và trạng thái

- [Roadmap ban đầu — Tool First](../project/SCST_Roadmap_Ban_Dau_Tool_First.md): giữ nguyên mục tiêu và mốc; thứ tự triển khai tuân theo chỉ đạo của owner về việc thống nhất hướng trước.
- [Kiến trúc tham khảo v0.1](../reference/design-v0.1/07_ARCHITECTURE_TREEVIEW.md), [roadmap tham khảo v0.1](../reference/design-v0.1/06_ROADMAP_GATED.md) và [phạm vi v0.1](../reference/design-v0.1/01_SCOPE_CONTRACT.md): rút gọn trách nhiệm module và nhãn trạng thái, chưa nhận toàn bộ chi tiết làm thiết kế đã chốt.
- [Mô hình nghiệp vụ](../reference/domain/02_OPERATIONAL_MODEL.md): căn cứ cho rủi ro hầm BOX và nhu cầu nhiều tầng.
- [Trạng thái project](../project/PROJECT_STATUS.md): M2c đạt kiểm kỹ thuật; chưa có nghiệm thu nghiệp vụ hoặc vận hành, không có work order app đang thi công.

Owner đã thống nhất hướng; M1 đạt kiểm kỹ thuật, chưa được nghiệm thu nghiệp vụ. Bảng mốc ở trên được đăng ký trong `docs/milestone-coverage-authority.json` (mã `SCST-ROADMAP`); tiêu chí đo được của M1 nằm trong [SPEC M1 v0.2](../specs/SCST_M1.md), mã `SCST-M1`. Bản v0.3 bổ sung mục hình tàu và đồng bộ trạng thái; giữ nguyên mục bảng mốc đã đăng ký, SPEC và snapshot dispatch M1.

<details>
<summary>Metadata CVF lịch sử cho lượt đối chiếu v0.2</summary>

Bản đồ tiêu chí `docs/milestone-coverage-authority.json` đã có từ 31-10-2026, trỏ mã `SCST-ROADMAP` tới mục "Phạm vi và đầu ra từng mốc". Trước khi sửa mục đó, liệt kê các work order đang trỏ tới; work order đã đóng được chuyển sang bản chụp lúc dispatch (ví dụ `docs/roadmaps/snapshots/SCST_ROADMAP_v0.2_at_f2b688e.md`, mã `SCST-ROADMAP-AT-F2B688E`), giữ nguyên hash; work order mới tính hash theo bản hiện hành. Metadata dưới đây chỉ ghi lượt soạn và sửa roadmap, không cấp quyền BUILD.

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": null,
  "milestone": {
    "id": "SCST-PLAN-1",
    "consumer": "Owner SCST",
    "outcome": "Compact roadmap, architecture tree, scope and deliverables; owner agreed direction on 31-10-2026 and revision v0.2 applies the agreed review points",
    "checkpoint": {"trigger": "Revision v0.2 delivered after owner agreement", "owner": "Project owner", "decision": "Proceed to SPEC M1 as the next slice, request further adjustment, or hold"}
  },
  "phase": "PLAN",
  "action": {
    "kind": "VERIFY", "selected": [], "owner": "Local agent / SPEC_AUTHOR",
    "output": "docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md v0.2 and synchronized navigation/continuity",
    "budgetMinutes": 30,
    "question": "Does revision v0.2 apply the owner-agreed review points (M2 slicing, multi-layer-ready contract, early real-data probe, risk section, status labels, load limits, rules/planner split) without changing agreed scope?",
    "sourceBoundary": "Draft v0.1, the review agreed by the owner, original roadmap, retained v0.1 references and domain model; no app execution",
    "stop": "Revision v0.2 and document checks, or budget exhausted; no automatic SPEC or implementation",
    "next": "Prepare SPEC M1 as the next slice; BUILD requires a separately authorized work order"
  },
  "rows": [],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING", "trancheSummary": "Owner agreed overall direction; revision v0.2 applied with follow-up review clarifications; milestone table registered as SCST-ROADMAP; M1 measurable criteria pending SPEC M1", "trancheEvidence": [],
    "product": "PENDING", "productSummary": "No accepted application capability", "acceptance": [], "owner": "Project owner"
  }
}
```

</details>
