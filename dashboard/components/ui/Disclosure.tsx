import type { ReactNode } from "react";

// Design System V2 (Phase 10.4), Part 6. Extracts the native
// <details>/<summary> progressive-disclosure pattern PillarDetailAccordion
// already established (components/compare/PillarDetailAccordion.tsx) into
// a reusable primitive -- zero-JS, fully keyboard-operable, screen-reader
// announced with no custom ARIA needed. This is the "headline insight ->
// explanation -> deeper evidence" shape Part 2's progressive-disclosure
// principle asks for: `summary` is the headline, `children` is everything
// underneath it, collapsed by default.
//
// PillarDetailAccordion itself is left using its own inline <details>
// markup rather than migrated onto this -- it already works, and Part 12
// scopes this phase to proving the primitive, not re-touching every
// existing disclosure in the app.
type DisclosureProps = {
  summary: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
  // Phase 10.10, Part 5: lets a caller link/scroll straight to a specific
  // Disclosure (e.g. a "what should I do next?" card pointing at "Edit
  // the full model") without inventing a second wrapper element.
  id?: string;
};

export default function Disclosure({ summary, children, defaultOpen = false, className = "", id }: DisclosureProps) {
  return (
    <details
      id={id}
      open={defaultOpen}
      className={["group rounded-2xl border border-border bg-surface open:pb-2", className].join(" ")}
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-sm font-semibold text-text-primary marker:content-none">
        {summary}

        <span
          aria-hidden="true"
          className="shrink-0 text-text-muted transition-transform group-open:rotate-180"
        >
          ▾
        </span>
      </summary>

      <div className="px-5 pb-4">{children}</div>
    </details>
  );
}
