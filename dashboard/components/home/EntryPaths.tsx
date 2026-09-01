import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";

// Phase 10.10 -- Founder Journey Integration, Part 4/16. Replaces the
// old two-CTA pair (ThreePaths.tsx's own "Analyze a startup" card AND
// AnalyzeCallout.tsx, a second section further down the page pointing at
// the exact same /analyze route with overlapping copy) with distinct
// entry points, one per Part 4's own stated visitor. Every link still
// goes straight into an EXISTING route -- no new pages, no new logic,
// same discipline the old ThreePaths already established. AnalyzeCallout.tsx
// is deleted; nothing it did isn't covered here.
//
// Phase 15 -- Founder Beta Surface Audit, Part 14/24: the fourth path
// ("I want inspiration" -> "Explore startups" -> /rankings) was removed
// here, not deleted as a route -- /rankings itself is untouched and
// still fully reachable by direct URL. The live discovery dataset it
// promised ("Browse startup profiles, rankings, compare companies") is
// currently a single row named "Unknown" (verified via GET /rankings
// during this phase's audit); leading a brand-new Founder Beta visitor
// there from the homepage's own primary entry grid would undercut the
// exact trust this page exists to build. Restore this path once the
// dataset is credible.
type Path = {
  eyebrow: string;
  title: string;
  description: string;
  cta: string;
  href: string;
  icon: React.ReactNode;
};

const PATHS: Path[] = [
  {
    eyebrow: "I have an idea",
    title: "Build an idea",
    description:
      "Model a startup, explore assumptions, run what-if scenarios, and turn uncertainty into a plan.",
    cta: "Start building",
    href: "/idea-lab",
    icon: (
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-6">
        <path
          d="M12 3l2.4 5.3 5.6.6-4.2 3.9 1.2 5.6L12 15.8l-5 2.6 1.2-5.6-4.2-3.9 5.6-.6L12 3z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    eyebrow: "I already have a startup",
    title: "Analyze my startup",
    description:
      "Analyze your company information or website and get a structured Startup Profile.",
    cta: "Analyze my startup",
    href: "/analyze",
    icon: (
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-6">
        <path d="M12 3v4M12 17v4M3 12h4M17 12h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeWidth="1.8" />
      </svg>
    ),
  },
  {
    eyebrow: "I have a pitch deck",
    title: "Review my pitch deck",
    description:
      "Upload a PDF deck and get coaching on the story it tells, what's working, and what to fix first.",
    cta: "Review my deck",
    href: "/analyze/deck",
    icon: (
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-6">
        <rect x="4" y="3" width="16" height="18" rx="2" stroke="currentColor" strokeWidth="1.6" />
        <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
  },
];

export default function EntryPaths() {
  return (
    <section>
      <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Where do you want to start?
      </h2>

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {PATHS.map((path) => (
          <Link key={path.href} href={path.href} className="group block">
            <BaseCard
              variant="raised"
              className="flex h-full flex-col p-6 transition-transform group-hover:-translate-y-1"
            >
              <div className="flex size-11 items-center justify-center rounded-2xl bg-primary-soft text-primary">
                {path.icon}
              </div>

              <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-text-muted">
                {path.eyebrow}
              </p>

              <p className="mt-1.5 text-lg font-bold text-text-primary">{path.title}</p>

              <p className="mt-2 flex-1 text-sm leading-6 text-text-secondary">
                {path.description}
              </p>

              <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-primary">
                {path.cta}
                <span aria-hidden="true" className="transition-transform group-hover:translate-x-1">
                  →
                </span>
              </span>
            </BaseCard>
          </Link>
        ))}
      </div>
    </section>
  );
}
