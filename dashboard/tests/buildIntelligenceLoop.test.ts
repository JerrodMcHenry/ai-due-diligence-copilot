// Phase 34D -- SIE Build Intelligence Loop V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as the rest of
// this directory (this repo has no jest/vitest) -- run directly by
// Node's native TypeScript support.
//
// Covers the pure mapping between captureSignals.ts's ProposedSignal
// shape and the CreateEvidenceRequest payload the new
// POST /ventures/{id}/evidence endpoint expects, plus the plain-language
// label requirement (Phase 34D §15).
//
// Run with:
//   node tests/buildIntelligenceLoop.test.ts
// or:
//   npm run test:buildIntelligenceLoop
import { extractCaptureSignals } from "../lib/captureSignals.ts";
import {
  buildEvidenceDraft,
  defaultEvidenceType,
  defaultRelationship,
  toCreateEvidencePayload,
  toRawTextEvidencePayload,
  hasExplicitRelationship,
  allCheckedItemsHaveRelationship,
  EVIDENCE_TYPE_LABELS,
  RELATIONSHIP_LABELS,
  type RelationshipChoice,
} from "../lib/build/evidenceMapping.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

// --- result text -> candidate evidence (via the existing, unmodified
//     captureSignals.ts extractor) --------------------------------------

function test_result_text_produces_candidate_signals(): void {
  const signals = extractCaptureSignals("Talked to five prospects. Two are now paying $500/month.");
  expect(signals.length > 0, "Expected at least one candidate signal from a realistic result note");
  const priceSignal = signals.find((s) => s.fieldPath === "economics.price_point");
  expect(priceSignal !== undefined, "Expected a price signal to be detected");
  expect(priceSignal!.proposedValue === 500, `Expected proposedValue 500, got ${priceSignal!.proposedValue}`);
}

function test_no_recognized_signal_still_returns_empty_not_fabricated(): void {
  // §5: "If the founder's result produces no recognized structured
  // signal, the raw founder observation must still be preservable
  // without fabricating structured evidence." This is exactly
  // extractCaptureSignals()'s own existing, unmodified guarantee --
  // asserted here as the contract this phase's UI depends on.
  const signals = extractCaptureSignals("Sarah says hi.");
  expect(signals.length === 0, "An unstructured note must never be forced into a fabricated signal");
}

// --- evidence-type / relationship defaults -------------------------------

function test_price_and_paying_customer_signals_default_to_transaction(): void {
  const [priceSignal] = extractCaptureSignals("Two are now paying $500/month.").filter((s) => s.fieldPath === "economics.price_point");
  expect(defaultEvidenceType(priceSignal) === "transaction", `Expected "transaction", got "${defaultEvidenceType(priceSignal)}"`);
}

function test_interview_signal_defaults_to_reported_preference(): void {
  const [interviewSignal] = extractCaptureSignals("Talked to five prospects.").filter((s) => s.fieldPath === "validation.customer_interviews");
  expect(defaultEvidenceType(interviewSignal) === "reported_preference", `Expected "reported_preference", got "${defaultEvidenceType(interviewSignal)}"`);
}

function test_unmapped_signal_defaults_to_founder_claim(): void {
  const genericSignal = { id: "x", label: "Competitor mentioned", sourceQuote: "our competitor", polarity: "neutral" as const };
  expect(defaultEvidenceType(genericSignal) === "founder_claim", `Expected "founder_claim", got "${defaultEvidenceType(genericSignal)}"`);
}

function test_relationship_defaults_follow_polarity(): void {
  const positive = { id: "a", label: "x", sourceQuote: "x", polarity: "positive" as const };
  const negative = { id: "b", label: "x", sourceQuote: "x", polarity: "negative" as const };
  const neutral = { id: "c", label: "x", sourceQuote: "x", polarity: "neutral" as const };
  expect(defaultRelationship(positive) === "supports", `Expected "supports" for positive polarity, got "${defaultRelationship(positive)}"`);
  expect(defaultRelationship(negative) === "contradicts", `Expected "contradicts" for negative polarity, got "${defaultRelationship(negative)}"`);
  expect(defaultRelationship(neutral) === "neutral", `Expected "neutral" for neutral polarity, got "${defaultRelationship(neutral)}"`);
}

// --- confirmation payload -------------------------------------------------

function test_confirmed_draft_produces_the_exact_api_payload_shape(): void {
  const [priceSignal] = extractCaptureSignals("Two are now paying $500/month.").filter((s) => s.fieldPath === "economics.price_point");
  const draft = buildEvidenceDraft(priceSignal);
  const payload = toCreateEvidencePayload(draft);

  expect(payload.evidence_type === "transaction", "Expected the default evidence_type to survive into the payload");
  expect(payload.provenance === "founder_observed", `Every confirmed founder signal must be provenance="founder_observed", got "${payload.provenance}"`);
  expect(payload.statement === priceSignal.label, "statement must be the signal's own label");
  expect(payload.source_quote === priceSignal.sourceQuote, "source_quote must be preserved verbatim");
  expect(payload.structured_field_path === "economics.price_point", "structured_field_path must carry through");
  expect(payload.structured_value === 500, "structured_value must carry through");
  expect(payload.relationship === "supports", "relationship must default from polarity");
}

function test_payload_never_carries_a_score_or_confidence_field(): void {
  const [priceSignal] = extractCaptureSignals("Two are now paying $500/month.").filter((s) => s.fieldPath === "economics.price_point");
  const payload = toCreateEvidencePayload(buildEvidenceDraft(priceSignal));
  const serialized = JSON.stringify(payload);
  expect(!serialized.toLowerCase().includes("score"), `Payload must never carry a score field, got: ${serialized}`);
  expect(!serialized.toLowerCase().includes("confidence"), `Payload must never carry a confidence field, got: ${serialized}`);
  expect(!serialized.toLowerCase().includes("probability"), `Payload must never carry a probability field, got: ${serialized}`);
}

function test_raw_text_fallback_preserves_the_founder_words_verbatim(): void {
  const rawText = "Sarah says hi.";
  const payload = toRawTextEvidencePayload(rawText, "founder_claim", "neutral");
  expect(payload.statement === rawText, "The raw text fallback must preserve the founder's exact words");
  expect(payload.source_quote === rawText, "The raw text fallback's source_quote must also be the exact words");
  expect(payload.provenance === "founder_observed", "The raw text fallback must still be provenance=founder_observed, never fabricated as something stronger");
}

// --- Phase 34D-A §5.G: raw-note-only save works with NO relationship ------

function test_raw_note_only_save_remains_possible_without_relationship_classification(): void {
  // "Just save the raw note" (§2 of the 34D-A directive) must remain
  // valid without forcing an evidence relationship -- calling with no
  // third argument at all must still produce a valid, postable payload.
  const rawText = "Sarah says hi.";
  const payload = toRawTextEvidencePayload(rawText, "founder_claim");
  expect(payload.relationship === undefined, `Raw-note-only payload must omit relationship entirely, got "${payload.relationship}"`);
  expect(payload.statement === rawText, "Raw-note-only payload must still preserve the founder's exact words");
  expect(payload.provenance === "founder_observed", "Raw-note-only payload must still be provenance=founder_observed");
  // Confirming this never throws or otherwise misbehaves when serialized
  // (e.g. for the network request) with relationship absent.
  const serialized = JSON.stringify(payload);
  expect(!serialized.includes('"relationship"'), `Serialized raw-note payload must not carry a relationship key at all, got: ${serialized}`);
}

// --- Phase 34D-A §1/§5.A/§5.B: no silent relationship default -------------
//
// The Phase 34D live walkthrough saved an outcome as "neutral" without
// anyone choosing that -- these tests lock in the fix: an unselected
// relationship must never be treated as valid, for either a single
// outcome or a multi-signal confirmed-evidence batch.

function test_unselected_relationship_is_never_treated_as_explicit(): void {
  expect(hasExplicitRelationship(null) === false, "null (never chosen) must never count as an explicit relationship choice");
  expect(hasExplicitRelationship(undefined) === false, "undefined (never chosen) must never count as an explicit relationship choice");
}

function test_explicitly_chosen_neutral_is_still_a_valid_explicit_choice(): void {
  // "Doesn't tell us yet" (canonical "neutral") is a legitimate answer
  // once the founder actually clicks it -- it must not be conflated with
  // "nothing was chosen."
  expect(hasExplicitRelationship("neutral") === true, "An explicitly-chosen 'neutral' must count as explicit, distinct from unselected");
}

function test_confirmed_evidence_cannot_silently_save_with_an_unselected_relationship(): void {
  // §5.A: a batch of checked signals is only "ready to confirm" once
  // EVERY checked signal has an explicit relationship recorded -- one
  // missing entry (simulating a founder who checked a box but never
  // picked a relationship for it) must block the whole batch, exactly
  // the failure mode that produced the Phase 34D incident.
  const checkedIds = ["sig-1", "sig-2"];
  const partiallyClassified: Record<string, RelationshipChoice> = { "sig-1": "supports" };
  expect(
    allCheckedItemsHaveRelationship(checkedIds, partiallyClassified) === false,
    "A batch with any unclassified checked signal must never be considered ready to confirm"
  );

  const fullyClassified: Record<string, RelationshipChoice> = { "sig-1": "supports", "sig-2": "mixed" };
  expect(
    allCheckedItemsHaveRelationship(checkedIds, fullyClassified) === true,
    "A batch where every checked signal has an explicit relationship must be ready to confirm"
  );

  expect(
    allCheckedItemsHaveRelationship([], {}) === false,
    "An empty selection must never be considered ready to confirm (nothing to confirm)"
  );
}

function test_outcome_evidence_cannot_silently_save_with_an_unselected_relationship(): void {
  // §5.B: the single-outcome case (OutcomeState's Save button gate).
  expect(hasExplicitRelationship(null) === false, "An outcome with no relationship chosen must never be save-ready");
  expect(hasExplicitRelationship("mixed") === true, "An outcome with an explicitly chosen relationship must be save-ready");
}

// --- Phase 34D-A §5.C-F: each plain-language option maps to its exact
//     canonical value --------------------------------------------------

function test_supports_option_maps_to_canonical_supports(): void {
  expect(RELATIONSHIP_LABELS.supports.length > 0, "supports must have a plain-language label");
  expect(hasExplicitRelationship("supports") === true, "supports must be a valid explicit choice");
}

function test_mixed_option_maps_to_canonical_mixed(): void {
  expect(RELATIONSHIP_LABELS.mixed.length > 0, "mixed must have a plain-language label");
  expect(hasExplicitRelationship("mixed") === true, "mixed must be a valid explicit choice");
}

function test_contradicts_option_maps_to_canonical_contradicts(): void {
  expect(RELATIONSHIP_LABELS.contradicts.length > 0, "contradicts must have a plain-language label");
  expect(hasExplicitRelationship("contradicts") === true, "contradicts must be a valid explicit choice");
}

function test_doesnt_tell_us_yet_option_maps_to_canonical_neutral(): void {
  // The directive's own suggested copy ("Doesn't tell us yet") maps to
  // the existing canonical "neutral" value -- no new enum value is
  // introduced.
  expect(RELATIONSHIP_LABELS.neutral.toLowerCase().includes("doesn"), `Expected the neutral option's label to read as "doesn't tell us yet"-style copy, got "${RELATIONSHIP_LABELS.neutral}"`);
  expect(hasExplicitRelationship("neutral") === true, "neutral (once explicitly chosen) must be a valid explicit choice");
}

// --- plain-language requirement (§15) -------------------------------------

function test_evidence_type_labels_are_plain_language_not_taxonomy_jargon(): void {
  const forbidden = ["evidence_type", "provenance", "hypothesis", "taxonomy"];
  for (const label of Object.values(EVIDENCE_TYPE_LABELS)) {
    for (const term of forbidden) {
      expect(!label.toLowerCase().includes(term), `Evidence type label "${label}" must not leak internal jargon ("${term}")`);
    }
  }
  for (const label of Object.values(RELATIONSHIP_LABELS)) {
    for (const term of forbidden) {
      expect(!label.toLowerCase().includes(term), `Relationship label "${label}" must not leak internal jargon ("${term}")`);
    }
  }
}

function test_every_evidence_type_and_relationship_has_a_label(): void {
  const evidenceTypes = ["founder_claim", "reported_preference", "observed_behavior", "commitment", "transaction", "longitudinal_outcome"] as const;
  for (const type of evidenceTypes) {
    expect(typeof EVIDENCE_TYPE_LABELS[type] === "string" && EVIDENCE_TYPE_LABELS[type].length > 0, `Missing a plain-language label for evidence type "${type}"`);
  }
  const relationships = ["supports", "contradicts", "mixed", "neutral"] as const;
  for (const rel of relationships) {
    expect(typeof RELATIONSHIP_LABELS[rel] === "string" && RELATIONSHIP_LABELS[rel].length > 0, `Missing a plain-language label for relationship "${rel}"`);
  }
}

const TESTS = [
  test_result_text_produces_candidate_signals,
  test_no_recognized_signal_still_returns_empty_not_fabricated,
  test_price_and_paying_customer_signals_default_to_transaction,
  test_interview_signal_defaults_to_reported_preference,
  test_unmapped_signal_defaults_to_founder_claim,
  test_relationship_defaults_follow_polarity,
  test_confirmed_draft_produces_the_exact_api_payload_shape,
  test_payload_never_carries_a_score_or_confidence_field,
  test_raw_text_fallback_preserves_the_founder_words_verbatim,
  test_raw_note_only_save_remains_possible_without_relationship_classification,
  test_unselected_relationship_is_never_treated_as_explicit,
  test_explicitly_chosen_neutral_is_still_a_valid_explicit_choice,
  test_confirmed_evidence_cannot_silently_save_with_an_unselected_relationship,
  test_outcome_evidence_cannot_silently_save_with_an_unselected_relationship,
  test_supports_option_maps_to_canonical_supports,
  test_mixed_option_maps_to_canonical_mixed,
  test_contradicts_option_maps_to_canonical_contradicts,
  test_doesnt_tell_us_yet_option_maps_to_canonical_neutral,
  test_evidence_type_labels_are_plain_language_not_taxonomy_jargon,
  test_every_evidence_type_and_relationship_has_a_label,
];

function main(): void {
  console.log("\nPhase 34D -- SIE Build Intelligence Loop V1 tests");
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
