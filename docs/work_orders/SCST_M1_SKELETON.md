# SCST M1 — Khung thư mục theo treeview

Status: CLOSED (self-reviewed R1, owner checkpoint pending)
dispatchKind: INITIAL

Owner: local-development
Risk: R1

## Authority, scope, cost

31-10-2026: owner chọn phương án 1, tạo ngay khung thư mục M1 theo treeview của [roadmap v0.2](../roadmaps/SCST_ROADMAP_TONG_THE_DE_XUAT.md) đã thống nhất (quyết định SCST-D001). Đây là bước đầu của M1, làm trước SPEC M1.

**Được làm:** tạo các thư mục M1 dưới đây, mỗi thư mục có một `README.md` ngắn bằng tiếng Việt ghi trách nhiệm, mốc sử dụng và điều không thuộc thư mục đó; cập nhật cây "Cấu trúc hiện tại" trong `README.md` root.

| Thư mục | Trách nhiệm |
|---|---|
| `apps/frontend/src/features/` | Màn hình nhập hàng/hầm, phương án, chỉnh/so sánh |
| `apps/frontend/src/viewer-3d/` | Hiển thị 3D từ cùng dữ liệu phương án; không tự đánh giá an toàn |
| `apps/frontend/src/api/` | Giao tiếp backend theo contract |
| `services/backend/app/api/` | Nhận thao tác, trả dữ liệu và kết quả kiểm |
| `services/backend/app/domain/model/` | Hàng, hầm, phương án, đơn vị tính |
| `services/backend/app/domain/geometry/` | Biên, va chạm, tọa độ |
| `services/backend/app/domain/rules/` | Bộ kiểm tra, độc lập với bộ xếp |
| `services/backend/app/adapters/` | Lưu local, import/export (dùng từ M2) |
| `contracts/` | Dữ liệu/API, đơn vị tính, phiên bản |
| `tests/` | Kiểm nghiệp vụ, tích hợp, luồng dùng |
| `tooling/` | Lệnh chạy local |

**Không làm:** không viết code, không tạo `package.json`, `requirements`, launcher, schema hay test; không tạo `domain/planner/` (M2), `runtime-data/` (M2) hay phần đóng gói (M5); không khôi phục file từ `archive/`; không sửa CVF core, gate bundle, roadmap hay tài liệu tham khảo. Không dùng provider, credential, mạng hay dữ liệu thật.

**Đường dẫn được sửa:** `apps/frontend/src/**/README.md`, `services/backend/app/**/README.md`, `contracts/README.md`, `tests/README.md`, `tooling/README.md`, `README.md`, `docs/work_orders/SCST_M1_SKELETON.md`, `docs/milestone-coverage-authority.json`, `docs/catalog/**`, `docs/INDEX.md`, `docs/project/PROJECT_STATUS.md`, `CVF_SESSION/**`, `CVF_SESSION_MEMORY.md`, `IMPLEMENTATION_STATUS.json`. Commit owner: local commit-steward; không push.

**Vai trò** (cùng một local agent, R1): ORCHESTRATOR → WORK_ORDER_AUTHOR → IMPLEMENTATION_WORKER → REVIEWER → COMMIT_STEWARD → SESSION_SYNC_STEWARD. Không nhận là review độc lập. Chuyển vai trò ghi trong handoff.

**Ngân sách:** 30 phút gồm cả kiểm. Dừng nếu phải đổi phạm vi/rủi ro hoặc đến lần sửa thứ ba không có nguyên nhân mới.

**Tiêu chí đạt của lát cắt này:**

1. Đủ 11 thư mục trên, mỗi thư mục có `README.md`; không có file nào khác trong cây app.
2. Không có thư mục ngoài danh sách (`planner/`, `runtime-data/`, phần đóng gói).
3. Cây trong `README.md` root khớp với thư mục thật.
4. Catalog/INDEX hợp lệ; gate pre-dispatch, worker-return, reviewer-fast, pre-commit đạt.

Lát cắt này không hoàn thành M1. Hành vi, dữ liệu và tiêu chí đo được của M1 thuộc SPEC M1.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M1_SKELETON.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M1_SKELETON.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_V1_2026-10-31.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M1_SKELETON.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
| reviewer_fast | REVIEW | reviewer | REVIEW | apps/frontend; services/backend; contracts; tests; tooling; README.md | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | worker_return_fast |
| pre_commit | PRE_MATERIAL_COMMIT | commit-steward | PRE_MATERIAL_COMMIT | docs; CVF_SESSION; IMPLEMENTATION_STATUS.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | reviewer_fast |
| terminal_completion_review | POST_MATERIAL | reviewer | REVIEW | docs/work_orders | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | pre_commit |
| continuity | CONTINUITY_COMMIT | session-sync-steward | CONTINUITY_COMMIT | CVF_SESSION; CVF_SESSION_MEMORY.md; IMPLEMENTATION_STATUS.json; docs/catalog | BOUNDED_PATH_FAMILIES | session-sync-steward | CONTINUITY_COMMIT | terminal_completion_review |
| committed_range_closure | POST_MATERIAL_CLOSURE | commit-steward | POST_MATERIAL_CLOSURE | docs/work_orders; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | CORRECTIVE_MATERIAL_COMMIT | continuity |

## Coverage

Nguồn tiêu chí là bảng mốc của roadmap đã thống nhất. Lát cắt này chỉ chọn M1 và chỉ dựng khung; M1 chưa đạt sau lát cắt này.

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/roadmaps/snapshots/SCST_ROADMAP_v0.2_at_f2b688e.md",
    "heading": "## Phạm vi và đầu ra từng mốc",
    "sha256": "560ba09fe9210eb31ab58f858f89c4a007a397014507192fc5d1ae22f35794bb"
  },
  "milestone": {
    "id": "SCST-ROADMAP-AT-F2B688E",
    "consumer": "Owner SCST",
    "outcome": "M1 folder skeleton matching the agreed treeview, one README per folder, no application code",
    "checkpoint": {
      "trigger": "Skeleton created and checked",
      "owner": "Project owner",
      "decision": "Accept the skeleton and proceed to SPEC M1, or request adjustment"
    }
  },
  "phase": "DISPATCH",
  "action": {
    "kind": "IMPLEMENT",
    "selected": ["M1"],
    "owner": "local-development",
    "output": "M1 folder skeleton with README files and updated root README tree",
    "budgetMinutes": 30,
    "stop": "Scope or risk change, or third repair without a new cause",
    "next": "Owner reviews the skeleton; then SPEC M1"
  },
  "rows": [
    {
      "id": "M0",
      "state": "VERIFIED",
      "gap": "None; owner agreed overall direction",
      "owner": "Project owner",
      "destination": "docs/decisions/SCST_D001_THONG_NHAT_HUONG_M0_2026-10-31.md",
      "evidence": [
        {"path": "docs/decisions/SCST_D001_THONG_NHAT_HUONG_M0_2026-10-31.md", "sha256": "318f8c82ca527178492e96c521d4daaeb3d9226c7e6cad2e972842a342fc71c3"}
      ]
    },
    {
      "id": "M1",
      "state": "NOT_STARTED",
      "gap": "This slice creates only the folder skeleton; M1 behaviour, data and measurable criteria belong to SPEC M1",
      "owner": "local-development",
      "destination": "docs/specs/ (SPEC M1)",
      "evidence": []
    },
    {
      "id": "M2",
      "state": "NOT_STARTED",
      "gap": "Starts after M1 is accepted",
      "owner": "local-development",
      "destination": "Future M2a-M2d SPECs",
      "evidence": []
    },
    {
      "id": "M3",
      "state": "NOT_STARTED",
      "gap": "Needs real cases, hold measurements and stacking profiles",
      "owner": "local-development",
      "destination": "Future M3 SPEC",
      "evidence": []
    },
    {
      "id": "M4",
      "state": "NOT_STARTED",
      "gap": "Optional; owner must confirm a concrete AI task first",
      "owner": "Project owner",
      "destination": "Owner decision before any M4 SPEC",
      "evidence": []
    },
    {
      "id": "M5",
      "state": "NOT_STARTED",
      "gap": "Starts after the tool has been used on real cases in M3",
      "owner": "local-development",
      "destination": "Future M5 SPEC",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Skeleton created and self-reviewed (R1); owner checkpoint pending; M1 not achieved",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "No accepted application capability; M1-M5 remain",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

## Kết quả và review

31-10-2026, cùng một local agent (không phải review độc lập, mức R1):

- Dispatch: `f2b688e`, sửa continuity `54f5082` trước BUILD.
- IMPLEMENTATION_WORKER tạo 11 thư mục, mỗi thư mục một `README.md`, và cập nhật cây trong `README.md` root.
- REVIEWER kiểm bằng script:
  - tiêu chí 1: đủ 11 README, không có file khác;
  - tiêu chí 2: không có thư mục ngoài danh sách, `planner/` và `runtime-data/` không tồn tại;
  - tiêu chí 3: cây root khớp với thư mục thật, link không hỏng.
  
  Tất cả đạt. Reviewer sửa tại chỗ câu chữ README của `domain/rules` (không đổi phạm vi).
- Tiêu chí 4: catalog hợp lệ; worker-return, reviewer-fast và pre-commit đạt trước commit material.
- Không có code, dependency hay dữ liệu. M1 vẫn chưa đạt; bước tiếp theo là owner xem khung, rồi SPEC M1.

## Ghi chú sửa nguồn tiêu chí sau khi đóng

31-10-2026: roadmap hiện hành đổi mục bảng mốc ở commit `2f29a1a`, làm kiểm trực tiếp work order này báo `COV_AUTHORITY_STALE`. Bộ kiểm chỉ đọc file hiện tại và mỗi mã chỉ trỏ một file, nên không giữ được nguồn lúc dispatch nếu không sửa block. Đã sửa tối thiểu: `milestone.id` → `SCST-ROADMAP-AT-F2B688E`, `authority.path` → bản chụp `docs/roadmaps/snapshots/SCST_ROADMAP_v0.2_at_f2b688e.md` lấy từ commit dispatch `f2b688e`. **Hash nguồn giữ nguyên** (`560ba09f…`); rows, kết luận và phần còn lại không đổi. Mã `SCST-ROADMAP` vẫn trỏ roadmap hiện hành cho work order mới. Ghi nhận: [learning SCST-L001](../reviews/learnings/SCST_L001_CLOSED_PACKET_AUTHORITY_DRIFT.md).
