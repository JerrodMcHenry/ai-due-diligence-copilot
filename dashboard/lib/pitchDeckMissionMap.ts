// Phase 11 -- Pitch Deck Coach V2, Part 13. Maps a deck section's fixed
// SectionCategory (app/models/pitch_deck_coach.py::SectionCategory) onto
// a MissionType -- the same "classify a fixed vocabulary into a mission
// type" job dashboard/components/idea-lab/missionSuggestions.ts already
// does for NextMoves' milestone strings, applied to Pitch Deck Coach's
// own fixed category set instead. Deliberately its own small file, not
// folded into dashboard/lib/playbooks/resourceMap.ts -- that module
// explicitly avoids importing typed enums like MissionType (see its own
// docstring on staying runnable with plain `node`); this one needs
// MissionType and is used from a different surface (the deck review
// page, not Idea Lab), so it stays separate.
//
// A deck category with no clean mission-type fit maps to "other" --
// never a confident-sounding guess. This never runs automatically: it
// only classifies a fix's related_category AFTER the founder has already
// clicked "Make this a mission" on that specific fix.
import type { MissionType } from "@/types";

const DECK_CATEGORY_TO_MISSION_TYPE: Record<string, MissionType> = {
  problem: "validation",
  solution: "product",
  product: "product",
  traction: "customer_discovery",
  business_model: "economics",
  financials: "economics",
  ask: "economics",
  gtm: "gtm",
  team: "founder",
  market: "other",
  competition: "other",
  cover: "other",
  other: "other",
};

export function missionTypeForDeckCategory(category: string): MissionType {
  return DECK_CATEGORY_TO_MISSION_TYPE[category] ?? "other";
}
