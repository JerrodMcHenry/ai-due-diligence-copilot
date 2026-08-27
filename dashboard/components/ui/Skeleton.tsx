// Design System V2 (Phase 10.4), Part 6. Every loading state in the app
// currently hand-rolls its own `animate-pulse rounded-xl border ...`
// block (31 occurrences of animate-pulse across dashboard/, none sharing
// a component) -- often with hardcoded slate/border colors (e.g.
// AnalyzeStartupForm.tsx's `border-slate-800 bg-slate-900`), which is
// exactly the kind of dark-only shell bug Phase 10.3 already had to fix
// once at the nav level. This is the one place that pattern should live.
type SkeletonProps = {
  className?: string;
};

export function Skeleton({ className = "h-24 w-full" }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={["animate-pulse rounded-xl border border-border bg-surface-subtle", className].join(" ")}
    />
  );
}

// A few stacked lines -- the common case for "a card's worth of text is
// still loading" (used in place of a full custom skeleton layout when the
// caller doesn't need one).
export function SkeletonLines({ count = 3, className = "" }: { count?: number; className?: string }) {
  return (
    <div className={["space-y-2", className].join(" ")} aria-hidden="true">
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="h-3 animate-pulse rounded-full bg-surface-subtle"
          style={{ width: index === count - 1 ? "60%" : "100%" }}
        />
      ))}
    </div>
  );
}

export default Skeleton;
