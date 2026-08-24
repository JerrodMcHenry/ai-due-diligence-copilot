// Canonical Dashboard MVP: get_analytics() now returns exactly these two
// fields, both computed from the canonical (Rankings) population --
// average_readiness_score was dropped, not just left unrendered
// (readiness_score has no defined numeric scale; see the P0 Product Trust
// Cleanup report). average_overall_score is nullable because it's None
// when zero canonical startups exist yet.
export interface AnalyticsSummary {
  total_startups: number;
  average_overall_score: number | null;
}
