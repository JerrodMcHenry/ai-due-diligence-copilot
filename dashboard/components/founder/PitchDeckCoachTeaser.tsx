import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";

// Phase 10.10 -- Founder Journey Integration, Part 9/10. A small, static
// sibling to FundraisingReadinessCard -- together they read as ONE
// "prepare to raise" pair (pitch + readiness) rather than Pitch Deck
// Coach being an isolated, undiscoverable utility. Deliberately no data
// fetch (unlike FundraisingReadinessCard, there is no canonical-startup
// deck review to summarize -- Pitch Deck Coach reviews are
// ownership-scoped to the founder's OWN account, not this specific
// startup, per Phase 10.8's own isolation boundary) -- this never infers
// or displays deck quality here, only invites the founder to go review one.
export default function PitchDeckCoachTeaser() {
  return (
    <Link href="/analyze/deck" className="group block">
      <BaseCard className="flex h-full flex-wrap items-center justify-between gap-4 p-5 transition-colors group-hover:border-primary">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Preparing to raise?
          </p>
          <p className="mt-1 text-base font-semibold text-text-primary">Review your pitch deck</p>
          <p className="mt-1 text-sm text-text-muted">
            Get coaching on the story it tells and what to fix first.
          </p>
        </div>

        <span className="inline-flex shrink-0 items-center gap-1.5 text-sm font-semibold text-primary">
          Review deck
          <span aria-hidden="true" className="transition-transform group-hover:translate-x-0.5">→</span>
        </span>
      </BaseCard>
    </Link>
  );
}
