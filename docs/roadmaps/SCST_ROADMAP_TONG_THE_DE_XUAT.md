# SCST — Roadmap tổng thể và kiến trúc dự kiến

Status: DRAFT

**Bản đề xuất v0.1 · 31-10-2026 · Chờ owner thống nhất hướng.** Chỉ chi tiết hóa phần sắp làm sau khi thống nhất bản này; chưa cấp quyền triển khai.

## Mục tiêu và phạm vi

Tạo tool local cho một người dùng chính: **nhập hàng + hầm → lập phương án sơ bộ → xem bảng/3D → chỉnh và kiểm lại → lưu, so sánh, xuất PDF/Excel**. Core chạy được khi tắt AI. Giao diện và tooltip tiếng Việt, ngày dd-mm-yyyy.

Bắt đầu bằng bó thép thanh/bó thép ống có kích thước bao rõ, giữ nguyên từng bó; hầm BOX trước. Mở rộng nhiều tầng, nhóm hàng khác nhau và hình học hầm theo case thực ở M3. Điều phối cảng, xe/cẩu, ERP/WMS, mô phỏng cơ học tổng quát và cloud nhiều người dùng nằm ngoài phạm vi khởi đầu.

**Luồng chính:** M0 → M1 → M2 → M3 → M5. **M4 là nhánh tùy chọn**, xem xét sau khi core có ích; không phải điều kiện để làm M5. Các mốc mô tả kết quả, chưa cam kết thời lượng.

## Phạm vi và đầu ra từng mốc

| Mốc | Phạm vi | Đầu ra / điều kiện chuyển mốc | Phụ thuộc và thông tin cần đúng lúc |
|---|---|---|---|
| M0 — Thống nhất hướng | Chốt mục tiêu, ranh giới, thứ tự mốc và kiến trúc tổng thể trong bản này | Có bản hướng được owner đồng ý và phần tiếp theo được chọn để viết chi tiết | Owner quyết định hướng; agent ghi lại điểm thống nhất. Đây là bước kế hoạch, chưa dựng app |
| M1 — Khung chạy được | FE/BE tối thiểu; hầm BOX và bó hàng synthetic; API nối bảng và 3D; thay một dữ liệu và kiểm cơ bản | Chạy local theo hướng dẫn; bảng/3D cùng unit ID, tọa độ và số liệu backend; thấy được một lỗi vượt tải hoặc vượt biên. Có bằng chứng chạy và giới hạn demo | Sau M0 mới viết SPEC/phạm vi thi công M1. Dùng dữ liệu demo có nhãn, chưa cần chuyến thật |
| M2 — Tool cơ bản dùng trọn luồng | Nhập tay, import theo mẫu; kiểm khối lượng/hình học; xếp sơ bộ bằng heuristic; hàng chưa xếp và lý do; chỉnh/kiểm lại; lưu/mở/so sánh; PDF/XLSX | Người dùng hoàn tất luồng nhập → gợi ý → xem/chỉnh → lưu/mở lại → xuất. Mọi đơn vị hàng được đối soát; bản trước khi sửa được giữ; dữ liệu bảng, 3D và báo cáo khớp nhau | Khung M1 đạt yêu cầu; lấy mẫu import khi làm importer. Chia M2 thành các phần nhỏ khi đến mốc, chưa đặc tả tất cả ngay |
| M3 — Hoàn thiện tool với case thực | Case đại diện; nhiều tầng, nhóm kích thước khác nhau; profile kê/chồng, geometry cần thiết; cải thiện thao tác | Có case thực được đối chiếu, phạm vi sử dụng đã xác nhận và phần chưa hỗ trợ nêu rõ; người dùng thực hiện được công việc đại diện | Cần manifest, số đo hầm và profile phù hợp cho từng cấu hình; owner bố trí người hiểu nghiệp vụ đối chiếu. Agent chịu trách nhiệm kiểm kỹ thuật trước |
| M4 — AI hỗ trợ, nếu có ích | Tác vụ cụ thể như trích xuất, hỏi bổ sung, giải thích hoặc đề xuất chỉnh; actions qua quyền backend và CVF | Giảm thao tác ở tác vụ đã chọn; người dùng xác nhận thay đổi; core vẫn chạy khi AI tắt. Có kiểm chứng tích hợp thật trong phạm vi được bật | Owner xác nhận nhu cầu/tác vụ trước; lúc đó mới chọn provider và cách tích hợp. Có thể hoãn hoặc bỏ nhánh này |
| M5 — Hoàn thiện để sử dụng ổn định | Bộ cài/khởi chạy, độ bền lưu trữ, backup/restore, hiệu năng; lịch sử/quyền/review theo nhu cầu đã xác nhận | Cài/chạy theo hướng dẫn, lưu dữ liệu bền, khôi phục được bản sao và vận hành ổn định trong phạm vi đã thử | Dựa trên tool đã được dùng thử ở M3; M4 không bắt buộc. Nhiều người dùng, cloud, tích hợp ngoài cần quyết định phạm vi riêng |

M1 chỉ chứng minh khung và luồng dữ liệu; **M3 mới xử lý nhu cầu thực tế nhiều tầng**. Lưu/mở và giữ bản trước đã thuộc M2; M5 hoàn thiện độ tin cậy khi vận hành. Chưa yêu cầu thuật toán chứng minh tối ưu toàn cục.

Mỗi mốc có một checkpoint khi đủ đầu ra hoặc phát hiện thay đổi ảnh hưởng phạm vi: agent cung cấp bản chạy/bằng chứng, kết quả kiểm và phần còn thiếu; owner quyết định tiếp tục, điều chỉnh hướng hoặc tạm dừng. Lỗi kỹ thuật trong phạm vi được giao do agent tự sửa và kiểm lại trước khi xin phản hồi nghiệp vụ.

## Treeview kiến trúc dự kiến

Một repository, một tool chạy local; frontend và backend tách trách nhiệm qua API. **Cây dưới đây là phương án, chưa phải các thư mục app đã được tạo.** Chỉ tạo phần cần dùng ở mốc đang triển khai.

```text
Cargo_Stowage_Tool/
├── apps/frontend/src/              # giao diện React/TypeScript dự kiến
│   ├── features/                   # nhập hàng/hầm, phương án, chỉnh/so sánh [M1–M3]
│   ├── viewer-3d/                  # hiển thị cùng dữ liệu phương án [M1+]
│   └── api/                        # giao tiếp backend theo contract [M1+]
├── services/backend/app/
│   ├── api/                        # nhận thao tác, trả dữ liệu/kết quả kiểm [M1+]
│   ├── domain/                     # mô hình, quy tắc, geometry, lập phương án [M1–M3]
│   └── adapters/                   # lưu local, import/export [M2]; AI/CVF nếu cần [M4]
├── contracts/                      # dữ liệu/API, đơn vị tính và phiên bản [M1+]
├── tests/                          # kiểm nghiệp vụ, tích hợp, luồng dùng theo từng mốc
├── tooling/                        # chạy local [M1]; đóng gói/cài đặt [M5]
├── runtime-data/                   # dữ liệu local, không commit Git [M2+]
├── docs/                           # kế hoạch, quyết định, hướng dẫn và bằng chứng
├── archive/                        # lịch sử; bản thử M1 đang tạm dừng
├── scripts/                        # công cụ quản lý CVF hiện có
└── .cvf/ + CVF_SESSION/             # cấu hình, trạng thái và bàn giao CVF hiện có
```

**Luồng trách nhiệm:** giao diện → API → nghiệp vụ/kiểm tra → adapter lưu trữ hoặc xuất. Bộ xếp tạo đề xuất rồi lớp kiểm tra kiểm lại; bảng, viewer và báo cáo cùng đọc một phương án có ID/phiên bản. Frontend không ghi trực tiếp database; AI tùy chọn cũng đi qua API và quyền backend.

**Stack đề xuất kế thừa tài liệu gốc:** React/TypeScript; Python/FastAPI; Three.js/R3F; SQLite khi cần lưu bền. Đây là lựa chọn sơ bộ, chưa chốt phiên bản hoặc thư viện phụ. Domain tách khỏi giao diện, database và provider để có thể kiểm độc lập.

## Nguyên tắc xuyên suốt

- Mỗi bó có ID, kích thước và khối lượng rõ; không chia tổng manifest để suy ra khối lượng từng bó. Đơn vị đo nhất quán, không làm tròn xuống để lọt giới hạn.
- Dùng đúng giới hạn hàng hóa; phân biệt required/optional/excluded và đối soát toàn bộ manifest. Hàng chưa xếp hoặc chưa hỗ trợ vẫn hiện cùng lý do.
- Backend kiểm quy tắc trong phạm vi hỗ trợ: tải, biên, va chạm và điều kiện kê/chồng khi được bổ sung. Mọi chỉnh sửa cần kiểm lại, giữ bản trước.
- Dữ liệu demo có nhãn; thiếu dữ liệu hoặc chưa kiểm được phải hiện rõ. Phương án là kết quả tính sơ bộ; người dùng quyết định, AI không tự xác nhận thông số hoặc phê duyệt.

## Cách đi tiếp theo CVF

**Hiện tại: DESIGN — trao đổi bản tổng thể này.** Sau khi thống nhất hướng, mới viết SPEC cho phần M1 sắp làm (hành vi, phạm vi, tiêu chí đạt), rồi WORK_ORDER giới hạn việc được thi công. BUILD chỉ bắt đầu khi được cho tiếp tục; agent kiểm và REVIEW kết quả trước khi bàn giao, FREEZE phần đã được chấp nhận. Lặp lại với phần kế tiếp, giữ những mốc xa ở mức bảng phía trên.

Ba điểm cần thống nhất trong bản tổng thể: (1) local-first, một người dùng và ranh giới nghiệp vụ; (2) đầu ra/thứ tự M1–M5, AI tùy chọn; (3) một repository với FE/BE và các lớp trách nhiệm như cây dự kiến. Chưa cần chốt endpoint, schema chi tiết, thuật toán cụ thể hay danh sách file triển khai.

Bản M1 trong archive là nguồn tham khảo. Sau khi có SPEC M1 được thống nhất mới đánh giá phần nào có thể tái sử dụng; kết quả test cũ không tự trở thành nghiệm thu cho hướng mới.

## Nguồn và trạng thái

- [Roadmap ban đầu — Tool First](../project/SCST_Roadmap_Ban_Dau_Tool_First.md): giữ nguyên mục tiêu và mốc; thứ tự triển khai tuân theo chỉ đạo mới của owner về việc thống nhất hướng trước.
- [Kiến trúc tham khảo v0.1](../reference/design-v0.1/07_ARCHITECTURE_TREEVIEW.md) và [roadmap tham khảo v0.1](../reference/design-v0.1/06_ROADMAP_GATED.md): rút gọn trách nhiệm module, chưa nhận toàn bộ chi tiết làm thiết kế đã chốt.
- [Trạng thái project](../project/PROJECT_STATUS.md): không có capability app đã được owner chấp nhận hoặc work order app đang hoạt động.

Các mốc/tiêu chí phía trên còn là đề xuất. Chỉ đăng ký nguồn tiêu chí được duyệt và coverage thực thi sau khi owner thống nhất; metadata dưới đây giới hạn lượt đối chiếu nguồn/soạn đề xuất, không cấp quyền BUILD. Trách nhiệm phần còn lại: owner quyết định M0; agent chuẩn bị từng phần M1–M5 khi được giao, lấy dữ liệu/phản hồi tại checkpoint tương ứng.

<details>
<summary>Metadata CVF cho lượt đối chiếu và đề xuất</summary>

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": null,
  "milestone": {
    "id": "SCST-PLAN-1",
    "consumer": "Owner SCST",
    "outcome": "Compact proposed roadmap, architecture tree, scope and deliverables for owner discussion",
    "checkpoint": {"trigger": "Proposal delivered or verification budget exhausted", "owner": "Project owner", "decision": "Agree direction, request adjustments or hold; detail only the next slice after agreement"}
  },
  "phase": "PLAN",
  "action": {
    "kind": "VERIFY", "selected": [], "owner": "Local agent / SPEC_AUTHOR",
    "output": "docs/roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md and synchronized navigation/continuity",
    "budgetMinutes": 30,
    "question": "Which compact milestones and module responsibilities preserve tool-first intent under the owner's planning-only instruction?",
    "sourceBoundary": "Original roadmap, retained v0.1 architecture and roadmap, current project state and latest owner instruction; no app execution",
    "stop": "One source-aligned proposal and document checks, or budget exhausted; no automatic implementation or additional research tranche",
    "next": "Owner discusses overall direction; only then detail the next authorized slice"
  },
  "rows": [],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING", "trancheSummary": "Proposal available for discussion; agreed scope and milestone admission remain pending", "trancheEvidence": [],
    "product": "PENDING", "productSummary": "Application work paused; no accepted application capability", "acceptance": [], "owner": "Project owner"
  }
}
```

</details>
