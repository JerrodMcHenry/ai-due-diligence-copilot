"use client";

import { useRef, useState } from "react";

import { SPSRing } from "@/components/sps";
import BaseCard from "@/components/ui/BaseCard";

import PillarDetailDrawer from "./PillarDetailDrawer";

import type {
  ConfidenceLevel,
  PillarAnalysis,
  SIEMethodologyAnalysis,
} from "@/types";

type IntelligencePillarsProps = {
  methodology: SIEMethodologyAnalysis;
};

type PillarKey =
  | "market"
  | "team"
  | "product"
  | "execution"
  | "traction"
  | "financial_health";

type PillarDefinition = {
  key: PillarKey;
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

export const CONFIDENCE_BADGE_CLASSES: Record<ConfidenceLevel, string> = {
  Low: "border border-border text-text-secondary",
  Medium: "bg-warning/10 text-warning",
  High: "bg-success/10 text-success",
};

export default function IntelligencePillars({
  methodology,
}: IntelligencePillarsProps) {
  const [selectedKey, setSelectedKey] = useState<PillarKey | null>(null);

  const triggerRefs = useRef<
    Partial<Record<PillarKey, HTMLButtonElement | null>>
  >({});

  function handleClose() {
    const key = selectedKey;
    setSelectedKey(null);

    // Return focus to the card that opened the drawer once it unmounts.
    if (key) {
      requestAnimationFrame(() => {
        triggerRefs.current[key]?.focus();
      });
    }
  }

  const selectedPillar = PILLARS.find((pillar) => pillar.key === selectedKey);

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
            isSelected={selectedKey === pillar.key}
            onSelect={() => setSelectedKey(pillar.key)}
            triggerRef={(node) => {
              triggerRefs.current[pillar.key] = node;
            }}
          />
        ))}
      </div>

      {selectedPillar ? (
        <PillarDetailDrawer
          label={selectedPillar.label}
          pillar={methodology[selectedPillar.key]}
          onClose={handleClose}
        />
      ) : null}
    </section>
  );
}

type PillarCardProps = {
  label: string;
  pillar: PillarAnalysis;
  isSelected: boolean;
  onSelect: () => void;
  triggerRef: (node: HTMLButtonElement | null) => void;
};

function PillarCard({
  label,
  pillar,
  isSelected,
  onSelect,
  triggerRef,
}: PillarCardProps) {
  const score = pillar.score;

  const strengths = pillar.strengths.slice(0, 2);
  const weaknesses = pillar.weaknesses.slice(0, 2);

  return (
    <button
      ref={triggerRef}
      type="button"
      onClick={onSelect}
      aria-haspopup="dialog"
      aria-expanded={isSelected}
      className={[
        "group block w-full appearance-none rounded-2xl border-0 bg-transparent p-0 text-left",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
      ].join(" ")}
    >
      <BaseCard
        className={[
          "p-6 transition duration-200 ease-out",
          "group-hover:-translate-y-0.5 group-hover:border-primary/40 group-hover:shadow-lg",
          isSelected ? "border-primary/60 shadow-lg ring-2 ring-primary/40" : "",
        ].join(" ")}
      >
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

        <div className="mt-4 flex items-center gap-1 text-xs font-semibold text-primary">
          <span>View full breakdown</span>
          <span
            aria-hidden="true"
            className="transition-transform duration-200 group-hover:translate-x-0.5"
          >
            →
          </span>
        </div>
      </BaseCard>
    </button>
  );
}

type PillarListProps = {
  heading?: string;
  items: string[];
  emptyLabel: string;
  markerClassName: string;
};

export function PillarList({
  heading,
  items,
  emptyLabel,
  markerClassName,
}: PillarListProps) {
  return (
    <div>
      {heading ? (
        <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
          {heading}
        </p>
      ) : null}

      {items.length > 0 ? (
        <ul className={["space-y-1.5", heading ? "mt-2" : ""].join(" ")}>
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
        <p className={["text-sm text-text-muted", heading ? "mt-2" : ""].join(" ")}>
          {emptyLabel}
        </p>
      )}
    </div>
  );
}
