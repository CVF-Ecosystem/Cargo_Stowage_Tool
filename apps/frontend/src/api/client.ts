import type { Evaluation, Plan } from "../features/model";
import type { components } from "./generated/api";
export type VesselProfile = components["schemas"]["VesselProfile"];

// Vessel profiles (SUP-02B). Types come from the generated contract; the profile body is a loose object there,
// so VesselProfileV1 mirrors the backend's scst.vessel-profile.v1 shape and ProfileDetail.profile is cast to it.
export type ProfileDetail = components["schemas"]["ProfileDetail"];
export type ProfileListItem = components["schemas"]["ProfileListItem"];
export type ProfilePreview = components["schemas"]["ProfilePreview"];
export type ProfileVersionConflict = components["schemas"]["ProfileVersionConflict"];
export type ProfileError = components["schemas"]["ProfileError"];
export type Verification = components["schemas"]["Verification"];
export type LandmarkCheck = components["schemas"]["LandmarkCheck"];
export type BoundsCheck = components["schemas"]["BoundsCheck"];
export type ViewerBlock = components["schemas"]["ViewerBlock"];
export type FieldStatus = "ESTIMATED" | "SOURCED" | "MEASURED";
export type VesselProfileV1 = {
  contract_version: "scst.vessel-profile.v1";
  id: string;
  version: number;
  name: string;
  registration: string;
  dimensions_m: { length: number; beam: number; depth: number };
  hold: { id: string; name: string; length_mm: number; width_mm: number; height_mm: number; status: FieldStatus };
  cases: { id: string; cargo_mass_g: number; draft_m: number; deadweight_t?: number | null; freeboard_mm?: number | null }[];
  notes: string[];
  provenance: {
    source_documents: { title: string; sha256?: string | null }[];
    field_status: { dimensions_m: FieldStatus; hold: FieldStatus; cases: FieldStatus };
  };
  transform: { translation_m: number[]; yaw_deg: number };
  landmarks: { name: string; glb_m: number[]; hold_mm: number[] }[];
  hull_mesh_names?: string[];
};
export type ProfileUpload = { profile: Record<string, unknown>; glb_base64: string };
// The contract types the profile body as a loose object; this is the single place that narrows it.
export const profileBody = (detail: ProfileDetail) => detail.profile as unknown as VesselProfileV1;

const NETWORK_ERROR = "Không kết nối được backend. Thử lại khi backend sẵn sàng.";
const UPLOAD_TIMEOUT_MS = 60000;

// Server-side Vietnamese failures: 409 {message, latest_version}, 413 {message, errors}, 400 {message} or a preview payload.
export class ProfileApiError extends Error {
  status: number;
  errors: ProfileError[];
  latestVersion: number | null;
  constructor(message: string, status: number, errors: ProfileError[] = [], latestVersion: number | null = null) {
    super(message);
    this.name = "ProfileApiError";
    this.status = status;
    this.errors = errors;
    this.latestVersion = latestVersion;
  }
}

async function readDetail(response: Response): Promise<unknown> {
  try {
    return ((await response.json()) as { detail?: unknown }).detail;
  } catch {
    return undefined;
  }
}

function errorFrom(detail: unknown, status: number, fallback: string): ProfileApiError {
  if (typeof detail === "string" && detail) return new ProfileApiError(detail, status);
  if (detail && typeof detail === "object") {
    const d = detail as { message?: unknown; errors?: unknown; latest_version?: unknown };
    const errors = Array.isArray(d.errors) ? (d.errors as ProfileError[]) : [];
    const latest = typeof d.latest_version === "number" ? d.latest_version : null;
    if (typeof d.message === "string" && d.message) return new ProfileApiError(d.message, status, errors, latest);
    if (errors.length) return new ProfileApiError(fallback, status, errors, latest);
  }
  return new ProfileApiError(`${fallback} (HTTP ${status})`, status);
}

async function profileGet<T>(path: string, fallback: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { signal: AbortSignal.timeout(15000) });
  } catch {
    throw new ProfileApiError(NETWORK_ERROR, 0);
  }
  if (!response.ok) throw errorFrom(await readDetail(response), response.status, fallback);
  return (await response.json()) as T;
}

export const listVesselProfiles = () => profileGet<ProfileListItem[]>("/api/vessel-profiles", "Không đọc được danh sách tàu.");
export const getVesselProfile = (id: string, version: number) =>
  profileGet<ProfileDetail>(`/api/vessel-profiles/${encodeURIComponent(id)}/${version}`, `Không đọc được hồ sơ tàu ${id} phiên bản ${version}.`);

// VINAFCO268 keeps its legacy route (byte-identical responses); other profiles use the profile route.
export async function requestProfileCasePlan(profile: { id: string; version: number }, caseId: string): Promise<Evaluation> {
  if (profile.id === "VINAFCO268") return requestVesselPlan(caseId);
  const path = `/api/vessel-profiles/${encodeURIComponent(profile.id)}/${profile.version}/cases/${encodeURIComponent(caseId)}/plan`;
  let response: Response;
  try {
    response = await fetch(path, { signal: AbortSignal.timeout(15000) });
  } catch {
    throw new Error("Không tải được trạng thái phương tiện.");
  }
  if (!response.ok) {
    const detail = await readDetail(response);
    const message = detail && typeof detail === "object" ? (detail as { message?: unknown }).message : detail;
    throw new Error(typeof message === "string" && message ? message : "Không tải được trạng thái phương tiện.");
  }
  return (await response.json()) as Evaluation;
}

// Preview never writes. A 400 answer carries the whole preview payload in `detail`, so it is returned, not thrown.
export async function previewVesselProfile(body: ProfileUpload): Promise<ProfilePreview> {
  let response: Response;
  try {
    response = await fetch("/api/vessel-profiles/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(UPLOAD_TIMEOUT_MS),
    });
  } catch {
    throw new ProfileApiError(NETWORK_ERROR, 0);
  }
  if (response.ok) {
    try {
      return (await response.json()) as ProfilePreview;
    } catch {
      throw new ProfileApiError("Phản hồi kiểm profile không đọc được.", response.status);
    }
  }
  const detail = await readDetail(response);
  if (response.status === 400 && detail && typeof detail === "object" && typeof (detail as Partial<ProfilePreview>).valid === "boolean")
    return detail as ProfilePreview;
  throw errorFrom(detail, response.status, "Không xem trước được profile tàu.");
}

export async function createVesselProfile(body: ProfileUpload): Promise<ProfileListItem> {
  let response: Response;
  try {
    response = await fetch("/api/vessel-profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(UPLOAD_TIMEOUT_MS),
    });
  } catch {
    throw new ProfileApiError(NETWORK_ERROR, 0);
  }
  if (response.ok) return (await response.json()) as ProfileListItem;
  const detail = await readDetail(response);
  if (response.status === 400 && detail && typeof detail === "object" && Array.isArray((detail as ProfilePreview).errors)) {
    const errors = (detail as ProfilePreview).errors;
    const verification = (detail as ProfilePreview).verification;
    const message = errors.length
      ? "Hồ sơ hoặc GLB chưa hợp lệ; chưa ghi gì."
      : verification?.result === "FAIL"
        ? "Kiểm landmark hoặc hộp bao GLB không đạt; chưa ghi gì."
        : "Không tạo được profile tàu; chưa ghi gì.";
    throw new ProfileApiError(message, 400, errors, null);
  }
  throw errorFrom(detail, response.status, "Không tạo được profile tàu; chưa ghi gì.");
}

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

// Printable plan report (M2d). Read-only model derived from a saved snapshot; errors carry the server's Vietnamese detail.
export type PlanReport = components["schemas"]["PlanReport"];
export async function getPlanReport(id: string): Promise<PlanReport> {
  let response: Response;
  try {
    response = await fetch(`/api/snapshots/${encodeURIComponent(id)}/report`, { signal: AbortSignal.timeout(15000) });
  } catch {
    throw new Error(NETWORK_ERROR);
  }
  if (!response.ok) {
    const detail = await readDetail(response);
    const message = detail && typeof detail === "object" ? (detail as { message?: unknown }).message : detail;
    throw new Error(typeof message === "string" && message ? message : `Không đọc được báo cáo phương án (HTTP ${response.status}).`);
  }
  return (await response.json()) as PlanReport;
}

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
