// Phase 34D -- SIE Build Intelligence Loop V1.
//
// Pure mapping from a captureSignals.ts ProposedSignal (or a raw-text
// fallback) into the CreateEvidenceRequest shape POST
// /ventures/{id}/evidence expects. Zero "@/..." imports -- plain-node
// testable, same discipline as lib/simulate/*.ts and captureSignals.ts
// itself.
//
// This module does NOT extract evidence -- it never touches raw text or
// runs a pattern match. It exists only because captureSignals.ts's
// output (ProposedSignal) and the backend's Evidence contract
// (docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md §D.2) are
// close but not identical shapes: this is the one small, honest seam
// between "what extraction found" and "what a founder confirmed."

type MinimalProposedSignal = {
  id: string;
  label: string;
  sourceQuote: string;
  fieldPath?: string;
  proposedValue?: number;
  polarity: "positive" | "negative" | "neutral";
};

export type EvidenceTypeChoice =
  | "founder_claim"
  | "reported_preference"
  | "observed_behavior"
  | "commitment"
  | "transaction"
  | "longitudinal_outcome";

export type RelationshipChoice = "supports" | "contradicts" | "mixed" | "neutral";

// Plain-language labels the founder actually sees -- never the raw
// taxonomy vocabulary (Phase 34D §15: the founder should not need to
// understand "evidence taxonomy," "provenance," or any other internal
// architecture noun).
export const EVIDENCE_TYPE_LABELS: Record<EvidenceTypeChoice, string> = {
  founder_claim: "Something I believe, not yet confirmed",
  reported_preference: "Someone said they would",
  observed_behavior: "Someone actually did something",
  commitment: "Someone agreed to / committed to something",
  transaction: "Money actually changed hands",
  longitudinal_outcome: "This is what happened afterward, over time",
};

// Phase 34D-A: these are the ONLY plain-language relationship options a
// founder is ever shown -- "Doesn't tell us yet" is a legitimate,
// explicitly-chosen answer (maps to the canonical "neutral" value), not a
// placeholder. See the picker in CurrentQuestionCard.tsx, which never
// pre-selects one of these on the founder's behalf.
export const RELATIONSHIP_LABELS: Record<RelationshipChoice, string> = {
  supports: "Supports it",
  contradicts: "Contradicts it",
  mixed: "Mixed -- some of both",
  neutral: "Doesn't tell us yet",
};

// A sensible default evidence type, based on which VentureAssumptions
// field (if any) the signal maps to -- the founder can always change it
// before confirming (§6: "correct relevant information if the existing
// interaction safely supports it"). Never itself sent to the backend
// without the founder having seen and kept (or changed) this default.
export function defaultEvidenceType(signal: MinimalProposedSignal): EvidenceTypeChoice {
  if (signal.fieldPath === "validation.paying_customers" || signal.fieldPath === "economics.price_point") {
    return "transaction";
  }
  if (signal.fieldPath === "validation.customer_interviews") {
    return "reported_preference";
  }
  if (signal.fieldPath === "validation.retention_pct") {
    return "observed_behavior";
  }
  return "founder_claim";
}

// The polarity-implied relationship for a signal -- used only as a pure
// reference value (e.g. by tests, or a future "suggested" hint rendered
// alongside the picker). Phase 34D-A: NEVER used to pre-select or
// silently fall back to a relationship value in the interactive
// confirmation UI -- classifying how a result affects what was being
// tested is always an explicit founder choice, even when polarity makes
// one answer likely. See docs/product/SIE_BUILD_INTELLIGENCE_ARCHITECTURE_V1.md's
// 34D-A implementation appendix for the incident this responds to.
export function defaultRelationship(signal: MinimalProposedSignal): RelationshipChoice {
  if (signal.polarity === "positive") return "supports";
  if (signal.polarity === "negative") return "contradicts";
  return "neutral";
}

export type EvidenceDraft = {
  signal: MinimalProposedSignal;
  evidenceType: EvidenceTypeChoice;
  relationship: RelationshipChoice;
};

export function buildEvidenceDraft(signal: MinimalProposedSignal): EvidenceDraft {
  return {
    signal,
    evidenceType: defaultEvidenceType(signal),
    relationship: defaultRelationship(signal),
  };
}

export type CreateEvidencePayload = {
  evidence_type: EvidenceTypeChoice;
  statement: string;
  provenance: "founder_observed";
  source_quote: string;
  // Optional at the type level only for the raw-note fallback (§2 of the
  // 34D-A directive: "Just save the raw note" must remain valid without
  // forcing a relationship). Every other caller in this codebase always
  // supplies an explicit, founder-chosen value -- see
  // CurrentQuestionCard.tsx's RelationshipPicker, which never lets a
  // Confirm/Save action fire with this unset.
  relationship?: RelationshipChoice;
  structured_field_path?: string;
  structured_value?: number;
};

// provenance is always "founder_observed" here, never "sie_inferred" --
// extracting STRUCTURE from the founder's own words (captureSignals.ts)
// is not the same as SIE claiming independent knowledge about the world;
// the underlying fact was still reported by the founder. See
// docs/product/SIE_BUILD_METHODOLOGY_V1.md §14: "do not pretend
// founder-reported observations are independently verified" -- this
// applies in the other direction too: don't mislabel a founder's own
// report as an SIE inference merely because SIE helped parse it.
export function toCreateEvidencePayload(draft: EvidenceDraft): CreateEvidencePayload {
  const payload: CreateEvidencePayload = {
    evidence_type: draft.evidenceType,
    statement: draft.signal.label,
    provenance: "founder_observed",
    source_quote: draft.signal.sourceQuote,
    relationship: draft.relationship,
  };
  if (draft.signal.fieldPath) {
    payload.structured_field_path = draft.signal.fieldPath;
  }
  if (draft.signal.proposedValue !== undefined) {
    payload.structured_value = draft.signal.proposedValue;
  }
  return payload;
}

// The fallback path (§5): when nothing was structurally extracted, or
// the founder wants to record the raw text as-is, the entire raw result
// must still be preservable as evidence -- never fabricating structure
// that isn't there.
//
// `relationship` is optional and, per Phase 34D-A §2, deliberately never
// defaulted here: "Just save the raw note" is exempt from relationship
// classification entirely (it is not a confirmed, classified piece of
// evidence -- it is the unclassified original text). Callers that DO have
// a founder-chosen relationship (none currently do for the raw-note path,
// but the parameter stays available) may still pass one explicitly.
export function toRawTextEvidencePayload(
  rawText: string,
  evidenceType: EvidenceTypeChoice,
  relationship?: RelationshipChoice
): CreateEvidencePayload {
  const payload: CreateEvidencePayload = {
    evidence_type: evidenceType,
    statement: rawText,
    provenance: "founder_observed",
    source_quote: rawText,
  };
  if (relationship) {
    payload.relationship = relationship;
  }
  return payload;
}

// --- Phase 34D-A: shared "is this ready to confirm/save?" gates ------------
//
// These exist so the single-source-of-truth answer to "has the founder
// actually chosen a relationship?" lives in one tested, importable place
// rather than being reimplemented inline wherever a Confirm/Save button
// needs to disable itself (CurrentQuestionCard.tsx's OutcomeState and
// CandidateEvidenceReview both call these rather than each rolling their
// own null-check).

// A single outcome/evidence item's relationship is "explicit" only when
// the founder has clicked one of the RelationshipPicker options -- `null`/
// `undefined` (never chosen) must never be treated as equivalent to a
// real value, even "neutral"/"Doesn't tell us yet" (which IS a real,
// explicitly-choosable answer, just not a synonym for "not answered").
export function hasExplicitRelationship(
  relationship: RelationshipChoice | null | undefined
): relationship is RelationshipChoice {
  return relationship !== null && relationship !== undefined;
}

// The multi-item case (CandidateEvidenceReview's checked signals): ready
// to confirm only once at least one signal is checked AND every checked
// signal has an explicit relationship recorded against its id. An empty
// selection is never "ready" (there is nothing to confirm).
export function allCheckedItemsHaveRelationship(
  checkedIds: readonly string[],
  relationships: Readonly<Record<string, RelationshipChoice>>
): boolean {
  return checkedIds.length > 0 && checkedIds.every((id) => hasExplicitRelationship(relationships[id]));
}
