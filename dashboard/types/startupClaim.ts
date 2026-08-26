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

export interface StartupClaimStatus {
  claim_id: number;
  status: ClaimStatus;
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
