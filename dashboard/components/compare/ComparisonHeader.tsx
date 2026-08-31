import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";
import { SPSRing } from "@/components/sps";

import { isSpsTooCloseToRank } from "@/lib/compareInsights";
import { gridColsClass } from "./gridCols";

import type { ComparisonStartup } from "@/types";

type ComparisonHeaderProps = {
  startups: ComparisonStartup[];
  onRemove: (startupId: number) => void;
};

// Part 8: SPS stays visually prominent (the ring, same component every
// other canonical surface uses) but the numbers themselves are never
// altered -- this only adds restrained language when the whole selected
// set is within SPS_CLOSE_THRESHOLD of each other, so a 78.8-vs-78.7 gap
// doesn't read as "Ramp is the stronger company."
export default function ComparisonHeader({
  startups,
  onRemove,
}: ComparisonHeaderProps) {
  const tooClose = isSpsTooCloseToRank(startups);

  return (
    <div>
      <div className={`grid gap-4 ${gridColsClass(startups.length)}`}>
        {startups.map((startup) => (
          <BaseCard key={startup.startup_id} className="flex flex-col items-center gap-3 p-5 text-center">
            <button
              type="button"
              onClick={() => onRemove(startup.startup_id)}
              aria-label={`Remove ${startup.company_name} from comparison`}
              className="self-end text-xs font-medium text-text-muted hover:text-danger"
            >
              Remove ×
            </button>

            <Link
              href={`/startup/${encodeURIComponent(startup.company_name)}`}
              className="group"
            >
              {/* Phase 10.9, Part 15/21: SPSRing now renders null as its
                  own honest "unavailable" state -- coercing to 0 here
                  would draw a real, danger-red ring for a startup that
                  simply has no score, indistinguishable from one that
                  scored zero on real evidence. */}
              <SPSRing
                score={startup.overall_score}
                size="sm"
                showDetails={false}
              />

              <h2 className="mt-3 text-base font-semibold text-text-primary transition-colors group-hover:text-primary">
                {startup.company_name}
              </h2>
            </Link>

            <div className="flex flex-wrap justify-center gap-1.5 text-xs text-text-muted">
              {startup.industry ? <span>{startup.industry}</span> : null}
              {startup.industry && startup.company_stage ? <span>·</span> : null}
              {startup.company_stage ? <span>{startup.company_stage}</span> : null}
            </div>

            <Link
              href={`/startup/${encodeURIComponent(startup.company_name)}`}
              className="text-xs font-semibold text-primary hover:text-primary-hover"
            >
              View profile →
            </Link>
          </BaseCard>
        ))}
      </div>

      {tooClose ? (
        <p className="mt-3 text-center text-xs text-text-muted">
          These startups have very close Startup Power Scores — treat this
          as roughly tied, not a clear leader.
        </p>
      ) : null}
    </div>
  );
}
