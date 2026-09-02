// Phase 21A -- Fundraising Simulation Specification & Math Validation.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/simulate.test.ts (this repo has no jest/vitest), run directly by
// Node's native TypeScript support -- no build step, no bundler, which is
// why lib/fundraising/*.ts is written with zero "@/..." alias imports.
//
// Run with:
//   node tests/fundraising.test.ts
// or:
//   npm run test:fundraising
//
// Scenario matrix A-N (Part 20), three independently hand-calculated
// golden cases (Part 21, labeled GOLDEN #1/#2/#3), and one external
// cross-check (Part 22) against Y Combinator's own Post-Money SAFE User
// Guide (v1.2, Feb 2023) Appendix II worked example -- see
// docs/methodology/FUNDRAISING_SIMULATION_V1_SPEC.md for full citations
// and the hand-derivation of every expected number below.

import { initialCapTable, totalShares, ownershipOf, assertOwnershipInvariant } from "../lib/fundraising/capTable.ts";
import { runSimplePricedRound, runSafeConversionAndPricedRound } from "../lib/fundraising/pricedRound.ts";
import { computeSafeConversion, estimateStandaloneSafeOwnership } from "../lib/fundraising/safe.ts";
import { computeRunway } from "../lib/fundraising/runway.ts";
import { FinancingError } from "../lib/fundraising/errors.ts";
import { makeRational, toPercentString, toFlooredShares, ratDiv } from "../lib/fundraising/rational.ts";
import type { CapTableState, SafeInput, PricedRoundInput } from "../lib/fundraising/types.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function expectThrows(fn: () => void, message: string): void {
  try {
    fn();
    throw new Error(`Expected an error, but none was thrown: ${message}`);
  } catch (e) {
    if (!(e instanceof FinancingError)) {
      throw new Error(`Expected a FinancingError, got ${(e as Error).constructor.name}: ${message}`);
    }
  }
}

const cents = (dollars: number): bigint => BigInt(Math.round(dollars * 100));

// --- Fixture A: two founders, no financing ---------------------------------

function test_A_two_founders_no_financing(): void {
  const state = initialCapTable("State 0", [
    { id: "f1", name: "Founder A", kind: "founder", shares: BigInt(600_000) },
    { id: "f2", name: "Founder B", kind: "founder", shares: BigInt(400_000) },
  ]);
  expect(totalShares(state) === BigInt(1_000_000), "Total shares must be 1,000,000");
  expect(toPercentString(ownershipOf(state, "f1")) === "60.00%", `Founder A must own exactly 60.00%, got ${toPercentString(ownershipOf(state, "f1"))}`);
  expect(toPercentString(ownershipOf(state, "f2")) === "40.00%", `Founder B must own exactly 40.00%, got ${toPercentString(ownershipOf(state, "f2"))}`);
  assertOwnershipInvariant(state);
}

// --- Fixture B / GOLDEN CASE #1: simple priced round ------------------------
//
// Hand-derivation (this is the directive's own worked example):
//   Pre-money $8,000,000, new money $2,000,000 -> post-money $10,000,000.
//   Founders hold 8,000,000 shares pre-round.
//   Step 1: price/share = $8,000,000 / 8,000,000 shares = $1.00
//   Step 2: new investor shares = $2,000,000 / $1.00 = 2,000,000
//   Step 3: new total shares = 8,000,000 + 2,000,000 = 10,000,000
//   Final: new investor = 2,000,000 / 10,000,000 = 20.00% exactly.
//           founders diluted from 100% to 8,000,000/10,000,000 = 80.00%.

function test_B_golden_1_simple_priced_round(): void {
  const preRound = initialCapTable("State 0", [{ id: "founders", name: "Founders", kind: "founder", shares: BigInt(8_000_000) }]);
  const round: PricedRoundInput = {
    id: "seed",
    name: "Seed",
    preMoneyValuationCents: cents(8_000_000),
    newMoneyCents: cents(2_000_000),
    optionPoolIncreaseShares: BigInt(0),
    newInvestorName: "Seed Investor",
  };
  const result = runSimplePricedRound(preRound, round);

  expect(result.postMoneyValuationCents === cents(10_000_000), `Post-money must be $10,000,000, got ${result.postMoneyValuationCents}`);
  // pricePerShare is denominated in CENTS per share (both money and price
  // are cents-based throughout this engine); $1.00/share == 100 cents/share.
  expect(result.pricePerShare.num === BigInt(100) && result.pricePerShare.den === BigInt(1), `Price/share must be exactly 100 cents ($1.00), got ${result.pricePerShare.num}/${result.pricePerShare.den}`);
  expect(result.newInvestorShares === BigInt(2_000_000), `New investor must get exactly 2,000,000 shares, got ${result.newInvestorShares}`);
  expect(result.newTotalShares === BigInt(10_000_000), `New total must be 10,000,000 shares, got ${result.newTotalShares}`);
  expect(toPercentString(result.newInvestorOwnership) === "20.00%", `New investor must own exactly 20.00%, got ${toPercentString(result.newInvestorOwnership)}`);
  expect(toPercentString(ownershipOf(result.postRoundState, "founders")) === "80.00%", `Founders must be diluted to exactly 80.00%`);
  assertOwnershipInvariant(result.postRoundState);

  const dilution = result.dilution.find((d) => d.stakeholderId === "founders")!;
  expect(toPercentString(dilution.percentagePointChange) === "-20.00%", `Founders must lose exactly 20 percentage points, got ${toPercentString(dilution.percentagePointChange)}`);
  expect(toPercentString(dilution.percentageDilution!) === "20.00%", `Founders' percentage dilution must be exactly 20% (1/5 of their stake), got ${toPercentString(dilution.percentageDilution!)}`);
}

// --- Fixture C: unequal founders + priced round -----------------------------

function test_C_unequal_founders_priced_round(): void {
  const preRound = initialCapTable("State 0", [
    { id: "fa", name: "Founder A", kind: "founder", shares: BigInt(700_000) },
    { id: "fb", name: "Founder B", kind: "founder", shares: BigInt(300_000) },
  ]);
  const round: PricedRoundInput = {
    id: "seed",
    name: "Seed",
    preMoneyValuationCents: cents(4_000_000),
    newMoneyCents: cents(1_000_000),
    optionPoolIncreaseShares: BigInt(0),
    newInvestorName: "Seed Investor",
  };
  const result = runSimplePricedRound(preRound, round);

  expect(result.newInvestorShares === BigInt(250_000), `New investor must get exactly 250,000 shares, got ${result.newInvestorShares}`);
  expect(toPercentString(ownershipOf(result.postRoundState, "fa")) === "56.00%", "Founder A must be diluted to exactly 56.00%");
  expect(toPercentString(ownershipOf(result.postRoundState, "fb")) === "24.00%", "Founder B must be diluted to exactly 24.00%");
  expect(toPercentString(result.newInvestorOwnership) === "20.00%", "New investor must own exactly 20.00%");
  assertOwnershipInvariant(result.postRoundState);
}

// --- Fixture D: single post-money SAFE, standalone --------------------------
//
// Mirrors the shape of Y Combinator's own Quick Start Guide illustration
// (Founders/Options/Unissued Pool at 90/8/2, single SAFE at a 10%-implied
// cap uniformly dilutes every existing row).

function test_D_single_safe_standalone(): void {
  const preSafe = initialCapTable("State 0", [
    { id: "founders", name: "Founders", kind: "founder", shares: BigInt(900_000) },
    { id: "options", name: "Outstanding Options", kind: "option_pool", shares: BigInt(80_000) },
    { id: "pool", name: "Unissued Pool", kind: "option_pool", shares: BigInt(20_000) },
  ]);
  const safe: SafeInput = { id: "safeA", holderName: "Investor A", investmentCents: cents(500_000), valuationCapCents: cents(5_000_000), discountPercent: null };

  const result = estimateStandaloneSafeOwnership(preSafe, [safe]);
  expect(result.companyCapitalization === BigInt(1_111_111), `Company Capitalization must be 1,111,111, got ${result.companyCapitalization}`);
  expect(result.totalSafeShares === BigInt(111_111), `SAFE must convert to 111,111 shares, got ${result.totalSafeShares}`);

  // Demonstrates the display-rounding rule (rational.ts Rule 2): the exact
  // fraction 111,111 / 1,111,111 is a hair under 10% due to two separate
  // floor operations, but rounds to "10.00%" at 2 decimal places.
  const safePct = ratDiv(makeRational(result.totalSafeShares), makeRational(result.companyCapitalization));
  expect(toPercentString(safePct) === "10.00%", `SAFE percentage must display as 10.00% after rounding, got ${toPercentString(safePct)}`);
}

// --- Fixture E / EXTERNAL CROSS-CHECK: multiple post-money SAFEs -----------
//
// Reproduces Y Combinator's Post-Money SAFE User Guide (v1.2, Feb 2023),
// Appendix II, Example 1's pre-Series-A cap table and two outstanding
// SAFEs EXACTLY, including stakeholder share counts:
//   Founders 9,250,000 + Outstanding Options 300,000 + Promised Options
//   350,000 + Unissued Pool 100,000 = 10,000,000 pre-safe shares.
//   Investor A: $200,000 / $4,000,000 cap (5% implied)
//   Investor B: $800,000 / $8,000,000 cap (10% implied)
// The Guide's own stated results: Company Capitalization = 11,764,705;
// Investor A converts to 588,235 shares; Investor B converts to
// 1,176,470 shares. This engine is asserted against those externally
// authoritative numbers below -- not against its own formula in isolation.

function test_E_external_cross_check_multiple_safes(): void {
  const preSafe = initialCapTable("Pre-Series A", [
    { id: "founders", name: "Founders", kind: "founder", shares: BigInt(9_250_000) },
    { id: "options_out", name: "Outstanding Options", kind: "option_pool", shares: BigInt(300_000) },
    { id: "options_promised", name: "Promised Options", kind: "option_pool", shares: BigInt(350_000) },
    { id: "pool", name: "Unissued Pool", kind: "option_pool", shares: BigInt(100_000) },
  ]);
  expect(totalShares(preSafe) === BigInt(10_000_000), "Pre-safe fully diluted shares must be 10,000,000 (matches the Guide's own cap table)");

  const safeA: SafeInput = { id: "safeA", holderName: "Investor A", investmentCents: cents(200_000), valuationCapCents: cents(4_000_000), discountPercent: null };
  const safeB: SafeInput = { id: "safeB", holderName: "Investor B", investmentCents: cents(800_000), valuationCapCents: cents(8_000_000), discountPercent: null };

  const result = computeSafeConversion(totalShares(preSafe), [safeA, safeB]);

  // EXTERNAL CROSS-CHECK -- fixture / external (YC-published) / engine result:
  expect(result.companyCapitalization === BigInt(11_764_705), `EXTERNAL CROSS-CHECK FAILED: Company Capitalization must equal the Guide's stated 11,764,705, engine produced ${result.companyCapitalization}`);
  expect(result.safeDetails[0].conversionShares === BigInt(588_235), `EXTERNAL CROSS-CHECK FAILED: Investor A must convert to the Guide's stated 588,235 shares, engine produced ${result.safeDetails[0].conversionShares}`);
  expect(result.safeDetails[1].conversionShares === BigInt(1_176_470), `EXTERNAL CROSS-CHECK FAILED: Investor B must convert to the Guide's stated 1,176,470 shares, engine produced ${result.safeDetails[1].conversionShares}`);
  expect(result.totalSafeShares === BigInt(1_764_705), `Total SAFE shares must be 1,764,705, got ${result.totalSafeShares}`);
}

// --- Fixture F / GOLDEN CASE #2: SAFE conversion + priced Seed --------------
//
// Builds on fixture E's exact, externally-verified SAFE conversion
// (10,000,000 pre-safe + 1,764,705 safe shares = 11,764,705 post-safe
// shares), then layers a priced round on top with numbers chosen so the
// remaining math is exactly hand-verifiable:
//   Price/share fixed at exactly $1.00 by setting pre-money =
//   $11,764,705.00 (11,764,705 shares x $1.00).
//   New money $3,000,000 -> new investor shares = 3,000,000 / $1.00 =
//   3,000,000 exactly.
//   Final total = 11,764,705 + 3,000,000 = 14,764,705.

function test_F_golden_2_safe_plus_priced_seed(): void {
  const preSafe = initialCapTable("Pre-Series A", [
    { id: "founders", name: "Founders", kind: "founder", shares: BigInt(9_250_000) },
    { id: "options_out", name: "Outstanding Options", kind: "option_pool", shares: BigInt(300_000) },
    { id: "options_promised", name: "Promised Options", kind: "option_pool", shares: BigInt(350_000) },
    { id: "pool", name: "Unissued Pool", kind: "option_pool", shares: BigInt(100_000) },
  ]);
  const safeA: SafeInput = { id: "safeA", holderName: "Investor A", investmentCents: cents(200_000), valuationCapCents: cents(4_000_000), discountPercent: null };
  const safeB: SafeInput = { id: "safeB", holderName: "Investor B", investmentCents: cents(800_000), valuationCapCents: cents(8_000_000), discountPercent: null };

  const round: PricedRoundInput = {
    id: "seriesA",
    name: "Series A",
    preMoneyValuationCents: cents(11_764_705),
    newMoneyCents: cents(3_000_000),
    optionPoolIncreaseShares: BigInt(0),
    newInvestorName: "Series A Lead",
  };

  const result = runSafeConversionAndPricedRound(preSafe, [safeA, safeB], round);

  expect(result.safeConversion.companyCapitalization === BigInt(11_764_705), "SAFE conversion sub-step must reproduce the externally-verified Company Capitalization");
  expect(result.safeConversion.totalSafeShares === BigInt(1_764_705), "SAFE conversion sub-step must reproduce the externally-verified total SAFE shares");
  expect(result.pricePerShare.num === BigInt(100) && result.pricePerShare.den === BigInt(1), `Series A price/share must be exactly 100 cents ($1.00), got ${result.pricePerShare.num}/${result.pricePerShare.den}`);
  expect(result.newInvestorShares === BigInt(3_000_000), `Series A lead must get exactly 3,000,000 shares, got ${result.newInvestorShares}`);
  expect(totalShares(result.postRoundState) === BigInt(14_764_705), `Final total shares must be 14,764,705, got ${totalShares(result.postRoundState)}`);
  expect(result.priceWarnings.length === 0, `No SAFE priced below the round in this fixture -- expected zero warnings, got ${result.priceWarnings.length}`);
  assertOwnershipInvariant(result.postRoundState);
}

// --- Fixture G: existing option pool participates in dilution normally -----

function test_G_existing_option_pool_dilutes_proportionally(): void {
  const preRound = initialCapTable("State 0", [
    { id: "founders", name: "Founders", kind: "founder", shares: BigInt(800_000) },
    { id: "pool", name: "Option Pool", kind: "option_pool", shares: BigInt(200_000) },
  ]);
  const round: PricedRoundInput = {
    id: "seed",
    name: "Seed",
    preMoneyValuationCents: cents(1_000_000),
    newMoneyCents: cents(250_000),
    optionPoolIncreaseShares: BigInt(0),
    newInvestorName: "Seed Investor",
  };
  const result = runSimplePricedRound(preRound, round);

  expect(toPercentString(ownershipOf(result.postRoundState, "founders")) === "64.00%", "Founders must be diluted to exactly 64.00%");
  expect(toPercentString(ownershipOf(result.postRoundState, "pool")) === "16.00%", "Pool must be diluted to exactly 16.00%");

  const founderDilution = result.dilution.find((d) => d.stakeholderId === "founders")!;
  const poolDilution = result.dilution.find((d) => d.stakeholderId === "pool")!;
  expect(
    toPercentString(founderDilution.percentageDilution!) === toPercentString(poolDilution.percentageDilution!),
    "With no pool increase, founders and the existing pool must be diluted at IDENTICAL percentage rates (both 20%) -- a plain new-money round dilutes every pre-round holder pro-rata"
  );
}

// --- Fixture H: option-pool expansion -- who bears the dilution ------------
//
// Confirms Part 13's core mechanic: a SAFE's CONVERSION SHARE COUNT is
// fixed by Company Capitalization (which depends only on pre-safe shares
// and the SAFEs' own caps) BEFORE any option-pool expansion decision is
// made for the triggering round -- so the pool increase cannot change how
// many shares a SAFE converts into, even though its resulting OWNERSHIP
// PERCENTAGE still moves slightly because the total share count it's a
// fraction of has grown. The dilution from the new pool is borne by
// founders (and any other pre-existing non-safe holders), not by the
// converting SAFE.

function test_H_option_pool_expansion_does_not_change_safe_share_count(): void {
  const preSafe = initialCapTable("State 0", [{ id: "founders", name: "Founders", kind: "founder", shares: BigInt(10_000_000) }]);
  const safe: SafeInput = { id: "safeA", holderName: "Investor A", investmentCents: cents(1_000_000), valuationCapCents: cents(10_000_000), discountPercent: null };

  const noIncrease: PricedRoundInput = {
    id: "seedNoPool",
    name: "Seed (no pool increase)",
    preMoneyValuationCents: cents(11_111_111),
    newMoneyCents: cents(2_000_000),
    optionPoolIncreaseShares: BigInt(0),
    newInvestorName: "Seed Investor",
  };
  const withIncrease: PricedRoundInput = {
    id: "seedWithPool",
    name: "Seed (with pool increase)",
    preMoneyValuationCents: cents(12_222_222),
    newMoneyCents: cents(2_000_000),
    optionPoolIncreaseShares: BigInt(1_111_111),
    newInvestorName: "Seed Investor",
  };

  const resultNoIncrease = runSafeConversionAndPricedRound(preSafe, [safe], noIncrease);
  const resultWithIncrease = runSafeConversionAndPricedRound(preSafe, [safe], withIncrease);

  expect(resultNoIncrease.safeConversion.totalSafeShares === BigInt(1_111_111), `Baseline SAFE share count must be 1,111,111, got ${resultNoIncrease.safeConversion.totalSafeShares}`);
  expect(
    resultNoIncrease.safeConversion.totalSafeShares === resultWithIncrease.safeConversion.totalSafeShares,
    "A SAFE's converted SHARE COUNT must be identical whether or not the triggering round expands the option pool -- the pool increase is excluded from the Company Capitalization the SAFE converts against"
  );
  expect(resultNoIncrease.pricePerShare.num === BigInt(100) && resultNoIncrease.pricePerShare.den === BigInt(1), "Baseline price/share must be exactly 100 cents ($1.00)");
  expect(resultWithIncrease.pricePerShare.num === BigInt(100) && resultWithIncrease.pricePerShare.den === BigInt(1), "With-pool-increase price/share must also be exactly 100 cents ($1.00) (numbers chosen to isolate the share-count comparison)");

  const founderPctNoIncrease = toPercentString(ownershipOf(resultNoIncrease.postRoundState, "founders"));
  const founderPctWithIncrease = toPercentString(ownershipOf(resultWithIncrease.postRoundState, "founders"));
  expect(founderPctNoIncrease !== founderPctWithIncrease, "Founders' final ownership MUST differ between the two scenarios -- they, not the SAFE, bear the pool-increase dilution");
}

// --- Fixture I / GOLDEN CASE #3: SAFE + option pool + priced round ---------
//
// A from-scratch, independently hand-picked fixture where every
// intermediate number is an EXACT integer (zero flooring anywhere),
// specifically to demonstrate end-to-end traceability with no rounding
// ambiguity at any step:
//   Founders 9,000,000 shares (100%).
//   SAFE: $1,000,000 / $10,000,000 cap -> capOwnership = 10%.
//     Company Capitalization = 9,000,000 / 0.9 = 10,000,000 exactly.
//     SAFE shares = 10,000,000 x 10% = 1,000,000 exactly.
//   Priced round: option pool increase = 1,000,000 shares (absolute).
//     Denominator = 10,000,000 (post-safe) + 1,000,000 (pool) = 11,000,000.
//     Pre-money set to $22,000,000 -> price/share = $22,000,000 /
//     11,000,000 = $2.00 exactly.
//     New money $5,000,000 -> new investor shares = 5,000,000 / $2.00 =
//     2,500,000 exactly.
//   Final total = 10,000,000 + 1,000,000 + 2,500,000 = 13,500,000.
//   Founders 9,000,000/13,500,000 = 2/3 exactly (66.67% displayed).
//   SAFE 1,000,000/13,500,000 = pool 1,000,000/13,500,000 (both 7.41%).
//   New investor 2,500,000/13,500,000 = 18.52%.

function test_I_golden_3_safe_plus_option_pool_plus_priced_round(): void {
  const preSafe = initialCapTable("State 0", [{ id: "founders", name: "Founders", kind: "founder", shares: BigInt(9_000_000) }]);
  const safe: SafeInput = { id: "safeA", holderName: "Investor A", investmentCents: cents(1_000_000), valuationCapCents: cents(10_000_000), discountPercent: null };
  const round: PricedRoundInput = {
    id: "seed",
    name: "Seed",
    preMoneyValuationCents: cents(22_000_000),
    newMoneyCents: cents(5_000_000),
    optionPoolIncreaseShares: BigInt(1_000_000),
    newInvestorName: "Seed Investor",
  };

  const result = runSafeConversionAndPricedRound(preSafe, [safe], round);

  expect(result.safeConversion.companyCapitalization === BigInt(10_000_000), `Company Capitalization must be exactly 10,000,000, got ${result.safeConversion.companyCapitalization}`);
  expect(result.safeConversion.totalSafeShares === BigInt(1_000_000), `SAFE shares must be exactly 1,000,000, got ${result.safeConversion.totalSafeShares}`);
  expect(result.pricePerShare.num === BigInt(200) && result.pricePerShare.den === BigInt(1), `Price/share must be exactly 200 cents ($2.00), got ${result.pricePerShare.num}/${result.pricePerShare.den}`);
  expect(result.newInvestorShares === BigInt(2_500_000), `New investor shares must be exactly 2,500,000, got ${result.newInvestorShares}`);
  expect(totalShares(result.postRoundState) === BigInt(13_500_000), `Final total shares must be exactly 13,500,000, got ${totalShares(result.postRoundState)}`);

  expect(toPercentString(ownershipOf(result.postRoundState, "founders")) === "66.67%", `Founders must display as 66.67% (exactly 2/3), got ${toPercentString(ownershipOf(result.postRoundState, "founders"))}`);
  const safeRow = result.postRoundState.stakeholders.find((s) => s.kind === "safe")!;
  const poolRow = result.postRoundState.stakeholders.find((s) => s.kind === "option_pool")!;
  expect(safeRow.shares === BigInt(1_000_000) && poolRow.shares === BigInt(1_000_000), "SAFE and option pool must each hold exactly 1,000,000 shares");
  expect(toPercentString(ownershipOf(result.postRoundState, safeRow.id)) === "7.41%", "SAFE must display as 7.41%");
  expect(toPercentString(result.newInvestorOwnership) === "18.52%", "New investor must display as 18.52%");

  assertOwnershipInvariant(result.postRoundState);
}

// --- Fixture J: sequential Seed -> Series A ---------------------------------

function test_J_sequential_seed_then_series_a(): void {
  const state0 = initialCapTable("State 0", [{ id: "founders", name: "Founders", kind: "founder", shares: BigInt(1_000_000) }]);

  const seed: PricedRoundInput = {
    id: "seed",
    name: "Seed",
    preMoneyValuationCents: cents(3_000_000),
    newMoneyCents: cents(900_000),
    optionPoolIncreaseShares: BigInt(0),
    newInvestorName: "Seed Investor",
  };
  const seedResult = runSimplePricedRound(state0, seed);
  expect(seedResult.newInvestorShares === BigInt(300_000), `Seed investor must get exactly 300,000 shares, got ${seedResult.newInvestorShares}`);
  expect(totalShares(seedResult.postRoundState) === BigInt(1_300_000), "Post-seed total must be 1,300,000");

  // The Seed round's own OUTPUT state feeds directly into the Series A
  // round as its INPUT state -- no special-casing required for sequencing.
  const seriesA: PricedRoundInput = {
    id: "seriesA",
    name: "Series A",
    preMoneyValuationCents: cents(5_200_000),
    newMoneyCents: cents(1_300_000),
    optionPoolIncreaseShares: BigInt(0),
    newInvestorName: "Series A Lead",
  };
  const seriesAResult = runSimplePricedRound(seedResult.postRoundState, seriesA);

  expect(seriesAResult.newInvestorShares === BigInt(325_000), `Series A lead must get exactly 325,000 shares, got ${seriesAResult.newInvestorShares}`);
  expect(totalShares(seriesAResult.postRoundState) === BigInt(1_625_000), "Post-Series-A total must be 1,625,000");
  expect(toPercentString(seriesAResult.newInvestorOwnership) === "20.00%", "Series A lead must own exactly 20.00%");
  assertOwnershipInvariant(seriesAResult.postRoundState);
}

// --- Fixture K: runway (kept separate from ownership math) -----------------

function test_K_runway(): void {
  const result = computeRunway({ cashOnHandCents: cents(500_000), monthlyBurnCents: cents(62_500) });
  expect(!result.isInfinite, "Runway with positive burn must not be infinite");
  expect(result.runwayMonths!.num === BigInt(8) && result.runwayMonths!.den === BigInt(1), `Runway must be exactly 8 months, got ${result.runwayMonths!.num}/${result.runwayMonths!.den}`);

  const zeroBurn = computeRunway({ cashOnHandCents: cents(500_000), monthlyBurnCents: BigInt(0) });
  expect(zeroBurn.isInfinite === true && zeroBurn.runwayMonths === null, "Zero burn must report isInfinite=true and no numeric runwayMonths");

  expectThrows(() => computeRunway({ cashOnHandCents: -BigInt(1), monthlyBurnCents: cents(10_000) }), "Negative cash must be rejected");
  expectThrows(() => computeRunway({ cashOnHandCents: cents(10_000), monthlyBurnCents: -BigInt(1) }), "Negative burn must be rejected");
}

// --- Fixture L: zero / invalid inputs never silently normalized ------------

function test_L_invalid_inputs_fail_loudly(): void {
  const founders = initialCapTable("State 0", [{ id: "founders", name: "Founders", kind: "founder", shares: BigInt(1_000_000) }]);

  expectThrows(
    () => runSimplePricedRound(founders, { id: "r", name: "Bad", preMoneyValuationCents: BigInt(0), newMoneyCents: cents(1_000), optionPoolIncreaseShares: BigInt(0), newInvestorName: "X" }),
    "Zero pre-money valuation must be rejected"
  );
  expectThrows(
    () => runSimplePricedRound(founders, { id: "r", name: "Bad", preMoneyValuationCents: cents(-1), newMoneyCents: cents(1_000), optionPoolIncreaseShares: BigInt(0), newInvestorName: "X" }),
    "Negative pre-money valuation must be rejected"
  );
  expectThrows(
    () => runSimplePricedRound(founders, { id: "r", name: "Bad", preMoneyValuationCents: cents(1_000), newMoneyCents: -BigInt(1), optionPoolIncreaseShares: BigInt(0), newInvestorName: "X" }),
    "Negative new money must be rejected"
  );
  expectThrows(
    () => runSimplePricedRound(founders, { id: "r", name: "Bad", preMoneyValuationCents: cents(1_000), newMoneyCents: cents(100), optionPoolIncreaseShares: -BigInt(1), newInvestorName: "X" }),
    "Negative option pool increase must be rejected"
  );

  const badSafeInvestment: SafeInput = { id: "s", holderName: "X", investmentCents: -BigInt(1), valuationCapCents: cents(1_000_000), discountPercent: null };
  expectThrows(() => computeSafeConversion(BigInt(1_000_000), [badSafeInvestment]), "Negative SAFE investment must be rejected");

  const badSafeCap: SafeInput = { id: "s", holderName: "X", investmentCents: cents(1_000), valuationCapCents: BigInt(0), discountPercent: null };
  expectThrows(() => computeSafeConversion(BigInt(1_000_000), [badSafeCap]), "Zero valuation cap must be rejected");

  const discountOnlySafe: SafeInput = { id: "s", holderName: "X", investmentCents: cents(1_000), valuationCapCents: null, discountPercent: makeRational(BigInt(1), BigInt(5)) };
  expectThrows(() => computeSafeConversion(BigInt(1_000_000), [discountOnlySafe]), "Discount-only SAFEs must be rejected at conversion (explicitly unsupported in V1)");

  // Multiple SAFEs whose combined cap-implied ownership is >= 100%.
  const bigSafeA: SafeInput = { id: "sa", holderName: "A", investmentCents: cents(6_000_000), valuationCapCents: cents(10_000_000), discountPercent: null };
  const bigSafeB: SafeInput = { id: "sb", holderName: "B", investmentCents: cents(5_000_000), valuationCapCents: cents(10_000_000), discountPercent: null };
  expectThrows(() => computeSafeConversion(BigInt(1_000_000), [bigSafeA, bigSafeB]), "SAFEs summing to >=100% implied ownership must be rejected");

  expectThrows(() => runSimplePricedRound({ label: "Empty", stakeholders: [] }, { id: "r", name: "Bad", preMoneyValuationCents: cents(1_000), newMoneyCents: cents(100), optionPoolIncreaseShares: BigInt(0), newInvestorName: "X" }), "A cap table with zero shares must be rejected");
}

// --- Fixture M: ownership invariant ------------------------------------------

function test_M_ownership_invariant_holds_across_every_produced_state(): void {
  const founders = initialCapTable("State 0", [{ id: "founders", name: "Founders", kind: "founder", shares: BigInt(8_000_000) }]);
  const round: PricedRoundInput = { id: "seed", name: "Seed", preMoneyValuationCents: cents(8_000_000), newMoneyCents: cents(2_000_000), optionPoolIncreaseShares: BigInt(0), newInvestorName: "X" };
  const r = runSimplePricedRound(founders, round);
  assertOwnershipInvariant(r.postRoundState); // must not throw

  // A hand-corrupted state (shares that don't reflect reality) must be
  // caught, not silently accepted -- this is the one place a malformed
  // state can enter the system (a hand-built fixture), and it must fail.
  const corrupted: CapTableState = { label: "Corrupted", stakeholders: [{ id: "x", name: "X", kind: "founder", shares: -BigInt(5) }] };
  expectThrows(() => assertOwnershipInvariant(corrupted), "A stakeholder with negative shares must fail the invariant check");

  const empty: CapTableState = { label: "Empty", stakeholders: [] };
  expectThrows(() => assertOwnershipInvariant(empty), "A cap table with zero stakeholders must fail the invariant check");
}

// --- Fixture N: numerical precision / rounding -------------------------------

function test_N_numerical_precision_and_rounding(): void {
  expect(toPercentString(makeRational(BigInt(1), BigInt(3))) === "33.33%", `1/3 must display as 33.33%, got ${toPercentString(makeRational(BigInt(1), BigInt(3)))}`);
  expect(toPercentString(makeRational(BigInt(2), BigInt(3))) === "66.67%", `2/3 must display as 66.67%, got ${toPercentString(makeRational(BigInt(2), BigInt(3)))}`);

  // toFlooredShares always truncates toward zero, never rounds.
  expect(toFlooredShares(makeRational(BigInt(9_999_999), BigInt(10))) === BigInt(999_999), "toFlooredShares must truncate 999,999.9 down to 999,999, never round up to 1,000,000");

  // BigInt-based math must not lose precision on values beyond
  // Number.MAX_SAFE_INTEGER (2^53 - 1 = 9,007,199,254,740,991) -- this is
  // the entire reason a floating-point `number` is never used for share
  // counts or money anywhere in this engine.
  const huge = BigInt(10_000_000_000_000); // 10 trillion, well beyond MAX_SAFE_INTEGER
  const half = toFlooredShares(makeRational(huge, BigInt(2)));
  expect(half === BigInt(5_000_000_000_000), `Exact BigInt division of a value beyond Number.MAX_SAFE_INTEGER must not lose precision, got ${half}`);

  // Rounding is applied ONLY at display time -- verified by fixture D's
  // 111,111/1,111,111 case (9.999991...% displaying as "10.00%") and here
  // directly: the exact Rational for that fraction is NOT equal to
  // exactly 1/10 internally (no premature rounding of the intermediate).
  const notExactlyOneTenth = makeRational(BigInt(111_111), BigInt(1_111_111));
  expect(!(notExactlyOneTenth.num === BigInt(1) && notExactlyOneTenth.den === BigInt(10)), "The intermediate Rational must remain the exact, unrounded fraction -- only its STRING display rounds");
}

const TESTS = [
  test_A_two_founders_no_financing,
  test_B_golden_1_simple_priced_round,
  test_C_unequal_founders_priced_round,
  test_D_single_safe_standalone,
  test_E_external_cross_check_multiple_safes,
  test_F_golden_2_safe_plus_priced_seed,
  test_G_existing_option_pool_dilutes_proportionally,
  test_H_option_pool_expansion_does_not_change_safe_share_count,
  test_I_golden_3_safe_plus_option_pool_plus_priced_round,
  test_J_sequential_seed_then_series_a,
  test_K_runway,
  test_L_invalid_inputs_fail_loudly,
  test_M_ownership_invariant_holds_across_every_produced_state,
  test_N_numerical_precision_and_rounding,
];

function main(): void {
  console.log("\nFundraising Simulation (Phase 21A) tests");
  console.log("-".repeat(72));

  const failures: string[] = [];
  for (const test of TESTS) {
    const name = test.name;
    try {
      test();
      console.log(`PASS  ${name}`);
    } catch (error) {
      console.log(`FAIL  ${name}\n      ${(error as Error).message}`);
      failures.push(name);
    }
  }

  console.log("-".repeat(72));
  console.log(`${TESTS.length - failures.length}/${TESTS.length} passed`);

  if (failures.length > 0) {
    process.exit(1);
  }
}

main();
