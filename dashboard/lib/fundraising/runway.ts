// Phase 21A -- Fundraising Simulation, Part 15 (runway).
//
// Deliberately separate from cap-table/ownership math (pricedRound.ts,
// safe.ts) -- runway is cash divided by burn, nothing else. It never
// feeds into or reads from ownership calculations, and it never predicts
// future burn: burn is a single caller-supplied constant, held flat.

import type { RunwayInput } from "./types.ts";
import { type Rational, makeRational } from "./rational.ts";
import { FinancingError, assertNonNegativeCents } from "./errors.ts";

export interface RunwayResult {
  readonly cashOnHandCents: bigint;
  readonly monthlyBurnCents: bigint;
  readonly runwayMonths: Rational | null; // null only when isInfinite is true
  readonly isInfinite: boolean; // true when monthly burn is exactly zero
}

export function computeRunway(input: RunwayInput): RunwayResult {
  assertNonNegativeCents(input.cashOnHandCents, "Cash on hand");
  if (input.monthlyBurnCents < BigInt(0)) {
    throw new FinancingError(`Monthly burn cannot be negative, got ${input.monthlyBurnCents}`);
  }

  if (input.monthlyBurnCents === BigInt(0)) {
    return { cashOnHandCents: input.cashOnHandCents, monthlyBurnCents: BigInt(0), runwayMonths: null, isInfinite: true };
  }

  const runwayMonths = makeRational(input.cashOnHandCents, input.monthlyBurnCents);
  return { cashOnHandCents: input.cashOnHandCents, monthlyBurnCents: input.monthlyBurnCents, runwayMonths, isInfinite: false };
}
