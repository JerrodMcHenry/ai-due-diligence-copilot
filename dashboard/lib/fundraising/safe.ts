// Phase 21A -- Fundraising Simulation, Part 10/11/12 (SAFE mechanics).
//
// Implements post-money SAFE conversion using the "Company Capitalization"
// method documented in Y Combinator's official Post-Money SAFE User Guide
// (v1.2, Feb 2023) -- the current, authoritative primary source for this
// instrument. See docs/methodology/FUNDRAISING_SIMULATION_V1_SPEC.md for
// the full derivation and citations.
//
// Formula (matches the User Guide's Appendix II worked example exactly --
// see fundraising.test.ts's golden case #2 for the numeric cross-check):
//
//   For each SAFE, capOwnership = investmentCents / valuationCapCents
//   totalSafeCapOwnership = sum(capOwnership across all outstanding SAFEs)
//   CompanyCapitalization = PreSafeShares / (1 - totalSafeCapOwnership)
//     (self-referential: Company Capitalization must include the SAFEs'
//      own as-converted shares, which is why it's solved this way rather
//      than simply added up)
//   Each SAFE's shares = floor(CompanyCapitalization * its own capOwnership)
//
// computeSafeConversion() is used both standalone (Quick Start Guide's
// simple "what would this SAFE be worth if it converted right now"
// examples) and as the first step of runSafeConversionAndPricedRound()
// (pricedRound.ts) -- the formula is identical in both cases; a priced
// round changes what happens to the company's shares AFTER this step, not
// this step itself.

import type { CapTableState, Cents, SafeInput, Shares } from "./types.ts";
import {
  type Rational,
  RAT_ONE,
  RAT_ZERO,
  makeRational,
  ratAdd,
  ratCompare,
  ratDiv,
  ratMul,
  toFlooredShares,
} from "./rational.ts";
import { FinancingError, assertPositiveCents } from "./errors.ts";
import { totalShares } from "./capTable.ts";

export interface SafeConversionDetail {
  readonly safeId: string;
  readonly holderName: string;
  readonly investmentCents: Cents;
  readonly valuationCapCents: Cents;
  readonly capImpliedOwnership: Rational; // investment / cap, before the Company Capitalization solve
  readonly conversionShares: Shares;
  readonly capPricePerShare: Rational; // investmentCents / conversionShares, for cross-checking against a round's own price
}

export interface SafeConversionResult {
  readonly preSafeShares: Shares;
  readonly totalSafeCapOwnership: Rational;
  readonly companyCapitalization: Shares; // floored
  readonly safeDetails: readonly SafeConversionDetail[];
  readonly totalSafeShares: Shares;
}

function validateSafeForConversion(safe: SafeInput): void {
  if (safe.valuationCapCents === null) {
    throw new FinancingError(
      `SAFE "${safe.holderName}": V1 only supports conversion math for SAFEs with a valuation cap. ` +
        `Discount-only or MFN-only SAFEs are recognized shapes but are explicitly unsupported for ` +
        `conversion in this phase -- see the spec doc's Unsupported Instruments section.`
    );
  }
  assertPositiveCents(safe.investmentCents, `SAFE "${safe.holderName}" investment amount`);
  assertPositiveCents(safe.valuationCapCents, `SAFE "${safe.holderName}" valuation cap`);
}

export function computeSafeConversion(preSafeShares: Shares, safes: readonly SafeInput[]): SafeConversionResult {
  if (preSafeShares <= BigInt(0)) {
    throw new FinancingError(`Cannot convert SAFEs against a cap table with non-positive pre-SAFE shares (${preSafeShares})`);
  }
  if (safes.length === 0) {
    return {
      preSafeShares,
      totalSafeCapOwnership: RAT_ZERO,
      companyCapitalization: preSafeShares,
      safeDetails: [],
      totalSafeShares: BigInt(0),
    };
  }

  for (const safe of safes) validateSafeForConversion(safe);

  const capOwnerships: Rational[] = safes.map((safe) => makeRational(safe.investmentCents, safe.valuationCapCents as bigint));
  const totalSafeCapOwnership = capOwnerships.reduce((sum, o) => ratAdd(sum, o), RAT_ZERO);

  if (ratCompare(totalSafeCapOwnership, RAT_ONE) >= 0) {
    throw new FinancingError(
      `Outstanding SAFEs alone imply total ownership >= 100% of the company (their combined ` +
        `investment/cap ratios sum to ${totalSafeCapOwnership.num}/${totalSafeCapOwnership.den}), which is impossible.`
    );
  }

  // CompanyCapitalization = PreSafeShares / (1 - totalSafeCapOwnership).
  const oneMinusTotal: Rational = { num: totalSafeCapOwnership.den - totalSafeCapOwnership.num, den: totalSafeCapOwnership.den };
  const companyCapRat = ratDiv(makeRational(preSafeShares), oneMinusTotal);
  const companyCapitalization = toFlooredShares(companyCapRat);
  const companyCapAsRational = makeRational(companyCapitalization);

  const safeDetails: SafeConversionDetail[] = safes.map((safe, i) => {
    const sharesRat = ratMul(companyCapAsRational, capOwnerships[i]);
    const conversionShares = toFlooredShares(sharesRat);
    if (conversionShares <= BigInt(0)) {
      throw new FinancingError(`SAFE "${safe.holderName}" converts to zero shares -- check its investment amount and cap`);
    }
    const capPricePerShare = ratDiv(makeRational(safe.investmentCents), makeRational(conversionShares));
    return {
      safeId: safe.id,
      holderName: safe.holderName,
      investmentCents: safe.investmentCents,
      valuationCapCents: safe.valuationCapCents as bigint,
      capImpliedOwnership: capOwnerships[i],
      conversionShares,
      capPricePerShare,
    };
  });

  const totalSafeShares = safeDetails.reduce((sum, d) => sum + d.conversionShares, BigInt(0));

  return { preSafeShares, totalSafeCapOwnership, companyCapitalization, safeDetails, totalSafeShares };
}

// Convenience wrapper matching the Quick Start Guide's simple "what is
// this SAFE worth right now" framing -- identical math to
// computeSafeConversion(), just named for that standalone use case.
export function estimateStandaloneSafeOwnership(preSafeState: CapTableState, safes: readonly SafeInput[]): SafeConversionResult {
  return computeSafeConversion(totalShares(preSafeState), safes);
}
