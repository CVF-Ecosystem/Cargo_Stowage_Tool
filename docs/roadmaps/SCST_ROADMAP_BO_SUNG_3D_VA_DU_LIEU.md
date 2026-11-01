# SCST — Roadmap bổ sung 3D và dữ liệu hàng

Status: ACTIVE

Ngày 01-11-2026 owner chốt **roadmap bổ sung trước khi triển khai**. Tài liệu này là kế hoạch,
không phải SPEC, WORK_ORDER hay quyền BUILD. Chỉ lập SPEC chi tiết cho SUP-01 khi được chọn;
SUP-02 và SUP-03 được mô tả ở mức kết quả, sẽ chốt contract và giới hạn khi đến lượt.

Hệ tọa độ VINAFCO hiện hành đã được kiểm trước khi lập kế hoạch: 6 điểm mốc và 12 trường hợp
hàng trong runtime; đây không phải lỗi mới cần sửa. Hai gói handoff có 23 file chung trùng byte;
gói mới chỉ bổ sung tài liệu audit (file cache Python không thuộc nguồn đã bỏ). Audit là nguồn tham khảo, không tự thay đổi quyền triển khai.

## Vị trí trong roadmap

Bổ sung **SUP-01 → SUP-02 → SUP-03 → kiểm tra tích hợp** sau M2c và sửa đơn vị hiển thị,
trước M2d xuất báo cáo. Sau đó tiếp tục M2d xuất PDF/XLSX → M3 case thực và nhiều tầng;
M4 AI là tùy chọn, M5 hoàn thiện vận hành. M0–M5 và điều kiện của chúng giữ nguyên theo
[roadmap tổng thể](SCST_ROADMAP_TONG_THE_DE_XUAT.md); tài liệu này bổ sung thứ tự, không sửa bảng cũ.

## Phạm vi và đầu ra

| ID | Phạm vi và đầu ra | Checkpoint, phụ thuộc và phần còn lại |
|---|---|---|
| SUP-01 | Viewer 3D thực dụng, dễ quan sát và mượt theo kết quả đo: giữ scene, GLB và camera khi cập nhật cùng tàu/hầm hoặc bật/tắt thân; thay tàu/profile thì cập nhật đúng đối tượng và căn khung có chủ đích; toàn cảnh vừa khung, nhìn trên/mạn và tập trung bó chọn; vật liệu/ghost giúp thấy hầm; chẩn đoán chi tiết chỉ bật khi cần. | Tái dùng viewer, Plan, GLB và fallback hiện có. Đo tải, thao tác, picking và tài nguyên trên cảnh điển hình và list nguồn, ghi thiết bị/trình duyệt; không đặt FPS tùy ý. Nhóm phát triển chứng minh bằng kiểm kỹ thuật và luồng dùng được trước checkpoint owner. |
| SUP-02 | Dữ liệu hàng phát triển theo thực tế và profile tàu/tọa độ: giữ nguồn bất biến, tạo revision làm việc có provenance; nhận cập nhật từ người dùng/nhà máy/khách hàng theo nhóm, bó hoặc lô; giữ ID và ghim revision trong phương án đã lưu. Phương án bị ảnh hưởng được đánh dấu cần kiểm lại. | Kế thừa Plan, registry, adapter nhập và SQLite; không cố định sản phẩm vào Baltimore 1.076 bó. Validation, giới hạn nhập, di trú và chính sách revision chốt trong SPEC riêng; AI hỗ trợ nhập chỉ tùy chọn. Profile lưu nguồn, GLB, hầm và phép đổi tọa độ có kiểm chứng. |
| SUP-03 | Biểu diễn khối bao, bó giản lược và bó/ống chi tiết là các cách nhìn cùng một thực thể; packing gắn nguồn và trạng thái theo nhóm hoặc bó. Khi đủ đầu vào, tự dựng chi tiết và kiểm số lượng, OD và kích thước. | Dựa trên SUP-02 để nhận dữ liệu và cập nhật sau này. Khi thiếu hoặc mâu thuẫn, giữ khối bao và cảnh báo có hướng xử lý cho nhóm/bó liên quan; không chặn toàn bộ dữ liệu. Chất lượng hiển thị không đổi khối lượng hay envelope nghiệp vụ. |

Nguồn bổ sung và tình trạng xác nhận được gắn theo thông tin/nhóm/bó, không dùng một cờ khóa
chi tiết cho toàn bộ mọi lô. AI có thể cảnh báo hoặc gợi ý dữ liệu; người dùng vẫn có thể nhập/nạp
trực tiếp và áp dụng bản cập nhật khi nhận thông tin, không phải chờ AI. Chỉ các phương án phụ thuộc
revision thay đổi mới cần đối chiếu và kiểm lại; bản đã lưu tiếp tục giữ revision cũ.

Mỗi checkpoint được kích hoạt khi đạt đầu ra hoặc gặp thay đổi phạm vi/rủi ro; nhóm phát triển
hoàn tất kiểm, sửa lỗi được giao và nêu phần chưa giao trước khi owner quyết định bước tiếp.
Hoàn tất một SUP không đồng nghĩa hoàn tất M2 hoặc nghiệm thu kinh doanh/vận hành.

## Nguyên tắc dữ liệu và hình học

- Phương án và nguồn là cơ sở cho bảng, kiểm tra, lưu/mở và 3D; mesh chỉ biểu diễn, không là
  nguồn duy nhất của ID, số lượng, khối lượng hoặc pose. Bật/tắt hiển thị không đổi số liệu.
- Dữ liệu Baltimore hiện dùng khối lượng tính từ **K × L** theo gram chính xác; tổng cột O
  là cơ sở đối chiếu, không mặc nhiên chuyển sang O/M theo audit. Các nguồn mới cần khai báo
  cơ sở riêng và provenance; không suy khối lượng bó bằng cách chia tổng manifest tùy ý.
- Giữ đơn vị nội bộ và độ chính xác hiện có; giao diện dùng kg/cm/m. Làm tròn hiển thị
  không đổi geometry, dữ liệu lưu hoặc dung sai kiểm. Khối bao từ list là dữ liệu tạm xác minh.
- GLB hiện ở mét, Y-up; adapter profile đưa về hệ hầm. Kiểm đổi trục, gốc, chiều và kích thước
  bằng điểm mốc và hàng thực trước/sau thay đổi; không xoay, scale hoặc center lại hai lần.
- Kích thước hầm và tuyến hình VINAFCO còn ước tính. Ba nhóm có 16 bó cần xác minh envelope;
  đây là cảnh báo của dữ liệu hiện tại, không phải giới hạn vĩnh viễn của sản phẩm.
- Cần kiểm lại được ghi trên bản làm việc phụ thuộc dữ liệu mới; nếu áp dụng cập nhật cho phương án
  đã lưu thì tạo bản kế tiếp và kiểm lại, giữ snapshot cũ bất biến.
- Không suy ra mớn, ổn định, sức bền, tải sàn hoặc packing đã xác nhận từ hình minh họa.
  Cập nhật dữ liệu mới phải giữ được lịch sử và tình trạng kiểm của từng phương án.

## Cây trách nhiệm dự kiến

```text
Frontend
├── Giao diện phương án và viewer 3D [đã có; mở rộng SUP-01, SUP-03]
└── Nhập/sửa, provenance và trạng thái cần kiểm lại [mở rộng SUP-02]
Backend
├── Domain hàng, Plan và rules [đã có; revision/packing mở rộng SUP-02/03]
├── Geometry và profile tàu/tọa độ [đã có nền; mở rộng SUP-02]
├── Adapter nguồn/import [đã có nền; nguồn mới theo SPEC SUP-02]
└── Lưu trữ snapshot [đã có; ghim revision và di trú theo SPEC SUP-02]
```

Đây là trách nhiệm logic, không ấn định file hay thư viện mới. Reuse API, bộ kiểm, lịch sử,
SQLite, viewer và profile hiện có; nhóm phát triển sở hữu thiết kế và bằng chứng của từng tranche.

## Ngoài phạm vi bắt buộc và phần chờ

Gizmo kéo hàng, góc xoay tự do, OBB, nhiều tầng, đổi engine, hậu kỳ nặng và mô hình từng ống
không phải điều kiện mặc định của SUP-01; lựa chọn sau theo nhu cầu, dữ liệu và SPEC liên quan.
M3 sở hữu nhiều tầng/case thực; kiểm tích hợp trước M2d không thay nghiệm thu M3. Đo hầm thật,
xác minh 16 envelope và chấp nhận nghiệp vụ/vận hành vẫn có chủ sở hữu và checkpoint riêng.

Tài liệu gốc để đối chiếu: [review VINAFCO](../reviews/SCST_VINAFCO268_REVIEW.md),
[review list ống](../reviews/SCST_PIPE_LIST_REVIEW.md), [review M2c](../reviews/SCST_M2C_REVIEW.md),
[review đơn vị hiển thị](../reviews/SCST_DISPLAY_UNITS_REVIEW.md) và
[trạng thái triển khai](../../IMPLEMENTATION_STATUS.json). Tài liệu audit mới là đầu vào tham khảo;
kiểm chứng độc lập được ghi trong [review roadmap](../reviews/SCST_3D_SUPPLEMENT_ROADMAP_REVIEW.md).

## Kiểm tra tích hợp trước M2d

Nhóm phát triển đối chiếu cùng một phương án qua bảng, viewer, kiểm tra và lưu/mở;
kiểm ID, revision, nguồn, vị trí, số lượng, khối lượng và cảnh báo còn nhất quán.
Kiểm các trường hợp cập nhật dữ liệu khiến phương án cũ cần kiểm lại, thiếu packing,
và chọn bó sau khi đổi cách hiển thị. Owner cung cấp dữ liệu đo/nguồn khi sẵn có;
nhóm phát triển chịu trách nhiệm xác minh kỹ thuật và công bố giới hạn còn lại.
Kết quả checkpoint là quyết định tiếp tục M2d hoặc ghi nhận phần chưa đạt có người phụ trách.

<details>
<summary>Coverage để tiếp quản — chưa cấp quyền thi công</summary>

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/roadmaps/SCST_ROADMAP_BO_SUNG_3D_VA_DU_LIEU.md",
    "heading": "## Phạm vi và đầu ra",
    "sha256": "e9517a91ecc81f871928614673e45151459173f7946bb5cffeae3a8e066cd987"
  },
  "milestone": {
    "id": "SCST-3D-SUPPLEMENT",
    "consumer": "Owner SCST",
    "outcome": "Readable smooth viewer, evolving cargo/profile data and data-driven detailed packing before M2d",
    "checkpoint": {
      "trigger": "Each SUP reaches its outcome or scope/source/risk boundary; integrated flow before M2d",
      "owner": "Development team for internal proof; project owner for business direction",
      "decision": "Review evidence and remaining owned work, select next bounded SPEC; no automatic BUILD"
    }
  },
  "phase": "PLAN",
  "action": {
    "kind": "PLAN",
    "selected": [],
    "owner": "Root orchestrator/reviewer with Terra document worker",
    "output": "docs/roadmaps/SCST_ROADMAP_BO_SUNG_3D_VA_DU_LIEU.md",
    "budgetMinutes": 45,
    "stop": "Supplemental roadmap reviewed and synchronized, or planning budget/scope boundary",
    "next": "Only SUP-01 may be detailed next in SPEC and then WORK_ORDER when requested; no implementation now"
  },
  "rows": [
    {
      "id": "SUP-01",
      "state": "NOT_STARTED",
      "gap": "Existing viewer requires persistent lifecycle, framing/presets, materials and measured diagnostics work; no supplemental implementation yet",
      "owner": "Root orchestrator, then implementation/review roles in future work order",
      "destination": "docs/specs/SCST_SUP_01.md",
      "evidence": []
    },
    {
      "id": "SUP-02",
      "state": "NOT_STARTED",
      "gap": "Working source revisions and generic vessel/profile contract require design and migration proof; current fixed registry is retained until then",
      "owner": "Root orchestrator, then implementation/review roles in future work order",
      "destination": "docs/specs/SCST_SUP_02.md",
      "evidence": []
    },
    {
      "id": "SUP-03",
      "state": "NOT_STARTED",
      "gap": "Detailed packing capability and per-bundle source/status consistency require their own contract and implementation; current boxes remain valid fallback",
      "owner": "Root orchestrator, then implementation/review roles in future work order",
      "destination": "docs/specs/SCST_SUP_03.md",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Roadmap direction finalized as documentation; implementation tranches not opened",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "Three SUP outcomes unimplemented; M2d/M3 and business/operational acceptance remain owned work",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

</details>
