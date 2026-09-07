import type { DraftProvenance } from "@/types";

// Phase 6.1, Part 6: restrained, non-certain language -- never implies
// something is more verified than it is. "Based on your description" is
// still a paraphrase/extraction, not a guarantee of accuracy; "SIE
// assumption" is explicitly a guess for the founder to edit; "Not
// provided yet" is neutral, not a criticism.
//
// Phase 34F, Section 3: "Modeled assumption" -> "SIE assumption" --
// "modeled" names SIE's own internal representation, not something
// meaningful to the founder; the provenance distinction itself (founder's
// own words vs. SIE's guess) is unchanged and still exactly as visible.
export default function ProvenanceBadge({ provenance }: { provenance: DraftProvenance }) {
  if (provenance === "user_provided") {
    return (
      <span className="rounded-full bg-primary-soft px-2 py-0.5 text-xs font-semibold text-primary">
        Based on your description
      </span>
    );
  }

  if (provenance === "ai_inferred") {
    return (
      <span className="rounded-full bg-warning-soft px-2 py-0.5 text-xs font-semibold text-warning">
        SIE assumption
      </span>
    );
  }

  return (
    <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs font-medium text-text-muted">
      Not provided yet
    </span>
  );
}
