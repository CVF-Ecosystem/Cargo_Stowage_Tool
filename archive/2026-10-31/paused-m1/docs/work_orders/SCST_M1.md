# SCST M1 — Build packet

Status: HOLD_BY_OPERATOR
dispatchKind: INITIAL

Owner: local-development
Risk: R1

## Authority, scope, cost

Owner yêu cầu dựng project theo roadmap tool-first ngày 31-10-2026. SPEC: docs/specs/SCST_M1.md. Chỉ tạo app demo và bằng chứng M1; không sửa CVF core, gate bundle hoặc baseline review. Được cài dependency phát triển từ registry công khai; không dùng provider/credential, deploy, dữ liệu thật hay dịch vụ ngoài trong runtime.

Đường dẫn: apps/frontend/**, services/backend/**, contracts/**, tests/**, tooling/**, docs/specs/SCST_M1.md, docs/work_orders/SCST_M1.md, docs/reviews/SCST_M1*, docs/APP_GUIDE.md, docs/catalog/**, docs/INDEX.md, docs/milestone-coverage-authority.json, CVF_SESSION/**, CVF_SESSION_MEMORY.md, IMPLEMENTATION_STATUS.json, .gitignore, Start-SCST.cmd, requirements-dev.txt, pytest.ini. Commit owner: local commit-steward; không push.

Vai trò tuần tự do cùng local agent giữ cho R1: ORCHESTRATOR → SPEC_AUTHOR → WORK_ORDER_AUTHOR → IMPLEMENTATION_WORKER → REVIEWER → COMMIT_STEWARD → SESSION_SYNC_STEWARD. Không giả nhận review độc lập. Chuyển vai trò và kết quả ghi handoff. Bootstrap/doctor đã PASS; không suy ra live governance proof.

Ngân sách phần triển khai + kiểm: 120 phút; support paperwork tối đa thêm 15 phút. Tái sử dụng review/checksum cũ, không chạy lại toàn bộ 86 reference checks để đóng M1. Chi phí provider không đo được, không bịa số tiền. Dừng nếu phải đổi phạm vi/rủi ro, cần dữ liệu thật/credential hoặc repair vòng 3 không có nguyên nhân mới. Phần còn lại M2–M5 thuộc owner/local-development ở roadmap gốc. Sau M1, ưu tiên lát cắt M2 nhập tay + lưu/mở; không mở trước khi có M1 runnable và bằng chứng.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/specs/SCST_M1.md; docs/work_orders/SCST_M1.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M1.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_V1_2026-10-31.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; tests; tooling; contracts | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | contracts; tests; docs/reviews | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M1.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | apps/frontend; services/backend; tests; docs/reviews | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
| reviewer_fast | REVIEW | reviewer | REVIEW | apps/frontend; services/backend; tests; docs/reviews | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | worker_return_fast |
| pre_commit | PRE_MATERIAL_COMMIT | commit-steward | PRE_MATERIAL_COMMIT | docs; CVF_SESSION; IMPLEMENTATION_STATUS.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | reviewer_fast |
| terminal_completion_review | POST_MATERIAL | reviewer | REVIEW | docs/reviews; docs/work_orders | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | pre_commit |
| continuity | CONTINUITY_COMMIT | session-sync-steward | CONTINUITY_COMMIT | CVF_SESSION; CVF_SESSION_MEMORY.md; IMPLEMENTATION_STATUS.json; docs/catalog | BOUNDED_PATH_FAMILIES | session-sync-steward | CONTINUITY_COMMIT | terminal_completion_review |
| committed_range_closure | POST_MATERIAL_CLOSURE | commit-steward | POST_MATERIAL_CLOSURE | docs/reviews; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | CORRECTIVE_MATERIAL_COMMIT | continuity |

## Coverage

Coverage machine block is maintained below; acceptance authority is the six M1 criteria, not the entire roadmap.

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/specs/SCST_M1.md",
    "heading": "## M1 acceptance",
    "sha256": "6e10e1f94cf8e078b80f49d7bc5bd3f0191d4fdef22e4bc0e580a2a113128707"
  },
  "milestone": {
    "id": "M1",
    "consumer": "Owner using synthetic local demo",
    "outcome": "API to table and 3D with editable basic checks",
    "checkpoint": {
      "trigger": "Runnable tested demo delivered",
      "owner": "project-owner",
      "decision": "Review usefulness and select M2 slice"
    }
  },
  "phase": "DISPATCH",
  "action": {
    "kind": "IMPLEMENT",
    "selected": [
      "M1-01",
      "M1-02",
      "M1-03",
      "M1-04",
      "M1-05",
      "M1-06"
    ],
    "owner": "local-development",
    "output": "Local M1 app and evidence",
    "budgetMinutes": 120,
    "stop": "Scope/risk expansion or third repair without new cause",
    "next": "Review internal readiness then owner feedback"
  },
  "rows": [
    {
      "id": "M1-01",
      "state": "NOT_STARTED",
      "gap": "Implement and verify",
      "owner": "local-development",
      "destination": "docs/reviews/SCST_M1_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M1-02",
      "state": "NOT_STARTED",
      "gap": "Implement and verify",
      "owner": "local-development",
      "destination": "docs/reviews/SCST_M1_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M1-03",
      "state": "NOT_STARTED",
      "gap": "Implement and verify",
      "owner": "local-development",
      "destination": "docs/reviews/SCST_M1_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M1-04",
      "state": "NOT_STARTED",
      "gap": "Implement and verify",
      "owner": "local-development",
      "destination": "docs/reviews/SCST_M1_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M1-05",
      "state": "NOT_STARTED",
      "gap": "Implement and verify",
      "owner": "local-development",
      "destination": "docs/reviews/SCST_M1_REVIEW.md",
      "evidence": []
    },
    {
      "id": "M1-06",
      "state": "NOT_STARTED",
      "gap": "Implement and verify",
      "owner": "local-development",
      "destination": "docs/reviews/SCST_M1_REVIEW.md",
      "evidence": []
    }
  ],
  "supportingWork": [
    {
      "criterionIds": [
        "M1-06"
      ],
      "reason": "Required CVF dispatch and continuity",
      "budgetMinutes": 15,
      "stop": "No more governance expansion for this demo",
      "returnToProduct": "Build API and viewer"
    }
  ],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Authorized M1 build",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "M1 implementation not yet demonstrated; M2-M5 remain",
    "acceptance": [],
    "owner": "local-development"
  }
}
```

## Operator hold

31-10-2026: owner paused coding to discuss the final roadmap. This packet is not an execution grant while held. Existing implementation and tests do not constitute owner acceptance.
