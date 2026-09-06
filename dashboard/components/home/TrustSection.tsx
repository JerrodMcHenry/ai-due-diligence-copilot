import BaseCard from "@/components/ui/BaseCard";

// Phase 10.5, Part 11. Below the excitement, not leading with it -- no
// methodology name, no version string, just the one distinction that
// matters for credibility: a modeled idea is not the same thing as a
// real company's evidence-based intelligence. This is the same
// distinction VPSResultPanel/ScoreDisplay already enforce in the product
// itself (see Design System V2, Part 7); this section just states it in
// plain language before someone reaches either screen.
export default function TrustSection() {
  return (
    <section className="mx-auto max-w-4xl">
      <h2 className="text-center text-xl font-bold text-text-primary sm:text-2xl">
        Imagination and evidence are not the same thing
      </h2>

      <div className="mt-8 grid gap-5 sm:grid-cols-2">
        <BaseCard variant="subtle" className="p-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-warning">
            Modeled ideas
          </p>
          {/* Phase 31C-C, Part 1/3: this is the load-bearing explanation of
              a distinction the whole product depends on a visitor
              understanding correctly -- bumped to the 16px floor. */}
          <p className="mt-2 text-base leading-7 text-text-secondary">
            When you build an idea, SIE reasons from your assumptions — not
            observed evidence. It&rsquo;s a tool for thinking, never
            presented as a real company&rsquo;s score.
          </p>
        </BaseCard>

        <BaseCard variant="subtle" className="p-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-success">
            Real startups
          </p>
          <p className="mt-2 text-base leading-7 text-text-secondary">
            When SIE analyzes an actual company, it builds structured
            startup intelligence from real evidence — public information,
            pitch decks, and company data.
          </p>
        </BaseCard>
      </div>
    </section>
  );
}
