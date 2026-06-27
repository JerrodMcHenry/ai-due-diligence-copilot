"use client";

import { useEffect, useState } from "react";
import AnalyticsCard from "@/components/AnalyticsCard";
import TopStartupsTable from "@/components/TopStartupsTable";
import TopImprovingStartupsTable from "@/components/TopImprovingStartupsTable";

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
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-5xl font-bold">Startup Intelligence Engine</h1>

      <p className="mt-4 text-gray-400">
        AI-powered startup intelligence for founders and investors.
      </p>

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
    </main>
  );
}
