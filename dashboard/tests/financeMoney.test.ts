// Phase 35B -- Financial State Persistence + Runway Engine V1 tests.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as the rest of
// this directory (no jest/vitest here) -- run directly by Node's native
// TypeScript support.
//
// Run with:
//   node tests/financeMoney.test.ts

import { dollarsToCents, centsToDollars, formatWholeDollars, formatMonthYear } from "../lib/finance/money.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

function test_dollars_to_cents_basic(): void {
  expect(dollarsToCents(500000) === 50000000, `expected 50,000,000 cents for $500,000, got ${dollarsToCents(500000)}`);
  expect(dollarsToCents(0) === 0, "explicit zero dollars must convert to explicit zero cents");
}

function test_dollars_to_cents_rounds_floating_point_noise(): void {
  // 20.1 * 100 in raw floating point is 2009.9999999999998 without rounding.
  expect(dollarsToCents(20.1) === 2010, `expected exact 2010 cents, got ${dollarsToCents(20.1)}`);
}

function test_cents_to_dollars_round_trip(): void {
  expect(centsToDollars(dollarsToCents(1234.56)) === 1234.56, "round trip through cents must preserve the original dollar amount");
}

function test_format_whole_dollars(): void {
  expect(formatWholeDollars(50000000) === "$500,000", `got: ${formatWholeDollars(50000000)}`);
  expect(formatWholeDollars(0) === "$0", `explicit zero must format as $0, not blank, got: ${formatWholeDollars(0)}`);
}

function test_format_month_year_no_timezone_shift(): void {
  // The classic bug this guards against: `new Date("2026-03-01")` is UTC
  // midnight, which renders as "February 2026" in any negative-UTC-offset
  // timezone (e.g. US timezones) -- formatMonthYear must never do that.
  expect(formatMonthYear("2026-03-01") === "March 2026", `got: ${formatMonthYear("2026-03-01")}`);
  expect(formatMonthYear("2026-01-01") === "January 2026", `got: ${formatMonthYear("2026-01-01")}`);
  expect(formatMonthYear("2026-12-01") === "December 2026", `got: ${formatMonthYear("2026-12-01")}`);
}

const TESTS = [
  test_dollars_to_cents_basic,
  test_dollars_to_cents_rounds_floating_point_noise,
  test_cents_to_dollars_round_trip,
  test_format_whole_dollars,
  test_format_month_year_no_timezone_shift,
];

function main(): void {
  console.log("\nPhase 35B -- Financial State Persistence + Runway Engine V1 tests");
  console.log("-".repeat(72));

  const failures: string[] = [];
  for (const test of TESTS) {
    const name = test.name;
    try {
      test();
      console.log(`PASS  ${name}`);
    } catch (error) {
      console.log(`FAIL  ${name}\n      ${(error as Error).message}`);
      failures.push(name);
    }
  }

  console.log("-".repeat(72));
  console.log(`${TESTS.length - failures.length}/${TESTS.length} passed`);

  if (failures.length > 0) {
    process.exit(1);
  }
}

main();
