"use client";

import { useEffect, useState } from "react";

import PageHeader from "@/components/layout/PageHeader";
import RankingsTable from "@/components/rankings/RankingsTable";

import { getRankings } from "@/lib/api";

import type { RankingEntry } from "@/types";

export default function RankingsPage() {
  const [rankings, setRankings] = useState<RankingEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadRankings() {
      try {
        setIsLoading(true);
        setError(null);

        const data = await getRankings();

        if (isMounted) {
          setRankings(data);
        }
      } catch (error) {
        console.error("Failed to load rankings:", error);

        if (isMounted) {
          setError("The rankings could not be loaded.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadRankings();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <>
      <PageHeader
        title="Rankings"
        subtitle="Compare startup intelligence scores across the platform."
      />

      {isLoading ? (
        <div className="h-96 animate-pulse rounded-xl border border-slate-800 bg-slate-900" />
      ) : error ? (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">
            Unable to load rankings
          </h2>

          <p className="mt-2 text-sm text-red-200/80">{error}</p>
        </div>
      ) : (
        <RankingsTable rankings={rankings} />
      )}
    </>
  );
}
