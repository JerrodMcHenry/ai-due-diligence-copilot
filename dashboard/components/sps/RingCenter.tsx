type RingCenterProps = {
  // Phase 10.9, Part 15: null renders "—" (never "0.0") plus
  // unavailableLabel underneath -- an unavailable score must be visually
  // unmistakable from a real, low, legitimately-scored one.
  score: number | null;
  unavailableLabel?: string;
  label?: string;
  grade?: string;
  compact?: boolean;
};

export default function RingCenter({
  score,
  unavailableLabel,
  label,
  grade,
  compact = false,
}: RingCenterProps) {
  if (score === null) {
    if (compact) {
      return (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold tracking-tight text-text-muted">—</span>
        </div>
      );
    }

    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-4">
        <span className="text-5xl font-bold tracking-tight text-text-muted">—</span>
        <span className="mt-1 text-sm font-medium text-text-secondary">SPS</span>
        {unavailableLabel ? (
          <span className="mt-2 text-xs text-text-muted">{unavailableLabel}</span>
        ) : null}
      </div>
    );
  }

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
