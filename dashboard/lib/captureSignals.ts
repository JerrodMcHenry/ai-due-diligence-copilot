// Phase 23 -- Universal Founder Capture V1, Part 5 (structured
// interpretation).
//
// A small, DETERMINISTIC, zero-AI heuristic parser -- explicitly NOT a
// new AI agent (the directive's own instruction). Given a founder's free
// text ("What happened?"), it proposes a short list of possible signals
// using conservative pattern matching only: no LLM call, no network
// request, no randomness, same input always produces the same output.
//
// This is deliberately conservative rather than clever. Part 5's own
// instruction: "do NOT pretend every note can be structured." A note with
// no recognizable pattern (see the "Sarah" fixture in
// tests/captureSignals.test.ts) must return zero signals, not a
// hallucinated one. Every signal that maps to a real VentureAssumptions
// field is marked `fieldPath` and carries a `proposedValue` the founder
// can see, edit, or discard before anything is applied (Part 6) --
// signals with no safe field mapping (problem confirmations, churn,
// product milestones, fundraising mentions, market/competitor mentions,
// experiment outcomes) are still surfaced as plain informational text,
// exactly as real as the field-mapped ones, just never presented as an
// editable model field ("nothing becomes canonical merely because
// extraction found it" -- Part 5's own instruction).
//
// A future phase MAY swap this module for an actual LLM-based extractor
// without changing anything else: every caller only depends on this
// module's return shape (ProposedSignal[]), never on how it was produced.
//
// Zero "@/..." alias imports -- importable directly by plain Node, same
// convention as lib/fundraising/*.ts and lib/simulate/*.ts.

export type CaptureFieldPath =
  | "validation.customer_interviews"
  | "validation.paying_customers"
  | "validation.retention_pct"
  | "economics.price_point";

export interface ProposedSignal {
  readonly id: string;
  readonly label: string;
  // The specific phrase in the founder's own text this signal came from
  // -- shown alongside the proposal so a founder can see exactly why SIE
  // suggested it, never a bare unexplained number.
  readonly sourceQuote: string;
  // Present only for signals with a safe, unambiguous mapping onto a
  // real VentureAssumptions field. Absent for informational-only signals.
  readonly fieldPath?: CaptureFieldPath;
  readonly proposedValue?: number;
  // Deliberately three-valued, never boolean: a "negative" signal (e.g.
  // "none would pay $500/month") is exactly as valuable as a positive
  // one and must never be framed as bad news -- see Part 10. It exists so
  // callers can choose non-punitive copy/emphasis, never to hide or
  // downweight the signal itself.
  readonly polarity: "positive" | "negative" | "neutral";
  // Phase 26 -- Retention Loop Closure, Part 3 (Capture Outcome Classes).
  // Present ONLY on informational-only signals (fieldPath is absent) that
  // describe something worth a founder looking into, not just knowing --
  // e.g. an unquantified churn mention or a product-friction complaint.
  // Absent (never true) on field-mapped signals, since those already have
  // a stronger outcome (an "Update my model" proposal) -- Part 6's "avoid
  // CTA explosion" means a signal never carries both an update-model AND
  // a make-this-an-action affordance. Absent on informational signals that
  // are real but don't call for investigation (a shipped milestone, a
  // mentioned competitor) -- those stay Class C, learning-only.
  readonly actionRelevant?: boolean;
  // A short, honest, deterministic action title -- present only when
  // actionRelevant is true. Never AI-generated; a fixed string per
  // pattern, exactly like every other label in this module.
  readonly suggestedActionTitle?: string;
}

const NUMBER_WORDS: Record<string, number> = {
  one: 1, two: 2, three: 3, four: 4, five: 5,
  six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
  dozen: 12,
};

function parseCount(token: string): number | null {
  const lower = token.toLowerCase();
  if (lower in NUMBER_WORDS) return NUMBER_WORDS[lower];
  const digits = Number(token);
  return Number.isFinite(digits) && digits > 0 ? digits : null;
}

function makeId(kind: string, index: number): string {
  return `${kind}-${index}`;
}

// Signal 1: interview/conversation count -- "talked to six restaurant
// owners", "spoke with 10 customers", "interviewed 3 users", "met with
// four founders". Requires BOTH a countable number AND a conversation
// verb in proximity, deliberately, to avoid matching an unrelated number
// elsewhere in the note.
const INTERVIEW_PATTERN =
  /\b(?:talked to|spoke (?:with|to)|interviewed|met with)\s+(\w+)\b/gi;

function extractInterviewSignals(text: string): ProposedSignal[] {
  const signals: ProposedSignal[] = [];
  let match: RegExpExecArray | null;
  let index = 0;
  INTERVIEW_PATTERN.lastIndex = 0;
  while ((match = INTERVIEW_PATTERN.exec(text)) !== null) {
    const count = parseCount(match[1]);
    if (count === null) continue;
    signals.push({
      id: makeId("interviews", index++),
      label: `${count} customer conversation${count === 1 ? "" : "s"}`,
      sourceQuote: match[0].trim(),
      fieldPath: "validation.customer_interviews",
      proposedValue: count,
      polarity: "neutral",
    });
  }
  return signals;
}

// Signal 2: a dollar-per-month/year price mention, split into positive
// ("would pay", or a plain statement like "signed ... at $X/month") and
// negative ("wouldn't pay" / "would not pay" / "won't pay" / "none would
// pay") willingness-to-pay. Only the POSITIVE case proposes a
// economics.price_point value -- proposing that value for a negative
// statement would silently invert what the founder actually observed.
const PRICE_PATTERN = /\$\s?([\d,]+(?:\.\d+)?)\s*(?:\/|\bper\b)?\s*(month|mo\b|year|yr\b)/gi;
const NEGATIVE_WTP_NEARBY = /\b(?:none|nobody|no one|wouldn't|would not|won't|will not|didn't|did not)\b[^.!?$]{0,40}\bpay\b/i;
const POSITIVE_WTP_NEARBY = /\b(?:would pay|willing to pay|signed|closed|paying)\b/i;

function extractPriceSignals(text: string): ProposedSignal[] {
  const signals: ProposedSignal[] = [];
  let match: RegExpExecArray | null;
  let index = 0;
  PRICE_PATTERN.lastIndex = 0;
  while ((match = PRICE_PATTERN.exec(text)) !== null) {
    const amount = Number(match[1].replace(/,/g, ""));
    if (!Number.isFinite(amount) || amount <= 0) continue;

    const windowStart = Math.max(0, match.index - 60);
    const surrounding = text.slice(windowStart, match.index + match[0].length + 10);
    const isNegative = NEGATIVE_WTP_NEARBY.test(surrounding);
    const isPositive = !isNegative && POSITIVE_WTP_NEARBY.test(surrounding);

    if (isNegative) {
      signals.push({
        id: makeId("price-negative", index++),
        label: `Pricing resistance around $${amount.toLocaleString()}/mo`,
        sourceQuote: surrounding.trim(),
        polarity: "negative",
      });
    } else if (isPositive) {
      signals.push({
        id: makeId("price-positive", index++),
        label: `$${amount.toLocaleString()}/mo pricing signal`,
        sourceQuote: match[0].trim(),
        fieldPath: "economics.price_point",
        proposedValue: amount,
        polarity: "positive",
      });
    } else {
      // A bare dollar figure with neither a positive nor negative
      // willingness-to-pay cue nearby -- real, worth surfacing, but not
      // confident enough to propose as a canonical price point.
      signals.push({
        id: makeId("price-neutral", index++),
        label: `$${amount.toLocaleString()}/mo mentioned`,
        sourceQuote: match[0].trim(),
        polarity: "neutral",
      });
    }
  }
  return signals;
}

// Signal 3: a new paying customer -- "signed", "closed", "first
// customer", "new customer". Proposes incrementing paying_customers by
// one; the caller (the review UI) is responsible for adding this to the
// venture's CURRENT count, never overwriting it -- this module has no
// access to current assumptions and never guesses a total.
const NEW_CUSTOMER_PATTERN = /\b(?:signed (?:our|a|the)?\s*(?:first\s+)?(?:new\s+)?customer|closed (?:our|a|the)?\s*(?:first\s+)?(?:new\s+)?customer|new paying customer|first customer)\b/i;

function extractNewCustomerSignal(text: string): ProposedSignal[] {
  const match = NEW_CUSTOMER_PATTERN.exec(text);
  if (!match) return [];
  return [{
    id: "new-customer-0",
    label: "New paying customer",
    sourceQuote: match[0].trim(),
    fieldPath: "validation.paying_customers",
    proposedValue: 1, // a +1 delta, not an absolute count -- see this function's own comment
    polarity: "positive",
  }];
}

// Signal 4 -- Phase 26, Part 5 (root-cause fix for the churn dead-end).
// A COUNTABLE churn mention -- "Three customers churned this month.",
// "2 customers cancelled" -- requires BOTH a number AND a churn verb in
// proximity, the identical discipline extractInterviewSignals already
// applies, so a bare "the customer churned" (no count) never matches
// here and instead falls through to the informational, unquantified
// churn signal below. A countable churn is exactly as safe to propose as
// the existing "new paying customer" +1 -- both are a delta on the same
// real, already-canonical validation.paying_customers field; this is
// just the negative direction of that same mechanic, not a new field.
const CHURN_COUNT_PATTERN = /\b(\w+)\s+(?:customers?|users?|clients?)\s+(?:churned|cancel(?:l?ed)?|left)\b/gi;

function extractChurnCountSignals(text: string): ProposedSignal[] {
  const signals: ProposedSignal[] = [];
  let match: RegExpExecArray | null;
  let index = 0;
  CHURN_COUNT_PATTERN.lastIndex = 0;
  while ((match = CHURN_COUNT_PATTERN.exec(text)) !== null) {
    const count = parseCount(match[1]);
    if (count === null) continue;
    signals.push({
      id: makeId("churn-count", index++),
      label: `${count} customer${count === 1 ? "" : "s"} churned`,
      sourceQuote: match[0].trim(),
      fieldPath: "validation.paying_customers",
      proposedValue: -count, // a negative delta -- current + (-count), same mechanic as the +1 new-customer signal above
      polarity: "negative",
    });
  }
  return signals;
}

// Signal 5 -- Phase 26, Part 5. An explicit retention percentage --
// "Retention dropped to 82%.", "Retention is at 91%" -- validation.
// retention_pct is a real, already-scored VentureAssumptions field (see
// app/api.py::_ASSUMPTION_DIFF_FIELDS and the Retention field already on
// the venture-creation review screen); this module simply never proposed
// a value for it before. Like price_point, this is a REPLACEMENT
// (an observed rate), never a delta.
const RETENTION_PATTERN = /\bretention\b[^.!?%]{0,30}?(\d{1,3})\s?%/i;
const NEGATIVE_TREND_NEARBY = /\b(?:dropped|fell|falling|declined|declining|down|worsened|slipped)\b/i;
const POSITIVE_TREND_NEARBY = /\b(?:rose|rising|improved|improving|increased|increasing|up|grew|climbed)\b/i;

function extractRetentionSignal(text: string): ProposedSignal[] {
  const match = RETENTION_PATTERN.exec(text);
  if (!match) return [];
  const pct = Number(match[1]);
  if (!Number.isFinite(pct) || pct < 0 || pct > 100) return [];

  const windowStart = Math.max(0, match.index - 20);
  const surrounding = text.slice(windowStart, match.index + match[0].length);
  const polarity: ProposedSignal["polarity"] = NEGATIVE_TREND_NEARBY.test(surrounding)
    ? "negative"
    : POSITIVE_TREND_NEARBY.test(surrounding)
      ? "positive"
      : "neutral";

  return [{
    id: "retention-0",
    label: `Retention at ${pct}%`,
    sourceQuote: match[0].trim(),
    fieldPath: "validation.retention_pct",
    proposedValue: pct,
    polarity,
  }];
}

// Informational-only signals: real, worth showing, but with no safe
// single-field mapping onto VentureAssumptions (Part 5: "do NOT pretend
// every note can be structured"). Each entry is [pattern, label,
// polarity, actionRelevant?, suggestedActionTitle?].
//
// Phase 26, Part 3/5: actionRelevant marks the signals that name
// something worth a founder investigating, not just recording -- churn
// (unquantified -- a countable churn is handled above as a MODEL-RELEVANT
// delta instead) and product/customer friction. A shipped milestone, a
// mentioned competitor, a fundraising mention, and a confirmed problem
// are real but don't call for an action of their own; they stay
// Class C (learning-only).
const INFORMATIONAL_PATTERNS: ReadonlyArray<{
  pattern: RegExp;
  label: string;
  polarity: ProposedSignal["polarity"];
  actionRelevant?: boolean;
  suggestedActionTitle?: string;
}> = [
  {
    pattern: /\bchurned\b|\bcancel(?:l?ed)?\b|\blost the customer\b/i,
    label: "Customer churn mentioned",
    polarity: "negative",
    actionRelevant: true,
    suggestedActionTitle: "Investigate why this customer churned",
  },
  {
    pattern: /\bcomplain(?:ed|t)?\b|\bfrustrat(?:ed|ion)\b|\bconfused about\b/i,
    label: "Customer friction/complaint mentioned",
    polarity: "negative",
    actionRelevant: true,
    suggestedActionTitle: "Investigate the friction customers are reporting",
  },
  { pattern: /\bshipped\b|\blaunched\b|\breleased\b|\bdeployed\b/i, label: "Product milestone mentioned", polarity: "positive" },
  { pattern: /\binvestor\b|\bVC\b|\bterm sheet\b|\bfundrais(?:e|ing)\b|\bpitch(?:ed)?\b/i, label: "Fundraising conversation mentioned", polarity: "neutral" },
  { pattern: /\bcompetitor(?:s)?\b/i, label: "Competitor/market observation mentioned", polarity: "neutral" },
  {
    pattern: /\bexperiment\b|\bfailed\b|\bdidn't work\b|\bdid not work\b|\bno(?:body| one) clicked\b/i,
    label: "Experiment result mentioned",
    polarity: "neutral",
    actionRelevant: true,
    suggestedActionTitle: "Investigate why this experiment didn't work",
  },
  { pattern: /\b(?:said|confirmed|agreed)\b[^.!?]{0,40}\bproblem\b/i, label: "Problem confirmation mentioned", polarity: "positive" },
];

function extractInformationalSignals(text: string, suppressChurn: boolean): ProposedSignal[] {
  const signals: ProposedSignal[] = [];
  INFORMATIONAL_PATTERNS.forEach(({ pattern, label, polarity, actionRelevant, suggestedActionTitle }, i) => {
    // The unquantified churn pattern is the first entry above -- suppressed
    // when a COUNTABLE churn signal already matched the same note, so a
    // founder never sees both "Customer churn mentioned" (informational)
    // and "N customers churned" (field-mapped) for the same real event.
    if (i === 0 && suppressChurn) return;
    const match = pattern.exec(text);
    if (!match) return;
    signals.push({
      id: makeId("info", i),
      label,
      sourceQuote: match[0].trim(),
      polarity,
      ...(actionRelevant ? { actionRelevant: true, suggestedActionTitle } : {}),
    });
  });
  return signals;
}

// Public entry point. Order is deliberate: field-mappable signals first
// (interviews, price, new customer, churn count, retention),
// informational signals last -- the review UI (Part 6) renders editable
// proposals before plain-text ones.
export function extractCaptureSignals(text: string): ProposedSignal[] {
  const trimmed = text.trim();
  if (!trimmed) return [];

  const churnCountSignals = extractChurnCountSignals(trimmed);

  return [
    ...extractInterviewSignals(trimmed),
    ...extractPriceSignals(trimmed),
    ...extractNewCustomerSignal(trimmed),
    ...churnCountSignals,
    ...extractRetentionSignal(trimmed),
    ...extractInformationalSignals(trimmed, churnCountSignals.length > 0),
  ];
}
