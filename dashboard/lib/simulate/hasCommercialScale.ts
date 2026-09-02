// Simulate V1. The one shared definition of "commercial scale" -- SIE
// Intelligence Reset's own threshold, previously duplicated inline inside
// components/idea-lab/whatIfScenarios.ts's own getWhatIfScenarios(). Moved
// here so that file and the new custom-scenario builder (Part 6E: "only
// where the current model actually has a meaningful retention concept")
// share exactly one definition instead of two copies that could drift.
// Zero imports -- stays plain-`node`-testable, same discipline as every
// other pure file in this directory family.
export function hasCommercialScale(payingCustomers: number | null, monthlyRevenue: number | null): boolean {
  return (payingCustomers !== null && payingCustomers >= 10) || (monthlyRevenue !== null && monthlyRevenue >= 10_000);
}
