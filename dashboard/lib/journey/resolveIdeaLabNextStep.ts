// Phase 10.10 -- Founder Journey Integration, Part 6. A pure, deterministic
// function -- no LLM, no score, no prediction. It reads only the two
// fields VentureWorkspace already has in hand (`vps`, `next_milestones`),
// both already produced by the existing backend VPS scoring/guidance
// pipeline (app/ai/vps_scoring.py and app/ai/vps_guidance.py), and returns
// a small discriminated-union description of what to show. It performs no
// I/O and calls nothing -- VentureWorkspace.tsx is responsible for turning
// this into real NextStepCard props (including anything that needs a
// callback, like "Make this a mission", which this module has no access
// to and shouldn't).
export type IdeaLabNextStep =
  | { kind: "add_assumptions" }
  | { kind: "work_on_milestone"; milestoneText: string }
  | { kind: "ready_for_real_startup" };

type MinimalModelResult = {
  vps: number | null;
  next_milestones: string[];
};

export function resolveIdeaLabNextStep(modelResult: MinimalModelResult | null): IdeaLabNextStep {
  if (!modelResult || modelResult.vps === null) {
    return { kind: "add_assumptions" };
  }

  if (modelResult.next_milestones.length > 0) {
    return { kind: "work_on_milestone", milestoneText: modelResult.next_milestones[0] };
  }

  // No open milestones left in the deterministic guidance list -- the
  // model has addressed what it can flag on its own. This is a
  // reasonable moment to surface the idea -> real startup bridge (Part
  // 8), never a claim the venture is "done" or guaranteed to succeed.
  return { kind: "ready_for_real_startup" };
}
