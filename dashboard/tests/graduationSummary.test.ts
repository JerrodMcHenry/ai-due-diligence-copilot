// Phase 31 -- Venture -> Startup Graduation V1 tests: the Data Transfer
// Contract's text builder (lib/ventureToStartupHandoff.ts). Same
// hand-rolled expect()/PASS-FAIL/main() convention as tests/journey.test.ts,
// run directly by Node's native TypeScript support. The one "@/types"
// import inside ventureToStartupHandoff.ts is `import type` only --
// erased entirely at runtime, per TypeScript's own erasable-syntax
// guarantee -- so this file needs no alias resolution to run under plain
// `node`.
//
// Run with:
//   node tests/graduationSummary.test.ts
// or:
//   npm run test:graduationSummary
import { buildGraduationSummaryText, type GraduationSourceVenture } from "../lib/ventureToStartupHandoff.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function emptyAssumptions() {
  return {
    target_customer: null,
    market: { market_description: null, estimated_market_size: null, competition_intensity: null },
    problem_solution: { problem_statement: null, solution_description: null, differentiation: null },
    founder: {
      founder_count: null,
      relevant_domain_experience_years: null,
      has_technical_cofounder: null,
      has_business_cofounder: null,
    },
    gtm: { primary_acquisition_strategy: null, expected_cac: null },
    economics: { pricing_model: null, price_point: null, expected_gross_margin_pct: null },
    validation: {
      customer_interviews: null,
      waitlist_signups: null,
      paying_customers: null,
      monthly_revenue: null,
      prior_monthly_revenue: null,
      retention_pct: null,
    },
    capital: { starting_capital: null, monthly_burn: null },
  };
}

function baseVenture(overrides: Partial<GraduationSourceVenture> = {}): GraduationSourceVenture {
  return {
    name: "ZZTest Co",
    description: null,
    industry: null,
    business_model: null,
    target_customer: null,
    stage: null,
    assumptions: emptyAssumptions(),
    ...overrides,
  };
}

function test_unknown_data_never_fabricated_as_text() {
  const result = buildGraduationSummaryText(baseVenture());
  expect(result.text === "", "An all-null venture must produce empty summary text, never fabricated content");
  expect(result.fieldsIncluded === 0, "An all-null venture must report zero fields included");
}

function test_no_null_or_undefined_leaks_into_text() {
  const venture = baseVenture({
    description: "We help restaurants schedule staff.",
    assumptions: {
      ...emptyAssumptions(),
      validation: { ...emptyAssumptions().validation, paying_customers: 5 },
    },
  });
  const result = buildGraduationSummaryText(venture);
  expect(!result.text.includes("null"), "Summary text must never contain the literal string 'null'");
  expect(!result.text.includes("undefined"), "Summary text must never contain the literal string 'undefined'");
  expect(result.text.includes("5"), "A real reported value must actually appear in the summary");
}

function test_capital_fields_never_included() {
  // Part 5/6: capital.* is explicitly DO NOT TRANSFER.
  const venture = baseVenture({
    assumptions: {
      ...emptyAssumptions(),
      capital: { starting_capital: 250000, monthly_burn: 15000 },
    },
  });
  const result = buildGraduationSummaryText(venture);
  expect(!result.text.includes("250000") && !result.text.includes("15000"), "Capital fields must never appear in the graduation summary");
}

function test_validation_fields_are_unlabeled_safe_evidence() {
  const venture = baseVenture({
    assumptions: {
      ...emptyAssumptions(),
      validation: { ...emptyAssumptions().validation, paying_customers: 12, monthly_revenue: 4000 },
    },
  });
  const result = buildGraduationSummaryText(venture);
  expect(result.text.includes("Paying customers: 12"), "Real paying-customer evidence must appear plainly");
  expect(result.text.includes("Monthly revenue: 4000"), "Real revenue evidence must appear plainly");
}

function test_review_fields_are_explicitly_labeled_as_assumptions() {
  const venture = baseVenture({
    assumptions: {
      ...emptyAssumptions(),
      market: { market_description: null, estimated_market_size: "Large", competition_intensity: null },
    },
  });
  const result = buildGraduationSummaryText(venture);
  expect(
    result.text.includes("Modeled assumptions from Idea Lab (not yet verified"),
    "A modeled-assumption field (market size) must be explicitly labeled as unverified, never presented as fact"
  );
}

function test_description_counts_as_a_transferred_field() {
  const venture = baseVenture({ description: "We help restaurants schedule staff." });
  const result = buildGraduationSummaryText(venture);
  expect(result.fieldsIncluded === 1, "A present description alone must count as exactly one transferred field");
}

const TESTS = [
  test_unknown_data_never_fabricated_as_text,
  test_no_null_or_undefined_leaks_into_text,
  test_capital_fields_never_included,
  test_validation_fields_are_unlabeled_safe_evidence,
  test_review_fields_are_explicitly_labeled_as_assumptions,
  test_description_counts_as_a_transferred_field,
];

function main(): void {
  console.log("\nPhase 31 -- Venture -> Startup Graduation V1 (summary text) tests");
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
