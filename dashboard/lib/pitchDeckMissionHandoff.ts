// Phase 11 -- Pitch Deck Coach V2, Part 13. "Make this a mission" needs
// to hand a fix off from /analyze/deck/[reviewId] (no venture context at
// all -- a deck review belongs to a user, never a venture, see
// app/database/db.py's pitch_deck_reviews table comment) to a specific
// venture's own Idea Lab page, where Founder Missions already lives.
//
// Same same-tab sessionStorage stash-and-consume mechanism
// lib/ventureToStartupHandoff.ts and lib/homepageIdeaHandoff.ts already
// established for this exact kind of cross-page, same-tab handoff --
// nothing is created here, and nothing is auto-submitted: the venture
// page reads this once, pre-fills the SAME "pending mission" confirmation
// step Idea Lab's own NextMoves "Make this a mission" button already
// uses (MissionsSection.tsx), and the founder still has to see it appear
// before it's actually posted.
import type { MissionType } from "@/types";

const STORAGE_KEY = "sie:pitch-deck-mission-handoff";

export type PitchDeckMissionHandoff = {
  title: string;
  description: string | null;
  missionType: MissionType;
  relatedCategory: string | null;
  resourceRef: string | null;
};

export function stashPitchDeckMission(mission: PitchDeckMissionHandoff): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(mission));
  } catch {
    // Private browsing / storage disabled -- the founder just won't see
    // the mission pre-filled on the venture page. Not worth blocking
    // navigation over.
  }
}

export function consumePitchDeckMission(): PitchDeckMissionHandoff | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    sessionStorage.removeItem(STORAGE_KEY);
    const parsed = JSON.parse(raw);
    if (
      typeof parsed !== "object" ||
      parsed === null ||
      typeof parsed.title !== "string" ||
      typeof parsed.missionType !== "string"
    ) {
      return null;
    }
    return parsed as PitchDeckMissionHandoff;
  } catch {
    return null;
  }
}
