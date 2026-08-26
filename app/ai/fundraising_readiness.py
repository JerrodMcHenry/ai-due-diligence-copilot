"""
Phase 8 -- Fundraising Readiness V1.

INVESTIGATION FINDING (documented here as the load-bearing design record
for this module): app/ai/readiness_score.py's generate_readiness_score()
-- the only prior "readiness" concept in this codebase -- is a single
ungrounded LLM call that re-scores the SAME six pillar scores + overall
SPS that already produce startup_intelligence_score, with no stage
awareness, no evidence/confidence input, and no determinism (a fresh,
unseeded LLM call every time). It is effectively SPS restated in
different words. The dashboard's own existing code already independently
reached the same conclusion for a sibling field (see
dashboard/app/page.tsx's "Average Readiness was removed here" comment
and dashboard/types/analytics.ts/startup.ts's matching notes) and never
renders it. This module does NOT read from, wrap, or extend
readiness_score/readiness_summary/milestone_readiness_score in any way --
those are left completely untouched for backward compatibility
(executive_coaching_summary, still rendered elsewhere, is sourced from
that same legacy call and this module does not touch that either). This
is a genuinely new, separate, deterministic assessment.

DEFINITION this module implements: "How prepared is this startup to
enter a serious fundraising process at its current stage?" -- distinct
from SPS's "what does the evidence show about this company's quality".
The distinguishing architectural idea: SPS is driven by pillar SCORE.
Fundraising Readiness is driven by how DEFENSIBLE that score is --
confidence and evidence_coverage, stage-weighted -- so a startup can have
high SPS with a great-looking but thinly-evidenced story (low
readiness), or a modest SPS with a well-documented, defensible one
(higher readiness than SPS alone would suggest). See
compute_pillar_readiness()'s own docstring for the exact formula.

DETERMINISM: every function here is pure arithmetic/string logic over
already-computed, already-stored fields (PillarAnalysis.score/confidence/
score_breakdown.evidence_coverage, AnalysisContext.evidence_sources/
analysis_type, SIEContext.company_stage). No LLM call exists anywhere in
this module -- identical input always produces identical output (see
test_fundraising_readiness.py's own determinism test). This mirrors the
same "structured reasoning first, language second" principle
app/ai/scoring.py and app/ai/vps_scoring.py already follow for SPS/VPS.

PERSISTENCE: none. Every value here is recomputed fresh from the
startup's current canonical methodology on every request -- no new table,
no readiness history. See app/api.py's GET /founder/startups/{id}/
fundraising for the one call site, which reuses
get_founder_startup_workspace()'s existing read rather than a new query.
"""

from dataclasses import dataclass, field

PILLAR_KEYS = ("market", "team", "product", "execution", "traction", "financial_health")

PILLAR_LABELS = {
    "market": "Market Opportunity",
    "team": "Team & Founder Case",
    "product": "Product Readiness",
    "execution": "Execution & GTM",
    "traction": "Traction & Validation",
    "financial_health": "Financial Preparedness",
}

CONFIDENCE_MULTIPLIER = {"Low": 0.4, "Medium": 0.7, "High": 1.0}

READINESS_BANDS = (
    (0, 35, "Early"),
    (35, 60, "Developing"),
    (60, 80, "Getting Ready"),
    (80, 101, "Raise Ready"),
)

# Canonical stage vocabulary, matching exactly what
# app/ai/structured_analysis.py's own extraction prompt instructs the LLM
# to use ("stage should be one of: Idea, Pre-Seed, Seed, Series A,
# Series B+, Growth") -- reused here rather than inventing a second stage
# taxonomy. Series B+ and Growth share one weight profile below (both
# represent "later stage, evidence-heavy expectations").
#
# Each profile is a per-pillar weight (sums to 1.0) reflecting what a
# fundraising conversation actually expects to be well-evidenced at that
# stage -- e.g. a pre-seed company is not expected to have strong
# Traction/Financial evidence, so those carry less weight (never zero --
# any real evidence there still helps, it just isn't required to be
# "ready"). This is the readiness-aggregation analog of what Methodology
# v2's own per-dimension stage_guidance already does at the LLM-scoring
# layer (app/ai/scoring_methodology.py) -- applied here, deterministically,
# one layer up, at aggregation rather than scoring.
STAGE_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "idea": {
        "market": 0.30, "team": 0.30, "product": 0.20,
        "execution": 0.10, "traction": 0.05, "financial_health": 0.05,
    },
    "pre-seed": {
        "market": 0.25, "team": 0.25, "product": 0.20,
        "execution": 0.15, "traction": 0.10, "financial_health": 0.05,
    },
    "seed": {
        "market": 0.20, "team": 0.15, "product": 0.15,
        "execution": 0.15, "traction": 0.25, "financial_health": 0.10,
    },
    "series a": {
        "market": 0.15, "team": 0.10, "product": 0.15,
        "execution": 0.15, "traction": 0.25, "financial_health": 0.20,
    },
    "series b+": {
        "market": 0.10, "team": 0.10, "product": 0.10,
        "execution": 0.15, "traction": 0.25, "financial_health": 0.30,
    },
    "growth": {
        "market": 0.10, "team": 0.10, "product": 0.10,
        "execution": 0.15, "traction": 0.25, "financial_health": 0.30,
    },
}

# Unrecognized/empty stage: equal weight across all six pillars rather
# than guessing which stage-specific profile applies -- an honest
# fallback, not a fabricated default.
_EQUAL_WEIGHT_PROFILE = {key: 1.0 / len(PILLAR_KEYS) for key in PILLAR_KEYS}


def normalize_stage(raw_stage: str | None) -> str | None:
    """Returns the canonical lowercase stage key used by
    STAGE_WEIGHT_PROFILES, or None if the stage is empty/unrecognized.
    Never guesses -- an unrecognized stage string (e.g. a company_stage
    the LLM extracted outside the standard vocabulary) falls back to the
    equal-weight profile via resolve_stage_weights(), not a fabricated
    stage label."""
    if not raw_stage:
        return None

    normalized = raw_stage.strip().lower()
    return normalized if normalized in STAGE_WEIGHT_PROFILES else None


def resolve_stage_weights(raw_stage: str | None) -> dict[str, float]:
    stage_key = normalize_stage(raw_stage)
    return dict(STAGE_WEIGHT_PROFILES[stage_key]) if stage_key else dict(_EQUAL_WEIGHT_PROFILE)


@dataclass
class PillarReadinessInput:
    """The minimal slice of a real PillarAnalysis this module needs --
    kept as a plain dataclass (not a dependency on app.models.startup)
    so this module has zero import coupling to the Methodology v2 model
    layer; the API layer is responsible for extracting these five values
    from the real SIEMethodologyAnalysis."""
    score: float | None
    confidence: str
    evidence_coverage: float
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)


@dataclass
class PillarReadiness:
    pillar: str
    label: str
    score: float | None
    confidence: str
    evidence_coverage: float
    weight: float
    # 0-10 scale, same range as the underlying pillar score -- None when
    # the pillar itself is Unavailable (score is None). Never a
    # fabricated 0.
    readiness_contribution: float | None
    top_strength: str | None
    top_weakness: str | None


def compute_pillar_readiness(
    pillar_key: str, pillar_input: PillarReadinessInput, weight: float
) -> PillarReadiness:
    """
    The one formula this whole module's numeric score rests on:

        readiness_contribution = score * (0.3 + 0.7 * defensibility)
        defensibility = average(confidence_multiplier, evidence_coverage_fraction)

    A pillar with a strong score (9/10) but Low confidence and 20%
    evidence coverage is heavily discounted (defensibility ~0.3 ->
    contribution ~9*0.51 ~= 4.6): a great-sounding but thinly-evidenced
    story that would not survive investor diligence. A pillar with a
    modest score (5/10) but High confidence and 90% coverage keeps most
    of its value (defensibility ~0.95 -> contribution ~5*0.965 ~= 4.8):
    a well-documented, defensible story even if not exceptional. This is
    the concrete mechanism behind this phase's own worked examples
    ("high SPS + low fundraising readiness" and the reverse).

    Returns readiness_contribution=None (never 0) when the pillar itself
    has no score (Unavailable) -- excluded from the weighted aggregate
    entirely by the caller, the same "no default substituted" rule
    Methodology v2 itself applies to its own Unavailable dimensions.
    """
    if pillar_input.score is None:
        contribution = None
    else:
        confidence_multiplier = CONFIDENCE_MULTIPLIER.get(pillar_input.confidence, 0.4)
        coverage_fraction = max(0.0, min(1.0, pillar_input.evidence_coverage / 100.0))
        defensibility = (confidence_multiplier + coverage_fraction) / 2.0
        contribution = pillar_input.score * (0.3 + 0.7 * defensibility)

    return PillarReadiness(
        pillar=pillar_key,
        label=PILLAR_LABELS[pillar_key],
        score=pillar_input.score,
        confidence=pillar_input.confidence,
        evidence_coverage=pillar_input.evidence_coverage,
        weight=weight,
        readiness_contribution=contribution,
        top_strength=pillar_input.strengths[0] if pillar_input.strengths else None,
        top_weakness=pillar_input.weaknesses[0] if pillar_input.weaknesses else None,
    )


def band_for_score(score: float) -> str:
    for low, high, label in READINESS_BANDS:
        if low <= score < high:
            return label
    return READINESS_BANDS[-1][2]


def aggregate_readiness_score(pillar_readiness: list[PillarReadiness]) -> tuple[float | None, str | None]:
    """
    Weighted average of readiness_contribution (0-10 scale) across every
    pillar that HAS a contribution, renormalizing weights over just
    those pillars -- identical "exclude, don't default" discipline
    get_founder_startup_workspace()-adjacent scoring already uses.
    Returns (None, None) if every pillar is Unavailable -- never a
    fabricated 0/100.
    """
    scored = [p for p in pillar_readiness if p.readiness_contribution is not None]

    if not scored:
        return None, None

    total_weight = sum(p.weight for p in scored) or 1.0
    weighted_sum = sum(p.readiness_contribution * p.weight for p in scored)
    score_0_to_10 = weighted_sum / total_weight
    score_0_to_100 = round(max(0.0, min(100.0, score_0_to_10 * 10)), 1)

    return score_0_to_100, band_for_score(score_0_to_100)


@dataclass
class ReadinessGap:
    category: str
    pillar: str | None
    issue: str
    why_it_matters: str
    recommended_next_step: str
    source_text: str  # dedup/Action-Plan-provenance key, see app/api.py


GAP_SEVERITY_ORDER = {"unavailable": 0, "low_confidence": 1, "weak_score": 2}


def _lower_label(label: str) -> str:
    """Lowercases a pillar label for mid-sentence use, without mangling
    an all-caps acronym like "GTM" in "Execution & GTM" into "gtm"."""
    return " ".join(word if word.isupper() else word.lower() for word in label.split())


def _gap_for_pillar(pillar: PillarReadiness, stage_label: str) -> tuple[str, ReadinessGap] | None:
    if pillar.score is None:
        if pillar.weight < 0.12:
            # Stage-appropriate absence (e.g. Traction at Idea stage) --
            # not a gap, matching Part 4's "do not punish a pre-seed
            # company for lacking Series A metrics."
            return None
        issue = f"No usable evidence yet for {_lower_label(pillar.label)}, which matters at {stage_label}."
        return "unavailable", ReadinessGap(
            category="insufficient_evidence_for_stage",
            pillar=pillar.pillar,
            issue=issue,
            why_it_matters=f"Investors evaluating a {stage_label.lower()} company will expect some grounded evidence here.",
            recommended_next_step=f"Gather and record real evidence for {_lower_label(pillar.label)} (see Founder Workspace's Action Plan/Updates).",
            source_text=issue,
        )

    if pillar.confidence == "Low" or pillar.evidence_coverage < 40:
        weakness = pillar.top_weakness or f"limited evidence coverage in {_lower_label(pillar.label)}"
        issue = f"{pillar.label}: {weakness}"
        return "low_confidence", ReadinessGap(
            category="weak_evidence",
            pillar=pillar.pillar,
            issue=issue,
            why_it_matters="Thin or low-confidence evidence is unlikely to hold up under investor diligence, even if the underlying story is good.",
            recommended_next_step=f"Strengthen the evidence behind {_lower_label(pillar.label)} before relying on it in a pitch.",
            source_text=issue,
        )

    if pillar.score < 5.0:
        weakness = pillar.top_weakness or f"{_lower_label(pillar.label)} scored below average"
        issue = f"{pillar.label}: {weakness}"
        return "weak_score", ReadinessGap(
            category="likely_investor_scrutiny",
            pillar=pillar.pillar,
            issue=issue,
            why_it_matters="This is likely to draw direct investor pushback in a fundraising conversation.",
            recommended_next_step=f"Be ready to address {_lower_label(pillar.label)} directly, or improve it before raising.",
            source_text=issue,
        )

    return None


def compute_gaps(pillar_readiness: list[PillarReadiness], stage_label: str, has_pitch_deck: bool, max_gaps: int = 5) -> list[ReadinessGap]:
    """Only surfaces gaps actually supported by computed data -- never a
    manufactured investor objection. Capped and severity-sorted so the
    founder sees the handful that matter most, not every subscore."""
    ranked: list[tuple[int, ReadinessGap]] = []

    for pillar in pillar_readiness:
        result = _gap_for_pillar(pillar, stage_label)
        if result is not None:
            severity_key, gap = result
            ranked.append((GAP_SEVERITY_ORDER[severity_key], gap))

    if not has_pitch_deck:
        issue = "No pitch deck has been analyzed by SIE yet."
        ranked.append((0, ReadinessGap(
            category="materials",
            pillar=None,
            issue=issue,
            why_it_matters="Most fundraising conversations start from a deck -- SIE can't yet assess what yours communicates.",
            recommended_next_step="Analyze your pitch deck so SIE can factor its content into future assessments.",
            source_text=issue,
        )))

    ranked.sort(key=lambda pair: pair[0])
    return [gap for _, gap in ranked[:max_gaps]]


# Deterministic gap-category -> investor-question templates. No LLM
# anywhere in this module (Part 8's own requirement: "Do not let an LLM
# determine the score" -- here, extended to "determine the questions"
# too, since a template fill is simpler, fully deterministic, and
# sufficient for V1). Every question is filled from the SAME gap data
# already shown to the founder -- never a fact the gap didn't already
# state.
_QUESTION_TEMPLATES = {
    "insufficient_evidence_for_stage": "What evidence can you show for {pillar_lower}?",
    "weak_evidence": "How would you defend {pillar_lower} under direct diligence questions?",
    "likely_investor_scrutiny": "How do you respond to concerns about {pillar_lower}?",
    "materials": "Can you walk me through your pitch deck?",
}


def compute_investor_questions(gaps: list[ReadinessGap]) -> list[str]:
    questions: list[str] = []
    seen: set[str] = set()

    for gap in gaps:
        template = _QUESTION_TEMPLATES.get(gap.category)
        if not template:
            continue

        pillar_lower = PILLAR_LABELS.get(gap.pillar, "this area").lower() if gap.pillar else "this area"
        question = template.format(pillar_lower=pillar_lower)

        if question not in seen:
            seen.add(question)
            questions.append(question)

    return questions


@dataclass
class ChecklistItem:
    category: str
    status: str  # "Ready" | "Needs Work" | "Missing / Unknown"
    note: str


def _checklist_status_for_pillar(pillar: PillarReadiness) -> tuple[str, str]:
    if pillar.score is None:
        return "Missing / Unknown", "No usable evidence yet."
    if pillar.confidence != "Low" and pillar.evidence_coverage >= 60 and pillar.score >= 6:
        return "Ready", "Well-evidenced and holding up."
    if pillar.confidence == "Low" or pillar.evidence_coverage < 40:
        return "Needs Work", "Evidence is thin or low-confidence."
    return "Needs Work", "Present, but not yet strong enough to rely on."


def compute_checklist(pillar_readiness_by_key: dict[str, PillarReadiness], has_pitch_deck: bool) -> list[ChecklistItem]:
    """
    Only includes categories SIE can honestly assess. Deliberately
    excludes "Use of Funds" and general "data room completeness" --
    SIE has no field capturing either today (no use-of-funds extraction,
    no diligence-document inventory), so including them would fabricate
    a judgment. "Investor Narrative" is Market+Team combined (the two
    dimensions a coherent narrative actually rests on); "Pitch Deck" is
    presence-only (Ready/Missing), never a quality judgment this module
    doesn't have grounds to make (Part 10's own constraint).
    """
    market = pillar_readiness_by_key.get("market")
    team = pillar_readiness_by_key.get("team")
    traction = pillar_readiness_by_key.get("traction")
    financial = pillar_readiness_by_key.get("financial_health")

    items: list[ChecklistItem] = []

    if market is not None and team is not None:
        narrative_pillars = [market, team]
        if any(p.score is None for p in narrative_pillars):
            items.append(ChecklistItem("Investor Narrative", "Missing / Unknown", "Market or team evidence is not yet available."))
        else:
            statuses = [_checklist_status_for_pillar(p)[0] for p in narrative_pillars]
            status = "Ready" if all(s == "Ready" for s in statuses) else "Needs Work"
            items.append(ChecklistItem("Investor Narrative", status, "Derived from Market + Team readiness."))

    if market is not None:
        status, note = _checklist_status_for_pillar(market)
        items.append(ChecklistItem("Market Evidence", status, note))

    if traction is not None:
        status, note = _checklist_status_for_pillar(traction)
        items.append(ChecklistItem("Traction Evidence", status, note))

    if financial is not None:
        status, note = _checklist_status_for_pillar(financial)
        items.append(ChecklistItem("Financial Preparation", status, note))

    items.append(
        ChecklistItem("Pitch Deck Analyzed", "Ready", "SIE has analyzed a pitch deck for this startup.")
        if has_pitch_deck
        else ChecklistItem("Pitch Deck Analyzed", "Missing / Unknown", "No pitch deck has been analyzed by SIE yet.")
    )

    return items


@dataclass
class FundraisingReadinessAssessment:
    has_canonical_analysis: bool
    stage_label: str
    stage_recognized: bool
    readiness_score: float | None
    readiness_band: str | None
    pillar_readiness: list[PillarReadiness]
    gaps: list[ReadinessGap]
    investor_questions: list[str]
    checklist: list[ChecklistItem]
    has_pitch_deck: bool
    pitch_deck_note: str


def _extract_pillar_input(methodology: dict, pillar_key: str) -> PillarReadinessInput:
    """Reads directly from the raw methodology dict (the same JSONB shape
    get_founder_startup_workspace() already returns) -- deliberately not
    coupled to the app.models.startup Pydantic classes, so this whole
    module stays testable with plain dicts/dataclasses and has zero
    import surface into the Methodology v2 model layer. Missing keys
    degrade to honest "Unavailable" defaults, never fabricated scores --
    the same posture every other reader of this JSONB takes for an
    analysis stored before a given field existed."""
    pillar = methodology.get(pillar_key) or {}
    breakdown = pillar.get("score_breakdown") or {}

    return PillarReadinessInput(
        score=pillar.get("score"),
        confidence=pillar.get("confidence") or "Low",
        evidence_coverage=breakdown.get("evidence_coverage") or 0.0,
        strengths=pillar.get("strengths") or [],
        weaknesses=pillar.get("weaknesses") or [],
    )


def assess_fundraising_readiness(methodology: dict | None) -> FundraisingReadinessAssessment:
    """
    The one entry point app/api.py calls. methodology is the raw dict
    already returned by get_founder_startup_workspace() -- None when this
    startup has no canonical analysis yet (Part 18: honest "SIE needs an
    analysis" state, never a fabricated 0/100).
    """
    if methodology is None:
        return FundraisingReadinessAssessment(
            has_canonical_analysis=False,
            stage_label="Unknown stage",
            stage_recognized=False,
            readiness_score=None,
            readiness_band=None,
            pillar_readiness=[],
            gaps=[],
            investor_questions=[],
            checklist=[],
            has_pitch_deck=False,
            pitch_deck_note="No pitch deck has been analyzed by SIE yet.",
        )

    context = methodology.get("context") or {}
    raw_stage = context.get("company_stage") or context.get("funding_stage") or None
    stage_key = normalize_stage(raw_stage)
    stage_label = raw_stage.strip() if (raw_stage and stage_key) else "Unrecognized/unknown stage"
    weights = resolve_stage_weights(raw_stage)

    pillar_readiness = [
        compute_pillar_readiness(key, _extract_pillar_input(methodology, key), weights[key])
        for key in PILLAR_KEYS
    ]
    pillar_readiness_by_key = {p.pillar: p for p in pillar_readiness}

    readiness_score, readiness_band = aggregate_readiness_score(pillar_readiness)

    analysis_context = methodology.get("analysis_context") or {}
    evidence_sources = analysis_context.get("evidence_sources") or []
    analysis_type = analysis_context.get("analysis_type") or ""
    has_pitch_deck = "pitch_deck" in evidence_sources or analysis_type == "pitch_deck"
    pitch_deck_note = (
        "SIE has analyzed a pitch deck for this startup."
        if has_pitch_deck
        else "No pitch deck has been analyzed by SIE yet."
    )

    gaps = compute_gaps(pillar_readiness, stage_label, has_pitch_deck)
    investor_questions = compute_investor_questions(gaps)
    checklist = compute_checklist(pillar_readiness_by_key, has_pitch_deck)

    return FundraisingReadinessAssessment(
        has_canonical_analysis=True,
        stage_label=stage_label,
        stage_recognized=stage_key is not None,
        readiness_score=readiness_score,
        readiness_band=readiness_band,
        pillar_readiness=pillar_readiness,
        gaps=gaps,
        investor_questions=investor_questions,
        checklist=checklist,
        has_pitch_deck=has_pitch_deck,
        pitch_deck_note=pitch_deck_note,
    )
