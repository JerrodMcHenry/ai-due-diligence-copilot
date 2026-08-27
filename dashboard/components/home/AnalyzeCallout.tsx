import Link from "next/link";

import BaseCard from "@/components/ui/BaseCard";
import Button from "@/components/ui/Button";

// Phase 10.5, Part 8. Links straight into the EXISTING /analyze
// experience -- no upload implementation on Home itself, this is purely
// a callout + CTA.
export default function AnalyzeCallout() {
  return (
    <section className="mx-auto max-w-4xl">
      <BaseCard variant="raised" className="flex flex-col items-center gap-6 p-8 text-center sm:flex-row sm:text-left">
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Already building?
          </p>

          <p className="mt-2 text-xl font-bold text-text-primary">
            Analyze your startup or pitch deck
          </p>

          <p className="mt-2 text-sm leading-6 text-text-secondary">
            If you&rsquo;re already running a company, SIE can analyze your
            company information or pitch deck and build a full, structured
            Startup Profile — the same intelligence investors and founders
            use across the platform.
          </p>
        </div>

        <Link href="/analyze" className="shrink-0">
          <Button size="lg" variant="secondary">
            Analyze My Startup
          </Button>
        </Link>
      </BaseCard>
    </section>
  );
}
