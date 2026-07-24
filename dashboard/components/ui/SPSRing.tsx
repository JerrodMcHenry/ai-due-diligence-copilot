type SPSRingProps = {
  score: number;
  size?: number;
  strokeWidth?: number;
};

export default function SPSRing({
  score,
  size = 220,
  strokeWidth = 16,
}: SPSRingProps) {
  const normalizedScore = Math.max(0, Math.min(score, 100));

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const offset = circumference - (normalizedScore / 100) * circumference;

  return (
    <div
      className="relative flex items-center justify-center"
      style={{
        width: size,
        height: size,
      }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          className="stroke-border"
          strokeWidth={strokeWidth}
        />

        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          className="stroke-primary transition-all duration-1000"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>

      <div className="absolute flex flex-col items-center">
        <span className="text-5xl font-bold">{normalizedScore.toFixed(1)}</span>

        <span className="mt-1 text-sm text-text-secondary">SPS</span>
      </div>
    </div>
  );
}
