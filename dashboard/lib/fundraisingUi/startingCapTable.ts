// Phase 21B, Part 5/6/7 -- the ephemeral starting-ownership builder's pure
// logic: validating founder-entered percentages and converting them into a
// Phase 21A CapTableState. This is simulation-only and never touches the
// canonical venture model (Part 23).

import { initialCapTable } from "../fundraising/capTable.ts";
import type { CapTableState } from "../fundraising/types.ts";
import type { StakeholderRole, UiStakeholder } from "./types.ts";

// A synthetic, hidden share basis -- the founder only ever sees and enters
// percentages. Large enough that percentage inputs given to 2 decimal
// places (the finest granularity the UI exposes) convert without visible
// rounding artifacts.
const SHARE_BASIS = BigInt(1_000_000);

export function totalPercent(stakeholders: readonly UiStakeholder[]): number {
  return stakeholders.reduce((sum, s) => sum + s.percent, 0);
}

// Part 6/7: ownership must be explicitly confirmed, never assumed, and
// must sum to exactly 100% before a scenario can run -- this is the UI's
// own precondition check, distinct from (and in addition to) the engine's
// own ownership-invariant assertion on the resulting CapTableState.
export function validateOwnershipPercentages(stakeholders: readonly UiStakeholder[]): string | null {
  if (stakeholders.length === 0) {
    return "Add at least one stakeholder to describe who owns the company today.";
  }
  for (const s of stakeholders) {
    if (!Number.isFinite(s.percent) || s.percent <= 0) {
      return `${s.name || "Every stakeholder"} needs an ownership percentage greater than 0%.`;
    }
  }
  const total = totalPercent(stakeholders);
  // Rounded to 2 decimals for comparison -- percentage inputs are entered
  // to at most 2 decimals in the UI, so this tolerates floating-point
  // display noise (e.g. 33.33 + 33.33 + 33.34) without masking a genuine
  // founder mistake (entering 95% or 105%).
  const rounded = Math.round(total * 100) / 100;
  if (rounded !== 100) {
    return `Ownership percentages must add up to 100%. Currently: ${rounded}%.`;
  }
  return null;
}

export function oneClickSoleFounder(founderName: string): UiStakeholder[] {
  return [{ id: "you", name: founderName || "You", role: "founder", percent: 100 }];
}

// Converts validated UI percentages into an exact CapTableState. Callers
// MUST call validateOwnershipPercentages() first and only call this when
// it returns null -- this function does not re-validate the 100% sum (its
// only job is the percent -> exact-share conversion), but it does still
// floor+remainder so the resulting shares sum to exactly SHARE_BASIS
// regardless of rounding, keeping the engine's own ownership invariant
// intact by construction.
export function buildStartingCapTable(label: string, stakeholders: readonly UiStakeholder[]): CapTableState {
  const shares = stakeholders.map((s) => (SHARE_BASIS * BigInt(Math.round(s.percent * 100))) / BigInt(10_000));
  const allocated = shares.reduce((sum, s) => sum + s, BigInt(0));
  const remainder = SHARE_BASIS - allocated;

  const positions = stakeholders.map((s, i) => ({
    id: s.id,
    name: s.name || roleToDefaultName(s.role),
    kind: uiRoleToEngineKind(s.role),
    // The remainder (a consequence of percent->share flooring, never more
    // than a few shares out of 1,000,000) is assigned to the largest
    // holder so it never visibly perturbs a small stakeholder's percentage.
    shares: i === largestIndex(shares) ? shares[i] + remainder : shares[i],
  }));

  return initialCapTable(label, positions);
}

function largestIndex(values: readonly bigint[]): number {
  let idx = 0;
  for (let i = 1; i < values.length; i++) {
    if (values[i] > values[idx]) idx = i;
  }
  return idx;
}

function roleToDefaultName(role: StakeholderRole): string {
  switch (role) {
    case "founder":
      return "Founder";
    case "cofounder":
      return "Cofounder";
    case "employee_pool":
      return "Employee / Option Pool";
    case "existing_investor":
      return "Existing Investor";
    default:
      return "Other";
  }
}

function uiRoleToEngineKind(role: StakeholderRole): "founder" | "option_pool" | "investor" | "other" {
  if (role === "founder" || role === "cofounder") return "founder";
  if (role === "employee_pool") return "option_pool";
  if (role === "existing_investor") return "investor";
  return "other";
}
