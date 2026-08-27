"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import Badge, { type BadgeTone } from "@/components/ui/Badge";
import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import { getSPSMetadata } from "@/components/sps/utils/scoreMetadata";

import type { RankingEntry } from "@/types";

// Design System V2 (Phase 10.4), Part 12: this was the single most
// hardcoded-dark-only file found in Part 1's audit (slate/white/cyan/
// indigo/fuchsia literals, backdrop-blur, raw rgba() glow shadows,
// independent 80/65/50 score-color thresholds that disagreed with
// SPSRing's own banding) -- picked as the "one representative public
// intelligence surface" migration this phase asks for. Every filter/sort/
// search useState and useMemo below is byte-for-byte unchanged; only
// className/markup was touched.
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

// Reuses the exact same score-band logic SPSRing already renders with --
// previously this file had its OWN independent 80/65/50 thresholds that
// could (and did) disagree with the ring's 95/90/.../40 bands, so the same
// score could read as one color here and a different one on the Startup
// Profile it links to. One source of truth for "what color is a B+" now.
function scoreBadgeClasses(score: number | null | undefined) {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return "border-border bg-surface-muted text-text-muted";
  }

  const metadata = getSPSMetadata(score);
  return `border-transparent ${metadata.backgroundClass} ${metadata.textClass}`;
}

// Simplified from three distinct hardcoded gold/silver/bronze hues to two
// semantic tones -- #1 stands out, #2/#3 are gently distinguished from the
// rest, without inventing colors the token system doesn't otherwise have.
function rankBadgeTone(rank: number): BadgeTone {
  if (rank === 1) return "warning";
  if (rank <= 3) return "primary";
  return "neutral";
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
    <BaseCard className="p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
        {label}
      </p>

      <p className="mt-3 text-3xl font-semibold tracking-tight text-text-primary">
        {value}
      </p>

      <p className="mt-1 text-sm text-text-muted">{detail}</p>
    </BaseCard>
  );
}

const SELECT_CLASSES =
  "h-11 w-full rounded-xl border border-border bg-surface px-3 text-sm text-text-secondary outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20";

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
      <EmptyState
        icon={<span className="text-sm font-bold">SI</span>}
        title="No ranking data available"
        description="Rankings will appear after startup analyses have been completed."
      />
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

      <BaseCard className="overflow-hidden">
        <div className="border-b border-border bg-surface-subtle p-4 sm:p-5">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(260px,1fr)_190px_180px_190px]">
            <div className="relative">
              <label htmlFor="ranking-search" className="sr-only">
                Search companies
              </label>

              <span
                aria-hidden="true"
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-base text-text-muted"
              >
                ⌕
              </span>

              <input
                id="ranking-search"
                type="search"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search companies..."
                className="h-11 w-full rounded-xl border border-border bg-surface pl-10 pr-4 text-sm text-text-primary outline-none transition-colors placeholder:text-text-muted focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>

            <label>
              <span className="sr-only">Filter by industry</span>

              <select
                value={industryFilter}
                onChange={(event) => setIndustryFilter(event.target.value)}
                className={SELECT_CLASSES}
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
                className={SELECT_CLASSES}
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
                className={SELECT_CLASSES}
              >
                <option value="score-desc">Score: highest first</option>
                <option value="score-asc">Score: lowest first</option>
                <option value="company-asc">Company: A–Z</option>
                <option value="newest">Most recently analyzed</option>
              </select>
            </label>
          </div>

          <p className="mt-3 text-sm text-text-muted">
            Showing {filteredRankings.length} of {rankings.length} startups
          </p>
        </div>

        {filteredRankings.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-lg font-semibold text-text-primary">
              No startups match these filters
            </p>

            <p className="mt-2 text-sm text-text-muted">
              Try changing the company search, industry, or stage.
            </p>

            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="mt-5"
              onClick={() => {
                setSearchQuery("");
                setIndustryFilter("all");
                setStageFilter("all");
                setSortOption("score-desc");
              }}
            >
              Clear filters
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-sm">
              <thead className="bg-surface-subtle">
                <tr className="border-b border-border text-left text-xs font-semibold uppercase tracking-wide text-text-muted">
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

              <tbody className="divide-y divide-border">
                {filteredRankings.map((startup, index) => {
                  const rank = index + 1;
                  const companyName =
                    startup.company_name?.trim() || "Unknown Startup";

                  return (
                    <tr
                      key={startup.id}
                      className="transition-colors hover:bg-surface-subtle"
                    >
                      <td className="whitespace-nowrap px-6 py-5">
                        <Badge tone={rankBadgeTone(rank)} className="min-w-11 justify-center">
                          #{rank}
                        </Badge>
                      </td>

                      <td className="px-6 py-5">
                        <Link
                          href={`/startup/${encodeURIComponent(companyName)}`}
                          className="group/link inline-flex items-center gap-3"
                        >
                          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-xs font-bold text-primary transition-colors group-hover/link:bg-primary group-hover/link:text-white">
                            {getInitials(companyName)}
                          </span>

                          <span className="text-sm font-semibold text-text-primary transition-colors group-hover/link:text-primary">
                            {companyName}
                          </span>

                          <span
                            aria-hidden="true"
                            className="translate-x-0 text-base text-text-muted opacity-0 transition-all group-hover/link:translate-x-1 group-hover/link:text-primary group-hover/link:opacity-100"
                          >
                            →
                          </span>
                        </Link>
                      </td>

                      <td className="whitespace-nowrap px-6 py-5">
                        <Badge tone="neutral" className="max-w-[190px] truncate">
                          {startup.industry?.trim() || "--"}
                        </Badge>
                      </td>

                      <td className="whitespace-nowrap px-6 py-5">
                        <Badge tone="neutral" className="max-w-[190px] truncate">
                          {startup.stage?.trim() || "--"}
                        </Badge>
                      </td>

                      <td className="hidden whitespace-nowrap px-6 py-5 lg:table-cell">
                        <Badge tone="neutral" className="max-w-[190px] truncate">
                          {startup.business_model?.trim() || "--"}
                        </Badge>
                      </td>

                      <td className="whitespace-nowrap px-6 py-5 text-right">
                        <span
                          className={`inline-flex min-w-16 items-center justify-center rounded-full border px-3.5 py-1.5 text-sm font-bold tabular-nums ${scoreBadgeClasses(
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
      </BaseCard>
    </div>
  );
}
