import type { Evaluation, Plan } from "../features/model";
import type { components } from "./generated/api";
export type VesselProfile = components["schemas"]["VesselProfile"];

export async function requestEvaluation(plan?: Plan): Promise<Evaluation> {
  const response = await fetch(plan ? "/api/validate" : "/api/demo", {
    method: plan ? "POST" : "GET",
    headers: plan ? { "Content-Type": "application/json" } : undefined,
    body: plan ? JSON.stringify(plan) : undefined,
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    if (response.status === 422)
      throw new Error(
        "Dữ liệu không đúng cấu trúc được hỗ trợ. Phương án trước vẫn được giữ.",
      );
    throw new Error(
      `Không thể kiểm phương án (HTTP ${response.status}). Thử lại khi backend sẵn sàng.`,
    );
  }
  const data = (await response.json()) as Evaluation;
  if (
    !["scst.m1.v1", "scst.m2a.v1", "scst.pipe-list.v1", "scst.pipe-list.v2"].includes(data.plan?.contract_version) ||
    !["SYNTHETIC", "MIXED_REFERENCE", "USER_ENTERED"].includes(data.plan.source)
  )
    throw new Error("Phiên bản dữ liệu API không tương thích.");
  return data;
}

export async function requestVesselProfile(): Promise<VesselProfile> {
  const response = await fetch("/api/vessels/vinafco268", { signal: AbortSignal.timeout(15000) }).catch(() => { throw new Error("Không tải được dữ liệu phương tiện."); });
  if (!response.ok) throw new Error("Không tải được dữ liệu phương tiện.");
  return await response.json() as VesselProfile;
}

export async function requestVesselPlan(caseId: string): Promise<Evaluation> {
  const response = await fetch(`/api/vessels/vinafco268/cases/${encodeURIComponent(caseId)}/plan`, { signal: AbortSignal.timeout(15000) }).catch(() => { throw new Error("Không tải được trạng thái phương tiện."); });
  if (!response.ok) throw new Error("Không tải được trạng thái phương tiện.");
  return await response.json() as Evaluation;
}

export type CsvPreview = components["schemas"]["CsvPreview"];
export type SavedSummary = components["schemas"]["SavedSummary"];
async function jsonRequest<T>(path: string, body?: unknown): Promise<T> {
  try {
    const response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers: body === undefined ? undefined : {"Content-Type":"application/json"}, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000)});
    if (!response.ok) throw new Error();
    return await response.json() as T;
  } catch { throw new Error("Không thể xử lý dữ liệu local; phương án đang mở được giữ nguyên."); }
}
export const previewCsv = (plan: Plan, csv_text: string) => jsonRequest<CsvPreview>("/api/import/csv/preview", {plan,csv_text});
export const saveSnapshot = (plan: Plan, name: string) => jsonRequest<SavedSummary>("/api/snapshots", {plan,name});
export type SnapshotListItem = components["schemas"]["SnapshotListItem"];
export const listSnapshots = () => jsonRequest<SnapshotListItem[]>("/api/snapshots");
export const openSnapshot = (id: string) => jsonRequest<Evaluation>(`/api/snapshots/${encodeURIComponent(id)}`);

export type PipeLibrary = components["schemas"]["PipeLibrary"];
export const getPipeLibrary = () => jsonRequest<PipeLibrary>("/api/pipe-list");
export const previewPipeList = (plan: Plan) => jsonRequest<Evaluation>("/api/pipe-list/preview",plan);

export type PlannerPreview = components["schemas"]["PlannerPreview"];
export const previewPlanner = (plan: Plan) => jsonRequest<PlannerPreview>("/api/planner/preview",plan);

export type CompareResult = components["schemas"]["CompareResult"];
export const comparePlans = (before: Plan, after: Plan) => jsonRequest<CompareResult>("/api/plans/compare",{before,after});

// Cargo revisions (SUP-02A). These calls surface the server's Vietnamese messages and per-change errors
// instead of a generic text, so the UI can show 409 ParentConflict and 400 RevisionRejected precisely.
export type RevisionList = components["schemas"]["RevisionList"];
export type RevisionSummary = components["schemas"]["RevisionSummary"];
export type RevisionDetail = components["schemas"]["RevisionDetail"];
export type RevisionGroup = components["schemas"]["RevisionGroup"];
export type ProvenanceStamp = components["schemas"]["ProvenanceStamp"];
export type RevisionDraft = components["schemas"]["RevisionDraft"];
export type RevisionPreview = components["schemas"]["RevisionPreview"];
export type RevisionRejected = components["schemas"]["RevisionRejected"];
export type ParentConflict = components["schemas"]["ParentConflict"];
export type BatchError = components["schemas"]["BatchError"];
export type RebaseResult = components["schemas"]["RebaseResult"];
export type DroppedPlacement = components["schemas"]["DroppedPlacement"];

export class RevisionApiError extends Error {
  status: number;
  errors: BatchError[];
  latestRevisionId: string | null;
  constructor(message: string, status: number, errors: BatchError[] = [], latestRevisionId: string | null = null) {
    super(message);
    this.name = "RevisionApiError";
    this.status = status;
    this.errors = errors;
    this.latestRevisionId = latestRevisionId;
  }
}

async function revisionRequest<T>(path: string, body?: unknown, fallback = "Không thể xử lý dữ liệu hàng; phương án đang mở được giữ nguyên.", post = body !== undefined): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {method: post ? "POST" : "GET", headers: body === undefined ? undefined : {"Content-Type":"application/json"}, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000)});
  } catch { throw new RevisionApiError(fallback, 0); }
  if (!response.ok) {
    let detail: unknown = null;
    try { detail = (await response.json() as {detail?: unknown}).detail; } catch { /* keep fallback */ }
    if (typeof detail === "string" && detail) throw new RevisionApiError(detail, response.status);
    if (detail && typeof detail === "object") {
      const d = detail as Partial<RevisionRejected & ParentConflict>;
      throw new RevisionApiError(typeof d.message === "string" && d.message ? d.message : fallback, response.status, Array.isArray(d.errors) ? d.errors : [], typeof d.latest_revision_id === "string" ? d.latest_revision_id : null);
    }
    if (response.status === 422) throw new RevisionApiError("Dữ liệu không đúng cấu trúc được hỗ trợ.", 422);
    throw new RevisionApiError(`${fallback} (HTTP ${response.status})`, response.status);
  }
  return await response.json() as T;
}
export const listCargoRevisions = () => revisionRequest<RevisionList>("/api/cargo-revisions", undefined, "Không đọc được danh sách revision dữ liệu hàng.");
export const getCargoRevision = (revisionId: string) => revisionRequest<RevisionDetail>(`/api/cargo-revisions/${encodeURIComponent(revisionId)}`, undefined, "Không đọc được revision dữ liệu hàng.");
export const previewCargoRevision = (draft: RevisionDraft) => revisionRequest<RevisionPreview>("/api/cargo-revisions/preview", draft, "Không xem trước được lô cập nhật.");
export const createCargoRevision = (draft: RevisionDraft) => revisionRequest<RevisionSummary>("/api/cargo-revisions", draft, "Không tạo được revision dữ liệu hàng.");
export const previewRevisionPlan = (revisionId: string, plan: Plan) => revisionRequest<Evaluation>(`/api/cargo-revisions/${encodeURIComponent(revisionId)}/plan-preview`, plan, "Không xem được list ống theo revision.");
export const rebaseSnapshot = (id: string) => revisionRequest<RebaseResult>(`/api/snapshots/${encodeURIComponent(id)}/rebase`, undefined, "Không tạo được bản theo dữ liệu mới.", true);
