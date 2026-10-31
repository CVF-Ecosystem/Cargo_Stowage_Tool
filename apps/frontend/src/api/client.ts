import type { Evaluation, Plan } from "../features/model";

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
    data.plan?.contract_version !== "scst.m1.v1" ||
    data.plan.source !== "SYNTHETIC"
  )
    throw new Error("Phiên bản dữ liệu API không tương thích.");
  return data;
}
