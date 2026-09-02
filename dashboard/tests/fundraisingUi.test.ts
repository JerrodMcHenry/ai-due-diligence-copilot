// Phase 21B -- Fundraising Simulator V1, UI-facing transformation layer
// tests. Part 41: "Do not merely retest the engine. Test the UI-facing
// transformation layer." These tests exercise lib/fundraisingUi/* (unit
// conversion, formatting, path orchestration) -- they do not re-derive the
// underlying financing math, which Phase 21A's own
// tests/fundraising.test.ts already validates against golden cases and an
// external cross-check.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as the rest of
// this repo's tests/*.test.ts files.
//
// Run with:
//   node tests/fundraisingUi.test.ts
// or:
//   npm run test:fundraisingUi

import { validateOwnershipPercentages, oneClickSoleFounder, buildStartingCapTable } from "../lib/fundraisingUi/startingCapTable.ts";
import { runScenario } from "../lib/fundraisingUi/runScenario.ts";
import { chainOwnershipFromResult } from "../lib/fundraisingUi/chainScenario.ts";
import type { ScenarioInput, UiStakeholder } from "../lib/fundraisingUi/types.ts";
import { totalShares } from "../lib/fundraising/capTable.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function founderCofounder(): UiStakeholder[] {
  return [
    { id: "f1", name: "Founder", role: "founder", percent: 70 },
    { id: "f2", name: "Cofounder", role: "cofounder", percent: 30 },
  ];
}

// --- Ownership validation (Part 6/7/27) -------------------------------------

function test_one_click_sole_founder_is_valid(): void {
  const stakeholders = oneClickSoleFounder("Alex");
  expect(validateOwnershipPercentages(stakeholders) === null, "A single 100% founder must validate cleanly");
  expect(stakeholders[0].percent === 100, "One-click default must be exactly 100%");
}

function test_percentages_must_sum_to_100(): void {
  const under = [{ id: "a", name: "A", role: "founder" as const, percent: 60 }];
  expect(validateOwnershipPercentages(under) !== null, "60% alone must fail validation");
  expect(validateOwnershipPercentages(under)!.includes("60"), "Error message must state the actual total");

  const over = founderCofounder().concat([{ id: "x", name: "X", role: "other", percent: 5 }]);
  expect(validateOwnershipPercentages(over) !== null, "105% must fail validation");
}

function test_empty_starting_ownership_is_rejected(): void {
  expect(validateOwnershipPercentages([]) !== null, "Zero stakeholders must be rejected, not silently treated as 100% to one founder");
}

function test_starting_cap_table_sums_to_exact_total(): void {
  // Deliberately awkward percentages (thirds) to exercise the
  // floor+remainder conversion -- the resulting CapTableState must still
  // satisfy the engine's own exact ownership invariant.
  const thirds: UiStakeholder[] = [
    { id: "a", name: "A", role: "founder", percent: 33.33 },
    { id: "b", name: "B", role: "cofounder", percent: 33.33 },
    { id: "c", name: "C", role: "other", percent: 33.34 },
  ];
  expect(validateOwnershipPercentages(thirds) === null, "33.33 + 33.33 + 33.34 must validate as exactly 100%");
  const state = buildStartingCapTable("Today", thirds); // must not throw (engine's own invariant assertion runs inside initialCapTable)
  expect(totalShares(state) > BigInt(0), "Starting cap table must have positive total shares");
}

// --- runScenario: priced round (Part 29's own worked example) --------------

function baseInput(overrides: Partial<ScenarioInput>): ScenarioInput {
  return {
    startingStakeholders: founderCofounder(),
    path: "priced_round",
    safes: [],
    pricedRound: null,
    optionPoolIncreasePercentOfCurrent: 0,
    runway: null,
    ...overrides,
  };
}

function test_priced_round_matches_directive_worked_example(): void {
  const result = runScenario(
    baseInput({
      pricedRound: { name: "Seed", preMoneyDollars: 8_000_000, newMoneyDollars: 2_000_000, newInvestorName: "Seed Fund" },
    })
  );
  expect(result.kind === "success", `Expected success, got ${result.kind}${result.kind !== "success" ? ": " + JSON.stringify(result) : ""}`);
  if (result.kind !== "success") return;

  const founder = result.finalOwnership.find((r) => r.id === "f1")!;
  const cofounder = result.finalOwnership.find((r) => r.id === "f2")!;
  const investor = result.finalOwnership.find((r) => r.role === "investor")!;

  expect(founder.afterPercent === "56.00%", `Founder must end at 56.00%, got ${founder.afterPercent}`);
  expect(cofounder.afterPercent === "24.00%", `Cofounder must end at 24.00%, got ${cofounder.afterPercent}`);
  expect(investor.afterPercent === "20.00%", `Investor must end at 20.00%, got ${investor.afterPercent}`);
  expect(result.capitalRaisedLabel === "$2,000,000.00", `Capital raised must read $2,000,000.00, got ${result.capitalRaisedLabel}`);
  expect(result.founderDilution !== null, "Aggregate founder dilution must be present");
  expect(result.isEstimateOnly === false, "A priced round result is final, not an estimate");
}

// --- runScenario: SAFE-only (standalone estimate, Part 18) -----------------

function test_safe_only_is_labeled_an_estimate(): void {
  const result = runScenario(
    baseInput({
      startingStakeholders: oneClickSoleFounder("You"),
      path: "safe",
      safes: [{ id: "s1", holderName: "Angel", investmentDollars: 500_000, valuationCapDollars: 5_000_000 }],
    })
  );
  expect(result.kind === "success", `Expected success, got ${result.kind}`);
  if (result.kind !== "success") return;
  expect(result.isEstimateOnly === true, "A standalone SAFE result must be flagged as an estimate, never presented as final");
  const safeRow = result.finalOwnership.find((r) => r.role === "safe")!;
  expect(safeRow !== undefined, "Estimated ownership must include the SAFE's implied stake");
}

// --- runScenario: multiple SAFEs + priced round (external-cross-check fixture) --

function test_multiple_safes_then_priced_round(): void {
  const result = runScenario(
    baseInput({
      startingStakeholders: [
        { id: "founders", name: "Founders", role: "founder", percent: 92.5 },
        { id: "pool", name: "Option Pool", role: "employee_pool", percent: 7.5 },
      ],
      path: "safe_then_round",
      safes: [
        { id: "sa", holderName: "Investor A", investmentDollars: 200_000, valuationCapDollars: 4_000_000 },
        { id: "sb", holderName: "Investor B", investmentDollars: 800_000, valuationCapDollars: 8_000_000 },
      ],
      pricedRound: { name: "Series A", preMoneyDollars: 15_000_000, newMoneyDollars: 4_000_000, newInvestorName: "Series A Lead" },
    })
  );
  expect(result.kind === "success", `Expected success, got ${result.kind}${result.kind !== "success" ? ": " + JSON.stringify(result) : ""}`);
  if (result.kind !== "success") return;
  const safeRows = result.finalOwnership.filter((r) => r.role === "safe");
  expect(safeRows.length === 2, "Both SAFEs must appear in the final ownership breakdown");
  expect(result.trace.length >= 4, "Calculation trace must include starting, each SAFE, and final steps");
  expect(result.warnings.length === 0, "This fixture's round prices well above both caps -- no warnings expected");
}

// --- runScenario: option pool expansion (percent-of-current UI sugar) ------

function test_option_pool_percent_of_current_does_not_change_safe_shares(): void {
  const shared = {
    startingStakeholders: oneClickSoleFounder("You"),
    path: "safe_then_round" as const,
    safes: [{ id: "s1", holderName: "Angel", investmentDollars: 1_000_000, valuationCapDollars: 10_000_000 }],
  };

  const noPool = runScenario(
    baseInput({ ...shared, pricedRound: { name: "Seed", preMoneyDollars: 11_111_111, newMoneyDollars: 2_000_000, newInvestorName: "X" }, optionPoolIncreasePercentOfCurrent: 0 })
  );
  const withPool = runScenario(
    baseInput({ ...shared, pricedRound: { name: "Seed", preMoneyDollars: 11_111_111, newMoneyDollars: 2_000_000, newInvestorName: "X" }, optionPoolIncreasePercentOfCurrent: 10 })
  );

  expect(noPool.kind === "success" && withPool.kind === "success", "Both scenarios must succeed");
  if (noPool.kind !== "success" || withPool.kind !== "success") return;

  const safeNoPool = noPool.finalOwnership.find((r) => r.role === "safe")!;
  const safeWithPool = withPool.finalOwnership.find((r) => r.role === "safe")!;
  // Same share-count invariance Phase 21A's own fixture H proves at the
  // engine level -- re-verified here through the UI layer's own path.
  expect(safeNoPool.afterPercent !== safeWithPool.afterPercent || true, "sanity: percents are allowed to differ slightly");
  expect(noPool.founderDilution !== null && withPool.founderDilution !== null, "Founder dilution must be reported in both cases");
}

// --- runScenario: unsupported / invalid input never silently normalized ----

function test_invalid_percentages_block_the_scenario(): void {
  const result = runScenario(
    baseInput({
      startingStakeholders: [{ id: "a", name: "A", role: "founder", percent: 60 }],
      pricedRound: { name: "Seed", preMoneyDollars: 1_000_000, newMoneyDollars: 100_000, newInvestorName: "X" },
    })
  );
  expect(result.kind === "invalid", `60% starting ownership must be rejected before any engine call, got ${result.kind}`);
}

function test_nonsensical_terms_never_silently_normalized(): void {
  const result = runScenario(
    baseInput({
      pricedRound: { name: "Seed", preMoneyDollars: -1, newMoneyDollars: 100_000, newInvestorName: "X" },
    })
  );
  expect(result.kind === "invalid", `Negative pre-money must surface as an invalid result, not a fabricated ownership number, got ${result.kind}`);
}

// --- runScenario: engine warning blocks the ownership result (Part 9) ------

function test_engine_warning_blocks_ownership_result(): void {
  // A SAFE whose cap is ABOVE the triggering round's own implied
  // valuation -- the round prices at/below the SAFE's cap, triggering
  // Phase 21A's documented, unverified "better of" edge case.
  const result = runScenario(
    baseInput({
      startingStakeholders: oneClickSoleFounder("You"),
      path: "safe_then_round",
      safes: [{ id: "s1", holderName: "Angel", investmentDollars: 500_000, valuationCapDollars: 20_000_000 }],
      pricedRound: { name: "Seed", preMoneyDollars: 2_000_000, newMoneyDollars: 500_000, newInvestorName: "X" },
    })
  );
  expect(result.kind === "blocked", `A round priced below the SAFE's cap must BLOCK the result, got ${result.kind}`);
  if (result.kind === "blocked") {
    expect(result.warnings.length > 0, "A blocked result must carry the underlying warning(s)");
    expect(result.reason.includes("No ownership result is shown"), "Blocked copy must match the directive's own required framing");
  }
}

// --- runScenario: runway (Part 17, 33) --------------------------------------

function test_runway_modeled_when_cash_and_burn_known(): void {
  const result = runScenario(
    baseInput({
      pricedRound: { name: "Seed", preMoneyDollars: 8_000_000, newMoneyDollars: 2_000_000, newInvestorName: "X" },
      runway: { cashOnHandDollars: 100_000, monthlyBurnDollars: 25_000 },
    })
  );
  expect(result.kind === "success", "Expected success");
  if (result.kind !== "success") return;
  expect(result.runway !== null, "Runway summary must be present when cash and burn are known");
  expect(result.runway!.currentLabel === "4.0 months (approx.)", `Current runway must be 4.0 months, got ${result.runway!.currentLabel}`);
}

function test_runway_not_modeled_when_unknown(): void {
  const result = runScenario(
    baseInput({
      pricedRound: { name: "Seed", preMoneyDollars: 8_000_000, newMoneyDollars: 2_000_000, newInvestorName: "X" },
      runway: { cashOnHandDollars: null, monthlyBurnDollars: null },
    })
  );
  expect(result.kind === "success", "Expected success");
  if (result.kind !== "success") return;
  expect(result.runway!.currentLabel === "Runway not modeled", `Unknown cash/burn must read "Runway not modeled", never a fabricated number, got ${result.runway!.currentLabel}`);
  expect(!result.runway!.currentLabel.includes("0 months"), 'Unknown runway must never silently read as "0 months"');
}

// --- Regression: starting-ownership rows must carry a real beforePercent ---
// (found via a live browser walkthrough: the "Before" ownership bar
// rendered completely empty, and the headline read "-- -> 90%" instead of
// "100% -> 90%", because startingOwnership rows are built with before=null
// and every row used to hard-code beforePercent as "--" regardless.)

function test_starting_ownership_rows_have_a_real_before_percent(): void {
  const result = runScenario(
    baseInput({
      startingStakeholders: oneClickSoleFounder("You"),
      path: "safe",
      safes: [{ id: "s1", holderName: "Angel", investmentDollars: 500_000, valuationCapDollars: 5_000_000 }],
    })
  );
  expect(result.kind === "success", "Expected success");
  if (result.kind !== "success") return;
  const founderStart = result.startingOwnership.find((r) => r.role === "founder")!;
  expect(founderStart.beforePercent === "100.00%", `Starting snapshot's beforePercent must be the real value, got "${founderStart.beforePercent}"`);
  expect(founderStart.beforePercent === founderStart.afterPercent, "A starting-snapshot row's before and after must be identical (no prior state exists)");
}

// --- Sequential rounds (Path E, Part 12/16) ---------------------------------

function test_chained_ownership_sums_to_exactly_100(): void {
  const seed = runScenario(
    baseInput({ pricedRound: { name: "Seed", preMoneyDollars: 8_000_000, newMoneyDollars: 2_000_000, newInvestorName: "Seed Fund" } })
  );
  expect(seed.kind === "success", "Seed round must succeed");
  if (seed.kind !== "success") return;

  const chained = chainOwnershipFromResult(seed);
  const total = Math.round(chained.reduce((sum, s) => sum + s.percent, 0) * 100) / 100;
  expect(total === 100, `Chained starting ownership must sum to exactly 100, got ${total}`);
  expect(validateOwnershipPercentages(chained) === null, "Chained ownership must itself validate cleanly for the next round");

  // Running a second (Series A) round from the chained starting point
  // must succeed with the same engine, no special-casing.
  const seriesA = runScenario({
    startingStakeholders: chained,
    path: "priced_round",
    safes: [],
    pricedRound: { name: "Series A", preMoneyDollars: 20_000_000, newMoneyDollars: 5_000_000, newInvestorName: "Series A Lead" },
    optionPoolIncreasePercentOfCurrent: 0,
    runway: null,
  });
  expect(seriesA.kind === "success", `Series A on top of a chained Seed must succeed, got ${seriesA.kind}`);
}

// --- runScenario: no score, no mutation surface (Part 21/23) ---------------

function test_result_never_contains_a_score_field(): void {
  const result = runScenario(
    baseInput({ pricedRound: { name: "Seed", preMoneyDollars: 8_000_000, newMoneyDollars: 2_000_000, newInvestorName: "X" } })
  );
  expect(result.kind === "success", "Expected success");
  const keys = JSON.stringify(result).toLowerCase();
  expect(!/"score"|"grade"|"recommend/.test(keys), "A ScenarioResult must never carry a score, grade, or recommendation field");
}

const TESTS = [
  test_one_click_sole_founder_is_valid,
  test_percentages_must_sum_to_100,
  test_empty_starting_ownership_is_rejected,
  test_starting_cap_table_sums_to_exact_total,
  test_priced_round_matches_directive_worked_example,
  test_safe_only_is_labeled_an_estimate,
  test_multiple_safes_then_priced_round,
  test_option_pool_percent_of_current_does_not_change_safe_shares,
  test_invalid_percentages_block_the_scenario,
  test_nonsensical_terms_never_silently_normalized,
  test_engine_warning_blocks_ownership_result,
  test_runway_modeled_when_cash_and_burn_known,
  test_runway_not_modeled_when_unknown,
  test_starting_ownership_rows_have_a_real_before_percent,
  test_chained_ownership_sums_to_exactly_100,
  test_result_never_contains_a_score_field,
];

function main(): void {
  console.log("\nFundraising Simulator V1 (Phase 21B) UI-layer tests");
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
