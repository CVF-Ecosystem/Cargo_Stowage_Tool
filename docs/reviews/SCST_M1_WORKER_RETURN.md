# SCST M1 — Worker return

Work order `SCST_M1_REUSE`, dispatch 60f7cd3333b431ebb80e8a3be59eb424d8df7e55; worker IMPLEMENTATION_WORKER. Đây là kết quả worker để reviewer độc lập đánh giá, không phải owner nghiệm thu hay bằng chứng CVF điều khiển AI. Không gọi provider, không dùng dữ liệu thật.

## Kết quả theo acceptance

| ID | Thực hiện và bằng chứng | Tình trạng worker |
|---|---|---|
| M1-01 | `tests/cold_start_smoke.py`: môi trường Python/Node mới, setup bằng launcher, demo API; `tests/launcher_smoke.py`: launcher trên cây hiện tại, health AI off + HTML + API. `cold-start.log`, `launcher-smoke.log`. Browser offline có guard Python và chặn non-loopback trong browser: `browser-offline-e2e.log`, `offline-guard-probe.log`. | Đã kiểm |
| M1-02 | D2, D3, strict integer và identities trong model; API kiểm 422; `backend-tests.log`, `contract-hashes.txt`, `contract-regeneration.log`, `contract-types.log`. | Đã kiểm |
| M1-03 | Domain tách model/geometry/rules; kiểm xác định và không mutation trong backend tests; rules không dùng planner. | Đã kiểm |
| M1-04 | Backend tests 1g với onboard > 0, 1mm, chạm mặt/overlap, yaw, required/optional/excluded, từng trường D3; reviewer bổ sung oracle độc lập `reviewer-backend.json`. | Đã kiểm |
| M1-05 | Test ba status và ưu tiên hình học khi có nhiều lỗi, operational_eligible false và unchecked trong backend tests. | Đã kiểm |
| M1-06 | Viewer, bảng, tóm tắt dùng checked result; actual mesh parameters/positions được đo từ THREE objects; browser test đối chiếu API/3D/2D, click mesh, mass và cả ba limits/available capacity với onboard > 0. | Đã kiểm |
| M1-07 | Draft raw và kết quả đã kiểm tách riêng, giữ draft khi lỗi; so snapshot lúc response và giữ chỉnh sửa mới; browser test gồm sửa tiếp khi response đang chờ, 422, mất mạng và undo. | Đã kiểm |
| M1-08 | Viewer 3D, picking/orbit/zoom/reset, 2D keyboard và WebGL fallback; browser test và ảnh mới `browser-3d-yaw.png`, `browser-2d-stale.png`, `browser-mobile-fallback.png`, `browser-mobile-table-scrolled.png`. | Đã kiểm |
| M1-09 | `docs/APP_GUIDE.md`, log mới; archive identity do root reviewer kiểm độc lập. | Chờ reviewer xác minh archive |

## Lệnh và kết quả

- `.venv/Scripts/python.exe -m pip install -r requirements-lock.txt`: exit 0, venv mới.
- `npm.cmd ci` trong `apps/frontend`: exit 0, 109 package; npm audit báo 0 vulnerability trong lượt đó, không phải chứng nhận an toàn toàn diện.
- `.venv/Scripts/python.exe -m pytest tests/backend -q`: exit 0, 51 passed; một cảnh báo Starlette/httpx deprecation (`backend-tests.log`).
- `.venv/Scripts/python.exe tooling/export_contract.py` và `npm.cmd --prefix apps/frontend run contract`: exit 0; chạy lại và SHA-256 OpenAPI/types giống nhau (`contract-hashes.txt`).
- `npm.cmd --prefix apps/frontend run build`: exit 0 (`frontend-build.log`); Vite cảnh báo chunk Three.js trên 500 kB.
- `.venv/Scripts/python.exe tests/launcher_smoke.py`: exit 0 (`launcher-smoke.log`).
- `.venv/Scripts/python.exe tests/cold_start_smoke.py`: exit 0 (`cold-start.log`) sau khi sửa encoding stdout; lượt trước setup và API thành công nhưng test process exit 1 khi in ký tự Unicode vào console cp1252. Snapshot cold start sau sửa nhãn, D3 và surface quan sát mesh; trước CSS reviewer-local, setup/launcher không thay đổi sau đó. Lần chạy mới dùng cache package hệ thống, không chuyển paused runtime.
- `$env:PYTHONPATH=(Resolve-Path tests/offline_guard).Path; npm.cmd --prefix apps/frontend run test:e2e`: exit 0, 5/5 passed (`browser-offline-e2e.log`); guard được nạp vào server Python, browser route chặn kết nối ngoài loopback. `tests/offline_guard_probe.py` exit 0 xác nhận guard chặn DNS `example.com`; giới hạn bằng chứng là Python socket/DNS và browser routing, không phải firewall toàn hệ điều hành. Lượt đầu 3/4 và lượt bổ sung 4/5 do assertion test chờ response / selection cũ, test được sửa và chạy lại; không ẩn lỗi cũ.

## Nguồn dùng lại và phần thay đổi

- `archive/.../domain/models.py` → `services/backend/app/domain/model/__init__.py`: strict model giữ lại; bổ sung limits, D3, D4, contract.
- `archive/.../domain/validation.py` → `domain/geometry` và `domain/rules`: giữ phép tính integer/overlap, tách hình học, đổi tải và status.
- Fixture 13 bó/12 vị trí → `services/backend/app/demo.py`; API/routes/main giữ wiring và chuyển imports.
- `Viewer.tsx` → `apps/frontend/src/viewer-3d/Viewer.tsx`, giữ Three/2D/interaction; thêm quan sát số trực tiếp từ mesh. Helpers → `features/model.ts`, request → `api/client.ts`; workspace được viết lại theo draft/checked để đáp ứng D7, giữ luồng chọn/bảng/undo.
- Lock/config/launcher/tooling chọn lọc từ archive; contract/types sinh từ backend mới; backend tests chuyển và mở rộng; browser tests tạo mới trên app mới. Không đưa cache/build/log/authority cũ vào ứng dụng.

## Giới hạn và lưu ý review

Không khẳng định an toàn khai thác hoặc product acceptance. Chưa có planner, import/lưu/export, nhiều tầng, dữ liệu thật hoặc AI. Dữ liệu trong tab mất khi refresh; hàng đã có được giả định ngoài hầm mục tiêu. Cảnh báo test-client deprecation và Vite chunk size được giữ nguyên, không đổi dependency ngoài phạm vi. Lượt status parent-container REPAIR_REQUIRED đã ghi riêng trong handoff, không sửa container/core. Mọi quyền closure, catalog/continuity và commit thuộc root.
