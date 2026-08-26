import type {
  CreateMilestoneRequest,
  StartupMilestone,
  UpdateMilestoneStatusRequest,
} from "@/types";

import { apiFetch } from "./client";

// Phase 7.4 -- Founder Evidence + Milestones V1.

export function getStartupMilestones(
  startupId: number,
  token: string
): Promise<StartupMilestone[]> {
  return apiFetch<StartupMilestone[]>(`/founder/startups/${startupId}/milestones`, {
    token,
  });
}

export function createStartupMilestone(
  startupId: number,
  request: CreateMilestoneRequest,
  token: string
): Promise<StartupMilestone> {
  return apiFetch<StartupMilestone>(`/founder/startups/${startupId}/milestones`, {
    method: "POST",
    body: request,
    token,
  });
}

export function updateMilestoneStatus(
  startupId: number,
  milestoneId: number,
  request: UpdateMilestoneStatusRequest,
  token: string
): Promise<StartupMilestone> {
  return apiFetch<StartupMilestone>(
    `/founder/startups/${startupId}/milestones/${milestoneId}`,
    {
      method: "PATCH",
      body: request,
      token,
    }
  );
}
