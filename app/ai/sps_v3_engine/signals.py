"""
Phase 10.8G -- substantive-signal identity, deduplication, source-
independence corroboration, and conflict detection/resolution.

Core amendment: Strength and Coverage must be computed over UNIQUE
ACCEPTED SUBSTANTIVE SIGNALS, never over raw observation/source counts
(Rulebook Part 16 amendment). Confidence may still consider genuinely
independent corroboration -- but "genuinely independent" is itself a
narrow, explicit, deterministic classification, not "more than one
source exists."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.ai.sps_v3_engine.types import (
    CommercialContractObservation,
    CompetitiveEvidenceObservation,
    ConflictStatus,
    CustomerCountObservation,
    CustomerEvidenceObservation,
    EvidenceBase,
    FounderExperienceObservation,
    FounderOutcomeObservation,
    MarketGrowthObservation,
    MarketSizeObservation,
    ProductCapabilityObservation,
    ProvenanceGrade,
    RetentionObservation,
    RevenueObservation,
    RunwayStatementObservation,
    SourceIndependence,
)

# Deterministic, total precedence order for CONFLICT RESOLUTION only
# (Part 8/9) -- distinct from Confidence's grade mapping in
# evaluators.py. Grades within the same tier NEVER auto-resolve a
# conflict against each other (Part 8's explicit instruction: no
# universal winner between self-report and high-quality-secondary).
_PRECEDENCE_TIER = {
    ProvenanceGrade.PRIMARY_VERIFIED: 3,
    ProvenanceGrade.PRIMARY_SELF_REPORTED: 2,
    ProvenanceGrade.HIGH_QUALITY_SECONDARY: 2,
    ProvenanceGrade.DERIVED: 2,
    ProvenanceGrade.SECONDARY_ESTIMATE: 1,
    ProvenanceGrade.UNVERIFIED: 0,
}


def _signal_key(observation: EvidenceBase) -> tuple:
    """The deterministic identity of the SUBSTANTIVE FACT an
    observation reports -- deliberately EXCLUDES the reported value
    itself, so two observations of the same (metric, entity, period)
    with DIFFERENT values are the same signal-key (a conflict to
    resolve, Part 9), while two observations with the same value are
    corroboration of one signal (Part 3/4), and observations of
    different periods/entities/metrics are genuinely distinct signals
    (never merged)."""

    if isinstance(observation, RevenueObservation):
        return ("revenue", "COMPANY", observation.metric_type.value, observation.as_of_date.isoformat())
    if isinstance(observation, CustomerCountObservation):
        return ("customer_count", "COMPANY", observation.customer_type.value, observation.as_of_date.isoformat())
    if isinstance(observation, RetentionObservation):
        # Retention doesn't carry as_of_date in this harness's minimal
        # schema; identity collapses to "the current retention signal"
        # -- multiple RetentionObservations are treated as the same
        # signal (corroboration/conflict) unless a future schema
        # revision adds a date field.
        return ("retention", "COMPANY", "RETENTION_METRIC", "CURRENT")
    if isinstance(observation, MarketSizeObservation):
        return ("market_size", observation.market_label, "SIZE", "CURRENT")
    if isinstance(observation, MarketGrowthObservation):
        return ("market_growth", observation.category_label, "GROWTH", "CURRENT")
    if isinstance(observation, FounderExperienceObservation):
        return ("founder_experience", observation.founder_role, observation.experience_type.value, observation.prior_entity_name or "")
    if isinstance(observation, FounderOutcomeObservation):
        return ("founder_outcome", observation.prior_entity_name, observation.outcome_type.value, "STRUCTURAL")
    if isinstance(observation, CompetitiveEvidenceObservation):
        return ("competitor", observation.named_competitor, observation.competitor_type.value, "CURRENT")
    if isinstance(observation, ProductCapabilityObservation):
        return ("product_capability", observation.capability_label, str(observation.shipped), "CURRENT")
    if isinstance(observation, CustomerEvidenceObservation):
        return ("customer_evidence", observation.named_customer or "UNNAMED", observation.outcome_claim, "CURRENT")
    if isinstance(observation, CommercialContractObservation):
        return ("commercial_contract", observation.named_customer or "UNNAMED", observation.contract_type.value, "CURRENT")
    if isinstance(observation, RunwayStatementObservation):
        return ("runway_statement", "COMPANY", "RUNWAY", "CURRENT")
    # Cash/Burn/Funding: identity by (type, as_of_date/announced_date) --
    # handled generically via getattr since their shape is simple.
    as_of = getattr(observation, "as_of_date", None) or getattr(observation, "announced_date", None)
    return (type(observation).__name__, "COMPANY", "VALUE", as_of.isoformat() if as_of else "UNDATED")


def _values_agree(a: EvidenceBase, b: EvidenceBase) -> bool:
    """Whether two same-signal-key observations report the SAME
    substantive value (corroboration) or a DIFFERENT one (conflict,
    Part 9). Only quantitative types can meaningfully disagree in this
    harness's schema; qualitative types sharing a signal_key are
    definitionally the same classification (the key already encodes
    the classification), so they always agree."""

    if isinstance(a, RevenueObservation) and isinstance(b, RevenueObservation):
        return a.amount == b.amount
    if isinstance(a, CustomerCountObservation) and isinstance(b, CustomerCountObservation):
        return a.count == b.count
    if isinstance(a, RetentionObservation) and isinstance(b, RetentionObservation):
        return (a.nrr_pct, a.grr_pct, a.logo_churn_pct) == (b.nrr_pct, b.grr_pct, b.logo_churn_pct)
    if isinstance(a, MarketSizeObservation) and isinstance(b, MarketSizeObservation):
        return a.amount == b.amount
    if isinstance(a, MarketGrowthObservation) and isinstance(b, MarketGrowthObservation):
        return a.growth_pct == b.growth_pct
    if isinstance(a, RunwayStatementObservation) and isinstance(b, RunwayStatementObservation):
        return a.months == b.months
    if hasattr(a, "amount") and hasattr(b, "amount"):
        return a.amount == b.amount
    return True  # qualitative types: same signal_key implies same claim by construction


def _resolve_conflict_precedence(observations: tuple) -> tuple[EvidenceBase | None, ConflictStatus]:
    """Deterministic, ORDER-INDEPENDENT conflict resolution (Part 8-10).
    Returns (winning_observation_or_None, status). Never depends on
    list order -- always sorts by (precedence_tier, observation_id) so
    ties break on a stable, content-derived key, never insertion order."""

    tiers = sorted({_PRECEDENCE_TIER[o.provenance_grade] for o in observations}, reverse=True)
    top_tier = tiers[0]
    top_candidates = sorted(
        (o for o in observations if _PRECEDENCE_TIER[o.provenance_grade] == top_tier),
        key=lambda o: o.observation_id,
    )

    if len(tiers) > 1:
        # A strictly higher tier exists -- it deterministically wins
        # (Part 9 Example D: PRIMARY_VERIFIED beats SECONDARY_ESTIMATE).
        if len(top_candidates) == 1:
            return top_candidates[0], ConflictStatus.CONFLICT_RESOLVED_BY_PRECEDENCE
        # Multiple observations tied at the top tier but a lower tier
        # also disagreed -- still a same-tier conflict among the top
        # candidates; fall through to the tie logic below.

    if len(top_candidates) == 1:
        return top_candidates[0], ConflictStatus.CONFLICT_RESOLVED_BY_PRECEDENCE

    # Same tier, genuine disagreement -- Part 8's explicit "no
    # universal winner" case (e.g. self-report vs. independent
    # high-quality-secondary, or two independent high-quality sources).
    return None, ConflictStatus.CONFLICT_DETECTED


@dataclass(frozen=True)
class CanonicalSignal:
    """One deduplicated, conflict-resolved substantive fact -- the
    unit Strength and Coverage evaluators consume (Part 4/5), never a
    raw observation list."""

    signal_key: tuple
    accepted_observation: EvidenceBase | None    # None if CONFLICT_DETECTED and unresolved
    supporting_observation_ids: tuple[str, ...]    # every observation contributing (for the trace, Part 31)
    conflict_status: ConflictStatus
    independent_corroboration_count: int           # count of genuinely INDEPENDENT observations (Part 6), capped
                                                     # sensibly by build_canonical_signals below


def build_canonical_signals(observations: tuple) -> tuple[CanonicalSignal, ...]:
    """Groups raw observations by signal_key, resolves same-key
    disagreement via precedence (never insertion order), and computes
    an independence-aware corroboration count for Confidence's use.
    This is the ONLY place Strength-relevant deduplication happens --
    every evaluator must consume this output, never raw `company.evidence`
    directly, for any dimension in scope of the Part 17 fix."""

    accepted = [o for o in observations]
    groups: dict[tuple, list] = {}
    for obs in accepted:
        groups.setdefault(_signal_key(obs), []).append(obs)

    signals = []
    for key in sorted(groups.keys(), key=lambda k: tuple(str(x) for x in k)):
        group = groups[key]
        # Partition into value-agreement clusters first (same key,
        # same value = corroboration; same key, different value =
        # candidates for conflict resolution).
        agreeing_clusters: list[list] = []
        for obs in sorted(group, key=lambda o: o.observation_id):
            placed = False
            for cluster in agreeing_clusters:
                if _values_agree(cluster[0], obs):
                    cluster.append(obs)
                    placed = True
                    break
            if not placed:
                agreeing_clusters.append([obs])

        if len(agreeing_clusters) == 1:
            cluster = agreeing_clusters[0]
            representative = min(cluster, key=lambda o: (-_PRECEDENCE_TIER[o.provenance_grade], o.observation_id))
            independent_count = _count_independent(cluster)
            signals.append(CanonicalSignal(
                signal_key=key,
                accepted_observation=representative,
                supporting_observation_ids=tuple(o.observation_id for o in cluster),
                conflict_status=ConflictStatus.NO_CONFLICT,
                independent_corroboration_count=independent_count,
            ))
        else:
            # Genuine value disagreement within the same signal_key --
            # resolve by precedence across cluster REPRESENTATIVES
            # (one per distinct value), deterministically, no order
            # dependence.
            representatives = tuple(
                min(cluster, key=lambda o: (-_PRECEDENCE_TIER[o.provenance_grade], o.observation_id))
                for cluster in agreeing_clusters
            )
            winner, status = _resolve_conflict_precedence(representatives)
            all_ids = tuple(o.observation_id for cluster in agreeing_clusters for o in cluster)
            if winner is not None:
                winning_cluster = next(c for c in agreeing_clusters if winner in c)
                independent_count = _count_independent(winning_cluster)
                signals.append(CanonicalSignal(
                    signal_key=key, accepted_observation=winner,
                    supporting_observation_ids=all_ids, conflict_status=status,
                    independent_corroboration_count=independent_count,
                ))
            else:
                signals.append(CanonicalSignal(
                    signal_key=key, accepted_observation=None,
                    supporting_observation_ids=all_ids, conflict_status=ConflictStatus.CONFLICT_DETECTED,
                    independent_corroboration_count=0,
                ))

    return tuple(signals)


def _count_independent(cluster: list) -> int:
    """Part 6: only observations explicitly marked INDEPENDENT of each
    other (distinct origin_id, or explicitly tagged INDEPENDENT with no
    shared origin_id) count toward corroboration beyond the first.
    SAME_ORIGIN/DERIVATIVE/UNKNOWN_ORIGIN observations contribute 0
    additional independent corroboration, no matter how many exist --
    this is the direct fix for the derivative-source attack (Part 19)."""

    seen_origins: set[str] = set()
    independent_count = 0
    for obs in cluster:
        if obs.source_independence == SourceIndependence.INDEPENDENT:
            origin = obs.origin_id or obs.observation_id  # an INDEPENDENT obs with no origin_id is its own origin
            if origin not in seen_origins:
                seen_origins.add(origin)
                independent_count += 1
        # SAME_ORIGIN, DERIVATIVE, UNKNOWN_ORIGIN: never counted,
        # regardless of quantity (Part 19's required invariant).
    return independent_count
