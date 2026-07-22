type StartupProfilePageProps = {
  params: Promise<{
    id: string;
  }>;
};

import ScoreBreakdown from "@/components/startup/ScoreBreakdown";
import AnalysisSection from "@/components/startup/AnalysisSection";
import StartupHero from "@/components/startup/StartupHero";
import PrimaryScoreCard from "@/components/startup/PrimaryScoreCard";

export default async function StartupProfilePage({
  params,
}: StartupProfilePageProps) {
  const { id } = await params;

  const response = await fetch(
    `http://127.0.0.1:8000/startup/${encodeURIComponent(id)}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    return (
      <div className="p-8">
        <h1 className="text-4xl font-bold">Startup Not Found</h1>
        <p className="mt-4 text-gray-400">No startup profile found for {id}.</p>
      </div>
    );
  }

  const startup = await response.json();

  return (
    <div className="p-8">
      <StartupHero
        companyName={startup.company_name}
        industry={startup.industry}
        stage={startup.stage}
        businessModel={startup.business_model}
        recommendation={startup.recommendation}
      />

      <div className="mt-8 grid grid-cols-2 gap-6">
        <PrimaryScoreCard
          title="Startup Intelligence Score"
          score={startup.overall_score}
        />

        <PrimaryScoreCard
          title="Readiness Score"
          score={startup.readiness_score}
        />
      </div>

      <ScoreBreakdown
        marketScore={startup.market_score}
        teamScore={startup.team_score}
        productScore={startup.product_score}
        competitionScore={startup.competition_score}
        tractionScore={startup.traction_score}
        financialScore={startup.financial_score}
      />

      <AnalysisSection title="Executive Summary" content={startup.summary} />

      <AnalysisSection
        title="Founder Analysis"
        content={startup.founder_analysis}
      />

      <AnalysisSection
        title="Market Analysis"
        content={startup.market_analysis}
      />

      <AnalysisSection
        title="Traction Analysis"
        content={startup.traction_analysis}
      />

      <AnalysisSection title="Investment Memo" content={startup.memo} />

      <AnalysisSection
        title="Competitor Analysis"
        content={startup.competitor_analysis}
      />

      <section className="mt-10 rounded-xl bg-gray-900 p-6">
        <h2 className="text-2xl font-bold mb-4">Readiness Summary</h2>
        <p className="text-gray-300">{startup.readiness_summary}</p>
      </section>
    </div>
  );
}
