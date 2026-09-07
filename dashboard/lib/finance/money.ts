// Phase 35B -- Financial State Persistence + Runway Engine V1.
//
// Dollars <-> cents conversion for Finance, deliberately using a plain
// JS `number` for cents rather than the bigint domain
// dashboard/lib/fundraising/rational.ts's cap-table engine uses. This is
// a considered choice, not an inconsistency: the fundraising engine needs
// bigint because it MULTIPLIES/DIVIDES share counts against cent amounts
// to solve for exact fractional ownership, where float error would
// corrupt a real legal cap table. Finance only ever ADDS and SUBTRACTS
// money (revenue, expenses, cash) -- operations plain integers perform
// exactly regardless of magnitude -- and cents cross the network as JSON,
// where bigint has no native representation (it would need custom
// string-encoding on every request/response). `Number.MAX_SAFE_INTEGER`
// cents is about $90 trillion, far beyond any real company's cash
// balance, so precision is never at risk here.
//
// Zero "@/..." alias imports -- plain-Node-testable, same discipline as
// dashboard/lib/fundraisingUi/formatUi.ts and every other pure lib file
// in this codebase.

export function dollarsToCents(dollars: number): number {
  // Math.round guards against JS floating-point noise (0.1 + 0.2-style
  // error) before committing to an exact integer cent count -- the same
  // discipline dashboard/lib/fundraisingUi/formatUi.ts::dollarsToCents()
  // already uses for the fundraising engine's bigint domain, applied here
  // to a plain number.
  return Math.round(dollars * 100);
}

export function centsToDollars(cents: number): number {
  return cents / 100;
}

export function formatWholeDollars(cents: number): string {
  return `$${Math.round(centsToDollars(cents)).toLocaleString("en-US")}`;
}

export function formatMonthYear(isoDate: string): string {
  // "2026-03-01" -> "March 2026". Parsed as a plain date (no timezone
  // shift) -- an ISO date-only string from the backend is a calendar
  // date, not an instant, so it's parsed by its own components rather
  // than through `new Date(isoDate)` (which treats a bare "YYYY-MM-DD"
  // as UTC midnight and can display the PREVIOUS day in a
  // negative-UTC-offset timezone).
  const [year, month] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, 1);
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}
