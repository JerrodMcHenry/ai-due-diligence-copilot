import BaseCard from "@/components/ui/BaseCard";

import type { ScenarioCompareResponse } from "@/types";

function formatDelta(from: number | null, to: number | null): string {
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
    return "text-text-muted";
  }
  return to > from ? "text-success" : "text-danger";
}

type ScenarioComparisonProps = {
  scenario: ScenarioCompareResponse;
  onApply: () => void;
  onDiscard: () => void;
  isApplying: boolean;
};

// Part 9/11: the core what-if loop. Never overwrites the venture's saved
// state on its own -- this is a PREVIEW (see VentureWorkspace's own
// handling: this component's data comes from POST /ventures/
// scenario-compare, a stateless endpoint that never writes to the
// venture). "Apply" explicitly hands off to the venture's own Save
// action; "Discard" just clears the preview.
export default function ScenarioComparison({
  scenario,
  onApply,
  onDiscard,
  isApplying,
}: ScenarioComparisonProps) {
  const { current, modified } = scenario;

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
          <button
            type="button"
            onClick={onDiscard}
            className="rounded-lg px-3 py-2 text-sm font-semibold text-text-muted transition-colors hover:text-danger"
          >
            Discard
          </button>
          <button
            type="button"
            disabled={isApplying}
            onClick={onApply}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isApplying ? "Saving..." : "Apply & Save"}
          </button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
