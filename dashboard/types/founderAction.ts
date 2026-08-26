// Phase 7.3 -- Founder Progress & Improvement V1. Mirrors
// app/models/founder_action.py exactly. founder_actions is pure workflow
// state -- it never influences, and is never influenced by, SPS/
// Methodology v2. created_by_user_id is provenance only: any verified
// member of the startup can see and act on every action (the plan is
// shared per-startup, not private per-member).

export type FounderActionStatus = "todo" | "in_progress" | "completed" | "dismissed";
export type FounderActionSource = "sie_recommendation" | "founder_created";

export interface FounderAction {
  id: number;
  startup_id: number;
  created_by_user_id: string;
  title: string;
  description: string | null;
  related_pillar: string | null;
  status: FounderActionStatus;
  source: FounderActionSource;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface CreateFounderActionRequest {
  title: string;
  description?: string | null;
  related_pillar?: string | null;
  source?: FounderActionSource;
}

export interface UpdateFounderActionStatusRequest {
  status: FounderActionStatus;
}
