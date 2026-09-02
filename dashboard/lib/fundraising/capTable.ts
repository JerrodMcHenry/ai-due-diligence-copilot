// Phase 21A -- Fundraising Simulation, Part 6/18 (canonical model +
// ownership invariant).

import type { CapTableState, Shares, StakeholderPosition } from "./types.ts";
import { type Rational, RAT_ZERO, makeRational } from "./rational.ts";
import { FinancingError } from "./errors.ts";

// Total fully diluted shares is always DERIVED from the stakeholder list,
// never tracked as a separate field -- this is what makes the Part 18
// ownership invariant (sum of ownership == exactly 100%) hold by
// construction, not by a post-hoc approximate check.
export function totalShares(state: CapTableState): Shares {
  return state.stakeholders.reduce((sum, s) => sum + s.shares, BigInt(0));
}

export function ownershipOf(state: CapTableState, stakeholderId: string): Rational {
  const total = totalShares(state);
  if (total === BigInt(0)) return RAT_ZERO;
  const pos = state.stakeholders.find((s) => s.id === stakeholderId);
  if (!pos) return RAT_ZERO;
  return makeRational(pos.shares, total);
}

export interface OwnershipRow {
  readonly id: string;
  readonly name: string;
  readonly kind: StakeholderPosition["kind"];
  readonly shares: Shares;
  readonly ownership: Rational;
}

export function ownershipBreakdown(state: CapTableState): OwnershipRow[] {
  const total = totalShares(state);
  return state.stakeholders.map((s) => ({
    id: s.id,
    name: s.name,
    kind: s.kind,
    shares: s.shares,
    ownership: total === BigInt(0) ? RAT_ZERO : makeRational(s.shares, total),
  }));
}

// Part 18: "Total fully diluted ownership must equal ~100% after every
// completed financing state, enforced by tests." Because totalShares() is
// always derived as the sum of stakeholder shares, this invariant holds
// EXACTLY (zero tolerance needed, not an approximation) for any state
// produced by this engine's own functions. This assertion exists to catch
// a hand-constructed or externally malformed CapTableState (e.g. in a
// test fixture), and to make the guarantee explicit and checked rather
// than merely implicit.
export function assertOwnershipInvariant(state: CapTableState): void {
  if (state.stakeholders.length === 0) {
    throw new FinancingError(`Ownership invariant violated: "${state.label}" has zero stakeholders`);
  }
  for (const s of state.stakeholders) {
    if (s.shares < BigInt(0)) {
      throw new FinancingError(`Ownership invariant violated: "${state.label}" stakeholder "${s.name}" has negative shares (${s.shares})`);
    }
  }
  const total = totalShares(state);
  if (total <= BigInt(0)) {
    throw new FinancingError(`Ownership invariant violated: "${state.label}" has non-positive total shares (${total})`);
  }
  const sumOfBreakdownNumerators = ownershipBreakdown(state).reduce(
    (sum, row) => sum + row.ownership.num * (total / row.ownership.den),
    BigInt(0)
  );
  if (sumOfBreakdownNumerators !== total) {
    throw new FinancingError(`Ownership invariant violated: "${state.label}" ownership fractions do not sum to exactly 100%`);
  }
}

export function initialCapTable(label: string, stakeholders: StakeholderPosition[]): CapTableState {
  const state: CapTableState = { label, stakeholders };
  assertOwnershipInvariant(state);
  return state;
}
