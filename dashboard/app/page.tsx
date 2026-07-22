"use client";

import { useEffect, useState } from "react";

import AnalyticsCard from "@/components/dashboard/AnalyticsCard";
import TopStartupsTable from "@/components/dashboard/TopStartupsTable";
import TopImprovingStartupsTable from "@/components/dashboard/TopImprovingStartupsTable";
import PageHeader from "@/components/layout/PageHeader";

import {
  getAnalytics,
  getTopImprovingStartups,
  getTopStartups,
} from "@/lib/api";

import type {
  AnalyticsSummary,
  ImprovingStartup,
  StartupRanking,
} from "@/types";

export default function Home() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [topStartups, setTopStartups] = useState<StartupRanking[]>([]);
  const [topImprovingStartups, setTopImprovingStartups] = useState<
    ImprovingStartup[]
  >([]);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadDashboard() {
      try {
        setIsLoading(true);
        setError(null);

        const [analyticsData, topStartupsData, topImprovingData] =
          await Promise.all([
            getAnalytics(),
            getTopStartups(),
            getTopImprovingStartups(),
          ]);

        if (!isMounted) {
          return;
        }

        setAnalytics(analyticsData);
        setTopStartups(topStartupsData);
        setTopImprovingStartups(topImprovingData);
      } catch (error) {
        if (!isMounted) {
          return;
        }

        console.error("Failed to load dashboard:", error);
        setError("The dashboard data could not be loaded.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      isMounted = false;
    };
  }, []);

  if (error) {
    return (
      <>
        <PageHeader
          title="Dashboard"
          subtitle="Monitor startup performance, intelligence scores, and recent movement across the platform."
        />

        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6">
          <h2 className="text-base font-semibold text-red-300">
            Unable to load dashboard
          </h2>

          <p className="mt-2 text-sm text-red-200/80">{error}</p>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-5 rounded-lg bg-red-500 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-400"
          >
            Try again
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Monitor startup performance, intelligence scores, and recent movement across the platform."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <AnalyticsCard
          title="Total Startups"
          value={isLoading ? "--" : analytics?.total_startups ?? 0}
        />

        <AnalyticsCard
          title="Average Score"
          value={isLoading ? "--" : analytics?.average_overall_score ?? 0}
        />

        <AnalyticsCard
          title="Average Readiness"
          value={isLoading ? "--" : analytics?.average_readiness_score ?? 0}
        />
      </div>

      {isLoading ? (
        <div className="mt-10 space-y-6">
          <div className="h-72 animate-pulse rounded-xl border border-slate-800 bg-slate-900" />
          <div className="h-72 animate-pulse rounded-xl border border-slate-800 bg-slate-900" />
        </div>
      ) : (
        <>
          <TopStartupsTable startups={topStartups} />

          <TopImprovingStartupsTable startups={topImprovingStartups} />
        </>
      )}
    </>
  );
}
