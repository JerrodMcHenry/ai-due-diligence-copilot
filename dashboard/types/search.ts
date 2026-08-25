// Superseded by Startup Discovery V1 (DiscoveryResult below) as of the
// /search page redesign -- kept because GET /analyses/search still exists
// and works server-side, in case a future page wants free-text document
// search again. No component currently uses this.
export interface StartupSearchResult {
  company_name: string | null;
  summary: string | null;
  overall_score: number | null;
}

// Startup Discovery V1 -- GET /discover row shape. Deliberately flat,
// mirroring SavedStartupEntry/RankingEntry. Every field is read fresh from
// that startup's current latest canonical analysis on every request, never
// a stale snapshot. Pillar fields are null when that pillar was
// Unavailable on the underlying analysis -- never fabricated.
export interface DiscoveryResult {
  startup_id: number;
  company_name: string;
  industry: string | null;
  stage: string | null;
  business_model: string | null;
  overall_score: number | null;
  market_score: number | null;
  team_score: number | null;
  product_score: number | null;
  execution_score: number | null;
  traction_score: number | null;
  financial_score: number | null;
  created_at: string;
}

export interface DiscoveryResponse {
  total: number;
  results: DiscoveryResult[];
}

// Startup Discovery V1, Part 4: option lists derived from the real
// canonical population -- never a hardcoded taxonomy. See
// get_discovery_filter_options()'s own docstring.
export interface DiscoveryFilterOptions {
  industries: string[];
  stages: string[];
  business_models: string[];
}

export type DiscoverySort = "sps_desc" | "sps_asc" | "newest" | "name_asc";

// Mirrors app/database/db.py's discover_startups() parameter shape --
// every field optional and additive. Kept as a single object so the page,
// the API wrapper, and the URL-state sync all share one shape.
export interface DiscoveryFilters {
  query?: string;
  industry?: string;
  stage?: string;
  business_model?: string;
  min_sps?: number;
  max_sps?: number;
  min_market?: number;
  min_team?: number;
  min_product?: number;
  min_execution?: number;
  min_traction?: number;
  min_financial_health?: number;
  sort?: DiscoverySort;
  limit?: number;
  offset?: number;
}
