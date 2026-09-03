// Phase 23 -- Universal Founder Capture V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as the rest of
// this repo's tests/*.test.ts files. Every fixture here is one of the
// directive's own worked examples (Part 18's live-acceptance list) --
// this file is the deterministic, offline proof those examples behave
// correctly before any live browser walkthrough.
//
// Run with:
//   node tests/captureSignals.test.ts
// or:
//   npm run test:captureSignals

import { extractCaptureSignals } from "../lib/captureSignals.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

// --- A. Customer interview (directive's own worked example) ----------------

function test_restaurant_owners_example(): void {
  const text =
    "Talked to six restaurant owners. Four said inventory waste is a serious problem, but only one would pay $500/month.";
  const signals = extractCaptureSignals(text);

  const interview = signals.find((s) => s.fieldPath === "validation.customer_interviews");
  expect(interview !== undefined, "Must find an interview-count signal");
  expect(interview!.proposedValue === 6, `Must propose 6 interviews, got ${interview!.proposedValue}`);

  const price = signals.find((s) => s.fieldPath === "economics.price_point");
  expect(price !== undefined, "Must find a positive price signal");
  expect(price!.proposedValue === 500, `Must propose $500, got ${price!.proposedValue}`);
  expect(price!.polarity === "positive", "The $500 signal must be positive (one restaurant owner WOULD pay)");

  const problemConfirmation = signals.find((s) => s.label.includes("Problem confirmation"));
  expect(problemConfirmation !== undefined, "Must surface the problem-confirmation mention (informational only)");
  expect(problemConfirmation!.fieldPath === undefined, "Problem confirmation must NOT propose a canonical field (no safe mapping exists)");
}

// --- B. Positive commercial event -------------------------------------------

function test_first_customer_signed(): void {
  const text = "We signed our first customer at $299/month.";
  const signals = extractCaptureSignals(text);

  const newCustomer = signals.find((s) => s.fieldPath === "validation.paying_customers");
  expect(newCustomer !== undefined, "Must find a new-paying-customer signal");
  expect(newCustomer!.proposedValue === 1, "New customer signal must propose a +1 delta, never an absolute count");
  expect(newCustomer!.polarity === "positive", "Signing a customer must be framed positive");

  const price = signals.find((s) => s.fieldPath === "economics.price_point");
  expect(price !== undefined, "Must find the $299 price signal");
  expect(price!.proposedValue === 299, `Must propose $299, got ${price!.proposedValue}`);
}

// --- C. Negative evidence ----------------------------------------------------

function test_negative_pricing_evidence(): void {
  const text = "We spoke with 10 customers and none would pay $500/month.";
  const signals = extractCaptureSignals(text);

  const interview = signals.find((s) => s.fieldPath === "validation.customer_interviews");
  expect(interview !== undefined, "Must still find the interview count even in a negative-outcome note");
  expect(interview!.proposedValue === 10, `Must propose 10 interviews, got ${interview!.proposedValue}`);

  const negativePrice = signals.find((s) => s.polarity === "negative" && s.label.toLowerCase().includes("pricing"));
  expect(negativePrice !== undefined, "Must surface the pricing-resistance signal");
  expect(negativePrice!.fieldPath === undefined, "A negative willingness-to-pay signal must NEVER propose economics.price_point = 500 -- that would invert what the founder actually observed");

  // Explicit non-punitive-framing check: nothing in the produced labels
  // may read as blame/failure language.
  const allText = signals.map((s) => s.label).join(" ").toLowerCase();
  for (const bad of ["fail", "bad", "lost progress", "penalty", "setback"]) {
    expect(!allText.includes(bad), `Signal labels must never use punitive language ("${bad}") -- got: "${allText}"`);
  }
}

// --- D. Unstructured note (must yield some or zero signals honestly) -------

function test_unstructured_note_hallucinates_nothing(): void {
  const text = "Had a great conversation with Sarah about onboarding. Need to think about it more.";
  const signals = extractCaptureSignals(text);

  // "conversation" alone (no number, no verb+number pairing this parser
  // recognizes) must not fabricate an interview count.
  expect(signals.every((s) => s.fieldPath !== "validation.customer_interviews"), "Must not fabricate an interview count from a note with no actual number");
  expect(signals.every((s) => s.fieldPath !== "economics.price_point"), "Must not fabricate a price from a note with no dollar amount");
  expect(signals.every((s) => s.fieldPath !== "validation.paying_customers"), "Must not fabricate a new-customer signal");
  // Zero signals entirely is the correct, honest outcome for this note.
  expect(signals.length === 0, `A note with no recognizable pattern must yield zero signals, got ${signals.length}: ${JSON.stringify(signals.map((s) => s.label))}`);
}

// --- Additional fixtures from the directive's own Part 3 examples ----------

// Phase 26 -- Retention Loop Closure, Part 5. Superseded from Phase 23's
// original assertion: a COUNTABLE churn mention ("Three customers
// churned...") now safely proposes a negative delta on the existing,
// already-canonical validation.paying_customers field -- the identical
// mechanic the "new paying customer" +1 signal already used, just
// negative. This is deliberately DIFFERENT from an unquantified churn
// mention (see test_unquantified_churn_is_action_relevant below), per
// Phase 25's own explicit finding: "these should not all be treated
// identically if the evidence differs."
function test_countable_churn_is_model_relevant(): void {
  const text = "Three customers churned this month.";
  const signals = extractCaptureSignals(text);
  const churn = signals.find((s) => s.fieldPath === "validation.paying_customers");
  expect(churn !== undefined, "A countable churn mention must propose a paying_customers delta");
  expect(churn!.proposedValue === -3, `Must propose a -3 delta, got ${churn!.proposedValue}`);
  expect(churn!.polarity === "negative", "Churn is real negative evidence, correctly labeled as such (not punitive language, just accurate polarity)");
  // No duplicate: the generic informational "Customer churn mentioned"
  // signal must be suppressed when the countable version already fired,
  // so a founder never sees the same real event listed twice.
  const duplicateInfo = signals.filter((s) => s.label === "Customer churn mentioned");
  expect(duplicateInfo.length === 0, "Must not also surface the generic informational churn signal alongside the countable, field-mapped one");
}

// Phase 26, Part 3/5 (the directive's own reproduced dead-end example).
// An UNQUANTIFIED churn mention has no safe number to propose a delta
// from -- it must stay informational, but Class B (ACTION-RELEVANT), not
// a silent dead end: the founder should be told this may be worth
// investigating, using the existing action-creation pathway.
function test_unquantified_churn_is_action_relevant(): void {
  const text = "Customer cancelled because onboarding took too long.";
  const signals = extractCaptureSignals(text);
  const churn = signals.find((s) => s.label === "Customer churn mentioned");
  expect(churn !== undefined, "Must surface the churn mention");
  expect(churn!.fieldPath === undefined, "An unquantified churn mention must never invent a count to decrement paying_customers by");
  expect(churn!.actionRelevant === true, "An unquantified churn mention must be marked action-relevant -- Phase 25's own dead-end case");
  expect(typeof churn!.suggestedActionTitle === "string" && churn!.suggestedActionTitle!.length > 0, "Must carry a deterministic suggested action title");
}

// Phase 26, Part 5: a quality/friction complaint is real negative
// evidence, but it is NOT churn -- conflating the two would misrepresent
// what the founder actually observed (nobody said they left).
function test_complaint_is_distinct_from_churn(): void {
  const text = "Five customers complained about onboarding.";
  const signals = extractCaptureSignals(text);
  const churnLabeled = signals.find((s) => s.label.includes("churn"));
  expect(churnLabeled === undefined, "A complaint must never be mislabeled as churn -- no customer was said to have left");
  const complaint = signals.find((s) => s.label.includes("friction") || s.label.includes("complaint"));
  expect(complaint !== undefined, "Must surface the complaint as its own distinct signal");
  expect(complaint!.fieldPath === undefined, "A complaint has no safe canonical field mapping");
  expect(complaint!.actionRelevant === true, "A complaint is action-relevant -- worth investigating");
}

// Phase 26, Part 5: an explicit retention percentage IS a safe,
// already-canonical field (validation.retention_pct already exists and
// is already scored/diffed elsewhere in this codebase) -- this must
// propose a value, not dead-end like the unquantified churn case.
function test_retention_percentage_is_model_relevant(): void {
  const text = "Retention dropped to 82%.";
  const signals = extractCaptureSignals(text);
  const retention = signals.find((s) => s.fieldPath === "validation.retention_pct");
  expect(retention !== undefined, "An explicit retention percentage must propose a validation.retention_pct value");
  expect(retention!.proposedValue === 82, `Must propose 82, got ${retention!.proposedValue}`);
  expect(retention!.polarity === "negative", "'Dropped to' must be read as a negative trend");
}

// Phase 26, Part 5's own explicit instruction: these three examples must
// NOT all be treated identically.
function test_churn_examples_are_differentiated(): void {
  const unquantified = extractCaptureSignals("Customer cancelled because onboarding took too long.");
  const countable = extractCaptureSignals("Three customers churned this month.");
  const retention = extractCaptureSignals("Retention dropped to 82%.");

  expect(
    unquantified.every((s) => s.fieldPath === undefined),
    "Unquantified churn must never propose a canonical field"
  );
  expect(
    countable.some((s) => s.fieldPath === "validation.paying_customers" && s.proposedValue === -3),
    "Countable churn must propose a specific paying_customers delta"
  );
  expect(
    retention.some((s) => s.fieldPath === "validation.retention_pct" && s.proposedValue === 82),
    "An explicit retention percentage must propose a specific retention_pct value"
  );
}

function test_product_shipped_is_informational_only(): void {
  const signals = extractCaptureSignals("Shipped our Stripe integration.");
  const shipped = signals.find((s) => s.label.includes("Product milestone"));
  expect(shipped !== undefined, "Must surface the product-shipped mention");
  expect(shipped!.fieldPath === undefined, "No VentureAssumptions field represents 'shipped a feature' -- must stay informational");
}

function test_investor_note_is_informational_only(): void {
  const signals = extractCaptureSignals("An investor told us our market may be too narrow.");
  const investor = signals.find((s) => s.label.includes("Fundraising"));
  expect(investor !== undefined, "Must surface the investor-conversation mention");
  expect(investor!.fieldPath === undefined, "Fundraising conversations never propose a canonical field");
}

function test_failed_experiment_is_neutral_not_punitive(): void {
  const signals = extractCaptureSignals("The experiment failed. Nobody clicked the paid ad.");
  const experiment = signals.find((s) => s.label.includes("Experiment"));
  expect(experiment !== undefined, "Must surface the experiment-result mention");
  expect(experiment!.polarity !== "negative" || !experiment!.label.toLowerCase().includes("fail"), "Experiment outcome must not be labeled with punitive language even though the founder's own word was 'failed'");
}

// Phase 29B Closure, Part 3 -- a real, live-reproduced gap: "Two more
// customers signed up this week" produced NO paying-customer signal at
// all (the existing NEW_CUSTOMER_PATTERN requires "signed"/"closed"
// immediately followed by the word "customer", not a preceding count).
// Mirrors test_countable_churn_is_model_relevant's own shape exactly --
// same field, opposite direction.
function test_countable_new_customers_is_model_relevant(): void {
  const text = "Two more customers signed up this week.";
  const signals = extractCaptureSignals(text);
  const growth = signals.find((s) => s.fieldPath === "validation.paying_customers");
  expect(growth !== undefined, "A countable new-customer mention must propose a paying_customers delta");
  expect(growth!.proposedValue === 2, `Must propose a +2 delta, got ${growth!.proposedValue}`);
  expect(growth!.polarity === "positive", "New paying customers are positive evidence");
}

function test_countable_new_customers_recognizes_started_paying_phrasing(): void {
  const signals = extractCaptureSignals("Three users started paying this month.");
  const growth = signals.find((s) => s.fieldPath === "validation.paying_customers");
  expect(growth !== undefined, "'started paying' must be recognized as a countable new-paying-customer signal");
  expect(growth!.proposedValue === 3, `Must propose a +3 delta, got ${growth!.proposedValue}`);
}

// The exact original live-reproduced sentence: a domain-specific noun
// ("contractors" instead of customers/users/clients) still does not
// match -- documented as a deliberate limit (Phase 29B Closure, Part 3's
// own conclusion), not an oversight. Covering arbitrary business
// vocabulary would require broader inference than a fixed pattern can
// safely offer.
function test_domain_specific_noun_remains_a_documented_gap(): void {
  const signals = extractCaptureSignals(
    "Two more contractors signed up this week at $25/month, bringing us to 5 paying customers."
  );
  const growth = signals.find((s) => s.fieldPath === "validation.paying_customers");
  expect(growth === undefined, "A domain-specific noun ('contractors') is a documented, deliberate gap, not something this fix claims to cover");
}

// --- Determinism / purity -----------------------------------------------

function test_extraction_is_pure_and_deterministic(): void {
  const text = "We signed our first customer at $299/month.";
  const a = extractCaptureSignals(text);
  const b = extractCaptureSignals(text);
  expect(JSON.stringify(a) === JSON.stringify(b), "Identical input must always produce identical output (no randomness, no AI call)");
}

function test_empty_text_yields_no_signals(): void {
  expect(extractCaptureSignals("").length === 0, "Empty text must yield zero signals, not an error");
  expect(extractCaptureSignals("   ").length === 0, "Whitespace-only text must yield zero signals");
}

const TESTS = [
  test_restaurant_owners_example,
  test_first_customer_signed,
  test_negative_pricing_evidence,
  test_unstructured_note_hallucinates_nothing,
  test_countable_churn_is_model_relevant,
  test_unquantified_churn_is_action_relevant,
  test_complaint_is_distinct_from_churn,
  test_retention_percentage_is_model_relevant,
  test_churn_examples_are_differentiated,
  test_countable_new_customers_is_model_relevant,
  test_countable_new_customers_recognizes_started_paying_phrasing,
  test_domain_specific_noun_remains_a_documented_gap,
  test_product_shipped_is_informational_only,
  test_investor_note_is_informational_only,
  test_failed_experiment_is_neutral_not_punitive,
  test_extraction_is_pure_and_deterministic,
  test_empty_text_yields_no_signals,
];

function main(): void {
  console.log("\nUniversal Founder Capture V1 -- signal extraction tests");
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
