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
    <section className="mx-auto max-w-4xl">
      <p className="text-center text-sm font-medium text-text-muted">
        Every idea gets modeled across six categories
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {CATEGORIES.map((category) => (
          <BaseCard key={category.label} variant="subtle" className="p-5">
            <p className="text-sm font-semibold text-text-primary">{category.label}</p>
            {/* Global readability audit: bumped from text-xs/text-muted --
                muted text on this card's own muted surface (variant
                "subtle") was a genuine low-contrast combination, not just
                a small-text one -- text-secondary reads clearly against
                the same background in both themes. */}
            <p className="mt-1 text-sm leading-6 text-text-secondary">{category.description}</p>
          </BaseCard>
        ))}
      </div>
    </section>
  );
}
