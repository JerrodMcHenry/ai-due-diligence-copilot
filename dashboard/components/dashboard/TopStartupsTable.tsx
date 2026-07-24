import BaseCard from "@/components/ui/BaseCard";

import type { StartupRanking } from "@/types";

type TopStartupsTableProps = {
  startups: StartupRanking[];
};

function formatScore(value: number) {
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

function getScoreClasses(score: number) {
  if (score >= 80) {
    return "bg-success-soft text-success";
  }

  if (score >= 65) {
    return "bg-primary-soft text-primary";
  }

  if (score >= 50) {
    return "bg-warning-soft text-warning";
  }

  return "bg-danger-soft text-danger";
}

export default function TopStartupsTable({ startups }: TopStartupsTableProps) {
  return (
    <BaseCard className="overflow-hidden">
      <div className="flex flex-col gap-2 border-b border-border px-5 py-5 sm:px-6">
        <h2 className="text-lg font-semibold text-text-primary">
          Top startup power scores
        </h2>

        <p className="text-sm text-text-muted">
          Highest-ranked companies based on their latest SPS analysis.
        </p>
      </div>

      {startups.length === 0 ? (
        <div className="px-6 py-14 text-center">
          <p className="text-sm font-medium text-text-primary">
            No startup rankings available
          </p>

          <p className="mt-2 text-sm text-text-muted">
            Rankings will appear after startup analyses are completed.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-sm">
            <thead className="bg-surface-muted">
              <tr className="border-b border-border text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                <th scope="col" className="min-w-[240px] px-6 py-3.5">
                  Company
                </th>

                <th scope="col" className="min-w-[150px] px-6 py-3.5">
                  Industry
                </th>

                <th scope="col" className="px-6 py-3.5">
                  Stage
                </th>

                <th scope="col" className="px-6 py-3.5">
                  SPS
                </th>

                <th scope="col" className="px-6 py-3.5">
                  Readiness
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border">
              {startups.map((startup, index) => (
                <tr
                  key={`${startup.company_name}-${startup.stage}-${index}`}
                  className="transition-colors hover:bg-surface-muted"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-xs font-semibold text-primary">
                        {index + 1}
                      </span>

                      <span className="font-medium text-text-primary">
                        {startup.company_name}
                      </span>
                    </div>
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-text-secondary">
                    {startup.industry || "Not specified"}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-text-secondary">
                    {startup.stage || "Not specified"}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={[
                        "inline-flex min-w-12 justify-center rounded-full px-2.5 py-1 text-xs font-semibold",
                        getScoreClasses(startup.overall_score),
                      ].join(" ")}
                    >
                      {formatScore(startup.overall_score)}
                    </span>
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-text-secondary">
                    {formatScore(startup.readiness_score)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </BaseCard>
  );
}
