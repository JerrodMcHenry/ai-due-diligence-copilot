// Phase 31 -- Venture -> Startup Graduation V1, Part 2/3. Pure,
// deterministic, zero I/O -- same discipline as this directory's other
// resolvers (inferVentureStage.ts, resolveIdeaLabNextStep.ts). This is
// the ENTIRE "is this venture ready to graduate?" check: no AI call, no
// VPS score, no new score of any kind. It reads exactly the two
// founder-REPORTED OBSERVATION fields (see idea_lab.py's own
// ValidationObservations docstring for why these two -- not modeled
// assumptions -- are the only fields honest enough to gate a real-world
// suggestion) that already exist on every venture's assumptions.
//
// This is a SUGGESTION, never a gate: VentureGraduation.tsx renders a
// manual "Create Startup Profile" control regardless of what this
// function returns (Part 3's own "graduation may remain manually
// accessible without a suggestion") -- eligible=true only changes
// whether that control also gets a more prominent placement/framing.
//
// Not imported from "@/types" on purpose -- zero "@/..." alias imports
// here, same as inferVentureStage.ts, so this stays trivially runnable
// by plain `node` in a script or test.
type MinimalValidation = {
  paying_customers: number | null;
  monthly_revenue: number | null;
};

export function isEligibleForGraduationSuggestion(validation: MinimalValidation | null): boolean {
  if (!validation) {
    return false;
  }

  const hasPayingCustomers = validation.paying_customers !== null && validation.paying_customers > 0;
  const hasRevenue = validation.monthly_revenue !== null && validation.monthly_revenue > 0;

  return hasPayingCustomers || hasRevenue;
}
