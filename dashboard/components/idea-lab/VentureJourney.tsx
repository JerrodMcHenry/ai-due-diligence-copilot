import { getJourneyStage, VENTURE_JOURNEY_STEP_IDS, VENTURE_STAGE_TO_JOURNEY_STAGE } from "@/lib/founderJourney";

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

function currentStepIndex(stage: string | null): number {
  if (!stage) {
    return 0;
  }

  // Goes through the shared normalization map rather than indexing
  // VENTURE_STAGES/VENTURE_JOURNEY_STEP_IDS in parallel -- correct even
  // if the two arrays are ever reordered independently.
  const journeyStageId = VENTURE_STAGE_TO_JOURNEY_STAGE[stage];
  const index = journeyStageId ? VENTURE_JOURNEY_STEP_IDS.indexOf(journeyStageId) : -1;
  return index === -1 ? 0 : index;
}

type VentureJourneyProps = {
  stage: string | null;
};

export default function VentureJourney({ stage }: VentureJourneyProps) {
  const activeIndex = currentStepIndex(stage);

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

      <p className="mt-3 text-center text-[11px] text-text-muted">
        Based on the status you&rsquo;ve set below — not an assessment of how far along the venture
        really is.
      </p>
    </div>
  );
}
