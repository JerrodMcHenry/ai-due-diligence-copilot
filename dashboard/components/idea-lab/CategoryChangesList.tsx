import { describeCategoryShift, type CategoryChange } from "./categoryChangeExplain";

// Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and Decision
// Support. No numeric delta ("+1.5", "newly scored") anywhere -- only
// describeCategoryShift()'s plain-word description of what kind of change
// this was, still derived from the exact same category score data.
const SHIFT_CLASSES: Record<string, string> = {
  strengthened: "text-movement-positive",
  weakened: "text-movement-negative",
  "now modeled": "text-movement-neutral",
  "no longer modeled": "text-movement-neutral",
};

// Phase 10.7 -- shared "Why it changed" presentation for both a scenario
// preview (ScenarioComparison) and a real, saved explicit model update
// (MissionsSection) -- one visual treatment, not two. Every line comes
// from categoryChangeExplain.ts's own extraction of vps_scoring.py's
// `basis` field; nothing here is generated.
type CategoryChangesListProps = {
  changes: CategoryChange[];
  heading?: string;
};

export default function CategoryChangesList({ changes, heading = "Why it changed" }: CategoryChangesListProps) {
  if (changes.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{heading}</p>

      {changes.map((change) => {
        // Up to 2 basis lines -- enough to explain the movement without
        // reprinting the scorer's entire internal reasoning.
        const reasons = change.basis.slice(0, 2);
        const shift = describeCategoryShift(change.fromScore, change.toScore);

        return (
          <div key={change.key} className="rounded-lg bg-surface-subtle p-3">
            <p className="text-sm font-semibold text-text-primary">
              {change.label.toUpperCase()}
              {shift ? <span className={`ml-1 ${SHIFT_CLASSES[shift]}`}>{shift}</span> : null}
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
      })}
    </div>
  );
}
