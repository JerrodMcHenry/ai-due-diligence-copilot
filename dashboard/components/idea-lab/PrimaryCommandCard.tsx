import NextStepCard from "@/components/journey/NextStepCard";
import { resolveIdeaLabNextStep } from "@/lib/journey/resolveIdeaLabNextStep";
import { suggestionForMilestone } from "./missionSuggestions";
import { getPlaybookForMission } from "@/lib/playbooks/resourceMap";

import type { MissionType, VPSResult } from "@/types";

// Phase 33 -- Idea Workspace Information Architecture & Founder Operating
// Loop, Part 7. THE dynamic primary command area -- exactly ONE of two
// mutually exclusive states ever renders, never both at once:
//
//   CASE A (no active action) -- "What should I do next?": the exact
//   same resolveIdeaLabNextStep()-derived recommendation the old
//   IdeaLabNextStep (formerly inline in VentureWorkspace.tsx, removed
//   this phase) already rendered. No new recommendation logic, no new
//   AI, no new score -- same pure resolver, same next_milestones/vps
//   data it always read.
//
//   CASE B (an active action exists) -- "Your current focus": the
//   recommendation the founder already acted on, restated as their
//   current work, with "Log what happened" as the one primary action.
//
// This is the fix for the directive's own named bug: the old page
// rendered a "What should I do next?" recommendation card AND
// MissionsSection's own active-mission card side by side, both
// describing the identical milestone, at the same time, permanently.
// primaryMissionTitle (a REAL venture_missions row's title, lifted up
// from MissionsSection via its own existing onPrimaryMissionChanged
// callback -- see VentureWorkspace.tsx) is the single source of truth
// for "is there an active action right now," deliberately never
// re-derived from resolveIdeaLabNextStep() itself: next_milestones has
// no concept of missions/actions at all and keeps recommending the same
// milestone even after a real mission for it already exists (it only
// changes when the underlying assumptions change) -- checking the real
// mission state, not the raw recommendation, is what makes Case A and
// Case B mutually exclusive rather than racing each other.
type Suggestion = { relatedCategory: string; missionType: MissionType; why?: string };

export default function PrimaryCommandCard({
  modelResult,
  primaryMissionTitle,
  missionedMilestones,
  onStartMission,
  onAnalyzeStartup,
  onEditModel,
  onLogWhatHappened,
}: {
  modelResult: VPSResult | null;
  primaryMissionTitle: string | null;
  missionedMilestones: string[];
  onStartMission: (milestoneText: string, suggestion: Suggestion) => void;
  onAnalyzeStartup: () => void;
  onEditModel: () => void;
  onLogWhatHappened: () => void;
}) {
  // Case B wins outright whenever a real active action exists, regardless
  // of what the raw recommendation currently says.
  if (primaryMissionTitle) {
    const suggestion = suggestionForMilestone(primaryMissionTitle);
    const playbook = getPlaybookForMission(suggestion);

    return (
      <NextStepCard
        eyebrow="Your current focus"
        badge="In progress"
        title={primaryMissionTitle}
        why={suggestion.why ?? "This reduces one of your venture's biggest unknowns right now."}
        primaryAction={{ label: "Log what happened", onClick: onLogWhatHappened }}
        learnPlaybookSlug={playbook?.slug}
      />
    );
  }

  if (!modelResult) {
    return null;
  }

  const nextStep = resolveIdeaLabNextStep(modelResult);

  if (nextStep.kind === "add_assumptions") {
    return (
      <NextStepCard
        title="Add a few assumptions to see your first model"
        why="Even a rough guess at your market or problem statement is enough to get started."
        primaryAction={{ label: "Edit your model", onClick: onEditModel }}
      />
    );
  }

  if (nextStep.kind === "work_on_milestone") {
    const suggestion = suggestionForMilestone(nextStep.milestoneText);
    const alreadyMissioned = missionedMilestones.includes(nextStep.milestoneText);
    const playbook = getPlaybookForMission({
      missionType: suggestion.missionType,
      relatedCategory: suggestion.relatedCategory,
    });

    return (
      <NextStepCard
        title={nextStep.milestoneText}
        why={suggestion.why ?? "This reduces one of your venture's biggest unknowns right now."}
        primaryAction={
          alreadyMissioned
            ? { label: "Go to your actions", href: "#your-missions" }
            : { label: "Start this action", onClick: () => onStartMission(nextStep.milestoneText, suggestion) }
        }
        learnPlaybookSlug={playbook?.slug}
      />
    );
  }

  // "ready_for_real_startup" -- Part 8's idea -> real startup bridge.
  // Deliberately explains the boundary rather than implying anything
  // transfers automatically: analyzing does not create a startup by
  // itself, and nothing here invents evidence.
  return (
    <NextStepCard
      eyebrow="Your model looks solid"
      title="Ready to turn this into a real startup?"
      why="This modeled idea shows what COULD work, based on your own assumptions. A real Startup Profile shows what evidence supports TODAY, built the same way for every company on SIE. Analyzing brings over your own description as a starting point -- it never creates anything or invents evidence on your behalf."
      primaryAction={{ label: "Analyze My Startup", onClick: onAnalyzeStartup }}
    />
  );
}
