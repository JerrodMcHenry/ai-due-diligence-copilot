// Phase 7.4 -- Founder Evidence + Milestones V1. Mirrors
// app/models/startup_milestone.py exactly.

export type MilestoneStatus = "planned" | "in_progress" | "achieved" | "cancelled";

export interface StartupMilestone {
  id: number;
  startup_id: number;
  created_by_user_id: string;
  title: string;
  description: string | null;
  related_pillar: string | null;
  status: MilestoneStatus;
  target_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateMilestoneRequest {
  title: string;
  description?: string | null;
  related_pillar?: string | null;
  target_date?: string | null;
}

export interface UpdateMilestoneStatusRequest {
  status: MilestoneStatus;
}
