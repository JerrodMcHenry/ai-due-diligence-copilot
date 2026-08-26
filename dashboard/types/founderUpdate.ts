// Phase 7.4 -- Founder Evidence + Milestones V1. Mirrors
// app/models/founder_update.py exactly. Every row here is
// FOUNDER-REPORTED record -- distinct from canonical, LLM-extracted
// Evidence (used inside PillarAnalysis) and from FounderAction
// (something intended, not something reported as having happened).
// Never automatically becomes canonical evidence or changes SPS.

export type FounderUpdateType =
  | "customer"
  | "revenue"
  | "product"
  | "team"
  | "fundraising"
  | "partnership"
  | "validation"
  | "operations"
  | "other";

export interface FounderUpdate {
  id: number;
  startup_id: number;
  created_by_user_id: string;
  update_type: FounderUpdateType;
  title: string;
  description: string | null;
  related_pillar: string | null;
  metric_name: string | null;
  metric_value: number | null;
  metric_unit: string | null;
  occurred_at: string;
  created_at: string;
  updated_at: string;
}

export interface FounderUpdateRequestFields {
  update_type: FounderUpdateType;
  title: string;
  description?: string | null;
  related_pillar?: string | null;
  occurred_at: string;
  metric_name?: string | null;
  metric_value?: number | null;
  metric_unit?: string | null;
}

export type CreateFounderUpdateRequest = FounderUpdateRequestFields;
// Full-field correction, same shape as create (Part 13) -- see
// app/models/founder_update.py's own UpdateFounderUpdateRequest.
export type EditFounderUpdateRequest = FounderUpdateRequestFields;
