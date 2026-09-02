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
  // SIE Intelligence Reset. Same founder-reported-observation status as
  // every other field here -- see app/models/idea_lab.py's own comment.
  prior_monthly_revenue: number | null;
  retention_pct: number | null;
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
      prior_monthly_revenue: null,
      retention_pct: null,
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

// Founder Loop V2, Section 7 ("Path to 8"). See
// app/ai/vps_guidance.py::_path_to_stronger()'s own docstring -- a
// currently-scored, below-threshold category plus a deterministic,
// template-driven hint. Never carries a projected/fabricated score.
export interface PathToStrongerItem {
  key: string;
  label: string;
  score: number;
  hint: string;
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
  path_to_stronger: PathToStrongerItem[];
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
  // Founder Progress / Venture History V1. Only meaningful (and only
  // ever sent) on an UPDATE (updateVenture() reuses this same request
  // shape) -- see MissionsSection.tsx's own handleUpdateModel() for the
  // one call site that sets it. Ignored by the backend on create.
  related_mission_id?: number | null;
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
    prior_monthly_revenue: DraftField<number>;
    retention_pct: DraftField<number>;
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
      prior_monthly_revenue: draft.validation.prior_monthly_revenue.value,
      retention_pct: draft.validation.retention_pct.value,
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

// Phase 11 -- Pitch Deck Coach V2, Part 13: "pitch_deck_coach" added
// alongside the existing two values -- a mission a founder explicitly
// created from a deck review's "Make this a mission" button. See
// app/models/venture_missions.py::MissionSource for the matching backend
// widen.
export type MissionSource = "vps_guidance" | "founder_created" | "pitch_deck_coach";

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
  // Phase 11, Part 14: a playbook slug (dashboard/content/playbooks), or
  // null when nothing maps cleanly. The first real use of this
  // long-reserved field -- see app/database/db.py's
  // create_venture_mission() docstring.
  resource_ref: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

// ---------------------------------------------------------------------------
// Phase 16 -- Founder Progress / Venture History V1. Mirrors
// app/models/idea_lab.py's own VentureHistory* models exactly. A small,
// closed set of event types -- not a generic event envelope.
// ---------------------------------------------------------------------------

export type VentureHistoryEventType =
  | "venture_created"
  | "action_added"
  | "learning_recorded"
  | "action_completed"
  | "model_updated";

export interface VentureHistoryCategoryChange {
  key: string;
  label: string;
  before: number | null;
  after: number | null;
}

// Phase 24 -- Weekly Founder Review V1, Part 7. Already-formatted
// before/after strings (see app/api.py::_diff_assumption_changes() for
// the curated field list and formatting rule) -- never a raw value the
// frontend would need per-field formatting knowledge to display.
export interface VentureHistoryAssumptionChange {
  field_path: string;
  label: string;
  before: string;
  after: string;
}

export interface VentureHistoryEvent {
  event_type: VentureHistoryEventType;
  occurred_at: string;
  title: string;
  description: string | null;
  before_vps: number | null;
  after_vps: number | null;
  category_changes: VentureHistoryCategoryChange[];
  assumption_changes: VentureHistoryAssumptionChange[];
  mission_id: number | null;
  mission_title: string | null;
}

export interface VentureHistoryResponse {
  events: VentureHistoryEvent[];
  current_vps: number | null;
  started_at: string;
  actions_completed: number;
  model_updates_count: number;
  strongest_improvement: VentureHistoryCategoryChange | null;
}

export interface CreateMissionRequest {
  title: string;
  description?: string | null;
  mission_type?: MissionType;
  related_category?: string | null;
  source?: MissionSource;
  resource_ref?: string | null;
}
