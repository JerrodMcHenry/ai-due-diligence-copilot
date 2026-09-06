// Phase 34A -- Remove VPS + Rebuild Idea Lab Around Evidence and Decision
// Support, Part 6. The pure derivation behind ScenarioComparison.tsx's
// four qualitative sections -- extracted so it's testable the same way
// this directory's other pure files are (plain `node`, zero "@/..."
// imports), matching directConsequences.ts / assumptionDiff.ts's own
// discipline.
//
// Reads ONLY data the backend already returns from POST
// /ventures/scenario-compare (categories' score/basis, validation_gaps,
// next_milestones) -- no new call, no new score, no new AI. Every
// sentence surfaced is either a real `basis` line vps_scoring.py's
// deterministic scorer produced, a real `validation_gaps` sentence
// vps_guidance.py produced, or a real `next_milestones` sentence that
// newly appears as a consequence of the scenario -- never generated here.
type MinimalCategory = {
  key: string;
  label: string;
  score: number | null;
  basis: string[];
};

type MinimalVPSResult = {
  categories: MinimalCategory[];
  validation_gaps: string[];
  next_milestones: string[];
};

export type CategoryShift = {
  key: string;
  label: string;
  reason: string;
};

export type ScenarioInsights = {
  // Categories whose evidence/assumptions genuinely improved (a category
  // moved from Unavailable to scored, or its score rose) -- the
  // "what this would strengthen" section.
  strengthened: CategoryShift[];
  // Categories whose score fell -- the "may need re-examining" half of
  // "new questions / risks."
  weakened: CategoryShift[];
  // Still-Unavailable categories (by label) plus the backend's own
  // validation_gaps sentences, deduplicated -- "what would still be
  // unknown."
  stillUnknown: string[];
  // Milestones present in the scenario's next_milestones that were NOT
  // already present in the current venture's -- a plain set diff over
  // already-deterministic data, never a new recommendation engine.
  newQuestions: string[];
};

function hasMeaningfulChange(from: number | null, to: number | null): boolean {
  if (from === null && to === null) return false;
  if (from === null || to === null) return true;
  return Math.abs(to - from) >= 0.05;
}

export function buildScenarioInsights(current: MinimalVPSResult, modified: MinimalVPSResult): ScenarioInsights {
  const currentByKey = new Map(current.categories.map((c) => [c.key, c]));

  const strengthened: CategoryShift[] = [];
  const weakened: CategoryShift[] = [];

  for (const category of modified.categories) {
    const before = currentByKey.get(category.key);
    const fromScore = before?.score ?? null;
    const toScore = category.score;

    if (!hasMeaningfulChange(fromScore, toScore)) continue;

    const becameStronger = (fromScore === null && toScore !== null) || (fromScore !== null && toScore !== null && toScore > fromScore);
    const becameWeaker = fromScore !== null && toScore !== null && toScore < fromScore;

    const reason = category.basis[0] ?? (becameStronger ? "gains real supporting evidence." : "looks weaker under this scenario.");

    if (becameStronger) {
      strengthened.push({ key: category.key, label: category.label, reason });
    } else if (becameWeaker) {
      weakened.push({ key: category.key, label: category.label, reason });
    }
  }

  const stillUnknownCategories = modified.categories.filter((c) => c.score === null).map((c) => c.label);
  const stillUnknown = [...stillUnknownCategories, ...modified.validation_gaps].filter(
    (item, index, all) => all.indexOf(item) === index
  );

  const newQuestions = modified.next_milestones.filter((milestone) => !current.next_milestones.includes(milestone));

  return { strengthened, weakened, stillUnknown, newQuestions };
}
