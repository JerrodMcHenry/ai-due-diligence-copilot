import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import CategoryChangesList from "./CategoryChangesList";
import { categoryDeltaDirection, explainCategoryChanges, formatCategoryDelta } from "./categoryChangeExplain";

import type { ScenarioCompareResponse } from "@/types";

const DELTA_CLASSES = {
  positive: "text-movement-positive",
  negative: "text-movement-negative",
  neutral: "text-movement-neutral",
} as const;

type ScenarioComparisonProps = {
  scenario: ScenarioCompareResponse;
  onApply: () => void;
  onDiscard: () => void;
  isApplying: boolean;
};

// Part 9/11 (V1) + Phase 10.6 Part 7/8 (V2) + Phase 10.7 (shared "why"
// extraction). The core what-if loop, still backed by the exact same
// stateless POST /ventures/scenario-compare this component always used --
// "Apply" still hands off to the venture's own unchanged Save action,
// "Discard" still just clears local state. The "Why it changed" section
// (Part 8, V2) now shares its logic/presentation with the explicit
// validation-update flow (Part 10.7's MissionsSection) via
// categoryChangeExplain.ts/CategoryChangesList.tsx -- one implementation.
export default function ScenarioComparison({
  scenario,
  onApply,
  onDiscard,
  isApplying,
}: ScenarioComparisonProps) {
  const { current, modified } = scenario;

  const changedCategories = explainCategoryChanges(current.categories, modified.categories);

  return (
    <BaseCard className="space-y-5 border-primary/30 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-text-muted">
            Scenario Preview
          </h3>
          <p className="mt-1 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-text-primary">
              {current.vps !== null ? current.vps.toFixed(1) : "—"}
            </span>
            <span aria-hidden="true" className="text-text-muted">→</span>
            <span className="text-2xl font-bold text-text-primary">
              {modified.vps !== null ? modified.vps.toFixed(1) : "—"}
            </span>
            <span className={`text-sm font-semibold ${DELTA_CLASSES[categoryDeltaDirection(current.vps, modified.vps)]}`}>
              ({formatCategoryDelta(current.vps, modified.vps)})
            </span>
          </p>
          <p className="mt-1 text-xs text-text-muted">
            This is a preview — your saved venture is unchanged until you apply it.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button type="button" variant="subtle" onClick={onDiscard}>
            Discard
          </Button>
          <Button type="button" disabled={isApplying} onClick={onApply}>
            {isApplying ? "Saving..." : "Apply & Save"}
          </Button>
        </div>
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
    </BaseCard>
  );
}
