"use client";

import Link from "next/link";
import { useState } from "react";

import PageHeader from "@/components/layout/PageHeader";
import { searchStartups } from "@/lib/api";

import type { StartupSearchResult } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StartupSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSearch() {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setResults([]);
      setError("Enter a company name or keyword.");
      setHasSearched(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      setHasSearched(true);

      const data = await searchStartups(trimmedQuery);
      setResults(data);
    } catch (error) {
      console.error("Failed to search startups:", error);
      setResults([]);
      setError("Search could not be completed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void handleSearch();
  }

  return (
    <>
      <PageHeader
        title="Search"
        subtitle="Find startups by company name, market, summary, or risk."
      />

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <label htmlFor="startup-search" className="sr-only">
          Search startups
        </label>

        <input
          id="startup-search"
          type="search"
          className="min-h-11 w-full rounded-lg border border-slate-800 bg-slate-900 px-4 text-white outline-none transition-colors placeholder:text-slate-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          placeholder="Search by company, summary, market, or risk..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />

        <button
          type="submit"
          disabled={isLoading}
          className="min-h-11 rounded-lg bg-blue-600 px-6 text-sm font-semibold text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? "Searching..." : "Search"}
        </button>
      </form>

      {error ? (
        <div className="mt-6 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      <div className="mt-8 space-y-4">
        {isLoading ? (
          <>
            <div className="h-40 animate-pulse rounded-xl border border-slate-800 bg-slate-900" />
            <div className="h-40 animate-pulse rounded-xl border border-slate-800 bg-slate-900" />
          </>
        ) : null}

        {!isLoading && hasSearched && results.length === 0 && !error ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900 px-6 py-12 text-center">
            <p className="font-medium text-slate-300">
              No matching startups found
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Try another company name or a broader keyword.
            </p>
          </div>
        ) : null}

        {!isLoading &&
          results.map((startup) => {
            const companyName = startup.company_name ?? "Unknown Startup";

            return (
              <article
                key={`${companyName}-${startup.overall_score ?? "unscored"}`}
                className="rounded-xl border border-slate-800 bg-slate-900 p-6"
              >
                <h2 className="text-xl font-semibold text-white">
                  {companyName}
                </h2>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                  {startup.summary ?? "No summary is available."}
                </p>

                <p className="mt-4 text-sm text-slate-300">
                  Overall Score:{" "}
                  <span className="font-semibold text-white">
                    {startup.overall_score ?? "--"}
                  </span>
                </p>

                <Link
                  href={`/startup/${encodeURIComponent(companyName)}`}
                  className="mt-5 inline-flex text-sm font-semibold text-blue-400 transition-colors hover:text-blue-300"
                >
                  View startup →
                </Link>
              </article>
            );
          })}
      </div>
    </>
  );
}
