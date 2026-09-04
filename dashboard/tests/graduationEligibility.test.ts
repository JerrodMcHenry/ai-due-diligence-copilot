// Phase 31 -- Venture -> Startup Graduation V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/journey.test.ts (this repo has no jest/vitest), run directly by
// Node's native TypeScript support.
//
// Run with:
//   node tests/graduationEligibility.test.ts
// or:
//   npm run test:graduation
import { isEligibleForGraduationSuggestion } from "../lib/journey/resolveGraduationEligibility.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function test_null_validation_is_not_eligible() {
  expect(isEligibleForGraduationSuggestion(null) === false, "null validation must not be eligible");
}

function test_all_null_fields_not_eligible() {
  expect(
    isEligibleForGraduationSuggestion({ paying_customers: null, monthly_revenue: null }) === false,
    "all-null fields must not be eligible"
  );
}

function test_zero_values_not_eligible() {
  expect(
    isEligibleForGraduationSuggestion({ paying_customers: 0, monthly_revenue: 0 }) === false,
    "zero paying customers and zero revenue must not be eligible -- never mistaken for real traction"
  );
}

function test_real_paying_customers_is_eligible() {
  expect(
    isEligibleForGraduationSuggestion({ paying_customers: 1, monthly_revenue: null }) === true,
    "1+ real paying customers must be eligible"
  );
}

function test_real_revenue_is_eligible() {
  expect(
    isEligibleForGraduationSuggestion({ paying_customers: null, monthly_revenue: 500 }) === true,
    "real monthly revenue must be eligible"
  );
}

function test_negative_values_not_eligible() {
  // Defensive: the backend's own Pydantic ge=0 constraint should prevent
  // this, but the frontend check must never treat corrupt/negative data
  // as real traction either.
  expect(
    isEligibleForGraduationSuggestion({ paying_customers: -1, monthly_revenue: -1 }) === false,
    "negative values must not be eligible"
  );
}

const TESTS = [
  test_null_validation_is_not_eligible,
  test_all_null_fields_not_eligible,
  test_zero_values_not_eligible,
  test_real_paying_customers_is_eligible,
  test_real_revenue_is_eligible,
  test_negative_values_not_eligible,
];

function main(): void {
  console.log("\nPhase 31 -- Venture -> Startup Graduation V1 (eligibility) tests");
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
