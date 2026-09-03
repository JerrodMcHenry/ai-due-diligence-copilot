import PlaybookLink from "@/components/playbooks/PlaybookLink";
import { getMetricConcept } from "@/content/concepts";

// Learn V1, Part 14/19. The one reusable "what is this term?" trigger
// used everywhere a metric concept (CAC, gross margin, retention,
// burn -- content/concepts/data.ts::METRIC_CONCEPTS) shows up next to a
// real field or What If scenario.
//
// Deliberately a bespoke, minimal <details>/<summary> here rather than
// reusing components/ui/Disclosure -- that component's bordered-card
// chrome (rounded-2xl border, px-5 py-4) is right for a section-level
// disclosure ("Edit the full model", "Venture history") but would be
// visually heavy stacked under every single CAC/margin/retention/burn
// field, exactly the "visually noisy" input Part 14 warns against. This
// keeps the SAME accessible primitive (a native <details>, keyboard- and
// tap-operable with no custom ARIA, satisfying Part 20 identically) at a
// weight proportionate to one small field. Renders nothing (not even a
// wrapper) when the key doesn't resolve, so a caller can pass a concept
// key unconditionally without an extra existence check at every call
// site.
//
// Layer 1 (whatIsThis) + Layer 2 (whyItMatters) + a deterministic,
// value-driven personalization line (Part 10/11) + an optional Layer 3
// Playbook link (Part 3) -- exactly the three layers Part 3 defines, and
// nothing else: no score, no mutation, no history event (Part 17/18).
type ConceptDisclosureProps = {
  conceptKey: string;
  // The field's own current value, exactly as already held by the
  // caller -- no extra fetch, no derived read. `undefined` (field not
  // applicable to this call site) is treated the same as `null`
  // (Unknown) for personalization purposes.
  value?: number | null;
  className?: string;
};

export default function ConceptDisclosure({ conceptKey, value = null, className = "" }: ConceptDisclosureProps) {
  const concept = getMetricConcept(conceptKey);
  if (!concept) {
    return null;
  }

  return (
    <details className={["group mt-1.5", className].join(" ")}>
      <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-xs font-semibold text-primary marker:content-none hover:text-primary-hover">
        What&rsquo;s this?
        <span aria-hidden="true" className="text-text-muted transition-transform group-open:rotate-180">▾</span>
      </summary>

      <div className="mt-1.5 space-y-2 rounded-lg border border-border bg-surface-muted p-3 text-xs leading-5 text-text-secondary">
        <p>{concept.whatIsThis}</p>
        <p>{concept.whyItMatters}</p>
        <p className="font-medium text-text-primary">{concept.personalize(value)}</p>
        {concept.playbookSlug ? <PlaybookLink slug={concept.playbookSlug} className="pt-1" /> : null}
      </div>
    </details>
  );
}
