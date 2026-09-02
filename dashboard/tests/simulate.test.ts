// Simulate V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/journey.test.ts and tests/concepts.test.ts (this repo has no
// jest/vitest), run directly by Node's native TypeScript support -- no
// build step, no bundler, which is why lib/simulate/* is written with
// zero "@/..." alias imports (see those files' own docstrings).
//
// Run with:
//   node tests/simulate.test.ts
// or:
//   npm run test:simulate
import { hasCommercialScale } from "../lib/simulate/hasCommercialScale.ts";
import { diffScenarioAssumptions } from "../lib/simulate/assumptionDiff.ts";
import { computeDirectConsequences } from "../lib/simulate/directConsequences.ts";
import { getWhatIfScenarios } from "../components/idea-lab/whatIfScenarios.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function emptyAssumptions() {
  return {
    market: { competition_intensity: null as string | null },
    founder: { has_technical_cofounder: null as boolean | null, has_business_cofounder: null as boolean | null },
    gtm: { expected_cac: null as number | null },
    economics: { price_point: null as number | null, expected_gross_margin_pct: null as number | null },
    validation: {
      customer_interviews: null as number | null,
      paying_customers: null as number | null,
      monthly_revenue: null as number | null,
      retention_pct: null as number | null,
    },
  };
}

// --- hasCommercialScale ---------------------------------------------------

function test_has_commercial_scale_matches_the_original_whatifscenarios_threshold(): void {
  expect(hasCommercialScale(10, null) === true, "10 paying customers must count as commercial scale");
  expect(hasCommercialScale(9, null) === false, "9 paying customers must not count as commercial scale");
  expect(hasCommercialScale(null, 10_000) === true, "$10,000 monthly revenue must count as commercial scale");
  expect(hasCommercialScale(null, 9_999) === false, "$9,999 monthly revenue must not count as commercial scale");
  expect(hasCommercialScale(null, null) === false, "No signal at all must not count as commercial scale");
}

function test_what_if_scenarios_still_use_the_shared_threshold(): void {
  // Part 2's own regression case, still true after the refactor: a
  // venture with 186 paying customers must never be offered "interview
  // 20 customers" -- confirms the extraction didn't change behavior.
  const a = emptyAssumptions();
  a.validation.paying_customers = 186;
  a.validation.monthly_revenue = 11_800_000 / 12;
  const scenarios = getWhatIfScenarios(a);
  expect(
    !scenarios.some((s) => s.id === "interview-20" || s.id === "interview-more"),
    "A commercial-scale venture must not be offered an interview-count scenario"
  );
}

// --- diffScenarioAssumptions -----------------------------------------------

function test_diff_returns_nothing_when_assumptions_are_identical(): void {
  const a = emptyAssumptions();
  a.economics.price_point = 199;
  const rows = diffScenarioAssumptions(a, { ...a });
  expect(rows.length === 0, "Identical assumptions must produce zero diff rows");
}

function test_diff_reports_only_changed_fields(): void {
  const current = emptyAssumptions();
  current.economics.price_point = 199;
  current.validation.paying_customers = 20;

  const scenario = emptyAssumptions();
  scenario.economics.price_point = 249;
  scenario.validation.paying_customers = 20; // unchanged

  const rows = diffScenarioAssumptions(current, scenario);
  expect(rows.length === 1, `Expected exactly 1 changed row, got ${rows.length}`);
  expect(rows[0].key === "price_point", `Expected the price_point row, got "${rows[0].key}"`);
  expect(rows[0].before === "$199" && rows[0].after === "$249", `Unexpected formatting: ${rows[0].before} -> ${rows[0].after}`);
}

function test_diff_unknown_to_known_reads_not_known_never_zero(): void {
  // Part 18's own exact worked example: "Not known -> $50", never "$0 -> $50".
  const current = emptyAssumptions();
  const scenario = emptyAssumptions();
  scenario.gtm.expected_cac = 50;

  const rows = diffScenarioAssumptions(current, scenario);
  const cacRow = rows.find((r) => r.key === "expected_cac")!;
  expect(cacRow.before === "Not known", `Expected "Not known", got "${cacRow.before}"`);
  expect(cacRow.after === "$50", `Expected "$50", got "${cacRow.after}"`);
  expect(!cacRow.before.includes("$0"), 'Unknown must never render as "$0"');
}

function test_diff_covers_percent_boolean_and_text_fields(): void {
  const current = emptyAssumptions();
  const scenario = emptyAssumptions();
  scenario.economics.expected_gross_margin_pct = 76;
  scenario.founder.has_technical_cofounder = true;
  scenario.market.competition_intensity = "High";

  const rows = diffScenarioAssumptions(current, scenario);
  const byKey = Object.fromEntries(rows.map((r) => [r.key, r]));

  expect(byKey.expected_gross_margin_pct?.after === "76%", `Expected "76%", got "${byKey.expected_gross_margin_pct?.after}"`);
  expect(byKey.has_technical_cofounder?.before === "Not known", "A null boolean must read as Not known, not No");
  expect(byKey.has_technical_cofounder?.after === "Yes", `Expected "Yes", got "${byKey.has_technical_cofounder?.after}"`);
  expect(byKey.competition_intensity?.after === "High", `Expected "High", got "${byKey.competition_intensity?.after}"`);
}

// --- computeDirectConsequences ---------------------------------------------

function test_direct_consequences_computes_mrr_and_arr_when_valid(): void {
  const a = emptyAssumptions();
  a.economics.price_point = 199;
  a.validation.paying_customers = 50;

  const results = computeDirectConsequences(a);
  const mrr = results.find((r) => r.key === "modeled_monthly_revenue");
  const arr = results.find((r) => r.key === "modeled_annual_revenue");

  expect(mrr !== undefined, "Expected a modeled monthly revenue consequence");
  expect(mrr!.explanation.includes("$9,950"), `Expected "$9,950" (199 x 50) in "${mrr!.explanation}"`);
  expect(arr !== undefined, "Expected a modeled annual revenue consequence");
  expect(arr!.explanation.includes("$119,400"), `Expected "$119,400" (9,950 x 12) in "${arr!.explanation}"`);
}

function test_direct_consequences_is_empty_when_price_or_customers_unknown(): void {
  const priceOnly = emptyAssumptions();
  priceOnly.economics.price_point = 199;
  expect(computeDirectConsequences(priceOnly).length === 0, "Price alone (no customers) must not fabricate a revenue figure");

  const customersOnly = emptyAssumptions();
  customersOnly.validation.paying_customers = 50;
  expect(computeDirectConsequences(customersOnly).length === 0, "Customers alone (no price) must not fabricate a revenue figure");

  expect(computeDirectConsequences(emptyAssumptions()).length === 0, "No data at all must not fabricate a revenue figure");
}

function test_direct_consequences_never_predicts_anything_beyond_arithmetic(): void {
  // Part 9's explicit anti-pattern check: no percentage-growth language,
  // no churn/demand claims anywhere in the generated copy.
  const a = emptyAssumptions();
  a.economics.price_point = 199;
  a.validation.paying_customers = 50;
  const text = computeDirectConsequences(a).map((r) => r.explanation).join(" ").toLowerCase();

  expect(!/will increase|will grow|will churn|demand|forecast/.test(text), `Consequence copy must stay arithmetic-only, got: "${text}"`);
  expect(text.includes("if") && text.includes("modeled"), 'Every consequence must be framed as an "if/then... modeled" scenario calculation');
}

const TESTS = [
  test_has_commercial_scale_matches_the_original_whatifscenarios_threshold,
  test_what_if_scenarios_still_use_the_shared_threshold,
  test_diff_returns_nothing_when_assumptions_are_identical,
  test_diff_reports_only_changed_fields,
  test_diff_unknown_to_known_reads_not_known_never_zero,
  test_diff_covers_percent_boolean_and_text_fields,
  test_direct_consequences_computes_mrr_and_arr_when_valid,
  test_direct_consequences_is_empty_when_price_or_customers_unknown,
  test_direct_consequences_never_predicts_anything_beyond_arithmetic,
];

function main(): void {
  console.log("\nSimulate V1 tests");
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
