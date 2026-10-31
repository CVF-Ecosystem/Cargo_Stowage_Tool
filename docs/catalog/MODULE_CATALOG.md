# Module Catalog

Machine-readable source: `docs/catalog/MODULE_REGISTRY.json`

Status: GOVERNED

## Metrics

- Total modules: 5
- Enforced: 4
- Partial: 0
- Contract-only: 1
- Stub: 0
- Deprecated: 0

| id | status | path | evidence | description |
|---|---|---|---|---|
| scst-api | ENFORCED | `services/backend/app/api` | services/backend/app/api/routes.py; backend tests and launcher-smoke.log | Local health/demo/validate API calling domain; AI off. |
| scst-contract | CONTRACT_ONLY | `contracts/openapi.json` | tooling/export_contract.py; contract-hashes.txt and reviewer-source-manifest.json | OpenAPI and derived frontend types for scst.m1.v1. |
| scst-domain | ENFORCED | `services/backend/app/domain` | tests/backend/test_validation.py; docs/reviews/SCST_M1_EVIDENCE/reviewer-pytest.log (51 pass); reviewer-backend.json (498 checks) | Synthetic BOX/single-layer model, integer geometry and rules only; no operational approval. |
| scst-frontend | ENFORCED | `apps/frontend/src` | tests/browser/workspace.spec.ts; docs/reviews/SCST_M1_EVIDENCE/reviewer-browser.log (5 pass) | Checked/draft workspace, table, Three/SVG projections and STALE/error recovery for synthetic M1. |
| scst-launcher | ENFORCED | `tooling` | tests/launcher_smoke.py; tests/cold_start_smoke.py; launcher-smoke.log; cold-start.log | Windows local setup, loopback server and contract generation. |
