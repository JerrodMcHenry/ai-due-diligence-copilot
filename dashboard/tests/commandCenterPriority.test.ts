// Phase 38B -- Founder Command Center V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/graduationEligibility.test.ts (this repo has no jest/vitest), run
// directly by Node's native TypeScript support.
//
// Run with:
//   node tests/commandCenterPriority.test.ts
import { isFinancialConstraintActive } from "../lib/build/commandCenterPriority.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function test_null_derived_is_not_a_constraint() {
  expect(
    isFinancialConstraintActive(null) === false,
    "no Finance data at all must never be treated as a constraint"
  );
}

function test_insufficient_data_is_not_a_constraint() {
  expect(
    isFinancialConstraintActive({ status: "insufficient_data" }) === false,
    "unknown revenue/expenses must not manufacture urgency"
  );
}

function test_cash_flow_positive_is_not_a_constraint() {
  // Test case C of the 38B directive: a cash-flow-positive company must
  // never have Finance manufacture urgency merely because Finance data
  // exists.
  expect(
    isFinancialConstraintActive({ status: "cash_flow_positive" }) === false,
    "a cash-flow-positive company must never be flagged as a financial constraint"
  );
}

function test_break_even_is_not_a_constraint() {
  expect(
    isFinancialConstraintActive({ status: "break_even" }) === false,
    "break-even must not be flagged as a financial constraint"
  );
}

function test_burning_with_any_runway_is_not_a_constraint() {
  // Test case D: a company with known cash and positive burn must NOT
  // have a modeled consequence shown as an override unless the approved
  // rule (out_of_cash) actually fires -- "burning" alone, regardless of
  // how few or many months of runway remain, is deliberately never
  // treated as urgent here, because no existing methodology establishes
  // a runway-months cutoff and this function must never invent one.
  expect(
    isFinancialConstraintActive({ status: "burning" }) === false,
    "burning (any runway) must not be flagged as a financial constraint -- no invented threshold"
  );
}

function test_out_of_cash_is_a_constraint() {
  expect(
    isFinancialConstraintActive({ status: "out_of_cash" }) === true,
    "out_of_cash (cash at or below zero while burn is positive) is the one real, existing, objective override"
  );
}

const TESTS = [
  test_null_derived_is_not_a_constraint,
  test_insufficient_data_is_not_a_constraint,
  test_cash_flow_positive_is_not_a_constraint,
  test_break_even_is_not_a_constraint,
  test_burning_with_any_runway_is_not_a_constraint,
  test_out_of_cash_is_a_constraint,
];

function main(): void {
  console.log("\nPhase 38B -- Founder Command Center V1 (financial priority) tests");
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
