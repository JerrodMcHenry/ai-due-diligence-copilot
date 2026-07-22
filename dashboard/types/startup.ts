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
