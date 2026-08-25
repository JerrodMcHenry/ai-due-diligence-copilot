import BaseCard from "@/components/ui/BaseCard";

import {
  computeEvidenceGaps,
  computeLeadershipGroups,
  computePillarLeadership,
  computeTiedPillars,
} from "@/lib/compareInsights";

import type { ComparisonStartup } from "@/types";

type KeyDifferencesPanelProps = {
  startups: ComparisonStartup[];
};

// Part 10: entirely deterministic, built from the same pillar scores
// PillarComparisonTable renders -- no LLM call, no inferred outcomes.
// Restrained language throughout ("leads on", never "will outperform").
export default function KeyDifferencesPanel({
  startups,
}: KeyDifferencesPanelProps) {
  const leadership = computePillarLeadership(startups);
  const groups = computeLeadershipGroups(startups, leadership).filter(
    (group) => group.leadsIn.length > 0
  );
  const tiedPillars = computeTiedPillars(leadership);
  const evidenceGaps = computeEvidenceGaps(leadership);

  const hasNothingToShow =
    groups.length === 0 && tiedPillars.length === 0 && evidenceGaps.length === 0;

  return (
    <section>
      <h2 className="text-xl font-semibold text-text-primary">
        Key Differences
      </h2>

      {hasNothingToShow ? (
        <BaseCard className="mt-4 p-5">
          <p className="text-sm text-text-secondary">
            These startups score within a point of each other on every
            pillar — there&rsquo;s no clear leader here based on SIE&rsquo;s
            current evidence.
          </p>
        </BaseCard>
      ) : (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {groups.map((group) => (
            <BaseCard key={group.startupId} className="p-5">
              <h3 className="text-sm font-semibold text-text-primary">
                {group.companyName} leads in:
              </h3>

              <ul className="mt-2 space-y-1.5 text-sm text-text-secondary">
                {group.leadsIn.map((entry) => (
                  <li key={entry.pillarLabel} className="flex items-baseline gap-1.5">
                    <span aria-hidden="true" className="text-success">
                      ▲
                    </span>
                    <span>
                      {entry.pillarLabel}{" "}
                      <span className="text-text-muted">
                        (+{entry.gap.toFixed(1)} pts)
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </BaseCard>
          ))}

          {tiedPillars.length > 0 ? (
            <BaseCard className="p-5">
              <h3 className="text-sm font-semibold text-text-primary">
                Approximately tied on:
              </h3>

              <ul className="mt-2 space-y-1.5 text-sm text-text-secondary">
                {tiedPillars.map((label) => (
                  <li key={label} className="flex items-baseline gap-1.5">
                    <span aria-hidden="true" className="text-primary">
                      ≈
                    </span>
                    <span>{label}</span>
                  </li>
                ))}
              </ul>
            </BaseCard>
          ) : null}

          {evidenceGaps.length > 0 ? (
            <BaseCard className="p-5">
              <h3 className="text-sm font-semibold text-text-primary">
                Evidence gaps:
              </h3>

              <ul className="mt-2 space-y-1.5 text-sm text-text-secondary">
                {evidenceGaps.map((gap) => (
                  <li key={gap.pillarLabel} className="flex items-baseline gap-1.5">
                    <span aria-hidden="true" className="text-warning">
                      !
                    </span>
                    <span>
                      {gap.pillarLabel} is unavailable for{" "}
                      {gap.companies.join(", ")}.
                    </span>
                  </li>
                ))}
              </ul>
            </BaseCard>
          ) : null}
        </div>
      )}
    </section>
  );
}
