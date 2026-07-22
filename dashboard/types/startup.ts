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
