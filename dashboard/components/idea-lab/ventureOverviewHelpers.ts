import type { VPSCategoryResult } from "@/types";

// Phase 10.6 -- Idea Lab V2. Short, human phrases for VentureOverview's
// "What we still need to figure out" list -- one per VPS category key
// (app/ai/vps_scoring.py's own VPS_CATEGORIES, unchanged). Deliberately
// shorter than the categories' own full labels ("Market Potential" ->
// "Market demand") to read as a casual list, not a repeat of the
// category grid below it.
const STILL_FIGURING_OUT_LABELS: Record<string, string> = {
  market_potential: "Market demand",
  problem_solution: "Problem & solution fit",
  founder_readiness: "Founder fit",
  gtm_feasibility: "Acquisition strategy",
  economic_potential: "Pricing",
  validation: "Real-world validation",
};

// Categories with score === null (Unavailable -- see compute_vps()'s own
// docstring) are genuinely "not enough assumptions yet," not a scored
// weakness -- exactly the set VentureOverview should surface as still
// unknown. Never fabricates a category that IS scored as also unknown.
export function stillFiguringOutFromCategories(categories: VPSCategoryResult[]): string[] {
  return categories
    .filter((category) => category.score === null)
    .map((category) => STILL_FIGURING_OUT_LABELS[category.key] ?? category.label);
}

// Before a model_result exists at all (the draft-review step, before the
// venture is even created) -- every category is still open by
// definition, so this is the same six phrases in the same fixed order
// compute_vps() always evaluates them in, not a computed guess.
export function defaultStillFiguringOut(): string[] {
  return Object.values(STILL_FIGURING_OUT_LABELS);
}
