import BaseCard from "@/components/ui/BaseCard";

import { classifyCategoryKnowledge } from "./ventureKnowledge";

import type { VPSResult } from "@/types";

// Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and Decision
// Support, Part 3/4. Replaces VPSResultPanel as the Model tab's centerpiece.
// VPSResultPanel (score ring, "Path to Stronger," strength/weak-point
// framing) is retained unmodified in the codebase -- see this phase's
// final report for exactly why -- but is no longer rendered anywhere in
// the live Idea Lab flow. This panel reads the same VPSResult.categories
// data (score/basis, unchanged) and organizes it around the six
// categories as WHAT WE KNOW / WHAT WE BELIEVE / WHAT WE DON'T KNOW YET,
// per category, instead of a 0-10 number. No score, no color grading, no
// "strength"/"weak point" language -- see ventureKnowledge.ts's own
// docstring for exactly how each category's real, existing data maps
// onto these three states.
type VentureUnderstandingPanelProps = {
  result: VPSResult;
};

// The one framing sentence _validation_gaps() (app/ai/vps_guidance.py)
// always prepends when any gap exists -- kept as the first bullet
// wherever gaps render (still true and still worth saying), never
// stripped out or reworded here.
export default function VentureUnderstandingPanel({ result }: VentureUnderstandingPanelProps) {
  const categories = classifyCategoryKnowledge(result.categories);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-text-primary">What SIE understands so far</h2>
        <p className="mt-1 text-base leading-7 text-text-secondary">
          Organized by category — what&rsquo;s backed by something you&rsquo;ve actually observed, what&rsquo;s
          still a modeled guess, and what&rsquo;s genuinely unknown.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {categories.map((category) => (
          <CategoryKnowledgeCard
            key={category.key}
            category={category}
            validationGaps={category.isEvidenceBased ? result.validation_gaps : []}
          />
        ))}
      </div>
    </div>
  );
}

function CategoryKnowledgeCard({
  category,
  validationGaps,
}: {
  category: ReturnType<typeof classifyCategoryKnowledge>[number];
  validationGaps: string[];
}) {
  return (
    <BaseCard className="p-5">
      <p className="text-base font-semibold text-text-primary">{category.label}</p>

      {category.hasSignal ? (
        <div className="mt-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {category.isEvidenceBased ? "What we know" : "What we believe"}
          </p>
          <ul className="mt-1.5 space-y-1">
            {category.facts.map((fact) => (
              <li key={fact} className="text-sm leading-6 text-text-secondary">
                {fact}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-2.5 text-sm leading-6 text-text-secondary">
          Not enough modeled yet to say anything here.
        </p>
      )}

      {category.isEvidenceBased && validationGaps.length > 0 ? (
        <div className="mt-3 border-t border-border pt-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">What we don&rsquo;t know yet</p>
          <ul className="mt-1.5 space-y-1">
            {validationGaps.map((gap) => (
              <li key={gap} className="text-sm leading-6 text-text-secondary">
                {gap}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </BaseCard>
  );
}
