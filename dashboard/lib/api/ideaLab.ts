import type {
  CreateVentureRequest,
  ScenarioCompareResponse,
  StructureIdeaResponse,
  UpdateVentureShareRequest,
  VentureAssumptions,
  VentureHistoryResponse,
  VentureResponse,
  VentureShareSettings,
  VentureSnapshotResponse,
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

// Phase 27 -- Shareable Venture Snapshot V1. These three, unlike every
// other function in this file, are NOT all founder-only: getVentureShare/
// updateVentureShare/getVentureSharePreview require a token (owner-only,
// same as every other venture endpoint); getPublicVentureSnapshot
// deliberately takes NO token at all -- it is THE public, unauthenticated
// route, and passing no `token` to apiFetch already omits the
// Authorization header entirely (see lib/api/client.ts).

export function getVentureShare(id: number, token: string): Promise<VentureShareSettings> {
  return apiFetch<VentureShareSettings>(`/ventures/${id}/share`, { token });
}

export function updateVentureShare(
  id: number,
  request: UpdateVentureShareRequest,
  token: string
): Promise<VentureShareSettings> {
  return apiFetch<VentureShareSettings>(`/ventures/${id}/share`, {
    method: "PUT",
    body: request,
    token,
  });
}

export function getVentureSharePreview(id: number, token: string): Promise<VentureSnapshotResponse> {
  return apiFetch<VentureSnapshotResponse>(`/ventures/${id}/share/preview`, { token });
}

// THE public call -- no token, callable from the public /v/[publicId]
// page with zero Clerk session in scope.
export function getPublicVentureSnapshot(publicId: string): Promise<VentureSnapshotResponse> {
  return apiFetch<VentureSnapshotResponse>(`/ventures/share/${publicId}`);
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
