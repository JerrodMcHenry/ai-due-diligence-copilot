// Simulate V1, Part 8/9/21 -- CLASS A (directly calculable) consequences
// ONLY. Every value here is plain arithmetic over assumptions the founder
// (or the scenario they're previewing) directly controls -- never an
// invented relationship (elasticity, churn response, demand curves).
// Part 9's own worked example is the exact shape this module produces:
// "If you reached 50 paying customers at your current $199 monthly
// price, modeled monthly revenue would be approximately $9,950." -- an
// "if/then" scenario calculation, never asserted as a prediction.
//
// Deliberately narrow: Part 6 scopes V1 to price/customers/CAC/margin/
// retention, and of those, only price x paying_customers has an
// unambiguous, business-model-agnostic arithmetic meaning (a recurring
// per-customer charge). CAC, margin, and retention do NOT get a Class A
// calculation here -- there is no safe, universal formula connecting them
// to a single output number without assuming things about the business
// this module has no basis for (e.g. LTV needs a retention-derived
// customer lifetime, which is itself a modeling choice, not arithmetic).
// Those stay purely in the VPS/category preview (Class B) instead.
//
// Zero imports -- plain-`node`-testable, same discipline as this
// directory's other pure files.
type MinimalAssumptions = {
  economics: { price_point: number | null };
  validation: { paying_customers: number | null };
};

export type DirectConsequence = {
  key: string;
  label: string;
  // The full "if/then" sentence -- Part 9's own framing, never a bare
  // number presented as fact.
  explanation: string;
};

export function computeDirectConsequences(assumptions: MinimalAssumptions): DirectConsequence[] {
  const price = assumptions.economics.price_point;
  const customers = assumptions.validation.paying_customers;

  // Both must be real, positive numbers -- Part 8: "If validity cannot
  // be established, do not calculate it." Zero customers or a zero/
  // negative price would produce a technically-correct but useless
  // "$0/month," which reads as a broken feature rather than an honest
  // "not enough to calculate" state.
  if (price === null || customers === null || price <= 0 || customers <= 0) {
    return [];
  }

  const monthlyRevenue = price * customers;
  const annualRevenue = monthlyRevenue * 12;

  return [
    {
      key: "modeled_monthly_revenue",
      label: "Modeled monthly revenue",
      explanation: `If ${customers.toLocaleString()} customers each pay $${price.toLocaleString()}, that's a modeled $${monthlyRevenue.toLocaleString()}/month. This assumes a simple recurring per-customer price -- it may not match your actual pricing model.`,
    },
    {
      key: "modeled_annual_revenue",
      label: "Modeled annual revenue (ARR)",
      explanation: `Annualized, that's a modeled $${annualRevenue.toLocaleString()}/year.`,
    },
  ];
}
