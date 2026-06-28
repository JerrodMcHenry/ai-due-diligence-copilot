"use client";

import { useEffect, useState } from "react";
import AnalyticsCard from "@/components/AnalyticsCard";
import TopStartupsTable from "@/components/TopStartupsTable";
import TopImprovingStartupsTable from "@/components/TopImprovingStartupsTable";
import PageHeader from "@/components/layout/PageHeader";

export default function Home() {
  const [analytics, setAnalytics] = useState<any>(null);
  const [topStartups, setTopStartups] = useState<any[]>([]);
  const [topImprovingStartups, setTopImprovingStartups] = useState<any[]>([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/analytics")
      .then((response) => response.json())
      .then((data) => setAnalytics(data));

    fetch("http://127.0.0.1:8000/top-startups")
      .then((response) => response.json())
      .then((data) => setTopStartups(data));

    fetch("http://127.0.0.1:8000/top-improving-startups")
      .then((response) => response.json())
      .then((data) => setTopImprovingStartups(data));
  }, []);

  return (
    <div>
      <PageHeader
        title="Startup Intelligence Engine"
        subtitle="Here’s what’s happening across your startup ecosystem."
      />

      <div className="mt-10 grid grid-cols-3 gap-6">
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
