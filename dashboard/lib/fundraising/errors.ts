// Phase 21A -- Fundraising Simulation, Part 23 (error handling).
//
// Every nonsensical input state fails LOUDLY with a specific, named
// FinancingError -- never silently normalized, clamped, or coerced into a
// plausible-looking result. See the spec doc's "Error Handling" section
// for the full enumerated list this module implements.

import type { Cents } from "./types.ts";
import { type Rational, RAT_ONE, ratCompare, ratIsNegative } from "./rational.ts";

export class FinancingError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "FinancingError";
  }
}

export function assertPositiveCents(value: Cents, label: string): void {
  if (value <= BigInt(0)) {
    throw new FinancingError(`${label} must be a positive amount in cents, got ${value}`);
  }
}

export function assertNonNegativeCents(value: Cents, label: string): void {
  if (value < BigInt(0)) {
    throw new FinancingError(`${label} cannot be negative, got ${value}`);
  }
}

export function assertNonNegativeShares(value: bigint, label: string): void {
  if (value < BigInt(0)) {
    throw new FinancingError(`${label} cannot be a negative share count, got ${value}`);
  }
}

// Discount SAFEs are a recognized V1 shape but only the [0%, 100%) range
// is even conceptually valid -- 0% is "no discount" (should be modeled as
// null instead) and 100%+ would mean investors pay nothing or get paid to
// invest, which is nonsensical.
export function assertValidDiscount(discount: Rational | null): void {
  if (discount === null) return;
  if (ratIsNegative(discount) || ratCompare(discount, RAT_ONE) >= 0) {
    throw new FinancingError(`Discount must be between 0% and 100% (exclusive of 100%), got a fraction outside that range`);
  }
}
