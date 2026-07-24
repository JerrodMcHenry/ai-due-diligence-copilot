"use client";

import { useEffect, useState } from "react";

import AnalyticsCard from "@/components/dashboard/AnalyticsCard";
import TopImprovingStartupsTable from "@/components/dashboard/TopImprovingStartupsTable";
import TopStartupsTable from "@/components/dashboard/TopStartupsTable";

import PageHeader from "@/components/layout/PageHeader";
import BaseCard from "@/components/ui/BaseCard";
import { SPSRing } from "@/components/sps";

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

function formatMetric(value: number | undefined) {
  if (value === undefined) {
    return "0";
  }

  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="h-56 animate-pulse rounded-2xl border border-border bg-surface" />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div
            key={index}
            className="h-40 animate-pulse rounded-2xl border border-border bg-surface"
          />
        ))}
      </div>

      <div className="h-96 animate-pulse rounded-2xl border border-border bg-surface" />

      <div className="h-80 animate-pulse rounded-2xl border border-border bg-surface" />
    </div>
  );
}

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
        console.error(error);

        if (isMounted) {
          setError("Unable to load dashboard data.");
        }
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

  return (
    <div className="space-y-8">
      <PageHeader
        title="Good Evening 👋"
        subtitle="Welcome back. Here's how your startup intelligence platform is performing today."
      />

      {error ? (
        <BaseCard className="border-danger/30 bg-danger-soft p-6">
          <h2 className="text-base font-semibold text-danger">
            Unable to load dashboard
          </h2>

          <p className="mt-2 text-sm text-danger">{error}</p>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-5 rounded-xl bg-danger px-4 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
          >
            Try Again
          </button>
        </BaseCard>
      ) : isLoading ? (
        <DashboardSkeleton />
      ) : (
        <>
          {/* Hero */}

          <section className="grid gap-6 lg:grid-cols-3">
            <BaseCard className="p-8 lg:col-span-2">
              <div className="flex flex-col gap-8 xl:flex-row xl:justify-between">
                <div>
                  <p className="text-sm font-medium text-text-secondary">
                    Startup Intelligence Engine
                  </p>

                  <div className="mt-6">
                    <SPSRing
                      score={analytics?.average_overall_score ?? 0}
                      size="lg"
                      trend={2.4}
                      percentile={32}
                      confidence="Medium"
                    />
                  </div>

                  <p className="mt-6 text-xl font-semibold">
                    Startup Power Score
                  </p>

                  <p className="mt-3 text-green-500 font-medium">
                    ▲ Platform Average
                  </p>

                  <div className="mt-8">
                    <div className="mb-2 flex justify-between text-sm">
                      <span>Goal</span>
                      <span>80 SPS</span>
                    </div>

                    <div className="h-3 overflow-hidden rounded-full bg-border">
                      <div
                        className="h-full rounded-full bg-primary transition-all duration-700"
                        style={{
                          width: `${Math.min(
                            ((analytics?.average_overall_score ?? 0) / 80) *
                              100,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div className="rounded-xl bg-primary/10 px-4 py-2 text-sm font-semibold text-primary">
                  SPS™
                </div>
              </div>
            </BaseCard>

            <div className="grid gap-4">
              <AnalyticsCard
                title="Tracked Startups"
                value={analytics?.total_startups ?? 0}
                description="Companies currently tracked."
              />

              <AnalyticsCard
                title="Average Readiness"
                value={formatMetric(analytics?.average_readiness_score)}
                description="Average investment readiness."
              />
            </div>
          </section>

          {/* Recommended Actions */}

          <section className="grid gap-4 md:grid-cols-3">
            <BaseCard className="p-6">
              <p className="text-sm text-text-secondary">Highest Impact</p>

              <h3 className="mt-4 text-lg font-semibold">
                Improve GTM Strategy
              </h3>

              <p className="mt-6 text-sm text-text-secondary">
                Estimated Impact
              </p>

              <p className="mt-1 text-2xl font-bold text-green-500">+3 SPS</p>
            </BaseCard>

            <BaseCard className="p-6">
              <p className="text-sm text-text-secondary">Validate Pricing</p>

              <p className="mt-8 text-2xl font-bold">+2 SPS</p>
            </BaseCard>

            <BaseCard className="p-6">
              <p className="text-sm text-text-secondary">Customer Interviews</p>

              <p className="mt-8 text-2xl font-bold">+2 SPS</p>
            </BaseCard>
          </section>

          {/* Rankings */}

          <section className="space-y-8">
            <TopStartupsTable startups={topStartups} />

            <TopImprovingStartupsTable startups={topImprovingStartups} />
          </section>
        </>
      )}
    </div>
  );
}
