# 07 — Architecture Treeview v0.1

**Decision:** FE/BE tách từ đầu, **một monorepo, một tool local**. Đây là cây **dự kiến**, không phải báo cáo repository đã tạo.

```text
steel-cargo-stowage-tool/
├── apps/
│   └── frontend/                 # React + TypeScript + R3F/Three.js
│       ├── src/features/
│       │   ├── vessel-intake/    # tài liệu gốc + hỏi xác minh
│       │   ├── manifest-intake/  # import/validation
│       │   ├── loading-case/     # limits và selection
│       │   ├── stowage-plan/     # report, compare, approve
│       │   └── viewer-3d/       # render from plan JSON, no own safety decisions
│       ├── src/api/              # generated TypeScript client from OpenAPI
│       └── tests/
├── services/
│   └── backend/                  # Python + FastAPI
│       ├── app/api/v1/          # typed endpoints; no raw DB in UI/agent
│       ├── app/domain/
│       │   ├── vessel/
│       │   ├── manifest/
│       │   ├── loading_case/
│       │   ├── rules/
│       │   ├── geometry/
│       │   ├── optimizer/
│       │   └── approval/
│       ├── app/adapters/
│       │   ├── file_store/
│       │   ├── sqlite/
│       │   ├── ai_optional/
│       │   └── cvf_bridge/       # isolated candidate adapter
│       ├── app/migrations/
│       └── tests/
├── contracts/
│   ├── schemas/                  # schemas, versioned
│   ├── api/                      # generated OpenAPI snapshots
│   └── rules/                    # rule IDs, source/applicability/version
├── packages/
│   └── cvf-guard-bridge/         # optional Node local process, AFTER feasibility spike
├── tests/
│   ├── golden-cases/
│   ├── safety-invariants/
│   ├── ui-e2e/
│   ├── security/
│   └── backup-restore/
├── docs/
│   ├── contracts/
│   ├── audit-reports/
│   ├── engineering-reviews/
│   └── user-guide/
├── tooling/
│   └── local-launcher/           # local one-click launch/package
└── runtime-data/                 # user local only: DB/files/backups; gitignored
```

## Layer rules

1. `frontend` không phụ thuộc ORM/SQLite/CVF internals; mọi mutation qua typed API.
2. `backend.domain` thuần logic, có unit tests; phụ thuộc adapter qua interface, không hardcode provider.
3. `optimizer` tạo dữ liệu tọa độ, validate lại độc lập trước khi lưu `RULES_CHECKED`.
4. `viewer-3d` là projection của `Plan JSON` và **không** đánh giá cargo safety.
5. `cvf_bridge` chỉ kiểm soát Agent actions; business rules chạy dù CVF/AI offline.
6. Tài liệu chứng từ thực và tệp khách hàng không commit Git.

## FE/BE API boundary

`FastAPI Pydantic models → OpenAPI snapshot → generated TypeScript models/client → React UI`. Pin OpenAPI/schema versions và hợp đồng tương thích. UI version mismatch hiển thị cảnh báo và từ chối hành động unsafe. `POST /optimize` là công việc có thể kéo dài; MVP có thể dùng job ID + polling local, không nhất thiết WebSocket.

## Gợi ý technology choices, CHƯA cố định

- FE: TypeScript + React, Three.js/react-three-fiber, một state store gọn, table/grid nhập liệu.
- BE: Python 3.x, FastAPI, Pydantic, SQLite migration tool, OR-Tools/heuristics bounded.
- Files: content-addressed immutable originals.
- Package: local launch (FE build có thể được backend serve như static assets). Không microservices.
