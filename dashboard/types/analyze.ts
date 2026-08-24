import type { SIEContext } from "./startup";

// Matches app.models.startup.StartupAnalysisResponse. context.company_name
// is the one field the Analyze page actually depends on (to redirect to
// the persisted Startup Profile) -- startup_scorecard/methodology are
// typed unknown here on purpose: the Analyze page never renders them
// itself, the Startup Profile page re-fetches and renders the canonical
// analysis independently after redirect (see app/analyze/page.tsx).
export interface AnalyzeStartupResponse {
  context: SIEContext;
  startup_scorecard?: unknown;
  methodology?: unknown;
}
