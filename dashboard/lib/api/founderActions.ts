import type {
  CreateFounderActionRequest,
  FounderAction,
  UpdateFounderActionStatusRequest,
} from "@/types";

import { apiFetch } from "./client";

// Phase 7.3 -- Founder Progress & Improvement V1. Every call here
// requires a real Clerk session token, same pattern as
// lib/api/founder.ts -- the backend independently re-verifies
// startup_memberships on every request (RequireStartupMember); nothing
// here ever sends a user_id.

export function getFounderActions(
  startupId: number,
  token: string
): Promise<FounderAction[]> {
  return apiFetch<FounderAction[]>(`/founder/startups/${startupId}/actions`, {
    token,
  });
}

export function createFounderAction(
  startupId: number,
  request: CreateFounderActionRequest,
  token: string
): Promise<FounderAction> {
  return apiFetch<FounderAction>(`/founder/startups/${startupId}/actions`, {
    method: "POST",
    body: request,
    token,
  });
}

export function updateFounderActionStatus(
  startupId: number,
  actionId: number,
  request: UpdateFounderActionStatusRequest,
  token: string
): Promise<FounderAction> {
  return apiFetch<FounderAction>(
    `/founder/startups/${startupId}/actions/${actionId}`,
    {
      method: "PATCH",
      body: request,
      token,
    }
  );
}
