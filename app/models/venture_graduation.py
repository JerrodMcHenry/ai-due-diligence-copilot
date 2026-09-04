"""
Phase 31 -- Venture -> Startup Graduation V1. Request/response contracts
only -- see app/database/db.py's venture_graduations section for the
persistence and reasoning this backs, and
docs/product/VENTURE_TO_STARTUP_GRADUATION_V1.md for the full design
record.

Deliberately excludes any eligibility/suggestion field: Part 2/3's
eligibility check is a pure, client-side function
(dashboard/lib/journey/resolveGraduationEligibility.ts) over assumptions
the founder's browser already has loaded -- no AI, no VPS, no new score,
so there is nothing for the backend to compute or cache here. This file
only carries the two things that genuinely require a server round trip:
"has this venture already graduated" and "create the graduation".
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

GraduationTrigger = Literal["suggested", "manual"]


class VentureGraduationStatus(BaseModel):
    """GET /ventures/{venture_id}/graduation. graduated=False means every
    other field is None -- never a partially-populated "sort of
    graduated" state, matching venture_graduations' own UNIQUE(venture_id)
    all-or-nothing row."""
    graduated: bool
    startup_id: int | None = None
    startup_name: str | None = None
    connected_existing_startup: bool = False
    graduated_at: datetime | None = None


class GraduateVentureRequest(BaseModel):
    """
    company_name: the founder's own chosen company name for the new
    Startup -- deliberately NOT auto-filled from venture.name without
    review (Part 15: "the founder decides what the company is called"),
    though the review screen pre-fills this input with venture.name as a
    convenience default the founder can edit before submitting.

    connect_existing_startup_id: Part 13's "Connect existing Startup"
    case. When set, company_name is ignored server-side (the target
    startup's own existing canonical_name is authoritative) and
    resolve_startup_for_graduation()'s collision logic is bypassed
    entirely in favor of a direct RequireStartupMember-equivalent
    ownership check on this exact id -- see the endpoint's own docstring
    in app/api.py.
    """
    company_name: str = Field(min_length=1, max_length=200)
    trigger: GraduationTrigger
    connect_existing_startup_id: int | None = None
    # Analytics-only, never persisted as venture/startup content -- the
    # count of SAFE + REVIEW-classified fields the frontend's own summary
    # builder (ventureToStartupHandoff.ts) actually included in the
    # pre-fill text it stashed for /analyze. Purely a number for
    # `venture_graduated`'s event metadata (Part 14); defaults to 0 so an
    # older/other caller never fails validation.
    fields_transferred_count: int = Field(default=0, ge=0, le=100)


class GraduateVentureResponse(BaseModel):
    startup_id: int
    startup_name: str
    connected_existing_startup: bool
