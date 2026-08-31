"""
Experimental V3 domain types (Phase 10.8F, Part 4).

These types are deliberately NOT the production Pydantic models under
app/models/ -- no import in either direction. Plain, immutable
dataclasses + enums are used instead of dict[str, Any] so invalid
states fail loudly (a malformed enum value raises at construction, a
missing required field raises at construction) rather than being
silently accepted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum


# ---------------------------------------------------------------------
# Shared evidence primitives
# ---------------------------------------------------------------------

class ProvenanceStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED_UNTRACEABLE = "REJECTED_UNTRACEABLE"
    REJECTED_CONTRADICTED = "REJECTED_CONTRADICTED"


class ProvenanceGrade(str, Enum):
    PRIMARY_VERIFIED = "PRIMARY_VERIFIED"
    PRIMARY_SELF_REPORTED = "PRIMARY_SELF_REPORTED"
    HIGH_QUALITY_SECONDARY = "HIGH_QUALITY_SECONDARY"
    SECONDARY_ESTIMATE = "SECONDARY_ESTIMATE"
    DERIVED = "DERIVED"
    UNVERIFIED = "UNVERIFIED"


class DirectOrDerived(str, Enum):
    DIRECT = "DIRECT"
    DERIVED = "DERIVED"


class ExtractionConfidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SourceIndependence(str, Enum):
    """Phase 10.8G, Part 6-7: is this source ITS OWN observation of the
    underlying fact, or does it trace back to the same origin as another
    already-accepted observation of the identical signal? Determines
    whether a second/third/Nth observation of the same fact may
    contribute to Confidence's corroboration count -- it may never
    contribute to Strength or Coverage regardless of this value
    (Rulebook Part 16 amendment, Part 4)."""

    SAME_ORIGIN = "SAME_ORIGIN"       # explicitly the same origin_id as another accepted observation of this signal
    DERIVATIVE = "DERIVATIVE"          # a downstream repetition of another source (e.g. a blog citing a press release)
    INDEPENDENT = "INDEPENDENT"        # a genuinely separate original observation of the same fact
    UNKNOWN_ORIGIN = "UNKNOWN_ORIGIN"  # origin not established -- treated conservatively, never counted as
                                        # independent corroboration by default (Part 6: unknown must not be
                                        # assumed independent, or every duplicate could claim independence)


class ConflictStatus(str, Enum):
    NO_CONFLICT = "NO_CONFLICT"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    CONFLICT_RESOLVED_BY_PRECEDENCE = "CONFLICT_RESOLVED_BY_PRECEDENCE"


class Stage(str, Enum):
    IDEA = "IDEA"
    PRE_SEED = "PRE_SEED"
    SEED = "SEED"
    SERIES_A = "SERIES_A"
    SERIES_B_PLUS = "SERIES_B_PLUS"
    GROWTH = "GROWTH"


STAGE_ORDER = [Stage.IDEA, Stage.PRE_SEED, Stage.SEED, Stage.SERIES_A, Stage.SERIES_B_PLUS, Stage.GROWTH]


def _validate_derivation(direct_or_derived: DirectOrDerived, derivation: str | None) -> None:
    if direct_or_derived is DirectOrDerived.DERIVED and not derivation:
        raise ValueError("DERIVED observations must specify a derivation.")
    if direct_or_derived is DirectOrDerived.DIRECT and derivation:
        raise ValueError("DIRECT observations must not carry a derivation.")


@dataclass(frozen=True)
class EvidenceBase:
    """Shared base -- every typed observation carries these fields."""

    observation_id: str
    source_excerpt: str
    provenance_status: ProvenanceStatus
    provenance_grade: ProvenanceGrade
    direct_or_derived: DirectOrDerived
    extraction_confidence: ExtractionConfidence
    source_reference: str | None = None
    source_date: date | None = None
    derivation: str | None = None
    as_of_date: date | None = None
    # Phase 10.8G, Part 7 (source lineage): origin_id identifies the
    # ultimate original information source. Two observations sharing
    # the same non-None origin_id are the SAME underlying report
    # (e.g. one company press release, quoted by many outlets) --
    # deliberately minimal metadata (a single opaque id), not a full
    # citation graph, per Part 7's explicit "keep V1 implementable"
    # instruction.
    origin_id: str | None = None
    # Phase 10.8G, Part 6: explicit, model-assigned independence
    # classification for this specific observation RELATIVE TO the
    # signal it will be grouped into -- defaults to UNKNOWN_ORIGIN,
    # the conservative default (never assumed independent).
    source_independence: SourceIndependence = SourceIndependence.UNKNOWN_ORIGIN

    def __post_init__(self) -> None:
        if not self.observation_id:
            raise ValueError("observation_id is required.")
        if not self.source_excerpt:
            raise ValueError("source_excerpt is required (fails loudly rather than accepting an untraceable claim).")
        _validate_derivation(self.direct_or_derived, self.derivation)


# ---------------------------------------------------------------------
# Typed observation subclasses (Part 4 pattern -- a representative,
# not exhaustive, set: enough to exercise Market/Team/Product/
# Execution/Traction/Financial-Health evaluators faithfully)
# ---------------------------------------------------------------------

class RevenueMetricType(str, Enum):
    ARR = "ARR"
    MRR = "MRR"
    ANNUAL_REVENUE = "ANNUAL_REVENUE"
    QUARTERLY_REVENUE = "QUARTERLY_REVENUE"
    BOOKINGS = "BOOKINGS"
    GMV = "GMV"


@dataclass(frozen=True)
class RevenueObservation(EvidenceBase):
    amount: Decimal = Decimal("0")
    currency: str = "USD"
    metric_type: RevenueMetricType = RevenueMetricType.ARR

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.as_of_date is None:
            raise ValueError("RevenueObservation requires as_of_date.")
        if self.amount < 0:
            raise ValueError("Revenue amount cannot be negative.")


class CustomerType(str, Enum):
    PAYING = "PAYING"
    PILOT = "PILOT"
    SIGNED_CONTRACT_UNPAID = "SIGNED_CONTRACT_UNPAID"
    FREEMIUM_ACTIVE = "FREEMIUM_ACTIVE"


@dataclass(frozen=True)
class CustomerCountObservation(EvidenceBase):
    count: int = 0
    customer_type: CustomerType = CustomerType.PAYING

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.as_of_date is None:
            raise ValueError("CustomerCountObservation requires as_of_date.")
        if self.count < 0:
            raise ValueError("Customer count cannot be negative.")


@dataclass(frozen=True)
class RetentionObservation(EvidenceBase):
    nrr_pct: Decimal | None = None
    grr_pct: Decimal | None = None
    logo_churn_pct: Decimal | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.nrr_pct is None and self.grr_pct is None and self.logo_churn_pct is None:
            raise ValueError("RetentionObservation requires at least one of nrr_pct/grr_pct/logo_churn_pct.")


class FundingRoundLabel(str, Enum):
    PRE_SEED = "PRE_SEED"
    SEED = "SEED"
    SERIES_A = "SERIES_A"
    SERIES_B = "SERIES_B"
    SERIES_C_PLUS = "SERIES_C_PLUS"
    GROWTH_PE = "GROWTH_PE"
    UNDISCLOSED = "UNDISCLOSED"


@dataclass(frozen=True)
class FundingObservation(EvidenceBase):
    amount: Decimal = Decimal("0")
    currency: str = "USD"
    round_label: FundingRoundLabel = FundingRoundLabel.UNDISCLOSED
    announced_date: date | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.announced_date is None:
            raise ValueError("FundingObservation requires announced_date.")
    # Deliberately no field lets this be consumed as revenue or cash --
    # Part 5's "funding != revenue, funding != cash" rule is enforced by
    # evaluators.py never accepting a FundingObservation where a
    # RevenueObservation/CashObservation is required, not by a shared field.


@dataclass(frozen=True)
class CashObservation(EvidenceBase):
    amount: Decimal = Decimal("0")
    currency: str = "USD"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.as_of_date is None:
            raise ValueError("CashObservation requires as_of_date.")


class BurnPeriod(str, Enum):
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


@dataclass(frozen=True)
class BurnObservation(EvidenceBase):
    amount: Decimal = Decimal("0")
    currency: str = "USD"
    period: BurnPeriod = BurnPeriod.MONTHLY

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.as_of_date is None:
            raise ValueError("BurnObservation requires as_of_date.")


@dataclass(frozen=True)
class RunwayStatementObservation(EvidenceBase):
    """A direct disclosed runway claim (e.g. '18 months of runway'),
    accepted in its own right per the Rulebook's Capital Efficiency
    design -- does not require a separate cash/burn split to exist."""

    months: Decimal = Decimal("0")


class MarketEstimateSourceType(str, Enum):
    THIRD_PARTY_RESEARCH = "THIRD_PARTY_RESEARCH"
    COMPANY_STATED = "COMPANY_STATED"
    ANALYST_ESTIMATE = "ANALYST_ESTIMATE"


@dataclass(frozen=True)
class MarketSizeObservation(EvidenceBase):
    amount: Decimal = Decimal("0")
    currency: str = "USD"
    market_label: str = ""
    estimate_source_type: MarketEstimateSourceType = MarketEstimateSourceType.COMPANY_STATED

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.market_label:
            raise ValueError("MarketSizeObservation requires a named market_label.")


@dataclass(frozen=True)
class MarketGrowthObservation(EvidenceBase):
    growth_pct: Decimal = Decimal("0")
    category_label: str = ""
    estimate_source_type: MarketEstimateSourceType = MarketEstimateSourceType.COMPANY_STATED

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.category_label:
            raise ValueError("MarketGrowthObservation requires a named category_label.")


class FounderExperienceType(str, Enum):
    UNRELATED_DOMAIN = "UNRELATED_DOMAIN"
    ADJACENT_DOMAIN = "ADJACENT_DOMAIN"
    DIRECT_DOMAIN = "DIRECT_DOMAIN"
    REPEAT_FOUNDER = "REPEAT_FOUNDER"
    PRIOR_EXIT = "PRIOR_EXIT"


@dataclass(frozen=True)
class FounderExperienceObservation(EvidenceBase):
    founder_role: str = ""
    experience_type: FounderExperienceType = FounderExperienceType.UNRELATED_DOMAIN
    prior_entity_name: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.founder_role:
            raise ValueError("FounderExperienceObservation requires founder_role.")
        if self.experience_type in (FounderExperienceType.REPEAT_FOUNDER, FounderExperienceType.PRIOR_EXIT) and not self.prior_entity_name:
            raise ValueError(f"{self.experience_type} requires a named prior_entity_name.")


class FounderOutcomeType(str, Enum):
    ACQUIRED = "ACQUIRED"
    IPO = "IPO"
    SHUT_DOWN = "SHUT_DOWN"
    STILL_OPERATING = "STILL_OPERATING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FounderOutcomeObservation(EvidenceBase):
    outcome_type: FounderOutcomeType = FounderOutcomeType.UNKNOWN
    prior_entity_name: str = ""
    attributed_to_founder: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.prior_entity_name:
            raise ValueError("FounderOutcomeObservation requires a named prior_entity_name.")


class CompetitorType(str, Enum):
    DIRECT = "DIRECT"
    ADJACENT = "ADJACENT"
    SUBSTITUTE = "SUBSTITUTE"


@dataclass(frozen=True)
class CompetitiveEvidenceObservation(EvidenceBase):
    named_competitor: str = ""
    competitor_type: CompetitorType = CompetitorType.DIRECT
    differentiator_named: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.named_competitor:
            raise ValueError("CompetitiveEvidenceObservation requires a named_competitor.")


@dataclass(frozen=True)
class ProductCapabilityObservation(EvidenceBase):
    capability_label: str = ""
    shipped: bool = False
    named_integration: str | None = None
    disclosed_reliability_metric: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.capability_label:
            raise ValueError("ProductCapabilityObservation requires capability_label.")


@dataclass(frozen=True)
class CustomerEvidenceObservation(EvidenceBase):
    named_customer: str | None = None
    outcome_claim: str = ""
    quantified: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.outcome_claim:
            raise ValueError("CustomerEvidenceObservation requires outcome_claim.")


@dataclass(frozen=True)
class CommercialContractObservation(EvidenceBase):
    contract_type: CustomerType = CustomerType.SIGNED_CONTRACT_UNPAID
    named_customer: str | None = None
    renewal_evidence: bool = False


@dataclass(frozen=True)
class NegativeSignalObservation(EvidenceBase):
    """Explicit, typed negative evidence -- see Rulebook Part 17.
    Never constructed from mere absence of positive evidence; always
    requires its own cited source_excerpt (enforced by EvidenceBase)."""

    signal_type: str = ""     # e.g. "revenue_decline", "founder_departure"
    severity: str = "MODERATE"  # LOW | MODERATE | SEVERE
    affected_dimension: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.signal_type:
            raise ValueError("NegativeSignalObservation requires signal_type.")
        if not self.affected_dimension:
            raise ValueError("NegativeSignalObservation requires affected_dimension.")


# ---------------------------------------------------------------------
# Scoring-stage output types
# ---------------------------------------------------------------------

class AvailabilityStatus(str, Enum):
    SCORABLE = "SCORABLE"
    UNAVAILABLE_NO_EVIDENCE = "UNAVAILABLE_NO_EVIDENCE"
    UNAVAILABLE_INSUFFICIENT = "UNAVAILABLE_INSUFFICIENT"
    UNAVAILABLE_PRIVATE_INFORMATION = "UNAVAILABLE_PRIVATE_INFORMATION"
    UNAVAILABLE_NOT_APPLICABLE_FOR_STAGE = "UNAVAILABLE_NOT_APPLICABLE_FOR_STAGE"
    UNAVAILABLE_RESEARCH_FAILURE = "UNAVAILABLE_RESEARCH_FAILURE"
    UNAVAILABLE_CONFLICTING_EVIDENCE = "UNAVAILABLE_CONFLICTING_EVIDENCE"


UNAVAILABLE_STATUSES = {
    AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE,
    AvailabilityStatus.UNAVAILABLE_INSUFFICIENT,
    AvailabilityStatus.UNAVAILABLE_PRIVATE_INFORMATION,
    AvailabilityStatus.UNAVAILABLE_NOT_APPLICABLE_FOR_STAGE,
    AvailabilityStatus.UNAVAILABLE_RESEARCH_FAILURE,
    AvailabilityStatus.UNAVAILABLE_CONFLICTING_EVIDENCE,
}


class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class ClassificationResult:
    classification: str
    supporting_evidence_ids: tuple[str, ...]
    negative_evidence_ids: tuple[str, ...] = ()
    reason: str = ""

    def __post_init__(self) -> None:
        if self.classification != "NO_SIGNAL" and not self.supporting_evidence_ids and not self.negative_evidence_ids:
            raise ValueError(
                f"A non-NO_SIGNAL classification ({self.classification}) requires at least one "
                f"cited evidence id -- an unsupported positive/negative label is a contract "
                f"violation (Rulebook Part 16)."
            )


@dataclass(frozen=True)
class RuleTrace:
    rule_id: str
    provisional_parameter_ids: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class DimensionResult:
    dimension_id: str
    pillar: str
    weight: Decimal
    score: Decimal | None
    availability: AvailabilityStatus
    confidence: ConfidenceLevel
    classification: ClassificationResult | None
    rule_trace: RuleTrace
    cited_evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.score is not None and self.availability != AvailabilityStatus.SCORABLE:
            raise ValueError(f"{self.dimension_id}: a non-null score requires SCORABLE availability.")
        if self.score is None and self.availability == AvailabilityStatus.SCORABLE:
            raise ValueError(f"{self.dimension_id}: SCORABLE availability requires a non-null score.")
        if self.score is not None and not (Decimal("0") <= self.score <= Decimal("10")):
            raise ValueError(f"{self.dimension_id}: score {self.score} out of [0,10] range.")


@dataclass(frozen=True)
class PillarResult:
    pillar: str
    strength: Decimal | None          # 0-10, None if pillar itself is unpublishable
    completeness_pct: Decimal         # 0-100, coverage of this pillar's configured weight
    confidence: ConfidenceLevel
    publishable: bool
    dimension_results: tuple[DimensionResult, ...]
    withhold_reason: str | None = None


@dataclass(frozen=True)
class CoverageResult:
    overall_pct: Decimal
    per_pillar_pct: dict


@dataclass(frozen=True)
class ConfidenceResult:
    overall: ConfidenceLevel
    per_pillar: dict


@dataclass(frozen=True)
class SPSResult:
    sps: Decimal | None
    publishable: bool
    withhold_reason: str | None
    pillar_results: tuple[PillarResult, ...]
    coverage: CoverageResult
    confidence: ConfidenceResult
    stage: Stage

    def __post_init__(self) -> None:
        if self.sps is not None and not self.publishable:
            raise ValueError("A non-null SPS requires publishable=True.")
        if self.sps is None and self.publishable:
            raise ValueError("publishable=True requires a non-null SPS.")
        if self.sps is not None and not (Decimal("0") <= self.sps <= Decimal("100")):
            raise ValueError(f"SPS {self.sps} out of [0,100] range.")
