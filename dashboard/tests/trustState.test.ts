// Phase 32A -- Trust-State Consistency tests.
//
// Direct unit coverage for resolveStartupTrustState() -- the one
// function ClaimStartupButton.tsx's "member" phase branches on to show
// "Founder-managed" vs "✓ Verified". Complements the backend's own
// app/tests/test_startup_claims.py coverage (which proves the DATA is
// exposed correctly end-to-end through the API); this file proves the
// FRONTEND's own interpretation of that data is correct and can never
// flip the two states.
//
// Same hand-rolled expect()/PASS-FAIL/main() convention as
// tests/whatIfSemantics.test.ts, run directly by Node's native
// TypeScript support.
//
// Run with:
//   node tests/trustState.test.ts
// or:
//   npm run test:trustState
import { resolveStartupTrustState } from "../lib/trust/resolveStartupTrustState.ts";

function expect(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(message);
  }
}

// A. Idea -> Startup graduation relationship renders Founder-managed.
function test_venture_graduation_resolves_to_founder_managed(): void {
  expect(
    resolveStartupTrustState("venture_graduation") === "founder_managed",
    "verification_method 'venture_graduation' must resolve to 'founder_managed'"
  );
}

// B. Independently reviewed claim renders Verified.
function test_manual_review_resolves_to_verified(): void {
  expect(
    resolveStartupTrustState("manual_review") === "verified",
    "verification_method 'manual_review' must resolve to 'verified'"
  );
}

// C. Founder-managed cannot accidentally render Verified.
function test_venture_graduation_never_resolves_to_verified(): void {
  expect(
    resolveStartupTrustState("venture_graduation") !== "verified",
    "'venture_graduation' must never resolve to 'verified'"
  );
}

// D. Verified claim cannot accidentally render Founder-managed.
function test_manual_review_never_resolves_to_founder_managed(): void {
  expect(
    resolveStartupTrustState("manual_review") !== "founder_managed",
    "'manual_review' must never resolve to 'founder_managed'"
  );
}

// Defensive default: an unrecognized/legacy verification_method value
// (there is currently only ever one of two real values, but the column
// itself has no CHECK constraint -- see create_startup_claims_table()'s
// own comment) must fail closed toward "verified", never silently grant
// the less-scrutinized "founder_managed" label to data this function
// doesn't recognize.
function test_unknown_verification_method_defaults_to_verified(): void {
  expect(
    resolveStartupTrustState("some_future_method") === "verified",
    "An unrecognized verification_method must default to 'verified', not 'founder_managed'"
  );
}

function test_resolver_is_pure(): void {
  const a = resolveStartupTrustState("venture_graduation");
  const b = resolveStartupTrustState("venture_graduation");
  expect(a === b, "resolveStartupTrustState must be deterministic for the same input");
}

const TESTS: [string, () => void][] = [
  ["test_venture_graduation_resolves_to_founder_managed", test_venture_graduation_resolves_to_founder_managed],
  ["test_manual_review_resolves_to_verified", test_manual_review_resolves_to_verified],
  ["test_venture_graduation_never_resolves_to_verified", test_venture_graduation_never_resolves_to_verified],
  ["test_manual_review_never_resolves_to_founder_managed", test_manual_review_never_resolves_to_founder_managed],
  ["test_unknown_verification_method_defaults_to_verified", test_unknown_verification_method_defaults_to_verified],
  ["test_resolver_is_pure", test_resolver_is_pure],
];

function main(): void {
  console.log("\nPhase 32A -- Trust-State Consistency tests");
  console.log("-".repeat(72));

  const failures: string[] = [];

  for (const [name, test] of TESTS) {
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
