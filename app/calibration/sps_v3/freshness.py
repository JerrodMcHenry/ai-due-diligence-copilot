"""
Phase 10.8G, Parts 11-12 -- recency/staleness architecture.

Deliberately simple, deterministic, evidence-TYPE-based (not a
continuous decay function): every observation type has one fixed
FreshnessClass; each class has one provisional "stale_after_months"
threshold (CALIBRATION REQUIRED, per the registry pattern already
established -- these are NEW parameters, not a recalibration of any
existing one, consistent with this phase's "do not calibrate score
bands/weights/coverage floor" restriction).

No wall-clock dependency anywhere -- every function here takes an
explicit `reference_date`, so evaluation stays fully deterministic
(Part 28) regardless of when the harness is actually run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from app.calibration.sps_v3.registry import ParameterRegistry
from app.calibration.sps_v3.types import (
    BurnObservation,
    CashObservation,
    CommercialContractObservation,
    CompetitiveEvidenceObservation,
    CustomerCountObservation,
    CustomerEvidenceObservation,
    EvidenceBase,
    FounderExperienceObservation,
    FounderOutcomeObservation,
    FundingObservation,
    MarketGrowthObservation,
    MarketSizeObservation,
    ProductCapabilityObservation,
    RetentionObservation,
    RevenueObservation,
    RunwayStatementObservation,
)


class FreshnessClass(str, Enum):
    STRUCTURAL_FACT = "STRUCTURAL_FACT"          # founder history, funding events -- ~never stale
    HISTORICAL_FACT = "HISTORICAL_FACT"           # market size/growth estimates -- stale slowly
    RECENT_PERFORMANCE = "RECENT_PERFORMANCE"      # customer count, retention, contracts -- moderate
    CURRENT_STATE = "CURRENT_STATE"                # revenue, cash, burn, runway -- stales quickly


class Freshness(str, Enum):
    FRESH = "FRESH"
    BORDERLINE = "BORDERLINE"
    STALE = "STALE"
    UNDATED = "UNDATED"   # no as_of_date at all -- structural facts commonly have none


_FRESHNESS_CLASS_MAP: dict[type, FreshnessClass] = {
    FounderExperienceObservation: FreshnessClass.STRUCTURAL_FACT,
    FounderOutcomeObservation: FreshnessClass.STRUCTURAL_FACT,
    FundingObservation: FreshnessClass.STRUCTURAL_FACT,
    MarketSizeObservation: FreshnessClass.HISTORICAL_FACT,
    MarketGrowthObservation: FreshnessClass.HISTORICAL_FACT,
    CompetitiveEvidenceObservation: FreshnessClass.HISTORICAL_FACT,
    ProductCapabilityObservation: FreshnessClass.HISTORICAL_FACT,
    CustomerEvidenceObservation: FreshnessClass.RECENT_PERFORMANCE,
    CustomerCountObservation: FreshnessClass.RECENT_PERFORMANCE,
    RetentionObservation: FreshnessClass.RECENT_PERFORMANCE,
    CommercialContractObservation: FreshnessClass.RECENT_PERFORMANCE,
    RevenueObservation: FreshnessClass.CURRENT_STATE,
    CashObservation: FreshnessClass.CURRENT_STATE,
    BurnObservation: FreshnessClass.CURRENT_STATE,
    RunwayStatementObservation: FreshnessClass.CURRENT_STATE,
}


def freshness_class_for(observation: EvidenceBase) -> FreshnessClass:
    return _FRESHNESS_CLASS_MAP.get(type(observation), FreshnessClass.HISTORICAL_FACT)


def _dated_field(observation: EvidenceBase) -> date | None:
    return getattr(observation, "as_of_date", None) or getattr(observation, "announced_date", None) or observation.source_date


def evaluate_freshness(
    observation: EvidenceBase,
    reference_date: date,
    registry: ParameterRegistry,
) -> Freshness:
    fc = freshness_class_for(observation)
    dated = _dated_field(observation)
    if dated is None:
        return Freshness.UNDATED

    age_months = Decimal((reference_date - dated).days) / Decimal("30.44")
    stale_after = registry.value(f"freshness.{fc.value.lower()}.stale_after_months")
    borderline_after = stale_after * Decimal("0.75")

    if age_months >= stale_after:
        return Freshness.STALE
    if age_months >= borderline_after:
        return Freshness.BORDERLINE
    return Freshness.FRESH


@dataclass(frozen=True)
class FreshnessAssessment:
    freshness: Freshness
    freshness_class: FreshnessClass
    age_months: Decimal | None
