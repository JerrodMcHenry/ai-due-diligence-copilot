import RingCenter from "./RingCenter";
import RingSVG from "./RingSVG";

import type { SPSRingProps } from "./types";

const SIZE_CONFIG = {
  sm: {
    diameter: 120,
    strokeWidth: 10,
  },
  md: {
    diameter: 170,
    strokeWidth: 12,
  },
  lg: {
    diameter: 220,
    strokeWidth: 16,
  },
  xl: {
    diameter: 280,
    strokeWidth: 18,
  },
} as const;

function getGrade(score: number) {
  if (score >= 95) return "A+";
  if (score >= 90) return "A";
  if (score >= 85) return "A−";
  if (score >= 80) return "B+";
  if (score >= 75) return "B";
  if (score >= 70) return "B−";
  if (score >= 65) return "C+";
  if (score >= 60) return "C";
  if (score >= 50) return "D";
  return "F";
}

function getScoreLabel(score: number) {
  if (score >= 90) return "Exceptional";
  if (score >= 80) return "Excellent";
  if (score >= 70) return "Strong";
  if (score >= 60) return "Promising";
  if (score >= 40) return "Developing";
  return "Needs attention";
}

export default function SPSRing({
  score,
  trend,
  percentile,
  confidence,
  grade,
  label,
  size = "lg",
  animated = true,
  showDetails = true,
}: SPSRingProps) {
  const normalizedScore = Math.max(0, Math.min(score, 100));
  const config = SIZE_CONFIG[size];

  const resolvedGrade = grade ?? getGrade(normalizedScore);
  const resolvedLabel = label ?? getScoreLabel(normalizedScore);

  return (
    <div className="flex flex-col items-center">
      <div
        className="relative flex items-center justify-center"
        style={{
          width: config.diameter,
          height: config.diameter,
        }}
        role="img"
        aria-label={`Startup Power Score ${normalizedScore.toFixed(
          1
        )} out of 100`}
      >
        <RingSVG
          score={normalizedScore}
          size={config.diameter}
          strokeWidth={config.strokeWidth}
          animated={animated}
        />

        <RingCenter
          score={normalizedScore}
          grade={showDetails ? resolvedGrade : undefined}
          label={showDetails ? resolvedLabel : undefined}
        />
      </div>

      {showDetails ? (
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
          {trend !== undefined ? (
            <span
              className={[
                "rounded-full px-3 py-1 text-xs font-semibold",
                trend > 0
                  ? "bg-success/10 text-success"
                  : trend < 0
                  ? "bg-danger/10 text-danger"
                  : "bg-surface-muted text-text-secondary",
              ].join(" ")}
            >
              {trend > 0 ? "▲" : trend < 0 ? "▼" : "—"}{" "}
              {Math.abs(trend).toFixed(1)}
            </span>
          ) : null}

          {percentile !== undefined ? (
            <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              Top {percentile}%
            </span>
          ) : null}

          {confidence ? (
            <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-text-secondary">
              {confidence} confidence
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
