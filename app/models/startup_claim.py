"""
Phase 7.1A -- Startup Claim & Membership backend lifecycle. Request/
response contracts only -- see app/database/db.py's Phase 7.1A section
for the actual state machine and its own invariant statement (only
approve_startup_claim() may ever write startup_memberships).

Deliberately its own file, not folded into app/models/startup.py --
claims are a distinct concern (a pending, reviewable request) from
canonical Startup intelligence, the same reasoning app/models/idea_lab.py
already applies to modeled ventures.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ClaimStatus = Literal["pending", "approved", "rejected", "cancelled"]


class CreateStartupClaimRequest(BaseModel):
    startup_id: int
    justification: str = Field(min_length=1, max_length=2000)
    # Deliberately optional and NEVER labeled "verified" anywhere in this
    # system -- self-reported context for a human reviewer, not a
    # verification mechanism (see the Phase 7.1 design report's Part 3).
    contact_email: str | None = Field(default=None, max_length=320)


class StartupClaimSubmissionResponse(BaseModel):
    id: int
    startup_id: int
    status: ClaimStatus


class MyStartupClaim(BaseModel):
    """GET /me/startup-claims row shape -- the caller's own claims only.
    Deliberately excludes justification/contact_email (not part of the
    approved field list) and is structurally incapable of naming another
    user, since list_startup_claims_for_user() only ever selects rows
    matching the caller's own user_id."""
    id: int
    startup_id: int
    canonical_name: str
    status: ClaimStatus
    verification_method: str
    submitted_at: datetime
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None


class StartupClaimStatus(BaseModel):
    """Smallest single-startup helper for Phase 7.1B's future 'Claim this
    startup' control. The endpoint returns this or null -- never reveals
    whether anyone ELSE has claimed the same startup."""
    claim_id: int
    status: ClaimStatus
    submitted_at: datetime
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None


class AdminStartupClaim(BaseModel):
    """GET /admin/startup-claims row shape -- admin-only (RequireAdmin).
    Carries exactly what a human reviewer needs: who's claiming what,
    their own justification/contact info, and how many members the
    startup already has (context, never a submission blocker)."""
    id: int
    startup_id: int
    canonical_name: str
    user_id: str
    user_email: str | None = None
    contact_email: str | None = None
    justification: str | None = None
    submitted_at: datetime
    existing_member_count: int


class RejectStartupClaimRequest(BaseModel):
    rejection_reason: str = Field(min_length=1, max_length=2000)


class StartupClaimActionResponse(BaseModel):
    claim_id: int
    status: ClaimStatus
