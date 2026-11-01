# Local editor-help wording review

Risk: R2
Worker: root-orchestrator
Reviewer: Sol-Medium

Scope: the single help paragraph in `apps/frontend/src/features/Workspace.tsx` supplied as a reviewer-local wording repair after the frozen display build. Before: “Giá trị nhập hiển thị làm tròn; chỉ trường bạn sửa mới được cập nhật. Có thể nhập lẻ đến 0,1 cm hoặc 0,001 kg.” After: “Số hiển thị làm tròn đến kg/cm; chỉ trường bạn sửa mới được cập nhật.” The current source contains the latter text once, in the editor form paragraph at line 297; `git diff --check` passes for the file.

This aligns with DU-01's practical kg/cm emphasis. It retains DU-02's essential warning that only an explicitly edited field is updated. The changed JSX is a static text node: it contains no input value, handler, parser, state update, API call or geometry expression. The existing `parseKg`/`parseCm` paths remain present and still accept the fractions specified by the approved SPEC; the shorter help sentence does not change that acceptance. The CSV contract keeps its separate mm/kg instructions. Objective, design, allowed path, R2/local effects and commit owner remain unchanged.

Disposition: accept this localized wording correction. This review is source/contract inspection only; root reported 31/31 full browser checks and an additional 167-source case before the wording change and owns the rebuild/focused post-change check. No operational safety or CVF governance behavior is claimed here.
