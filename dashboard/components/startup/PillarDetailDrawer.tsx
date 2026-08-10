"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

import { SPSRing } from "@/components/sps";

import { CONFIDENCE_BADGE_CLASSES, PillarList } from "./IntelligencePillars";

import type { ConfidenceLevel, Evidence, PillarAnalysis, Subscore } from "@/types";

type PillarDetailDrawerProps = {
  label: string;
  pillar: PillarAnalysis;
  onClose: () => void;
};

const EVIDENCE_STATUS_BADGE_CLASSES: Record<string, string> = {
  Observed: "bg-success/10 text-success",
  Inferred: "bg-warning/10 text-warning",
  Unavailable: "border border-border text-text-muted",
};

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
    )
  );
}

function formatWeight(weight: number): string {
  return `${Math.round(weight * 100)}%`;
}

export default function PillarDetailDrawer({
  label,
  pillar,
  onClose,
}: PillarDetailDrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  // Mount closed, then flip a frame later so the enter transition runs.
  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    panelRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key !== "Tab" || !panelRef.current) {
        return;
      }

      const focusable = getFocusableElements(panelRef.current);

      if (focusable.length === 0) {
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  const score = pillar.score;
  const breakdown = pillar.score_breakdown;
  const subscores = breakdown.subscores ?? [];
  const evidenceCoverage = breakdown.evidence_coverage ?? 0;

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        aria-label="Close pillar details"
        onClick={onClose}
        className={[
          "absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300",
          visible ? "opacity-100" : "opacity-0",
        ].join(" ")}
      />

      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="pillar-drawer-title"
        tabIndex={-1}
        className={[
          "absolute inset-y-0 right-0 flex h-full w-full flex-col overflow-y-auto",
          "border-l border-border bg-surface-elevated shadow-2xl outline-none",
          "sm:max-w-lg lg:max-w-xl",
          "transition-transform duration-300 ease-out",
          visible ? "translate-x-0" : "translate-x-full",
        ].join(" ")}
      >
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-border bg-surface-elevated px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              Intelligence Pillar
            </p>
            <h2
              id="pillar-drawer-title"
              className="mt-1 text-xl font-bold text-text-primary"
            >
              {label}
            </h2>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 rounded-full border border-border p-2 text-text-secondary transition hover:border-primary/40 hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <span aria-hidden="true">✕</span>
          </button>
        </div>

        <div className="flex-1 space-y-8 px-6 py-6">
          <section className="flex items-center gap-5">
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

            <div>
              <p className="text-2xl font-bold text-text-primary">
                {score !== null ? `${score.toFixed(1)} / 10` : "No score yet"}
              </p>

              <span
                className={[
                  "mt-2 inline-block rounded-full px-2.5 py-1 text-xs font-medium",
                  CONFIDENCE_BADGE_CLASSES[pillar.confidence],
                ].join(" ")}
              >
                {pillar.confidence} confidence
              </span>
            </div>
          </section>

          <Section title="Summary">
            {pillar.summary ? (
              <p className="text-sm leading-6 text-text-secondary">
                {pillar.summary}
              </p>
            ) : (
              <p className="text-sm text-text-muted">Not enough evidence.</p>
            )}
          </Section>

          <div className="grid gap-6 sm:grid-cols-2">
            <Section title="Strengths">
              <PillarList
                items={pillar.strengths}
                emptyLabel="None noted yet."
                markerClassName="text-success"
              />
            </Section>

            <Section title="Weaknesses">
              <PillarList
                items={pillar.weaknesses}
                emptyLabel="None noted yet."
                markerClassName="text-danger"
              />
            </Section>
          </div>

          <Section title="Recommendations">
            <PillarList
              items={pillar.recommendations}
              emptyLabel="No recommendations yet."
              markerClassName="text-primary"
            />
          </Section>

          <Section title="Evidence">
            <EvidenceList items={pillar.evidence} />
          </Section>

          <Section title="Scoring methodology">
            {breakdown.scoring_summary ? (
              <p className="text-sm leading-6 text-text-secondary">
                {breakdown.scoring_summary}
              </p>
            ) : (
              <p className="text-sm text-text-muted">Not enough evidence.</p>
            )}

            <div className="mt-4">
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span>Evidence coverage</span>
                <span>{evidenceCoverage}%</span>
              </div>

              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-muted">
                <div
                  className="h-full rounded-full bg-primary transition-[width] duration-500"
                  style={{ width: `${evidenceCoverage}%` }}
                />
              </div>
            </div>
          </Section>

          <Section title="Subscores">
            {subscores.length > 0 ? (
              <div className="space-y-2">
                {subscores.map((subscore) => (
                  <SubscoreRow key={subscore.name} subscore={subscore} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted">Not enough evidence.</p>
            )}
          </Section>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section>
      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
      <div className="mt-2">{children}</div>
    </section>
  );
}

function isEvidenceObject(item: Evidence | string): item is Evidence {
  return typeof item === "object" && item !== null;
}

function EvidenceList({ items }: { items: Array<Evidence | string> }) {
  const [expanded, setExpanded] = useState(false);
  const visibleCount = 3;

  if (items.length === 0) {
    return <p className="text-sm text-text-muted">Not enough evidence.</p>;
  }

  const visibleItems = expanded ? items : items.slice(0, visibleCount);
  const remaining = items.length - visibleItems.length;

  return (
    <div>
      <ul className="space-y-2">
        {visibleItems.map((item, index) => (
          <li
            key={index}
            className="rounded-lg border border-border bg-surface-muted px-3 py-2 text-sm text-text-secondary"
          >
            {isEvidenceObject(item) ? (
              <>
                {item.title ? (
                  <p className="font-medium text-text-primary">{item.title}</p>
                ) : null}

                {item.text ? <p className="mt-0.5">{item.text}</p> : null}

                {item.url ? (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-1 inline-block text-xs font-medium text-primary hover:underline"
                  >
                    {item.source ?? item.url}
                  </a>
                ) : item.source ? (
                  <p className="mt-1 text-xs text-text-muted">{item.source}</p>
                ) : null}

                {!item.title && !item.text && !item.url && !item.source ? (
                  <p className="text-text-muted">No details provided.</p>
                ) : null}
              </>
            ) : (
              <p>{item}</p>
            )}
          </li>
        ))}
      </ul>

      {remaining > 0 ? (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="mt-2 text-xs font-semibold text-primary hover:underline"
        >
          Show {remaining} more
        </button>
      ) : null}

      {expanded && items.length > visibleCount ? (
        <button
          type="button"
          onClick={() => setExpanded(false)}
          className="mt-2 ml-4 text-xs font-semibold text-text-secondary hover:underline"
        >
          Show less
        </button>
      ) : null}
    </div>
  );
}

function MiniList({ heading, items }: { heading: string; items?: string[] }) {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
        {heading}
      </p>

      <ul className="mt-1 space-y-1">
        {items.map((item, index) => (
          <li key={index} className="text-sm text-text-secondary">
            • {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function SubscoreRow({ subscore }: { subscore: Subscore }) {
  const [expanded, setExpanded] = useState(false);

  const hasDetails =
    Boolean(subscore.rationale) ||
    (subscore.evidence?.length ?? 0) > 0 ||
    (subscore.recommendations?.length ?? 0) > 0 ||
    (subscore.missing_information?.length ?? 0) > 0;

  return (
    <div className="rounded-xl border border-border">
      <button
        type="button"
        onClick={() => setExpanded((previous) => !previous)}
        disabled={!hasDetails}
        aria-expanded={expanded}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left disabled:cursor-default"
      >
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-text-primary">
            {subscore.name}
          </p>
          <p className="mt-0.5 text-xs text-text-muted">
            Weight {formatWeight(subscore.weight)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <span className="text-sm font-semibold text-text-primary">
            {subscore.score !== null ? subscore.score.toFixed(1) : "—"}
          </span>

          {subscore.evidence_status ? (
            <span
              className={[
                "rounded-full px-2 py-0.5 text-[11px] font-medium",
                EVIDENCE_STATUS_BADGE_CLASSES[subscore.evidence_status] ??
                  "border border-border text-text-muted",
              ].join(" ")}
            >
              {subscore.evidence_status}
            </span>
          ) : null}

          {hasDetails ? (
            <span
              aria-hidden="true"
              className={[
                "text-text-muted transition-transform duration-200",
                expanded ? "rotate-90" : "",
              ].join(" ")}
            >
              ▸
            </span>
          ) : null}
        </div>
      </button>

      {expanded && hasDetails ? (
        <div className="space-y-3 border-t border-border px-4 py-3">
          {subscore.confidence ? (
            <p className="text-xs text-text-muted">
              Confidence:{" "}
              <span
                className={[
                  "rounded-full px-2 py-0.5 text-[11px] font-medium",
                  CONFIDENCE_BADGE_CLASSES[subscore.confidence as ConfidenceLevel],
                ].join(" ")}
              >
                {subscore.confidence}
              </span>
            </p>
          ) : null}

          {subscore.rationale ? (
            <p className="text-sm leading-6 text-text-secondary">
              {subscore.rationale}
            </p>
          ) : (
            <p className="text-sm text-text-muted">No rationale provided.</p>
          )}

          <MiniList heading="Evidence" items={subscore.evidence} />
          <MiniList heading="Recommendations" items={subscore.recommendations} />
          <MiniList
            heading="Missing information"
            items={subscore.missing_information}
          />
        </div>
      ) : null}
    </div>
  );
}
