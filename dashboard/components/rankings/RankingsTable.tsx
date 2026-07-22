import Link from "next/link";

import type { RankingEntry } from "@/types";

type RankingsTableProps = {
  rankings: RankingEntry[];
};

function formatScore(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

export default function RankingsTable({ rankings }: RankingsTableProps) {
  if (rankings.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 px-6 py-12 text-center">
        <p className="font-medium text-slate-300">No ranking data available</p>

        <p className="mt-1 text-sm text-slate-500">
          Rankings will appear after startup analyses have been completed.
        </p>
      </div>
    );
  }

  return (
    <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-sm">
          <thead className="bg-slate-950/50">
            <tr className="border-b border-slate-800 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              <th scope="col" className="w-20 px-6 py-3">
                Rank
              </th>

              <th scope="col" className="min-w-[240px] px-6 py-3">
                Company
              </th>

              <th scope="col" className="min-w-[160px] px-6 py-3">
                Industry
              </th>

              <th scope="col" className="min-w-[120px] px-6 py-3">
                Stage
              </th>

              <th scope="col" className="whitespace-nowrap px-6 py-3">
                Business Model
              </th>

              <th scope="col" className="whitespace-nowrap px-6 py-3">
                Overall Score
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-800">
            {rankings.map((startup, index) => {
              const companyName = startup.company_name ?? "Unknown Startup";

              return (
                <tr
                  key={startup.id}
                  className="transition-colors hover:bg-slate-800/40"
                >
                  <td className="whitespace-nowrap px-6 py-4 font-semibold text-slate-500">
                    #{index + 1}
                  </td>

                  <td className="px-6 py-4">
                    <Link
                      href={`/startup/${encodeURIComponent(companyName)}`}
                      className="font-medium text-white transition-colors hover:text-blue-300"
                    >
                      {companyName}
                    </Link>
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                    {startup.industry ?? "--"}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                    {startup.stage ?? "--"}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4 text-slate-300">
                    {startup.business_model ?? "--"}
                  </td>

                  <td className="whitespace-nowrap px-6 py-4">
                    <span className="inline-flex rounded-full bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-300">
                      {formatScore(startup.overall_score)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
