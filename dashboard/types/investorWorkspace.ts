// Phase 9 -- Investor Workspace V1. Mirrors app/models/investor_workspace.py
// exactly. This is a deterministic re-derivation of canonical intelligence
// already surfaced elsewhere (SPS, six pillar scores) -- never a second
// scoring system. See app/ai/investor_workspace.py's own module docstring
// for the full design record (thresholds, "needs attention" semantics).

export interface PillarChange {
  pillar: string;
  label: string;
  current_score: number | null;
  previous_score: number | null;
  delta: number | null;
  confidence: string | null;
  evidence_coverage: number | null;
}

export interface WatchedStartup {
  startup_id: number;
  company_name: string;
  industry: string | null;
  stage: string | null;
  saved_at: string;
  latest_analysis_at: string | null;
  has_canonical_analysis: boolean;
  has_multiple_analyses: boolean;
  current_sps: number | null;
  previous_sps: number | null;
  sps_delta: number | null;
  overall_confidence: string | null;
  is_stale: boolean;
  pillars: PillarChange[];
  attention_reasons: string[];
}

export interface RecentChange {
  startup_id: number;
  company_name: string;
  statement: string;
  magnitude: number;
  direction: "up" | "down";
}

export interface AttentionItem {
  startup_id: number;
  company_name: string;
  reason: string;
}

export interface InvestorOverview {
  watched_count: number;
  startups_with_analysis: number;
  average_current_sps: number | null;
  improved_count: number;
  declined_count: number;
  recently_analyzed_count: number;
}

export interface InvestorWorkspace {
  overview: InvestorOverview;
  watched_startups: WatchedStartup[];
  recent_changes: RecentChange[];
  attention_items: AttentionItem[];
}
