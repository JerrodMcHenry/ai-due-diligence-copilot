// Phase 10.9 -- Founder Playbooks V1.
//
// INVESTIGATION FINDING (Part 1): the repo has zero prior playbook/guide/
// education concept. The closest adjacent things are all narrower and
// stay untouched: venture_missions.resource_ref (a nullable, unused-in-V1
// column already reserved for exactly this future use, per its own
// comment in app/database/db.py) and vps_guidance.py's next_milestones
// (a fixed, deterministic template list). Neither needed a schema or
// backend change to support this phase -- see resourceMap.ts's own
// docstring for why the mapping lives entirely in the frontend, keyed
// off fields (mission_type, related_category, deck section category,
// readiness gap category/pillar) every one of those systems ALREADY
// returns today.
//
// ARCHITECTURE DECISION (Part 2): code/content-driven, not a database
// table. A playbook is curated, reviewed prose written by this codebase,
// never user-generated, never queried/filtered/searched at scale, and
// never touched by an LLM -- there is no requirement here that a table +
// migration + admin CRUD would serve better than a typed array literal.
// If a future phase needs founder-editable or CMS-authored content, this
// module is the one place that would need to change; nothing that reads
// PLAYBOOKS needs to know the difference.
import { PLAYBOOKS } from "./data.ts";
import type { Playbook, PlaybookJourneyStage } from "./types.ts";

export type { Playbook, PlaybookAudience, PlaybookJourneyStage } from "./types.ts";

export function getAllPlaybooks(): Playbook[] {
  return PLAYBOOKS;
}

export function getPlaybookBySlug(slug: string): Playbook | undefined {
  return PLAYBOOKS.find((playbook) => playbook.slug === slug);
}

const JOURNEY_STAGE_LABELS: Record<PlaybookJourneyStage, string> = {
  start: "Start",
  model: "Model",
  build: "Build",
  pitch: "Pitch",
  fundraise: "Fundraise",
};

const JOURNEY_STAGE_ORDER: PlaybookJourneyStage[] = ["start", "model", "build", "pitch", "fundraise"];

export type PlaybookJourneyGroup = {
  stage: PlaybookJourneyStage;
  label: string;
  playbooks: Playbook[];
};

// Part 4's suggested journey grouping, computed from each playbook's own
// `journeyStage` rather than a second, separately-maintained ordering
// list -- adding a playbook only ever requires editing data.ts.
export function getJourneyGroups(): PlaybookJourneyGroup[] {
  return JOURNEY_STAGE_ORDER.map((stage) => ({
    stage,
    label: JOURNEY_STAGE_LABELS[stage],
    playbooks: PLAYBOOKS.filter((playbook) => playbook.journeyStage === stage),
  }));
}
