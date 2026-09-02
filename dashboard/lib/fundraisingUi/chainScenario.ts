// Phase 21B, Part 7/12/16 -- "Model another round on top of this"
// (sequential rounds, Path E). Rather than chaining the engine's own
// exact bigint CapTableState across an open-ended UI session (which would
// mean building a persistent multi-round session model this phase's
// directive explicitly warns against -- "do not build a giant event
// framework"), each additional round re-enters the SAME starting-
// ownership step with a fresh UiStakeholder[] derived from the previous
// result's DISPLAYED percentages. This is a deliberate, disclosed
// simplification for this convenience path specifically: the next round's
// math is still computed exactly by the Phase 21A engine from this new
// starting point, but that starting point itself is derived from
// 2-decimal display strings, not the prior round's exact fraction. A
// single scenario's own internal math is never approximated by this.

import type { OwnershipRow, ScenarioSuccess, StakeholderRole, UiStakeholder } from "./types.ts";

function roleForChain(role: OwnershipRow["role"]): StakeholderRole {
  if (role === "safe" || role === "investor") return "existing_investor";
  return role;
}

export function chainOwnershipFromResult(result: ScenarioSuccess): UiStakeholder[] {
  const rows = result.finalOwnership.filter((r) => r.afterPercent !== "—");
  const rounded = rows.map((r) => Math.round(Number.parseFloat(r.afterPercent.replace("%", "")) * 100) / 100);
  const sum = Math.round(rounded.reduce((a, b) => a + b, 0) * 100) / 100;
  const diff = Math.round((100 - sum) * 100) / 100;

  // Assign any rounding remainder (from independently-rounded display
  // percentages) to the largest holder, so it never visibly perturbs a
  // small stakeholder's percentage, and the total is exactly 100.
  let largestIdx = 0;
  for (let i = 1; i < rounded.length; i++) {
    if (rounded[i] > rounded[largestIdx]) largestIdx = i;
  }
  const adjusted = rounded.map((p, i) => (i === largestIdx ? Math.round((p + diff) * 100) / 100 : p));

  return rows.map((r, i) => ({ id: r.id, name: r.name, role: roleForChain(r.role), percent: adjusted[i] }));
}
