import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import CategoryChangesList from "./CategoryChangesList";
import { categoryDeltaDirection, explainCategoryChanges, formatCategoryDelta } from "./categoryChangeExplain";
import { diffScenarioAssumptions } from "@/lib/simulate/assumptionDiff";
import { computeDirectConsequences } from "@/lib/simulate/directConsequences";

import type { ScenarioCompareResponse, VentureAssumptions } from "@/types";

const DELTA_CLASSES = {
  positive: "text-movement-positive",
  negative: "text-movement-negative",
  neutral: "text-movement-neutral",
} as const;

type ScenarioComparisonProps = {
  scenario: ScenarioCompareResponse;
  // Simulate V1, Part 5/10: the raw before/after assumption VALUES, not
  // just the resulting VPSResult -- ScenarioCompareResponse never carried
  // these (it's stateless VPS-only, computed twice), so the caller
  // (VentureWorkspace.tsx) now passes its own already-in-hand
  // venture.assumptions / draft alongside the existing `scenario` prop.
  // Nothing new is fetched; this is purely additive.
  currentAssumptions: VentureAssumptions;
  scenarioAssumptions: VentureAssumptions;
  onApply: () => void;
  onDiscard: () => void;
  isApplying: boolean;
};

// Part 9/11 (V1) + Phase 10.6 Part 7/8 (V2) + Phase 10.7 (shared "why"
// extraction) + Simulate V1 (Part 5/8/9/10/11/12: assumption diff, direct
// modeled consequences, honest "what this doesn't predict," reordered
// hierarchy, explicit Apply copy). Still backed by the exact same
// stateless POST /ventures/scenario-compare this component always used --
// "Apply" still hands off to the venture's own unchanged Save action,
// "Discard" still just clears local state. The "Why it changed" section
// shares its logic/presentation with the explicit validation-update flow
// (MissionsSection) via categoryChangeExplain.ts/CategoryChangesList.tsx
// -- one implementation.
export default function ScenarioComparison({
  scenario,
  currentAssumptions,
  scenarioAssumptions,
  onApply,
  onDiscard,
  isApplying,
}: ScenarioComparisonProps) {
  const { current, modified } = scenario;

  const changedCategories = explainCategoryChanges(current.categories, modified.categories);
  const assumptionChanges = diffScenarioAssumptions(currentAssumptions, scenarioAssumptions);
  const currentConsequences = computeDirectConsequences(currentAssumptions);
  const scenarioConsequences = computeDirectConsequences(scenarioAssumptions);

  const vpsDirection = categoryDeltaDirection(current.vps, modified.vps);

  return (
    <BaseCard className="space-y-5 border-primary/30 p-6">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Scenario Preview</h3>
        <p className="mt-1 text-xs text-text-muted">
          This is a preview — your saved venture is unchanged until you apply it.
        </p>
      </div>

      {/* Part 10: "Do not bury the assumptions beneath the score." The
          actual before/after field values come first, before any score. */}
      {assumptionChanges.length > 0 ? (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Key assumption changes</p>
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

      {/* Part 8/9/21: Class A -- directly calculable consequences only,
          always framed as an "if/then" scenario calculation, never a
          prediction. Renders nothing when price x paying_customers isn't
          a valid calculation for either side (Part 8: "If validity
          cannot be established, do not calculate it"). */}
      {scenarioConsequences.length > 0 ? (
        <div className="border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Direct modeled consequences</p>
          <ul className="mt-2 space-y-2">
            {scenarioConsequences.map((consequence) => {
              const currentValue = currentConsequences.find((c) => c.key === consequence.key);
              return (
                <li key={consequence.key} className="text-sm leading-6 text-text-secondary">
                  <span className="font-medium text-text-primary">{consequence.label}: </span>
                  {consequence.explanation}
                  {!currentValue ? (
                    <span className="block text-xs text-text-muted">
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

      {/* Part 11: "VPS change is ONE consequence. It is not the
          objective of Simulate." Plain-fact framing, no "increase your
          score" language, no internal formula. */}
      <div className="border-t border-border pt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">Venture Potential Score</p>
        <p className="mt-1 flex items-baseline gap-2">
          <span className="text-2xl font-bold text-text-primary">
            {current.vps !== null ? current.vps.toFixed(1) : "—"}
          </span>
          <span aria-hidden="true" className="text-text-muted">→</span>
          <span className="text-2xl font-bold text-text-primary">
            {modified.vps !== null ? modified.vps.toFixed(1) : "—"}
          </span>
          <span className={`text-sm font-semibold ${DELTA_CLASSES[vpsDirection]}`}>
            ({formatCategoryDelta(current.vps, modified.vps)})
          </span>
        </p>
        <p className="mt-1 text-xs text-text-muted">
          Under these assumptions, Venture Potential Score would change as shown above — this reflects the frozen,
          unchanged scoring methodology, not a new prediction.
        </p>
      </div>

      {changedCategories.length > 0 ? (
        <div className="border-t border-border pt-4">
          <CategoryChangesList changes={changedCategories} />
        </div>
      ) : null}

      <div className="grid gap-3 border-t border-border pt-4 sm:grid-cols-2 lg:grid-cols-3">
        {modified.categories.map((modifiedCategory) => {
          const currentCategory = current.categories.find((c) => c.key === modifiedCategory.key);
          const delta = formatCategoryDelta(currentCategory?.score ?? null, modifiedCategory.score);

          return (
            <div key={modifiedCategory.key} className="rounded-lg border border-border bg-surface p-3">
              <p className="text-xs font-medium text-text-muted">{modifiedCategory.label}</p>
              <p className="mt-1 flex items-baseline gap-1.5 text-sm">
                <span className="text-text-secondary">
                  {currentCategory?.score !== null && currentCategory?.score !== undefined
                    ? currentCategory.score.toFixed(1)
                    : "—"}
                </span>
                <span aria-hidden="true" className="text-text-muted">→</span>
                <span className="font-semibold text-text-primary">
                  {modifiedCategory.score !== null ? modifiedCategory.score.toFixed(1) : "—"}
                </span>
                {delta && delta !== "no meaningful change" ? (
                  <span className={`text-xs font-semibold ${DELTA_CLASSES[categoryDeltaDirection(currentCategory?.score ?? null, modifiedCategory.score)]}`}>
                    ({delta})
                  </span>
                ) : null}
              </p>
            </div>
          );
        })}
      </div>

      {/* Part 8/9's core safety principle, stated plainly rather than
          computed per-scenario -- true of every scenario Simulate can
          run, not just this one. */}
      <div className="border-t border-border pt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What this doesn&rsquo;t predict</p>
        <p className="mt-1 text-xs leading-5 text-text-secondary">
          This preview shows the direct effects of the assumptions you changed — it does not predict how customers,
          competitors, or the market might respond (for example, whether a price change affects signups or churn).
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
        <p className="text-xs text-text-muted">
          Applying will update your venture model. Your score and venture history may change.
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
