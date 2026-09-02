// Phase 21B, Part 12/40. A stacked ownership-composition bar. The
// ACCESSIBLE representation is the text list every row already renders
// (name + percentage) -- the colored bar segments beneath it are purely
// decorative reinforcement (aria-hidden), so ownership is never conveyed
// by color alone, and the component works identically for a screen-reader
// user, a color-blind user, or someone skimming visually.
import type { OwnershipRow } from "@/lib/fundraisingUi/types";

// A small, fixed palette cycled by row index -- not tied to stakeholder
// role, since a scenario can have an arbitrary number of stakeholders.
// Chosen from existing design tokens (Badge.tsx's own tone palette) so
// this never introduces one-off colors outside the design system.
const SEGMENT_CLASSES = [
  "bg-primary",
  "bg-success",
  "bg-info",
  "bg-warning",
  "bg-danger",
  "bg-text-muted",
];

type OwnershipBarProps = {
  title: string;
  rows: OwnershipRow[];
  percentField: "beforePercent" | "afterPercent";
};

function parsePercent(value: string): number {
  const n = Number.parseFloat(value.replace("%", ""));
  return Number.isFinite(n) ? n : 0;
}

export default function OwnershipBar({ title, rows, percentField }: OwnershipBarProps) {
  const visibleRows = rows.filter((r) => r[percentField] !== "—");

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">{title}</p>

      <div aria-hidden="true" className="mt-2 flex h-4 w-full overflow-hidden rounded-full bg-border">
        {visibleRows.map((row, i) => {
          const width = parsePercent(row[percentField]);
          if (width <= 0) return null;
          return <div key={row.id} className={SEGMENT_CLASSES[i % SEGMENT_CLASSES.length]} style={{ width: `${width}%` }} />;
        })}
      </div>

      <ul className="mt-2 space-y-1">
        {visibleRows.map((row, i) => (
          <li key={row.id} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex min-w-0 items-center gap-2 text-text-secondary">
              <span aria-hidden="true" className={["size-2.5 shrink-0 rounded-full", SEGMENT_CLASSES[i % SEGMENT_CLASSES.length]].join(" ")} />
              <span className="truncate">{row.name}</span>
            </span>
            <span className="shrink-0 font-semibold text-text-primary">{row[percentField]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
