import type { ReactNode } from "react";
import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";
import { SPSRing } from "@/components/sps";
import SaveStartupButton from "@/components/startup/SaveStartupButton";
import CompareToggle from "./CompareToggle";
import { PILLARS, type PillarKey } from "@/components/startup/pillarMeta";

import type { DiscoveryResult } from "@/types";

function formatAnalysisDate(iso: string): string {
  const date = new Date(iso);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

// DiscoveryResult's columns are named after get_rankings()'s own
// pre-existing convention (financial_score, not financial_health_score) --
// this maps PILLARS' canonical keys onto that shape rather than renaming
// either side.
function getPillarScore(result: DiscoveryResult, key: PillarKey): number | null {
  switch (key) {
    case "market":
      return result.market_score;
    case "team":
      return result.team_score;
    case "product":
      return result.product_score;
    case "execution":
      return result.execution_score;
    case "traction":
      return result.traction_score;
    case "financial_health":
      return result.financial_score;
    default:
      return null;
  }
}

function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-full border border-border px-2.5 py-1 text-xs font-medium text-text-secondary">
      {children}
    </span>
  );
}

type DiscoveryResultCardProps = {
  result: DiscoveryResult;
  compareSelected?: boolean;
  compareDisabled?: boolean;
  onToggleCompare?: () => void;
};

export default function DiscoveryResultCard({
  result,
  compareSelected = false,
  compareDisabled = false,
  onToggleCompare,
}: DiscoveryResultCardProps) {
  const profileHref = `/startup/${encodeURIComponent(result.company_name)}`;

  return (
    <BaseCard className="flex flex-col gap-4 p-5 transition-colors hover:border-primary/40">
      <div className="flex items-start justify-between gap-3">
        <Link href={profileHref} className="group min-w-0">
          <h3 className="truncate text-lg font-semibold text-text-primary transition-colors group-hover:text-primary">
            {result.company_name}
          </h3>

          <p className="mt-1 text-xs text-text-muted">
            Analyzed {formatAnalysisDate(result.created_at)}
          </p>
        </Link>

        {/* overall_score is never null for a discovery result -- the
            underlying query requires startup_intelligence_score IS NOT
            NULL to be canonical at all (see discover_startups()'s own
            docstring) -- the ?? 0 fallback below is defensive typing
            only, never an expected runtime path. */}
        <SPSRing score={result.overall_score ?? 0} size="xs" showDetails={false} />
      </div>

      <div className="flex flex-wrap gap-2">
        {result.industry ? <Chip>{result.industry}</Chip> : null}
        {result.stage ? <Chip>{result.stage}</Chip> : null}
        {result.business_model ? <Chip>{result.business_model}</Chip> : null}
      </div>

      <div className="grid grid-cols-3 gap-x-2 gap-y-2 border-t border-border pt-3 text-center text-xs sm:grid-cols-6">
        {PILLARS.map((pillar) => {
          const score = getPillarScore(result, pillar.key);

          return (
            <div key={pillar.key}>
              <p className="truncate text-text-muted" title={pillar.label}>
                {pillar.label.split(" ")[0]}
              </p>

              <p className="font-semibold text-text-secondary">
                {score !== null ? score.toFixed(1) : "—"}
              </p>
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between border-t border-border pt-3">
        <Link
          href={profileHref}
          className="text-sm font-semibold text-primary hover:text-primary-hover"
        >
          View profile →
        </Link>

        <div className="flex items-center gap-2">
          {onToggleCompare ? (
            <CompareToggle
              selected={compareSelected}
              disabled={compareDisabled}
              onToggle={onToggleCompare}
            />
          ) : null}

          <SaveStartupButton startupId={result.startup_id} />
        </div>
      </div>
    </BaseCard>
  );
}
