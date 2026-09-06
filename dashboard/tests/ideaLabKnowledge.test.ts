// Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and Decision
// Support. Tests for the two small pure modules behind the new Model tab
// (VentureUnderstandingPanel) and the qualitative-shift wording shared by
// ScenarioComparison/MissionsSection/CaptureWhatHappened.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as the rest of
// this directory (this repo has no jest/vitest) -- run directly by Node's
// native TypeScript support.
//
// Run with:
//   node tests/ideaLabKnowledge.test.ts
// or:
//   npm run test:ideaLabKnowledge
import { describeCategoryShift } from "../components/idea-lab/categoryChangeExplain.ts";
import { classifyCategoryKnowledge } from "../components/idea-lab/ventureKnowledge.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

// --- describeCategoryShift ---------------------------------------------

function test_describe_shift_null_to_scored_is_now_modeled(): void {
  expect(describeCategoryShift(null, 6.0) === "now modeled", `Expected "now modeled", got "${describeCategoryShift(null, 6.0)}"`);
}

function test_describe_shift_scored_to_null_is_no_longer_modeled(): void {
  expect(describeCategoryShift(6.0, null) === "no longer modeled", `Expected "no longer modeled", got "${describeCategoryShift(6.0, null)}"`);
}

function test_describe_shift_higher_score_is_strengthened(): void {
  expect(describeCategoryShift(5.0, 7.0) === "strengthened", `Expected "strengthened", got "${describeCategoryShift(5.0, 7.0)}"`);
}

function test_describe_shift_lower_score_is_weakened(): void {
  // The directive's own worked bug: adding paying customers can lower a
  // category/aggregate through the scoring engine's own renormalization
  // -- this must read as "weakened," never silently hidden or inverted.
  expect(describeCategoryShift(7.0, 5.0) === "weakened", `Expected "weakened", got "${describeCategoryShift(7.0, 5.0)}"`);
}

function test_describe_shift_tiny_change_is_null(): void {
  expect(describeCategoryShift(5.0, 5.02) === null, "A sub-threshold change must not be described as any kind of shift");
}

function test_describe_shift_never_returns_a_number(): void {
  // The whole point of this function existing: every possible return
  // value must be a plain word, never a numeric delta string.
  const cases = [
    describeCategoryShift(null, 6.0),
    describeCategoryShift(6.0, null),
    describeCategoryShift(5.0, 7.0),
    describeCategoryShift(7.0, 5.0),
    describeCategoryShift(5.0, 5.0),
  ];
  for (const result of cases) {
    if (result !== null) {
      expect(!/\d/.test(result), `Expected no digit in "${result}"`);
    }
  }
}

// --- classifyCategoryKnowledge -------------------------------------------

function test_classify_only_validation_is_evidence_based(): void {
  const categories = [
    { key: "market_potential", label: "Market Potential", score: 6.0, basis: ["Estimated market size: Large"] },
    { key: "validation", label: "Validation", score: 5.0, basis: ["3 paying customers reported"] },
  ];
  const result = classifyCategoryKnowledge(categories);
  const market = result.find((c) => c.key === "market_potential")!;
  const validation = result.find((c) => c.key === "validation")!;
  expect(market.isEvidenceBased === false, "market_potential must never be classified as evidence-based");
  expect(validation.isEvidenceBased === true, "validation must always be classified as evidence-based");
}

function test_classify_null_score_means_no_signal(): void {
  const categories = [{ key: "founder_readiness", label: "Founder Readiness", score: null, basis: [] }];
  const result = classifyCategoryKnowledge(categories);
  expect(result[0].hasSignal === false, "A null score must classify as hasSignal: false");
  expect(result[0].facts.length === 0, "An Unavailable category must carry no facts");
}

function test_classify_scored_category_carries_its_real_basis_verbatim(): void {
  const categories = [
    { key: "economic_potential", label: "Economic Potential", score: 6.5, basis: ["Assumed gross margin of 78%"] },
  ];
  const result = classifyCategoryKnowledge(categories);
  expect(result[0].hasSignal === true, "A scored category must classify as hasSignal: true");
  expect(
    result[0].facts.length === 1 && result[0].facts[0] === "Assumed gross margin of 78%",
    "Basis text must be reused verbatim, never rewritten or summarized"
  );
}

function test_classify_never_exposes_a_score_number(): void {
  const categories = [
    { key: "validation", label: "Validation", score: 6.5, basis: ["5 paying customers reported"] },
    { key: "market_potential", label: "Market Potential", score: null, basis: [] },
  ];
  const result = classifyCategoryKnowledge(categories);
  const serialized = JSON.stringify(result);
  expect(!/"score"/.test(serialized), `classifyCategoryKnowledge's output must never carry a "score" field, got: ${serialized}`);
}

const TESTS = [
  test_describe_shift_null_to_scored_is_now_modeled,
  test_describe_shift_scored_to_null_is_no_longer_modeled,
  test_describe_shift_higher_score_is_strengthened,
  test_describe_shift_lower_score_is_weakened,
  test_describe_shift_tiny_change_is_null,
  test_describe_shift_never_returns_a_number,
  test_classify_only_validation_is_evidence_based,
  test_classify_null_score_means_no_signal,
  test_classify_scored_category_carries_its_real_basis_verbatim,
  test_classify_never_exposes_a_score_number,
];

function main(): void {
  console.log("\nPhase 34A -- Idea Lab knowledge-state tests");
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
