// Founder Loop V2 Acceptance Pass -- bug found live in the real signed-in
// app: VentureCard's own `oneLineConcept` prop was being fed the ENTIRE
// raw multi-paragraph venture description verbatim (VentureWorkspace.tsx's
// "Preview your venture card" call site), reproducing exactly the "narrow
// card containing the whole startup description" defect Founder Loop V2's
// own brief described as already fixed -- it wasn't; VentureCard.tsx's
// own component body was fine (name / one-line concept / VPS / top 2
// category badges, nothing else), but nothing had ever shortened what
// was actually passed into it. This is a small, targeted fix at the call
// site, not a VentureCard redesign.
//
// Pure, zero "@/..." alias imports (same discipline as
// lib/journey/inferVentureStage.ts and whatIfScenarios.ts), so this is
// trivially testable with plain `node`.
const MAX_CONCEPT_LENGTH = 160;

export function summarizeConceptForCard(description: string | null): string | null {
  if (!description) {
    return null;
  }

  const trimmed = description.trim();
  if (!trimmed) {
    return null;
  }

  // The first sentence (a period/!/? followed by whitespace or end of
  // string), or the whole string if there's no such break -- never
  // fabricates a summary, just stops repeating the whole paragraph.
  const firstSentenceMatch = trimmed.match(/^.*?[.!?](?=\s|$)/);
  const firstSentence = firstSentenceMatch ? firstSentenceMatch[0] : trimmed;

  if (firstSentence.length <= MAX_CONCEPT_LENGTH) {
    return firstSentence;
  }

  const cut = firstSentence.slice(0, MAX_CONCEPT_LENGTH);
  const lastSpace = cut.lastIndexOf(" ");
  return `${(lastSpace > 40 ? cut.slice(0, lastSpace) : cut).trim()}…`;
}
