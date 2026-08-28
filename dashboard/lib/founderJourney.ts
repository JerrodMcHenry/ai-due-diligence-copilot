// Phase 10.10 -- Founder Journey Integration, Part 3. ONE shared founder
// journey vocabulary -- before this file, three separate hardcoded
// 5-label arrays already existed for essentially the same idea
// (components/home/IdeaJourney.tsx, components/idea-lab/VentureJourney.tsx,
// and the backend's own VENTURE_STAGES/"Idea"|"Researching"|"Validating"|
// "Building"|"Launched"), plus a fourth, DIFFERENT 5-value taxonomy in
// Founder Playbooks (journeyStage: "start"|"model"|"build"|"pitch"|
// "fundraise"). This file is the single place that vocabulary now lives;
// every component that used to hardcode its own journey labels imports
// from here instead.
//
// Deliberately presentation-only and additive:
// - No database persistence, no backend journey engine, no journey score.
// - Never implies a deterministic sequence or a completion percentage --
//   see JourneyStage's own docstring below.
// - `VENTURE_STAGES` (app/models/idea_lab.py's stage field) and Founder
//   Playbooks' `PlaybookJourneyStage` are NOT renamed or modified --
//   Part 11's own rule ("do not rename backend/domain models just for UX
//   copy"). This file only NORMALIZES those existing vocabularies onto
//   the new 8-stage one for display purposes.
// - Zero imports from anywhere else in the app (mirrors the discipline
//   dashboard/content/playbooks/*.ts already established), so this stays
//   trivially testable with plain `node` and can never accidentally pick
//   up a dependency on the scoring/persistence layers.
export type JourneyStageId =
  | "idea"
  | "model"
  | "learn"
  | "experiment"
  | "improve"
  | "build"
  | "pitch"
  | "fundraise";

// This is GUIDANCE, not a funnel (Part 2's own explicit requirement): a
// founder may skip, revisit, or work several of these simultaneously, or
// enter SIE already at "pitch" or "fundraise" with an existing company.
// Nothing that reads this array may render it as a progress bar with a
// completion percentage, or claim a founder must pass through every
// stage in order.
export interface JourneyStage {
  id: JourneyStageId;
  label: string;
  plainLanguageLabel: string;
  description: string;
}

export const JOURNEY_STAGES: JourneyStage[] = [
  {
    id: "idea",
    label: "Idea",
    plainLanguageLabel: "Your Idea",
    description: "Turn something you're imagining into a startup concept.",
  },
  {
    id: "model",
    label: "Model",
    plainLanguageLabel: "Your Model",
    description: "Understand how the startup might work.",
  },
  {
    id: "learn",
    label: "Learn",
    plainLanguageLabel: "What You Need to Know",
    description: "Understand the concepts you need right now.",
  },
  {
    id: "experiment",
    label: "Experiment",
    plainLanguageLabel: "Test Your Idea",
    description: "Test the assumptions that matter.",
  },
  {
    id: "improve",
    label: "Improve",
    plainLanguageLabel: "What You've Learned",
    description: "Update the model based on what you learn.",
  },
  {
    id: "build",
    label: "Build",
    plainLanguageLabel: "Building",
    description: "Turn the validated concept into a real company.",
  },
  {
    id: "pitch",
    label: "Pitch",
    plainLanguageLabel: "Your Pitch",
    description: "Explain the company clearly.",
  },
  {
    id: "fundraise",
    label: "Fundraise",
    plainLanguageLabel: "Get Ready to Raise",
    description: "Prepare for investor conversations.",
  },
];

const JOURNEY_STAGES_BY_ID: Record<JourneyStageId, JourneyStage> = Object.fromEntries(
  JOURNEY_STAGES.map((stage) => [stage.id, stage])
) as Record<JourneyStageId, JourneyStage>;

export function getJourneyStage(id: JourneyStageId): JourneyStage {
  return JOURNEY_STAGES_BY_ID[id];
}

// --- Normalization: Founder Playbooks' journeyStage -------------------------
//
// Playbooks use a smaller, 5-value vocabulary (start/model/build/pitch/
// fundraise) written before this phase. Rather than widen Playbooks'
// own field (Part 11: never rename a domain model just for UX copy),
// this maps each existing value onto the closest matching stage in the
// larger 8-stage vocabulary above. "start" (Customer Discovery, Problem
// Validation) maps to "learn" -- those two playbooks ARE the "understand
// the concepts you need right now" content for an early idea, which is
// exactly what the "learn" stage means.
export const PLAYBOOK_STAGE_TO_JOURNEY_STAGE: Record<string, JourneyStageId> = {
  start: "learn",
  model: "model",
  build: "build",
  pitch: "pitch",
  fundraise: "fundraise",
};

// --- Normalization: modeled venture `stage` (VENTURE_STAGES) ---------------
//
// The backend's own five-value `stage` field (unchanged) -- "Validating"
// maps to "experiment" (that value's whole meaning is "testing
// assumptions against reality") rather than the old presentation label
// "Validate", to match this phase's vocabulary exactly. "Launched" maps
// to "fundraise" as a heuristic, not a claim every launched venture is
// fundraising -- carried over unchanged from VentureJourney.tsx's own
// prior mapping.
export const VENTURE_STAGE_TO_JOURNEY_STAGE: Record<string, JourneyStageId> = {
  Idea: "idea",
  Researching: "model",
  Validating: "experiment",
  Building: "build",
  Launched: "fundraise",
};

// The 5 stages VentureJourney.tsx's per-venture stepper actually needs,
// in order -- a curated subset of the 8, not all of them (Learn/Improve/
// Pitch are activities that happen WITHIN these stages, not separate
// positions on a single-venture stepper backed by one `stage` field).
export const VENTURE_JOURNEY_STEP_IDS: JourneyStageId[] = ["idea", "model", "experiment", "build", "fundraise"];
