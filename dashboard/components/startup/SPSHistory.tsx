"use client";

import { useId, useState } from "react";

import BaseCard from "@/components/ui/BaseCard";

import type { SPSHistoryPoint } from "@/types";

type SPSHistoryProps = {
  history: SPSHistoryPoint[];
  // Phase 10.9 verification fix: this component always tracks the legacy
  // V2.1 startup_intelligence_score (score_history has no V3 field --
  // see get_sps_history()'s own docstring in app/database/db.py). When
  // the current analysis ALSO has a V3 assessment, showing a bare
  // "SPS History" / "Current SPS" here reads as a second, competing
  // number right next to (or directly contradicting, for LIMITED/
  // INSUFFICIENT) the V3 assessment above it. This only changes the
  // copy to disambiguate which methodology the number belongs to -- the
  // data source and every number are unchanged.
  isLegacyLabel?: boolean;
};

const CHART_WIDTH = 640;
const CHART_HEIGHT = 200;
const PADDING_X = 32;
const PADDING_TOP = 20;
const PADDING_BOTTOM = 28;

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function SPSHistory({ history, isLegacyLabel = false }: SPSHistoryProps) {
  const gradientId = useId();
  const currentLabel = isLegacyLabel ? "V2.1 SPS (legacy)" : "Current SPS";

  if (history.length === 0) {
    return (
      <BaseCard className="p-6">
        <SectionHeading isLegacyLabel={isLegacyLabel} />
        <p className="mt-3 text-sm text-text-muted">
          No historical analyses yet. Run another analysis for this company
          to start tracking its SPS over time.
        </p>
      </BaseCard>
    );
  }

  const first = history[0];
  const latest = history[history.length - 1];

  if (history.length === 1) {
    return (
      <BaseCard className="p-6">
        <SectionHeading isLegacyLabel={isLegacyLabel} />

        <div className="mt-4 flex flex-wrap items-end gap-x-10 gap-y-4">
          <Stat
            label={currentLabel}
            value={latest.startup_intelligence_score.toFixed(1)}
          />
          <Stat label="Historical analyses" value="1" />
          <Stat label="Last analysis" value={formatDate(latest.created_at)} />
        </div>

        <p className="mt-4 text-sm text-text-muted">
          {isLegacyLabel
            ? "This tracks the earlier V2.1 methodology's score history, separate from the Startup Power Score assessment above."
            : "Only one canonical analysis exists for this company — a trend will appear once a second analysis is recorded."}
        </p>
      </BaseCard>
    );
  }

  const change =
    latest.startup_intelligence_score - first.startup_intelligence_score;
  const changeTone = change > 0 ? "success" : change < 0 ? "danger" : "neutral";

  return (
    <BaseCard className="p-6">
      <SectionHeading isLegacyLabel={isLegacyLabel} />

      <div className="mt-4 flex flex-wrap items-end gap-x-10 gap-y-4">
        <Stat
          label={currentLabel}
          value={latest.startup_intelligence_score.toFixed(1)}
        />

        <Stat
          label="Change from first"
          value={`${change > 0 ? "+" : ""}${change.toFixed(1)}`}
          tone={changeTone}
        />

        <Stat label="Historical analyses" value={String(history.length)} />
        <Stat label="Last analysis" value={formatDate(latest.created_at)} />
      </div>

      {isLegacyLabel ? (
        <p className="mt-2 text-xs text-text-muted">
          This chart tracks the earlier V2.1 methodology&rsquo;s score history, separate from the
          Startup Power Score assessment above.
        </p>
      ) : null}

      <div className="mt-6">
        <SPSLineChart history={history} gradientId={gradientId} />
      </div>
    </BaseCard>
  );
}

function SectionHeading({ isLegacyLabel }: { isLegacyLabel: boolean }) {
  return (
    <h2 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
      {isLegacyLabel ? "V2.1 SPS History" : "SPS History"}
    </h2>
  );
}

function Stat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "success" | "danger" | "neutral";
}) {
  const toneClass =
    tone === "success"
      ? "text-success"
      : tone === "danger"
      ? "text-danger"
      : "text-text-primary";

  return (
    <div>
      <p className="text-[11px] font-medium uppercase tracking-wide text-text-muted">
        {label}
      </p>
      <p className={["mt-0.5 text-xl font-bold", toneClass].join(" ")}>
        {value}
      </p>
    </div>
  );
}

function SPSLineChart({
  history,
  gradientId,
}: {
  history: SPSHistoryPoint[];
  gradientId: string;
}) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const times = history.map((point) => new Date(point.created_at).getTime());
  const scores = history.map((point) => point.startup_intelligence_score);

  const minTime = Math.min(...times);
  const maxTime = Math.max(...times);
  const timeRange = maxTime - minTime || 1;

  const rawMin = Math.min(...scores);
  const rawMax = Math.max(...scores);
  const scorePadding = Math.max((rawMax - rawMin) * 0.15, 3);
  const yMin = Math.max(0, Math.floor(rawMin - scorePadding));
  const yMax = Math.min(100, Math.ceil(rawMax + scorePadding));
  const yRange = yMax - yMin || 1;

  const plotWidth = CHART_WIDTH - PADDING_X * 2;
  const plotHeight = CHART_HEIGHT - PADDING_TOP - PADDING_BOTTOM;
  const baselineY = PADDING_TOP + plotHeight;

  function xFor(time: number) {
    return PADDING_X + ((time - minTime) / timeRange) * plotWidth;
  }

  function yFor(score: number) {
    return PADDING_TOP + plotHeight - ((score - yMin) / yRange) * plotHeight;
  }

  const points = history.map((point, index) => ({
    x: xFor(new Date(point.created_at).getTime()),
    y: yFor(point.startup_intelligence_score),
    point,
    index,
  }));

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");

  const areaPath =
    `${linePath} ` +
    `L${points[points.length - 1].x.toFixed(1)},${baselineY.toFixed(1)} ` +
    `L${points[0].x.toFixed(1)},${baselineY.toFixed(1)} Z`;

  const maxLabels = 6;
  const labelStep = Math.max(1, Math.ceil(points.length / maxLabels));
  const active = activeIndex !== null ? points[activeIndex] : null;

  return (
    <div className="relative">
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        className="w-full"
        role="img"
        aria-label={`SPS history chart, ${history.length} analyses, current score ${history[
          history.length - 1
        ].startup_intelligence_score.toFixed(1)}`}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.18" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {[0, 0.5, 1].map((fraction) => {
          const y = PADDING_TOP + plotHeight * fraction;
          return (
            <line
              key={fraction}
              x1={PADDING_X}
              x2={CHART_WIDTH - PADDING_X}
              y1={y}
              y2={y}
              className="stroke-border"
              strokeWidth={1}
            />
          );
        })}

        <text x={2} y={PADDING_TOP + 3} className="fill-text-muted text-[9px]">
          {yMax}
        </text>
        <text x={2} y={baselineY + 3} className="fill-text-muted text-[9px]">
          {yMin}
        </text>

        <path d={areaPath} fill={`url(#${gradientId})`} stroke="none" />

        <path
          d={linePath}
          fill="none"
          className="stroke-primary"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {points
          .filter((p) => p.index % labelStep === 0 || p.index === points.length - 1)
          .map(({ x, point, index }) => (
            <text
              key={index}
              x={x}
              y={CHART_HEIGHT - 8}
              textAnchor="middle"
              className="fill-text-muted text-[9px]"
            >
              {formatShortDate(point.created_at)}
            </text>
          ))}

        {points.map(({ x, y, point, index }) => {
          const isLatest = index === points.length - 1;
          const isActive = activeIndex === index;

          return (
            <g key={point.analysis_id}>
              {isActive || isLatest ? (
                <circle cx={x} cy={y} r={isLatest ? 9 : 7} className="fill-primary/15" />
              ) : null}

              <circle
                cx={x}
                cy={y}
                r={isLatest ? 5 : 3.5}
                strokeWidth={isLatest ? 0 : 1.5}
                className={isLatest ? "fill-primary" : "fill-surface stroke-primary"}
              />

              <circle
                cx={x}
                cy={y}
                r={12}
                fill="transparent"
                tabIndex={0}
                role="img"
                aria-label={`${formatDate(point.created_at)}: SPS ${point.startup_intelligence_score.toFixed(
                  1
                )}`}
                onMouseEnter={() => setActiveIndex(index)}
                onMouseLeave={() => setActiveIndex(null)}
                onFocus={() => setActiveIndex(index)}
                onBlur={() => setActiveIndex(null)}
                className="cursor-pointer outline-none"
              />
            </g>
          );
        })}
      </svg>

      {active ? (
        <div
          className="pointer-events-none absolute -translate-x-1/2 -translate-y-full rounded-lg border border-border bg-surface-elevated px-2.5 py-1.5 text-xs whitespace-nowrap shadow-lg"
          style={{
            left: `${(active.x / CHART_WIDTH) * 100}%`,
            top: `${(active.y / CHART_HEIGHT) * 100}%`,
            marginTop: -8,
          }}
        >
          <p className="font-semibold text-text-primary">
            {active.point.startup_intelligence_score.toFixed(1)}
          </p>
          <p className="text-text-muted">{formatDate(active.point.created_at)}</p>
        </div>
      ) : null}
    </div>
  );
}
