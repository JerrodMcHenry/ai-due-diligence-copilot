"""
Phase 9 -- Investor Workspace V1.

Turns Saved Startups (the existing bookmark relationship -- see
save_startup_for_user()/get_saved_startups_for_user() in app/database/db.py)
into an intelligence layer: "what changed across the startups I'm
watching, and what deserves attention." Everything here is a deterministic
re-derivation of canonical intelligence already stored in `analyses.
methodology` -- there is no LLM call anywhere in this module, no new
persistence, and no new score. It never writes anything back; it only
reads app.database.db.get_watchlist_startups_for_user()'s output and
diffs it.

This is NOT a second scoring system. It reuses the exact SPS
(startup_intelligence_score) and six pillar scores Methodology v2 already
computes; it never recomputes, re-weights, or re-labels them. The only
new concepts introduced here are:

  1. A deterministic delta between a startup's latest and previous
     canonical analysis (SPS and per-pillar).
  2. A restrained, transparent "meaningful change" filter so the investor
     sees signal, not every 0.1-point wobble.
  3. Deterministic, fully-explained "needs attention" reasons -- never a
     hidden proprietary score. Every attention item names the exact
     fact that triggered it (e.g. "Financial Health declined 0.8").

Meaningful-change thresholds (investigated against real dev data before
being chosen -- see Phase 9's own investigation report):

  Across the three startups in the dev database with two canonical
  analyses each (Linear, Ramp Business Corporation, X), observed pillar
  deltas cluster into two clearly separated bands: a noise band at
  0.0-0.4 (0.0, 0.0, 0.0, 0.1, 0.2, 0.3, 0.4 all occurred) and a signal
  band at 0.8-2.0 (0.8, 0.9, 1.0, 2.0 all occurred). PILLAR_MEANINGFUL_
  CHANGE_THRESHOLD = 0.5 sits in the empirically-observed gap between
  those two bands. The same three startups' SPS deltas were all exactly
  1.8 (in either direction) -- SPS_MEANINGFUL_CHANGE_THRESHOLD = 1.5 is a
  clean round number below that single observed magnitude; there isn't
  yet enough real SPS-delta variety to tune it further, so it is
  deliberately conservative (flags real observed changes, but would also
  flag anything smaller down to 1.5 -- revisit once more re-analysis
  history exists).

STALE_ANALYSIS_DAYS (90) and RECENTLY_ANALYZED_DAYS (14) have no existing
precedent elsewhere in the codebase to reuse; they are editorial choices
documented here, not derived from data (every analysis in the current dev
database is under 3 days old, so neither constant currently changes any
demo output -- see the Phase 9 report's live-verification section).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


PILLAR_KEYS = ("market", "team", "product", "execution", "traction", "financial_health")

PILLAR_LABELS = {
    "market": "Market",
    "team": "Team",
    "product": "Product",
    "execution": "Execution",
    "traction": "Traction",
    "financial_health": "Financial Health",
}

CONFIDENCE_RANK = {"Low": 0, "Medium": 1, "High": 2}

# See module docstring for how these were chosen.
SPS_MEANINGFUL_CHANGE_THRESHOLD = 1.5
PILLAR_MEANINGFUL_CHANGE_THRESHOLD = 0.5
STALE_ANALYSIS_DAYS = 90
RECENTLY_ANALYZED_DAYS = 14

MAX_RECENT_CHANGES = 8
MAX_ATTENTION_ITEMS = 8


@dataclass
class PillarChange:
    pillar: str
    label: str
    current_score: float | None
    previous_score: float | None
    delta: float | None
    confidence: str | None
    evidence_coverage: float | None


@dataclass
class AttentionReason:
    reason: str
    # Kept for ordering only -- never surfaced as a raw number to the
    # investor (Part 7: "do not create a mysterious proprietary Investor
    # Score"). The reason string itself is always the actual fact.
    severity: float


@dataclass
class WatchedStartup:
    startup_id: int
    company_name: str
    industry: str | None
    stage: str | None
    saved_at: datetime
    latest_analysis_at: datetime | None
    has_canonical_analysis: bool
    has_multiple_analyses: bool
    current_sps: float | None
    previous_sps: float | None
    sps_delta: float | None
    overall_confidence: str | None
    is_stale: bool
    pillars: list[PillarChange] = field(default_factory=list)
    attention_reasons: list[str] = field(default_factory=list)

    @property
    def needs_attention(self) -> bool:
        return len(self.attention_reasons) > 0


@dataclass
class RecentChange:
    startup_id: int
    company_name: str
    statement: str
    magnitude: float
    direction: str  # "up" | "down"


@dataclass
class AttentionItem:
    startup_id: int
    company_name: str
    reason: str


@dataclass
class InvestorOverview:
    watched_count: int
    startups_with_analysis: int
    average_current_sps: float | None
    improved_count: int
    declined_count: int
    recently_analyzed_count: int


@dataclass
class InvestorWorkspaceAssessment:
    overview: InvestorOverview
    watched_startups: list[WatchedStartup]
    recent_changes: list[RecentChange]
    attention_items: list[AttentionItem]


def _overall_confidence(methodology: dict) -> str | None:
    """
    Mode of the six pillars' current confidence, ties broken toward the
    lowest confidence present -- the exact same "majority vote" definition
    dashboard/components/startup/StartupHeroV2.tsx's getOverallConfidence()
    already uses for the same concept elsewhere in the product, not a new
    or competing definition of "overall confidence."
    """
    counts = {"Low": 0, "Medium": 0, "High": 0}

    for pillar_key in PILLAR_KEYS:
        pillar = methodology.get(pillar_key) or {}
        confidence = pillar.get("confidence")
        if confidence in counts:
            counts[confidence] += 1

    if sum(counts.values()) == 0:
        return None

    best = "Low"
    for level in ("Low", "Medium", "High"):
        if counts[level] > counts[best]:
            best = level

    return best


def _pillar_changes(latest_methodology: dict | None, previous_methodology: dict | None) -> list[PillarChange]:
    changes = []

    for key in PILLAR_KEYS:
        latest_pillar = (latest_methodology or {}).get(key) or {}
        previous_pillar = (previous_methodology or {}).get(key) or {}

        current_score = latest_pillar.get("score")
        previous_score = previous_pillar.get("score") if previous_methodology is not None else None

        delta = (
            current_score - previous_score
            if current_score is not None and previous_score is not None
            else None
        )

        score_breakdown = latest_pillar.get("score_breakdown") or {}

        changes.append(PillarChange(
            pillar=key,
            label=PILLAR_LABELS[key],
            current_score=current_score,
            previous_score=previous_score,
            delta=delta,
            confidence=latest_pillar.get("confidence"),
            evidence_coverage=score_breakdown.get("evidence_coverage"),
        ))

    return changes


def _attention_reasons_for(
    sps_delta: float | None,
    pillars: list[PillarChange],
    overall_confidence: str | None,
    is_stale: bool,
    latest_analysis_at: datetime | None,
    now: datetime,
) -> list[AttentionReason]:
    reasons: list[AttentionReason] = []

    if sps_delta is not None and sps_delta <= -SPS_MEANINGFUL_CHANGE_THRESHOLD:
        reasons.append(AttentionReason(
            reason=f"Startup Power Score declined {abs(sps_delta):.1f} points since the previous analysis.",
            severity=abs(sps_delta),
        ))

    for pillar in pillars:
        if pillar.delta is not None and pillar.delta <= -PILLAR_MEANINGFUL_CHANGE_THRESHOLD:
            reasons.append(AttentionReason(
                reason=f"{pillar.label} declined {abs(pillar.delta):.1f} since the previous analysis.",
                severity=abs(pillar.delta),
            ))

    if overall_confidence == "Low":
        reasons.append(AttentionReason(
            reason="Current intelligence is Low confidence overall.",
            severity=0.1,
        ))

    if is_stale and latest_analysis_at is not None:
        age_days = (now - latest_analysis_at).days
        reasons.append(AttentionReason(
            reason=f"Last analyzed {age_days} days ago -- may be out of date.",
            severity=0.05,
        ))

    reasons.sort(key=lambda item: item.severity, reverse=True)
    return reasons


def _watched_startup_from_row(row: dict, now: datetime) -> WatchedStartup:
    latest = row.get("latest")
    previous = row.get("previous")

    latest_methodology = latest["methodology"] if latest else None
    previous_methodology = previous["methodology"] if previous else None

    context = (latest_methodology or {}).get("context") or {}
    industry = context.get("industry") or None
    stage = context.get("company_stage") or None

    current_sps = latest_methodology.get("startup_intelligence_score") if latest_methodology else None
    previous_sps = previous_methodology.get("startup_intelligence_score") if previous_methodology else None

    sps_delta = (
        current_sps - previous_sps
        if current_sps is not None and previous_sps is not None
        else None
    )

    latest_analysis_at = latest["created_at"] if latest else None

    is_stale = False
    if latest_analysis_at is not None:
        reference = latest_analysis_at
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        is_stale = (now - reference).days >= STALE_ANALYSIS_DAYS

    pillars = _pillar_changes(latest_methodology, previous_methodology)
    overall_confidence = _overall_confidence(latest_methodology) if latest_methodology else None

    reasons = _attention_reasons_for(
        sps_delta=sps_delta,
        pillars=pillars,
        overall_confidence=overall_confidence,
        is_stale=is_stale,
        latest_analysis_at=latest_analysis_at,
        now=now,
    )

    return WatchedStartup(
        startup_id=row["startup_id"],
        company_name=row["company_name"],
        industry=industry,
        stage=stage,
        saved_at=row["saved_at"],
        latest_analysis_at=latest_analysis_at,
        has_canonical_analysis=latest is not None,
        has_multiple_analyses=previous is not None,
        current_sps=current_sps,
        previous_sps=previous_sps,
        sps_delta=sps_delta,
        overall_confidence=overall_confidence,
        is_stale=is_stale,
        pillars=pillars,
        attention_reasons=[item.reason for item in reasons],
    )


def _build_overview(watched: list[WatchedStartup], now: datetime) -> InvestorOverview:
    with_analysis = [w for w in watched if w.has_canonical_analysis]
    scores = [w.current_sps for w in with_analysis if w.current_sps is not None]

    improved = sum(1 for w in watched if w.sps_delta is not None and w.sps_delta > 0)
    declined = sum(1 for w in watched if w.sps_delta is not None and w.sps_delta < 0)

    recently_analyzed = 0
    for w in with_analysis:
        if w.latest_analysis_at is None:
            continue
        reference = w.latest_analysis_at
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)
        if (now - reference).days <= RECENTLY_ANALYZED_DAYS:
            recently_analyzed += 1

    return InvestorOverview(
        watched_count=len(watched),
        startups_with_analysis=len(with_analysis),
        average_current_sps=round(sum(scores) / len(scores), 1) if scores else None,
        improved_count=improved,
        declined_count=declined,
        recently_analyzed_count=recently_analyzed,
    )


def _build_recent_changes(watched: list[WatchedStartup]) -> list[RecentChange]:
    changes: list[RecentChange] = []

    for w in watched:
        if w.sps_delta is not None and abs(w.sps_delta) >= SPS_MEANINGFUL_CHANGE_THRESHOLD:
            direction = "up" if w.sps_delta > 0 else "down"
            verb = "increased" if direction == "up" else "declined"
            changes.append(RecentChange(
                startup_id=w.startup_id,
                company_name=w.company_name,
                statement=f"{w.company_name}'s Startup Power Score {verb} {abs(w.sps_delta):.1f} point{'s' if abs(round(w.sps_delta, 1)) != 1 else ''}.",
                magnitude=abs(w.sps_delta),
                direction=direction,
            ))

        for pillar in w.pillars:
            if pillar.delta is not None and abs(pillar.delta) >= PILLAR_MEANINGFUL_CHANGE_THRESHOLD:
                direction = "up" if pillar.delta > 0 else "down"
                verb = "increased" if direction == "up" else "declined"
                changes.append(RecentChange(
                    startup_id=w.startup_id,
                    company_name=w.company_name,
                    statement=f"{w.company_name}'s {pillar.label} score {verb} {abs(pillar.delta):.1f}.",
                    magnitude=abs(pillar.delta),
                    direction=direction,
                ))

    changes.sort(key=lambda item: item.magnitude, reverse=True)
    return changes[:MAX_RECENT_CHANGES]


def _build_attention_items(watched: list[WatchedStartup]) -> list[AttentionItem]:
    items: list[AttentionItem] = []

    for w in watched:
        for reason in w.attention_reasons:
            items.append(AttentionItem(
                startup_id=w.startup_id,
                company_name=w.company_name,
                reason=reason,
            ))

    return items[:MAX_ATTENTION_ITEMS]


def assess_investor_workspace(watchlist_rows: list[dict], now: datetime | None = None) -> InvestorWorkspaceAssessment:
    """
    Top-level entry point. `watchlist_rows` is exactly
    get_watchlist_startups_for_user()'s return value -- this function does
    no database access of its own, which keeps it trivially unit-testable
    and keeps "what data feeds this" auditable in one place (app/api.py's
    endpoint).
    """
    resolved_now = now or datetime.now(timezone.utc)

    watched = [_watched_startup_from_row(row, resolved_now) for row in watchlist_rows]

    return InvestorWorkspaceAssessment(
        overview=_build_overview(watched, resolved_now),
        watched_startups=watched,
        recent_changes=_build_recent_changes(watched),
        attention_items=_build_attention_items(watched),
    )
