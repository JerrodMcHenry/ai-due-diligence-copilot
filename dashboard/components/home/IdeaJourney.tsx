// Phase 10.5, Part 6. "SIE isn't only an idea grader -- it stays useful as
// the idea becomes a real company." A concise five-step progression, kept
// aspirational without implying any guarantee (no "get funded", no
// success framing) -- each step's description says what SIE HELPS WITH,
// never what it promises will happen.
const STEPS = [
  { label: "Idea", description: "Describe it in your own words." },
  { label: "Model", description: "SIE structures it into a venture model." },
  { label: "Validate", description: "Test assumptions, run what-if scenarios." },
  { label: "Build", description: "Track milestones and progress as a founder." },
  { label: "Fundraise", description: "Understand your fundraising readiness." },
];

export default function IdeaJourney() {
  return (
    <section>
      <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary md:text-3xl">
        From idea to startup
      </h2>

      <p className="mx-auto mt-3 max-w-xl text-center text-sm leading-6 text-text-secondary">
        SIE stays useful at every stage — not just while you&rsquo;re still
        deciding whether to start.
      </p>

      {/* Desktop: one horizontal row, circles joined by a connecting line
          running behind them. Below md: a plain vertical list -- kept as
          a genuinely separate layout rather than one DOM shape forced to
          read both ways, since a shared connector is fragile at these
          very different aspect ratios. md (768px), not sm (640px): five
          circles + labels genuinely need that much room, matching the
          same breakpoint TopNav/MobileTabBar already switch on. */}
      <div className="relative mt-10 hidden md:grid md:grid-cols-5 md:gap-4">
        <div
          aria-hidden="true"
          className="absolute left-0 right-0 top-[18px] h-px bg-border"
          style={{ marginInline: "10%" }}
        />

        {STEPS.map((step, index) => (
          <div key={step.label} className="relative flex flex-col items-center text-center">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full border-2 border-primary bg-surface text-sm font-bold text-primary">
              {index + 1}
            </span>

            <p className="mt-3 text-sm font-bold text-text-primary">{step.label}</p>
            <p className="mt-1 text-xs leading-5 text-text-muted">{step.description}</p>
          </div>
        ))}
      </div>

      <ol className="mt-10 space-y-5 md:hidden">
        {STEPS.map((step, index) => (
          <li key={step.label} className="flex items-start gap-4">
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full border-2 border-primary bg-surface text-sm font-bold text-primary">
              {index + 1}
            </span>

            <div className="pt-1">
              <p className="text-sm font-bold text-text-primary">{step.label}</p>
              <p className="mt-0.5 text-xs leading-5 text-text-muted">{step.description}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
