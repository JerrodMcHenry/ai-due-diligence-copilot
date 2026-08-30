"""
SIE Methodology v2 — canonical configuration.

Single source of truth for the frozen v2 dimension architecture: which 28
dimensions exist, which pillar each belongs to, its within-pillar weight,
its scoring mode, and its anchor status. Nothing else in the codebase should
hold its own copy of this information (Phase 2 of the v2 implementation).

Source of truth: app/docs/SIE_Methodology_v2_Specification.md, frozen at
commit 438d17c. This module implements that document; it does not extend or
reinterpret it. Anything marked CALIBRATION_REQUIRED here has no numeric
anchor anywhere -- that is a direct statement from the spec itself (Part 11),
not an omission.

Frozen/provisional anchor status is drawn from the completed calibration
program (app/calibration/v2/{calibration_rerun,freeze_sprint}/), never
invented here. See ANCHOR_REGISTRY below for exact provenance per anchor.
"""

from dataclasses import dataclass, field
from enum import Enum


# Methodology V2.1 (Phase 10.8B, 2026-08-29): bumped from v2-spec-2026-08-23
# after Phase 10.8's real-company blind validation
# (docs/validation/SPS_REAL_COMPANY_VALIDATION_REPORT.md) and Phase 10.8A's
# discrimination audit (docs/validation/SPS_DISCRIMINATION_AUDIT.md) found
# concrete, code-level correctness and discrimination defects -- see
# docs/validation/SPS_METHODOLOGY_V2_1_CHANGELOG.md for the full list of
# what changed and why. The 28-dimension architecture itself (which
# dimensions exist, their pillar/weight/scoring-mode) is UNCHANGED; this
# version bump reflects anchor-band, inference-rule, evidence-provenance,
# and research-input changes, not a new dimension set. Analyses produced
# under v2-spec-2026-08-23 are historical V2 output and are never rewritten
# to this version -- analysis_context.methodology_version is stamped at
# analysis time and read back from storage for every existing record.
METHODOLOGY_VERSION = "v2.1-spec-2026-08-29"
CANONICAL_SPEC_PATH = "app/docs/SIE_Methodology_v2_Specification.md"
CALIBRATION_CONTRACT_VERSION = "v2-calibration-rerun-2026-08-23"

# Anchor registry version -- bump this if the FROZEN/PROVISIONAL anchor set
# below changes, independent of the methodology_version (dimension
# architecture) itself changing. Lets provenance distinguish "same 28
# dimensions, refined anchor" from "different dimension set entirely".
# Bumped for V2.1's Team/Execution anchor-band rewrite (Phase 10.8B, Parts
# 6/8/9) and the confidence-score-cap mechanism (Part 11).
ANCHOR_REGISTRY_VERSION = "v2.1-anchor-registry-2026-08-29"


class ScoringMode(str, Enum):
    DETERMINISTIC = "Deterministic"
    HYBRID = "Hybrid"
    CONSTRAINED_LLM = "Constrained LLM"


class AnchorStatus(str, Enum):
    FROZEN = "FROZEN"
    FROZEN_PROVISIONAL = "FROZEN_AS_PROVISIONAL"
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"


# Unchanged from v1 -- out of scope for this specification (spec header,
# Part 3). Re-exported here so this module is a complete, self-contained
# picture of the v2 architecture; app/ai/scoring_methodology.py remains the
# single place the *value* is actually defined to avoid a second copy.
PILLAR_WEIGHTS: dict[str, float] = {
    "market": 0.20,
    "team": 0.20,
    "product": 0.20,
    "execution": 0.15,
    "traction": 0.15,
    "financial_health": 0.10,
}


@dataclass(frozen=True)
class DimensionSpecV2:
    name: str
    pillar: str  # matches SCORING_METHODOLOGY's pillar keys ("Market", "Team", ...)
    weight: float  # within-pillar weight
    mode: ScoringMode
    anchor_status: AnchorStatus
    evidence_requirement: str  # "Public" | "Inferred" | "Private" (existing v1 vocabulary, unchanged)
    notes: str = ""


# ---------------------------------------------------------------------------
# The 28 scored dimensions (spec Part 2, Part 7, Part 8).
# ---------------------------------------------------------------------------

DIMENSIONS: list[DimensionSpecV2] = [
    # Market (.20) -- weights/names unchanged from v1
    DimensionSpecV2("Market Size", "Market", 0.25, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Public"),
    DimensionSpecV2("Market Growth", "Market", 0.20, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Public"),
    DimensionSpecV2("Market Timing", "Market", 0.20, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Public"),
    DimensionSpecV2("Competitive Intensity", "Market", 0.15, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Public"),
    DimensionSpecV2(
        "Customer Demand", "Market", 0.20, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred",
        notes="Narrowed v2 scope: pre-revenue/pre-Traction demand signal only. Lifecycle: "
              "Pre-Seed Expected, Seed Expected-until-superseded, Series A+ Not Applicable "
              "once realized Traction supersedes it -- by actual maturity, not round label.",
    ),

    # Team (.20) -- unchanged from v1
    DimensionSpecV2("Founder-Market Fit", "Team", 0.25, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Public"),
    DimensionSpecV2("Technical Capability", "Team", 0.20, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),
    DimensionSpecV2("Business Capability", "Team", 0.20, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),
    DimensionSpecV2("Leadership", "Team", 0.20, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),
    DimensionSpecV2("Execution Track Record", "Team", 0.15, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),

    # Product (.20) -- unchanged from v1
    DimensionSpecV2("Customer Value", "Product", 0.25, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),
    DimensionSpecV2("Differentiation", "Product", 0.20, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Public"),
    DimensionSpecV2("Usability", "Product", 0.15, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Public"),
    DimensionSpecV2("Defensibility", "Product", 0.20, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),
    DimensionSpecV2("Adoption Potential", "Product", 0.20, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),

    # Execution (.15) -- reweighted .25 each, Execution Velocity removed
    DimensionSpecV2(
        "Go-to-Market Execution", "Execution", 0.25, ScoringMode.HYBRID, AnchorStatus.FROZEN_PROVISIONAL, "Inferred",
        notes="CAC payback <12mo = excellent (FROZEN, partial -- existing production benchmark text).",
    ),
    DimensionSpecV2("Product Execution", "Execution", 0.25, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred",
                     notes="Roadmap-velocity evidence item absorbed from the removed Execution Velocity dimension."),
    DimensionSpecV2("Operational Execution", "Execution", 0.25, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Private"),
    DimensionSpecV2("Strategic Execution", "Execution", 0.25, ScoringMode.CONSTRAINED_LLM, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),

    # Traction (.15) -- Commercial Validation removed, Growth Velocity added
    DimensionSpecV2("Customer Growth", "Traction", 0.15, ScoringMode.DETERMINISTIC, AnchorStatus.FROZEN_PROVISIONAL, "Public",
                     notes="Growth-conversion architecture FROZEN (calibration program); exact scale-tier cutoffs FROZEN AS PROVISIONAL."),
    DimensionSpecV2("Revenue Growth", "Traction", 0.25, ScoringMode.DETERMINISTIC, AnchorStatus.FROZEN_PROVISIONAL, "Public",
                     notes="Same architecture as Customer Growth; same-metric-confirmed-actual rule enforced."),
    DimensionSpecV2("Retention", "Traction", 0.25, ScoringMode.DETERMINISTIC, AnchorStatus.FROZEN, "Public",
                     notes="Best-anchored dimension in the methodology: NRR>130%=9-10, GRR>90%=strong, logo churn<1.5%/mo=strong."),
    DimensionSpecV2("Engagement", "Traction", 0.15, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),
    DimensionSpecV2(
        "Growth Velocity", "Traction", 0.20, ScoringMode.DETERMINISTIC, AnchorStatus.FROZEN_PROVISIONAL, "Public",
        notes="New in v2 (relocated/redefined from the removed Execution Velocity). Materiality-floor -> "
              "annualized-CAGR -> scale-tiered-band architecture FROZEN; exact scale-tier cutoffs FROZEN AS "
              "PROVISIONAL. N/A (not scored) for pre-revenue companies or below the materiality floor.",
    ),

    # Financial Health (.10) -- Fundraising Readiness removed (unscored flag), reweighted
    DimensionSpecV2("Revenue Quality", "Financial Health", 0.20, ScoringMode.HYBRID, AnchorStatus.CALIBRATION_REQUIRED, "Inferred"),
    DimensionSpecV2(
        "Unit Economics", "Financial Health", 0.25, ScoringMode.DETERMINISTIC, AnchorStatus.FROZEN_PROVISIONAL, "Private",
        notes="Business-model-agnostic (6 evidence families). SaaS family anchors FROZEN "
              "(margin>80%, payback<12mo, LTV:CAC>3x). Other 5 families: CALIBRATION_REQUIRED numerically; "
              "family-selection logic and 2 families' withholding rules are FROZEN, others FROZEN AS PROVISIONAL.",
    ),
    DimensionSpecV2(
        "Burn Efficiency", "Financial Health", 0.25, ScoringMode.HYBRID, AnchorStatus.FROZEN_PROVISIONAL, "Private",
        notes="Deterministic->Hybrid. Quantitative burn-multiple path CALIBRATION_REQUIRED (unused in calibration). "
              "Qualitative 5-band architecture FROZEN; exact score-within-band FROZEN AS PROVISIONAL. Must not become Runway.",
    ),
    DimensionSpecV2(
        "Runway", "Financial Health", 0.30, ScoringMode.HYBRID, AnchorStatus.FROZEN, "Public",
        notes="Deterministic->Hybrid. Linear quantitative bands FROZEN (18mo=healthy, 24mo=strong, <6mo=critical). "
              "Qualitative 6-band architecture FROZEN; exact score-within-band FROZEN AS PROVISIONAL. "
              "Non-linear runway-floor pillar cap: structural rule FROZEN, exact threshold CALIBRATION_REQUIRED. "
              "Absence of public cash data is never itself grounds to infer distress.",
    ),
]

assert len(DIMENSIONS) == 28, f"v2 dimension architecture must total 28, got {len(DIMENSIONS)}"
assert sum(1 for d in DIMENSIONS if d.mode == ScoringMode.DETERMINISTIC) == 5
assert sum(1 for d in DIMENSIONS if d.mode == ScoringMode.HYBRID) == 15
assert sum(1 for d in DIMENSIONS if d.mode == ScoringMode.CONSTRAINED_LLM) == 8

for _pillar in ("Market", "Team", "Product", "Execution", "Traction", "Financial Health"):
    _pillar_dims = [d for d in DIMENSIONS if d.pillar == _pillar]
    _total = round(sum(d.weight for d in _pillar_dims), 6)
    assert _total == 1.0, f"{_pillar} weights sum to {_total}, not 1.0"

# Unscored narrative flags (spec Part 2): not scored dimensions, never enter
# aggregation, kept only as free-text profile flags.
UNSCORED_NARRATIVE_FLAGS = ["Fundraising Readiness"]

# Explicitly removed, not replaced, not carried forward in any form:
REMOVED_DIMENSIONS = ["Commercial Validation", "Execution Velocity"]


def dimensions_for_pillar(pillar: str) -> list[DimensionSpecV2]:
    return [d for d in DIMENSIONS if d.pillar == pillar]


def get_dimension(name: str) -> DimensionSpecV2 | None:
    for d in DIMENSIONS:
        if d.name == name:
            return d
    return None


def dimension_weights(pillar: str) -> list[tuple[str, float]]:
    """Return (name, weight) tuples for a pillar -- the shape scoring.py's
    get_scoring_dimensions() already returns, so callers don't need to change."""
    return [(d.name, d.weight) for d in dimensions_for_pillar(pillar)]


def deterministic_dimension_names() -> set[str]:
    return {d.name for d in DIMENSIONS if d.mode == ScoringMode.DETERMINISTIC}


# ---------------------------------------------------------------------------
# Frozen / provisional anchor registry -- provenance only, mirrors the
# dimension-level anchor_status above but stated once as a flat, human-
# readable list matching app/calibration/freeze_manifest.json exactly, so a
# reviewer can cross-check code against the calibration program's own
# closing artifact without re-deriving anything.
# ---------------------------------------------------------------------------

FROZEN_ANCHORS = [
    "Growth Velocity / Customer Growth conversion architecture "
    "(materiality floor -> annualized CAGR -> scale-tiered bands, incl. short-window dampening)",
    "Qualitative Burn Efficiency band architecture (5-tier)",
    "Qualitative Runway band architecture (6-tier)",
    "Marketplace Unit Economics: take-rate-alone-insufficient withholding rule",
    "Commerce/DTC Unit Economics: thesis-is-not-outcome withholding rule",
    "Retention anchors (NRR>130%=9-10, GRR>90%=strong, logo churn<1.5%/mo=strong)",
    "Runway linear quantitative bands (18mo=healthy, 24mo=strong, <6mo=critical)",
    "Unit Economics SaaS-family anchors (margin>80%, payback<12mo, LTV:CAC>3x)",
]

FROZEN_AS_PROVISIONAL_ANCHORS = [
    "Growth Velocity / Customer Growth exact scale-tier absolute cutoffs",
    "Insurance Unit Economics qualitative-disclosure threshold",
    "Commerce/DTC and hardware Unit Economics insufficient-combination withholding rules",
    "Qualitative Burn Efficiency / Runway exact score-within-band placement",
    "Marketplace Unit Economics / Customer Growth family-selection logic",
]

REJECTED_ANCHORS: list[str] = []  # none, per the freeze sprint's final audit

# Explicitly still CALIBRATION_REQUIRED with no anchor of any kind (Part 11) --
# implementers must not invent a number for these; see the gap analysis doc.
CALIBRATION_REQUIRED_NO_ANCHOR = [
    "Non-SaaS Unit Economics numeric thresholds (marketplace take-rate %, insurance loss/combined "
    "ratio, hardware per-unit margin, R&D-partnership program economics) -- family definitions exist, numbers do not",
    "Burn Efficiency deterministic burn-multiple threshold",
    "Partial Structural Coverage triggering threshold",
    "SPS-suppression coverage floor",
    "Ranking-tier count and boundaries",
    "Runway non-linear floor-cap exact threshold",
]
