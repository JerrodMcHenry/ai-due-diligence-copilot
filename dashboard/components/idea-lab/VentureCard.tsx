import BaseCard from "@/components/ui/BaseCard";
import Badge from "@/components/ui/Badge";

import type { VPSCategoryResult } from "@/types";

// Phase 10.6 -- Idea Lab V2, Part 11. Visual architecture for a FUTURE
// shareable venture card -- NOT wired to any sharing, export, or public
// route. Nothing renders here that isn't already visible to the venture's
// own owner elsewhere in the workspace; this component exists only to
// show what a "something you'd send a friend" artifact could look like,
// so a later phase can wire a real Share action onto it once the privacy
// architecture in this phase's final report is actually built. The
// MODELED / ASSUMPTION-BASED disclaimer is structurally part of the card,
// never optional -- see the report's "Privacy/sharing decision" section
// for why this stays presentation-only in V2.
type VentureCardProps = {
  name: string;
  oneLineConcept: string | null;
  vps: number | null;
  categories: VPSCategoryResult[];
};

export default function VentureCard({ name, oneLineConcept, vps, categories }: VentureCardProps) {
  const topCategories = categories
    .filter((category) => category.score !== null)
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    .slice(0, 2);

  return (
    <BaseCard variant="raised" className="mx-auto max-w-sm overflow-hidden p-0">
      <div className="bg-gradient-to-br from-primary-soft to-surface p-6 text-center">
        <p className="truncate text-lg font-bold text-text-primary">{name}</p>
        {oneLineConcept ? (
          <p className="mt-1.5 text-sm leading-5 text-text-secondary">{oneLineConcept}</p>
        ) : null}

        <p className="mt-4 text-4xl font-bold text-primary">
          {vps !== null ? vps.toFixed(1) : "—"}
        </p>
        <p className="mt-1 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
          Modeled / assumption-based
        </p>
      </div>

      {topCategories.length > 0 ? (
        <div className="flex flex-wrap justify-center gap-2 border-t border-border p-4">
          {topCategories.map((category) => (
            <Badge key={category.key} tone="primary">
              {category.label}
            </Badge>
          ))}
        </div>
      ) : null}
    </BaseCard>
  );
}
