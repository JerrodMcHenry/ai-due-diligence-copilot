import { resolveVentureState } from "@/lib/journey/inferVentureStage";
import { VENTURE_STAGE_TO_JOURNEY_STAGE, VENTURE_JOURNEY_STEP_IDS } from "@/lib/founderJourney";
import type { VentureAssumptions } from "@/types";

// Founder Experience Model correction. This component used to render a
// numbered 1-2-3-4-5 stepper (Idea -> Model -> Experiment -> Build ->
// Fundraise) with earlier circles filled solid and a connecting line --
// a staircase that visually claimed mandatory, one-way, unlockable
// progression no matter what its own docstring said. That was
// conceptually wrong: modeling happens repeatedly, founders return to
// assumptions after learning, validation and building overlap, and
// fundraising is a tool some founders never use at all -- never the
// destination every venture is implicitly working toward.
//
// This is now a single, plain-language DESCRIPTION of where the venture
// appears to stand right now (see lib/journey/inferVentureStage.ts's own
// resolveVentureState() docstring for the full reasoning) -- not a
// position on a path, not a level, and never rendered as something the
// venture must move forward through in order. The same underlying
// evidence (the founder's own manual `stage` field, reconciled with real
// assumptions/validation data already in the model) is reused completely
// unchanged; only the presentation changed, from a forward-only stepper
// to a single current-state statement that can equally describe a
// venture moving backward as new evidence complicates an assumption.
function manualStepIndex(stage: string | null): number {
  if (!stage) {
    return -1;
  }

  const journeyStageId = VENTURE_STAGE_TO_JOURNEY_STAGE[stage];
  return journeyStageId ? VENTURE_JOURNEY_STEP_IDS.indexOf(journeyStageId) : -1;
}

// Global visual polish, Part 4. Three mutually-exclusive states, shown
// ONE at a time (never simultaneously competing for attention the way
// e.g. six always-visible VPS categories would) -- restrained venture-
// state identity using colors this design system already defines for
// other purposes, not new hues invented for this: "idea" stays neutral
// (nothing earned yet, not a judgment), "validating" uses "info" (the
// same token MissionsSection/Badge already use for an in-progress/
// informational state), "building" uses "success" (real execution
// underway). The state's own text label is always shown alongside --
// color is reinforcement, never the only signal.
const STATE_PILL_CLASSES: Record<string, string> = {
  idea: "bg-surface-muted text-text-secondary",
  validating: "bg-info-soft text-info",
  building: "bg-success-soft text-success",
};

type VentureJourneyProps = {
  stage: string | null;
  // Optional and additive. Omitted, this behaves exactly as before --
  // manual stage only, defaulting to "Idea" when unset/unmapped.
  assumptions?: VentureAssumptions | null;
};

export default function VentureJourney({ stage, assumptions = null }: VentureJourneyProps) {
  const manualIndex = manualStepIndex(stage);
  const state = resolveVentureState(manualIndex, assumptions);

  return (
    <div className="flex flex-wrap items-center gap-3">
      <span
        className={[
          "inline-flex shrink-0 items-center rounded-full px-3 py-1 text-sm font-bold",
          STATE_PILL_CLASSES[state.id],
        ].join(" ")}
      >
        {state.label}
      </span>
      <p className="text-sm leading-6 text-text-secondary">
        {state.description}{" "}
        <span className="text-text-muted">
          This describes where things stand right now, not a level you&rsquo;ve unlocked — it can move
          forward or backward as new evidence comes in.
        </span>
      </p>
    </div>
  );
}
