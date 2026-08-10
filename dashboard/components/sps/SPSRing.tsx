import RingCenter from "./RingCenter";
import RingSVG from "./RingSVG";
import { getSPSMetadata, normalizeSPS } from "./utils/scoreMetadata";

import type { SPSRingProps } from "./types";

const SIZE_CONFIG = {
  xs: {
    diameter: 56,
    strokeWidth: 5,
  },
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
  ariaLabel,
}: SPSRingProps) {
  const normalizedScore = normalizeSPS(score);
  const config = SIZE_CONFIG[size];
  const metadata = getSPSMetadata(normalizedScore);

  const resolvedGrade = grade ?? metadata.grade;
  const resolvedLabel = label ?? metadata.label;

  return (
    <div className="flex flex-col items-center">
      <div
        className={[
          "relative flex items-center justify-center rounded-full",
          "transition-transform duration-300 ease-out",
          "hover:scale-[1.02]",
          metadata.glowClass,
        ]
          .filter(Boolean)
          .join(" ")}
        style={{
          width: config.diameter,
          height: config.diameter,
        }}
        role="img"
        aria-label={
          ariaLabel ??
          `Startup Power Score ${normalizedScore.toFixed(1)} out of 100`
        }
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
          compact={size === "xs"}
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
