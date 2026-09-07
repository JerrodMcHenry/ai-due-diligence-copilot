import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import { diffScenarioAssumptions } from "@/lib/simulate/assumptionDiff";
import { computeDirectConsequences } from "@/lib/simulate/directConsequences";
import { buildScenarioInsights } from "@/lib/simulate/scenarioInsights";

import type { ScenarioCompareResponse, VentureAssumptions } from "@/types";

type ScenarioComparisonProps = {
  scenario: ScenarioCompareResponse;
  // Simulate V1, Part 5/10: the raw before/after assumption VALUES, not
  // just the resulting VPSResult -- ScenarioCompareResponse never carried
  // these (it's stateless, computed twice), so the caller
  // (VentureWorkspace.tsx) passes its own already-in-hand
  // venture.assumptions / draft alongside the existing `scenario` prop.
  // Nothing new is fetched; this is purely additive.
  currentAssumptions: VentureAssumptions;
  scenarioAssumptions: VentureAssumptions;
  onApply: () => void;
  onDiscard: () => void;
  isApplying: boolean;
};

// Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and Decision
// Support, Part 6. What-If stops behaving like "change assumption -> see
// new score" and instead answers "if this became true, what would change
// about our understanding of the venture?" The backend call underneath is
// completely unchanged (POST /ventures/scenario-compare still returns two
// full VPSResults, categories/basis/next_milestones and all) -- this
// component simply stops reading `.vps` and the per-category numeric
// `.score` from that response, and instead re-derives four honest,
// qualitative sections from the SAME data:
//
//   ASSUMPTION CHANGES     -- diffScenarioAssumptions(), unchanged.
//   DIRECT CONSEQUENCES    -- computeDirectConsequences(), unchanged.
//   WHAT THIS WOULD STRENGTHEN -- categories whose basis/evidence
//     improved (explainCategoryChanges(), unchanged), restated as real
//     sentences, never a score delta.
//   WHAT WOULD STILL BE UNKNOWN -- categories still Unavailable after the
//     scenario, plus the backend's own validation_gaps sentences.
//   NEW QUESTIONS TO INVESTIGATE -- milestones that newly appear in
//     next_milestones as a consequence of this scenario (a simple set
//     diff over data the backend already computes deterministically --
//     no new AI call, no new recommendation engine).
//
// No VPS number appears anywhere in this component -- not as a headline,
// not in a footnote, not as a "your score would change" caveat.
export default function ScenarioComparison({
  scenario,
  currentAssumptions,
  scenarioAssumptions,
  onApply,
  onDiscard,
  isApplying,
}: ScenarioComparisonProps) {
  const { current, modified } = scenario;

  const assumptionChanges = diffScenarioAssumptions(currentAssumptions, scenarioAssumptions);
  const currentConsequences = computeDirectConsequences(currentAssumptions);
  const scenarioConsequences = computeDirectConsequences(scenarioAssumptions);

  const { strengthened, weakened, stillUnknown, newQuestions } = buildScenarioInsights(current, modified);

  return (
    <BaseCard className="space-y-5 border-primary/30 p-6">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Scenario Preview</h3>
        <p className="mt-1 text-sm text-text-secondary">
          This is a preview — your saved venture is unchanged until you apply it.
        </p>
      </div>

      {/* Part 10: "Do not bury the assumptions beneath the score." The
          actual before/after field values come first. */}
      {assumptionChanges.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What changed</p>
          <ul className="mt-2 space-y-1.5">
            {assumptionChanges.map((change) => (
              <li key={change.key} className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5 text-sm">
                <span className="text-text-secondary">{change.label}</span>
                <span className="font-medium text-text-primary">
                  {change.before} <span aria-hidden="true" className="text-text-muted">→</span> {change.after}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Part 8/9/21 (Simulate V1): Class A -- directly calculable
          consequences only, always framed as an "if/then" scenario
          calculation, never a prediction. */}
      {scenarioConsequences.length > 0 ? (
        <div className="border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Direct modeled consequences</p>
          <ul className="mt-2 space-y-2">
            {scenarioConsequences.map((consequence) => {
              const currentValue = currentConsequences.find((c) => c.key === consequence.key);
              return (
                <li key={consequence.key} className="text-base leading-7 text-text-secondary">
                  <span className="font-medium text-text-primary">{consequence.label}: </span>
                  {consequence.explanation}
                  {!currentValue ? (
                    <span className="block text-sm text-text-secondary">
                      (Not calculable for your current model — {currentAssumptions.economics.price_point === null
                        ? "no price is set yet"
                        : "no paying customers are set yet"}.)
                    </span>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {strengthened.length > 0 ? (
        <div className="border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What this would strengthen</p>
          <ul className="mt-2 space-y-2">
            {strengthened.map((change) => (
              <li key={change.key} className="text-sm leading-6 text-text-secondary">
                <span className="font-medium text-text-primary">{change.label}: </span>
                {change.reason}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {stillUnknown.length > 0 ? (
        <div className="border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What would still be unknown</p>
          <ul className="mt-2 space-y-1.5">
            {stillUnknown.map((item) => (
              <li key={item} className="text-sm leading-6 text-text-secondary">
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {weakened.length > 0 || newQuestions.length > 0 ? (
        <div className="border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">New questions / risks</p>
          <ul className="mt-2 space-y-2">
            {weakened.map((change) => (
              <li key={change.key} className="text-sm leading-6 text-text-secondary">
                <span className="font-medium text-text-primary">{change.label} may need re-examining: </span>
                {change.reason}
              </li>
            ))}
            {newQuestions.map((question) => (
              <li key={question} className="text-sm leading-6 text-text-secondary">
                {question}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {/* Part 8/9's core safety principle, stated plainly rather than
          computed per-scenario -- true of every scenario Simulate can
          run, not just this one. */}
      <div className="border-t border-border pt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What this doesn&rsquo;t predict</p>
        <p className="mt-1 text-xs leading-5 text-text-secondary">
          This preview shows the direct effects of the assumptions you changed — it does not predict how customers,
          competitors, or the market might respond (for example, whether a price change affects signups or churn),
          and it does not predict whether this venture will succeed.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
        <p className="text-xs text-text-muted">
          Applying will update your venture details and history.
        </p>
        <div className="flex items-center gap-2">
          <Button type="button" variant="subtle" onClick={onDiscard}>
            Discard
          </Button>
          <Button type="button" disabled={isApplying} onClick={onApply}>
            {isApplying ? "Applying..." : "Apply these assumptions to my venture"}
          </Button>
        </div>
      </div>
    </BaseCard>
  );
}
