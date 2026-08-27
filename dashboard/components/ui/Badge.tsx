import type { ReactNode } from "react";

// Design System V2 (Phase 10.4), Part 6. Generalizes the soft-pill
// pattern ProvenanceBadge.tsx already established (rounded-full, soft
// token background + solid token text, small type) into a shared
// primitive -- for stage/industry/status/provenance/confidence metadata
// across the app. ProvenanceBadge itself is left as-is (it carries
// specific, reviewed copy for Idea Lab's provenance states) rather than
// migrated, per this phase's "limited migration" boundary.
//
// "confidence" is its own tone group, not reused success/warning/text-
// muted directly, so a future design change to what "medium confidence"
// looks like doesn't also silently change what a "warning" badge looks
// like elsewhere -- see the movement-*/confidence-* token aliases added
// to globals.css this phase.
export type BadgeTone =
  | "neutral"
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "confidence-high"
  | "confidence-medium"
  | "confidence-low";

const TONE_CLASSES: Record<BadgeTone, string> = {
  neutral: "bg-surface-muted text-text-secondary",
  primary: "bg-primary-soft text-primary",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  danger: "bg-danger-soft text-danger",
  info: "bg-info-soft text-info",
  "confidence-high": "bg-success-soft text-confidence-high",
  "confidence-medium": "bg-warning-soft text-confidence-medium",
  "confidence-low": "bg-surface-muted text-confidence-low",
};

type BadgeProps = {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
};

export default function Badge({ tone = "neutral", children, className = "" }: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold",
        TONE_CLASSES[tone],
        className,
      ].join(" ")}
    >
      {children}
    </span>
  );
}

// Maps SIE's own three confidence levels directly to a tone -- the one
// place that mapping lives, so "medium" always means the same badge
// wherever confidence is shown.
export function confidenceBadgeTone(confidence: string): BadgeTone {
  const normalized = confidence.toLowerCase();

  if (normalized === "high") return "confidence-high";
  if (normalized === "low") return "confidence-low";
  return "confidence-medium";
}
