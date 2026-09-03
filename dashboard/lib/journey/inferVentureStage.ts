// Founder Loop V2, Section 10. Pure, deterministic, zero I/O -- same
// discipline as this directory's other resolvers (resolveIdeaLabNextStep,
// resolveRecentLearning). NOT a new score: this never calls the backend
// scoring function and produces only an INDEX into the existing 5-step
// VENTURE_JOURNEY_STEP_IDS the venture journey stepper (VentureJourney.tsx)
// already renders -- the shared founderJourney.ts vocabulary and its
// labels are completely unchanged.
//
// Why this exists: the stepper used to derive its active step SOLELY from
// the founder's manually-set `stage` dropdown (VENTURE_STAGES) -- a value
// that defaults to "Idea", is easy to forget to update, and silently
// falls back to index 0 ("Idea") for any string that doesn't map onto
// the shared vocabulary at all. A real, confirmed example found during
// this phase's own investigation: a venture with $840K ARR and 14 paying
// customers whose `stage` had been set to a free-typed value the fixed
// VENTURE_STAGE_TO_JOURNEY_STAGE lookup doesn't recognize rendered as
// "stuck at Idea" -- exactly the failure mode Section 10 named.
//
// The fix is additive, not a replacement: this function infers an index
// from the venture's own MODELED EVIDENCE (assumptions + validation
// observations), and the caller takes the MORE ADVANCED of (the
// founder's explicit manual stage, this inferred index) -- so evidence
// can rescue a stale/default/unmapped manual selection, but a founder's
// own explicit, further-along choice (e.g. "Launched") is never
// overridden or walked backward. "Fundraise" (the final step) is
// deliberately NEVER auto-inferred here, only reachable via the
// founder's own explicit stage -- Section 10's own point that fundraising
// isn't every venture's destination, so evidence of traction alone
// should never imply it.
// A structural subset of VentureAssumptions -- only the fields this
// function actually reads. Deliberately not imported from "@/types" (zero
// "@/..." alias imports here, same discipline as this directory's other
// resolvers), so this stays trivially runnable by plain `node`; the real
// VentureAssumptions type satisfies this shape by construction wherever
// it's passed in from a "use client" component.
type MinimalAssumptions = {
  market: { estimated_market_size: string | null; competition_intensity: string | null; market_description: string | null };
  problem_solution: { problem_statement: string | null; solution_description: string | null };
  founder: { founder_count: number | null };
  gtm: { primary_acquisition_strategy: string | null };
  economics: { pricing_model: string | null };
  validation: {
    customer_interviews: number | null;
    waitlist_signups: number | null;
    paying_customers: number | null;
    monthly_revenue: number | null;
  };
};

export function inferEvidenceStepIndex(assumptions: MinimalAssumptions | null): number {
  if (!assumptions) {
    return 0;
  }

  const validation = assumptions.validation;
  const hasRealTraction =
    (validation.paying_customers !== null && validation.paying_customers > 0) ||
    (validation.monthly_revenue !== null && validation.monthly_revenue > 0);

  if (hasRealTraction) {
    return 3; // Build -- real customers/revenue already exist.
  }

  const hasValidationSignal =
    (validation.customer_interviews !== null && validation.customer_interviews > 0) ||
    (validation.waitlist_signups !== null && validation.waitlist_signups > 0);

  if (hasValidationSignal) {
    return 2; // Experiment -- testing assumptions against reality.
  }

  const hasAnyModeledAssumption =
    Boolean(assumptions.market.estimated_market_size) ||
    Boolean(assumptions.market.competition_intensity) ||
    Boolean(assumptions.market.market_description) ||
    Boolean(assumptions.problem_solution.problem_statement) ||
    Boolean(assumptions.problem_solution.solution_description) ||
    assumptions.founder.founder_count !== null ||
    Boolean(assumptions.gtm.primary_acquisition_strategy) ||
    Boolean(assumptions.economics.pricing_model);

  if (hasAnyModeledAssumption) {
    return 1; // Model -- assumptions exist, no real-world signal yet.
  }

  return 0; // Idea -- mostly hypothesis.
}

// The step index the stepper should actually highlight: whichever of
// (the founder's explicit manual stage, the evidence-inferred index) is
// FURTHER ALONG. `manualIndex` is -1 when the founder's `stage` doesn't
// map onto the shared vocabulary at all (unset, or a nonstandard value) --
// treated as "no signal from the manual field," not as index 0, so it
// never wins a tie against real evidence by construction.
export function resolveVentureStepIndex(manualIndex: number, assumptions: MinimalAssumptions | null): number {
  const evidenceIndex = inferEvidenceStepIndex(assumptions);
  return Math.max(manualIndex, evidenceIndex);
}

// Founder Experience Model correction, Part 4. The 5-position stepper
// index above (0-4, "fundraise" included via a founder's own manual
// "Launched" selection) is now re-presented as ONE OF THREE plain-
// language DESCRIPTIONS of where a venture appears to stand -- not
// unlockable levels, and never a claim the venture must have passed
// through the others in order (Part 3's own explicit instruction: no
// staircase). Deliberately reuses this file's own existing, already-
// tested resolveVentureStepIndex()/inferEvidenceStepIndex() rather than
// inventing a second inference system -- this is a display BUCKETING of
// the same evidence, not a new score:
//   - 0 or 1 (no evidence yet, or modeled assumptions only) -> "idea":
//     still defining the problem, customer, solution, and assumptions.
//   - 2 (customer interviews or waitlist signups reported) -> "validating":
//     testing whether those assumptions are true against real evidence.
//   - 3 or 4 (real paying customers/revenue, or a founder-set "Launched")
//     -> "building": executing against increasingly validated assumptions.
// "Fundraise" is deliberately NOT its own state here (Part 3/5's own
// instruction: fundraising is a tool, never entrepreneurship's
// destination, and is never implied by traction alone) -- a founder who
// has actually raised still reads as "building," which remains true
// regardless of financing history.
export type VentureStateId = "idea" | "validating" | "building";

export interface VentureStateInfo {
  id: VentureStateId;
  label: string;
  description: string;
}

export const VENTURE_STATES: Record<VentureStateId, VentureStateInfo> = {
  idea: {
    id: "idea",
    label: "Idea",
    description: "Defining the problem, customer, solution, and the assumptions that matter most.",
  },
  validating: {
    id: "validating",
    label: "Validating",
    description: "Testing whether the important assumptions are true against real-world evidence.",
  },
  building: {
    id: "building",
    label: "Building",
    description: "Executing against increasingly validated assumptions and tracking real progress.",
  },
};

export function resolveVentureState(manualIndex: number, assumptions: MinimalAssumptions | null): VentureStateInfo {
  const stepIndex = resolveVentureStepIndex(manualIndex, assumptions);
  if (stepIndex >= 3) return VENTURE_STATES.building;
  if (stepIndex === 2) return VENTURE_STATES.validating;
  return VENTURE_STATES.idea;
}
