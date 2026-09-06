import type { VPSCategoryResult } from "@/types";

// Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and Decision
// Support, Part 3.
//
// VPS is gone from the UI, but the data compute_vps() already produces
// per category -- `score` (null vs. a number) and `basis` (the exact
// deterministic sentences the scorer used) -- is still exactly the
// structured understanding this product needs; it was never itself "the
// problem." What was misleading was presenting it AS a 0-10 grade. This
// module re-reads the SAME VPSCategoryResult[] the backend has always
// returned and reclassifies it into three honest knowledge states
// instead, with zero new backend calls and zero new score:
//
//   WHAT WE KNOW     -- only ever true for the "validation" category,
//                       because vps_scoring.py's own module docstring
//                       establishes this structurally: everything under
//                       assumptions.validation is a founder-REPORTED
//                       OBSERVATION, every other group is a MODELED
//                       ASSUMPTION. This is not a per-field tag this
//                       module invents -- it's the same provenance rule
//                       the backend has always scored by.
//   WHAT WE BELIEVE  -- the other five categories, when scored at all
//                       (score !== null): their `basis` lines restated
//                       as assumptions, never as a grade.
//   WHAT WE DON'T KNOW YET -- a category with score === null (not
//                       enough was modeled to say anything at all), or,
//                       for validation specifically, the backend's own
//                       validation_gaps sentences (finer-grained than a
//                       whole-category null -- validation can be
//                       partially known and partially open at once).
//
// Never fabricates precision: a category that IS scored is described by
// its own real basis sentences, never a synthesized summary; a category
// that ISN'T scored says exactly that, nothing more.
const EVIDENCE_CATEGORY_KEY = "validation";

export type CategoryKnowledge = {
  key: string;
  label: string;
  // True only for the one category scored from founder-reported
  // observations -- see this module's own docstring.
  isEvidenceBased: boolean;
  hasSignal: boolean; // category.score !== null
  facts: string[]; // category.basis, verbatim -- only meaningful when hasSignal
};

export function classifyCategoryKnowledge(categories: VPSCategoryResult[]): CategoryKnowledge[] {
  return categories.map((category) => ({
    key: category.key,
    label: category.label,
    isEvidenceBased: category.key === EVIDENCE_CATEGORY_KEY,
    hasSignal: category.score !== null,
    facts: category.basis,
  }));
}
