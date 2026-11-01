# SCST M2c — Chỉnh, giữ bản gốc và so sánh phương án

Status: APPROVED_FOR_EXECUTION

## Authority and outcome

Owner nói **“tiếp”** ngày01-11-2026 sau bàn giao M2b. Roadmap chọn phần kế tiếp M2c: chỉnh/kiểm lại, giữ bản trước và so sánh. Tái sử dụng editor, checked/draft, history20, M2b, snapshotSQLite immutable và viewerVINAFCO đã có; bổ sung baseline rõ ràng và so sánh đầy đủ. Root orchestrator/spec author/reviewer; Terra6.1High implementation; Sol-Medium browser. R2, local-only, không push dữ liệu hoặc sửa source/ship. M2d/export/nhiều tầng không mở trong lượt này.

Người dùng giữ bản A, chỉnh/kiểm thành B, xem chính xác bó/vị trí/giới hạn thay đổi, khôi phục A khi muốn và lưu B thành snapshot mới mà A vẫn nguyên. Có thể mở savedB theo luồng cũ rồi chọn savedA làm baseline; không cần thay DB hoặc xây hệ thống version mới.

## Design and contracts

D1 — Backend comparison: POST `/api/plans/compare` nhận `{before: Plan, after: Plan}` bằng model hiện tại, extra fields bị từ chối. Validate/re-evaluate riêng từng plan bằng rules hiện hành, không tin status đã lưu và không dùng hold/limits của B để kiểm A. Trả summariesA/B, deltas chính xác và context/unit changes; không mutate input, ghi DB hoặc tự chọn bản tốt hơn. Giữ contract v1/v2/source1076 và sourcebinding hiện có. Không thêm dependency/schemaDB/savedPlanversion.

D2 — Scope diff: so sánh tất cả context được hỗ trợ (contract/source/cargo_source/cargo_dataset, vessel/case, hold và limits); unit đối chiếu theo ID, orderarray không tạo diff. Mỗi ID thuộc đúng một trạng thái ADDED/REMOVED/CHANGED/UNCHANGED. CHANGED nếu thuộc tính unit hoặc placement đổi; ADDED/REMOVED có thông tin cần xem. So sánh cả name/kind/requirement/dimensions/mass/source_ref, exactdimensions_um, và placement x/y/z/yaw/layer/supported_by; absentplacement khác placed. Defaults canonical từ Pydantic tránh báo khác vì omitted/default. ID chung nhưng source_ref khác phải cảnh báo không xác nhận cùng bó vật lý. Không fuzzy match/merge hoặc renumber IDs.

D3 — Exact output: số tính theo g/mm/µm nguyên; summary deltas = B−A, gồm manifestmass/placedmass/remainingcapacity, placed/unplaced/excluded counts và số lỗi kiểm thực (fullcount kể cả issues bị cắt). Issue/status/unchecked/operational flags theo từng bản, luôn chưa cấp điều kiện vận hành. Context changed có cảnh báo phép so sánh khác điều kiện, không xếp hạng tối ưu/tốt hơn. Thứ tự output ổn định theo ID/field; cùngplan khác thứ tự arrays units/placements vẫn bằng nhau về dữ liệu từng bó/vị trí. Bounded O(n) hoặc O(nlogn) cộng hai lần evaluate,1076source trong15s; không nhân bản toàn bộ hai plan trong từng unchanged row.

D4 — Baseline UI: **Giữ bản hiện tại làm gốc** copy checkedplanA vào tab, hoặc chọn saved snapshot → **Dùng bản lưu làm gốc** thông qua APIopen hiện có. NạpA không thay B, draft, placements, history hay DB. Hiện nhãn/tên/thời gian/savedID phù hợp; baseline trongtab chưa lưu có nhãn. Baseline không tự thay sau apply/planner/save/openB; muốn đổi có thao tác rõ. Refresh không hứa giữ baseline trong bộ nhớ, có thể chọn lại savedA. Không mở nháp STALE để làm baseline.

D5 — Compare UI: **So sánh với bản gốc** gửi checkedA/B; summary2cột, delta và contextchanges cùng bảng diff lọc trạng thái/searchID, phân trang tối đa50. Mặc định tập trung thay đổi, vẫn xem được unchanged và counts toànunion. Chi tiết trường có nhãn/đơn vị tiếng Việt và before/after rõ; không xả rawJSON thay giao diện. Overview mass vẫn2số lẻ tấn, chi tiết so sánh đủ chính xác để thấy1g/1mm/µm và source khác nhau. Chọn row có ID trongB đồng bộ editor/bảng/viewerB; REMOVED không chọn ID mất. Tái dùng mainviewerB, không dựng hai WebGL scenes hoặc làm giả baseline overlay.

D6 — Restore and transaction: **Khôi phục bản gốc** rõ ràng revalidateA bằng transition/history hiện có, chỉ đổi workspace sau thành công; giữ B trong Bản trước, source/reference profile nạp đúng. Không overwrite/delete snapshotA; saveB vẫn UUIDmới. STALE chặn baseline/compare/restore, pending/late/error không mất rawdraft/context/selection/baseline mới. Comparekey buộc cảA/B và revision; thay baseline/checkedplan/rawdraft thì không hiện kết quả cũ như kết quả hiện hành. Sourceimmutable/edit restrictions/M2b reason invalidation/rounding và error recovery hiện tại giữ nguyên.

D7 — Reuse and boundaries: chỉnh bằng input X/Y/góc, requirement và genericunit/hold đã có; không bổ sung drag/drop, bulk edit hoặc reset nhiều record. Sourceunit chỉ requirement/placement, không đổi vật lý. SQLite vẫn immutable/list100 và không delete/overwrite; so sánh không tự ghi DB. Giữ local provenance, 16source envelopes và holdước tính. Đây là so sánh dữ liệu/kiểm hiện có; chưa phải nghiệm thu geometry/hải hành/nghiệp vụ. Không export/AI/multilayer/new ship.

## M2c acceptance

| ID | Đầu ra và bằng chứng |
|---|---|
| M2C-01 | API so sánh đầy đủ context/unit/placement theoID, ADDED/REMOVED/CHANGED/UNCHANGED đúng, default/order normalization và provenance mismatch rõ; input không mutate/ghi DB |
| M2C-02 | A/B re-evaluate độc lập, summaries/fullissuecounts và deltas nguyên chính xác;1g/1mm/µm không bị rounding che ở chi tiết; khác điều kiện không tự kết luận bản tốt hơn |
| M2C-03 | Pin currentA hoặc load savedA không đổi B; chỉnh/checkB, compare summary/context/row detail và chọn ID còn trongB dùng được với mainviewer;1076filter/search/pagination50 và mobile/fallback |
| M2C-04 | RestoreA revalidates/history giữB, undo/saveB/loadA không mất provenance/placements; SQLiteA immutable và hoạt động sau reload/restart, memorybaseline có nhãn, không hứa tựlưu |
| M2C-05 | STALE/pending/late/error baseline/compare/restore không ghi đè edit/selection/context/baseline mới; comparison cũ không gắn vào plan hiện tại; M1/M2a/M2b/source guards giữ |
| M2C-06 | Meaningful boundary/source1076/performance/API/build/contracts/browser regression và rootoracle/review độc lập đạt; packagedflow chỉnh→so sánh→khôi phục→save/open exercised, docs/roadmap/truth đồng bộ |

## Checkpoint and remainder

Chọn6criteria;180phút implementation +60phút review/support, total240min không reset khi sửa. Preparation scan/doctor28checks và bounded Sol designpreflight, elapsed/billing chưa đo đầy đủ UNKNOWN. Gap là baseline/diff có đối soát, history20 đơn thuần chưa đủ; reuse snapshot/validator/editor/viewer để tránh rewrite. Ưu tiên luồng người dùng nội bộ đủ trước ownerfeedback. Stop khi có proof, scope/budget boundary hoặc source contradiction, không tự mở M2d.

M2d report export do orchestrator mở SPEC ở checkpoint sau M2c; M3/nhiều tầng/hầm đo thực/16envelopes/professionalverification do owner+domainverification giữ theo roadmap. Unknowns không thay đổi tính đúng phép diff trên hai plan đã validate, nên không chặn tính năng so sánh có nhãn. Business acceptance và operational suitability chưa có, không suy diễn từ chỉ đạo tiếp tục.
