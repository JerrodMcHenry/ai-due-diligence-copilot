// Phase 31C, Part 6 -- What-If semantic integrity tests.
//
// Regression coverage for a demonstrated, live-reproduced bug: "What if
// I interview 20 customers?" was labeled UPSIDE even though applying it
// dropped VPS 5.0 -> 3.7. The root cause (see whatIfScenarios.ts's own
// WhatIfScenario.direction docstring) is semantic, not a scoring defect:
// an ACTION/EXPERIMENT whose outcome isn't yet known was being labeled
// as if a favorable outcome had already happened.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/simulate.test.ts, run directly by Node's native TypeScript
// support.
//
// Run with:
//   node tests/whatIfSemantics.test.ts
// or:
//   npm run test:whatIfSemantics
import { getWhatIfScenarios } from "../components/idea-lab/whatIfScenarios.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function emptyAssumptions() {
  return {
    market: { competition_intensity: null },
    founder: { has_technical_cofounder: null, has_business_cofounder: null },
    gtm: { expected_cac: null },
    economics: { price_point: null, expected_gross_margin_pct: null },
    validation: { customer_interviews: null, paying_customers: null, monthly_revenue: null, retention_pct: null },
  };
}

function findScenario(scenarios: ReturnType<typeof getWhatIfScenarios>, id: string) {
  const scenario = scenarios.find((s) => s.id === id);
  if (!scenario) {
    throw new Error(`Expected a "${id}" scenario to be offered for this assumption set`);
  }
  return scenario;
}

function test_every_scenario_has_a_valid_direction() {
  const scenarios = getWhatIfScenarios(emptyAssumptions());
  const validDirections = new Set(["upside", "downside", "experiment"]);

  expect(scenarios.length > 0, "Sanity: a blank venture must still offer some scenarios");

  for (const scenario of scenarios) {
    expect(
      validDirections.has(scenario.direction),
      `Scenario "${scenario.id}" has an invalid direction: ${scenario.direction}`
    );
  }
}

// The exact demonstrated bug: interviewing customers is an experiment,
// not a proven favorable outcome.
function test_interview_scenarios_are_experiments_not_upside() {
  const scenarios = getWhatIfScenarios(emptyAssumptions());
  const interview20 = findScenario(scenarios, "interview-20");
  expect(
    interview20.direction === "experiment",
    `"interview-20" must be labeled "experiment" (an action with an unknown outcome), got "${interview20.direction}"`
  );

  const withSomeInterviews = { ...emptyAssumptions(), validation: { ...emptyAssumptions().validation, customer_interviews: 25 } };
  const moreScenarios = getWhatIfScenarios(withSomeInterviews);
  const interviewMore = findScenario(moreScenarios, "interview-more");
  expect(
    interviewMore.direction === "experiment",
    `"interview-more" must be labeled "experiment", got "${interviewMore.direction}"`
  );
}

// A bare pricing decision has no proven effect until the market
// responds -- never a guaranteed upside.
function test_setting_a_price_is_an_experiment() {
  const scenarios = getWhatIfScenarios(emptyAssumptions());
  const price = findScenario(scenarios, "price-29");
  expect(
    price.direction === "experiment",
    `"price-29" must be labeled "experiment" (a modeling decision, not a proven outcome), got "${price.direction}"`
  );
}

// A bare CAC assumption isn't inherently bad without a price to compare
// it against -- never a guaranteed downside.
function test_setting_a_bare_cac_is_an_experiment() {
  const scenarios = getWhatIfScenarios(emptyAssumptions());
  const cac = findScenario(scenarios, "cac-50");
  expect(
    cac.direction === "experiment",
    `"cac-50" must be labeled "experiment" (a bare assumption, not a proven outcome), got "${cac.direction}"`
  );
}

// A RISE in an ALREADY-KNOWN CAC is a genuine, unconditional downside --
// this one legitimately states an unfavorable outcome, unlike the bare
// cac-50 case above, and must stay labeled as such.
function test_cac_rising_from_a_known_value_stays_downside() {
  const withCac = { ...emptyAssumptions(), gtm: { expected_cac: 40 } };
  const scenarios = getWhatIfScenarios(withCac);
  const cacRises = findScenario(scenarios, "cac-rises");
  expect(cacRises.direction === "downside", `"cac-rises" must stay "downside", got "${cacRises.direction}"`);
}

// Scenarios that genuinely state a favorable outcome (not just an
// action) must remain upside -- this fix must not over-correct into
// mislabeling real good news as a neutral experiment.
function test_genuine_favorable_outcomes_stay_upside() {
  const scenarios = getWhatIfScenarios(emptyAssumptions());
  const payingScenario = findScenario(scenarios, "5-paying");
  expect(payingScenario.direction === "upside", `"5-paying" must stay "upside", got "${payingScenario.direction}"`);

  const cofounderScenario = findScenario(scenarios, "find-cofounder");
  expect(
    cofounderScenario.direction === "upside",
    `"find-cofounder" must stay "upside", got "${cofounderScenario.direction}"`
  );
}

// Scenarios that genuinely state an unfavorable outcome must remain
// downside.
function test_genuine_unfavorable_outcomes_stay_downside() {
  const withPaying = { ...emptyAssumptions(), validation: { ...emptyAssumptions().validation, paying_customers: 10 } };
  const scenarios = getWhatIfScenarios(withPaying);
  const churnScenario = findScenario(scenarios, "churn");
  expect(churnScenario.direction === "downside", `"churn" must stay "downside", got "${churnScenario.direction}"`);
}

// No scenario may claim "upside" or "downside" purely because a field
// transitioned from unset to set -- that transition alone says nothing
// about favorability. This is the general shape of the bug class, not
// just the one demonstrated instance.
function test_no_first_time_assumption_is_labeled_as_a_proven_outcome() {
  const scenarios = getWhatIfScenarios(emptyAssumptions());
  const firstTimeAssumptionIds = new Set(["interview-20", "price-29", "cac-50"]);

  for (const scenario of scenarios) {
    if (firstTimeAssumptionIds.has(scenario.id)) {
      expect(
        scenario.direction === "experiment",
        `"${scenario.id}" sets a previously-unknown assumption for the first time -- it must be "experiment", not a proven outcome`
      );
    }
  }
}

const TESTS = [
  test_every_scenario_has_a_valid_direction,
  test_interview_scenarios_are_experiments_not_upside,
  test_setting_a_price_is_an_experiment,
  test_setting_a_bare_cac_is_an_experiment,
  test_cac_rising_from_a_known_value_stays_downside,
  test_genuine_favorable_outcomes_stay_upside,
  test_genuine_unfavorable_outcomes_stay_downside,
  test_no_first_time_assumption_is_labeled_as_a_proven_outcome,
];

function main(): void {
  console.log("\nPhase 31C -- What-If Semantic Integrity tests");
  console.log("-".repeat(72));

  const failures: string[] = [];

  for (const test of TESTS) {
    try {
      test();
      console.log(`PASS  ${test.name}`);
    } catch (error) {
      console.log(`FAIL  ${test.name}\n      ${(error as Error).message}`);
      failures.push(test.name);
    }
  }

  console.log("-".repeat(72));
  console.log(`${TESTS.length - failures.length}/${TESTS.length} passed`);

  if (failures.length > 0) {
    process.exit(1);
  }
}

main();
