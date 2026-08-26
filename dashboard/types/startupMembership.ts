// Phase 7.1C -- Founder Membership Authorization Foundation. Mirrors
// app/models/startup_membership.py's MyStartupMembership exactly. This is
// the current-authorization truth (a live startup_memberships row) --
// distinct from ClaimStatus in ./startupClaim.ts, which is claim
// request/review history and is NOT proof of current access on its own.

export interface MyStartupMembership {
  startup_id: number;
  canonical_name: string;
  role: string;
}
