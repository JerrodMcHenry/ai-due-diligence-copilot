import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";

// Phase 10.5, Part 5. Three strong pathways, not a feature grid -- each
// one links straight into an EXISTING route (no new pages, no new logic):
// Build -> /idea-lab, Analyze -> /analyze, Explore -> /rankings (the same
// primary Explore destination TopNav already uses -- see Phase 10.3's
// PRIMARY_NAVIGATION). Three items only, matching TopNav's own Explore/
// Build/Analyze vocabulary so Home and the shell nav reinforce the same
// mental model rather than introducing a fourth, different taxonomy.
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
    eyebrow: "For aspiring founders",
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
    eyebrow: "For founders already building",
    title: "Analyze a startup",
    description:
      "Analyze company information or a pitch deck and get structured startup intelligence.",
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
    eyebrow: "For investors, students & the curious",
    title: "Explore startups",
    description:
      "Browse startup profiles, rankings, compare companies, and understand what drives their scores.",
    cta: "Explore startups",
    href: "/rankings",
    icon: (
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="size-6">
        <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.8" />
        <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    ),
  },
];

export default function ThreePaths() {
  return (
    <section>
      <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Three ways in
      </h2>

      <div className="mt-8 grid gap-5 md:grid-cols-3">
        {PATHS.map((path) => (
          <Link key={path.href} href={path.href} className="group block">
            <BaseCard
              variant="raised"
              className="flex h-full flex-col p-7 transition-transform group-hover:-translate-y-1"
            >
              <div className="flex size-12 items-center justify-center rounded-2xl bg-primary-soft text-primary">
                {path.icon}
              </div>

              <p className="mt-5 text-xs font-semibold uppercase tracking-wide text-text-muted">
                {path.eyebrow}
              </p>

              <p className="mt-1.5 text-xl font-bold text-text-primary">{path.title}</p>

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
