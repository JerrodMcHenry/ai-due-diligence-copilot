import { getJourneyStage, VENTURE_JOURNEY_STEP_IDS, VENTURE_STAGE_TO_JOURNEY_STAGE } from "@/lib/founderJourney";
import { resolveVentureStepIndex } from "@/lib/journey/inferVentureStage";
import type { VentureAssumptions } from "@/types";

// Phase 10.6 -- Idea Lab V2, Part 4. Reuses Home's IDEA -> MODEL ->
// EXPERIMENT -> BUILD -> FUNDRAISE progression (components/home/
// IdeaJourney.tsx) as a per-venture position indicator -- product
// navigation and progress framing, explicitly NOT an objective claim the
// venture has reached a business stage (Part 4). It is a straightforward
// relabeling of the EXISTING `stage` field's five values (VENTURE_STAGES,
// unchanged) onto friendlier journey language.
//
// Phase 10.10, Part 3: the labels themselves now come from the ONE
// shared founderJourney.ts vocabulary (VENTURE_STAGE_TO_JOURNEY_STAGE's
// own docstring has the full Idea/Researching/Validating/Building/
// Launched -> idea/model/experiment/build/fundraise mapping) instead of
// a second, locally hardcoded label array. The underlying `stage` value
// stored on the venture, the VENTURE_STAGES dropdown, and every API
// contract remain completely unchanged -- this is presentation only,
// same discipline as Phase 10.3's nav relabeling.
const JOURNEY_LABELS = VENTURE_JOURNEY_STEP_IDS.map((id) => getJourneyStage(id).label);

// Founder Loop V2, Section 10: returns -1 (no signal), not 0, when
// `stage` is unset or doesn't map onto the shared vocabulary -- see
// lib/journey/inferVentureStage.ts's own docstring for why that
// distinction matters (an unmapped manual stage must never silently
// outrank real evidence just by defaulting to "Idea").
function manualStepIndex(stage: string | null): number {
  if (!stage) {
    return -1;
  }

  // Goes through the shared normalization map rather than indexing
  // VENTURE_STAGES/VENTURE_JOURNEY_STEP_IDS in parallel -- correct even
  // if the two arrays are ever reordered independently.
  const journeyStageId = VENTURE_STAGE_TO_JOURNEY_STAGE[stage];
  return journeyStageId ? VENTURE_JOURNEY_STEP_IDS.indexOf(journeyStageId) : -1;
}

type VentureJourneyProps = {
  stage: string | null;
  // Founder Loop V2, Section 10: optional and additive. Omitted (e.g. a
  // future caller with no assumptions in hand), this behaves exactly as
  // before -- manual stage only, defaulting to "Idea" when unset/unmapped.
  assumptions?: VentureAssumptions | null;
};

export default function VentureJourney({ stage, assumptions = null }: VentureJourneyProps) {
  const manualIndex = manualStepIndex(stage);
  const activeIndex = Math.max(0, resolveVentureStepIndex(manualIndex, assumptions));
  // Section 10's explicit requirement: the UI must say WHY this step is
  // active. True whether the evidence-inferred index or the founder's
  // own manual stage ended up winning -- both ultimately trace back to
  // the venture model, never an arbitrary checklist.
  const explanation = assumptions
    ? "Based on the status and evidence in your venture model."
    : "Based on the status you’ve set below — not an assessment of how far along the venture really is.";

  return (
    <div>
      <div className="flex items-center">
        {JOURNEY_LABELS.map((label, index) => (
          <div key={label} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <span
                className={[
                  "flex size-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold",
                  index < activeIndex
                    ? "border-primary bg-primary text-white"
                    : index === activeIndex
                      ? "border-primary bg-surface text-primary"
                      : "border-border bg-surface text-text-muted",
                ].join(" ")}
              >
                {index + 1}
              </span>
              <span
                className={[
                  "text-[11px] font-semibold",
                  index === activeIndex ? "text-primary" : "text-text-muted",
                ].join(" ")}
              >
                {label}
              </span>
            </div>

            {index < JOURNEY_LABELS.length - 1 ? (
              <span
                aria-hidden="true"
                className={["mx-1.5 h-px flex-1", index < activeIndex ? "bg-primary" : "bg-border"].join(" ")}
                style={{ marginBottom: "1.1rem" }}
              />
            ) : null}
          </div>
        ))}
      </div>

      <p className="mt-3 text-center text-[11px] text-text-muted">{explanation}</p>
    </div>
  );
}
