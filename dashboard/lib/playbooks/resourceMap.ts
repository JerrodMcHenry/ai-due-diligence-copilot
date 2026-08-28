// Phase 10.9 -- Founder Playbooks V1, Part 6. ONE central mapping
// mechanism -- every "which playbook is relevant here" decision in the
// whole app resolves through the two tables below (VPS_CATEGORY_TO_PLAYBOOK
// and DECK_SECTION_TO_PLAYBOOK), never a duplicated `if (category === ...)`
// scattered across components. Adding, removing, or changing a mapping
// means editing exactly one line, in exactly one place.
//
// Deliberately typed with plain `string` parameters, not imported enum
// types (MissionType/SectionCategory/etc.) -- see
// dashboard/content/playbooks/types.ts's own docstring for why this
// whole directory avoids the "@/..." alias and cross-module imports:
// it keeps this file (and its content-completeness tests) runnable with
// plain `node`, with zero risk of ever importing something from the
// scoring/persistence layers it must never touch (Part 10).
//
// This module reads nothing, writes nothing, and calls nothing -- every
// function here is a pure, synchronous lookup over the fixed tables
// below. It cannot change SPS, VPS, Fundraising Readiness, methodology,
// or any persisted row, structurally: there is no I/O in this file at
// all.
import { getPlaybookBySlug } from "../../content/playbooks/index.ts";
import type { Playbook } from "../../content/playbooks/index.ts";

// VPS category keys (app/ai/vps_scoring.py::VPS_CATEGORIES) -- the same
// six keys Idea Lab's VPSResultPanel/NextMoves already receive on every
// VPSResult, and the same vocabulary Founder Missions' `related_category`
// is drawn from (see missionSuggestions.ts). "validation" maps to
// Customer Discovery specifically because the Part 5 worked example
// ("You haven't talked to customers yet" -> Customer Discovery Playbook)
// is exactly the validation-gap case.
const VPS_CATEGORY_TO_PLAYBOOK: Record<string, string> = {
  market_potential: "market-sizing",
  problem_solution: "problem-validation",
  founder_readiness: "hiring",
  gtm_feasibility: "go-to-market",
  economic_potential: "pricing",
  validation: "customer-discovery",
};

// Founder Missions' `mission_type` (app/models/venture_missions.py::MissionType)
// -- checked BEFORE related_category for a mission, since mission_type is
// the more specific signal purpose-built for this (a mission always has
// one; related_category is optional free text). "other" intentionally has
// no entry -- a mission with no confident mapping shows no playbook link,
// per Part 5A's "must remain usable without opening the playbook."
const MISSION_TYPE_TO_PLAYBOOK: Record<string, string> = {
  customer_discovery: "customer-discovery",
  validation: "problem-validation",
  pricing: "pricing",
  gtm: "go-to-market",
  product: "mvp",
  founder: "hiring",
  economics: "pricing",
};

// Pitch Deck Coach's fixed 12-category vocabulary
// (app/models/pitch_deck_coach.py::SectionCategory) -- "cover" and
// "other" intentionally have no entry (no single playbook fits either
// honestly). Traction maps to Fundraising rather than Go-to-Market: Part
// 5C's own example list offers either, and Part 3's own worked example
// ("Traction evidence is thin" -> "What Investors Mean by Traction")
// frames traction as fundraising-conversation education specifically.
const DECK_SECTION_TO_PLAYBOOK: Record<string, string> = {
  problem: "problem-validation",
  solution: "mvp",
  product: "mvp",
  market: "market-sizing",
  business_model: "pricing",
  traction: "fundraising",
  gtm: "go-to-market",
  competition: "market-sizing",
  team: "hiring",
  financials: "pricing",
  ask: "fundraising",
};

// Fundraising Readiness's gap `pillar` (app/ai/fundraising_readiness.py::
// PILLAR_KEYS) -- checked only for a gap that HAS a pillar. financial_health
// maps to Cap Table & Dilution (not Pricing) per Part 5D's own explicit
// four-playbook list for this surface (Fundraising, Pitch Deck,
// Go-to-Market, Cap Table).
const READINESS_PILLAR_TO_PLAYBOOK: Record<string, string> = {
  market: "market-sizing",
  team: "hiring",
  product: "mvp",
  execution: "go-to-market",
  traction: "fundraising",
  financial_health: "cap-table",
};

function resolve(slug: string | undefined): Playbook | null {
  if (!slug) {
    return null;
  }
  return getPlaybookBySlug(slug) ?? null;
}

export function getPlaybookForVpsCategory(categoryKey: string): Playbook | null {
  return resolve(VPS_CATEGORY_TO_PLAYBOOK[categoryKey]);
}

export function getPlaybookForMission(mission: {
  missionType: string;
  relatedCategory?: string | null;
}): Playbook | null {
  const bySpecificType = MISSION_TYPE_TO_PLAYBOOK[mission.missionType];
  if (bySpecificType) {
    return resolve(bySpecificType);
  }

  if (mission.relatedCategory) {
    return getPlaybookForVpsCategory(mission.relatedCategory);
  }

  return null;
}

export function getPlaybookForDeckSection(category: string): Playbook | null {
  return resolve(DECK_SECTION_TO_PLAYBOOK[category]);
}

// Fundraising Readiness gaps: the "materials" category (no pitch deck
// analyzed yet -- app/ai/fundraising_readiness.py::compute_gaps()) always
// points at the Pitch Deck playbook regardless of pillar, since that IS
// the gap. Every other gap category falls back to its pillar, and
// finally to the generic Fundraising playbook if neither applies (a gap
// is always surfaced ON the Fundraising Readiness page, so that's a safe,
// always-relevant default rather than no link at all).
export function getPlaybookForReadinessGap(gap: {
  category: string;
  pillar?: string | null;
}): Playbook | null {
  if (gap.category === "materials") {
    return resolve("pitch-deck");
  }

  if (gap.pillar && READINESS_PILLAR_TO_PLAYBOOK[gap.pillar]) {
    return resolve(READINESS_PILLAR_TO_PLAYBOOK[gap.pillar]);
  }

  return resolve("fundraising");
}
