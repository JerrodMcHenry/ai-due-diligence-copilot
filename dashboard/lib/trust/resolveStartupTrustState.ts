// Phase 32A -- Trust-State Consistency. The ONE place the
// "Founder-managed" vs "Verified" distinction is decided from a claim's
// verification_method -- extracted out of ClaimStartupButton.tsx so it
// has its own direct, importable unit test (tests/trustState.test.ts)
// rather than only being exercised indirectly through a rendered
// component. Pure, deterministic, no I/O: the exact same
// verification_method string GET /me/startup-claims/{id} already
// returns (mirrors app/database/db.py's startup_claims.verification_method
// column) is the only input.
//
// "venture_graduation" is the one and only self-approved value this
// codebase's own claim lifecycle ever writes (see
// _ensure_graduation_membership() in app/database/db.py) -- every other
// value (today, always "manual_review") means a human admin reviewed and
// approved the claim via approve_startup_claim().
export type StartupTrustState = "founder_managed" | "verified";

export function resolveStartupTrustState(verificationMethod: string): StartupTrustState {
  return verificationMethod === "venture_graduation" ? "founder_managed" : "verified";
}
