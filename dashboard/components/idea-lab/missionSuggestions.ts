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
  // Founder Loop V2, Section 5: a milestone-specific "why does this
  // matter given what we already know" line -- richer than the generic,
  // category-level WHY_IT_MATTERS blurb in MissionsSection.tsx, because
  // it can speak to the actual reasoning behind THIS particular
  // recommendation (see app/ai/vps_guidance.py::_next_milestones()'s own
  // docstring for the traction-aware selection logic this explains).
  // Optional: falls back to the category-level blurb where absent.
  why?: string;
};

const KNOWN_MILESTONE_SUGGESTIONS: Record<string, MissionSuggestion> = {
  "Interview 20+ target customers to validate the problem is real.": {
    relatedCategory: "validation",
    missionType: "customer_discovery",
    why: "Real conversations are the cheapest way to find out whether the problem is as real and painful as you believe.",
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
    why: "Willingness to pay is a different, stronger signal than interest — it's the fastest way to know if this is a business, not just a nice-to-have.",
  },
  "Define what specifically differentiates your solution from alternatives.": {
    relatedCategory: "problem_solution",
    missionType: "product",
    why: "A specific point of difference makes the venture easier to explain, defend, and remember.",
  },
  "Strengthen the founding team's domain, technical, or business coverage.": {
    relatedCategory: "founder_readiness",
    missionType: "founder",
    why: "Investors and cofounders look for relevant experience and complementary skills on the founding team.",
  },
  "Define a primary customer-acquisition strategy.": {
    relatedCategory: "gtm_feasibility",
    missionType: "gtm",
    why: "Without a clear way to reach customers, even a great product can struggle to grow.",
  },
  // Founder Loop V2, Section 5: NEW candidate, added alongside the
  // existing fixed template set in app/ai/vps_guidance.py's own
  // _next_milestones() -- surfaces only for a venture that already has
  // real traction (paying customers or revenue) whose GTM Feasibility
  // category isn't yet a modeled strength. Distinct from "Define a
  // primary customer-acquisition strategy." above, which is for a
  // venture that hasn't named a strategy at all yet.
  "Prove customer acquisition works repeatably beyond founder-led sales or referrals.": {
    relatedCategory: "gtm_feasibility",
    missionType: "gtm",
    why: "Strong early traction often comes from founder-led selling and referrals. The next real uncertainty is whether growth holds up through a repeatable motion, not whether the problem or the product is real.",
  },
  "Estimate a pricing model and expected gross margin.": {
    relatedCategory: "economic_potential",
    missionType: "pricing",
    why: "Understanding your margins early avoids building something that can't sustain itself.",
  },
  "Assess how intense competition is in your target market.": {
    relatedCategory: "market_potential",
    missionType: "other",
    why: "Knowing your competitive landscape helps you position realistically.",
  },
};

export function suggestionForMilestone(milestoneText: string): MissionSuggestion {
  return KNOWN_MILESTONE_SUGGESTIONS[milestoneText] ?? { relatedCategory: "other", missionType: "other" };
}
