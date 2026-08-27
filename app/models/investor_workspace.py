"""
Phase 9 -- Investor Workspace V1 response contracts. Mirrors
app/ai/investor_workspace.py's dataclasses field-for-field; see that
module's own docstring for the full design record (thresholds, what
"needs attention" means, why there is no new score).
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PillarChangeOut(BaseModel):
    pillar: str
    label: str
    current_score: float | None = None
    previous_score: float | None = None
    delta: float | None = None
    confidence: str | None = None
    evidence_coverage: float | None = None


class WatchedStartupOut(BaseModel):
    startup_id: int
    company_name: str
    industry: str | None = None
    stage: str | None = None
    saved_at: datetime
    latest_analysis_at: datetime | None = None
    has_canonical_analysis: bool
    has_multiple_analyses: bool
    current_sps: float | None = None
    previous_sps: float | None = None
    sps_delta: float | None = None
    overall_confidence: str | None = None
    is_stale: bool
    pillars: list[PillarChangeOut] = Field(default_factory=list)
    attention_reasons: list[str] = Field(default_factory=list)


class RecentChangeOut(BaseModel):
    startup_id: int
    company_name: str
    statement: str
    magnitude: float
    direction: str


class AttentionItemOut(BaseModel):
    startup_id: int
    company_name: str
    reason: str


class InvestorOverviewOut(BaseModel):
    watched_count: int
    startups_with_analysis: int
    average_current_sps: float | None = None
    improved_count: int
    declined_count: int
    recently_analyzed_count: int


class InvestorWorkspaceResponse(BaseModel):
    overview: InvestorOverviewOut
    watched_startups: list[WatchedStartupOut] = Field(default_factory=list)
    recent_changes: list[RecentChangeOut] = Field(default_factory=list)
    attention_items: list[AttentionItemOut] = Field(default_factory=list)
