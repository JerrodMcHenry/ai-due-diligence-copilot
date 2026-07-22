type ImprovingStartup = {
  company_name: string;
  first_score: number;
  latest_score: number;
  score_change: number;
};

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
    <section className="mt-10 overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="border-b border-slate-800 px-5 py-5 sm:px-6">
        <h2 className="text-lg font-semibold text-white sm:text-xl">
          Top Improving Startups
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Companies with the largest increase in intelligence score.
        </p>
      </div>

      {startups.length === 0 ? (
        <div className="px-6 py-12 text-center">
          <p className="text-sm font-medium text-slate-300">
            No improvement data available
          </p>

          <p className="mt-1 text-sm text-slate-500">
            Score changes will appear after startups have multiple analyses.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-[700px] w-full text-sm">
            <thead className="bg-slate-950/50">
              <tr className="border-b border-slate-800 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                <th scope="col" className="min-w-[220px] px-6 py-3">
                  Company
                </th>

                <th scope="col" className="whitespace-nowrap px-6 py-3">
                  First Score
                </th>

                <th scope="col" className="whitespace-nowrap px-6 py-3">
                  Latest Score
                </th>

                <th scope="col" className="whitespace-nowrap px-6 py-3">
                  Score Change
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800">
              {startups.map((startup) => {
                const isPositive = startup.score_change > 0;
                const isNegative = startup.score_change < 0;

                return (
                  <tr
                    key={`${startup.company_name}-${startup.first_score}-${startup.latest_score}`}
                    className="transition-colors hover:bg-slate-800/40"
                  >
                    <td className="whitespace-nowrap px-6 py-4 font-medium text-white">
                      {startup.company_name}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                      {formatScore(startup.first_score)}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                      {formatScore(startup.latest_score)}
                    </td>

                    <td className="whitespace-nowrap px-6 py-4">
                      <span
                        className={[
                          "inline-flex rounded-full px-2.5 py-1 text-xs font-semibold",
                          isPositive
                            ? "bg-emerald-500/10 text-emerald-400"
                            : isNegative
                            ? "bg-red-500/10 text-red-400"
                            : "bg-slate-700/50 text-slate-300",
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
    </section>
  );
}
