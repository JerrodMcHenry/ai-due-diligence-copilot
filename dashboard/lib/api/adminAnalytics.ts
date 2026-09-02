import { apiFetch } from "./client";

// Phase 28 -- Product Analytics & Growth Measurement V1, Part 13. A
// separate, small file rather than folding into lib/api/ideaLab.ts --
// this is a genuinely different concern (aggregate, admin-only
// reporting, never a per-founder venture operation), matching this
// directory's own one-file-per-concern convention.
export type AnalyticsReport = {
  north_star: {
    window_days: number;
    active_ventures: number;
  };
  activation: {
    window_days: number;
    ventures_created: number;
    activated: number;
    activation_rate: number | null;
  };
  retention: {
    lookback_days: number;
    cohort_unit: string;
    activated_cohort_size: number;
    w1_retention: number | null;
    d1_retention: number | null;
    d7_retention: number | null;
    d30_retention: number | null;
  };
  meaningful_building_days: {
    window_days: number;
    meaningful_building_days: number;
    active_ventures: number;
    building_days_per_active_venture: number | null;
  };
  engagement: {
    window_days: number;
    captures: number;
    actions_completed: number;
    active_ventures: number;
    captures_per_active_venture: number | null;
    actions_completed_per_active_venture: number | null;
  };
  distribution: {
    window_days: number;
    activated_ventures: number;
    snapshots_enabled: number;
    share_activation_rate: number | null;
    snapshot_links_copied: number;
    public_snapshot_views: number;
    snapshot_cta_clicks: number;
    snapshot_cta_click_rate: number | null;
    ventures_created_from_snapshot: number;
    snapshot_to_venture_creation_rate: number | null;
  };
};

// Admin-only -- GET /admin/analytics is gated server-side by RequireAdmin
// (app/auth.py's existing ADMIN_USER_IDS allowlist, unchanged from Phase
// 7.1A). A non-admin's token still gets a real 403 from the backend; this
// function does no client-side authorization of its own.
export function getAdminAnalytics(windowDays: number, token: string): Promise<AnalyticsReport> {
  return apiFetch<AnalyticsReport>(`/admin/analytics?window_days=${windowDays}`, { token });
}
