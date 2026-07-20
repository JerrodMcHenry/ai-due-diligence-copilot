"use client";

import { useEffect, useState } from "react";

import AnalyticsCard from "@/components/AnalyticsCard";
import TopStartupsTable from "@/components/TopStartupsTable";
import TopImprovingStartupsTable from "@/components/TopImprovingStartupsTable";
import PageHeader from "@/components/layout/PageHeader";

import {
  getAnalytics,
  getTopStartups,
  getTopImprovingStartups,
} from "@/lib/api";

export default function Home() {
  const [analytics, setAnalytics] = useState<any>(null);
  const [topStartups, setTopStartups] = useState<any[]>([]);
  const [topImprovingStartups, setTopImprovingStartups] = useState<any[]>([]);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [analyticsData, topStartupsData, topImprovingData] =
          await Promise.all([
            getAnalytics(),
            getTopStartups(),
            getTopImprovingStartups(),
          ]);

        setAnalytics(analyticsData);
        setTopStartups(topStartupsData);
        setTopImprovingStartups(topImprovingData);
      } catch (error) {
        console.error("Failed to load dashboard:", error);
      }
    }

    loadDashboard();
  }, []);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Monitor startup performance, intelligence scores, and recent movement across the platform."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <AnalyticsCard
          title="Total Startups"
          value={analytics?.total_startups ?? "--"}
        />

        <AnalyticsCard
          title="Average Score"
          value={analytics?.average_overall_score ?? "--"}
        />

        <AnalyticsCard
          title="Average Readiness"
          value={analytics?.average_readiness_score ?? "--"}
        />
      </div>

      <TopStartupsTable startups={topStartups} />

      <TopImprovingStartupsTable startups={topImprovingStartups} />
    </div>
  );
}
