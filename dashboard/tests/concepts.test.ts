// Learn V1 -- Contextual Founder Education tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/playbooks.test.ts and tests/journey.test.ts (this repo has no
// jest/vitest), run directly by Node's native TypeScript support -- no
// build step, no bundler, which is why content/concepts/* and
// lib/learn/personalizeVpsCategoryScore.ts are written with zero
// "@/..." alias imports (see those files' own docstrings).
//
// Run with:
//   node tests/concepts.test.ts
// or:
//   npm run test:concepts
import {
  getMetricConcept,
  getMetricConceptForWhatIfScenario,
  getVpsCategoryConcept,
} from "../content/concepts/index.ts";
import { METRIC_CONCEPTS, VPS_CATEGORY_CONCEPTS, WHAT_IF_SCENARIO_CONCEPTS } from "../content/concepts/data.ts";
import { getPlaybookBySlug } from "../content/playbooks/index.ts";
import { personalizeVpsCategoryScore } from "../lib/learn/personalizeVpsCategoryScore.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

// app/ai/vps_scoring.py::VPS_CATEGORIES -- the fixed, frozen six-category
// vocabulary. Hardcoded here (not imported -- there is nothing to import
// across the Python/TypeScript boundary) the same way
// tests/playbooks.test.ts hardcodes REQUIRED_SLUGS.
const VPS_CATEGORY_KEYS = [
  "market_potential",
  "problem_solution",
  "founder_readiness",
  "gtm_feasibility",
  "economic_potential",
  "validation",
];

// --- VPS category education (Part 5/6) --------------------------------

function test_every_vps_category_has_an_explanation(): void {
  for (const key of VPS_CATEGORY_KEYS) {
    const concept = getVpsCategoryConcept(key);
    expect(concept !== undefined, `Missing VpsCategoryConcept for "${key}"`);
    expect(concept!.question.trim().length > 0, `${key}: question must not be empty`);
    expect(concept!.whyItMatters.trim().length > 0, `${key}: whyItMatters must not be empty`);
  }
}

function test_no_extra_vps_category_concepts_exist(): void {
  // Every key in the registry must be a real category -- a stale/typo'd
  // key would silently never render anywhere.
  for (const key of Object.keys(VPS_CATEGORY_CONCEPTS)) {
    expect(VPS_CATEGORY_KEYS.includes(key), `"${key}" is not a real VPS category key`);
  }
}

function test_vps_category_explanations_are_framed_as_a_question(): void {
  // Part 5's own worked example shape -- a question the category
  // answers, not a restatement of its label or score.
  for (const key of VPS_CATEGORY_KEYS) {
    const concept = getVpsCategoryConcept(key)!;
    expect(concept.question.trim().endsWith("?"), `${key}: question should read as an actual question`);
  }
}

function test_unknown_vps_category_resolves_to_undefined(): void {
  expect(getVpsCategoryConcept("not-a-real-category") === undefined, "An unknown category key must resolve to undefined, not throw or fabricate content");
}

// --- Metric concepts (Part 7) -------------------------------------------

function test_every_metric_concept_has_required_fields(): void {
  for (const [key, concept] of Object.entries(METRIC_CONCEPTS)) {
    expect(concept.key === key, `${key}: concept.key must match its own registry key`);
    expect(concept.name.trim().length > 0, `${key}: name must not be empty`);
    expect(concept.whatIsThis.trim().length > 0, `${key}: whatIsThis must not be empty`);
    expect(concept.whyItMatters.trim().length > 0, `${key}: whyItMatters must not be empty`);
  }
}

function test_metric_concept_names_introduce_plain_language_before_acronym(): void {
  // Part 8's explicit instruction: "Customer acquisition cost (CAC)",
  // never a bare acronym as the primary name.
  const cac = getMetricConcept("cac")!;
  expect(cac.name === "Customer acquisition cost (CAC)", `Unexpected CAC name: "${cac.name}"`);
  expect(!cac.name.startsWith("CAC"), "CAC's name must lead with plain language, not the bare acronym");
}

function test_metric_concept_playbook_slugs_resolve(): void {
  // Mirrors tests/playbooks.test.ts's own test_related_playbooks_resolve
  // -- an optional playbookSlug, when set, must point at a real playbook.
  for (const [key, concept] of Object.entries(METRIC_CONCEPTS)) {
    if (concept.playbookSlug) {
      expect(
        getPlaybookBySlug(concept.playbookSlug) !== undefined,
        `${key}: playbookSlug "${concept.playbookSlug}" does not resolve to a real playbook`
      );
    }
  }
}

function test_unknown_metric_resolves_to_undefined(): void {
  expect(getMetricConcept("not-a-real-metric") === undefined, "An unknown metric key must resolve to undefined, not throw or fabricate content");
}

// --- Unknown-state / personalization honesty (Part 10/11) ---------------

function test_personalize_null_is_honest_never_implies_zero(): void {
  for (const [key, concept] of Object.entries(METRIC_CONCEPTS)) {
    const unknownText = concept.personalize(null);
    expect(unknownText.trim().length > 0, `${key}: personalize(null) must not be empty`);
    // Part 11: Unknown must never be framed as $0 / 0% / a worse case.
    expect(!/\$0\b/.test(unknownText), `${key}: personalize(null) must not read as "$0" -- got: "${unknownText}"`);
    expect(!/\b0%/.test(unknownText), `${key}: personalize(null) must not read as "0%" -- got: "${unknownText}"`);
    // Never framed as bad/a failure.
    for (const badWord of ["bad", "fail", "wrong", "missing", "incomplete"]) {
      expect(!unknownText.toLowerCase().includes(badWord), `${key}: personalize(null) must not use judgmental language ("${badWord}") -- got: "${unknownText}"`);
    }
  }
}

function test_personalize_known_value_reflects_the_real_number(): void {
  // Part 10's own worked examples -- a known value must actually appear
  // in the personalized sentence, not just a generic acknowledgment.
  expect(getMetricConcept("cac")!.personalize(50).includes("50"), 'CAC personalize(50) must mention "50"');
  expect(getMetricConcept("gross_margin")!.personalize(72).includes("72"), 'gross_margin personalize(72) must mention "72"');
  expect(getMetricConcept("retention")!.personalize(90).includes("90"), 'retention personalize(90) must mention "90"');
  expect(getMetricConcept("burn")!.personalize(5000).includes("5,000"), 'burn personalize(5000) must mention the formatted figure');
}

function test_personalize_null_and_known_value_produce_different_text(): void {
  for (const concept of Object.values(METRIC_CONCEPTS)) {
    expect(
      concept.personalize(null) !== concept.personalize(42),
      `${concept.key}: Unknown and a known value must not produce identical copy`
    );
  }
}

// --- VPS category score personalization (Part 5/10/11) ------------------

function test_personalize_vps_category_score_null_is_neutral_not_negative(): void {
  const text = personalizeVpsCategoryScore(null);
  expect(text.trim().length > 0, "personalizeVpsCategoryScore(null) must not be empty");
  for (const badWord of ["bad", "fail", "wrong", "penalty", "penalized"]) {
    expect(!text.toLowerCase().includes(badWord), `personalizeVpsCategoryScore(null) must not use judgmental language ("${badWord}")`);
  }
}

function test_personalize_vps_category_score_bands_are_distinct(): void {
  const bands = [null, 2, 6, 8.5].map((score) => personalizeVpsCategoryScore(score as number | null));
  const unique = new Set(bands);
  expect(unique.size === bands.length, `Expected 4 distinct band messages, got ${unique.size}: ${JSON.stringify(bands)}`);
}

function test_personalize_vps_category_score_never_exposes_a_raw_number(): void {
  // Part 5: "Do not expose internal scoring formulas." -- the sentence
  // itself must never leak the literal score value or a weight/formula.
  for (const score of [null, 2, 5.5, 9]) {
    const text = personalizeVpsCategoryScore(score);
    expect(!/\d/.test(text), `personalizeVpsCategoryScore(${score}) must contain no digits (no raw score/weight leakage) -- got: "${text}"`);
  }
}

// --- What If integration (Part 15) ---------------------------------------

function test_what_if_scenario_concepts_resolve_to_real_metric_concepts(): void {
  for (const [scenarioId, conceptKey] of Object.entries(WHAT_IF_SCENARIO_CONCEPTS)) {
    expect(
      METRIC_CONCEPTS[conceptKey] !== undefined,
      `What If scenario "${scenarioId}" maps to unknown concept "${conceptKey}"`
    );
    expect(
      getMetricConceptForWhatIfScenario(scenarioId)?.key === conceptKey,
      `getMetricConceptForWhatIfScenario("${scenarioId}") did not resolve as expected`
    );
  }
}

function test_what_if_scenario_with_no_mapping_returns_undefined(): void {
  expect(
    getMetricConceptForWhatIfScenario("interview-20") === undefined,
    "A plain-language scenario (customer interviews) must not resolve to a jargon concept card"
  );
}

// --- Content quality (Part 9/23): no fabricated universal thresholds ----

function test_no_fabricated_universal_benchmarks(): void {
  // Part 9's explicit anti-pattern: "CAC should always be below $X."
  // Benchmarks vary by business model -- Learn explains concepts, it
  // never invents a universal startup commandment.
  const allCopy = [
    ...Object.values(VPS_CATEGORY_CONCEPTS).flatMap((c) => [c.question, c.whyItMatters]),
    ...Object.values(METRIC_CONCEPTS).flatMap((c) => [c.whatIsThis, c.whyItMatters, c.personalize(null), c.personalize(42)]),
  ].join(" ");

  expect(!/should (always|never) be (above|below|under|over)/i.test(allCopy), "Copy must not state a fabricated universal numeric rule");
  expect(!/\bgood (cac|margin|retention)\b/i.test(allCopy), "Copy must not label a specific number as universally 'good'");
}

const TESTS = [
  test_every_vps_category_has_an_explanation,
  test_no_extra_vps_category_concepts_exist,
  test_vps_category_explanations_are_framed_as_a_question,
  test_unknown_vps_category_resolves_to_undefined,
  test_every_metric_concept_has_required_fields,
  test_metric_concept_names_introduce_plain_language_before_acronym,
  test_metric_concept_playbook_slugs_resolve,
  test_unknown_metric_resolves_to_undefined,
  test_personalize_null_is_honest_never_implies_zero,
  test_personalize_known_value_reflects_the_real_number,
  test_personalize_null_and_known_value_produce_different_text,
  test_personalize_vps_category_score_null_is_neutral_not_negative,
  test_personalize_vps_category_score_bands_are_distinct,
  test_personalize_vps_category_score_never_exposes_a_raw_number,
  test_what_if_scenario_concepts_resolve_to_real_metric_concepts,
  test_what_if_scenario_with_no_mapping_returns_undefined,
  test_no_fabricated_universal_benchmarks,
];

function main(): void {
  console.log("\nLearn V1 -- Contextual Founder Education tests");
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
