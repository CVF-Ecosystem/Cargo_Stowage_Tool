# SCST M1 — Chuyển có chọn lọc và hoàn thiện theo SPEC v0.2

Status: CLOSED
dispatchKind: INITIAL

Owner: project-orchestrator
Risk: R2

## Authority, outcome and scope

Authority: [SCST-D002](../decisions/SCST_D002_M1_REUSE_EXECUTION.md), owner chỉ đạo tiếp tục bằng worker Terra 6.1 High, root orchestrator/reviewer; Sol-Medium khi cần xử lý phần khó cụ thể. Phạm vi: [SPEC M1 v0.2](../specs/SCST_M1.md), D1–D7 và toàn bộ M1-01…M1-09. Nguồn chọn lọc: [assessment](../reviews/SCST_M1_REUSE_ASSESSMENT_AND_PROPOSAL.md), bảng nguồn/đích được đưa vào Phụ lục SPEC.

Kết quả: một demo synthetic chạy local, backend authoritative, bảng/3D/2D cùng phương án; limits và states đúng SPEC; sửa/STALE/kiểm lại/undo không mất bản đã kiểm; bằng chứng kiểm đủ 9 tiêu chí. Không làm M2, không dùng kết quả demo cho nghiệp vụ thật.

Source pin: `archive/2026-10-31/paused-m1/` tại tree `e4004e274fc28aa143ce0e300b6c060d1cb1e5a0`, 50 file giữ nguyên bytes. Chỉ sao chép thành phần được chọn, sửa trên cây mới. Không nạp source hoặc dependency từ archive trong app runtime. `.cvf/runtime/paused-m1-local/` không dùng làm môi trường thực thi mới.

## Allowed paths, effects and ownership

- Worker được sửa: `apps/frontend/**`, `services/backend/**`, `contracts/**`, `tests/**`, `tooling/**`, `Start-SCST.cmd`, `requirements-dev.txt`, `requirements-lock.txt`, `pytest.ini`, `docs/APP_GUIDE.md`, `docs/reviews/SCST_M1_WORKER_RETURN.md`, `docs/reviews/SCST_M1_EVIDENCE/**`. README trách nhiệm giữ hoặc cập nhật theo source thật. Không dựng `domain/planner/`, runtime-data hoặc mã persistence.
- Local generated artifacts được phép: `.venv/`, node_modules, frontend/dist, browser traces/reports và `.cvf/runtime/m1-*` cho log tạm. Không commit dependency/build cache hoặc bí mật. Cài package công khai bằng pip/npm và browser test là được phép; AI/provider API, credentials, tài liệu thật, push/publish/deploy không được phép.
- Worker không sửa SPEC, roadmap, registry, work order, continuity, catalog, .cvf policy/gate bundle hoặc core; không commit. Nếu contract cần thay yêu cầu, báo root trước. Root giữ hồ sơ dispatch/review/closure và local commit.
- Không sửa `archive/**`, các snapshot/hồ sơ cũ và CVF core. Root xác minh lại blob identity của archive khi review.

Vai trò: root ORCHESTRATOR/WORK_ORDER_AUTHOR → Terra IMPLEMENTATION_WORKER → root REVIEWER (khác worker hiện tại) → root COMMIT_STEWARD/SESSION_SYNC_STEWARD. Root đã viết bản thử archive, công khai điều này; review tập trung bản chuyển/sửa và chứng cứ mới. Khi cần Sol hỗ trợ, root xác định việc cụ thể/phạm vi riêng, tránh hai worker sửa cùng file.

## Implementation order and verification

1. Model/geometry/rules + synthetic fixture + API: giữ oracle hình học/integer, thêm D2/D3/D4, không triển khai nhiều tầng. Giữ integer/extra forbid/ID constraints; onboard=0 khác mass/limits dương. API invalid structure 422, invalid layout trả evaluation để sửa.
2. Backend tests và regenerate OpenAPI/types: chứng minh D2 miền/trần/quan hệ, onboard>0 budget, 1g/1mm, overlap/chạm mặt, yaw, D3 từng trường, D4 ưu tiên và không mutation. Sinh lần hai không diff. Trần tổng tối đa 200 × 10^12 g vẫn an toàn JS.
3. FE theo features/api/viewer; chuyển helpers chính xác, giữ projection, fallback và điều khiển camera; thêm draft/STALE so với checked snapshot. Lỗi API/network giữ draft và checked. Bảng/summary/viewer chỉ gắn kết quả kiểm đúng snapshot; không biến UI thành validator.
4. Launcher/build/docs và browser tests: cold start/health, setup mới độc lập cache archive; offline sau setup (chặn traffic ngoài loopback); chọn đồng bộ, chỉnh limits/mass/position/undo, STALE và lỗi, WebGL fallback. Mesh position/dimensions sau yaw phải có đối chiếu với API, ảnh không thay oracle số.
5. Worker return: bảng từng M1-01…09 với lệnh, exit code, file evidence/giới hạn; ghi các phần tái sử dụng/thay đổi, path đúng, dependency hoặc lỗi còn lại. Log/evidence phải từ cây mới; không sao chép kết quả cũ để nhận đạt.

Evidence directory: `docs/reviews/SCST_M1_EVIDENCE/`. Worker return: `docs/reviews/SCST_M1_WORKER_RETURN.md`. Root tự review kết quả và chạy kiểm độc lập phù hợp; không bắt owner làm QA kỹ thuật. Không tuyên bố kiểm AI governance; synthetic local checks không cần provider.

## Cost, checkpoints and stop

Trần hiện tại: 120 phút triển khai + 45 phút review/sửa/kiểm; gồm tối đa 20 phút cài đặt/điều tra tương thích. Tận dụng source và các review đã có; chi phí cũ không đo. Không tự đổi stack hoặc nghiên cứu mở rộng. Báo root nếu setup lỗi lặp, scope/risk/acceptance đổi, hết trần hoặc vòng sửa thứ ba không có nguyên nhân mới; root quyết định trong authority hoặc báo owner khi vượt ranh giới.

Checkpoint backend/contract → frontend/integration → worker return. Không chia nhãn mới để reset budget. Phần khó báo root để dùng Sol-Medium trong cùng scope. Worker không tự chốt M1; product acceptance vẫn thuộc owner sau internal readiness.

## Gate-To-Role Closeability Contract

closeabilityContractVersion: cvf.gate-role-closeability@1.0.0
closeabilityDisposition: CLOSEABLE
returnTimeRecheck: REQUIRED_BEFORE_REPAIR
implementationTopologyPolicy: BOUNDED_PATH_FAMILIES
foreseeableFileSplitDisposition: COVERED_BY_BOUNDED_PATH_FAMILY

| gateId | mustPassBy | repairOwner | repairPhase | mutationSurface | topology | commitOwner | commitPhase | dependsOn |
|---|---|---|---|---|---|---|---|---|
| authorization_review | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M1_REUSE.md | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | NONE |
| pre_dispatch_gate | PRE_DISPATCH | work-order-author | PRE_DISPATCH | docs/work_orders/SCST_M1_REUSE.md; docs/milestone-coverage-authority.json | EXACT_PATHS | commit-steward | DISPATCH_COMMIT | authorization_review |
| dispatch_continuity | IMPLEMENTATION | session-sync-steward | IMPLEMENTATION | CVF_SESSION/handoffs/AGENT_HANDOFF_V1_2026-10-31.md material-SHA marker | EXACT_PATHS | session-sync-steward | DISPATCH_CONTINUITY_COMMIT | pre_dispatch_gate |
| focused_checker_tests | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| adif_integrity | WORKER_RETURN | implementation-worker | IMPLEMENTATION | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests |
| pre_implementation_autorun | IMPLEMENTATION | implementation-worker | IMPLEMENTATION | docs/work_orders/SCST_M1_REUSE.md; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | dispatch_continuity |
| worker_return_fast | WORKER_RETURN | implementation-worker | WORKER_RETURN | apps/frontend; services/backend; contracts; tests; tooling | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | focused_checker_tests, adif_integrity |
| reviewer_fast | REVIEW | reviewer | REVIEW | apps/frontend; services/backend; contracts; tests; tooling; README.md | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | worker_return_fast |
| pre_commit | PRE_MATERIAL_COMMIT | commit-steward | PRE_MATERIAL_COMMIT | docs; CVF_SESSION; IMPLEMENTATION_STATUS.json | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | reviewer_fast |
| terminal_completion_review | POST_MATERIAL | reviewer | REVIEW | docs/work_orders | BOUNDED_PATH_FAMILIES | commit-steward | MATERIAL_COMMIT | pre_commit |
| continuity | CONTINUITY_COMMIT | session-sync-steward | CONTINUITY_COMMIT | CVF_SESSION; CVF_SESSION_MEMORY.md; IMPLEMENTATION_STATUS.json; docs/catalog | BOUNDED_PATH_FAMILIES | session-sync-steward | CONTINUITY_COMMIT | terminal_completion_review |
| committed_range_closure | POST_MATERIAL_CLOSURE | commit-steward | POST_MATERIAL_CLOSURE | docs/work_orders; CVF_SESSION | BOUNDED_PATH_FAMILIES | commit-steward | CORRECTIVE_MATERIAL_COMMIT | continuity |



## Milestone coverage

Tiêu chí là toàn bộ mục `## M1 acceptance` của SPEC đã thống nhất. Tất cả được chọn; bản cũ chỉ là source candidate, chưa là bằng chứng M1 mới. Phần xa M2–M5 giữ theo roadmap, không mở trong work order này.

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/specs/SCST_M1.md",
    "heading": "## M1 acceptance",
    "sha256": "effb7d0b340f5e3e8313eb5f12df019c06e4f60ec1935f17c4ee9146202fa282"
  },
  "milestone": {
    "id": "SCST-M1",
    "consumer": "Owner SCST",
    "outcome": "Synthetic local M1 usable demo under SPEC v0.2, selective archive reuse and all nine acceptance criteria",
    "checkpoint": {
      "trigger": "Worker returns evidence for all M1-01 through M1-09 or budget/scope boundary reached",
      "owner": "Root orchestrator/reviewer; owner decides business acceptance",
      "decision": "Review technical readiness, repair within scope, or return unresolved scope to owner; no M2 implementation"
    }
  },
  "phase": "REVIEW",
  "action": {
    "kind": "REVIEW",
    "selected": [
      "M1-01",
      "M1-02",
      "M1-03",
      "M1-04",
      "M1-05",
      "M1-06",
      "M1-07",
      "M1-08",
      "M1-09"
    ],
    "owner": "Root independent reviewer",
    "output": "docs/reviews/SCST_M1_REVIEW.md and committed M1 source/evidence",
    "budgetMinutes": 165,
    "stop": "Technical work complete; no automatic M2 or business acceptance",
    "next": "Owner views M1 synthetic demo and provides business feedback"
  },
  "rows": [
    {
      "id": "M1-01",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-02",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-03",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-04",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-05",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-06",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-07",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-08",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    },
    {
      "id": "M1-09",
      "state": "VERIFIED",
      "gap": "Technical criterion verified; owner business feedback remains pending",
      "owner": "Root reviewer",
      "destination": "docs/reviews/SCST_M1_REVIEW.md; owner demo checkpoint",
      "evidence": [
        {
          "path": "docs/reviews/SCST_M1_REVIEW.md",
          "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
        },
        {
          "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
          "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
        }
      ]
    }
  ],
  "supportingWork": [
    {
      "criterionIds": [
        "M1-01",
        "M1-02",
        "M1-09"
      ],
      "reason": "Install public dependencies into a fresh local environment and make generation/build reproducible for the new tree",
      "budgetMinutes": 20,
      "stop": "Repeated setup failures or budget exhausted return to root without stack/scope changes",
      "returnToProduct": "Run M1 backend/browser/launcher checks and provide evidence from the new source"
    }
  ],
  "conclusions": {
    "tranche": "COMPLETE",
    "trancheSummary": "M1 implementation and independent technical review complete at material commit e81506ad79e3a7f84affa78c7f3ead47b0480c33; post-material committed-range checks passed",
    "trancheEvidence": [
      {
        "path": "docs/reviews/SCST_M1_REVIEW.md",
        "sha256": "b2c0dce4524ebb49af9066ca4f5e181523b5a556c2f1ccc6365b5e2b70bbaf42"
      },
      {
        "path": "docs/reviews/SCST_M1_EVIDENCE/reviewer-source-manifest.json",
        "sha256": "69854b28fee235ca91a31810b58e0c949af1682eb360994d93347c052dec18a0"
      },
      {
        "path": "docs/reviews/SCST_M1_EVIDENCE/demo-smoke.json",
        "sha256": "80bcda9ffc76e258d92043536de5c7d778c7b9a46359dea1da8b015c20b3f48d"
      }
    ],
    "product": "PENDING",
    "productSummary": "M1 technically ready; owner business/demo acceptance pending, M2-M5 remain out of scope",
    "acceptance": [],
    "owner": "Project owner for business acceptance; root for technical tranche closure"
  }
}
```

## Post-material closure

Material commit: e81506ad79e3a7f84affa78c7f3ead47b0480c33. Root reviewed worker return plus independent source/oracle/API/browser checks, then committed M1 and passed the committed-range review. All nine technical criteria verified; bounded implementation work is closed. Owner demo/business feedback remains pending and no M2 is dispatched. Root manages a foreground demo session at http://127.0.0.1:8765; it is not a published service. The original dispatch coverage state is preserved in commit 60f7cd3; the block above is current REVIEW reconciliation.
