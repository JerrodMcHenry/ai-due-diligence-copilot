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
//
// Phase 32 -- Product Information Architecture + Seamless User Journey,
// Part 6. Rebuilt around USER INTENT rather than product artifacts, per
// the directive's own exact recommended structure:
//   "I have a pitch deck" / "Review my pitch deck" is deliberately no
//   longer a co-equal third card here -- the directive's own instruction
//   is that pitch deck review "should not necessarily compete as an
//   equal top-level lifecycle state." It's still fully reachable (Part
//   16's own "hide, don't delete" precedent) via the small link below
//   the three cards instead, subordinate rather than competing.
const PATHS = [
  {
    eyebrow: "I have an idea",
    title: "Explore an Idea",
    description:
      "Model something you're considering and determine what would make it stronger — before you build anything.",
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
    eyebrow: "I'm building a startup",
    title: "Work on My Startup",
    description:
      "Continue validating, building, fundraising, and improving a startup you're actually pursuing.",
    cta: "My startups",
    href: "/founder",
    icon: (
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-6">
        <path d="M4 21V9l8-6 8 6v12" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        <path d="M9 21v-6h6v6" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    eyebrow: "I want SIE to evaluate a company",
    title: "Analyze a Company",
    description:
      "Build an evidence-based Startup Profile from a company's website, pitch deck, or public information.",
    cta: "Analyze",
    href: "/analyze",
    icon: (
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-6">
        <path d="M12 3v4M12 17v4M3 12h4M17 12h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeWidth="1.8" />
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

              <p className="mt-4 text-sm font-semibold uppercase tracking-wide text-text-secondary">
                {path.eyebrow}
              </p>

              <p className="mt-1.5 text-lg font-bold text-text-primary">{path.title}</p>

              <p className="mt-2 flex-1 text-base leading-6 text-text-secondary">
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

      {/* Part 6: pitch deck review kept fully reachable, deliberately
          subordinate to the three primary journeys above rather than a
          fourth equal-weight card. */}
      <p className="mt-6 text-center text-base text-text-secondary">
        Have a pitch deck instead?{" "}
        <Link href="/analyze/deck" className="font-semibold text-primary hover:underline">
          Get it reviewed →
        </Link>
      </p>
    </section>
  );
}
