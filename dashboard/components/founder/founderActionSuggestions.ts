// Phase 7.3 -- Founder Progress & Improvement V1. Deliberately NOT a
// "use client" module -- plain, framework-agnostic derivation logic,
// same reasoning as components/startup/pillarMeta.ts. Shared by
// ActionPlan.tsx (the only consumer as of this phase; previously this
// same ranking lived inline in FounderStartupWorkspaceView.tsx's
// PrioritiesSection as a read-only "Top Priorities" list -- consolidated
// here once "Add to Plan" made that list actionable, so the same
// recommendations aren't computed AND shown twice on one page).
//
// Every suggested action here is read verbatim from a real pillar's own
// `recommendations` array (genuine, evidence-derived LLM output) --
// never methodology.next_actions (see PillarHighlight's own prior
// comment: that field is a fixed, hardcoded list identical on every
// analysis, so it is never treated as a personalized suggestion), and
// never invented. Unavailable pillars (score === null) are excluded
// entirely, never ranked as "weakest".

import { PILLARS } from "@/components/startup/pillarMeta";

import type { PillarKey } from "@/components/startup/pillarMeta";
import type { SIEMethodologyAnalysis } from "@/types";

export type SuggestedAction = {
  pillar: PillarKey;
  pillarLabel: string;
  text: string;
};

const MAX_SUGGESTED_PILLARS = 2;
const MAX_SUGGESTIONS = 5;

export function getSuggestedActions(
  methodology: SIEMethodologyAnalysis
): SuggestedAction[] {
  const scored = PILLARS.map((pillar) => ({
    key: pillar.key,
    label: pillar.label,
    analysis: methodology[pillar.key],
  })).filter((pillar) => pillar.analysis.score !== null);

  if (scored.length === 0) {
    return [];
  }

  const sortedAscending = [...scored].sort(
    (a, b) => (a.analysis.score as number) - (b.analysis.score as number)
  );

  const weakest = sortedAscending.slice(0, MAX_SUGGESTED_PILLARS);

  const seen = new Set<string>();
  const suggestions: SuggestedAction[] = [];

  for (const pillar of weakest) {
    for (const text of pillar.analysis.recommendations) {
      const trimmed = text.trim();

      if (!trimmed || seen.has(trimmed)) {
        continue;
      }

      seen.add(trimmed);
      suggestions.push({ pillar: pillar.key, pillarLabel: pillar.label, text: trimmed });

      if (suggestions.length >= MAX_SUGGESTIONS) {
        return suggestions;
      }
    }
  }

  return suggestions;
}
