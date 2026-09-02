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

// Informational-only signals: real, worth showing, but with no safe
// single-field mapping onto VentureAssumptions (Part 5: "do NOT pretend
// every note can be structured"). Each entry is [pattern, label,
// polarity].
const INFORMATIONAL_PATTERNS: ReadonlyArray<{
  pattern: RegExp;
  label: string;
  polarity: ProposedSignal["polarity"];
}> = [
  { pattern: /\bchurned\b|\bcancel(?:l?ed)?\b|\blost the customer\b/i, label: "Customer churn mentioned", polarity: "negative" },
  { pattern: /\bshipped\b|\blaunched\b|\breleased\b|\bdeployed\b/i, label: "Product milestone mentioned", polarity: "positive" },
  { pattern: /\binvestor\b|\bVC\b|\bterm sheet\b|\bfundrais(?:e|ing)\b|\bpitch(?:ed)?\b/i, label: "Fundraising conversation mentioned", polarity: "neutral" },
  { pattern: /\bcompetitor(?:s)?\b/i, label: "Competitor/market observation mentioned", polarity: "neutral" },
  { pattern: /\bexperiment\b|\bfailed\b|\bdidn't work\b|\bdid not work\b|\bno(?:body| one) clicked\b/i, label: "Experiment result mentioned", polarity: "neutral" },
  { pattern: /\b(?:said|confirmed|agreed)\b[^.!?]{0,40}\bproblem\b/i, label: "Problem confirmation mentioned", polarity: "positive" },
];

function extractInformationalSignals(text: string): ProposedSignal[] {
  const signals: ProposedSignal[] = [];
  INFORMATIONAL_PATTERNS.forEach(({ pattern, label, polarity }, i) => {
    const match = pattern.exec(text);
    if (!match) return;
    signals.push({
      id: makeId("info", i),
      label,
      sourceQuote: match[0].trim(),
      polarity,
    });
  });
  return signals;
}

// Public entry point. Order is deliberate: field-mappable signals first
// (interviews, price, new customer), informational signals last -- the
// review UI (Part 6) renders editable proposals before plain-text ones.
export function extractCaptureSignals(text: string): ProposedSignal[] {
  const trimmed = text.trim();
  if (!trimmed) return [];

  return [
    ...extractInterviewSignals(trimmed),
    ...extractPriceSignals(trimmed),
    ...extractNewCustomerSignal(trimmed),
    ...extractInformationalSignals(trimmed),
  ];
}
