import BaseCard from "@/components/ui/BaseCard";

// Phase 10.5, Part 4. "Visually communicate what happens after entering
// an idea... prefer showing category structure over fake numbers." This
// deliberately shows ONLY the six VPS category names + one-line
// descriptions -- no progress bars, no numbers, no fabricated score for
// a fictional company. Anyone who later sees a REAL VentureDraftReview or
// VPSResultPanel screen will recognize these exact six categories, so
// this sets accurate expectations rather than a stylized preview that
// could be mistaken for a real (or fake) result.
const CATEGORIES = [
  { label: "Market Potential", description: "How big is the opportunity, really?" },
  { label: "Problem & Solution", description: "Is the problem real, and does the solution fit?" },
  { label: "Founder Readiness", description: "What relevant experience do you bring?" },
  { label: "Reaching Customers", description: "Can you actually reach these customers?" },
  { label: "Economic Potential", description: "Could this become a real business?" },
  { label: "Validation", description: "What evidence backs up your assumptions?" },
];

export default function VisualPayoff() {
  return (
    // Phase 31C-C -- Global Visual Scale + Readability Correction, Part 2/3:
    // widened max-w-4xl -> max-w-5xl -- at a normal desktop width this
    // section previously used ~900px of a 1300px+ available column,
    // compounding with 14px card text to read as a small island in a big
    // canvas. Wider container + larger card text (below) fixes both at
    // once rather than just the text.
    <section className="mx-auto max-w-5xl">
      <p className="text-center text-base font-medium text-text-secondary">
        Every idea gets modeled across six categories
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CATEGORIES.map((category) => (
          <BaseCard key={category.label} variant="subtle" className="p-6">
            <p className="text-base font-semibold text-text-primary">{category.label}</p>
            {/* Part 1: this is reading content, not metadata -- bumped to
                the new 16px body-copy floor (was 14px). */}
            <p className="mt-1.5 text-base leading-6 text-text-secondary">{category.description}</p>
          </BaseCard>
        ))}
      </div>
    </section>
  );
}
