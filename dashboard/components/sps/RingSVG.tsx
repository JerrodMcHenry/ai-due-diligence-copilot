import { getSPSMetadata, normalizeSPS } from "./utils/scoreMetadata";

type RingSVGProps = {
  // Phase 10.9, Part 15: null renders an empty, dashed track only -- no
  // colored progress arc at all. This must never be reached by silently
  // coercing null to 0 upstream (that would draw a full-danger-red empty
  // ring, visually indistinguishable from "scored zero").
  score: number | null;
  size: number;
  strokeWidth: number;
  animated?: boolean;
};

export default function RingSVG({
  score,
  size,
  strokeWidth,
  animated = true,
}: RingSVGProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  if (score === null) {
    return (
      <svg
        aria-hidden="true"
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeDasharray={`${strokeWidth} ${strokeWidth * 1.4}`}
          strokeLinecap="round"
          className="stroke-border"
        />
      </svg>
    );
  }

  const normalizedScore = normalizeSPS(score);
  const metadata = getSPSMetadata(normalizedScore);
  const strokeOffset = circumference - (normalizedScore / 100) * circumference;

  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="-rotate-90"
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        strokeWidth={strokeWidth}
        className="stroke-border"
      />

      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={strokeOffset}
        className={[
          metadata.strokeClass,
          animated
            ? "transition-[stroke-dashoffset] duration-1000 ease-out"
            : "",
        ]
          .filter(Boolean)
          .join(" ")}
      />
    </svg>
  );
}
