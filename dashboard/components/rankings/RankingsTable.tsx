"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { RankingEntry } from "@/types";

type RankingsTableProps = {
  rankings: RankingEntry[];
};

type SortOption = "score-desc" | "score-asc" | "company-asc" | "newest";

function formatScore(value: number | null | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "--";
  }

  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

function getScoreClasses(score: number | null | undefined) {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return "border-slate-700 bg-slate-800 text-slate-400";
  }

  if (score >= 80) {
    return "border-emerald-400/25 bg-emerald-400/10 text-emerald-300 shadow-[0_0_20px_rgba(52,211,153,0.08)]";
  }

  if (score >= 65) {
    return "border-cyan-400/25 bg-cyan-400/10 text-cyan-300 shadow-[0_0_20px_rgba(34,211,238,0.08)]";
  }

  if (score >= 50) {
    return "border-amber-400/25 bg-amber-400/10 text-amber-300";
  }

  return "border-rose-400/25 bg-rose-400/10 text-rose-300";
}

function getRankClasses(rank: number) {
  if (rank === 1) {
    return "border-amber-300/30 bg-amber-300/10 text-amber-200";
  }

  if (rank === 2) {
    return "border-slate-300/25 bg-slate-300/10 text-slate-200";
  }

  if (rank === 3) {
    return "border-orange-400/25 bg-orange-400/10 text-orange-300";
  }

  return "border-slate-700/80 bg-slate-800/70 text-slate-400";
}

function getInitials(companyName: string) {
  const words = companyName.trim().split(/\s+/).filter(Boolean);

  if (words.length === 0) {
    return "?";
  }

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0]}${words[1][0]}`.toUpperCase();
}

function MetadataBadge({ value }: { value: string | null | undefined }) {
  const displayValue = value?.trim() || "--";

  return (
    <span className="inline-flex max-w-[190px] truncate rounded-full border border-slate-700/80 bg-slate-800/70 px-3 py-1.5 text-[13px] font-medium text-slate-300">
      {displayValue}
    </span>
  );
}

function StatCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70 p-5 shadow-xl shadow-black/10 backdrop-blur">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-400/70 to-transparent" />

      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
        {value}
      </p>

      <p className="mt-1 text-sm text-slate-500">{detail}</p>
    </div>
  );
}

export default function RankingsTable({ rankings }: RankingsTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [industryFilter, setIndustryFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");
  const [sortOption, setSortOption] = useState<SortOption>("score-desc");

  const industries = useMemo(() => {
    return Array.from(
      new Set(
        rankings
          .map((startup) => startup.industry?.trim())
          .filter((industry): industry is string => Boolean(industry))
      )
    ).sort((a, b) => a.localeCompare(b));
  }, [rankings]);

  const stages = useMemo(() => {
    return Array.from(
      new Set(
        rankings
          .map((startup) => startup.stage?.trim())
          .filter((stage): stage is string => Boolean(stage))
      )
    ).sort((a, b) => a.localeCompare(b));
  }, [rankings]);

  const scoredStartups = useMemo(() => {
    return rankings.filter(
      (startup) =>
        typeof startup.overall_score === "number" &&
        !Number.isNaN(startup.overall_score)
    );
  }, [rankings]);

  const averageScore =
    scoredStartups.length > 0
      ? scoredStartups.reduce(
          (total, startup) => total + (startup.overall_score ?? 0),
          0
        ) / scoredStartups.length
      : null;

  const topScore =
    scoredStartups.length > 0
      ? Math.max(...scoredStartups.map((startup) => startup.overall_score ?? 0))
      : null;

  const filteredRankings = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    const filtered = rankings.filter((startup) => {
      const companyName = startup.company_name?.toLowerCase() ?? "";
      const industry = startup.industry?.trim() ?? "";
      const stage = startup.stage?.trim() ?? "";

      const matchesSearch =
        normalizedQuery.length === 0 || companyName.includes(normalizedQuery);

      const matchesIndustry =
        industryFilter === "all" || industry === industryFilter;

      const matchesStage = stageFilter === "all" || stage === stageFilter;

      return matchesSearch && matchesIndustry && matchesStage;
    });

    return [...filtered].sort((a, b) => {
      if (sortOption === "score-asc") {
        return (a.overall_score ?? -1) - (b.overall_score ?? -1);
      }

      if (sortOption === "company-asc") {
        return (a.company_name ?? "").localeCompare(b.company_name ?? "");
      }

      if (sortOption === "newest") {
        return (
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      }

      return (b.overall_score ?? -1) - (a.overall_score ?? -1);
    });
  }, [rankings, searchQuery, industryFilter, stageFilter, sortOption]);

  if (rankings.length === 0) {
    return (
      <div className="rounded-2xl border border-white/10 bg-slate-900/70 px-6 py-16 text-center shadow-xl shadow-black/20 backdrop-blur">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/10 to-indigo-500/10 text-lg font-semibold text-cyan-300">
          SI
        </div>

        <p className="mt-5 text-lg font-semibold text-slate-100">
          No ranking data available
        </p>

        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
          Rankings will appear after startup analyses have been completed.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard
          label="Ranked startups"
          value={rankings.length.toString()}
          detail="Companies with completed analyses"
        />

        <StatCard
          label="Average score"
          value={formatScore(averageScore)}
          detail="Across the current rankings"
        />

        <StatCard
          label="Top score"
          value={formatScore(topScore)}
          detail="Highest current intelligence score"
        />
      </section>

      <section className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70 shadow-2xl shadow-black/20 backdrop-blur">
        <div className="border-b border-white/10 bg-gradient-to-r from-indigo-500/[0.08] via-cyan-500/[0.04] to-fuchsia-500/[0.06] p-4 sm:p-5">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(260px,1fr)_190px_180px_190px]">
            <div className="relative">
              <label htmlFor="ranking-search" className="sr-only">
                Search companies
              </label>

              <span
                aria-hidden="true"
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-base text-slate-500"
              >
                ⌕
              </span>

              <input
                id="ranking-search"
                type="search"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search companies..."
                className="h-11 w-full rounded-xl border border-slate-700/80 bg-slate-950/70 pl-10 pr-4 text-[15px] text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-400/50 focus:ring-4 focus:ring-cyan-400/10"
              />
            </div>

            <label>
              <span className="sr-only">Filter by industry</span>

              <select
                value={industryFilter}
                onChange={(event) => setIndustryFilter(event.target.value)}
                className="h-11 w-full rounded-xl border border-slate-700/80 bg-slate-950/70 px-3 text-[15px] text-slate-300 outline-none transition focus:border-cyan-400/50 focus:ring-4 focus:ring-cyan-400/10"
              >
                <option value="all">All industries</option>

                {industries.map((industry) => (
                  <option key={industry} value={industry}>
                    {industry}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span className="sr-only">Filter by stage</span>

              <select
                value={stageFilter}
                onChange={(event) => setStageFilter(event.target.value)}
                className="h-11 w-full rounded-xl border border-slate-700/80 bg-slate-950/70 px-3 text-[15px] text-slate-300 outline-none transition focus:border-cyan-400/50 focus:ring-4 focus:ring-cyan-400/10"
              >
                <option value="all">All stages</option>

                {stages.map((stage) => (
                  <option key={stage} value={stage}>
                    {stage}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span className="sr-only">Sort rankings</span>

              <select
                value={sortOption}
                onChange={(event) =>
                  setSortOption(event.target.value as SortOption)
                }
                className="h-11 w-full rounded-xl border border-slate-700/80 bg-slate-950/70 px-3 text-[15px] text-slate-300 outline-none transition focus:border-cyan-400/50 focus:ring-4 focus:ring-cyan-400/10"
              >
                <option value="score-desc">Score: highest first</option>
                <option value="score-asc">Score: lowest first</option>
                <option value="company-asc">Company: A–Z</option>
                <option value="newest">Most recently analyzed</option>
              </select>
            </label>
          </div>

          <p className="mt-3 text-sm text-slate-500">
            Showing {filteredRankings.length} of {rankings.length} startups
          </p>
        </div>

        {filteredRankings.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-lg font-semibold text-slate-200">
              No startups match these filters
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Try changing the company search, industry, or stage.
            </p>

            <button
              type="button"
              onClick={() => {
                setSearchQuery("");
                setIndustryFilter("all");
                setStageFilter("all");
                setSortOption("score-desc");
              }}
              className="mt-5 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-2.5 text-sm font-semibold text-cyan-300 transition hover:border-cyan-400/40 hover:bg-cyan-400/15"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-[15px]">
              <thead className="bg-slate-950/80 backdrop-blur">
                <tr className="border-b border-white/10 text-left text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
                  <th scope="col" className="w-24 px-6 py-4">
                    Rank
                  </th>

                  <th scope="col" className="min-w-[280px] px-6 py-4">
                    Company
                  </th>

                  <th scope="col" className="min-w-[160px] px-6 py-4">
                    Industry
                  </th>

                  <th scope="col" className="min-w-[130px] px-6 py-4">
                    Stage
                  </th>

                  <th
                    scope="col"
                    className="hidden min-w-[180px] px-6 py-4 lg:table-cell"
                  >
                    Business model
                  </th>

                  <th
                    scope="col"
                    className="whitespace-nowrap px-6 py-4 text-right"
                  >
                    Overall score
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-white/[0.07]">
                {filteredRankings.map((startup, index) => {
                  const rank = index + 1;
                  const companyName =
                    startup.company_name?.trim() || "Unknown Startup";

                  return (
                    <tr
                      key={startup.id}
                      className="group transition duration-200 hover:bg-gradient-to-r hover:from-indigo-500/[0.08] hover:via-cyan-500/[0.04] hover:to-transparent"
                    >
                      <td className="whitespace-nowrap px-6 py-5">
                        <span
                          className={`inline-flex min-w-11 items-center justify-center rounded-full border px-3 py-1.5 text-[13px] font-bold ${getRankClasses(
                            rank
                          )}`}
                        >
                          #{rank}
                        </span>
                      </td>

                      <td className="px-6 py-5">
                        <Link
                          href={`/startup/${encodeURIComponent(companyName)}`}
                          className="group/link inline-flex items-center gap-3"
                        >
                          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-indigo-400/20 bg-gradient-to-br from-indigo-500/20 to-cyan-400/10 text-[13px] font-bold text-indigo-200 transition group-hover/link:border-cyan-400/30 group-hover/link:text-cyan-200">
                            {getInitials(companyName)}
                          </span>

                          <span className="text-[15px] font-semibold text-slate-100 transition-colors group-hover/link:text-cyan-300">
                            {companyName}
                          </span>

                          <span
                            aria-hidden="true"
                            className="translate-x-0 text-base text-slate-600 opacity-0 transition-all group-hover/link:translate-x-1 group-hover/link:text-cyan-300 group-hover/link:opacity-100"
                          >
                            →
                          </span>
                        </Link>
                      </td>

                      <td className="whitespace-nowrap px-6 py-5">
                        <MetadataBadge value={startup.industry} />
                      </td>

                      <td className="whitespace-nowrap px-6 py-5">
                        <MetadataBadge value={startup.stage} />
                      </td>

                      <td className="hidden whitespace-nowrap px-6 py-5 lg:table-cell">
                        <MetadataBadge value={startup.business_model} />
                      </td>

                      <td className="whitespace-nowrap px-6 py-5 text-right">
                        <span
                          className={`inline-flex min-w-16 items-center justify-center rounded-full border px-3.5 py-1.5 text-[15px] font-bold tabular-nums ${getScoreClasses(
                            startup.overall_score
                          )}`}
                        >
                          {formatScore(startup.overall_score)}
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
    </div>
  );
}
