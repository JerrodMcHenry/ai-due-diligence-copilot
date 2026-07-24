type RingSVGProps = {
  score: number;
  size: number;
  strokeWidth: number;
  animated?: boolean;
};

function getScoreClass(score: number) {
  if (score >= 80) {
    return "stroke-success";
  }

  if (score >= 60) {
    return "stroke-primary";
  }

  if (score >= 40) {
    return "stroke-warning";
  }

  return "stroke-danger";
}

export default function RingSVG({
  score,
  size,
  strokeWidth,
  animated = true,
}: RingSVGProps) {
  const normalizedScore = Math.max(0, Math.min(score, 100));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
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
          getScoreClass(normalizedScore),
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
