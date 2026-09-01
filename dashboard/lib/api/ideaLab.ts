import type {
  CreateVentureRequest,
  ScenarioCompareResponse,
  StructureIdeaResponse,
  VentureAssumptions,
  VentureHistoryResponse,
  VentureResponse,
  VentureSummary,
} from "@/types";

import { apiFetch } from "./client";

// Idea Lab / Venture Simulator V1. Every call here requires a real Clerk
// session token, same pattern as lib/api/savedStartups.ts -- modeled
// ventures are private user data, never public intelligence.

// Phase 6.1: stateless -- creates nothing, computes no VPS. See POST
// /ventures/structure-idea's own docstring in app/api.py.
export function structureIdea(
  description: string,
  token: string
): Promise<StructureIdeaResponse> {
  return apiFetch<StructureIdeaResponse>("/ventures/structure-idea", {
    method: "POST",
    body: { description },
    token,
  });
}

export function listVentures(token: string): Promise<VentureSummary[]> {
  return apiFetch<VentureSummary[]>("/ventures", { token });
}

export function getVenture(id: number, token: string): Promise<VentureResponse> {
  return apiFetch<VentureResponse>(`/ventures/${id}`, { token });
}

export function createVenture(
  request: CreateVentureRequest,
  token: string
): Promise<VentureResponse> {
  return apiFetch<VentureResponse>("/ventures", {
    method: "POST",
    body: request,
    token,
  });
}

export function updateVenture(
  id: number,
  request: CreateVentureRequest,
  token: string
): Promise<VentureResponse> {
  return apiFetch<VentureResponse>(`/ventures/${id}`, {
    method: "PUT",
    body: request,
    token,
  });
}

// Phase 16 -- Founder Progress / Venture History V1.
export function getVentureHistory(id: number, token: string): Promise<VentureHistoryResponse> {
  return apiFetch<VentureHistoryResponse>(`/ventures/${id}/history`, { token });
}

export function deleteVenture(id: number, token: string): Promise<{ deleted: boolean }> {
  return apiFetch<{ deleted: boolean }>(`/ventures/${id}`, {
    method: "DELETE",
    token,
  });
}

export function compareVentureScenarios(
  currentAssumptions: VentureAssumptions,
  modifiedAssumptions: VentureAssumptions,
  token: string
): Promise<ScenarioCompareResponse> {
  return apiFetch<ScenarioCompareResponse>("/ventures/scenario-compare", {
    method: "POST",
    body: {
      current_assumptions: currentAssumptions,
      modified_assumptions: modifiedAssumptions,
    },
    token,
  });
}
