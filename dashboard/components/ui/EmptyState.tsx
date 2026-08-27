import type { ReactNode } from "react";

// Design System V2 (Phase 10.4), Part 6. Generalizes the local EmptyState
// pattern already hand-rolled per-page (e.g. SavedStartupsView.tsx,
// FounderHome.tsx, CompareView.tsx) into one shared shape: an icon slot,
// a heading, an explanation, and one obvious CTA -- never more than one
// action, per Part 6's "one obvious CTA."
type EmptyStateProps = {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
};

export default function EmptyState({ icon, title, description, action, className = "" }: EmptyStateProps) {
  return (
    <div
      className={[
        "flex flex-col items-center rounded-2xl border border-dashed border-border bg-surface-subtle px-6 py-14 text-center",
        className,
      ].join(" ")}
    >
      {icon ? (
        <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-primary-soft text-primary">
          {icon}
        </div>
      ) : null}

      <h3 className="text-lg font-semibold text-text-primary">{title}</h3>

      {description ? (
        <p className="mt-2 max-w-sm text-sm leading-6 text-text-secondary">{description}</p>
      ) : null}

      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}
