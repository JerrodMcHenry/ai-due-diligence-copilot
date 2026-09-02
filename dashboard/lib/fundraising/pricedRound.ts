// Phase 21A -- Fundraising Simulation, Part 8/9/12/13/14 (priced-round
// math, dilution, SAFE conversion at a priced round, option pools,
// sequencing).

import type { CapTableState, PricedRoundInput, SafeInput, Shares, StakeholderPosition } from "./types.ts";
import { type Rational, makeRational, ratCompare, ratDiv, toFlooredShares } from "./rational.ts";
import { FinancingError, assertPositiveCents, assertNonNegativeShares } from "./errors.ts";
import { totalShares, assertOwnershipInvariant, ownershipOf } from "./capTable.ts";
import { type SafeConversionResult, computeSafeConversion } from "./safe.ts";

function applyOptionPoolIncrease(stakeholders: StakeholderPosition[], increaseShares: Shares, idPrefix: string): void {
  if (increaseShares === BigInt(0)) return;
  const poolIdx = stakeholders.findIndex((s) => s.kind === "option_pool");
  if (poolIdx >= 0) {
    stakeholders[poolIdx] = { ...stakeholders[poolIdx], shares: stakeholders[poolIdx].shares + increaseShares };
  } else {
    stakeholders.push({ id: `${idPrefix}_pool_increase`, name: "Option Pool", kind: "option_pool", shares: increaseShares });
  }
}

// Part 9: dilution as an ownership CONSEQUENCE, distinguished explicitly:
//   - percentage-POINT change = after% - before% (e.g. 25% -> 20% is "5
//     percentage points")
//   - percentage DILUTION = (before% - after%) / before% (e.g. 25% -> 20%
//     is "20% dilution" -- a fifth of the original stake is gone)
// These are NOT interchangeable and this engine never conflates them.
export interface DilutionRow {
  readonly stakeholderId: string;
  readonly name: string;
  readonly ownershipBefore: Rational;
  readonly ownershipAfter: Rational;
  readonly percentagePointChange: Rational; // after - before (negative == diluted)
  readonly percentageDilution: Rational | null; // (before - after) / before; null if before == 0
}

export function computeDilution(before: CapTableState, after: CapTableState): DilutionRow[] {
  const rows: DilutionRow[] = [];
  for (const s of before.stakeholders) {
    const ownershipBefore = ownershipOf(before, s.id);
    const ownershipAfter = ownershipOf(after, s.id);
    const percentagePointChange: Rational = {
      num: ownershipAfter.num * ownershipBefore.den - ownershipBefore.num * ownershipAfter.den,
      den: ownershipAfter.den * ownershipBefore.den,
    };
    let percentageDilution: Rational | null = null;
    if (ownershipBefore.num !== BigInt(0)) {
      const diff: Rational = {
        num: ownershipBefore.num * ownershipAfter.den - ownershipAfter.num * ownershipBefore.den,
        den: ownershipBefore.den * ownershipAfter.den,
      };
      percentageDilution = ratDiv(diff, ownershipBefore);
    }
    rows.push({ stakeholderId: s.id, name: s.name, ownershipBefore, ownershipAfter, percentagePointChange, percentageDilution });
  }
  return rows;
}

// Part 8: simple priced round, no outstanding SAFEs.
// Price/share = pre-money valuation / (pre-round fully diluted shares +
// option pool increase). The option-pool increase sits in the same
// denominator as existing shares, BEFORE the new investor's shares are
// added, so the pool dilutes existing holders at the same price the new
// investor pays -- and the new investor's own shares are computed from
// that price afterward, so the new investor is never diluted by the pool
// they're buying into. Matches the directive's own worked example: $8M
// pre + $2M new money -> $10M post, new investor owns exactly 20%.
export interface PricedRoundResult {
  readonly preMoneyValuationCents: bigint;
  readonly newMoneyCents: bigint;
  readonly postMoneyValuationCents: bigint;
  readonly pricePerShare: Rational;
  readonly preRoundTotalShares: Shares;
  readonly optionPoolIncreaseShares: Shares;
  readonly newInvestorShares: Shares;
  readonly newTotalShares: Shares;
  readonly newInvestorOwnership: Rational;
  readonly postRoundState: CapTableState;
  readonly dilution: DilutionRow[];
}

export function runSimplePricedRound(preRoundState: CapTableState, round: PricedRoundInput): PricedRoundResult {
  assertPositiveCents(round.preMoneyValuationCents, "Pre-money valuation");
  assertPositiveCents(round.newMoneyCents, "New money invested");
  assertNonNegativeShares(round.optionPoolIncreaseShares, "Option pool increase");

  const preRoundShares = totalShares(preRoundState);
  if (preRoundShares <= BigInt(0)) {
    throw new FinancingError("Cannot run a priced round against a cap table with zero or negative pre-round shares");
  }

  const postMoneyValuationCents = round.preMoneyValuationCents + round.newMoneyCents;
  const denominatorShares = preRoundShares + round.optionPoolIncreaseShares;
  const pricePerShare = ratDiv(makeRational(round.preMoneyValuationCents), makeRational(denominatorShares));

  const newInvestorShares = toFlooredShares(ratDiv(makeRational(round.newMoneyCents), pricePerShare));
  if (newInvestorShares <= BigInt(0)) {
    throw new FinancingError(`Round "${round.name}": computed new-investor share count is zero -- check the pre-money valuation and new money amounts`);
  }

  const stakeholders: StakeholderPosition[] = preRoundState.stakeholders.map((s) => ({ ...s }));
  applyOptionPoolIncrease(stakeholders, round.optionPoolIncreaseShares, round.id);
  stakeholders.push({ id: round.id, name: round.newInvestorName, kind: "investor", shares: newInvestorShares });

  const postRoundState: CapTableState = { label: round.name, stakeholders };
  assertOwnershipInvariant(postRoundState);

  const newTotalShares = totalShares(postRoundState);
  return {
    preMoneyValuationCents: round.preMoneyValuationCents,
    newMoneyCents: round.newMoneyCents,
    postMoneyValuationCents,
    pricePerShare,
    preRoundTotalShares: preRoundShares,
    optionPoolIncreaseShares: round.optionPoolIncreaseShares,
    newInvestorShares,
    newTotalShares,
    newInvestorOwnership: makeRational(newInvestorShares, newTotalShares),
    postRoundState,
    dilution: computeDilution(preRoundState, postRoundState),
  };
}

// Part 12: SAFE(s) converting into a triggering priced round, in one
// transaction -- founders -> SAFE(s) -> priced round -> SAFEs convert ->
// new round shares issued -> option pool applied -> final cap table.
export interface SafePlusPricedRoundResult {
  readonly safeConversion: SafeConversionResult;
  readonly pricePerShare: Rational;
  readonly optionPoolIncreaseShares: Shares;
  readonly newInvestorShares: Shares;
  readonly newInvestorOwnership: Rational;
  readonly postRoundState: CapTableState;
  readonly dilution: DilutionRow[];
  // Part 10's documented limitation: a defensive, NOT independently
  // primary-source-verified check. If a SAFE's cap-implied price per
  // share is worse for the investor than this round's own price per
  // share (i.e. the round priced at or below the SAFE's cap), general
  // SAFE market convention gives the investor the better of the two --
  // but that comparison's exact formula was not found in a worked
  // example during this phase's research, so this engine does NOT
  // silently apply it. It only flags the case for manual review.
  readonly priceWarnings: readonly string[];
}

export function runSafeConversionAndPricedRound(
  preSafeState: CapTableState,
  safes: readonly SafeInput[],
  round: PricedRoundInput
): SafePlusPricedRoundResult {
  assertPositiveCents(round.preMoneyValuationCents, "Pre-money valuation");
  assertPositiveCents(round.newMoneyCents, "New money invested");
  assertNonNegativeShares(round.optionPoolIncreaseShares, "Option pool increase");

  const preSafeShares = totalShares(preSafeState);
  const safeConversion = computeSafeConversion(preSafeShares, safes);

  const postSafeShares = preSafeShares + safeConversion.totalSafeShares;
  const denominatorShares = postSafeShares + round.optionPoolIncreaseShares;
  const pricePerShare = ratDiv(makeRational(round.preMoneyValuationCents), makeRational(denominatorShares));

  const priceWarnings: string[] = [];
  for (const detail of safeConversion.safeDetails) {
    if (ratCompare(detail.capPricePerShare, pricePerShare) > 0) {
      priceWarnings.push(
        `SAFE "${detail.holderName}": its cap-implied price per share is higher than round "${round.name}"'s price per share ` +
          `(the round priced at or below this SAFE's valuation cap). V1 does not independently verify the conversion formula ` +
          `for this case -- treat this SAFE's conversion result as provisional and confirm against legal documents.`
      );
    }
  }

  const newInvestorShares = toFlooredShares(ratDiv(makeRational(round.newMoneyCents), pricePerShare));
  if (newInvestorShares <= BigInt(0)) {
    throw new FinancingError(`Round "${round.name}": computed new-investor share count is zero -- check the pre-money valuation and new money amounts`);
  }

  const stakeholders: StakeholderPosition[] = preSafeState.stakeholders.map((s) => ({ ...s }));
  for (const detail of safeConversion.safeDetails) {
    stakeholders.push({ id: detail.safeId, name: detail.holderName, kind: "safe", shares: detail.conversionShares });
  }
  applyOptionPoolIncrease(stakeholders, round.optionPoolIncreaseShares, round.id);
  stakeholders.push({ id: round.id, name: round.newInvestorName, kind: "investor", shares: newInvestorShares });

  const postRoundState: CapTableState = { label: round.name, stakeholders };
  assertOwnershipInvariant(postRoundState);

  return {
    safeConversion,
    pricePerShare,
    optionPoolIncreaseShares: round.optionPoolIncreaseShares,
    newInvestorShares,
    newInvestorOwnership: makeRational(newInvestorShares, totalShares(postRoundState)),
    postRoundState,
    dilution: computeDilution(preSafeState, postRoundState),
    priceWarnings,
  };
}
