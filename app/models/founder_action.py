"""
Phase 7.3 -- Founder Progress & Improvement V1. Request/response
contracts only -- see app/database/db.py's own Phase 7.3 section for the
founder_actions table and its own statement of what this table is (pure
workflow state) and is not (never evidence, never a score, never joined
into scoring).

Its own file for the same reason app/models/startup_claim.py and
app/models/startup_membership.py are their own files: founder progress is
a distinct concern from canonical Startup Intelligence.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FounderActionStatus = Literal["todo", "in_progress", "completed", "dismissed"]
# Phase 8 -- Fundraising Readiness V1 adds "fundraising_gap" alongside
# the existing two sources (backward compatible: existing rows/callers
# using sie_recommendation/founder_created are unaffected). See
# app/database/db.py's add_fundraising_gap_source_to_founder_actions()
# for the corresponding CHECK-constraint migration and
# create_founder_action()'s own dedup discipline, which applies
# identically to this new source (same startup_id+source_ref partial
# unique index, just a third valid `source` value).
FounderActionSource = Literal["sie_recommendation", "founder_created", "fundraising_gap"]

# Mirrors SIEMethodologyAnalysis's six pillar field names exactly
# (app/models/startup.py) -- the only valid values for related_pillar.
FOUNDER_ACTION_PILLARS = frozenset(
    {"market", "team", "product", "execution", "traction", "financial_health"}
)


class FounderAction(BaseModel):
    """GET/POST/PATCH .../actions row shape -- one row per founder_actions
    relationship for a startup. created_by_user_id is provenance only
    (Part 11): it is never used to filter what a member can see, and any
    verified member may act on any action in the same startup's shared
    plan."""
    id: int
    startup_id: int
    created_by_user_id: str
    title: str
    description: str | None = None
    related_pillar: str | None = None
    status: FounderActionStatus
    source: FounderActionSource
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class CreateFounderActionRequest(BaseModel):
    """Covers both Part 6 (founder-created, source defaults to
    'founder_created', related_pillar optional) and Part 5's "Add to
    Plan" (source='sie_recommendation', title is the exact recommendation
    text already shown to this same authenticated founder in this
    startup's own GET /founder/startups/{id} response -- never generated
    server-side, never trusted as evidence, just echoed back to persist
    as a workflow item). source_ref is deliberately NOT a field here --
    see create_founder_action()'s own docstring for why it's derived
    server-side from title instead of accepted from the client."""
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    related_pillar: str | None = None
    source: FounderActionSource = "founder_created"


class UpdateFounderActionStatusRequest(BaseModel):
    status: FounderActionStatus
