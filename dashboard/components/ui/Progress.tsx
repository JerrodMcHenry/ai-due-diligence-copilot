// Design System V2 (Phase 10.4), Part 6. Generalizes the "Goal 80 SPS"
// progress bar already on the Home dashboard (app/page.tsx) into a
// shared primitive -- for venture completion, action completion, and
// modeled-category fill (Part 6/9). Deliberately just a filled track:
// no percentage-as-probability framing, no implied confidence interval --
// "progress" here always means "share of a known total reached," which is
// the only thing this component is allowed to represent (Part 9: do not
// manufacture progress the caller doesn't actually have).
export type ProgressTone = "primary" | "success" | "warning";

const TONE_CLASSES: Record<ProgressTone, string> = {
  primary: "bg-primary",
  success: "bg-success",
  warning: "bg-warning",
};

type ProgressProps = {
  value: number;
  max?: number;
  tone?: ProgressTone;
  label?: string;
  valueLabel?: string;
  className?: string;
};

export default function Progress({
  value,
  max = 100,
  tone = "primary",
  label,
  valueLabel,
  className = "",
}: ProgressProps) {
  const clamped = Math.max(0, Math.min(value, max));
  const percent = max > 0 ? (clamped / max) * 100 : 0;

  return (
    <div className={className}>
      {label || valueLabel ? (
        <div className="mb-2 flex items-center justify-between text-xs font-medium text-text-secondary">
          {label ? <span>{label}</span> : <span />}
          {valueLabel ? <span>{valueLabel}</span> : null}
        </div>
      ) : null}

      <div
        role="progressbar"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={max}
        className="h-3 overflow-hidden rounded-full bg-border"
      >
        <div
          className={["h-full rounded-full transition-all duration-700", TONE_CLASSES[tone]].join(" ")}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
