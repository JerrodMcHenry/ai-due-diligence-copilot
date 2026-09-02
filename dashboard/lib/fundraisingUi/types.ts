// Phase 21B -- Fundraising Simulator V1, UI-facing transformation layer.
//
// This layer translates founder-friendly, plain-`number` UI input (dollar
// amounts, ownership percentages) into calls against the Phase 21A engine
// (dashboard/lib/fundraising/*.ts) and translates the engine's exact
// Rational/bigint results back into founder-readable strings. It contains
// NO financing math of its own -- every ownership/dilution/SAFE/runway
// number is computed by the frozen Phase 21A engine; this file only
// converts units (dollars <-> cents, percent <-> synthetic share basis)
// and formats output. See docs/methodology/FUNDRAISING_SIMULATION_V1_SPEC.md.
//
// Zero "@/..." alias imports -- importable directly by plain Node (see
// tests/fundraisingUi.test.ts), matching lib/fundraising/*.ts's own
// convention.

export type StakeholderRole = "founder" | "cofounder" | "employee_pool" | "existing_investor" | "other";

export const STAKEHOLDER_ROLE_LABELS: Record<StakeholderRole, string> = {
  founder: "Founder",
  cofounder: "Cofounder",
  employee_pool: "Employee / option pool",
  existing_investor: "Existing investor",
  other: "Other",
};

// A row in the ephemeral starting-ownership builder (Part 5/6). `percent`
// is 0-100; across all rows in a scenario these must sum to exactly 100
// before a scenario can run -- see startingCapTable.ts::validateOwnershipPercentages().
export interface UiStakeholder {
  readonly id: string;
  readonly name: string;
  readonly role: StakeholderRole;
  readonly percent: number;
}

export interface UiSafeTerm {
  readonly id: string;
  readonly holderName: string;
  readonly investmentDollars: number;
  readonly valuationCapDollars: number;
}

export interface UiPricedRoundTerm {
  readonly name: string;
  readonly preMoneyDollars: number;
  readonly newMoneyDollars: number;
  readonly newInvestorName: string;
}

export type FundraisingPath = "safe" | "priced_round" | "safe_then_round";

export interface RunwayTerms {
  readonly cashOnHandDollars: number | null;
  readonly monthlyBurnDollars: number | null;
}

export interface ScenarioInput {
  readonly startingStakeholders: readonly UiStakeholder[];
  readonly path: FundraisingPath;
  readonly safes: readonly UiSafeTerm[];
  readonly pricedRound: UiPricedRoundTerm | null;
  // Part 10: an option-pool increase expressed as a percentage of the
  // CURRENT (pre-round) fully diluted share count -- NOT a target
  // percentage of the post-money cap table (that form is unsupported;
  // see the spec doc's Limitations). This is purely UI sugar over the
  // engine's own supported absolute-share-count input: the equivalent
  // share count is computed directly from the already-known pre-round
  // total, with no circular solve. 0 (the default) means no pool change.
  readonly optionPoolIncreasePercentOfCurrent: number;
  readonly runway: RunwayTerms | null;
}

export interface OwnershipRow {
  readonly id: string;
  readonly name: string;
  readonly role: StakeholderRole | "safe" | "investor";
  readonly beforePercent: string; // "70.00%", or "—" if the stakeholder didn't exist yet
  readonly afterPercent: string;
  readonly pointChange: string | null; // "-11.60%" or null if not applicable (new stakeholder)
  readonly percentDilution: string | null; // "16.57%" or null if not applicable
}

export interface TraceStep {
  readonly label: string;
  readonly detail: string;
}

export interface RunwaySummary {
  readonly currentLabel: string; // "18 months" | "Runway not modeled"
  readonly postFinancingLabel: string;
  readonly note: string;
}

export interface ScenarioSuccess {
  readonly kind: "success";
  readonly isEstimateOnly: boolean; // Part 18: true for a standalone (unconverted) SAFE
  readonly startingOwnership: OwnershipRow[];
  readonly finalOwnership: OwnershipRow[];
  readonly capitalRaisedLabel: string;
  readonly founderDilution: { readonly pointChange: string; readonly percentDilution: string } | null;
  readonly trace: TraceStep[];
  readonly detailedCapTable: { readonly name: string; readonly shares: string; readonly ownership: string }[];
  readonly runway: RunwaySummary | null;
  readonly warnings: string[];
}

// Part 9: when the engine's own priceWarnings fire, the UI must not
// present an authoritative ownership result -- this is a distinct result
// shape from ScenarioSuccess, not a flag on it, so a caller cannot
// accidentally render ownership numbers in this case.
export interface ScenarioBlocked {
  readonly kind: "blocked";
  readonly reason: string;
  readonly warnings: string[];
}

// A caller-fixable input problem (validation failure or an engine
// FinancingError on nonsensical input) -- never silently normalized.
export interface ScenarioInvalid {
  readonly kind: "invalid";
  readonly message: string;
}

export type ScenarioResult = ScenarioSuccess | ScenarioBlocked | ScenarioInvalid;
