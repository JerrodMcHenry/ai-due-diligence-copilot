type RingCenterProps = {
  score: number;
  label?: string;
  grade?: string;
  compact?: boolean;
};

export default function RingCenter({
  score,
  label,
  grade,
  compact = false,
}: RingCenterProps) {
  if (compact) {
    return (
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-sm font-bold tracking-tight text-text-primary">
          {score.toFixed(1)}
        </span>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
      <span className="text-5xl font-bold tracking-tight text-text-primary">
        {score.toFixed(1)}
      </span>

      <span className="mt-1 text-sm font-medium text-text-secondary">SPS</span>

      {grade ? (
        <span className="mt-2 text-sm font-semibold text-text-primary">
          {grade}
        </span>
      ) : null}

      {label ? (
        <span className="mt-1 text-xs text-text-muted">{label}</span>
      ) : null}
    </div>
  );
}
