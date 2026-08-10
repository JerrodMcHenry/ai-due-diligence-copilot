import { SPSRing } from "@/components/sps";
import BaseCard from "@/components/ui/BaseCard";

import type {
  ConfidenceLevel,
  PillarAnalysis,
  SIEMethodologyAnalysis,
} from "@/types";

type IntelligencePillarsProps = {
  methodology: SIEMethodologyAnalysis;
};

type PillarDefinition = {
  key:
    | "market"
    | "team"
    | "product"
    | "execution"
    | "traction"
    | "financial_health";
  label: string;
};

const PILLARS: PillarDefinition[] = [
  { key: "market", label: "Market" },
  { key: "team", label: "Team" },
  { key: "product", label: "Product" },
  { key: "execution", label: "Execution" },
  { key: "traction", label: "Traction" },
  { key: "financial_health", label: "Financial Health" },
];

const CONFIDENCE_BADGE_CLASSES: Record<ConfidenceLevel, string> = {
  Low: "border border-border text-text-secondary",
  Medium: "bg-warning/10 text-warning",
  High: "bg-success/10 text-success",
};

export default function IntelligencePillars({
  methodology,
}: IntelligencePillarsProps) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-text-primary">
        Intelligence Pillars
      </h2>

      <div className="mt-4 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {PILLARS.map((pillar) => (
          <PillarCard
            key={pillar.key}
            label={pillar.label}
            pillar={methodology[pillar.key]}
          />
        ))}
      </div>
    </section>
  );
}

type PillarCardProps = {
  label: string;
  pillar: PillarAnalysis;
};

function PillarCard({ label, pillar }: PillarCardProps) {
  const score = pillar.score;

  const strengths = pillar.strengths.slice(0, 2);
  const weaknesses = pillar.weaknesses.slice(0, 2);

  return (
    <BaseCard className="p-6">
      <div className="flex items-start gap-4">
        {score !== null ? (
          <SPSRing score={score * 10} size="sm" showDetails={false} />
        ) : (
          <div
            role="img"
            aria-label="Score not yet available"
            className="flex h-[120px] w-[120px] shrink-0 items-center justify-center rounded-full border-2 border-dashed border-border text-center"
          >
            <span className="px-3 text-xs font-medium text-text-muted">
              Not enough evidence yet
            </span>
          </div>
        )}

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-base font-semibold text-text-primary">
              {label}
            </h3>

            <span
              className={[
                "shrink-0 rounded-full px-2.5 py-1 text-xs font-medium",
                CONFIDENCE_BADGE_CLASSES[pillar.confidence],
              ].join(" ")}
            >
              {pillar.confidence}
            </span>
          </div>

          <p className="mt-1 text-sm font-medium text-text-secondary">
            {score !== null ? `${score.toFixed(1)} / 10` : "No score yet"}
          </p>

          {pillar.summary ? (
            <p className="mt-3 text-sm leading-6 text-text-secondary">
              {pillar.summary}
            </p>
          ) : null}
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-4 border-t border-border pt-4">
        <PillarList
          heading="Strengths"
          items={strengths}
          emptyLabel="None noted yet."
          markerClassName="text-success"
        />

        <PillarList
          heading="Weaknesses"
          items={weaknesses}
          emptyLabel="None noted yet."
          markerClassName="text-danger"
        />
      </div>
    </BaseCard>
  );
}

type PillarListProps = {
  heading: string;
  items: string[];
  emptyLabel: string;
  markerClassName: string;
};

function PillarList({
  heading,
  items,
  emptyLabel,
  markerClassName,
}: PillarListProps) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
        {heading}
      </p>

      {items.length > 0 ? (
        <ul className="mt-2 space-y-1.5">
          {items.map((item, index) => (
            <li
              key={index}
              className="flex gap-2 text-sm leading-5 text-text-secondary"
            >
              <span className={markerClassName} aria-hidden="true">
                •
              </span>

              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-text-muted">{emptyLabel}</p>
      )}
    </div>
  );
}
