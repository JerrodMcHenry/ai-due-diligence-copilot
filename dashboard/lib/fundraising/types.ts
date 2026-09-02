// Phase 21A -- Fundraising Simulation, Part 6 (canonical cap-table input
// model). Typed in-memory models ONLY -- no persistence, no database
// tables, no API routes. See docs/methodology/FUNDRAISING_SIMULATION_V1_SPEC.md
// for the full methodology these types implement.
//
// Money is always integer CENTS (bigint). Share counts are always integer
// SHARES (bigint). Neither is ever a floating-point `number` -- see
// rational.ts's own docstring for why.

import type { Rational } from "./rational.ts";

export type Cents = bigint;
export type Shares = bigint;

export type StakeholderKind = "founder" | "option_pool" | "safe" | "investor" | "other";

// One row of a cap table: how many shares one stakeholder holds.
export interface StakeholderPosition {
  readonly id: string;
  readonly name: string;
  readonly kind: StakeholderKind;
  readonly shares: Shares;
}

// The company's fully diluted cap table at one point in time. `stakeholders`
// is the single source of truth -- total shares is always DERIVED as their
// sum (see capTable.ts::totalShares), never tracked separately, which is
// what makes the ownership invariant (Part 18) hold by construction rather
// than by post-hoc checking.
export interface CapTableState {
  readonly label: string; // e.g. "State 0", "After Seed"
  readonly stakeholders: readonly StakeholderPosition[];
}

// V1-supported instrument: a post-money SAFE with a valuation cap.
// Discount-only and MFN-only SAFEs are recognized by this shape
// (valuationCapCents may be null) but are REJECTED at conversion time
// with a clear error -- see safe.ts -- because V1 has not independently
// validated their conversion math against a primary-source worked
// example. See the V1 SUPPORTED/UNSUPPORTED section of the spec doc.
export interface SafeInput {
  readonly id: string;
  readonly holderName: string;
  readonly investmentCents: Cents;
  readonly valuationCapCents: Cents | null;
  readonly discountPercent: Rational | null; // e.g. 0.2 == 20% discount
}

// V1-supported instrument: a priced equity round. `optionPoolIncreaseShares`
// is an ABSOLUTE share count -- V1 does NOT solve the "target % pool
// post-financing" form (that requires a simultaneous circular solve with
// price-per-share; deferred, see spec doc Limitations).
export interface PricedRoundInput {
  readonly id: string;
  readonly name: string;
  readonly preMoneyValuationCents: Cents;
  readonly newMoneyCents: Cents;
  readonly optionPoolIncreaseShares: Shares;
  readonly newInvestorName: string;
}

export interface RunwayInput {
  readonly cashOnHandCents: Cents;
  readonly monthlyBurnCents: Cents;
}
