type Startup = {
  company_name: string;
  industry: string;
  stage: string;
  overall_score: number;
  readiness_score: number;
};

type TopStartupsTableProps = {
  startups: Startup[];
};

function formatScore(value: number) {
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

export default function TopStartupsTable({ startups }: TopStartupsTableProps) {
  return (
    <section className="mt-10 overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="border-b border-slate-800 px-5 py-5 sm:px-6">
        <h2 className="text-lg font-semibold text-white sm:text-xl">
          Top Startups
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Highest-ranked companies based on their latest intelligence score.
        </p>
      </div>

      {startups.length === 0 ? (
        <div className="px-6 py-12 text-center">
          <p className="text-sm font-medium text-slate-300">
            No startup rankings available
          </p>

          <p className="mt-1 text-sm text-slate-500">
            Ranked startups will appear after analyses have been completed.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-sm">
            <thead className="bg-slate-950/50">
              <tr className="border-b border-slate-800 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                <th scope="col" className="min-w-[220px] px-6 py-3">
                  Company
                </th>

                <th scope="col" className="min-w-[160px] px-6 py-3">
                  Industry
                </th>

                <th scope="col" className="whitespace-nowrap px-6 py-3">
                  Stage
                </th>

                <th scope="col" className="whitespace-nowrap px-6 py-3">
                  Overall Score
                </th>

                <th scope="col" className="whitespace-nowrap px-6 py-3">
                  Readiness
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800">
              {startups.map((startup) => (
                <tr
                  key={`${startup.company_name}-${startup.stage}`}
                  className="transition-colors hover:bg-slate-800/40"
                >
                  <td className="whitespace-nowrap px-6 py-4 font-medium text-white">
                    {startup.company_name}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                    {startup.industry}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                    {startup.stage}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4">
                    <span className="inline-flex rounded-full bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-300">
                      {formatScore(startup.overall_score)}
                    </span>
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                    {formatScore(startup.readiness_score)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
