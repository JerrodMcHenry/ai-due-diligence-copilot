import type {
  CreateFinancialCommitmentRequest,
  CreateFinancialPlanRequest,
  CreateFinancialSnapshotRequest,
  CreateHirePlanRequest,
  CreateScenarioRequest,
  FinancialCommitmentComparisonResponse,
  FinancialCommitmentResponse,
  FinancialHistoryResponse,
  FinancialPlan,
  FinancialPlanImpactPreview,
  HireImpactPreview,
  HirePlan,
  HirePlanStatus,
  PlanStatus,
  Scenario,
  UpdateFinancialCommitmentExplanationRequest,
  VentureFinancialsResponse,
} from "@/types";

import { apiFetch } from "./client";

// Phase 35B -- Financial State Persistence + Runway Engine V1. Same
// pattern as lib/api/buildIntelligence.ts -- every call requires a real
// Clerk session token; these resources belong to a modeled venture,
// never public.

export function getVentureFinancials(ventureId: number, token: string): Promise<VentureFinancialsResponse> {
  return apiFetch<VentureFinancialsResponse>(`/ventures/${ventureId}/financials`, { token });
}

export function createVentureFinancialSnapshot(
  ventureId: number,
  request: CreateFinancialSnapshotRequest,
  token: string
): Promise<VentureFinancialsResponse> {
  return apiFetch<VentureFinancialsResponse>(`/ventures/${ventureId}/financials`, {
    method: "POST",
    body: request,
    token,
  });
}

export function getVentureFinancialHistory(ventureId: number, token: string): Promise<FinancialHistoryResponse> {
  return apiFetch<FinancialHistoryResponse>(`/ventures/${ventureId}/financials/history`, { token });
}

// --- Phase 35C -- Hiring + Operating Plan Engine V1 -------------------------

export function createHirePlan(ventureId: number, request: CreateHirePlanRequest, token: string): Promise<HirePlan> {
  return apiFetch<HirePlan>(`/ventures/${ventureId}/hire-plans`, { method: "POST", body: request, token });
}

export function listHirePlans(ventureId: number, token: string): Promise<HirePlan[]> {
  return apiFetch<HirePlan[]>(`/ventures/${ventureId}/hire-plans`, { token });
}

export function updateHirePlan(
  ventureId: number,
  hirePlanId: number,
  fields: Partial<CreateHirePlanRequest> & { status?: HirePlanStatus },
  token: string
): Promise<HirePlan> {
  return apiFetch<HirePlan>(`/ventures/${ventureId}/hire-plans/${hirePlanId}`, { method: "PATCH", body: fields, token });
}

// NEVER persists (Phase 35C §17: PERSISTED PLAN vs. TEMPORARY COMPARISON)
// -- used both for "see financial impact before saving" and for the
// hire-now-vs-later comparison (called twice with different start dates).
export function previewHirePlan(
  ventureId: number,
  request: CreateHirePlanRequest,
  token: string,
  excludeHirePlanId?: number
): Promise<HireImpactPreview> {
  const query = excludeHirePlanId !== undefined ? `?exclude_hire_plan_id=${excludeHirePlanId}` : "";
  return apiFetch<HireImpactPreview>(`/ventures/${ventureId}/hire-plans/preview${query}`, {
    method: "POST",
    body: request,
    token,
  });
}

// --- Phase 35D -- Operating Scenarios + Financial Plan Reconciliation V1 ---

export function createFinancialPlan(ventureId: number, request: CreateFinancialPlanRequest, token: string): Promise<FinancialPlan> {
  return apiFetch<FinancialPlan>(`/ventures/${ventureId}/financial-plans`, { method: "POST", body: request, token });
}

export function listFinancialPlans(ventureId: number, token: string): Promise<FinancialPlan[]> {
  return apiFetch<FinancialPlan[]>(`/ventures/${ventureId}/financial-plans`, { token });
}

export function updateFinancialPlan(
  ventureId: number,
  planId: number,
  fields: Partial<CreateFinancialPlanRequest> & { status?: PlanStatus },
  token: string
): Promise<FinancialPlan> {
  return apiFetch<FinancialPlan>(`/ventures/${ventureId}/financial-plans/${planId}`, { method: "PATCH", body: fields, token });
}

// NEVER persists -- same discipline as previewHirePlan().
export function previewFinancialPlan(
  ventureId: number,
  request: CreateFinancialPlanRequest,
  token: string,
  excludePlanId?: number
): Promise<FinancialPlanImpactPreview> {
  const query = excludePlanId !== undefined ? `?exclude_plan_id=${excludePlanId}` : "";
  return apiFetch<FinancialPlanImpactPreview>(`/ventures/${ventureId}/financial-plans/preview${query}`, {
    method: "POST",
    body: request,
    token,
  });
}

export function listScenarios(ventureId: number, token: string): Promise<Scenario[]> {
  return apiFetch<Scenario[]>(`/ventures/${ventureId}/scenarios`, { token });
}

export function createScenario(ventureId: number, request: CreateScenarioRequest, token: string): Promise<Scenario> {
  return apiFetch<Scenario>(`/ventures/${ventureId}/scenarios`, { method: "POST", body: request, token });
}

export function updateScenario(
  ventureId: number,
  scenarioId: number,
  fields: Partial<CreateScenarioRequest>,
  token: string
): Promise<Scenario> {
  return apiFetch<Scenario>(`/ventures/${ventureId}/scenarios/${scenarioId}`, { method: "PATCH", body: fields, token });
}

export function deleteScenario(ventureId: number, scenarioId: number, token: string): Promise<{ deleted: boolean }> {
  return apiFetch<{ deleted: boolean }>(`/ventures/${ventureId}/scenarios/${scenarioId}`, { method: "DELETE", token });
}

// §16: founder-controlled model bookkeeping, never a verification gate --
// the founder's own yes/no answer is recorded verbatim.
export function reconcileFinancialPlan(
  ventureId: number,
  planKind: "hire" | "financial",
  planId: number,
  included: boolean,
  token: string
): Promise<VentureFinancialsResponse> {
  return apiFetch<VentureFinancialsResponse>(`/ventures/${ventureId}/financials/reconcile`, {
    method: "POST",
    body: { plan_kind: planKind, plan_id: planId, included },
    token,
  });
}

// --- Phase 38D-A -- Financial Commitment Persistence + Frozen Expectation
// V1. Nothing here is ever recomputed or updated -- there is no
// update/delete client function, matching the append-only backend by
// design (see docs/product/SIE_COMMITTED_PLAN_LEARNING_ARCHITECTURE_V1.md).

export function createFinancialCommitment(
  ventureId: number,
  request: CreateFinancialCommitmentRequest,
  token: string
): Promise<FinancialCommitmentResponse> {
  return apiFetch<FinancialCommitmentResponse>(`/ventures/${ventureId}/financial-commitments`, {
    method: "POST",
    body: request,
    token,
  });
}

export function listFinancialCommitments(ventureId: number, token: string): Promise<FinancialCommitmentResponse[]> {
  return apiFetch<FinancialCommitmentResponse[]>(`/ventures/${ventureId}/financial-commitments`, { token });
}

export function getFinancialCommitment(
  ventureId: number,
  commitmentId: number,
  token: string
): Promise<FinancialCommitmentResponse> {
  return apiFetch<FinancialCommitmentResponse>(`/ventures/${ventureId}/financial-commitments/${commitmentId}`, { token });
}

// --- Phase 38D-B -- Committed Expectation vs Actual V1 ----------------------
// A pure read -- never persists anything, never mutates the commitment.

export function getFinancialCommitmentComparison(
  ventureId: number,
  commitmentId: number,
  token: string
): Promise<FinancialCommitmentComparisonResponse> {
  return apiFetch<FinancialCommitmentComparisonResponse>(
    `/ventures/${ventureId}/financial-commitments/${commitmentId}/comparison`,
    { token }
  );
}

// --- Phase 38D-C -- Founder Explanation + Learning Capture V1 ---------------
// Update-in-place -- the ONLY write path for founder_explanation. Never
// touches plan_snapshot/expected_monthly/committed_at/source_snapshot_id
// (see update_venture_financial_commitment_explanation_for_owner()'s own
// docstring, app/database/db.py). The backend rejects (409) a commitment
// still "awaiting_actuals" -- this function does not pre-check that
// itself, the UI gate + the backend's own rejection are the guard.

export function updateFinancialCommitmentExplanation(
  ventureId: number,
  commitmentId: number,
  request: UpdateFinancialCommitmentExplanationRequest,
  token: string
): Promise<FinancialCommitmentResponse> {
  return apiFetch<FinancialCommitmentResponse>(
    `/ventures/${ventureId}/financial-commitments/${commitmentId}/explanation`,
    { method: "PATCH", body: request, token }
  );
}
