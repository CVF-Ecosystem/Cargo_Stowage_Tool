# SCST — Áp dụng CVF trong quá trình dựng tool

Status: DESIGN

Cập nhật 01-11-2026 theo chỉ đạo owner: ưu tiên áp dụng CVF tại project trước SUP-01,
và duy trì xuyên suốt các mốc. Người nhận là đội agent phát triển và người tiếp quản.
Kết quả cần đạt là mỗi phần việc có phạm vi, vai trò, công cụ kiểm, bằng chứng và phần còn lại rõ ràng.
Đây là thiết kế áp dụng; chưa phải SPEC/WORK_ORDER hoặc kết luận CVF đã kiểm soát đầy đủ agent.

Tiến độ áp dụng: [đối chiếu và continuation giới hạn](../reviews/SCST_CVF_DEV_APPLICATION_RECONCILIATION.md)
đã cho SUP-01 thuần viewer đi tiếp; [SUP-01 đạt kiểm kỹ thuật](../reviews/SCST_SUP_01_REVIEW.md) với DA01/04/05
trong brief/kiểm/review. DEV-01 vẫn IMPLEMENTED_UNPROVED, DEV-02/03 UNKNOWN; full adoption/live proof chưa đóng.
Các đoạn DESIGN/lượt chuyển nguồn bên dưới giữ phạm vi riêng, không phủ nhận tiến độ runtime trong IMPLEMENTATION_STATUS.json.

## Vị trí và ranh giới

**CVF-DEV → SUP-01 → SUP-02 → SUP-03 → kiểm tích hợp → M2d**.
CVF-DEV là checkpoint chuẩn bị cách làm tại project; sau đó tiếp tục áp dụng ở mọi mốc,
không tạo một chương trình xây lại framework hoặc trì hoãn sản phẩm bằng việc kiểm mọi năng lực CVF.
M4 vẫn chỉ là nhánh AI/CVF trong sản phẩm khi đến lượt.

Core dùng chung ở `../.Controlled-Vibe-Framework-CVF`, pin `c4c8767ac8861854f40d466ba338ffd11eb9558e`,
giữ read-only. Trong project đã có `.cvf/`, `AGENTS.md`, gate runner và hồ sơ riêng.
Áp dụng được đánh giá theo đường gọi và bằng chứng của project, không theo vị trí thư mục core.
Tái sử dụng chuẩn, kit và công cụ phù hợp; chỉ bổ sung kết nối thiếu đã xác định, không chép toàn bộ core vào app.

## Đầu ra checkpoint CVF-DEV

| ID | Đầu ra và điều kiện đánh giá | Chủ sở hữu và phần còn lại |
|---|---|---|
| DEV-01 | Bản đồ áp dụng theo từng bước: nguồn CVF được ghim, vai trò, artifact và đường gọi kiểm của project; phân biệt phần có sẵn, đã gọi và chưa có bằng chứng. | Orchestrator đối chiếu; reviewer độc lập kiểm phạm vi và reuse. Bảng nền bên dưới chưa thay proof tuân thủ agent. |
| DEV-02 | Luồng làm việc tại project có điểm gọi kiểm trước giao việc, nhận kết quả, review và commit; xác định đường gọi tay/tự động, lỗi/dừng và khoảng trống hook/CI. Chỉ sửa kết nối thiếu qua SPEC/WORK_ORDER giới hạn. | Worker thực hiện sau khi có lệnh; reviewer kiểm phiên bản và cách tái lập. Hook/CI không được coi đã chạy chỉ vì có template hoặc YAML. |
| DEV-03 | Gói bằng chứng của phạm vi đã chọn và bàn giao có kết luận riêng về cơ học, hành vi agent và sản phẩm; phần chưa chứng minh có owner/điều kiện quay lại; learning có đường trả về CVF. | Reviewer độc lập đánh giá; orchestrator giữ phần còn lại. Mọi thử nghiệm/tuyên bố hành vi governance cần provider thật và request/response đã loại bí mật. |

Checkpoint kích hoạt khi ba đầu ra đã được đối chiếu và có quyết định review, hoặc gặp thay đổi
phạm vi/rủi ro/quyền gọi provider. Quyết định gồm tiếp tục SPEC SUP-01, sửa trong phạm vi, giữ phần phụ thuộc,
hoặc xin đổi phạm vi thực sự. Đội phát triển tự chuẩn bị và kiểm luồng trước phản hồi nghiệp vụ của owner.
Không dùng document PASS để đóng DEV-02/03. Không bắt SUP-01 chờ một tuyên bố “kiểm soát mọi agent”;
nếu proof chưa có mà không ảnh hưởng slice đã chọn, reviewer phải ghi căn cứ độc lập và giới hạn claim trước khi đi tiếp.

## Bản đồ kế thừa và trạng thái nền

Nền đối chiếu: commit `5712083`, profile `cvf.downstreamGateProfile@1.2.0`.
Các nhãn INSTALLED/INVOKED chỉ áp dụng cho cơ chế được dẫn; chưa có PROVEN_HERMETIC
hoặc bằng chứng live-provider của đợt này.

| CVF cung cấp | Chỗ áp dụng tại project | Bằng chứng nền / khoảng trống | Khi nào dùng, ai chịu trách nhiệm |
|---|---|---|---|
| Lifecycle, risk và vai trò | [AGENTS.md](../../AGENTS.md), [policy](../../.cvf/policy.json), `docs/specs/`, `docs/work_orders/` | Quy tắc và artifact hiện hữu; sự hiện diện không chứng minh agent luôn tuân thủ. | Orchestrator nhận việc/chuyển vai; reviewer kiểm nguồn và điều kiện giao việc mỗi tranche. |
| Coverage gắn kết quả người dùng | [authority registry](../milestone-coverage-authority.json), coverage trong roadmap và work order | Gate coverage có receipt INVOKED ở lượt roadmap trước; chỉ kiểm liên kết/shape/hash, không đánh giá thay người về sản phẩm dùng được. | Trước dispatch và khi đổi scope/source; giữ acceptance lịch sử theo snapshot khi cần. |
| Kit kiểm cục bộ được pin | [lock](../../.cvf/gate-profile.lock.json), [runner](../../scripts/cvf_gates/cvf_downstream_gate_runner.py) | INSTALLED; [reviewer-fast](../reviews/SCST_3D_SUPPLEMENT_EVIDENCE/gates/reviewer-fast.json) và [pre-commit](../reviews/SCST_3D_SUPPLEMENT_EVIDENCE/gates/pre-commit.json) đã INVOKED cho tài liệu trước. Không suy ra control work-order đã được thử từ kết quả N/A. | Worker/reviewer/steward gọi đúng phase; không sửa hoặc bypass control kế thừa. |
| Hook và CI | Template pre-commit trong kit; [workflow](../../.github/workflows/cvf-downstream-gates.yml) trong project | Máy local hiện không có `core.hooksPath` cấu hình và không có `.git/hooks/pre-commit`; đã dùng runner trực tiếp. Workflow INSTALLED, chưa xác minh lần chạy hosted CI ở lượt này. | DEV-02 xác minh đường gọi thực, chọn reuse hook được cung cấp nếu phù hợp; không tự nâng claim hoặc sửa workflow đang pin. |
| Continuity và catalog | `CVF_SESSION/`, [memory](../../CVF_SESSION_MEMORY.md), [implementation truth](../../IMPLEMENTATION_STATUS.json), [index](../INDEX.md) | Có hồ sơ và kiểm đồng bộ cục bộ. Bootstrap read model chưa có: BOOTSTRAP_MIGRATION_PENDING, không chặn cách đọc fallback được quy định. | Agent mới/tiếp quản đọc trước làm; steward cập nhật khi đổi authority hoặc bước kế tiếp. |
| Tri thức và learning | `knowledge/`, [learning home](../reviews/learnings/README.md) | Knowledge hiện mới có README; ingest không tạo tri thức nghiệp vụ mới. SCST-L001 đã sửa local, còn chờ parent assessment; chưa có cải tiến trả về. | Đọc theo trigger; ghi bài học có giá trị, giữ riêng local action/parent decision/returned adoption. |
| Bằng chứng governance thật | Quy định trong AGENTS/policy và review evidence của tranche liên quan | Lượt này NOT_RUN đối với live-provider; doctor/các receipt tài liệu không chứng minh risk/approval/DLP/provider routing hoặc agent behavior. | Trước thử nghiệm live cần scope R2, credential/quyền gọi và reviewer độc lập; lưu request/response không bí mật, cả FAIL/SKIP/NOT RUN. |

## Project Development Application — phần chung và riêng

Áp dụng bổ sung theo yêu cầu owner 01-11-2026 về nâng nền CVF và thử trên hai project.
Baseline Core pin `c4c8767ac8861854f40d466ba338ffd11eb9558e` giữ nguyên.
Nguồn bổ sung: artifact `project-development-application-standard` trong manifest
được `../CVF_RULE_PACKS/ACTIVE_RULE_PACK.json` trỏ tới; nguồn Core `docs/reference/downstream_gate_profile/CVF_PROJECT_DEVELOPMENT_APPLICATION_STANDARD.md`,
SHA-256 `d06b62387e015160a77658f333882a2a316d54ffd0421071354cf63a3730dd7a`. Đây là bản local từ worktree Core, chưa public export.

Phần chung: lifecycle/risk, phạm vi và owner, ưu tiên native/kit có sẵn, coverage,
review độc lập khi governance-significant, nghiệm thu nội bộ và ghi phần còn lại.
Bảng dưới cụ thể hóa việc phát triển SCST; không thêm quy tắc vận hành tàu.

| ID / nguồn tiêu chí | Quy tắc chung | Kiểm soát riêng khi phát triển | Trigger / owner | Cách kiểm và tình trạng |
|---|---|---|---|---|
| SCST-DA01 / IMPLEMENTATION_STATUS.json: exact stored data, kg/cm UI; SUP-01 | Giữ tiêu chí, kiểm đầu ra người dùng | Khi sửa viewer/form, phân biệt làm tròn hiển thị với giá trị lưu và ngưỡng hình học; không round-trip từ nhãn về dữ liệu chính xác | Worker trước sửa UI/serialization; reviewer trước nhận | Ca đổi đơn vị, trường chưa sửa, save/reload; đối chiếu giá trị gốc. Hướng dẫn đã ghi, ca sản phẩm mới chưa chạy |
| SCST-DA02 / IMPLEMENTATION_STATUS.json: SQLite snapshot, không reset DB lỗi | Scope/risk và bảo toàn dữ liệu | Dùng dữ liệu thử tách biệt; nêu phương án tương thích/phục hồi khi đổi schema/snapshot; không ghi vào SQLite user để chứng minh test | Worker khi đổi persistence; reviewer độc lập | Kiểm round-trip snapshot và lỗi không ghi đè/reset; dữ liệu user giữ nguyên. Chưa mở migration |
| SCST-DA03 / IMPLEMENTATION_STATUS.json: dimensions sourced/estimated; SUP-02/03 | Bằng chứng nguồn và owned remainder | Phân biệt số đo có nguồn với ước lượng; đối chiếu profile/revision và fixture packing; không dùng test placement để suy nghiệm thu stability/strength | Spec author và reviewer khi đổi profile/packing | Kiểm nguồn/đơn vị/revision, ca biên xếp hàng theo SPEC được chốt. Điều kiện chưa rõ giữ UNKNOWN, không tự tạo dung sai |
| SCST-DA04 / DEV-01/02/03 tại checkpoint này | Reuse, review và giới hạn claim | Dùng runner/kit hiện có, chỉ mở adapter cho điểm thiếu đã xác minh; mỗi task dẫn row áp dụng và bằng chứng thực gọi | Orchestrator trước dispatch, reviewer khi nhận | Đối chiếu contract/receipt với task; source/test/doctor không chứng minh agent behavior. DEV-01 IMPLEMENTED_UNPROVED; DEV-02/03 UNKNOWN giữ nguyên |
| SCST-DA05 / luồng SUP-01 tới M2d | Nghiệm thu nội bộ do đội dev sở hữu | Kiểm luồng nhập/sửa/xem/lưu/đọc lại liên quan đến slice đã chọn trước khi nhờ owner phản hồi nghiệp vụ | Worker + reviewer trước giao bản dùng được | Nêu input, hành động, output quan sát và phần chưa đạt; test count không thay flow acceptance. Chưa nhận nghiệm thu sản phẩm |

Khi agent mới nhận việc hoặc thay mục tiêu/rủi ro, chủ động kiểm bảng này với yêu cầu
và roadmap hiện tại; chỉ bổ sung row còn thiếu trong hồ sơ này. Brief dẫn đúng row,
tiêu chí đã chốt, phạm vi, owner và bằng chứng cần có. Thiếu điều kiện giữ phần phụ
thuộc; không tự mở thêm vòng kiểm toàn nền. Thiết lập bảng không đóng CVF-DEV.
Lượt hiện tại kiểm đường dẫn, nội dung, hash, catalog và gate tài liệu; live-provider
NOT_RUN, không sửa app/DB/hook/CI hoặc giải phóng milestone sản phẩm.

## Luồng áp dụng xuyên suốt

1. INTAKE/DESIGN: đọc continuity và nguồn; ghi kết quả cần đạt, rủi ro, reuse và phần thiếu.
2. SPEC/WORK_ORDER: chốt tiêu chí, đường dẫn được sửa, bằng chứng, người review và quyền commit;
   chạy `pre-dispatch` với packet áp dụng. Không cấp BUILD chỉ từ roadmap.
3. BUILD/worker return: sửa đúng phạm vi; kiểm phù hợp và chạy `worker-return`, giữ lỗi và giới hạn.
4. REVIEW: người độc lập đọc source/kết quả/coverage; chạy `reviewer-fast`; tách kiểm kỹ thuật,
   chấp nhận sản phẩm nội bộ và phản hồi nghiệp vụ. Governance-significant work phải có reviewer độc lập worker.
5. FREEZE/tiếp quản: chạy `pre-commit`, steward kiểm tập thay đổi, đồng bộ handoff/truth/catalog;
   CI chỉ được ghi INVOKED khi có run receipt. Commit/push/deploy vẫn theo quyền tương ứng.

Áp dụng ngay bằng hồ sơ hiện hữu; DEV-02 chỉ bổ sung điểm nối thực sự thiếu sau kiểm.
Việc quay vòng một hành động qua nhiều agent không tự tạo proof governance.

## Giới hạn và bước kế tiếp

Lượt này chỉ cập nhật DESIGN và kiểm tính nhất quán tài liệu; không cài hook, sửa runner/policy/CI,
gọi API, đọc secret, đổi app/DB hoặc chốt nghiệm thu. Giữ source/runtime đã giao và dữ liệu người dùng.
Ưu tiên tiếp theo là đối chiếu hữu hạn rồi SPEC/WORK_ORDER CVF-DEV cho khoảng trống có bằng chứng;
sau checkpoint mới SPEC SUP-01. Orchestrator sở hữu phần chưa đạt, không giao kiểm kỹ thuật cho owner.

Ngân sách lập/rà soát thay đổi định hướng này tối đa 45 phút, không reset qua repair; khi hết phải trả trạng thái
và phần còn lại. Khi mở verification CVF-DEV sau này, giới hạn 30 phút đọc kit/đường gọi, đầu ra là bảng gap
và SPEC có phạm vi hoặc kết luận chưa cần thay code; không tự mở điều tra kế tiếp hay gọi provider.

<details>
<summary>Coverage của checkpoint — planning only</summary>

```cvf-milestone-coverage-json
{
  "schemaVersion": "cvf.milestoneCoverage@1.0.0",
  "authority": {
    "path": "docs/project/SCST_CVF_DEVELOPMENT_ADOPTION.md",
    "heading": "## Đầu ra checkpoint CVF-DEV",
    "sha256": "ed8b0413e0e5a3ac83b77cf914f08081e2e4e239302b3e593fbb812d252e3fa0"
  },
  "milestone": {
    "id": "SCST-CVF-DEV",
    "consumer": "SCST development agents and project owner",
    "outcome": "Project-local CVF adoption with explicit invocation, proof limits and reusable learning before SUP-01",
    "checkpoint": {
      "trigger": "Adoption criteria reconciled or scope/risk/provider authority boundary reached",
      "owner": "Independent reviewer for internal evidence; orchestrator for remaining work",
      "decision": "Continue to bounded SUP-01 SPEC, repair, hold affected work or seek actual scope change"
    }
  },
  "phase": "PLAN",
  "action": {
    "kind": "PLAN",
    "selected": [],
    "owner": "Root orchestrator/design author with independent review",
    "output": "docs/project/SCST_CVF_DEVELOPMENT_ADOPTION.md",
    "budgetMinutes": 45,
    "stop": "Adoption design reviewed and continuity synchronized, or same-scope budget exhausted",
    "next": "Bounded CVF-DEV reconciliation then SPEC/WORK_ORDER only for evidenced gaps; no BUILD or provider call now"
  },
  "rows": [
    {
      "id": "DEV-01",
      "state": "IMPLEMENTED_UNPROVED",
      "gap": "Initial source and lifecycle mapping drafted; independent adoption reconciliation not completed",
      "owner": "Orchestrator and independent reviewer",
      "destination": "docs/specs/SCST_CVF_DEV.md",
      "evidence": []
    },
    {
      "id": "DEV-02",
      "state": "UNKNOWN",
      "gap": "Direct local runner receipts exist; actual per-stage invocation and hook/hosted-CI connection need bounded verification before changes",
      "owner": "Future worker and independent reviewer under CVF-DEV order",
      "destination": "docs/specs/SCST_CVF_DEV.md",
      "evidence": []
    },
    {
      "id": "DEV-03",
      "state": "UNKNOWN",
      "gap": "No live-provider proof in this design task; separate mechanical evidence, behavior proof and owned deferred claims in next contract",
      "owner": "Independent reviewer and orchestrator; credential authority separate",
      "destination": "docs/specs/SCST_CVF_DEV.md",
      "evidence": []
    }
  ],
  "supportingWork": [],
  "conclusions": {
    "tranche": "PENDING",
    "trancheSummary": "Design prioritization only; adoption checkpoint not accepted",
    "trancheEvidence": [],
    "product": "PENDING",
    "productSummary": "No full agent-governance or product readiness claim; app milestones remain separate",
    "acceptance": [],
    "owner": "Project owner"
  }
}
```

</details>
