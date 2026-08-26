import type {
  CreateVentureRequest,
  ScenarioCompareResponse,
  VentureAssumptions,
  VentureResponse,
  VentureSummary,
} from "@/types";

import { apiFetch } from "./client";

// Idea Lab / Venture Simulator V1. Every call here requires a real Clerk
// session token, same pattern as lib/api/savedStartups.ts -- modeled
// ventures are private user data, never public intelligence.

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
