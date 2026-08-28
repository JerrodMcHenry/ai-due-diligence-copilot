// Phase 10.9 -- Founder Playbooks V1. Content-driven, not database-backed
// (Part 2's own default, confirmed correct by investigation: nothing here
// needs to be queried, filtered, or authored by anyone other than this
// codebase, so a table + admin UI would be pure unused complexity for
// V1 -- see dashboard/content/playbooks/index.ts's own docstring for the
// full investigation record). No LLM involved anywhere in this file or
// anything that reads it -- a Playbook is curated, reviewed prose.
//
// Deliberately NOT importing anything from "@/types" -- this whole
// directory (and dashboard/lib/playbooks/resourceMap.ts) is written with
// zero dependency on any other app module, specifically so it stays
// trivially runnable outside Next's bundler (see dashboard/tests/
// playbooks.test.ts, executed with plain `node`, no path-alias resolver
// available) and so it can never accidentally import something from the
// scoring/persistence layers it must never touch (Part 10's firewall).
export type PlaybookJourneyStage = "start" | "model" | "build" | "pitch" | "fundraise";

export type PlaybookAudience = "founder" | "investor" | "general";

export interface Playbook {
  slug: string;
  title: string;
  // One sentence, shown on cards/lists.
  description: string;
  journeyStage: PlaybookJourneyStage;
  audience: PlaybookAudience;
  estimatedMinutes: number;
  // Slugs of other playbooks worth reading next -- must always resolve
  // to a real slug (enforced in dashboard/tests/playbooks.test.ts).
  relatedPlaybooks: string[];

  // "What is this?" -- plain-language, 1-3 short paragraphs.
  whatIsThis: string[];
  // "Why does it matter?"
  whyItMatters: string;
  // "What should I do?" -- a short, concrete sequence, not a treatise.
  steps: string[];
  commonMistakes: string[];
  checklist: string[];
  // "What good looks like" -- a short, concrete picture of doing this well.
  whatGoodLooksLike: string;
}
