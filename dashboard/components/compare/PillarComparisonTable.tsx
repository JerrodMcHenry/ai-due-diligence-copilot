import BaseCard from "@/components/ui/BaseCard";

import { computePillarLeadership } from "@/lib/compareInsights";
import { gridColsClass } from "./gridCols";

import type { ComparisonStartup } from "@/types";

type PillarComparisonTableProps = {
  startups: ComparisonStartup[];
};

function scoreBarWidth(score: number): string {
  return `${Math.max(0, Math.min(100, (score / 10) * 100))}%`;
}

// Part 16: deliberately NOT a wide table with one column per startup and
// horizontal scroll -- each pillar is its own section, and each
// startup's value within it stacks in a single column on mobile
// (grid-cols-1) and lays out side-by-side from sm: up (gridColsClass),
// same responsive pattern as the rest of the app.
export default function PillarComparisonTable({
  startups,
}: PillarComparisonTableProps) {
  const leadership = computePillarLeadership(startups);

  return (
    <section>
      <h2 className="text-xl font-semibold text-text-primary">
        Pillar Comparison
      </h2>

      <div className="mt-4 space-y-4">
        {leadership.map((pillarInfo) => (
          <BaseCard key={pillarInfo.pillarKey} className="p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-text-muted">
              {pillarInfo.pillarLabel}
            </h3>

            {pillarInfo.unavailableForAll ? (
              <p className="mt-3 text-sm text-text-muted">
                Unavailable for every selected startup.
              </p>
            ) : (
              <dl className={`mt-3 grid gap-3 ${gridColsClass(startups.length)}`}>
                {startups.map((startup) => {
                  const score = startup[pillarInfo.pillarKey].score;
                  const isLeader =
                    // Part 9: a leader is marked by both a label AND the
                    // score itself -- never color alone. A tie (>1
                    // leader) marks nobody as sole leader.
                    pillarInfo.leaders.length === 1 &&
                    pillarInfo.leaders[0].startupId === startup.startup_id;
                  const isTied =
                    pillarInfo.leaders.length > 1 &&
                    pillarInfo.leaders.some(
                      (leader) => leader.startupId === startup.startup_id
                    );

                  return (
                    <div key={startup.startup_id}>
                      <dt className="flex items-center justify-between gap-2 text-xs text-text-muted">
                        <span className="truncate">{startup.company_name}</span>

                        {isLeader ? (
                          <span className="shrink-0 rounded-full bg-success-soft px-2 py-0.5 text-[10px] font-semibold text-success">
                            Leads
                          </span>
                        ) : isTied ? (
                          <span className="shrink-0 rounded-full bg-primary-soft px-2 py-0.5 text-[10px] font-semibold text-primary">
                            Tied
                          </span>
                        ) : null}
                      </dt>

                      <dd className="mt-1 flex items-center gap-2">
                        <span className="w-10 shrink-0 text-sm font-semibold text-text-primary">
                          {score !== null ? score.toFixed(1) : "—"}
                        </span>

                        <span className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted">
                          {score !== null ? (
                            <span
                              className={[
                                "block h-full rounded-full",
                                isLeader ? "bg-success" : "bg-primary/60",
                              ].join(" ")}
                              style={{ width: scoreBarWidth(score) }}
                            />
                          ) : null}
                        </span>
                      </dd>

                      {score === null ? (
                        <p className="mt-1 text-[11px] text-text-muted">
                          Unavailable — no scoreable evidence
                        </p>
                      ) : null}
                    </div>
                  );
                })}
              </dl>
            )}
          </BaseCard>
        ))}
      </div>
    </section>
  );
}
