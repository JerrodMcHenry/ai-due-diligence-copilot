// Phase 21B -- founder-readable formatting helpers. Thin wrappers around
// the Phase 21A engine's own exact formatting (rational.ts) -- this file
// performs unit conversion (dollars <-> cents) and display composition
// only; it never computes a financial result itself.

import { centsToDollarString } from "../fundraising/rational.ts";

export function dollarsToCents(dollars: number): bigint {
  // Dollars entered via a form are already the founder's own round figure
  // (e.g. 500000 for $500,000); Math.round guards against JS floating-
  // point noise (e.g. 0.1 + 0.2) before converting to an exact integer
  // cent count -- this is the ONE place a floating-point `number` is
  // converted to the engine's exact bigint domain, and it happens before
  // any financing math runs, never after.
  return BigInt(Math.round(dollars * 100));
}

export function formatDollars(dollars: number): string {
  return centsToDollarString(dollarsToCents(dollars));
}

export function formatWholeDollars(dollars: number): string {
  const rounded = Math.round(dollars);
  return `$${rounded.toLocaleString("en-US")}`;
}
