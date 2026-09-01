import PlaybookLink from "@/components/playbooks/PlaybookLink";
import { getPlaybookForVpsCategory } from "@/lib/playbooks/resourceMap";
import { getVpsCategoryConcept } from "@/content/concepts";
import { personalizeVpsCategoryScore } from "@/lib/learn/personalizeVpsCategoryScore";

// Learn V1, Part 5/6/19/20. The per-category "what does this mean, and
// why does it matter?" trigger inside each VPS category card
// (VPSResultPanel.tsx) -- Part 5's core educational surface. Same
// bespoke lightweight <details> pattern as ConceptDisclosure.tsx (see
// that file's own docstring for why components/ui/Disclosure's card
// chrome is too heavy stacked inside an already-compact grid card).
//
// Deliberately reuses getPlaybookForVpsCategory -- the SAME lookup
// VPSResultPanel already calls for its own, separate "Learn how ->" link
// -- rather than inventing a second mapping; a category card can end up
// showing both this explainer's optional Playbook link and the panel's
// own, and that's fine (Part 12: Learn and Playbook stay distinct, not
// merged, so seeing both isn't duplication).
type VpsCategoryExplainerProps = {
  categoryKey: string;
  score: number | null;
  className?: string;
};

export default function VpsCategoryExplainer({ categoryKey, score, className = "" }: VpsCategoryExplainerProps) {
  const concept = getVpsCategoryConcept(categoryKey);
  if (!concept) {
    return null;
  }
  const playbook = getPlaybookForVpsCategory(categoryKey);

  return (
    <details className={["group mt-1.5", className].join(" ")}>
      <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-[11px] font-semibold text-primary marker:content-none hover:text-primary-hover">
        What does this mean?
        <span aria-hidden="true" className="text-text-muted transition-transform group-open:rotate-180">▾</span>
      </summary>

      <div className="mt-1.5 space-y-2 rounded-lg border border-border bg-surface-muted p-3 text-xs leading-5 text-text-secondary">
        <p className="font-medium text-text-primary">{concept.question}</p>
        <p>{concept.whyItMatters}</p>
        <p>{personalizeVpsCategoryScore(score)}</p>
        {playbook ? <PlaybookLink slug={playbook.slug} className="pt-1" /> : null}
      </div>
    </details>
  );
}
