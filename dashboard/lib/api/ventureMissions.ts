import type { CreateMissionRequest, MissionStatus, VentureMission } from "@/types";

import { apiFetch } from "./client";

// Phase 10.7 -- Founder Missions V1. Every call here requires a real
// Clerk session token, same as lib/api/ideaLab.ts -- missions belong to a
// modeled venture, never public. Deliberately a separate file/module from
// ideaLab.ts, mirroring founderActions.ts being separate from founder.ts:
// missions are a distinct resource with their own lifecycle, even though
// they're nested under a venture's own id.

export function listVentureMissions(ventureId: number, token: string): Promise<VentureMission[]> {
  return apiFetch<VentureMission[]>(`/ventures/${ventureId}/missions`, { token });
}

export function createVentureMission(
  ventureId: number,
  request: CreateMissionRequest,
  token: string
): Promise<VentureMission> {
  return apiFetch<VentureMission>(`/ventures/${ventureId}/missions`, {
    method: "POST",
    body: request,
    token,
  });
}

export function updateVentureMissionStatus(
  ventureId: number,
  missionId: number,
  status: MissionStatus,
  token: string
): Promise<VentureMission> {
  return apiFetch<VentureMission>(`/ventures/${ventureId}/missions/${missionId}/status`, {
    method: "PATCH",
    body: { status },
    token,
  });
}

export function recordVentureMissionLearning(
  ventureId: number,
  missionId: number,
  learningSummary: string,
  token: string
): Promise<VentureMission> {
  return apiFetch<VentureMission>(`/ventures/${ventureId}/missions/${missionId}/learning`, {
    method: "POST",
    body: { learning_summary: learningSummary },
    token,
  });
}

// Phase 23 -- Universal Founder Capture V1. "Save what happened" -- one
// call, POST /ventures/{id}/capture, which atomically creates + records
// learning on + completes a venture_missions row server-side (see
// app/database/db.py::capture_venture_observation()'s own docstring for
// why this is a composition of the three calls above, not a new
// architecture). Returns the same VentureMission shape every mission
// call already returns.
export function captureVentureObservation(
  ventureId: number,
  text: string,
  category: string | null,
  token: string
): Promise<VentureMission> {
  return apiFetch<VentureMission>(`/ventures/${ventureId}/capture`, {
    method: "POST",
    body: { text, category },
    token,
  });
}
