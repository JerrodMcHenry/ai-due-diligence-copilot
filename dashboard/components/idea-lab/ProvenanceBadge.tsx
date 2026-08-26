import type { DraftProvenance } from "@/types";

// Phase 6.1, Part 6: restrained, non-certain language -- never implies
// something is more verified than it is. "Based on your description" is
// still a paraphrase/extraction, not a guarantee of accuracy; "Modeled
// assumption" is explicitly a guess for the founder to edit; "Not
// provided yet" is neutral, not a criticism.
export default function ProvenanceBadge({ provenance }: { provenance: DraftProvenance }) {
  if (provenance === "user_provided") {
    return (
      <span className="rounded-full bg-primary-soft px-2 py-0.5 text-[10px] font-semibold text-primary">
        Based on your description
      </span>
    );
  }

  if (provenance === "ai_inferred") {
    return (
      <span className="rounded-full bg-warning-soft px-2 py-0.5 text-[10px] font-semibold text-warning">
        Modeled assumption
      </span>
    );
  }

  return (
    <span className="rounded-full bg-surface-muted px-2 py-0.5 text-[10px] font-medium text-text-muted">
      Not provided yet
    </span>
  );
}
