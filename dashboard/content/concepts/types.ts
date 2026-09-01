// Learn V1 -- Contextual Founder Education.
//
// Two distinct, deliberately separate content shapes -- see data.ts's own
// docstring for why they aren't unified into one generic "Concept" type:
// a VPS category explanation is framed as a QUESTION the category answers
// (Part 5's own worked example), while a metric concept explains a single
// TERM a founder might not know. Both are pure, static, hand-written
// content -- no LLM, no database, matching content/playbooks/'s own
// "code/content-driven, not a table" precedent (see that directory's
// index.ts for the original investigation record this phase reuses
// verbatim rather than re-deciding).

// One VPS category (app/ai/vps_scoring.py::VPS_CATEGORIES -- the same six
// keys VPSResultPanel already receives on every VPSResult.category.key).
export interface VpsCategoryConcept {
  key: string;
  // The question this category is really asking, in plain language --
  // Part 5's own worked example: "Can this venture consistently reach
  // and acquire customers?" Never a restatement of the category's score
  // or internal scoring logic.
  question: string;
  whyItMatters: string;
}

// A single startup term (CAC, gross margin, etc.) -- Part 7's small,
// curated registry. Only concepts actually surfaced by a real field,
// label, or What If scenario in the current product are included; see
// data.ts's own docstring for the specific audit this was built from.
export interface MetricConcept {
  key: string;
  // Plain language first, acronym second where one exists -- Part 8's
  // explicit instruction (e.g. "Customer acquisition cost (CAC)", not
  // bare "CAC").
  name: string;
  whatIsThis: string;
  whyItMatters: string;
  // Slug of an existing Playbook this concept naturally continues into
  // (Part 3's "Go Deeper" layer) -- omitted (not created) when nothing
  // in content/playbooks/data.ts is a genuinely close fit; Learn never
  // forces a weak match just to have a link (Part 3: "Do not
  // automatically create a new Playbook for every concept").
  playbookSlug?: string;
  // Part 10/11: a deterministic, one-sentence "for your venture" line,
  // computed purely from the field's own current value -- no venture
  // read beyond the single number the caller already has in hand, no
  // LLM, no new persistence. `null` is a first-class, honestly-framed
  // branch (Part 11), never treated as an error or a worse case than a
  // known value.
  personalize: (value: number | null) => string;
}
