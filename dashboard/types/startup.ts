// Canonical Dashboard MVP: get_top_startups() now returns exactly
// get_rankings()'s rows (see app/database/db.py), which never include
// readiness_score -- that field was dropped, not just left unrendered
// (readiness_score has no defined numeric scale; see the P0 Product Trust
// Cleanup report).
export interface StartupRanking {
  company_name: string;
  industry: string;
  stage: string;
  overall_score: number;
}

export interface ImprovingStartup {
  company_name: string;
  first_score: number;
  latest_score: number;
  score_change: number;
}

export interface RankingEntry {
  id: number;
  company_name: string | null;
  industry: string | null;
  stage: string | null;
  business_model: string | null;
  overall_score: number | null;
  market_score: number | null;
  team_score: number | null;
  product_score: number | null;
  competition_score: number | null;
  traction_score: number | null;
  financial_score: number | null;
  recommendation: string | null;
  created_at: string;
}

export type ConfidenceLevel = "Low" | "Medium" | "High";

export type Evidence = {
  source?: string;
  text?: string;
  title?: string;
  url?: string;
};

export type Subscore = {
  name: string;
  score: number | null;
  weight: number;
  confidence?: ConfidenceLevel;
  evidence_status?: string;
  rationale?: string;
  evidence?: string[];
  recommendations?: string[];
  missing_information?: string[];
};

export type PillarScoreBreakdown = {
  pillar?: string;
  score?: number | null;
  confidence?: ConfidenceLevel;
  evidence_coverage?: number;
  scoring_summary?: string;
  subscores?: Subscore[];
};

export type PillarAnalysis = {
  score: number | null;
  confidence: ConfidenceLevel;
  summary: string;
  evidence: Array<Evidence | string>;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  score_breakdown: PillarScoreBreakdown;
};

export type SIEContext = {
  company_name: string;
  industry: string;
  business_model: string;
  company_stage: string;
  funding_stage: string;
};

// SIE Methodology v2, Part 9 item 6 (Blocker 3): a purely additive,
// display-only whole-pillar-coverage label -- never a math adjustment to
// startup_intelligence_score. Optional/nullable because analyses stored
// before this field existed have no key for it at all.
export type PartialStructuralCoverage = {
  partial_structural_coverage: boolean;
  pillars_unavailable_entirely: string[];
  note: string;
};

export type SIEMethodologyAnalysis = {
  context: SIEContext;

  market: PillarAnalysis;
  team: PillarAnalysis;
  product: PillarAnalysis;
  execution: PillarAnalysis;
  traction: PillarAnalysis;
  financial_health: PillarAnalysis;

  startup_intelligence_score: number;
  milestone_readiness_score: number;
  momentum_score: number;
  confidence_score: number;

  executive_coaching_summary: string;
  next_actions: string[];

  structural_coverage?: PartialStructuralCoverage | null;

  startup_scorecard?: unknown;
  analysis_context?: unknown;
};

export type StartupProfileResponse = {
  id: number;
  // Saved Startups (Watchlist Phase 1): the canonical Startup FK, additive
  // alongside `id` (which is the analysis id, not the startup id -- see
  // the backend's get_startup_by_name() docstring). null only for
  // historical rows that predate the write path; the Save control hides
  // itself rather than guessing an id to save.
  startup_id: number | null;
  created_at: string;
  methodology: SIEMethodologyAnalysis;
};

// Saved Startups (Watchlist Phase 1): GET /me/saved-startups row shape.
// Deliberately flat, mirroring RankingEntry -- every field is read fresh
// from the startup's current latest canonical analysis on every request,
// never a snapshot copied in at save time. industry/stage/overall_score/
// latest_analysis_at are null when the saved startup currently has no
// canonical analysis -- never fabricated.
export type SavedStartupEntry = {
  startup_id: number;
  company_name: string;
  industry: string | null;
  stage: string | null;
  overall_score: number | null;
  latest_analysis_at: string | null;
  saved_at: string;
};

export type SavedStartupStatus = {
  saved: boolean;
};

// One point per canonical (methodology-bearing) analysis, sourced from
// GET /startup/{company_name}/sps-history. Chronological order.
export type SPSHistoryPoint = {
  analysis_id: number;
  created_at: string;
  startup_intelligence_score: number;
};
