import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

import type { ScenarioCompareResponse, VPSCategoryResult } from "@/types";

function formatDelta(from: number | null, to: number | null): string {
  if (from === null && to !== null) {
    return "newly scored";
  }
  if (from !== null && to === null) {
    return "no longer scored";
  }
  if (from === null || to === null) {
    return "";
  }
  const delta = to - from;
  if (Math.abs(delta) < 0.05) {
    return "no meaningful change";
  }
  return delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1);
}

function deltaColorClass(from: number | null, to: number | null): string {
  if (from === null || to === null || Math.abs(to - from) < 0.05) {
    return "text-movement-neutral";
  }
  return to > from ? "text-movement-positive" : "text-movement-negative";
}

// A category moving from Unavailable (null) to scored -- or the reverse --
// is itself a meaningful, explainable change (often the actual reason the
// overall VPS moved, since compute_vps() renormalizes around whichever
// categories are scored -- see that function's own docstring). Not just a
// same-to-same numeric delta.
function hasMeaningfulChange(from: number | null, to: number | null): boolean {
  if (from === null && to === null) {
    return false;
  }
  if (from === null || to === null) {
    return true;
  }
  return Math.abs(to - from) >= 0.05;
}

type ScenarioComparisonProps = {
  scenario: ScenarioCompareResponse;
  onApply: () => void;
  onDiscard: () => void;
  isApplying: boolean;
};

// Part 9/11 (V1) + Phase 10.6 Part 7/8 (V2). The core what-if loop, still
// backed by the exact same stateless POST /ventures/scenario-compare this
// component always used -- "Apply" still hands off to the venture's own
// unchanged Save action, "Discard" still just clears local state. New in
// this phase: a WHY per changed category (Part 8), built entirely from
// `basis` -- a field vps_scoring.py's CategoryResult has always returned,
// this component simply didn't render it before. Nothing here is
// generated or inferred; every explanation line is a basis string the
// backend's own deterministic scorer already produced for the modified
// scenario.
export default function ScenarioComparison({
  scenario,
  onApply,
  onDiscard,
  isApplying,
}: ScenarioComparisonProps) {
  const { current, modified } = scenario;

  const changedCategories = modified.categories.filter((modifiedCategory) => {
    const currentCategory = current.categories.find((c) => c.key === modifiedCategory.key);
    return hasMeaningfulChange(currentCategory?.score ?? null, modifiedCategory.score);
  });

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
            <span className={`text-sm font-semibold ${deltaColorClass(current.vps, modified.vps)}`}>
              ({formatDelta(current.vps, modified.vps)})
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
        <div className="space-y-3 border-t border-border pt-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Why it changed
          </p>

          {changedCategories.map((modifiedCategory) => {
            const currentCategory = current.categories.find((c) => c.key === modifiedCategory.key);
            const delta = formatDelta(currentCategory?.score ?? null, modifiedCategory.score);

            return (
              <CategoryReasonRow
                key={modifiedCategory.key}
                label={modifiedCategory.label}
                delta={delta}
                deltaClass={deltaColorClass(currentCategory?.score ?? null, modifiedCategory.score)}
                basis={modifiedCategory.basis}
              />
            );
          })}
        </div>
      ) : null}

      <div className="grid gap-3 border-t border-border pt-4 sm:grid-cols-2 lg:grid-cols-3">
        {modified.categories.map((modifiedCategory) => {
          const currentCategory = current.categories.find((c) => c.key === modifiedCategory.key);
          const delta = formatDelta(currentCategory?.score ?? null, modifiedCategory.score);

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
                  <span className={`text-xs font-semibold ${deltaColorClass(currentCategory?.score ?? null, modifiedCategory.score)}`}>
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

function CategoryReasonRow({
  label,
  delta,
  deltaClass,
  basis,
}: {
  label: string;
  delta: string;
  deltaClass: string;
  basis: VPSCategoryResult["basis"];
}) {
  // Up to 2 basis lines -- enough to explain the movement without
  // reprinting the scorer's entire internal reasoning (Part 8: the
  // explanation matters more than the number, but it should still read
  // as a short, human sentence, not a debug dump).
  const reasons = basis.slice(0, 2);

  return (
    <div className="rounded-lg bg-surface-subtle p-3">
      <p className="text-sm font-semibold text-text-primary">
        {label.toUpperCase()}{" "}
        <span className={deltaClass}>{delta}</span>
      </p>
      {reasons.length > 0 ? (
        <ul className="mt-1 space-y-0.5">
          {reasons.map((reason) => (
            <li key={reason} className="text-xs leading-5 text-text-secondary">
              {reason}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
