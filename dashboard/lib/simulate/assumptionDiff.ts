// Simulate V1, Part 5/10: "Display clearly: CURRENT versus SCENARIO...
// Do not bury the assumptions beneath the score." Before this phase,
// ScenarioComparison only ever showed the resulting VPSResult (scores) --
// the actual before/after ASSUMPTION VALUES that produced those scores
// were never surfaced anywhere in the comparison itself. This is the one
// new piece of logic that closes that gap: a small, fixed, explicit diff
// over exactly the fields any preset (whatIfScenarios.ts) or the new
// custom-scenario form can change -- not a generic deep-diff utility.
//
// Zero imports -- plain-`node`-testable, same discipline as
// whatIfScenarios.ts and this directory's other pure files.
type MinimalAssumptions = {
  market: { competition_intensity: string | null };
  founder: { has_technical_cofounder: boolean | null; has_business_cofounder: boolean | null };
  gtm: { expected_cac: number | null };
  economics: { price_point: number | null; expected_gross_margin_pct: number | null };
  validation: {
    customer_interviews: number | null;
    paying_customers: number | null;
    monthly_revenue: number | null;
    retention_pct: number | null;
  };
};

export type AssumptionDiffRow = {
  key: string;
  label: string;
  before: string;
  after: string;
};

// Part 18: "If current CAC is unknown, do not show $0 -> $50. Show Not
// known -> $50." Every formatter below routes null through this same
// honest label -- never a fabricated zero, never blank.
const UNKNOWN_LABEL = "Not known";

function formatCurrency(value: number | null): string {
  return value === null ? UNKNOWN_LABEL : `$${value.toLocaleString()}`;
}

function formatCount(value: number | null): string {
  return value === null ? UNKNOWN_LABEL : value.toLocaleString();
}

function formatPercent(value: number | null): string {
  return value === null ? UNKNOWN_LABEL : `${value}%`;
}

function formatBoolean(value: boolean | null): string {
  if (value === null) return UNKNOWN_LABEL;
  return value ? "Yes" : "No";
}

function formatText(value: string | null): string {
  return value === null || value.trim() === "" ? UNKNOWN_LABEL : value;
}

// Generic over the value type so one row-builder handles numbers,
// booleans, and strings identically -- callers below just supply the
// right formatter per field.
function row<T>(key: string, label: string, before: T, after: T, format: (value: T) => string): AssumptionDiffRow | null {
  if (before === after) {
    return null;
  }
  return { key, label, before: format(before), after: format(after) };
}

// Every field any existing preset (whatIfScenarios.ts) or the new
// custom-scenario form can change -- fixed and explicit, not a reflective
// walk over the whole VentureAssumptions object. Only fields that
// actually differ are returned, in a stable, founder-relevant order
// (Part 6's own A-E ordering: pricing, traction, CAC, economics,
// retention, then the two remaining preset-only fields).
export function diffScenarioAssumptions(
  current: MinimalAssumptions,
  scenario: MinimalAssumptions
): AssumptionDiffRow[] {
  const rows: (AssumptionDiffRow | null)[] = [
    row("price_point", "Price", current.economics.price_point, scenario.economics.price_point, formatCurrency),
    row(
      "paying_customers",
      "Paying customers",
      current.validation.paying_customers,
      scenario.validation.paying_customers,
      formatCount
    ),
    row("expected_cac", "Customer acquisition cost", current.gtm.expected_cac, scenario.gtm.expected_cac, formatCurrency),
    row(
      "expected_gross_margin_pct",
      "Gross margin",
      current.economics.expected_gross_margin_pct,
      scenario.economics.expected_gross_margin_pct,
      formatPercent
    ),
    row("retention_pct", "Retention", current.validation.retention_pct, scenario.validation.retention_pct, formatPercent),
    row(
      "customer_interviews",
      "Customer interviews",
      current.validation.customer_interviews,
      scenario.validation.customer_interviews,
      formatCount
    ),
    row("monthly_revenue", "Monthly revenue", current.validation.monthly_revenue, scenario.validation.monthly_revenue, formatCurrency),
    row(
      "competition_intensity",
      "Competition intensity",
      current.market.competition_intensity,
      scenario.market.competition_intensity,
      formatText
    ),
    row(
      "has_technical_cofounder",
      "Technical cofounder",
      current.founder.has_technical_cofounder,
      scenario.founder.has_technical_cofounder,
      formatBoolean
    ),
    row(
      "has_business_cofounder",
      "Business cofounder",
      current.founder.has_business_cofounder,
      scenario.founder.has_business_cofounder,
      formatBoolean
    ),
  ];

  return rows.filter((entry): entry is AssumptionDiffRow => entry !== null);
}
