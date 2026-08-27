import BaseCard from "@/components/ui/BaseCard";

// Phase 10.5, Part 7. A first glimpse of scenario thinking -- NOTHING is
// calculated on this page. These are illustrative example QUESTIONS, not
// live inputs and not a preview of a real result; no numbers change, no
// outcome is fabricated. The message is entirely in the caption below the
// examples, not implied by any interactive-looking element here.
const EXAMPLE_QUESTIONS = [
  "What happens if I get 10 customer interviews?",
  "What if I charge $49/month instead of $19?",
  "What if I target SMBs instead of enterprise?",
  "What if I find 3 design partners first?",
];

export default function ScenarioExamples() {
  return (
    <section className="mx-auto max-w-3xl text-center">
      <h2 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Change the assumptions. See how the model changes.
      </h2>

      <p className="mt-3 text-sm leading-6 text-text-secondary">
        Idea Lab lets you test what-if scenarios on your own venture model —
        here&rsquo;s the kind of thinking it&rsquo;s built for.
      </p>

      <div className="mt-8 grid gap-3 sm:grid-cols-2">
        {EXAMPLE_QUESTIONS.map((question) => (
          <BaseCard key={question} variant="subtle" className="p-5 text-left">
            <p className="text-sm font-medium text-text-primary">&ldquo;{question}&rdquo;</p>
          </BaseCard>
        ))}
      </div>

      <p className="mt-6 text-xs font-semibold uppercase tracking-wide text-text-muted">
        Change the assumptions · See how the model changes · Learn what to do next
      </p>
    </section>
  );
}
