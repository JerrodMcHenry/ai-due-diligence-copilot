export interface StartupRanking {
  company_name: string;
  industry: string;
  stage: string;
  overall_score: number;
  readiness_score: number;
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

  startup_scorecard?: unknown;
  analysis_context?: unknown;
};

export type StartupProfileResponse = {
  id: number;
  created_at: string;
  methodology: SIEMethodologyAnalysis;
};

// One point per canonical (methodology-bearing) analysis, sourced from
// GET /startup/{company_name}/sps-history. Chronological order.
export type SPSHistoryPoint = {
  analysis_id: number;
  created_at: string;
  startup_intelligence_score: number;
};
