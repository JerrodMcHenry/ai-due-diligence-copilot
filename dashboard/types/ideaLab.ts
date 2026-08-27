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

// Phase 6.1 -- AI-Assisted Idea Setup. Every leaf value the AI proposes
// carries its own provenance so the review UI can render "Based on your
// description" / "Modeled assumption" / "Not provided yet" instead of
// presenting everything with equal, unearned confidence. See
// app/models/idea_lab.py's own docstring -- validation fields are held
// to a stricter backend-enforced contract than this type alone can
// express (a value here with provenance "ai_inferred" under `validation`
// should never occur; the backend guarantees it, this type doesn't).
export type DraftProvenance = "user_provided" | "ai_inferred" | "unknown";

export interface DraftField<T> {
  value: T | null;
  provenance: DraftProvenance;
  source_quote: string | null;
}

export interface VentureDraft {
  name: DraftField<string>;
  industry: DraftField<string>;
  business_model: DraftField<string>;
  target_customer: DraftField<string>;
  stage: DraftField<string>;
  market: {
    market_description: DraftField<string>;
    estimated_market_size: DraftField<string>;
    competition_intensity: DraftField<string>;
  };
  problem_solution: {
    problem_statement: DraftField<string>;
    solution_description: DraftField<string>;
    differentiation: DraftField<string>;
  };
  founder: {
    founder_count: DraftField<number>;
    relevant_domain_experience_years: DraftField<number>;
    has_technical_cofounder: DraftField<boolean>;
    has_business_cofounder: DraftField<boolean>;
  };
  gtm: {
    primary_acquisition_strategy: DraftField<string>;
    expected_cac: DraftField<number>;
  };
  economics: {
    pricing_model: DraftField<string>;
    price_point: DraftField<number>;
    expected_gross_margin_pct: DraftField<number>;
  };
  validation: {
    customer_interviews: DraftField<number>;
    waitlist_signups: DraftField<number>;
    paying_customers: DraftField<number>;
    monthly_revenue: DraftField<number>;
  };
  capital: {
    starting_capital: DraftField<number>;
    monthly_burn: DraftField<number>;
  };
}

export interface StructureIdeaResponse {
  draft: VentureDraft;
}

// Converts a VentureDraft (every field is a {value, provenance} pair)
// into a plain VentureAssumptions the founder can edit and eventually
// submit to POST /ventures -- provenance is UI-only from this point on;
// the persisted venture only ever stores plain values, same as a
// manually-filled-in venture always has.
export function draftToAssumptions(draft: VentureDraft): VentureAssumptions {
  return {
    target_customer: draft.target_customer.value,
    market: {
      market_description: draft.market.market_description.value,
      estimated_market_size: draft.market.estimated_market_size.value,
      competition_intensity: draft.market.competition_intensity.value,
    },
    problem_solution: {
      problem_statement: draft.problem_solution.problem_statement.value,
      solution_description: draft.problem_solution.solution_description.value,
      differentiation: draft.problem_solution.differentiation.value,
    },
    founder: {
      founder_count: draft.founder.founder_count.value,
      relevant_domain_experience_years: draft.founder.relevant_domain_experience_years.value,
      has_technical_cofounder: draft.founder.has_technical_cofounder.value,
      has_business_cofounder: draft.founder.has_business_cofounder.value,
    },
    gtm: {
      primary_acquisition_strategy: draft.gtm.primary_acquisition_strategy.value,
      expected_cac: draft.gtm.expected_cac.value,
    },
    economics: {
      pricing_model: draft.economics.pricing_model.value,
      price_point: draft.economics.price_point.value,
      expected_gross_margin_pct: draft.economics.expected_gross_margin_pct.value,
    },
    validation: {
      customer_interviews: draft.validation.customer_interviews.value,
      waitlist_signups: draft.validation.waitlist_signups.value,
      paying_customers: draft.validation.paying_customers.value,
      monthly_revenue: draft.validation.monthly_revenue.value,
    },
    capital: {
      starting_capital: draft.capital.starting_capital.value,
      monthly_burn: draft.capital.monthly_burn.value,
    },
  };
}

export const VENTURE_STAGES = ["Idea", "Researching", "Validating", "Building", "Launched"] as const;

// Phase 10.7 -- Founder Missions V1. Mirrors app/models/venture_missions.py
// exactly. A mission is an ACTIVITY -- nothing in this shape can carry a
// number into VentureAssumptions.validation; `learning_summary` is
// free-text reflection only. See VentureMission's own comment below.
export type MissionType =
  | "customer_discovery"
  | "validation"
  | "pricing"
  | "gtm"
  | "product"
  | "founder"
  | "economics"
  | "other";

export type MissionSource = "vps_guidance" | "founder_created";

export type MissionStatus = "active" | "completed" | "dismissed";

export interface VentureMission {
  id: number;
  venture_id: number;
  created_by_user_id: string;
  title: string;
  description: string | null;
  mission_type: MissionType;
  related_category: string | null;
  source: MissionSource;
  source_ref: string | null;
  status: MissionStatus;
  learning_summary: string | null;
  learning_recorded_at: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface CreateMissionRequest {
  title: string;
  description?: string | null;
  mission_type?: MissionType;
  related_category?: string | null;
  source?: MissionSource;
}
