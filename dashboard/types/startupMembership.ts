// Phase 7.1C -- Founder Membership Authorization Foundation. Mirrors
// app/models/startup_membership.py's MyStartupMembership exactly. This is
// the current-authorization truth (a live startup_memberships row) --
// distinct from ClaimStatus in ./startupClaim.ts, which is claim
// request/review history and is NOT proof of current access on its own.

export interface MyStartupMembership {
  startup_id: number;
  canonical_name: string;
  role: string;
  // Phase 37B -- Company Identity + Workspace Routing Bridge. Present
  // only when this startup is linked (via venture_graduations) to a
  // modeled_venture the caller themselves owns -- ownership-checked
  // server-side. When present, this row should route into the existing
  // Venture Workspace (/idea-lab/{linked_venture_id}) instead of the
  // legacy Founder Workspace.
  linked_venture_id: number | null;
}
