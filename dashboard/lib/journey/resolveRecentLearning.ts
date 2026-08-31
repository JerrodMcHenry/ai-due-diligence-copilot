// Phase 13 -- Founder Home / Venture Command Center, Part 13. A pure,
// deterministic function -- no LLM, no interpretation, no summarization.
// Mirrors resolveIdeaLabNextStep.ts's own shape exactly: reads only
// fields the caller already has in hand (the venture_missions list
// MissionsSection already fetches via GET /ventures/{id}/missions), does
// no I/O, and returns a small typed result the caller renders as-is.
//
// Deliberately considers missions of ANY status, not just "active" --
// once a mission is marked completed, its learning_summary would
// otherwise become invisible everywhere in the UI (MissionsSection only
// ever renders the primary ACTIVE mission's own learning inline). This
// is the one place that gap is closed, purely by reading data that
// already exists -- no new persistence, no new endpoint.
export type RecentLearning = {
  missionTitle: string;
  summary: string;
  recordedAt: string;
};

type MinimalMission = {
  title: string;
  learning_summary: string | null;
  learning_recorded_at: string | null;
};

export function resolveRecentLearning(missions: MinimalMission[]): RecentLearning | null {
  const withLearning = missions.filter(
    (m): m is MinimalMission & { learning_summary: string; learning_recorded_at: string } =>
      Boolean(m.learning_summary && m.learning_recorded_at)
  );

  if (withLearning.length === 0) {
    return null;
  }

  const mostRecent = withLearning.reduce((latest, m) =>
    new Date(m.learning_recorded_at).getTime() > new Date(latest.learning_recorded_at).getTime() ? m : latest
  );

  return {
    missionTitle: mostRecent.title,
    summary: mostRecent.learning_summary,
    recordedAt: mostRecent.learning_recorded_at,
  };
}
