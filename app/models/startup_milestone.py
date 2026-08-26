"""
Phase 7.4 -- Founder Evidence + Milestones V1. Request/response
contracts only -- see app/database/db.py's own Phase 7.4 section for the
startup_milestones table and its own "never touches scoring" boundary
statement.

Its own file for the same reason app/models/founder_action.py is its own
file: a milestone (a target the startup is trying to reach) is a
distinct concern from an action (something intended) and from a
founder_update (something reported as having happened).
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

MilestoneStatus = Literal["planned", "in_progress", "achieved", "cancelled"]

# Same six pillar keys as FOUNDER_ACTION_PILLARS/FOUNDER_UPDATE_PILLARS.
MILESTONE_PILLARS = frozenset(
    {"market", "team", "product", "execution", "traction", "financial_health"}
)


class StartupMilestone(BaseModel):
    id: int
    startup_id: int
    created_by_user_id: str
    title: str
    description: str | None = None
    related_pillar: str | None = None
    status: MilestoneStatus
    target_date: date | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CreateMilestoneRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    related_pillar: str | None = None
    target_date: date | None = None


class UpdateMilestoneStatusRequest(BaseModel):
    status: MilestoneStatus
