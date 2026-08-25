type CompareToggleProps = {
  selected: boolean;
  disabled?: boolean;
  onToggle: () => void;
};

// Compare Startups V1, Part 4: a small, visually secondary control --
// deliberately NOT the whole card (which stays a plain link to the
// Startup Profile). A real checkbox input, not a styled div, so it's
// natively keyboard-toggleable and announced correctly by a screen
// reader (its label already states the action; no separate aria-label
// needed beyond that).
export default function CompareToggle({
  selected,
  disabled,
  onToggle,
}: CompareToggleProps) {
  return (
    <label
      className={[
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
        selected
          ? "border-primary/40 bg-primary-soft text-primary"
          : "border-border text-text-muted hover:border-primary/30 hover:text-text-secondary",
        disabled && !selected ? "cursor-not-allowed opacity-50" : "cursor-pointer",
      ].join(" ")}
    >
      <input
        type="checkbox"
        checked={selected}
        disabled={disabled && !selected}
        onChange={onToggle}
        className="size-3.5 accent-current"
      />
      Compare
    </label>
  );
}
