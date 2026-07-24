import BaseCard from "@/components/ui/BaseCard";

import type { ImprovingStartup } from "@/types";

type TopImprovingStartupsTableProps = {
  startups: ImprovingStartup[];
};

function formatScore(value: number) {
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

export default function TopImprovingStartupsTable({
  startups,
}: TopImprovingStartupsTableProps) {
  return (
    <BaseCard className="overflow-hidden">
      <div className="flex flex-col gap-2 border-b border-border px-5 py-5 sm:px-6">
        <h2 className="text-lg font-semibold text-text-primary">
          Fastest improving startups
        </h2>

        <p className="text-sm text-text-muted">
          Companies with the largest increase in Startup Power Score.
        </p>
      </div>

      {startups.length === 0 ? (
        <div className="px-6 py-14 text-center">
          <p className="text-sm font-medium text-text-primary">
            No improvement data available
          </p>

          <p className="mt-2 text-sm text-text-muted">
            Score movement will appear after startups receive multiple analyses.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[700px] text-sm">
            <thead className="bg-surface-muted">
              <tr className="border-b border-border text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                <th scope="col" className="min-w-[240px] px-6 py-3.5">
                  Company
                </th>

                <th scope="col" className="px-6 py-3.5">
                  Previous SPS
                </th>

                <th scope="col" className="px-6 py-3.5">
                  Current SPS
                </th>

                <th scope="col" className="px-6 py-3.5">
                  Change
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border">
              {startups.map((startup, index) => {
                const isPositive = startup.score_change > 0;
                const isNegative = startup.score_change < 0;

                return (
                  <tr
                    key={`${startup.company_name}-${startup.first_score}-${startup.latest_score}-${index}`}
                    className="transition-colors hover:bg-surface-muted"
                  >
                    <td className="px-6 py-4 font-medium text-text-primary">
                      {startup.company_name}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 text-text-secondary">
                      {formatScore(startup.first_score)}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 font-medium text-text-primary">
                      {formatScore(startup.latest_score)}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={[
                          "inline-flex min-w-14 justify-center rounded-full px-2.5 py-1 text-xs font-semibold",
                          isPositive
                            ? "bg-success-soft text-success"
                            : isNegative
                            ? "bg-danger-soft text-danger"
                            : "bg-surface-muted text-text-secondary",
                        ].join(" ")}
                      >
                        {isPositive ? "+" : ""}
                        {formatScore(startup.score_change)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </BaseCard>
  );
}
