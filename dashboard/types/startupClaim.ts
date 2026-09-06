// Phase 7.1B -- Startup Claim founder UX. Mirrors app/models/startup_claim.py's
// response shapes exactly. The UI never sends or reads a user_id, role,
// status, or verification_method as a value it controls -- status is
// always server-derived, role/verification_method never appear in any
// request this frontend sends at all.

export type ClaimStatus = "pending" | "approved" | "rejected" | "cancelled";

export interface StartupClaimSubmissionResponse {
  id: number;
  startup_id: number;
  status: ClaimStatus;
}

// Phase 32A -- Trust-State Consistency. verification_method mirrors the
// exact same column app/models/startup_claim.py's StartupClaimStatus now
// exposes (already present on MyStartupClaim's own list-endpoint shape;
// this was the one response missing it) -- the minimum existing signal
// ClaimStartupButton.tsx needs to tell "Founder-managed" (self-approved
// via Idea -> Startup graduation, verification_method === "venture_graduation")
// apart from "Verified" (an independently admin-reviewed claim, every
// other verification_method value). Not a new field the UI invented --
// the same string app/database/db.py's create_startup_claim() already
// writes and MakeMissionButton/GraduateVentureReview's own callers
// already pass.
export interface StartupClaimStatus {
  claim_id: number;
  status: ClaimStatus;
  verification_method: string;
  submitted_at: string;
  reviewed_at: string | null;
  rejection_reason: string | null;
}

export interface CreateStartupClaimRequest {
  startup_id: number;
  justification: string;
  contact_email?: string | null;
}

export interface StartupClaimActionResponse {
  claim_id: number;
  status: ClaimStatus;
}
