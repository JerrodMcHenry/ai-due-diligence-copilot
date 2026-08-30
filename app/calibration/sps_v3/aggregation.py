"""
Pillar/SPS aggregation, coverage, confidence, publishability
(Phase 10.8F, implementing Rulebook Parts 20-24).

Strength, Coverage, and Confidence are computed as three structurally
independent passes over the same DimensionResult list -- none of the
three functions below reads another's output, which is what makes the
Part 7 "firewall" tests (changing Coverage/Confidence must never
mathematically change Strength) true by construction, not by
convention.
"""

from __future__ import annotations

from decimal import Decimal

from app.calibration.sps_v3.evaluators import DIMENSION_PILLARS, PILLAR_WEIGHTS
from app.calibration.sps_v3.registry import ParameterRegistry
from app.calibration.sps_v3.types import (
    AvailabilityStatus,
    ConfidenceLevel,
    ConfidenceResult,
    CoverageResult,
    DimensionResult,
    PillarResult,
    SPSResult,
    Stage,
)

_CONFIDENCE_ORDER = {ConfidenceLevel.LOW: 0, ConfidenceLevel.MEDIUM: 1, ConfidenceLevel.HIGH: 2}
_ORDER_TO_CONFIDENCE = {v: k for k, v in _CONFIDENCE_ORDER.items()}

# Phase 10.8J: the CRITICAL_PILLARS concept (Market/Team/Product must be
# among the publishable pillars) is retired along with
# `gate.min_critical_pillars_present` -- overall Coverage (a
# PILLAR_WEIGHTS-weighted sum) already reflects a company whose
# representation skews away from these three highest-weighted pillars
# without a dedicated second check. Not deleted outright so the
# historical reasoning stays discoverable; simply unused now.


def _pillar_dimensions(dimension_results: tuple[DimensionResult, ...], pillar: str) -> tuple[DimensionResult, ...]:
    return tuple(d for d in dimension_results if d.pillar == pillar)


def compute_pillar_strength(dimensions: tuple[DimensionResult, ...]) -> Decimal | None:
    """Renormalized weighted average over SCORABLE dimensions only.
    Pure function of scores+weights -- never reads coverage or
    confidence (Part 7 firewall)."""
    scorable = [d for d in dimensions if d.availability == AvailabilityStatus.SCORABLE and d.score is not None]
    if not scorable:
        return None
    total_weight = sum(d.weight for d in scorable)
    if total_weight <= 0:
        return None
    weighted = sum(d.score * d.weight for d in scorable)
    return (weighted / total_weight).quantize(Decimal("0.01"))


def compute_pillar_completeness_pct(dimensions: tuple[DimensionResult, ...]) -> Decimal:
    """Weight-based coverage -- binary per dimension (scorable or not),
    never boosted by redundant evidence count (Rulebook Part 20)."""
    total_weight = sum(d.weight for d in dimensions)
    if total_weight <= 0:
        return Decimal("0")
    covered_weight = sum(d.weight for d in dimensions if d.availability == AvailabilityStatus.SCORABLE)
    return ((covered_weight / total_weight) * Decimal("100")).quantize(Decimal("0.1"))


def compute_pillar_confidence(dimensions: tuple[DimensionResult, ...]) -> ConfidenceLevel:
    """Weighted average of scored dimensions' confidence ordinal,
    rounded to the nearest level -- never reads score/coverage (Part 7)."""
    scorable = [d for d in dimensions if d.availability == AvailabilityStatus.SCORABLE]
    if not scorable:
        return ConfidenceLevel.LOW
    total_weight = sum(d.weight for d in scorable)
    if total_weight <= 0:
        return ConfidenceLevel.LOW
    weighted_ordinal = sum(Decimal(_CONFIDENCE_ORDER[d.confidence]) * d.weight for d in scorable) / total_weight
    rounded = int(weighted_ordinal.to_integral_value(rounding="ROUND_HALF_UP"))
    rounded = max(0, min(2, rounded))
    return _ORDER_TO_CONFIDENCE[rounded]


def evaluate_pillar(
    pillar: str,
    dimension_results: tuple[DimensionResult, ...],
    registry: ParameterRegistry,
) -> PillarResult:
    """
    Phase 10.8J simplification (Part 11): ONE rule decides whether a
    pillar shows a numerical Strength -- its own weighted coverage
    against a single minimum threshold. The prior two-gate design
    (a raw scorable-DIMENSION-COUNT floor, `gate.min_dimensions_per_pillar`,
    stacked on top of a weighted-coverage floor) is removed: dimension
    count and dimension weight can disagree (a pillar could clear a
    count floor while its scorable dimensions carry almost none of the
    pillar's real weight, or vice versa) -- coverage-by-weight is the
    more meaningful, and now the ONLY, test. `compute_pillar_strength`
    itself is unchanged (still a pure renormalized average over
    scorable dimensions only, per Part 5) -- this function only decides
    whether that already-computed number is shown or replaced with
    "not enough evidence".
    """
    dims = _pillar_dimensions(dimension_results, pillar)
    completeness = compute_pillar_completeness_pct(dims)
    min_coverage = registry.value("gate.min_pillar_coverage_pct")

    if completeness < min_coverage:
        return PillarResult(
            pillar=pillar, strength=compute_pillar_strength(dims), completeness_pct=completeness,
            confidence=compute_pillar_confidence(dims), publishable=False,
            dimension_results=dims,
            withhold_reason=f"Pillar coverage {completeness}% < {min_coverage}% floor (gate.min_pillar_coverage_pct).",
        )

    return PillarResult(
        pillar=pillar, strength=compute_pillar_strength(dims), completeness_pct=completeness,
        confidence=compute_pillar_confidence(dims), publishable=True,
        dimension_results=dims,
    )


def evaluate_sps(
    dimension_results: tuple[DimensionResult, ...],
    stage: Stage,
    registry: ParameterRegistry,
) -> SPSResult:
    """
    Phase 10.8J simplification (Part 10): SPS-level publishability is
    now ONE rule -- overall weighted Coverage against a single minimum
    threshold. The prior three-gate design (`gate.min_publishable_pillars`,
    `gate.min_critical_pillars_present`, `gate.overall_coverage_floor_pct`
    stacked together) is removed in favor of this single test, which
    already implies the other two structurally: overall Coverage is
    itself a PILLAR_WEIGHTS-weighted sum (see `_compute_overall_coverage`),
    so a company with too few pillars represented, or with its
    representation concentrated outside Market/Team/Product, will
    already show low overall Coverage without a separate dedicated
    check for either condition -- the single coverage number already
    "sees" both failure modes the two removed gates existed to catch.
    """
    pillar_results = tuple(
        evaluate_pillar(pillar, dimension_results, registry) for pillar in PILLAR_WEIGHTS
    )
    publishable_pillars = [p for p in pillar_results if p.publishable]

    overall_coverage = _compute_overall_coverage(dimension_results)
    overall_confidence = _compute_overall_confidence(pillar_results)

    coverage_floor = registry.value("gate.overall_coverage_floor_pct")

    withhold_reason = None
    if overall_coverage.overall_pct < coverage_floor:
        withhold_reason = f"Overall coverage {overall_coverage.overall_pct}% < {coverage_floor}% floor (gate.overall_coverage_floor_pct)."

    if withhold_reason is not None:
        return SPSResult(
            sps=None, publishable=False, withhold_reason=withhold_reason,
            pillar_results=pillar_results, coverage=overall_coverage, confidence=overall_confidence,
            stage=stage,
        )

    total_weight = sum(PILLAR_WEIGHTS[p.pillar] for p in publishable_pillars if p.strength is not None)
    if total_weight <= 0:
        return SPSResult(
            sps=None, publishable=False, withhold_reason="No publishable pillar has a computable strength.",
            pillar_results=pillar_results, coverage=overall_coverage, confidence=overall_confidence, stage=stage,
        )

    weighted = sum(p.strength * PILLAR_WEIGHTS[p.pillar] for p in publishable_pillars if p.strength is not None)
    sps = ((weighted / total_weight) * Decimal("10")).quantize(Decimal("0.1"))
    sps = max(Decimal("0"), min(Decimal("100"), sps))

    return SPSResult(
        sps=sps, publishable=True, withhold_reason=None,
        pillar_results=pillar_results, coverage=overall_coverage, confidence=overall_confidence, stage=stage,
    )


def _compute_overall_coverage(dimension_results: tuple[DimensionResult, ...]) -> CoverageResult:
    per_pillar = {}
    for pillar in PILLAR_WEIGHTS:
        dims = _pillar_dimensions(dimension_results, pillar)
        per_pillar[pillar] = compute_pillar_completeness_pct(dims)
    overall = sum(per_pillar[p] * PILLAR_WEIGHTS[p] for p in PILLAR_WEIGHTS)
    return CoverageResult(overall_pct=overall.quantize(Decimal("0.1")), per_pillar_pct=per_pillar)


def classify_ux_state(result: SPSResult) -> str:
    """
    Phase 10.8J Part 12: three deterministic UX output states, derived
    entirely from fields evaluate_sps() already computes -- ZERO new
    registry parameters, per the phase's explicit "do not add more
    scoring parameters" constraint. This function changes nothing about
    SPS/Coverage/Confidence; it only labels which of three fixed
    display modes the frontend should use.

    - "SUFFICIENT": result.publishable is True -- overall coverage
      cleared gate.overall_coverage_floor_pct, so the full SPS number
      (Strength+Coverage+Confidence) is shown.
    - "LIMITED": result.publishable is False, but at least one pillar's
      own PillarResult.publishable is True (it cleared
      gate.min_pillar_coverage_pct on its own) -- no overall SPS is
      shown, but that pillar's own strength can be, labeled as partial.
      This is not a new threshold: it reuses the pillar-level gate that
      already exists for exactly this purpose.
    - "INSUFFICIENT": no pillar is individually publishable -- nothing
      numeric is shown at all, only a plain "not enough evidence yet"
      message.

    The three states are mutually exclusive and collectively exhaustive
    by construction (SUFFICIENT implies at least one publishable pillar
    since evaluate_sps requires total_weight>0 among publishable
    pillars to set publishable=True; the other two split on whether any
    pillar is publishable).
    """
    if result.publishable:
        return "SUFFICIENT"
    if any(p.publishable for p in result.pillar_results):
        return "LIMITED"
    return "INSUFFICIENT"


def _compute_overall_confidence(pillar_results: tuple[PillarResult, ...]) -> ConfidenceResult:
    per_pillar = {p.pillar: p.confidence for p in pillar_results}
    scored = [p for p in pillar_results if p.strength is not None]
    if not scored:
        return ConfidenceResult(overall=ConfidenceLevel.LOW, per_pillar=per_pillar)
    total_weight = sum(PILLAR_WEIGHTS[p.pillar] for p in scored)
    weighted_ordinal = sum(Decimal(_CONFIDENCE_ORDER[p.confidence]) * PILLAR_WEIGHTS[p.pillar] for p in scored) / total_weight
    rounded = int(weighted_ordinal.to_integral_value(rounding="ROUND_HALF_UP"))
    rounded = max(0, min(2, rounded))
    return ConfidenceResult(overall=_ORDER_TO_CONFIDENCE[rounded], per_pillar=per_pillar)
