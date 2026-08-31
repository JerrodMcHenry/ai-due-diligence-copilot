import type { MissionType } from "@/types";

// Phase 10.7 -- Founder Missions V1, Part 5. Maps NextMoves' deterministic
// `next_milestones` strings (app/ai/vps_guidance.py::_next_milestones(),
// a small FIXED set of template sentences, not free-form AI text) onto a
// VPS category key + mission_type -- purely a frontend presentation/
// classification lookup, NOT a backend change. Deliberately exact-string
// matched, not fuzzy: an unrecognized milestone (e.g. a future template
// this table hasn't been updated for) safely falls back to no category/
// "other" rather than guessing wrong, so this table can never mislabel a
// mission with more confidence than it actually has.
type MissionSuggestion = {
  relatedCategory: string;
  missionType: MissionType;
};

const KNOWN_MILESTONE_SUGGESTIONS: Record<string, MissionSuggestion> = {
  "Interview 20+ target customers to validate the problem is real.": {
    relatedCategory: "validation",
    missionType: "customer_discovery",
  },
  // Phase 14 -- Founder Journey Audit, Part 11: missionType corrected
  // from "validation" to "pricing". This milestone is specifically about
  // willingness-to-pay, not general customer/problem validation -- the
  // old "validation" tag meant it resolved (via MISSION_TYPE_TO_PLAYBOOK)
  // to Problem Validation, and even before that, via NextMoves' own
  // category-only lookup, to Customer Discovery -- neither is the
  // Pricing & Willingness-to-Pay playbook Phase 12 built specifically
  // for this exact scenario ("Test willingness to pay" is that phase's
  // own worked example of what mission_type=pricing should map to).
  // relatedCategory stays "validation" (used only as a fallback, and for
  // MissionsSection's WHY_IT_MATTERS blurb, which still fits).
  "Secure a first paying customer to validate willingness to pay.": {
    relatedCategory: "validation",
    missionType: "pricing",
  },
  "Define what specifically differentiates your solution from alternatives.": {
    relatedCategory: "problem_solution",
    missionType: "product",
  },
  "Strengthen the founding team's domain, technical, or business coverage.": {
    relatedCategory: "founder_readiness",
    missionType: "founder",
  },
  "Define a primary customer-acquisition strategy.": {
    relatedCategory: "gtm_feasibility",
    missionType: "gtm",
  },
  "Estimate a pricing model and expected gross margin.": {
    relatedCategory: "economic_potential",
    missionType: "pricing",
  },
  "Assess how intense competition is in your target market.": {
    relatedCategory: "market_potential",
    missionType: "other",
  },
};

export function suggestionForMilestone(milestoneText: string): MissionSuggestion {
  return KNOWN_MILESTONE_SUGGESTIONS[milestoneText] ?? { relatedCategory: "other", missionType: "other" };
}
