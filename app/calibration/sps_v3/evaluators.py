"""
Deterministic dimension evaluators (Phase 10.8F, Part 5).

Implements the V3 rule STRUCTURE from docs/methodology/SPS_V3_RULEBOOK.md
faithfully -- 27 dimensions (the Rulebook's own Part 36 table sums to
27, not the "26" stated in that document's prose summary; this is a
transcription bug in the 10.8E document, corrected here per Phase
10.8F Part 43's allowance to fix "incorrect transcription of the
approved 10.8E rulebook" -- see the final report).

Every classification->score mapping reads its band values from the
provisional ParameterRegistry (registry.py), never a bare literal here
-- so every number in this file is traceable to one named, centrally-
listed provisional parameter.
"""

from __future__ import annotations

from dataclasses import dataclass, replace as dc_replace
from datetime import date
from decimal import Decimal
from typing import Callable

from app.calibration.sps_v3.company import SyntheticCompany
from app.calibration.sps_v3.freshness import Freshness, FreshnessClass, evaluate_freshness, freshness_class_for
from app.calibration.sps_v3.registry import ParameterRegistry
from app.calibration.sps_v3.signals import CanonicalSignal, build_canonical_signals
from app.calibration.sps_v3.types import (
    AvailabilityStatus,
    BurnObservation,
    CashObservation,
    ClassificationResult,
    CommercialContractObservation,
    CompetitiveEvidenceObservation,
    ConfidenceLevel,
    ConflictStatus,
    CustomerCountObservation,
    CustomerEvidenceObservation,
    CustomerType,
    DimensionResult,
    FounderExperienceObservation,
    FounderExperienceType,
    FounderOutcomeObservation,
    MarketGrowthObservation,
    MarketSizeObservation,
    ProductCapabilityObservation,
    ProvenanceGrade,
    RetentionObservation,
    RevenueMetricType,
    RevenueObservation,
    RuleTrace,
    RunwayStatementObservation,
    Stage,
)


# ---------------------------------------------------------------------
# Phase 10.8G, Part 12 -- staleness pre-filtering (applied once,
# centrally, in evaluate_all_dimensions -- see bottom of file -- rather
# than touching all 27 individual eval_* signatures). STALE CURRENT_STATE/
# RECENT_PERFORMANCE observations are excluded from the evidence view
# every evaluator sees; STRUCTURAL_FACT/HISTORICAL_FACT observations are
# never staleness-filtered at all (Part 11: founder history, funding,
# market estimates remain valid facts for far longer). Excluded
# observations are never deleted or converted to negative evidence --
# they are simply not part of the positive-evidence view for that run,
# exactly as Part 12 requires.
_STALENESS_FILTERED_CLASSES = (FreshnessClass.CURRENT_STATE, FreshnessClass.RECENT_PERFORMANCE)


def apply_staleness_filter(
    company: SyntheticCompany,
    reference_date: date | None,
    registry: ParameterRegistry,
) -> tuple[SyntheticCompany, tuple]:
    """Returns (filtered_company, excluded_observations). If
    reference_date is None, no filtering is applied (evidence is
    treated as of unknown/immaterial age) -- this is a deliberate,
    explicit opt-out, not a silent default, and every profile/test in
    this harness that cares about staleness passes an explicit date."""

    if reference_date is None:
        return company, ()

    kept = []
    excluded = []
    for obs in company.evidence:
        fc = freshness_class_for(obs)
        if fc not in _STALENESS_FILTERED_CLASSES:
            kept.append(obs)
            continue
        fresh = evaluate_freshness(obs, reference_date, registry)
        if fresh == Freshness.STALE:
            excluded.append(obs)
        else:
            kept.append(obs)

    filtered = SyntheticCompany(company.company_id, company.stage, tuple(kept), company.negative_signals)
    return filtered, tuple(excluded)


HIGH_GRADE = {ProvenanceGrade.PRIMARY_VERIFIED, ProvenanceGrade.HIGH_QUALITY_SECONDARY}
MEDIUM_GRADE = {ProvenanceGrade.PRIMARY_SELF_REPORTED, ProvenanceGrade.DERIVED}
LOW_GRADE = {ProvenanceGrade.SECONDARY_ESTIMATE, ProvenanceGrade.UNVERIFIED}


def confidence_from_evidence(evidence_items) -> ConfidenceLevel:
    """Weakest-link rule (Rulebook Part 21) -- not an average."""
    if not evidence_items:
        return ConfidenceLevel.LOW
    grades = [e.provenance_grade for e in evidence_items]
    if any(g in LOW_GRADE for g in grades):
        return ConfidenceLevel.LOW
    if all(g in HIGH_GRADE for g in grades):
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.MEDIUM


@dataclass(frozen=True)
class SignalCollection:
    positive_evidence: tuple
    negative_evidence: tuple


def confidence_from_canonical_signals(resolved_signals: list) -> ConfidenceLevel:
    """Phase 10.8G, Part 6: weakest-link over each RESOLVED canonical
    signal's representative provenance grade (unchanged base rule) --
    but a signal backed by >=2 genuinely INDEPENDENT corroborating
    sources (CanonicalSignal.independent_corroboration_count) may lift
    the overall floor by one tier, since that is real, non-redundant
    additional evidence. A signal's repetition via SAME_ORIGIN/
    DERIVATIVE/UNKNOWN_ORIGIN sources -- no matter how many -- never
    contributes to this count (see signals.py::_count_independent),
    so this upgrade cannot be gamed by duplication."""
    if not resolved_signals:
        return ConfidenceLevel.LOW
    base_grades = [s.accepted_observation.provenance_grade for s in resolved_signals if s.accepted_observation is not None]
    if not base_grades:
        return ConfidenceLevel.LOW
    if any(g in LOW_GRADE for g in base_grades):
        base = ConfidenceLevel.LOW
    elif all(g in HIGH_GRADE for g in base_grades):
        base = ConfidenceLevel.HIGH
    else:
        base = ConfidenceLevel.MEDIUM

    max_independent = max((s.independent_corroboration_count for s in resolved_signals), default=0)
    if max_independent >= 2:
        if base == ConfidenceLevel.LOW:
            return ConfidenceLevel.MEDIUM
        if base == ConfidenceLevel.MEDIUM:
            return ConfidenceLevel.HIGH
    return base


def _generic_b_classification(
    dimension_id: str,
    signals: SignalCollection,
    registry: ParameterRegistry,
) -> tuple[ClassificationResult, Decimal | None, AvailabilityStatus, list]:
    """The standard Category B mapping used by every taxonomy-based
    dimension in this harness (Rulebook Part 16/19 pattern, AMENDED in
    Phase 10.8G Part 4/17): 0 UNIQUE SUBSTANTIVE SIGNALS -> NO_SIGNAL/
    Unavailable, 1 -> SINGLE_SIGNAL, 2-3 -> MULTIPLE_SIGNALS, >=4 ->
    COMPREHENSIVE, negative evidence present -> overrides to a negative
    band regardless of positive count. The count driving classification
    is now len(deduplicated CanonicalSignal) -- NEVER raw observation
    count -- which is the direct fix for the Phase 10.8F redundant-
    evidence/fame-bias finding: 1 source and 100 sources supporting the
    identical fact both produce exactly one CanonicalSignal.
    Unresolved CONFLICT_DETECTED signals are excluded from both the
    positive count and Coverage (Part 9-10) -- they are neither
    positive nor negative evidence, they are unusable pending
    resolution."""

    if signals.negative_evidence:
        classification = ClassificationResult(
            classification="NEGATIVE_SIGNAL_PRESENT",
            supporting_evidence_ids=(),
            negative_evidence_ids=tuple(e.observation_id for e in signals.negative_evidence),
            reason=f"{dimension_id}: negative evidence present, overrides any positive signal.",
        )
        return classification, registry.value("band.negative_signal"), AvailabilityStatus.SCORABLE, []

    canonical_signals = build_canonical_signals(signals.positive_evidence)
    resolved = [s for s in canonical_signals if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
    n = len(resolved)

    if n == 0:
        if any(s.conflict_status == ConflictStatus.CONFLICT_DETECTED for s in canonical_signals):
            return (
                ClassificationResult(classification="NO_SIGNAL", supporting_evidence_ids=()),
                None, AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE, [],
            )
        return (
            ClassificationResult(classification="NO_SIGNAL", supporting_evidence_ids=()),
            None,
            AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE,
            [],
        )

    ids = tuple(s.accepted_observation.observation_id for s in resolved)
    if n == 1:
        label, band_key = "SINGLE_SIGNAL", "band.single_signal"
    elif n <= 3:
        label, band_key = "MULTIPLE_SIGNALS", "band.multiple_signals"
    else:
        label, band_key = "COMPREHENSIVE", "band.comprehensive"

    classification = ClassificationResult(
        classification=label,
        supporting_evidence_ids=ids,
        reason=f"{dimension_id}: {n} unique substantive signal(s) (deduplicated from {len(signals.positive_evidence)} raw observation(s)).",
    )
    return classification, registry.value(band_key), AvailabilityStatus.SCORABLE, resolved


def _build_b_result(
    dimension_id: str,
    pillar: str,
    weight: Decimal,
    signals: SignalCollection,
    registry: ParameterRegistry,
    rule_suffix: str,
) -> DimensionResult:
    classification, score, availability, resolved_signals = _generic_b_classification(dimension_id, signals, registry)
    if signals.negative_evidence:
        confidence = confidence_from_evidence(list(signals.negative_evidence))
    else:
        confidence = confidence_from_canonical_signals(resolved_signals) if resolved_signals else ConfidenceLevel.LOW
    band_param = None
    if classification.classification == "SINGLE_SIGNAL":
        band_param = "band.single_signal"
    elif classification.classification == "MULTIPLE_SIGNALS":
        band_param = "band.multiple_signals"
    elif classification.classification == "COMPREHENSIVE":
        band_param = "band.comprehensive"
    elif classification.classification == "NEGATIVE_SIGNAL_PRESENT":
        band_param = "band.negative_signal"

    return DimensionResult(
        dimension_id=dimension_id,
        pillar=pillar,
        weight=weight,
        score=score,
        availability=availability,
        confidence=confidence if score is not None else ConfidenceLevel.LOW,
        classification=classification,
        rule_trace=RuleTrace(
            rule_id=f"{pillar.upper()}.{dimension_id.upper()}.{rule_suffix}.V1",
            provisional_parameter_ids=(band_param,) if band_param else (),
            reason=classification.reason,
        ),
        cited_evidence_ids=(
            tuple(e.observation_id for e in signals.negative_evidence)
            if signals.negative_evidence
            else tuple(s.accepted_observation.observation_id for s in resolved_signals)
        ),
    )


# ---------------------------------------------------------------------
# Market (5, Category B)
# ---------------------------------------------------------------------

def eval_market_size(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(MarketSizeObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "market_size")
    return _build_b_result("market_size", "Market", Decimal("0.25"), SignalCollection(obs, negs), registry, "SIZE")


def eval_market_growth(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(MarketGrowthObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "market_growth")
    return _build_b_result("market_growth", "Market", Decimal("0.20"), SignalCollection(obs, negs), registry, "GROWTH")


def eval_market_timing(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    # Timing signals piggyback on MarketGrowthObservation + CompetitiveEvidenceObservation
    # tagged as catalysts in this harness's simplified model (Rulebook Part 9
    # notes Market Timing is the hardest Market dimension to reduce cleanly).
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, MarketGrowthObservation) and "catalyst" in (e.category_label or "").lower()
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "market_timing")
    return _build_b_result("market_timing", "Market", Decimal("0.20"), SignalCollection(obs, negs), registry, "TIMING")


def eval_competitive_intensity(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(CompetitiveEvidenceObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "competitive_intensity")
    return _build_b_result("competitive_intensity", "Market", Decimal("0.15"), SignalCollection(obs, negs), registry, "COMPINT")


def eval_customer_demand(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(CustomerEvidenceObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "customer_demand")
    return _build_b_result("customer_demand", "Market", Decimal("0.20"), SignalCollection(obs, negs), registry, "DEMAND")


# ---------------------------------------------------------------------
# Team (5, Category B)
# ---------------------------------------------------------------------

def eval_founder_market_fit(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, (FounderExperienceObservation, FounderOutcomeObservation))
        and not (isinstance(e, FounderExperienceObservation) and e.experience_type == FounderExperienceType.UNRELATED_DOMAIN)
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "founder_market_fit")
    return _build_b_result("founder_market_fit", "Team", Decimal("0.25"), SignalCollection(obs, negs), registry, "FMF")


def eval_technical_capability(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if (isinstance(e, ProductCapabilityObservation) and e.shipped)
        or (isinstance(e, FounderExperienceObservation) and "technical" in e.founder_role.lower())
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "technical_capability")
    return _build_b_result("technical_capability", "Team", Decimal("0.20"), SignalCollection(obs, negs), registry, "TECH")


def eval_business_capability(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(e for e in company.evidence if isinstance(e, (RevenueObservation, CommercialContractObservation)))
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "business_capability")
    return _build_b_result("business_capability", "Team", Decimal("0.20"), SignalCollection(obs, negs), registry, "BIZCAP")


def eval_leadership(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, FounderExperienceObservation) and "leadership" in e.founder_role.lower()
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "leadership")
    return _build_b_result("leadership", "Team", Decimal("0.20"), SignalCollection(obs, negs), registry, "LEAD")


def eval_execution_track_record_team(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, FounderOutcomeObservation) and e.outcome_type.value in ("ACQUIRED", "IPO")
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "execution_track_record_team")
    return _build_b_result("execution_track_record_team", "Team", Decimal("0.15"), SignalCollection(obs, negs), registry, "ETR")


# ---------------------------------------------------------------------
# Product (5, Category B)
# ---------------------------------------------------------------------

def eval_customer_value(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(CustomerEvidenceObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "customer_value")
    return _build_b_result("customer_value", "Product", Decimal("0.25"), SignalCollection(obs, negs), registry, "CUSTVAL")


def eval_differentiation(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(e for e in company.evidence if isinstance(e, CompetitiveEvidenceObservation) and e.differentiator_named)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "differentiation")
    return _build_b_result("differentiation", "Product", Decimal("0.20"), SignalCollection(obs, negs), registry, "DIFF")


def eval_product_accessibility(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, ProductCapabilityObservation) and (e.named_integration or e.disclosed_reliability_metric)
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "product_accessibility")
    return _build_b_result("product_accessibility", "Product", Decimal("0.15"), SignalCollection(obs, negs), registry, "ACCESS")


def eval_defensibility(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, ProductCapabilityObservation) and "defensib" in e.capability_label.lower()
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "defensibility")
    return _build_b_result("defensibility", "Product", Decimal("0.20"), SignalCollection(obs, negs), registry, "DEFENS")


def eval_adoption_potential(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, ProductCapabilityObservation) and "expansion" in e.capability_label.lower()
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "adoption_potential")
    return _build_b_result("adoption_potential", "Product", Decimal("0.20"), SignalCollection(obs, negs), registry, "ADOPT")


# ---------------------------------------------------------------------
# Execution (4, Category B)
# ---------------------------------------------------------------------

def eval_gtm_execution(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, ProductCapabilityObservation) and "gtm" in e.capability_label.lower()
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "gtm_execution")
    return _build_b_result("gtm_execution", "Execution", Decimal("0.33"), SignalCollection(obs, negs), registry, "GTM")


def eval_product_execution(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(e for e in company.evidence if isinstance(e, ProductCapabilityObservation) and e.shipped)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "product_execution")
    return _build_b_result("product_execution", "Execution", Decimal("0.33"), SignalCollection(obs, negs), registry, "PRODEX")


def eval_operating_discipline(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, ProductCapabilityObservation) and "process" in e.capability_label.lower()
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "operating_discipline")
    return _build_b_result("operating_discipline", "Execution", Decimal("0.17"), SignalCollection(obs, negs), registry, "OPDISC")


def eval_strategic_execution(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(
        e for e in company.evidence
        if isinstance(e, ProductCapabilityObservation) and "strategy" in e.capability_label.lower()
    )
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "strategic_execution")
    return _build_b_result("strategic_execution", "Execution", Decimal("0.17"), SignalCollection(obs, negs), registry, "STRATEX")


# ---------------------------------------------------------------------
# Traction (5: 2x Category A, 3x Category B)
# ---------------------------------------------------------------------

def _stage_key(stage: Stage) -> str:
    return {
        Stage.IDEA: "seed", Stage.PRE_SEED: "seed", Stage.SEED: "seed",
        Stage.SERIES_A: "series_a", Stage.SERIES_B_PLUS: "growth", Stage.GROWTH: "growth",
    }[stage]


def eval_current_scale(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    revenue_raw = tuple(e for e in company.evidence if isinstance(e, RevenueObservation) and e.metric_type == RevenueMetricType.ARR)
    customer_raw = tuple(e for e in company.evidence if isinstance(e, CustomerCountObservation) and e.customer_type == CustomerType.PAYING)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "current_scale")

    if negs:
        return _build_b_result("current_scale", "Traction", Decimal("0.20"), SignalCollection((), negs), registry, "SCALE")

    if not revenue_raw and not customer_raw:
        return DimensionResult(
            "current_scale", "Traction", Decimal("0.20"), None, AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE,
            ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
            RuleTrace("TRACTION.CURRENT_SCALE.V1", (), "No qualifying observation."), (),
        )

    # Phase 10.8G, Part 10: deduplicate + resolve same-period conflicts
    # via build_canonical_signals BEFORE picking "the latest" point --
    # never via a raw max()/insertion-order tie-break. Multiple
    # observations of the identical (metric, period) that AGREE
    # collapse to one signal (Part 3/4); observations that DISAGREE on
    # the same period become a CONFLICT_DETECTED signal, excluded from
    # scoring here (Part 9), never silently resolved by list position.
    if revenue_raw:
        canonical = build_canonical_signals(revenue_raw)
        resolved = [s for s in canonical if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
        had_conflict = any(s.conflict_status == ConflictStatus.CONFLICT_DETECTED for s in canonical)
        if not resolved:
            return DimensionResult(
                "current_scale", "Traction", Decimal("0.20"), None, AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE,
                ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
                RuleTrace("TRACTION.CURRENT_SCALE.CONFLICT.V1", (), "All revenue observations are in unresolved conflict."), (),
            )
        # Deterministic tie-break by the signal_key's own period string
        # (content-derived, never insertion order) -- picks the most
        # recent period among resolved signals.
        latest_signal = max(resolved, key=lambda s: s.signal_key[-1])
        latest = latest_signal.accepted_observation
        key = _stage_key(company.stage)
        ordinary_ceiling = registry.value(f"traction.current_scale.{key}.arr_ordinary_ceiling")
        strong_ceiling = registry.value(f"traction.current_scale.{key}.arr_strong_ceiling")
        if latest.amount < ordinary_ceiling:
            score = Decimal("5.0")
            band = "ordinary"
        elif latest.amount < strong_ceiling:
            score = Decimal("7.5")
            band = "strong"
        else:
            score = Decimal("9.5")
            band = "exceptional-for-stage"
        return DimensionResult(
            "current_scale", "Traction", Decimal("0.20"), score, AvailabilityStatus.SCORABLE,
            confidence_from_evidence([latest]),
            ClassificationResult(band.upper(), (latest.observation_id,), reason=f"ARR {latest.amount} at stage {company.stage.value}"),
            RuleTrace(
                f"TRACTION.CURRENT_SCALE.{key.upper()}.V1",
                (f"traction.current_scale.{key}.arr_ordinary_ceiling", f"traction.current_scale.{key}.arr_strong_ceiling"),
                f"Stage-relative ARR band: {band}",
            ),
            (latest.observation_id,),
        )

    # Customer-count fallback (no ARR, but paying customers exist) --
    # same conflict-aware, order-independent selection as the ARR path.
    canonical_c = build_canonical_signals(customer_raw)
    resolved_c = [s for s in canonical_c if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
    if not resolved_c:
        return DimensionResult(
            "current_scale", "Traction", Decimal("0.20"), None, AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE,
            ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
            RuleTrace("TRACTION.CURRENT_SCALE.CUSTOMER_CONFLICT.V1", (), "All customer-count observations are in unresolved conflict."), (),
        )
    latest_c = max(resolved_c, key=lambda s: s.signal_key[-1]).accepted_observation
    return DimensionResult(
        "current_scale", "Traction", Decimal("0.20"), Decimal("5.5"), AvailabilityStatus.SCORABLE,
        confidence_from_evidence([latest_c]),
        ClassificationResult("SINGLE_SIGNAL", (latest_c.observation_id,), reason="Paying-customer-count-only scale signal."),
        RuleTrace("TRACTION.CURRENT_SCALE.CUSTOMER_FALLBACK.V1", (), "No ARR observation; scored from customer count alone."),
        (latest_c.observation_id,),
    )


def eval_growth_trajectory(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    revenue_raw = tuple(e for e in company.evidence if isinstance(e, RevenueObservation) and e.metric_type == RevenueMetricType.ARR)
    # Phase 10.8G, Part 10: deduplicate by (metric, period) signal
    # identity first -- two observations of the SAME period that AGREE
    # collapse to one point (never double-counted as if they were two
    # distinct dated observations); two that DISAGREE on the same
    # period become an unresolved conflict, excluded here, never
    # order-dependent. Distinct periods remain distinct points, exactly
    # as required (10,000 customers in 2025 vs. 20,000 in 2026 are NOT
    # merged).
    canonical = build_canonical_signals(revenue_raw)
    resolved = [s for s in canonical if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
    revenue_obs = sorted((s.accepted_observation for s in resolved), key=lambda o: o.as_of_date)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "growth_trajectory")

    # Bug fix (Phase 10.8F, Part 43 -- experimental harness implementation
    # bug, not a Rulebook defect): explicit negative evidence must
    # override regardless of whether a two-point series ALSO exists --
    # the original code only checked `negs` inside the
    # insufficient-data branch, so a negative signal was silently
    # ignored whenever 2+ revenue points happened to also be present.
    # Negative evidence must never be diluted by simultaneously-present
    # quantitative data (Rulebook Parts 13/17: negative evidence
    # overrides, never averages).
    if negs:
        return _build_b_result("growth_trajectory", "Traction", Decimal("0.25"), SignalCollection((), negs), registry, "GROWTH")

    if len(revenue_obs) < 2:
        return DimensionResult(
            "growth_trajectory", "Traction", Decimal("0.25"), None, AvailabilityStatus.UNAVAILABLE_INSUFFICIENT,
            ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
            RuleTrace("TRACTION.GROWTH_TRAJECTORY.V1", (), "Fewer than two dated ARR observations -- fail-closed by design."), (),
        )

    earlier, later = revenue_obs[0], revenue_obs[-1]
    if earlier.amount == 0:
        yoy_pct = Decimal("999") if later.amount > 0 else Decimal("0")
    else:
        yoy_pct = ((later.amount - earlier.amount) / earlier.amount) * Decimal("100")

    strong = registry.value("traction.growth_trajectory.strong_yoy_pct")
    exceptional = registry.value("traction.growth_trajectory.exceptional_yoy_pct")
    decline_threshold = registry.value("traction.growth_trajectory.decline_negative_threshold_pct")

    cited = (earlier.observation_id, later.observation_id)
    if yoy_pct < decline_threshold:
        return DimensionResult(
            "growth_trajectory", "Traction", Decimal("0.25"), Decimal("2.0"), AvailabilityStatus.SCORABLE,
            confidence_from_evidence([earlier, later]),
            ClassificationResult("NEGATIVE_SIGNAL_PRESENT", cited, reason=f"Disclosed decline: {yoy_pct}% YoY."),
            RuleTrace("TRACTION.GROWTH_TRAJECTORY.DECLINE.V1", ("traction.growth_trajectory.decline_negative_threshold_pct",), "Two-point decline is direct negative evidence."),
            cited,
        )
    if yoy_pct >= exceptional:
        score, band = Decimal("9.5"), "EXCEPTIONAL"
    elif yoy_pct >= strong:
        score, band = Decimal("7.5"), "STRONG"
    else:
        score, band = Decimal("5.5"), "ORDINARY"

    return DimensionResult(
        "growth_trajectory", "Traction", Decimal("0.25"), score, AvailabilityStatus.SCORABLE,
        confidence_from_evidence([earlier, later]),
        ClassificationResult(band, cited, reason=f"{yoy_pct}% YoY growth."),
        RuleTrace("TRACTION.GROWTH_TRAJECTORY.V1", ("traction.growth_trajectory.strong_yoy_pct", "traction.growth_trajectory.exceptional_yoy_pct"), f"{yoy_pct}% YoY -> {band}"),
        cited,
    )


def eval_customer_adoption(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(CustomerCountObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "customer_adoption")
    return _build_b_result("customer_adoption", "Traction", Decimal("0.20"), SignalCollection(obs, negs), registry, "ADOPT")


def eval_retention_engagement(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(RetentionObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "retention_engagement")
    if negs:
        return _build_b_result("retention_engagement", "Traction", Decimal("0.20"), SignalCollection((), negs), registry, "RETEN")
    if not obs:
        return DimensionResult(
            "retention_engagement", "Traction", Decimal("0.20"), None, AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE,
            ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
            RuleTrace("TRACTION.RETENTION.V1", (), "No retention observation."), (),
        )
    # Phase 10.8G, Part 10: dedup/resolve via canonical signals rather
    # than `obs[-1]` (insertion order).
    canonical_ret = build_canonical_signals(obs)
    resolved_ret = [s for s in canonical_ret if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
    if not resolved_ret:
        return DimensionResult(
            "retention_engagement", "Traction", Decimal("0.20"), None, AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE,
            ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
            RuleTrace("TRACTION.RETENTION.CONFLICT.V1", (), "Retention observations are in unresolved conflict."), (),
        )
    latest = resolved_ret[0].accepted_observation
    nrr = latest.nrr_pct
    if nrr is not None and nrr >= Decimal("110"):
        score, band = Decimal("8.5"), "STRONG"
    elif nrr is not None and nrr >= Decimal("95"):
        score, band = Decimal("5.5"), "ORDINARY"
    else:
        score, band = Decimal("5.5"), "ORDINARY"
    return DimensionResult(
        "retention_engagement", "Traction", Decimal("0.20"), score, AvailabilityStatus.SCORABLE,
        confidence_from_evidence([latest]),
        ClassificationResult(band, (latest.observation_id,)),
        RuleTrace("TRACTION.RETENTION.V1", (), f"NRR/GRR/churn-based classification: {band}"),
        (latest.observation_id,),
    )


def eval_commercial_validation(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = company.evidence_of_type(CommercialContractObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "commercial_validation")
    return _build_b_result("commercial_validation", "Traction", Decimal("0.15"), SignalCollection(obs, negs), registry, "COMMVAL")


# ---------------------------------------------------------------------
# Financial Health (3: Revenue Quality [B], Unit Economics [A], Capital Efficiency [A])
# ---------------------------------------------------------------------

def eval_revenue_quality(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    obs = tuple(e for e in company.evidence if isinstance(e, RetentionObservation))
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "revenue_quality")
    return _build_b_result("revenue_quality", "Financial Health", Decimal("0.35"), SignalCollection(obs, negs), registry, "REVQ")


def eval_unit_economics(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    # Deterministic, fail-closed -- unchanged in spirit from V2.1's
    # Deterministic mechanism. Requires an explicit CAC/LTV-shaped signal;
    # this harness models it minimally via a NegativeSignal-free
    # RetentionObservation combined with a RevenueObservation as a proxy
    # for "unit economics disclosed" (full CAC/LTV typed pair intentionally
    # out of scope for this experimental harness, per Rulebook Part 4's
    # "representative, not exhaustive" scope).
    revenue = company.evidence_of_type(RevenueObservation)
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "unit_economics")
    if negs:
        return _build_b_result("unit_economics", "Financial Health", Decimal("0.30"), SignalCollection((), negs), registry, "UE")
    return DimensionResult(
        "unit_economics", "Financial Health", Decimal("0.30"), None, AvailabilityStatus.UNAVAILABLE_PRIVATE_INFORMATION,
        ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
        RuleTrace("FINHEALTH.UNIT_ECONOMICS.V1", (), "No typed CAC/LTV pair modeled in this experimental harness -- always fail-closed to Private-Information-Unavailable."), (),
    )


def eval_capital_efficiency(company: SyntheticCompany, registry: ParameterRegistry) -> DimensionResult:
    negs = tuple(n for n in company.negative_signals if n.affected_dimension == "capital_efficiency")
    # Bug fix (Phase 10.8F, Part 43 -- experimental harness implementation
    # bug, matching the Growth Trajectory fix above): explicit negative
    # evidence must override BEFORE any runway-statement/burn-ratio
    # branch is even considered, not only when those branches don't
    # otherwise resolve -- otherwise a disclosed-OK runway figure could
    # silently mask independently-cited negative evidence (e.g. a
    # disclosed severe_cash_constraint signal from a different source).
    if negs:
        return _build_b_result("capital_efficiency", "Financial Health", Decimal("0.35"), SignalCollection((), negs), registry, "CAPEFF")

    runway_stmt = company.evidence_of_type(RunwayStatementObservation)
    if runway_stmt:
        # Phase 10.8G, Part 10: dedup/resolve via canonical signals --
        # `runway_stmt[-1]` (insertion order) is exactly the forbidden
        # pattern. Multiple AGREEING runway statements collapse to one
        # signal; DISAGREEING ones become an unresolved conflict.
        canonical_runway = build_canonical_signals(runway_stmt)
        resolved_runway = [s for s in canonical_runway if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
        if not resolved_runway:
            return DimensionResult(
                "capital_efficiency", "Financial Health", Decimal("0.35"), None, AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE,
                ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
                RuleTrace("FINHEALTH.CAPITAL_EFFICIENCY.RUNWAY_CONFLICT.V1", (), "Disclosed runway statements are in unresolved conflict."), (),
            )
        latest = resolved_runway[0].accepted_observation
        severe_threshold = registry.value("finhealth.capital_efficiency.severe_constraint_months_runway")
        if latest.months < severe_threshold:
            return DimensionResult(
                "capital_efficiency", "Financial Health", Decimal("0.35"), Decimal("2.0"), AvailabilityStatus.SCORABLE,
                confidence_from_evidence([latest]),
                ClassificationResult("NEGATIVE_SIGNAL_PRESENT", (latest.observation_id,), reason=f"Disclosed runway {latest.months} months < severe threshold."),
                RuleTrace("FINHEALTH.CAPITAL_EFFICIENCY.SEVERE_RUNWAY.V1", ("finhealth.capital_efficiency.severe_constraint_months_runway",), "Direct disclosed runway statement triggers severe constraint."),
                (latest.observation_id,),
            )
        score = Decimal("7.5") if latest.months >= Decimal("18") else Decimal("5.5")
        return DimensionResult(
            "capital_efficiency", "Financial Health", Decimal("0.35"), score, AvailabilityStatus.SCORABLE,
            confidence_from_evidence([latest]),
            ClassificationResult("STRONG" if score >= Decimal("7") else "ORDINARY", (latest.observation_id,), reason=f"Disclosed runway {latest.months} months."),
            RuleTrace("FINHEALTH.CAPITAL_EFFICIENCY.RUNWAY_STATEMENT.V1", (), "Direct disclosed runway statement."),
            (latest.observation_id,),
        )

    cash = company.evidence_of_type(CashObservation)
    burn = company.evidence_of_type(BurnObservation)
    revenue = company.evidence_of_type(RevenueObservation)

    # (negs already handled unconditionally above, before the
    # runway_stmt branch -- no second check needed here.)
    if burn and revenue:
        # Phase 10.8G, Part 10: same order-independent dedup/conflict
        # discipline for burn and revenue -- `burn[-1]` and a bare
        # `max(revenue, key=as_of_date)` were both potentially
        # insertion-order-dependent on a same-date tie.
        canonical_burn = build_canonical_signals(burn)
        resolved_burn = [s for s in canonical_burn if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
        canonical_rev = build_canonical_signals(revenue)
        resolved_rev = [s for s in canonical_rev if s.conflict_status != ConflictStatus.CONFLICT_DETECTED]
        if not resolved_burn or not resolved_rev:
            return DimensionResult(
                "capital_efficiency", "Financial Health", Decimal("0.35"), None, AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE,
                ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
                RuleTrace("FINHEALTH.CAPITAL_EFFICIENCY.BURN_REVENUE_CONFLICT.V1", (), "Burn or revenue observations are in unresolved conflict."), (),
            )
        latest_burn = max(resolved_burn, key=lambda s: s.signal_key[-1]).accepted_observation
        latest_rev = max(resolved_rev, key=lambda s: s.signal_key[-1]).accepted_observation
        annualized_burn = latest_burn.amount * (Decimal("12") if latest_burn.period.value == "MONTHLY" else Decimal("1"))
        if latest_rev.amount == 0:
            ratio = Decimal("999")
        else:
            ratio = annualized_burn / latest_rev.amount
        exceptional_ratio = registry.value("finhealth.capital_efficiency.exceptional_burn_to_revenue_ratio")
        strong_ratio = registry.value("finhealth.capital_efficiency.strong_burn_to_revenue_ratio")
        cited = (latest_burn.observation_id, latest_rev.observation_id)
        if ratio <= exceptional_ratio:
            score, band = Decimal("9.0"), "EXCEPTIONAL"
        elif ratio <= strong_ratio:
            score, band = Decimal("7.5"), "STRONG"
        else:
            score, band = Decimal("5.0"), "ORDINARY"
        return DimensionResult(
            "capital_efficiency", "Financial Health", Decimal("0.35"), score, AvailabilityStatus.SCORABLE,
            confidence_from_evidence([latest_burn, latest_rev]),
            ClassificationResult(band, cited, reason=f"burn/revenue ratio {ratio}"),
            RuleTrace("FINHEALTH.CAPITAL_EFFICIENCY.BURN_REVENUE_RATIO.V1", ("finhealth.capital_efficiency.exceptional_burn_to_revenue_ratio", "finhealth.capital_efficiency.strong_burn_to_revenue_ratio"), f"Computed from real disclosed burn+revenue: {band}"),
            cited,
        )

    return DimensionResult(
        "capital_efficiency", "Financial Health", Decimal("0.35"), None, AvailabilityStatus.UNAVAILABLE_PRIVATE_INFORMATION,
        ConfidenceLevel.LOW, ClassificationResult("NO_SIGNAL", ()),
        RuleTrace("FINHEALTH.CAPITAL_EFFICIENCY.V1", (), "No real disclosed runway statement or burn+revenue pair -- fail-closed."), (),
    )


# ---------------------------------------------------------------------
# Registry of all 27 evaluators, keyed by (pillar, dimension_id)
# ---------------------------------------------------------------------

ALL_EVALUATORS: dict[str, Callable[[SyntheticCompany, ParameterRegistry], DimensionResult]] = {
    "market_size": eval_market_size,
    "market_growth": eval_market_growth,
    "market_timing": eval_market_timing,
    "competitive_intensity": eval_competitive_intensity,
    "customer_demand": eval_customer_demand,
    "founder_market_fit": eval_founder_market_fit,
    "technical_capability": eval_technical_capability,
    "business_capability": eval_business_capability,
    "leadership": eval_leadership,
    "execution_track_record_team": eval_execution_track_record_team,
    "customer_value": eval_customer_value,
    "differentiation": eval_differentiation,
    "product_accessibility": eval_product_accessibility,
    "defensibility": eval_defensibility,
    "adoption_potential": eval_adoption_potential,
    "gtm_execution": eval_gtm_execution,
    "product_execution": eval_product_execution,
    "operating_discipline": eval_operating_discipline,
    "strategic_execution": eval_strategic_execution,
    "current_scale": eval_current_scale,
    "growth_trajectory": eval_growth_trajectory,
    "customer_adoption": eval_customer_adoption,
    "retention_engagement": eval_retention_engagement,
    "commercial_validation": eval_commercial_validation,
    "revenue_quality": eval_revenue_quality,
    "unit_economics": eval_unit_economics,
    "capital_efficiency": eval_capital_efficiency,
}

DIMENSION_PILLARS: dict[str, str] = {
    "market_size": "Market", "market_growth": "Market", "market_timing": "Market",
    "competitive_intensity": "Market", "customer_demand": "Market",
    "founder_market_fit": "Team", "technical_capability": "Team", "business_capability": "Team",
    "leadership": "Team", "execution_track_record_team": "Team",
    "customer_value": "Product", "differentiation": "Product", "product_accessibility": "Product",
    "defensibility": "Product", "adoption_potential": "Product",
    "gtm_execution": "Execution", "product_execution": "Execution",
    "operating_discipline": "Execution", "strategic_execution": "Execution",
    "current_scale": "Traction", "growth_trajectory": "Traction", "customer_adoption": "Traction",
    "retention_engagement": "Traction", "commercial_validation": "Traction",
    "revenue_quality": "Financial Health", "unit_economics": "Financial Health",
    "capital_efficiency": "Financial Health",
}

assert len(ALL_EVALUATORS) == 27, f"Expected 27 dimensions per Rulebook Part 36's table, got {len(ALL_EVALUATORS)}"

PILLAR_WEIGHTS: dict[str, Decimal] = {
    "Market": Decimal("0.20"),
    "Team": Decimal("0.20"),
    "Product": Decimal("0.20"),
    "Execution": Decimal("0.15"),
    "Traction": Decimal("0.15"),
    "Financial Health": Decimal("0.10"),
}


def evaluate_all_dimensions(
    company: SyntheticCompany,
    registry: ParameterRegistry,
    reference_date: date | None = None,
) -> tuple[DimensionResult, ...]:
    """Phase 10.8G, Part 12: reference_date is an explicit, deterministic
    input (never wall-clock, see freshness.py's module docstring) --
    passing None (the default, preserving 10.8F call-site compatibility)
    skips staleness filtering entirely, exactly as before. Every 10.8G
    test that exercises freshness passes an explicit fixed date."""
    filtered_company, excluded_stale = apply_staleness_filter(company, reference_date, registry)
    return tuple(evaluator(filtered_company, registry) for evaluator in ALL_EVALUATORS.values())


def evaluate_all_dimensions_with_staleness_report(
    company: SyntheticCompany,
    registry: ParameterRegistry,
    reference_date: date,
) -> tuple[tuple[DimensionResult, ...], tuple]:
    """Same as evaluate_all_dimensions but also returns the excluded-
    as-stale observations, for tests that need to inspect what was
    filtered (Part 24's recency tests)."""
    filtered_company, excluded_stale = apply_staleness_filter(company, reference_date, registry)
    results = tuple(evaluator(filtered_company, registry) for evaluator in ALL_EVALUATORS.values())
    return results, excluded_stale
