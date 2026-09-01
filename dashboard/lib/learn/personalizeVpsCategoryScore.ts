// Learn V1, Part 5/10. A deterministic, one-sentence "for your venture"
// line for a VPS category explanation -- computed purely from the
// category's OWN already-computed score (VPSCategoryResult.score, a
// number the caller already has; nothing here reads assumptions, calls
// compute_vps again, or performs any I/O). Deliberately framed around
// how MUCH IS KNOWN/MODELED, never "good"/"bad" language and never a
// number a founder could reverse-engineer into the scoring formula
// (Part 5: "Do not expose internal scoring formulas. Do not teach
// founders how to game VPS."). Zero imports -- kept trivially portable
// and unit-testable with plain `node` (see tests/concepts.test.ts).
export function personalizeVpsCategoryScore(score: number | null): string {
  if (score === null) {
    return "You haven't modeled enough here yet to say.";
  }
  if (score < 5) {
    return "This looks like one of the more uncertain parts of your model right now.";
  }
  if (score < 7) {
    return "This is reasonably modeled, but still mostly assumption, not proof.";
  }
  return "This is one of the stronger, more developed parts of your model.";
}
