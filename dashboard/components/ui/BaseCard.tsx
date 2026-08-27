import type { HTMLAttributes, ReactNode } from "react";

// Design System V2 (Phase 10.4), Part 6: added `variant` -- three surfaces
// (Part 6: "not ten card variants"), not a rewrite. `variant` defaults to
// "default", whose className is byte-for-byte the same string this
// component always returned, so every one of the 30 existing BaseCard
// call sites across dashboard/ renders identically, unchanged.
export type BaseCardVariant = "default" | "raised" | "subtle";

const VARIANT_CLASSES: Record<BaseCardVariant, string> = {
  default: "rounded-2xl border border-border bg-surface shadow-sm",
  raised: "rounded-2xl border border-border bg-surface-raised shadow-md",
  subtle: "rounded-2xl border border-border bg-surface-subtle",
};

type BaseCardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
  variant?: BaseCardVariant;
};

export default function BaseCard({
  children,
  className = "",
  variant = "default",
  ...props
}: BaseCardProps) {
  return (
    <div className={[VARIANT_CLASSES[variant], className].join(" ")} {...props}>
      {children}
    </div>
  );
}
