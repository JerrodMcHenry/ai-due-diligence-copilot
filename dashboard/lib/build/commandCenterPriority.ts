// Phase 38B -- Founder Command Center V1
// (docs/product/SIE_FOUNDER_COMMAND_CENTER_V1.md is the governing spec).
//
// Pure, deterministic, zero I/O -- same discipline as this codebase's
// other journey resolvers (lib/journey/inferVentureStage.ts,
// resolveGraduationEligibility.ts). This is the ENTIRE "should Finance
// take the page's own 'what matters now' slot instead of Build?" check.
//
// Section 22 of the 38B directive is explicit: if the repository does
// not already establish an objective financial-urgency threshold, do
// not invent one. Read directly: app/ai/financial_engine.py's own
// compute_derived_metrics() produces exactly five status values
// (insufficient_data, cash_flow_positive, break_even, burning,
// out_of_cash), and FinanceOverview.tsx's own STATUS_COPY mapping gives
// "burning" the SAME tone regardless of how much runway remains -- there
// is no existing "short runway" bucket, at any number of months, this
// function could point to without choosing that number itself. The only
// bucket the product has already, objectively, labeled distinctly
// dangerous is "out_of_cash" (cash at or below zero while burn is
// positive) -- a fact, not a threshold. That is the only condition this
// function treats as a financial override.
//
// Not exported as a broader "priority resolver": Build's own priority
// (current_question vs. recommendation, contradiction-aware) is entirely
// CurrentQuestionCard's/build_recommendation.py's existing business
// logic, untouched and unduplicated here.
//
// Deliberately not imported from "@/types" -- zero "@/..." alias imports
// here, same discipline as this directory's sibling resolvers, so this
// stays trivially runnable by plain `node` in a script or test. The real
// DerivedFinancialMetrics type (dashboard/types/finance.ts) satisfies
// this shape by construction wherever it's passed in from a "use client"
// component.
type MinimalDerivedMetrics = {
  status: string;
};

export function isFinancialConstraintActive(derived: MinimalDerivedMetrics | null): boolean {
  return derived?.status === "out_of_cash";
}
