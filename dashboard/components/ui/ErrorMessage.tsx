import type { ReactNode } from "react";

// Design System V2 (Phase 10.4), Part 6. Generalizes the red-banner
// pattern repeated across AnalyzeStartupForm.tsx, ClaimStartupForm.tsx,
// and others (each with its own hardcoded `border-red-500/20 bg-red-500/10
// text-red-300`, dark-only) into one token-driven primitive. Human-
// readable, recoverable: an optional `action` slot for exactly the kind
// of "sign in again" / "go back" recovery link these forms already show,
// rather than a dead-end error.
type ErrorMessageProps = {
  children: ReactNode;
  action?: ReactNode;
  className?: string;
};

export default function ErrorMessage({ children, action, className = "" }: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className={[
        "rounded-xl border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger",
        className,
      ].join(" ")}
    >
      {children}
      {action ? <span className="ml-1">{action}</span> : null}
    </div>
  );
}
