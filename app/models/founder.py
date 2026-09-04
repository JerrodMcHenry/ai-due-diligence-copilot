"""
Phase 7.2 -- Founder Workspace V1. Response contract only -- see
app/database/db.py's get_founder_startup_workspace() for the read this
backs.

Deliberately reuses SIEMethodologyAnalysis (app/models/startup.py) as-is
for the `methodology` field rather than a parallel founder-specific
intelligence model -- Founder Workspace surfaces the exact same canonical
Methodology v2 intelligence the public Startup Profile does, just through
its own membership-gated endpoint (RequireStartupMember), and bundles the
same SPS history GET /startup/{company_name}/sps-history already
provides. This file's own existence is only to shape the ONE response
GET /founder/startups/{startup_id} returns -- it is not a second
intelligence model.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.startup import SIEMethodologyAnalysis


class FounderSPSHistoryPoint(BaseModel):
    analysis_id: int
    created_at: datetime
    startup_intelligence_score: float | None = None


class GraduatedFromVenture(BaseModel):
    """Phase 31 -- Venture -> Startup Graduation V1, Part 11. Present only
    when this startup was created via venture graduation -- the one
    restrained "Created from your X venture" acknowledgment Founder
    Workspace shows, plus a link back to that venture's own history. Never
    carries any venture assumption/evidence content -- see
    get_venture_graduation_by_startup()'s own docstring in
    app/database/db.py."""
    venture_id: int
    venture_name: str


class FounderStartupWorkspace(BaseModel):
    startup_id: int
    canonical_name: str
    # None when this startup has no canonical (methodology IS NOT NULL)
    # analysis yet -- never fabricated. See
    # get_founder_startup_workspace()'s own docstring for why this is
    # deliberately never allowed to disagree with the public Startup
    # Profile's own StartupProfileResponse for the same startup.
    created_at: datetime | None = None
    methodology: SIEMethodologyAnalysis | None = None
    sps_history: list[FounderSPSHistoryPoint] = Field(default_factory=list)
    graduated_from_venture: GraduatedFromVenture | None = None
