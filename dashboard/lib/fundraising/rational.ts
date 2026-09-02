// Phase 21A -- Fundraising Simulation, Part 17/18 (precision).
//
// Exact rational arithmetic for cap-table math, built on native BigInt.
// No external dependency (this repo has no decimal.js/bignumber.js and an
// established convention of zero-dependency pure modules under lib/*; see
// lib/simulate/*.ts). Money and share counts are exact integers; every
// derived quantity (ownership fractions, prices per share) is an exact
// Rational (num/den, den always > 0, always kept in lowest terms) -- never
// a floating-point number. Floating point is never used anywhere in this
// module or its callers for a value that participates in cap-table math.
//
// Rounding happens in exactly two places, both explicit and documented:
//   1. Share issuance always FLOORS (truncates toward zero) -- see
//      toFlooredShares(). This matches Y Combinator's own Post-Money SAFE
//      User Guide (v1.2, Feb 2023) worked example numbers exactly: e.g.
//      1,176,470.588... shares floors to 1,176,470, matching the guide's
//      own stated result. Fractional shares are not issuable.
//   2. Percentage/decimal DISPLAY strings round half-up at a caller-chosen
//      number of decimal places -- applied only at final formatting, never
//      to intermediate values used in further calculation.
//
// Zero "@/..." alias imports -- importable directly by plain Node (see
// tests/fundraising.test.ts), matching lib/simulate/*.ts's own convention.

export interface Rational {
  readonly num: bigint;
  readonly den: bigint; // always > 0
}

function gcd(a: bigint, b: bigint): bigint {
  a = a < BigInt(0) ? -a : a;
  b = b < BigInt(0) ? -b : b;
  while (b) {
    [a, b] = [b, a % b];
  }
  return a === BigInt(0) ? BigInt(1) : a;
}

export function makeRational(num: bigint, den: bigint = BigInt(1)): Rational {
  if (den === BigInt(0)) throw new Error("Rational: denominator cannot be zero");
  let n = num;
  let d = den;
  if (d < BigInt(0)) {
    n = -n;
    d = -d;
  }
  const g = gcd(n, d);
  return { num: n / g, den: d / g };
}

export const RAT_ZERO: Rational = { num: BigInt(0), den: BigInt(1) };
export const RAT_ONE: Rational = { num: BigInt(1), den: BigInt(1) };

export function ratAdd(a: Rational, b: Rational): Rational {
  return makeRational(a.num * b.den + b.num * a.den, a.den * b.den);
}

export function ratSub(a: Rational, b: Rational): Rational {
  return makeRational(a.num * b.den - b.num * a.den, a.den * b.den);
}

export function ratMul(a: Rational, b: Rational): Rational {
  return makeRational(a.num * b.num, a.den * b.den);
}

export function ratDiv(a: Rational, b: Rational): Rational {
  if (b.num === BigInt(0)) throw new Error("Rational: division by zero");
  return makeRational(a.num * b.den, a.den * b.num);
}

export function ratIsZero(a: Rational): boolean {
  return a.num === BigInt(0);
}

export function ratIsNegative(a: Rational): boolean {
  return a.num < BigInt(0);
}

export function ratCompare(a: Rational, b: Rational): -1 | 0 | 1 {
  const l = a.num * b.den;
  const r = b.num * a.den;
  if (l < r) return -1;
  if (l > r) return 1;
  return 0;
}

export function ratMin(a: Rational, b: Rational): Rational {
  return ratCompare(a, b) <= 0 ? a : b;
}

export function ratMax(a: Rational, b: Rational): Rational {
  return ratCompare(a, b) >= 0 ? a : b;
}

// Integer share counts as Rationals (den = 1) for use in the arithmetic
// helpers above.
export function ratFromInt(n: bigint): Rational {
  return { num: n, den: BigInt(1) };
}

// Rule 1 (see module docstring): share issuance always floors toward zero.
// Rejects negative inputs -- a negative share count is never a legal
// output of this engine; callers that can legitimately produce a negative
// intermediate must catch it before calling this.
export function toFlooredShares(r: Rational): bigint {
  if (r.num < BigInt(0)) throw new Error("toFlooredShares: negative share count is not valid");
  return r.num / r.den; // BigInt division truncates toward zero == floor for non-negatives
}

function roundHalfUpDiv(n: bigint, d: bigint): bigint {
  // d is always > 0 by construction of Rational.
  const q = n / d;
  const r = n % d;
  if (n >= BigInt(0)) {
    return r * BigInt(2) >= d ? q + BigInt(1) : q;
  }
  return -r * BigInt(2) >= d ? q - BigInt(1) : q;
}

// Rule 2 (see module docstring): percentage display, round-half-up at
// `decimals` places. `r` is a plain fraction (0.5 == 50%), not pre-scaled.
export function toPercentString(r: Rational, decimals = 2): string {
  const scale = BigInt(10) ** BigInt(decimals);
  const scaledPercent = roundHalfUpDiv(r.num * BigInt(100) * scale, r.den);
  const sign = scaledPercent < BigInt(0) ? "-" : "";
  const abs = scaledPercent < BigInt(0) ? -scaledPercent : scaledPercent;
  const intPart = abs / scale;
  if (decimals === 0) return `${sign}${intPart}%`;
  const fracPart = (abs % scale).toString().padStart(decimals, "0");
  return `${sign}${intPart}.${fracPart}%`;
}

// Decimal display (not a percentage), same round-half-up rule.
export function toDecimalString(r: Rational, decimals = 4): string {
  const scale = BigInt(10) ** BigInt(decimals);
  const scaled = roundHalfUpDiv(r.num * scale, r.den);
  const sign = scaled < BigInt(0) ? "-" : "";
  const abs = scaled < BigInt(0) ? -scaled : scaled;
  const intPart = abs / scale;
  if (decimals === 0) return `${sign}${intPart}`;
  const fracPart = (abs % scale).toString().padStart(decimals, "0");
  return `${sign}${intPart}.${fracPart}`;
}

// Cents (exact integer) -> dollar display string. No rounding is possible
// here since cents are already integral -- included for consistent
// formatting across the engine and its test/report output.
export function centsToDollarString(cents: bigint): string {
  const sign = cents < BigInt(0) ? "-" : "";
  const abs = cents < BigInt(0) ? -cents : cents;
  const dollars = abs / BigInt(100);
  const remainder = (abs % BigInt(100)).toString().padStart(2, "0");
  const withCommas = dollars.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${sign}$${withCommas}.${remainder}`;
}
