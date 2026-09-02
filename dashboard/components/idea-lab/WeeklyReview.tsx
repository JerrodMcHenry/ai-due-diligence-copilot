import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import { buildWeeklyReview } from "@/lib/journey/buildWeeklyReview";
import { resolveIdeaLabNextStep } from "@/lib/journey/resolveIdeaLabNextStep";
import { suggestionForMilestone } from "./missionSuggestions";

import type { VentureHistoryResponse, VPSResult, MissionType } from "@/types";

// Phase 24 -- Weekly Founder Review V1.
//
// Every fact rendered here is FACT or DERIVED FACT (buildWeeklyReview.ts's
// own deterministic aggregation over the existing, unmodified
// GET /ventures/{id}/history) or a DETERMINISTIC INTERPRETATION reused
// verbatim from resolveIdeaLabNextStep() -- the exact same function
// IdeaLabNextStep already uses above this component in VentureWorkspace.
// No AI call. No new score. No progress percentage, grade, streak, or
// completion ring anywhere in this file (Part 15). See
// docs/product/WEEKLY_FOUNDER_REVIEW_V1.md's own fact-classification
// table for the section-by-section breakdown.
type WeeklyReviewProps = {
  history: VentureHistoryResponse | null;
  isLoadingHistory: boolean;
  modelResult: VPSResult | null;
  missionedMilestones: string[];
  onStartMission: (milestoneText: string, suggestion: { relatedCategory: string; missionType: MissionType }) => void;
};

function formatVps(value: number | null): string {
  return value === null ? "—" : value.toFixed(1);
}

export default function WeeklyReview({
  history,
  isLoadingHistory,
  modelResult,
  missionedMilestones,
  onStartMission,
}: WeeklyReviewProps) {
  if (isLoadingHistory) {
    return <div className="h-56 animate-pulse rounded-2xl border border-border bg-surface" />;
  }

  if (!history) {
    return null; // history failed to load elsewhere -- VentureProgress already surfaces that error; no duplicate error UI here
  }

  const review = buildWeeklyReview(history);
  const nextStep = resolveIdeaLabNextStep(modelResult);

  return (
    <BaseCard className="p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{review.windowLabel}</p>

      {review.isBrandNew ? (
        <BrandNewState />
      ) : !review.hasActivityInWindow ? (
        <QuietWeekState nextStep={nextStep} missionedMilestones={missionedMilestones} onStartMission={onStartMission} />
      ) : (
        <ActiveWeekSections review={review} />
      )}

      {/* Part 9/10: close the loop back into Act -- a compact callback to
          the SAME current priority IdeaLabNextStep already shows above,
          never a duplicate full card. Rendered for every non-quiet,
          non-brand-new state; the quiet-week branch already includes its
          own version of this. */}
      {!review.isBrandNew && review.hasActivityInWindow ? (
        <FocusNext nextStep={nextStep} missionedMilestones={missionedMilestones} onStartMission={onStartMission} />
      ) : null}
    </BaseCard>
  );
}

function BrandNewState() {
  return (
    <div className="mt-3">
      <p className="text-sm text-text-primary">Your venture history is just getting started.</p>
      <p className="mt-1.5 text-sm leading-6 text-text-secondary">
        As you take actions, capture what happens, and update your model, this space will fill in with what you did,
        what you learned, and what changed.
      </p>
    </div>
  );
}

type NextStepInfo = ReturnType<typeof resolveIdeaLabNextStep>;

function QuietWeekState({
  nextStep,
  missionedMilestones,
  onStartMission,
}: {
  nextStep: NextStepInfo;
  missionedMilestones: string[];
  onStartMission: WeeklyReviewProps["onStartMission"];
}) {
  return (
    <div className="mt-3">
      {/* Part 11: honest, never shaming. The product genuinely does not
          know whether anything happened outside SIE. */}
      <p className="text-sm text-text-primary">No building activity has been recorded here yet.</p>
      <p className="mt-1.5 text-sm text-text-secondary">
        If something happened with your venture this week, it&rsquo;s worth putting here.
      </p>
      <FocusNext nextStep={nextStep} missionedMilestones={missionedMilestones} onStartMission={onStartMission} label="Your current focus" />
    </div>
  );
}

function ActiveWeekSections({ review }: { review: ReturnType<typeof buildWeeklyReview> }) {
  const { whatYouDid, whatYouLearned, vpsChange, assumptionChanges, strongestMovement } = review;

  const didItems: string[] = [];
  if (whatYouDid.actionsCompleted > 0) didItems.push(`${whatYouDid.actionsCompleted} action${whatYouDid.actionsCompleted === 1 ? "" : "s"} completed`);
  if (whatYouDid.observationsCaptured > 0) didItems.push(`${whatYouDid.observationsCaptured} observation${whatYouDid.observationsCaptured === 1 ? "" : "s"} captured`);
  if (whatYouDid.learningsRecorded > 0) didItems.push(`${whatYouDid.learningsRecorded} learning${whatYouDid.learningsRecorded === 1 ? "" : "s"} recorded`);
  if (whatYouDid.modelUpdates > 0) didItems.push(`${whatYouDid.modelUpdates} model update${whatYouDid.modelUpdates === 1 ? "" : "s"}`);

  const vpsMaterialChange = vpsChange && vpsChange.before !== null && vpsChange.after !== null && Math.abs(vpsChange.after - vpsChange.before) >= 0.05;

  return (
    <div className="mt-3 space-y-5">
      {didItems.length > 0 ? (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What you did</h3>
          <ul className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1">
            {didItems.map((item) => (
              <li key={item} className="text-sm text-text-primary">
                {item}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {whatYouLearned.length > 0 ? (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What you learned</h3>
          <ul className="mt-1.5 space-y-2">
            {whatYouLearned.map((item, i) => (
              <li key={i} className="text-sm leading-6 text-text-secondary">
                &ldquo;{item.text}&rdquo;
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {vpsChange || assumptionChanges.length > 0 ? (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">What changed</h3>
          <div className="mt-1.5 space-y-1.5">
            {vpsChange ? (
              <p className="flex flex-wrap items-baseline gap-x-2 text-sm">
                <span className="text-text-secondary">Venture Potential Score</span>
                <span className="font-semibold text-text-primary">
                  {formatVps(vpsChange.before)} <span aria-hidden="true" className="text-text-muted">→</span> {formatVps(vpsChange.after)}
                </span>
              </p>
            ) : null}
            {vpsChange && !vpsMaterialChange && assumptionChanges.length > 0 ? (
              <p className="text-xs text-text-muted">
                Your venture model changed, while Venture Potential Score remained {formatVps(vpsChange.after)}.
              </p>
            ) : null}
            {assumptionChanges.map((change) => (
              <p key={change.field_path} className="flex flex-wrap items-baseline gap-x-2 text-sm">
                <span className="text-text-secondary">{change.label}</span>
                <span className="font-medium text-text-primary">
                  {change.before} <span aria-hidden="true" className="text-text-muted">→</span> {change.after}
                </span>
              </p>
            ))}
          </div>
        </section>
      ) : null}

      {strongestMovement ? (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-text-muted">Strongest movement</h3>
          {/* Part 8/15: neutral phrasing regardless of direction -- never
              "declined"/"lost progress"; a downward movement reads as
              "moved... after your assumptions changed," matching the
              directive's own worked example verbatim. */}
          <p className="mt-1.5 text-sm text-text-secondary">
            {strongestMovement.direction === "positive" ? (
              <>
                <span className="font-medium text-text-primary">{strongestMovement.label}</span> strengthened from{" "}
                {strongestMovement.before.toFixed(1)} → {strongestMovement.after.toFixed(1)}.
              </>
            ) : (
              <>
                <span className="font-medium text-text-primary">{strongestMovement.label}</span> moved from{" "}
                {strongestMovement.before.toFixed(1)} → {strongestMovement.after.toFixed(1)} after your assumptions changed.
              </>
            )}
          </p>
        </section>
      ) : null}
    </div>
  );
}

function FocusNext({
  nextStep,
  missionedMilestones,
  onStartMission,
  label = "What still needs proving",
}: {
  nextStep: NextStepInfo;
  missionedMilestones: string[];
  onStartMission: WeeklyReviewProps["onStartMission"];
  label?: string;
}) {
  if (nextStep.kind === "add_assumptions") {
    return null; // no meaningful current priority to show yet -- IdeaLabNextStep above already covers this state
  }

  if (nextStep.kind === "ready_for_real_startup") {
    return (
      <div className="mt-4 border-t border-border pt-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{label}</p>
        <p className="mt-1 text-sm text-text-secondary">Your model looks solid -- see the full picture above.</p>
      </div>
    );
  }

  const alreadyMissioned = missionedMilestones.includes(nextStep.milestoneText);
  const suggestion = suggestionForMilestone(nextStep.milestoneText);

  return (
    <div className="mt-4 border-t border-border pt-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{label}</p>
      <p className="mt-1 text-sm text-text-primary">{nextStep.milestoneText}</p>
      {!alreadyMissioned ? (
        <Button type="button" variant="secondary" size="sm" className="mt-2" onClick={() => onStartMission(nextStep.milestoneText, suggestion)}>
          Make this an action
        </Button>
      ) : null}
    </div>
  );
}
