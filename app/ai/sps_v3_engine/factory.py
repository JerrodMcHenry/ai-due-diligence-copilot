"""
Synthetic evidence factory (Phase 10.8F, Part 10).

Thin builder helpers over the typed observation classes in types.py --
convenience only, no new semantics. Every builder defaults to
PRIMARY_SELF_REPORTED / ACCEPTED / DIRECT / MEDIUM unless overridden,
so profile-construction code (profiles.py) reads declaratively.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from itertools import count

from app.ai.sps_v3_engine.types import (
    BurnObservation,
    BurnPeriod,
    CashObservation,
    CommercialContractObservation,
    CompetitiveEvidenceObservation,
    CompetitorType,
    CustomerCountObservation,
    CustomerEvidenceObservation,
    CustomerType,
    DirectOrDerived,
    ExtractionConfidence,
    FounderExperienceObservation,
    FounderExperienceType,
    FounderOutcomeObservation,
    FounderOutcomeType,
    MarketEstimateSourceType,
    MarketGrowthObservation,
    MarketSizeObservation,
    NegativeSignalObservation,
    ProductCapabilityObservation,
    ProvenanceGrade,
    ProvenanceStatus,
    RetentionObservation,
    RevenueMetricType,
    RevenueObservation,
    RunwayStatementObservation,
)

_id_counter = count(1)


def _next_id(prefix: str) -> str:
    return f"{prefix}-{next(_id_counter):05d}"


def revenue(
    amount: str,
    as_of: date,
    metric_type: RevenueMetricType = RevenueMetricType.ARR,
    grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED,
    excerpt: str = "disclosed revenue figure",
) -> RevenueObservation:
    return RevenueObservation(
        observation_id=_next_id("REV"), source_excerpt=excerpt,
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        amount=Decimal(amount), metric_type=metric_type, as_of_date=as_of,
    )


def customer_count(
    count_: int, as_of: date, customer_type: CustomerType = CustomerType.PAYING,
    grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED, excerpt: str = "disclosed customer count",
) -> CustomerCountObservation:
    return CustomerCountObservation(
        observation_id=_next_id("CUST"), source_excerpt=excerpt,
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        count=count_, customer_type=customer_type, as_of_date=as_of,
    )


def retention(
    nrr: str | None = None, grr: str | None = None, churn: str | None = None,
    grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED, excerpt: str = "disclosed retention metric",
) -> RetentionObservation:
    return RetentionObservation(
        observation_id=_next_id("RET"), source_excerpt=excerpt,
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        nrr_pct=Decimal(nrr) if nrr else None, grr_pct=Decimal(grr) if grr else None,
        logo_churn_pct=Decimal(churn) if churn else None,
    )


def cash(amount: str, as_of: date, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> CashObservation:
    return CashObservation(
        observation_id=_next_id("CASH"), source_excerpt="disclosed cash balance",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        amount=Decimal(amount), as_of_date=as_of,
    )


def burn(amount: str, as_of: date, period: BurnPeriod = BurnPeriod.MONTHLY, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> BurnObservation:
    return BurnObservation(
        observation_id=_next_id("BURN"), source_excerpt="disclosed burn rate",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        amount=Decimal(amount), period=period, as_of_date=as_of,
    )


def runway_statement(months: str, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> RunwayStatementObservation:
    return RunwayStatementObservation(
        observation_id=_next_id("RWY"), source_excerpt=f"disclosed {months} months of runway",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        months=Decimal(months),
    )


def market_size(amount: str, label: str, source_type: MarketEstimateSourceType = MarketEstimateSourceType.COMPANY_STATED, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> MarketSizeObservation:
    return MarketSizeObservation(
        observation_id=_next_id("MKTSZ"), source_excerpt=f"named market: {label}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        amount=Decimal(amount), market_label=label, estimate_source_type=source_type,
    )


def market_growth(pct: str, category: str, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> MarketGrowthObservation:
    return MarketGrowthObservation(
        observation_id=_next_id("MKTGR"), source_excerpt=f"named category growth: {category}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        growth_pct=Decimal(pct), category_label=category,
    )


def founder_experience(
    role: str, experience_type: FounderExperienceType, prior_entity: str | None = None,
    grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED,
) -> FounderExperienceObservation:
    return FounderExperienceObservation(
        observation_id=_next_id("FEXP"), source_excerpt=f"{role}: {experience_type.value} at {prior_entity or 'n/a'}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        founder_role=role, experience_type=experience_type, prior_entity_name=prior_entity,
    )


def founder_outcome(prior_entity: str, outcome_type: FounderOutcomeType, attributed: bool = False, grade: ProvenanceGrade = ProvenanceGrade.HIGH_QUALITY_SECONDARY) -> FounderOutcomeObservation:
    return FounderOutcomeObservation(
        observation_id=_next_id("FOUT"), source_excerpt=f"{prior_entity}: {outcome_type.value}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        outcome_type=outcome_type, prior_entity_name=prior_entity, attributed_to_founder=attributed,
    )


def competitor(name: str, competitor_type: CompetitorType = CompetitorType.DIRECT, differentiator: bool = False, grade: ProvenanceGrade = ProvenanceGrade.HIGH_QUALITY_SECONDARY) -> CompetitiveEvidenceObservation:
    return CompetitiveEvidenceObservation(
        observation_id=_next_id("COMP"), source_excerpt=f"named competitor: {name}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        named_competitor=name, competitor_type=competitor_type, differentiator_named=differentiator,
    )


def product_capability(label: str, shipped: bool = True, integration: str | None = None, reliability: str | None = None, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> ProductCapabilityObservation:
    return ProductCapabilityObservation(
        observation_id=_next_id("PCAP"), source_excerpt=f"capability: {label}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        capability_label=label, shipped=shipped, named_integration=integration, disclosed_reliability_metric=reliability,
    )


def customer_evidence(claim: str, named_customer: str | None = None, quantified: bool = False, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> CustomerEvidenceObservation:
    return CustomerEvidenceObservation(
        observation_id=_next_id("CEV"), source_excerpt=claim,
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        named_customer=named_customer, outcome_claim=claim, quantified=quantified,
    )


def commercial_contract(contract_type: CustomerType = CustomerType.SIGNED_CONTRACT_UNPAID, named_customer: str | None = None, renewal: bool = False, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> CommercialContractObservation:
    return CommercialContractObservation(
        observation_id=_next_id("CONTR"), source_excerpt=f"contract: {contract_type.value}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        contract_type=contract_type, named_customer=named_customer, renewal_evidence=renewal,
    )


def negative_signal(signal_type: str, dimension: str, severity: str = "MODERATE", excerpt: str | None = None, grade: ProvenanceGrade = ProvenanceGrade.PRIMARY_SELF_REPORTED) -> NegativeSignalObservation:
    return NegativeSignalObservation(
        observation_id=_next_id("NEG"), source_excerpt=excerpt or f"disclosed {signal_type}",
        provenance_status=ProvenanceStatus.ACCEPTED, provenance_grade=grade,
        direct_or_derived=DirectOrDerived.DIRECT, extraction_confidence=ExtractionConfidence.MEDIUM,
        signal_type=signal_type, severity=severity, affected_dimension=dimension,
    )
