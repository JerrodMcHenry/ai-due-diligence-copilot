// Compare Startups V1, Part 10 -- "Key Differences" is built entirely from
// the structured intelligence GET /compare already returns (pillar
// scores). This is deterministic arithmetic, never a second LLM call, and
// never infers anything the underlying scores don't directly support --
// no "guaranteed to outperform", no future-outcome language.

import { PILLARS, type PillarKey } from "@/components/startup/pillarMeta";

import type { ComparisonStartup } from "@/types";

// Pillar scores are 0-10. A gap smaller than this is "approximately tied"
// -- restrained language, not false precision (Part 8/9). 0.5 (5% of the
// scale) rather than a rounder 1.0: verified against the real canonical
// dataset during Part 21's product review that 1.0 was too generous --
// it grouped genuinely distinct scores (e.g. Vanta 8.6 vs. Brex 7.8 on
// Market, a real 0.8-point gap grounded in different evidence) into
// "tied", which made Key Differences show almost nothing for a tightly
// clustered set of companies. 0.5 still absorbs genuinely negligible
// gaps (e.g. 8.1 vs. 8.0) without erasing real, evidence-based ones.
const PILLAR_TIE_THRESHOLD = 0.5;

// SPS is 0-100. A gap smaller than this should read as "roughly even",
// not as one startup being the clear stronger one (Part 8's explicit
// 78.8-vs-78.7 example).
export const SPS_CLOSE_THRESHOLD = 3.0;

type ScoredEntry = { startupId: number; companyName: string; score: number };

function getScoredEntries(
  startups: ComparisonStartup[],
  pillarKey: PillarKey
): ScoredEntry[] {
  return startups
    .map((startup) => ({
      startupId: startup.startup_id,
      companyName: startup.company_name,
      score: startup[pillarKey].score,
    }))
    .filter(
      (entry): entry is ScoredEntry =>
        typeof entry.score === "number" && !Number.isNaN(entry.score)
    );
}

export type PillarLeadership = {
  pillarKey: PillarKey;
  pillarLabel: string;
  // Every startup tied for the top score (length > 1 means a genuine tie
  // within PILLAR_TIE_THRESHOLD -- not a strict leader at all).
  leaders: ScoredEntry[];
  gapToRunnerUp: number | null;
  // True when every selected startup has no score at all for this pillar
  // -- distinct from a tie (which requires real scores).
  unavailableForAll: boolean;
  unavailableFor: string[];
};

export function computePillarLeadership(
  startups: ComparisonStartup[]
): PillarLeadership[] {
  return PILLARS.map((pillar) => {
    const scored = getScoredEntries(startups, pillar.key);
    const unavailableFor = startups
      .filter((s) => s[pillar.key].score === null)
      .map((s) => s.company_name);

    if (scored.length === 0) {
      return {
        pillarKey: pillar.key,
        pillarLabel: pillar.label,
        leaders: [],
        gapToRunnerUp: null,
        unavailableForAll: true,
        unavailableFor,
      };
    }

    const sorted = [...scored].sort((a, b) => b.score - a.score);
    const topScore = sorted[0].score;
    const leaders = sorted.filter(
      (entry) => topScore - entry.score < PILLAR_TIE_THRESHOLD
    );
    const runnerUp = sorted.find(
      (entry) => !leaders.some((leader) => leader.startupId === entry.startupId)
    );

    return {
      pillarKey: pillar.key,
      pillarLabel: pillar.label,
      leaders,
      gapToRunnerUp: runnerUp
        ? Number((topScore - runnerUp.score).toFixed(1))
        : null,
      unavailableForAll: false,
      unavailableFor,
    };
  });
}

export type LeadershipGroup = {
  startupId: number;
  companyName: string;
  leadsIn: { pillarLabel: string; gap: number }[];
};

// One group per startup, listing only the pillars where it is a STRICT,
// non-tied leader with a real (>= threshold) gap over the runner-up.
export function computeLeadershipGroups(
  startups: ComparisonStartup[],
  leadership: PillarLeadership[]
): LeadershipGroup[] {
  return startups.map((startup) => ({
    startupId: startup.startup_id,
    companyName: startup.company_name,
    leadsIn: leadership
      .filter(
        (entry) =>
          entry.leaders.length === 1 &&
          entry.leaders[0].startupId === startup.startup_id &&
          entry.gapToRunnerUp !== null &&
          entry.gapToRunnerUp >= PILLAR_TIE_THRESHOLD
      )
      .map((entry) => ({
        pillarLabel: entry.pillarLabel,
        gap: entry.gapToRunnerUp as number,
      })),
  }));
}

export function computeTiedPillars(leadership: PillarLeadership[]): string[] {
  return leadership
    .filter((entry) => entry.leaders.length > 1)
    .map((entry) => entry.pillarLabel);
}

export function computeEvidenceGaps(
  leadership: PillarLeadership[]
): { pillarLabel: string; companies: string[] }[] {
  return leadership
    .filter(
      (entry) =>
        !entry.unavailableForAll &&
        entry.unavailableFor.length > 0
    )
    .map((entry) => ({
      pillarLabel: entry.pillarLabel,
      companies: entry.unavailableFor,
    }));
}

// Each startup's own strongest/weakest pillar (by its own scores only --
// not compared against the others). Omitted when a startup has fewer
// than 2 scored pillars (nothing meaningful to contrast).
export function computeStrongestWeakest(
  startup: ComparisonStartup
): { strongest: string; weakest: string } | null {
  const scored = PILLARS.map((pillar) => ({
    label: pillar.label,
    score: startup[pillar.key].score,
  })).filter(
    (entry): entry is { label: string; score: number } =>
      typeof entry.score === "number"
  );

  if (scored.length < 2) {
    return null;
  }

  const strongest = scored.reduce((a, b) => (b.score > a.score ? b : a));
  const weakest = scored.reduce((a, b) => (b.score < a.score ? b : a));

  if (strongest.label === weakest.label) {
    return null;
  }

  return { strongest: strongest.label, weakest: weakest.label };
}

export function isSpsTooCloseToRank(startups: ComparisonStartup[]): boolean {
  const scores = startups
    .map((s) => s.overall_score)
    .filter((score): score is number => typeof score === "number");

  if (scores.length < 2) {
    return false;
  }

  const gap = Math.max(...scores) - Math.min(...scores);
  return gap < SPS_CLOSE_THRESHOLD;
}
