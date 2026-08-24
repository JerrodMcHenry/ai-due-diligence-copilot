"""
SIE Methodology v2 -- missing-evidence semantics (Part 4), Partial Structural
Coverage (Part 9 item 6), and Evidence Independence Metadata (freeze sprint,
Part 15 item 6 of the canonical spec).

Design decision (see app/docs/SIE_Methodology_v2_Implementation_Gap_Analysis.md):
implemented ADDITIVELY on top of the existing, working 3-state
(Observed/Inferred/Unavailable) pipeline rather than as a replacement. The
existing pipeline's ARITHMETIC treatment of "Unavailable" already matches
v2 exactly -- excluded from the scored set, no default substituted, which is
the one governing rule Part 4 states as absolute ("unknown must not become
weak"). What v2 adds beyond that is finer REPORTING granularity (which kind
of Unavailable, for diligence-flag severity) and two structural concepts
(stage-driven Not-Expected/Not-Applicable exclusion, and Partial Structural
Coverage) that do not exist in v1 at all. Both are added here as new,
optional fields/functions that a v1-shaped Subscore can simply not populate
without breaking anything that reads it.
"""

from dataclasses import dataclass
from enum import Enum


class MissingEvidenceState(str, Enum):
    """The nine canonical states (Part 4). Only meaningful when the
    underlying (existing) evidence_status is "Unavailable" -- a dimension
    that resolved to Observed/Inferred with a real score does not need one
    of these; SCORED_MIXED and SCORED_CONFLICTING_RESOLVED are the two
    exceptions (Mixed/resolved-Conflicting evidence, which DO carry a score
    but need the tension/verification flag preserved)."""

    NOT_EXPECTED_BY_STAGE = "not_expected_by_stage"
    NOT_APPLICABLE = "not_applicable"
    OPTIONAL_BUT_UNAVAILABLE = "optional_but_unavailable"
    USUALLY_PRIVATE_AND_UNAVAILABLE = "usually_private_and_unavailable"
    EXPECTED_BUT_UNAVAILABLE = "expected_but_unavailable"
    RESEARCH_FAILURE = "research_failure"
    EXPLICIT_MANAGEMENT_REFUSAL = "explicit_management_refusal"
    CONFLICTING_EVIDENCE_UNRESOLVED = "conflicting_evidence_unresolved"
    CONFLICTING_EVIDENCE_RESOLVED = "conflicting_evidence_resolved"  # scored, capped Low confidence
    MIXED_EVIDENCE = "mixed_evidence"  # scored, Medium-High confidence, never auto-Low


# States that are arithmetically identical -- excluded from the scored set,
# no default -- differing ONLY in diligence-flag severity (Part 4's
# "load-bearing resolution"). Both Usually-Private and Expected-But-
# Unavailable are here to make that identity explicit in code, not just prose.
EXCLUDED_FROM_SCORED_SET = {
    MissingEvidenceState.NOT_EXPECTED_BY_STAGE,
    MissingEvidenceState.NOT_APPLICABLE,
    MissingEvidenceState.OPTIONAL_BUT_UNAVAILABLE,
    MissingEvidenceState.USUALLY_PRIVATE_AND_UNAVAILABLE,
    MissingEvidenceState.EXPECTED_BUT_UNAVAILABLE,
    MissingEvidenceState.RESEARCH_FAILURE,
    MissingEvidenceState.EXPLICIT_MANAGEMENT_REFUSAL,
    MissingEvidenceState.CONFLICTING_EVIDENCE_UNRESOLVED,
}

# States that never enter the in-scope set at all (stage-gated out before
# evidence is even examined) -- distinct from "in-scope but excluded".
NEVER_IN_SCOPE = {
    MissingEvidenceState.NOT_EXPECTED_BY_STAGE,
    MissingEvidenceState.NOT_APPLICABLE,
}

DILIGENCE_FLAG_SEVERITY = {
    MissingEvidenceState.NOT_EXPECTED_BY_STAGE: "none",
    MissingEvidenceState.NOT_APPLICABLE: "none",
    MissingEvidenceState.OPTIONAL_BUT_UNAVAILABLE: "minimal",
    MissingEvidenceState.USUALLY_PRIVATE_AND_UNAVAILABLE: "standard",
    MissingEvidenceState.EXPECTED_BUT_UNAVAILABLE: "elevated",
    MissingEvidenceState.RESEARCH_FAILURE: "system_only",  # never company-facing
    MissingEvidenceState.EXPLICIT_MANAGEMENT_REFUSAL: "elevated_disclosure_risk",
    MissingEvidenceState.CONFLICTING_EVIDENCE_UNRESOLVED: "verification",
    MissingEvidenceState.CONFLICTING_EVIDENCE_RESOLVED: "verification",
    MissingEvidenceState.MIXED_EVIDENCE: "tension",
}


def classify_unavailable_dimension(
    evidence_requirement: str,  # "Public" | "Inferred" | "Private" (existing v1 vocabulary)
    stage_not_expected: bool,
    stage_not_applicable: bool,
    stage_optional: bool,
) -> MissingEvidenceState:
    """
    Maps an existing v1 "Unavailable" Subscore to one of the five
    Unavailable sub-states, using information the pipeline already has
    (evidence_requirement) plus stage-applicability flags a caller supplies
    from the per-dimension stage rules (Part 7). Does not require a new LLM
    call -- pure classification of already-known facts.
    """
    if stage_not_expected:
        return MissingEvidenceState.NOT_EXPECTED_BY_STAGE
    if stage_not_applicable:
        return MissingEvidenceState.NOT_APPLICABLE
    if stage_optional:
        return MissingEvidenceState.OPTIONAL_BUT_UNAVAILABLE
    if evidence_requirement == "Private":
        return MissingEvidenceState.USUALLY_PRIVATE_AND_UNAVAILABLE
    # Public/Inferred, in-scope, genuinely missing: this is the elevated case.
    return MissingEvidenceState.EXPECTED_BUT_UNAVAILABLE


# ---------------------------------------------------------------------------
# Partial Structural Coverage (Part 9, item 6)
# ---------------------------------------------------------------------------

# CALIBRATION_REQUIRED per Part 11 -- no threshold exists anywhere in the
# calibration program's own artifacts. Implemented at the most literal,
# non-invented reading of "whole pillar absent": any pillar with zero scored
# dimensions triggers the label. This is the floor of the possible range,
# not a tuned number -- flagged here and in the gap analysis doc as
# provisional pending a real threshold decision.
PSC_TRIGGER_MIN_UNAVAILABLE_PILLARS = 1


def compute_partial_structural_coverage(pillar_scores: dict[str, float | None]) -> dict:
    """
    pillar_scores: {"market": 6.5, "team": None, ...} -- None means that
    pillar had zero scored dimensions (already how v1's aggregation
    represents a fully-unavailable pillar; PSC is a purely additive display
    label layered on top, never a math change).
    """
    unavailable = [p for p, s in pillar_scores.items() if s is None]
    triggered = len(unavailable) >= PSC_TRIGGER_MIN_UNAVAILABLE_PILLARS
    return {
        "partial_structural_coverage": triggered,
        "pillars_unavailable_entirely": unavailable,
        "note": (
            "Display-layer label only. SPS math is unchanged and unpenalized; ranking eligibility is "
            "governed entirely separately (Part 10)."
            if triggered
            else ""
        ),
    }


# ---------------------------------------------------------------------------
# Evidence Independence Metadata (freeze sprint; Part 15 item 6 of the spec)
# ---------------------------------------------------------------------------
#
# Implemented at the metadata/provenance level only, per Phase 11's explicit
# instruction ("if straightforward, implement only the metadata structure...
# it must NOT modify SPS"). Evidence-event tagging at the LLM-prompt level
# (having the model itself emit a stable evidence_event_id per dimension) is
# NOT implemented -- that would require new prompt fields and new validation
# across all 28 dimensions, which is non-trivial within this phase's scope.
# What IS implemented: a post-hoc, pure-Python function that computes EIM
# fields given evidence_event_ids the CALLER supplies (e.g. from a future
# prompt change, or from manual/test annotation) -- the metadata contract
# itself, ready to be fed by a real tagging mechanism later. Left as
# documented v2.1 technical debt for the tagging half; reported honestly in
# the Phase 17 report, not silently skipped.


@dataclass(frozen=True)
class EIMDimension:
    name: str
    weight: float
    evidence_event_id: str | None  # None = no shared-event tag available


def compute_evidence_independence_metadata(scored_dimensions: list[EIMDimension]) -> dict:
    if not scored_dimensions:
        return {
            "effective_independent_dimensions": 0,
            "scored_dimension_count": 0,
            "concentration_ratio": 0.0,
            "independent_coverage_denominator_note": "no scored dimensions",
            "possible_semantic_duplication": False,
        }

    groups: dict[str, list[EIMDimension]] = {}
    singleton_count = 0
    for d in scored_dimensions:
        if d.evidence_event_id is None:
            singleton_count += 1
            continue
        groups.setdefault(d.evidence_event_id, []).append(d)

    effective_independent = singleton_count + len(groups)
    scored_count = len(scored_dimensions)
    concentration_ratio = round(1 - (effective_independent / scored_count), 3) if scored_count else 0.0

    # Semantic-duplication flag: 2+ dimensions sharing one event, all within
    # the same pillar, is the pattern PASS C found materially concentrating
    # (Zenefits' Product pillar, Shopify's Traction pillar) -- flagged, not
    # auto-resolved, per the freeze sprint's design.
    possible_duplication = any(len(members) >= 2 for members in groups.values())

    return {
        "effective_independent_dimensions": effective_independent,
        "scored_dimension_count": scored_count,
        "concentration_ratio": concentration_ratio,
        "shared_event_groups": {eid: [d.name for d in members] for eid, members in groups.items() if len(members) >= 2},
        "possible_semantic_duplication": possible_duplication,
    }
