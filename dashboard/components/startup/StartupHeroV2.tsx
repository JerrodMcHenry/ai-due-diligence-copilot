import type { ReactNode } from "react";

import { SPSRing } from "@/components/sps";
import BaseCard from "@/components/ui/BaseCard";

import { CONFIDENCE_BADGE_CLASSES, PILLARS } from "./pillarMeta";
import { SparkleIcon } from "./icons";

import type { ConfidenceLevel, SIEMethodologyAnalysis } from "@/types";

type StartupHeroV2Props = {
  methodology: SIEMethodologyAnalysis;
  createdAt: string;
};

const ANALYSIS_TYPE_LABELS: Record<string, string> = {
  public: "Public Analysis",
  pitch_deck: "Pitch Deck Analysis",
  founder: "Founder Analysis",
  investor: "Investor Analysis",
  data_room: "Data Room Analysis",
};

// analysis_context is intentionally typed `unknown` on the frontend (same
// reason as startup_scorecard below) — read defensively, no shape asserted.
function getAnalysisType(analysisContext: unknown): string | null {
  if (
    typeof analysisContext === "object" &&
    analysisContext !== null &&
    "analysis_type" in analysisContext
  ) {
    const value = (analysisContext as { analysis_type?: unknown }).analysis_type;

    if (typeof value === "string" && value.trim().length > 0) {
      return (
        ANALYSIS_TYPE_LABELS[value] ??
        value
          .split("_")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" ")
      );
    }
  }

  return null;
}

function formatAnalysisDate(isoDate: string): string | null {
  const date = new Date(isoDate);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// Derived from the six real, already-scored pillar confidences (not a
// separate field — `confidence_score` on the methodology model is never
// populated by the backend, so treating it as real data would mean
// displaying a number that's always 0). Ties resolve toward the more
// conservative (lower) confidence level.
function getOverallConfidence(methodology: SIEMethodologyAnalysis): ConfidenceLevel {
  const counts: Record<ConfidenceLevel, number> = { Low: 0, Medium: 0, High: 0 };

  for (const pillar of PILLARS) {
    counts[methodology[pillar.key].confidence] += 1;
  }

  let best: ConfidenceLevel = "Low";

  for (const level of ["Low", "Medium", "High"] as const) {
    if (counts[level] > counts[best]) {
      best = level;
    }
  }

  return best;
}

// startup_scorecard is intentionally typed `unknown` on the frontend (its
// shape isn't part of the canonical contract yet), so this reads it
// defensively rather than asserting a shape onto it.
function getRecommendation(startupScorecard: unknown): string | null {
  if (
    typeof startupScorecard === "object" &&
    startupScorecard !== null &&
    "recommendation" in startupScorecard
  ) {
    const value = (startupScorecard as { recommendation?: unknown }).recommendation;

    if (typeof value === "string" && value.trim().length > 0) {
      return value;
    }
  }

  return null;
}

export default function StartupHeroV2({
  methodology,
  createdAt,
}: StartupHeroV2Props) {
  const overallConfidence = getOverallConfidence(methodology);
  const recommendation = getRecommendation(methodology.startup_scorecard);
  const analysisType = getAnalysisType(methodology.analysis_context);
  const analysisDate = formatAnalysisDate(createdAt);

  const { company_stage, industry, business_model, funding_stage } = methodology.context;

  // Company stage and funding stage frequently describe the same thing
  // (e.g. both "Series A") — don't show the same value twice.
  const showFundingStage =
    Boolean(funding_stage) &&
    funding_stage.trim().toLowerCase() !== company_stage.trim().toLowerCase();

  return (
    <BaseCard className="p-8">
      <div className="grid gap-10 lg:grid-cols-[320px_1fr] lg:items-center">
        <div className="flex justify-center">
          <SPSRing
            score={methodology.startup_intelligence_score}
            confidence={overallConfidence}
            size="xl"
          />
        </div>

        <div>
          <h1 className="text-4xl font-bold text-text-primary">
            {methodology.context.company_name}
          </h1>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            {company_stage ? <MetaChip>{company_stage}</MetaChip> : null}
            {showFundingStage ? <MetaChip>{funding_stage}</MetaChip> : null}
            {industry ? <MetaChip>{industry}</MetaChip> : null}
            {business_model ? <MetaChip>{business_model}</MetaChip> : null}

            {recommendation ? (
              <MetaChip className="bg-primary/10 text-primary">
                {recommendation}
              </MetaChip>
            ) : null}

            <MetaChip className={CONFIDENCE_BADGE_CLASSES[overallConfidence]}>
              {overallConfidence} confidence
            </MetaChip>
          </div>

          {analysisType || analysisDate ? (
            <p className="mt-2 text-xs text-text-muted">
              {analysisType}
              {analysisType && analysisDate ? " · " : null}
              {analysisDate ? `Analyzed ${analysisDate}` : null}
            </p>
          ) : null}

          <div className="mt-6 border-t border-border pt-6">
            <h2 className="flex items-center gap-1.5 text-xl font-semibold text-text-primary">
              <SparkleIcon className="h-4 w-4 text-primary" />
              Executive Coaching Summary
            </h2>

            <p className="mt-3 max-w-prose text-[17px] leading-8 text-text-secondary">
              {methodology.executive_coaching_summary}
            </p>
          </div>
        </div>
      </div>
    </BaseCard>
  );
}

function MetaChip({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={[
        "rounded-full px-3 py-1 text-xs font-medium",
        className ?? "border border-border text-text-secondary",
      ].join(" ")}
    >
      {children}
    </span>
  );
}
