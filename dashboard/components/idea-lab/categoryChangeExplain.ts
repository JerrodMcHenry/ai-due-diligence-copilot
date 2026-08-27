import type { VPSCategoryResult } from "@/types";

// Phase 10.7 -- Founder Missions V1. Extracted from ScenarioComparison.tsx
// (Phase 10.6) so the SAME "what changed and why" logic explains both a
// scenario preview AND a real, saved explicit validation update (Part 12:
// "Then explain WHY using existing category basis/guidance data where
// possible") -- one implementation, not two copies that could drift.
// Every explanation line is a `basis` string vps_scoring.py's own
// deterministic scorer already produced; nothing here is generated.
export type CategoryChange = {
  key: string;
  label: string;
  fromScore: number | null;
  toScore: number | null;
  deltaLabel: string;
  deltaDirection: "positive" | "negative" | "neutral";
  basis: string[];
};

export function formatCategoryDelta(from: number | null, to: number | null): string {
  if (from === null && to !== null) {
    return "newly scored";
  }
  if (from !== null && to === null) {
    return "no longer scored";
  }
  if (from === null || to === null) {
    return "";
  }
  const delta = to - from;
  if (Math.abs(delta) < 0.05) {
    return "no meaningful change";
  }
  return delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1);
}

export function categoryDeltaDirection(from: number | null, to: number | null): "positive" | "negative" | "neutral" {
  if (from === null && to !== null) return "neutral";
  if (from !== null && to === null) return "neutral";
  if (from === null || to === null || Math.abs(to - from) < 0.05) return "neutral";
  return to > from ? "positive" : "negative";
}

// A category moving from Unavailable (null) to scored -- or the reverse --
// is itself a meaningful, explainable change (often the actual reason the
// overall VPS moved, since compute_vps() renormalizes around whichever
// categories are scored). Not just a same-to-same numeric delta.
function hasMeaningfulChange(from: number | null, to: number | null): boolean {
  if (from === null && to === null) return false;
  if (from === null || to === null) return true;
  return Math.abs(to - from) >= 0.05;
}

export function explainCategoryChanges(
  before: VPSCategoryResult[],
  after: VPSCategoryResult[]
): CategoryChange[] {
  return after
    .map((afterCategory) => {
      const beforeCategory = before.find((c) => c.key === afterCategory.key);
      const fromScore = beforeCategory?.score ?? null;
      const toScore = afterCategory.score;

      return {
        key: afterCategory.key,
        label: afterCategory.label,
        fromScore,
        toScore,
        deltaLabel: formatCategoryDelta(fromScore, toScore),
        deltaDirection: categoryDeltaDirection(fromScore, toScore),
        basis: afterCategory.basis,
      };
    })
    .filter((change) => hasMeaningfulChange(change.fromScore, change.toScore));
}
