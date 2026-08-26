import type {
  CreateFounderUpdateRequest,
  EditFounderUpdateRequest,
  FounderUpdate,
} from "@/types";

import { apiFetch } from "./client";

// Phase 7.4 -- Founder Evidence + Milestones V1. Every call here
// requires a real Clerk session token, same pattern as
// lib/api/founderActions.ts. The backend independently re-verifies
// startup_memberships on every request (RequireStartupMember); nothing
// here ever sends a user_id.

export function getFounderUpdates(
  startupId: number,
  token: string
): Promise<FounderUpdate[]> {
  return apiFetch<FounderUpdate[]>(`/founder/startups/${startupId}/updates`, {
    token,
  });
}

export function createFounderUpdate(
  startupId: number,
  request: CreateFounderUpdateRequest,
  token: string
): Promise<FounderUpdate> {
  return apiFetch<FounderUpdate>(`/founder/startups/${startupId}/updates`, {
    method: "POST",
    body: request,
    token,
  });
}

export function editFounderUpdate(
  startupId: number,
  updateId: number,
  request: EditFounderUpdateRequest,
  token: string
): Promise<FounderUpdate> {
  return apiFetch<FounderUpdate>(
    `/founder/startups/${startupId}/updates/${updateId}`,
    {
      method: "PATCH",
      body: request,
      token,
    }
  );
}
