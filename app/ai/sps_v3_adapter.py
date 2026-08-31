"""
Phase 10.9, Part 9 -- V3 evidence adapter.

    Production research (app/ai/research_enrichment.py)
    -> evidence extraction + pillar scoring (V2.1, app/ai/analyze_pillar.py,
       app/ai/pillar_scoring.py, app/ai/evidence_extraction.py -- UNCHANGED,
       still the only thing that runs by default)
    -> V3 canonical observation adapter (THIS FILE)
    -> canonical signals (app/ai/sps_v3_engine/signals.py)
    -> deterministic evaluators (app/ai/sps_v3_engine/evaluators.py)
    -> aggregation (app/ai/sps_v3_engine/aggregation.py)
    -> SIEMethodologyAnalysis.sps_v3 (app/models/sps_v3.py)

This module makes ZERO new research calls and gathers ZERO new evidence
(Phase 10.9 Part 8) -- it only re-reads the SAME six PillarAnalysis
objects V2.1 already computed for this exact analysis. Its one LLM call
(gated behind SPS_V3_ENABLED, see below) is a narrow CLASSIFICATION step
over text V2.1 already extracted and already marked "Observed" (real,
sourced, non-inferred) -- explicitly permitted by Phase 10.9 Part 7
("The LLM may... extract facts, normalize facts, classify evidence").
It is never asked for, and structurally cannot produce, a numeric score:
its output schema (_ExtractionResult below) has no score-shaped field at
all. Every downstream number is produced exclusively by the frozen,
deterministic app.ai.sps_v3_engine evaluators.

SCOPE (Part 9's "responsibly possible", Part 8's "not an attempt to
maximize Coverage"): this v1 adapter classifies evidence for 9 of the 27
V3 dimensions -- the qualitative ones whose required observation fields
(a named competitor, a founder's role, a shipped capability label, a
contract type) are safely groundable in a verbatim quote from V2.1's own
evidence text. It deliberately does NOT attempt the 4 Category-A
quantitative dimensions (current_scale, growth_trajectory,
retention_engagement, capital_efficiency) or the 2 remaining Category-B
Financial Health / Traction dimensions that require a precise number with
an as-of date (revenue_quality, customer_adoption) -- fabricating those
from loosely-parsed narrative text is exactly the numeric-fabrication
risk Part 10 exists to prevent, and the V2.1 evidence pipeline's own free-
text Evidence.statement shape (app/models/evidence.py) offers no
structured number to safely draw from. These dimensions are correctly,
honestly UNKNOWN under this adapter -- see
docs/methodology/SPS_V3_PRODUCTION_INTEGRATION_10_9.md Section 5 for the
full accounting and the explicitly-named next step (a dedicated
structured-numeric-extraction adapter) this phase does NOT build.

FIREWALL: every observation this adapter constructs carries a
verbatim_quote that is re-verified (after the LLM call returns) to
actually appear, near-verbatim, in the source text the model was given --
mirroring app/ai/evidence_provenance.py's existing "verify, don't just
prompt" discipline. A classification whose quote cannot be found is
dropped entirely, never kept on trust. No observation is ever
constructed from an "Inferred" or "Unavailable" V2.1 subscore -- only
"Observed".
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone

from pydantic import BaseModel, Field

from app.ai.pillar_shared import call_analysis_model, parse_json_from_response
from app.ai.sps_v3_engine.aggregation import evaluate_sps, classify_ux_state
from app.ai.sps_v3_engine.evaluators import evaluate_all_dimensions
from app.ai.sps_v3_engine.evidence_bundle import EvidenceBundle
from app.ai.sps_v3_engine.registry import DEFAULT_REGISTRY
from app.ai.sps_v3_engine.types import (
    CommercialContractObservation,
    CompetitiveEvidenceObservation,
    CompetitorType,
    CustomerEvidenceObservation,
    CustomerType,
    DirectOrDerived,
    EvidenceBase,
    ExtractionConfidence,
    FounderExperienceObservation,
    FounderExperienceType,
    FounderOutcomeObservation,
    FounderOutcomeType,
    ProductCapabilityObservation,
    ProvenanceGrade,
    ProvenanceStatus,
    Stage,
)
from app.models.startup import PillarAnalysis, SIEMethodologyAnalysis
from app.models.sps_v3 import SPSV3Assessment, SPSV3PillarResult

SPS_V3_ENGINE_VERSION = "SPS_V3_10_9"
# Deliberately NOT app.ai.sie_v2_methodology.METHODOLOGY_VERSION or
# app.ai.scoring_methodology.SCORING_VERSION -- Phase 10.9 Part 28
# forbids reusing a V2.1 version string for V3.
SPS_V3_SCORING_VERSION = "sps_v3.10_9.1"


def sps_v3_enabled() -> bool:
    """
    Phase 10.9 Part 29 -- the feature flag. Defaults OFF: an analysis
    run with this unset behaves EXACTLY as it did before this phase (no
    sps_v3 field is ever populated, no extra LLM call is made). Set
    SPS_ENGINE_VERSION=v3 in the environment to additionally compute the
    V3 assessment alongside the always-on V2.1 pipeline. This is
    intentionally a single boolean env var, not a flag platform.
    """
    return os.getenv("SPS_ENGINE_VERSION", "v2_1").strip().lower() == "v3"


_STAGE_KEYWORDS: tuple[tuple[str, Stage], ...] = (
    ("pre-seed", Stage.PRE_SEED),
    ("pre seed", Stage.PRE_SEED),
    ("idea", Stage.IDEA),
    ("seed", Stage.SEED),
    ("series a", Stage.SERIES_A),
    ("series b", Stage.SERIES_B_PLUS),
    ("series c", Stage.SERIES_B_PLUS),
    ("series d", Stage.SERIES_B_PLUS),
    ("growth", Stage.GROWTH),
    ("public", Stage.GROWTH),
    ("ipo", Stage.GROWTH),
)


def map_stage(stage_text: str | None) -> Stage:
    """Best-effort free-text -> Stage mapping. Only affects the 4
    Category-A dimensions this v1 adapter never feeds evidence to (see
    module docstring), so an unrecognized/empty stage defaulting to SEED
    has no observable effect on this adapter's output today -- kept
    correct anyway for whenever a future phase extends Category-A
    coverage."""
    lowered = (stage_text or "").strip().lower()
    for keyword, stage in _STAGE_KEYWORDS:
        if keyword in lowered:
            return stage
    return Stage.SEED


# ---------------------------------------------------------------------
# Extraction schema -- structurally cannot carry a score. Every field is
# either a closed enum, a bool, or a short label string, plus the
# required verbatim_quote used by the post-call firewall below.
# ---------------------------------------------------------------------

class _CompetitorClaim(BaseModel):
    verbatim_quote: str
    named_competitor: str
    # bool | None (not plain bool): the model sometimes emits an explicit
    # `null` for a boolean it isn't confident about, rather than omitting
    # the key or writing `false` -- a bare `bool` field rejects that with
    # a validation error and (before this fix) discarded the entire
    # extraction result. None is treated as "not stated" -> False when
    # constructing the observation (_extraction_to_observations), never
    # as True.
    differentiator_named: bool | None = False


class _CustomerDemandClaim(BaseModel):
    verbatim_quote: str
    outcome_claim: str
    named_customer: str | None = None


class _FounderExperienceClaim(BaseModel):
    verbatim_quote: str
    founder_role: str
    experience_type: str  # one of FounderExperienceType values
    prior_entity_name: str | None = None


class _FounderOutcomeClaim(BaseModel):
    verbatim_quote: str
    prior_entity_name: str
    outcome_type: str  # one of FounderOutcomeType values


class _CapabilityClaim(BaseModel):
    verbatim_quote: str
    capability_label: str
    shipped: bool | None = False


class _ContractClaim(BaseModel):
    verbatim_quote: str
    contract_type: str  # one of CustomerType values
    named_customer: str | None = None
    renewal_evidence: bool | None = False


class _PillarExtraction(BaseModel):
    competitors: list[_CompetitorClaim] = Field(default_factory=list)
    customer_demand: list[_CustomerDemandClaim] = Field(default_factory=list)
    customer_value: list[_CustomerDemandClaim] = Field(default_factory=list)
    founder_experience: list[_FounderExperienceClaim] = Field(default_factory=list)
    founder_outcomes: list[_FounderOutcomeClaim] = Field(default_factory=list)
    capabilities: list[_CapabilityClaim] = Field(default_factory=list)
    contracts: list[_ContractClaim] = Field(default_factory=list)


class _ExtractionResult(BaseModel):
    market: _PillarExtraction = Field(default_factory=_PillarExtraction)
    team: _PillarExtraction = Field(default_factory=_PillarExtraction)
    product: _PillarExtraction = Field(default_factory=_PillarExtraction)
    execution: _PillarExtraction = Field(default_factory=_PillarExtraction)
    traction: _PillarExtraction = Field(default_factory=_PillarExtraction)


_SYSTEM_MESSAGE = """You are a strict evidence classifier. You are given, per \
pillar, a list of ALREADY-VERIFIED text passages about one startup. Your \
ONLY job is to classify what is explicitly stated into a fixed taxonomy. \
You do not score, rate, rank, or judge the company in any way -- there is \
no score field in your output schema, and any such judgment is out of \
scope. You do not invent, estimate, or infer any fact not explicitly \
present in the given text. Every classification you produce MUST include \
verbatim_quote: an exact, word-for-word substring copied from the \
provided text that supports it. If you cannot find explicit text \
supporting a classification, do not include it -- an empty list is \
always a valid, correct answer for any category. Return only valid \
JSON matching the given schema."""


def _pillar_observed_text(pillar: PillarAnalysis) -> str:
    """Only 'Observed' subscores -- never 'Inferred' (an LLM judgment
    call, not a verified fact) or 'Unavailable'. Pulls each such
    subscore's own evidence quotes and extraction-stage signals -- the
    same fields app/models/scoring.py's Subscore docstring documents as
    populated by the evidence-extraction stage, not the scoring stage."""
    lines: list[str] = []
    for subscore in pillar.score_breakdown.subscores:
        if subscore.evidence_status != "Observed":
            continue
        for item in subscore.evidence:
            if item:
                lines.append(str(item))
        for signal in subscore.signals:
            if signal:
                lines.append(str(signal))
    return "\n".join(lines)


def _quote_is_grounded(quote: str, source_text: str) -> bool:
    """Post-call firewall (module docstring) -- mirrors
    app/ai/evidence_provenance.py's verify-don't-trust discipline. A
    normalized substring check: whitespace-insensitive, case-insensitive.
    Never trusts the model's own claim that a quote is verbatim."""
    if not quote or not source_text:
        return False
    normalize = lambda s: " ".join(s.split()).lower()
    return normalize(quote) in normalize(source_text)


def _extraction_confidence_from_v2_confidence(level: str) -> ExtractionConfidence:
    return {
        "Low": ExtractionConfidence.LOW,
        "Medium": ExtractionConfidence.MEDIUM,
        "High": ExtractionConfidence.HIGH,
    }.get(level, ExtractionConfidence.MEDIUM)


def _base_kwargs(observation_id: str, quote: str) -> dict:
    return dict(
        observation_id=observation_id,
        source_excerpt=quote,
        provenance_status=ProvenanceStatus.ACCEPTED,
        # V2.1's own evidence is sourced from company materials + public
        # research the model was given, never independently re-verified
        # against a primary filing -- PRIMARY_SELF_REPORTED is the
        # correct, non-inflated grade (never PRIMARY_VERIFIED, which
        # Phase 10.8's rulebook reserves for independently-confirmed
        # facts this adapter has no way to establish).
        provenance_grade=ProvenanceGrade.PRIMARY_SELF_REPORTED,
        direct_or_derived=DirectOrDerived.DIRECT,
        extraction_confidence=ExtractionConfidence.MEDIUM,
    )


def _extraction_to_observations(
    pillar_key: str,
    extraction: _PillarExtraction,
    source_text: str,
    id_seed: str,
) -> list[EvidenceBase]:
    observations: list[EvidenceBase] = []
    counter = 0

    def next_id(prefix: str) -> str:
        nonlocal counter
        counter += 1
        return f"{id_seed}-{prefix}-{counter}"

    for claim in extraction.competitors:
        if not _quote_is_grounded(claim.verbatim_quote, source_text):
            continue
        observations.append(CompetitiveEvidenceObservation(
            **_base_kwargs(next_id("COMP"), claim.verbatim_quote),
            named_competitor=claim.named_competitor[:200],
            competitor_type=CompetitorType.DIRECT,
            differentiator_named=bool(claim.differentiator_named),
        ))

    for claim in extraction.customer_demand + extraction.customer_value:
        if not _quote_is_grounded(claim.verbatim_quote, source_text):
            continue
        if not claim.outcome_claim:
            continue
        observations.append(CustomerEvidenceObservation(
            **_base_kwargs(next_id("CEV"), claim.verbatim_quote),
            named_customer=(claim.named_customer or None),
            outcome_claim=claim.outcome_claim[:500],
            quantified=False,
        ))

    for claim in extraction.founder_experience:
        if not _quote_is_grounded(claim.verbatim_quote, source_text):
            continue
        try:
            experience_type = FounderExperienceType(claim.experience_type)
        except ValueError:
            continue
        if experience_type in (FounderExperienceType.REPEAT_FOUNDER, FounderExperienceType.PRIOR_EXIT) and not claim.prior_entity_name:
            # Firewall: these two enum values require a named prior
            # entity (enforced by the dataclass itself) -- downgrade
            # rather than fabricate a name.
            experience_type = FounderExperienceType.DIRECT_DOMAIN
        if not claim.founder_role:
            continue
        observations.append(FounderExperienceObservation(
            **_base_kwargs(next_id("FEXP"), claim.verbatim_quote),
            founder_role=claim.founder_role[:200],
            experience_type=experience_type,
            prior_entity_name=(claim.prior_entity_name or None),
        ))

    for claim in extraction.founder_outcomes:
        if not _quote_is_grounded(claim.verbatim_quote, source_text):
            continue
        if not claim.prior_entity_name:
            continue
        try:
            outcome_type = FounderOutcomeType(claim.outcome_type)
        except ValueError:
            continue
        observations.append(FounderOutcomeObservation(
            **_base_kwargs(next_id("FOUT"), claim.verbatim_quote),
            outcome_type=outcome_type,
            prior_entity_name=claim.prior_entity_name[:200],
            attributed_to_founder=True,
        ))

    for claim in extraction.capabilities:
        if not _quote_is_grounded(claim.verbatim_quote, source_text):
            continue
        if not claim.capability_label:
            continue
        observations.append(ProductCapabilityObservation(
            **_base_kwargs(next_id("PCAP"), claim.verbatim_quote),
            capability_label=claim.capability_label[:200],
            shipped=bool(claim.shipped),
        ))

    for claim in extraction.contracts:
        if not _quote_is_grounded(claim.verbatim_quote, source_text):
            continue
        try:
            contract_type = CustomerType(claim.contract_type)
        except ValueError:
            continue
        observations.append(CommercialContractObservation(
            **_base_kwargs(next_id("CONTR"), claim.verbatim_quote),
            contract_type=contract_type,
            named_customer=(claim.named_customer or None),
            renewal_evidence=bool(claim.renewal_evidence),
        ))

    return observations


def classify_evidence_for_v3(
    market: PillarAnalysis,
    team: PillarAnalysis,
    product: PillarAnalysis,
    execution: PillarAnalysis,
    traction: PillarAnalysis,
    id_seed: str,
) -> tuple[EvidenceBase, ...]:
    """
    The one LLM call this adapter makes (Part 7-permitted classification,
    never scoring). Financial Health is deliberately excluded from the
    request -- this v1 adapter has no safely-classifiable qualitative
    dimension in that pillar (module docstring) -- so no tokens are spent
    asking about it.
    """
    pillar_texts = {
        "market": _pillar_observed_text(market),
        "team": _pillar_observed_text(team),
        "product": _pillar_observed_text(product),
        "execution": _pillar_observed_text(execution),
        "traction": _pillar_observed_text(traction),
    }

    if not any(pillar_texts.values()):
        return ()

    user_content = "\n\n".join(
        f"=== {name.upper()} EVIDENCE ===\n{text}" if text else f"=== {name.upper()} EVIDENCE ===\n(none)"
        for name, text in pillar_texts.items()
    )
    user_content += (
        "\n\nSchema fields per pillar: competitors (named_competitor, "
        "differentiator_named), customer_demand / customer_value "
        "(outcome_claim, named_customer), founder_experience "
        "(founder_role, experience_type: one of UNRELATED_DOMAIN/"
        "ADJACENT_DOMAIN/DIRECT_DOMAIN/REPEAT_FOUNDER/PRIOR_EXIT, "
        "prior_entity_name), founder_outcomes (prior_entity_name, "
        "outcome_type: one of ACQUIRED/IPO/SHUT_DOWN/STILL_OPERATING), "
        "capabilities (capability_label, shipped), contracts "
        "(contract_type: one of PAYING/PILOT/SIGNED_CONTRACT_UNPAID/"
        "FREEMIUM_ACTIVE, named_customer, renewal_evidence). Only Team "
        "evidence should populate founder_experience/founder_outcomes. "
        "Only Market evidence should populate competitors. Return JSON "
        "with top-level keys: market, team, product, execution, traction."
    )

    raw = call_analysis_model(_SYSTEM_MESSAGE, user_content, temperature=0.0)
    parsed = parse_json_from_response(raw)

    # Parsed per-pillar rather than as one _ExtractionResult(**parsed)
    # call: a single malformed claim (an unexpected null, an out-of-enum
    # string) anywhere in the model's response must not discard every
    # OTHER pillar's otherwise-valid, correctly-grounded claims. Each
    # pillar that fails to validate degrades to an empty _PillarExtraction
    # (equivalent to "no claims for this pillar"), never a crash and
    # never a fabricated fallback value.
    observations: list[EvidenceBase] = []
    for pillar_key in ("market", "team", "product", "execution", "traction"):
        pillar_raw = parsed.get(pillar_key) or {}
        try:
            pillar_extraction = _PillarExtraction(**pillar_raw)
        except Exception:
            continue
        observations.extend(
            _extraction_to_observations(pillar_key, pillar_extraction, pillar_texts[pillar_key], f"{id_seed}-{pillar_key}")
        )

    return tuple(observations)


# The engine's ConfidenceLevel enum values are upper-case ("LOW",
# "MEDIUM", "HIGH", app/ai/sps_v3_engine/types.py); every other
# confidence field in this codebase (app/models/scoring.py's
# ConfidenceLevel, app/models/sps_v3.py's SPSV3ConfidenceLevel) uses
# title case ("Low", "Medium", "High"). This maps engine output to the
# codebase-wide convention -- never the other way around.
_CONFIDENCE_TO_TITLE_CASE = {"LOW": "Low", "MEDIUM": "Medium", "HIGH": "High"}


def _pillar_result_to_model(result) -> SPSV3PillarResult:
    return SPSV3PillarResult(
        pillar=result.pillar,
        strength=(float(result.strength) if result.strength is not None else None),
        coverage_pct=float(result.completeness_pct),
        confidence=_CONFIDENCE_TO_TITLE_CASE[result.confidence.value],
        publishable=result.publishable,
        withhold_reason=result.withhold_reason,
    )


def compute_sps_v3_assessment(
    methodology: SIEMethodologyAnalysis,
    id_seed: str,
) -> SPSV3Assessment | None:
    """
    Entry point called from run_due_diligence() (only when
    sps_v3_enabled() is True). Takes the SIEMethodologyAnalysis V2.1 has
    ALREADY fully computed (market/team/product/execution/traction
    PillarAnalysis objects) and produces the additive sps_v3 field.
    Returns None (never raises) on any classification-call failure --
    Part 8's "if it doesn't support even LIMITED, return INSUFFICIENT" is
    honored by the deterministic engine itself when there is simply no
    evidence; a failed/unparseable LLM call is a different case (adapter
    unavailable, not "no evidence") and degrades to the analysis simply
    having no sps_v3 at all, exactly like an analysis run before this
    field existed -- never a fabricated INSUFFICIENT result standing in
    for an error.
    """
    stage = map_stage(methodology.context.company_stage or methodology.context.funding_stage)

    try:
        observations = classify_evidence_for_v3(
            methodology.market,
            methodology.team,
            methodology.product,
            methodology.execution,
            methodology.traction,
            id_seed=id_seed,
        )
    except Exception:
        return None

    bundle = EvidenceBundle(company_id=id_seed, stage=stage, evidence=observations)

    dimension_results = evaluate_all_dimensions(bundle, DEFAULT_REGISTRY)
    sps_result = evaluate_sps(dimension_results, stage, DEFAULT_REGISTRY)
    ux_state = classify_ux_state(sps_result)

    return SPSV3Assessment(
        engine_version=SPS_V3_ENGINE_VERSION,
        scoring_version=SPS_V3_SCORING_VERSION,
        overall_score=(float(sps_result.sps) if sps_result.sps is not None else None),
        coverage_pct=float(sps_result.coverage.overall_pct),
        confidence=_CONFIDENCE_TO_TITLE_CASE[sps_result.confidence.overall.value],
        assessment_state=ux_state.lower(),
        withhold_reason=sps_result.withhold_reason,
        pillars={p.pillar: _pillar_result_to_model(p) for p in sps_result.pillar_results},
        computed_at=datetime.now(timezone.utc).isoformat(),
    )
