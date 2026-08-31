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

  // --- Phase 12 (Founder Playbooks V1) additions ---------------------
  // All optional: the original 8 playbooks above this phase's scope
  // (market-sizing, pricing, go-to-market, pitch-deck, fundraising,
  // cap-table, company-formation, hiring, how-vcs-evaluate-startups)
  // keep working exactly as before without backfilling any of these;
  // the detail page renders each section only when present. Only the
  // 5 playbooks this phase targets (customer-discovery,
  // problem-validation, mvp, pricing-validation, early-traction) set
  // them all.

  // One line: "what you're trying to learn" by doing this playbook --
  // distinct from whyItMatters (which explains the broader stakes).
  objective?: string;
  // "BEFORE YOU START" -- prep to do before the real-world activity
  // begins (e.g. who to recruit, what to have ready).
  beforeYouStart?: string[];
  // "WHAT TO ASK / DO" -- concrete prompts/questions/actions, distinct
  // from `steps` (the overall sequence). This is the actual script.
  questionsToAskOrDo?: string[];
  // A full worked example (e.g. an interview script) -- alternating
  // speaker labels and lines, rendered as a small transcript. Optional;
  // only Customer Discovery uses it in V1.
  exampleScript?: { speaker: string; line: string }[];
  // "WHAT GOOD SIGNAL LOOKS LIKE" / "WHAT WEAK OR NEGATIVE SIGNAL LOOKS
  // LIKE" -- kept as two explicit, separate lists (Phase 12 Part 6) so
  // a founder can tell strong evidence from a polite non-answer at a
  // glance, not buried in one combined paragraph.
  goodSignal?: string[];
  weakSignal?: string[];
  // "WHEN YOU'RE DONE" -- a plain-language completion condition (not a
  // persisted checkbox; see checklist for the existing self-check list).
  whenYoureDone?: string;
  // "WHAT TO DO NEXT" -- action-oriented next steps, e.g. pointing back
  // to Missions / Record What I Learned. Never a second reflection
  // system of its own (Part 20's explicit prohibition).
  whatToDoNext?: string[];
  // Founder Missions' `mission_type` values (app/models/venture_missions.py
  // ::MissionType) this playbook is the natural match for -- documentation
  // of intent; the actual resolution mechanism stays entirely in
  // dashboard/lib/playbooks/resourceMap.ts's MISSION_TYPE_TO_PLAYBOOK
  // table (Part 12), never duplicated logic here.
  relatedMissionTypes?: string[];
}
