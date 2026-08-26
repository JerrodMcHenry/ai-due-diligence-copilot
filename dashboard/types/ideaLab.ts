// Idea Lab / Venture Simulator V1. Deliberately its own type family, not
// reusing SIEMethodologyAnalysis/ComparisonStartup -- a modeled venture is
// architecturally separate from a canonical Startup, and VPS is
// architecturally separate from SPS. See app/models/idea_lab.py's own
// docstring for the full reasoning.

export interface MarketAssumptions {
  market_description: string | null;
  estimated_market_size: string | null; // "Small" | "Medium" | "Large" | "Very Large"
  competition_intensity: string | null; // "Low" | "Medium" | "High"
}

export interface ProblemSolutionAssumptions {
  problem_statement: string | null;
  solution_description: string | null;
  differentiation: string | null;
}

export interface FounderAssumptions {
  founder_count: number | null;
  relevant_domain_experience_years: number | null;
  has_technical_cofounder: boolean | null;
  has_business_cofounder: boolean | null;
}

export interface GtmAssumptions {
  primary_acquisition_strategy: string | null;
  expected_cac: number | null;
}

export interface EconomicsAssumptions {
  pricing_model: string | null;
  price_point: number | null;
  expected_gross_margin_pct: number | null;
}

// Founder-REPORTED OBSERVATIONS, not modeled assumptions -- the one group
// VPS's Validation category scores from. See vps_scoring.py's own
// docstring for why this distinction is structural, not a per-field tag.
export interface ValidationObservations {
  customer_interviews: number | null;
  waitlist_signups: number | null;
  paying_customers: number | null;
  monthly_revenue: number | null;
}

export interface CapitalAssumptions {
  starting_capital: number | null;
  monthly_burn: number | null;
}

export interface VentureAssumptions {
  target_customer: string | null;
  market: MarketAssumptions;
  problem_solution: ProblemSolutionAssumptions;
  founder: FounderAssumptions;
  gtm: GtmAssumptions;
  economics: EconomicsAssumptions;
  validation: ValidationObservations;
  capital: CapitalAssumptions;
}

export function emptyAssumptions(): VentureAssumptions {
  return {
    target_customer: null,
    market: { market_description: null, estimated_market_size: null, competition_intensity: null },
    problem_solution: { problem_statement: null, solution_description: null, differentiation: null },
    founder: {
      founder_count: null,
      relevant_domain_experience_years: null,
      has_technical_cofounder: null,
      has_business_cofounder: null,
    },
    gtm: { primary_acquisition_strategy: null, expected_cac: null },
    economics: { pricing_model: null, price_point: null, expected_gross_margin_pct: null },
    validation: {
      customer_interviews: null,
      waitlist_signups: null,
      paying_customers: null,
      monthly_revenue: null,
    },
    capital: { starting_capital: null, monthly_burn: null },
  };
}

export interface VPSCategoryResult {
  key: string;
  label: string;
  score: number | null;
  basis: string[];
}

export interface VPSResult {
  vps: number | null;
  label: string; // "MODELED / ASSUMPTION-BASED"
  categories: VPSCategoryResult[];
  strengths: string[];
  risks: string[];
  key_assumptions: string[];
  validation_gaps: string[];
  next_milestones: string[];
}

export interface VentureResponse {
  id: number;
  name: string;
  description: string | null;
  industry: string | null;
  business_model: string | null;
  target_customer: string | null;
  stage: string | null;
  assumptions: VentureAssumptions;
  model_result: VPSResult | null;
  created_at: string;
  updated_at: string;
}

export interface VentureSummary {
  id: number;
  name: string;
  stage: string | null;
  vps: number | null;
  updated_at: string;
}

export interface CreateVentureRequest {
  name: string;
  description?: string | null;
  industry?: string | null;
  business_model?: string | null;
  target_customer?: string | null;
  stage?: string | null;
  assumptions: VentureAssumptions;
}

export interface ScenarioCompareResponse {
  current: VPSResult;
  modified: VPSResult;
}

export const VENTURE_STAGES = ["Idea", "Researching", "Validating", "Building", "Launched"] as const;
