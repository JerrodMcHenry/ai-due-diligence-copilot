import { SPSRing } from "@/components/sps";
import BaseCard from "@/components/ui/BaseCard";

import { CONFIDENCE_BADGE_CLASSES, PILLARS } from "./pillarMeta";

import type { PillarKey } from "./pillarMeta";
import type { SIEMethodologyAnalysis } from "@/types";

type PillarNavProps = {
  methodology: SIEMethodologyAnalysis;
  selectedKey: PillarKey;
  onSelect: (key: PillarKey) => void;
};

export default function PillarNav({
  methodology,
  selectedKey,
  onSelect,
}: PillarNavProps) {
  return (
    <BaseCard className="p-2 lg:sticky lg:top-10">
      <nav aria-label="Intelligence pillars" className="space-y-1">
        {PILLARS.map((pillar) => {
          const data = methodology[pillar.key];
          const isSelected = pillar.key === selectedKey;
          const score = data.score;

          return (
            <button
              key={pillar.key}
              type="button"
              onClick={() => onSelect(pillar.key)}
              aria-current={isSelected ? "true" : undefined}
              className={[
                "flex w-full items-center gap-3.5 rounded-xl border-l-2 px-3.5 py-3 text-left transition",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                isSelected
                  ? "border-primary bg-primary/10 shadow-sm"
                  : "border-transparent hover:border-border-strong hover:bg-surface-muted",
              ].join(" ")}
            >
              {score !== null ? (
                <SPSRing score={score * 10} size="xs" showDetails={false} />
              ) : (
                <div
                  role="img"
                  aria-label="Score not yet available"
                  className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-2 border-dashed border-border"
                >
                  <span className="text-xs font-medium text-text-muted">
                    N/A
                  </span>
                </div>
              )}

              <div className="min-w-0 flex-1">
                <p
                  className={[
                    "truncate text-base font-semibold",
                    isSelected ? "text-primary" : "text-text-primary",
                  ].join(" ")}
                >
                  {pillar.label}
                </p>

                <p className="text-xs text-text-secondary">
                  {score !== null ? `${score.toFixed(1)} / 10` : "No score yet"}
                </p>
              </div>

              <span
                className={[
                  "shrink-0 rounded-full px-2 py-0.5 text-xs font-medium",
                  CONFIDENCE_BADGE_CLASSES[data.confidence],
                ].join(" ")}
              >
                {data.confidence}
              </span>
            </button>
          );
        })}
      </nav>
    </BaseCard>
  );
}
