"""
SIE Methodology v2 -- deterministic/hybrid anchor functions.

Real Python implementations of the FROZEN and FROZEN_AS_PROVISIONAL anchors
from the completed calibration program. Nothing here invents a threshold:
every constant traces to app/calibration/v2/anchor_calibration/phase1/
ANCHOR_DESIGN.md or app/calibration/v2/freeze_sprint/ (see the docstring on
each function). Anything the calibration program left CALIBRATION_REQUIRED
with no anchor at all (non-SaaS Unit Economics numbers, the Burn Efficiency
deterministic burn-multiple threshold, the Runway floor-cap exact threshold)
is NOT implemented as a number here -- calling code must return Unavailable /
CALIBRATION_ANCHOR_REQUIRED for those cases, per Phase 5's explicit
"stop and report, do not improvise" instruction.

All functions are pure and side-effect-free: given identical inputs they
return identical outputs (Part 12's reproducibility contract for
Deterministic dimensions), and never make a network or LLM call.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
import math


class AnchorResult(str, Enum):
    """Every deterministic/anchor function returns one of these outcomes,
    never a bare number with no explanation of why -- Part 6's "never a
    stand-in for absence" rule applies to code, not just prompts."""

    SCORED = "scored"
    NOT_APPLICABLE = "not_applicable"           # structurally excluded (e.g. below materiality floor)
    CALIBRATION_ANCHOR_REQUIRED = "calibration_anchor_required"  # real evidence, no anchor exists
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # inputs don't clear the evidence bar at all


@dataclass(frozen=True)
class AnchorScore:
    result: AnchorResult
    score: float | None = None
    confidence: str | None = None  # "Low" | "Medium" | "High" | a hyphenated variant
    band: str | None = None
    rationale: str = ""


# ---------------------------------------------------------------------------
# Part 1/2/3 -- Growth Velocity / Customer Growth / Revenue Growth
# Source: app/calibration/v2/anchor_calibration/phase1/ANCHOR_DESIGN.md Parts 1-3,
# validated against 4 real companies in the freeze sprint (FROZEN architecture;
# exact scale-tier cutoffs FROZEN AS PROVISIONAL).
# ---------------------------------------------------------------------------

# Scale tiers are illustrative/provisional (freeze sprint only tested the
# SMB-SaaS/platform, commerce/DTC, and hardware families at "large" scale).
# Keyed by a coarse business-model family; "default" covers any family not
# explicitly tested, using the same shape but the widest (most conservative)
# floor, since an untested family's true floor is unknown.
SCALE_TIER_FLOORS: dict[str, float] = {
    "enterprise_saas": 10,       # logos
    "smb_saas_platform": 500,    # customers/merchants
    "consumer": 10_000,          # users
    "marketplace": 10_000,       # demand-side participants
    "commerce_dtc": 1_000,       # units/buyers
    "insurance": 1_000,          # policies
    "hardware": 50,              # units, high-ticket default; low-ticket categories need a higher floor
    "deeptech_partnership": None,  # customer/unit count is often the wrong unit entirely -- see note below
    "default": 1_000,
}

# CAGR bands by scale tier (Part 1 of ANCHOR_DESIGN.md): (weak_max, credible_max, strong_max)
# -- above strong_max is Exceptional (8-10); below weak_max is Weak (3-4); the gap between
# weak_max and credible_max is Credible (5); between credible_max and strong_max is Strong (6-7).
# Tier 1 = near-floor, Tier 4 = large/at-scale, applied by relative distance above the floor.
_CAGR_BAND_TIERS = [
    # (multiple_of_floor_upper_bound, weak_max, credible_max, strong_max)
    (2.0, 0.50, 1.50, 4.00),     # Tier 1: within 2x the floor
    (10.0, 0.35, 1.00, 2.50),    # Tier 2: 2x-10x the floor
    (100.0, 0.20, 0.60, 1.50),   # Tier 3: 10x-100x the floor
    (math.inf, 0.15, 0.40, 1.00),  # Tier 4: 100x+ the floor
]


def _scale_tier_bands(start_value: float, floor: float) -> tuple[float, float, float]:
    ratio = start_value / floor if floor else math.inf
    for upper, weak_max, credible_max, strong_max in _CAGR_BAND_TIERS:
        if ratio <= upper:
            return weak_max, credible_max, strong_max
    return _CAGR_BAND_TIERS[-1][1:]


_BAND_ORDER = ["Weak", "Credible", "Strong", "Exceptional"]
_BAND_SCORE = {"Weak": 3.5, "Credible": 5.0, "Strong": 6.5, "Exceptional": 8.5}


def _cagr_to_band(cagr: float, weak_max: float, credible_max: float, strong_max: float) -> str:
    if cagr < 0 or cagr < weak_max:
        return "Weak"
    if cagr < credible_max:
        return "Credible"
    if cagr < strong_max:
        return "Strong"
    return "Exceptional"


def _cagr_to_score(cagr: float, weak_max: float, credible_max: float, strong_max: float) -> tuple[float, str]:
    band = _cagr_to_band(cagr, weak_max, credible_max, strong_max)
    return (2.0 if cagr < 0 else _BAND_SCORE[band]), band


def score_growth_metric(
    start_value: float,
    end_value: float,
    window_years: float,
    business_model_family: str = "default",
    metric_confirmed_actual: bool = True,
) -> AnchorScore:
    """
    Growth Velocity's engine (and Revenue Growth's, which shares the same
    FROZEN conversion-function gap per spec Part 7). Implements: materiality-
    floor gate -> annualized CAGR -> scale-tiered bands -> short-window
    dampening. This answers Growth Velocity's specific question -- "how
    quickly is this expanding, once the rate is normalized for scale and
    time" -- which is why it requires a reliable window_years to annualize
    and dampens hard when that window is too short to trust. See
    ANCHOR_DESIGN.md Part 1 for the full design and the four real companies
    (Shopify, Dollar Shave Club, Peloton, Lemonade) it was validated against
    in the freeze sprint. NOT used for Customer Growth -- see
    score_customer_growth() below for that dimension's distinct contract
    (Blocker 2 fix, post-implementation review).
    """
    if not metric_confirmed_actual:
        return AnchorScore(
            AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
            rationale="One or both comparison points is a projection/guidance figure, not a confirmed "
                      "actual. Pairing a confirmed actual with a projection is explicitly disallowed "
                      "(same-metric-confirmed-actual rule, validated against the Etsy/Peloton/Zenefits "
                      "precedent) -- withheld rather than computed from mismatched inputs.",
        )

    if start_value <= 0 or end_value <= 0 or window_years <= 0:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale="Non-positive start/end value or non-positive window -- cannot compute a rate.",
        )

    floor = SCALE_TIER_FLOORS.get(business_model_family, SCALE_TIER_FLOORS["default"])
    if floor is None:
        return AnchorScore(
            AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
            rationale=f"'{business_model_family}' business-model family: customer/unit count is often "
                      f"the wrong unit for this family (deeptech/partnership) -- program count or "
                      f"contract value would be the appropriate unit, not implemented as a numeric anchor here.",
        )

    if start_value < floor:
        return AnchorScore(
            AnchorResult.NOT_APPLICABLE,
            rationale=f"Starting value ({start_value}) is below the materiality floor ({floor}) for the "
                      f"'{business_model_family}' family -- growth from an economically meaningless base "
                      f"is structurally excluded, not scored, per Part 1's explicit design goal.",
        )

    cagr = (end_value / start_value) ** (1.0 / window_years) - 1.0
    weak_max, credible_max, strong_max = _scale_tier_bands(start_value, floor)
    raw_score, band = _cagr_to_score(cagr, weak_max, credible_max, strong_max)

    confidence = "Medium"
    rationale_extra = ""
    if window_years <= 0.6:
        # Short-window dampening (validated against the Lemonade case in the
        # freeze sprint, an ~0.55-year window): do not report a literal,
        # wildly-extrapolated CAGR from a sub-2-quarter window at face value.
        # Threshold set at 0.6 (not a strict 0.5) so a "right at the boundary"
        # ~6-7 month window -- Lemonade's actual case -- is still caught.
        # Downgrade by one band (not a flat score cap) so a short-window
        # reading never scores higher than the same ratio measured over a
        # longer, more trustworthy window would -- capping at a fixed number
        # can otherwise invert that ordering when the honest longer-window
        # band is itself high.
        band_index = _BAND_ORDER.index(band)
        band = _BAND_ORDER[max(0, band_index - 1)]
        raw_score = _BAND_SCORE[band]
        confidence = "Low"
        rationale_extra = (
            f" Window is {window_years:.2f} years (<=0.6), at or below the ~2-quarter minimum for a "
            f"trustworthy annualized rate -- literal CAGR ({cagr:.1%}) dampened one band (to {band}) "
            f"rather than reported at face value, per the short-window caution rule."
        )

    return AnchorScore(
        AnchorResult.SCORED,
        score=round(raw_score, 1),
        confidence=confidence,
        band=band,
        rationale=(
            f"{start_value} -> {end_value} over {window_years:.2f} years (annualized CAGR {cagr:.1%}), "
            f"scale tier relative to a {floor} floor for '{business_model_family}' -> {band} band."
            f"{rationale_extra}"
        ),
    )


# Achieved-multiple bands for Customer Growth (Blocker 2 fix, post-
# implementation review): same scale-tier shape as _CAGR_BAND_TIERS above,
# but read as a straight end/start multiple rather than an annualized rate
# -- reusing the frozen materiality-floor architecture, not inventing a new
# one. A near-floor company needs a much larger multiple to read "Strong"
# than an at-scale company compounding off a huge base, exactly as with the
# rate-based bands.
_MULTIPLE_BAND_TIERS = [
    # (multiple_of_floor_upper_bound, weak_max, credible_max, strong_max)
    (2.0, 1.30, 2.00, 4.00),      # Tier 1: within 2x the floor
    (10.0, 1.20, 1.75, 3.00),     # Tier 2: 2x-10x the floor
    (100.0, 1.10, 1.40, 2.00),    # Tier 3: 10x-100x the floor
    (math.inf, 1.05, 1.25, 1.75),  # Tier 4: 100x+ the floor
]


def _multiple_tier_bands(start_value: float, floor: float) -> tuple[float, float, float]:
    ratio = start_value / floor if floor else math.inf
    for upper, weak_max, credible_max, strong_max in _MULTIPLE_BAND_TIERS:
        if ratio <= upper:
            return weak_max, credible_max, strong_max
    return _MULTIPLE_BAND_TIERS[-1][1:]


def _multiple_to_band(multiple: float, weak_max: float, credible_max: float, strong_max: float) -> str:
    if multiple < weak_max:
        return "Weak"
    if multiple < credible_max:
        return "Credible"
    if multiple < strong_max:
        return "Strong"
    return "Exceptional"


def score_customer_growth(
    start_value: float,
    end_value: float,
    window_years: float | None = None,
    business_model_family: str = "default",
    metric_confirmed_actual: bool = True,
) -> AnchorScore:
    """
    Customer Growth's own contract (Blocker 2 fix, post-implementation
    review) -- deliberately NOT score_growth_metric(). Growth Velocity asks
    "how quickly, once normalized for scale and time" and requires a
    reliable window to annualize; Customer Growth asks the more literal
    question spec Part 7 poses -- "how strongly is the customer/user/account
    base expanding" -- read from the ACHIEVED MULTIPLE (end_value /
    start_value) against the same business-model-aware materiality floor
    already frozen for the growth family (SCALE_TIER_FLOORS -- reused, not a
    new anchor), banded by how far above that floor the starting base
    already sits (same scale-tier architecture as Growth Velocity, applied
    to a multiple instead of an annualized rate).

    Because it is not annualizing, Customer Growth does not require a
    precise window_years the way Growth Velocity does -- window_years is
    optional here and, when supplied (or absent), only affects confidence,
    never withholds the score. This is the intentional asymmetry behind the
    required "one scoreable, one not" counterexample: a real multiple with a
    vague or missing time window can still support a Customer Growth read
    while the same input fails Growth Velocity's stricter annualization
    requirement (score_growth_metric() returns INSUFFICIENT_EVIDENCE for
    window_years <= 0).

    Grounded in the freeze sprint's own recorded judgments that Customer
    Growth and Growth Velocity legitimately diverge for the same company
    (e.g. Peloton: Customer Growth 8 vs. Growth Velocity 9; Lemonade:
    Customer Growth 8 vs. Growth Velocity 7 -- see
    app/calibration/v2/freeze_sprint/expansion_companies/*_scored.json). No
    new numeric anchor is introduced: the floor table and banding shape are
    the same frozen-as-provisional architecture already used by
    score_growth_metric(), re-read as a multiple rather than a rate.
    """
    if not metric_confirmed_actual:
        return AnchorScore(
            AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
            rationale="One or both comparison points is a projection/guidance figure, not a confirmed "
                      "actual -- withheld rather than computed from mismatched inputs (same rule as "
                      "Growth Velocity/Revenue Growth).",
        )

    if start_value <= 0 or end_value <= 0:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale="Non-positive start/end value -- cannot compute an achieved multiple.",
        )

    floor = SCALE_TIER_FLOORS.get(business_model_family, SCALE_TIER_FLOORS["default"])
    if floor is None:
        return AnchorScore(
            AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
            rationale=f"'{business_model_family}' business-model family: customer/unit count is often "
                      f"the wrong unit for this family (deeptech/partnership) -- not implemented as a "
                      f"numeric anchor here.",
        )

    if start_value < floor:
        return AnchorScore(
            AnchorResult.NOT_APPLICABLE,
            rationale=f"Starting value ({start_value}) is below the materiality floor ({floor}) for the "
                      f"'{business_model_family}' family -- growth from an economically meaningless base "
                      f"is structurally excluded, not scored (same materiality-floor rule as Growth Velocity).",
        )

    multiple = end_value / start_value
    weak_max, credible_max, strong_max = _multiple_tier_bands(start_value, floor)
    band = _multiple_to_band(multiple, weak_max, credible_max, strong_max)
    raw_score = _BAND_SCORE[band]

    confidence = "Medium"
    rationale_extra = ""
    if window_years is None:
        confidence = "Low"
        rationale_extra = (
            " No time window was supplied -- the achieved multiple can still be read on its own "
            "terms (Customer Growth is not a rate calculation), but confidence is lowered without "
            "a window to sanity-check it."
        )
    elif window_years <= 0.6 and multiple >= credible_max:
        # Customer Growth doesn't annualize, so a short window doesn't
        # invalidate the achieved multiple the way it would for Growth
        # Velocity's rate -- but a large multiple crammed into a very short
        # window is still worth flagging as lower-confidence rather than
        # silently trusted at face value.
        confidence = "Low"
        rationale_extra = (
            f" Window ({window_years:.2f} years) is short relative to the achieved multiple -- score "
            f"retained (Customer Growth is not a rate calculation) but confidence lowered."
        )

    return AnchorScore(
        AnchorResult.SCORED,
        score=round(raw_score, 1),
        confidence=confidence,
        band=band,
        rationale=(
            f"{start_value} -> {end_value} (achieved multiple {multiple:.2f}x), scale tier relative to "
            f"a {floor} floor for '{business_model_family}' -> {band} band.{rationale_extra}"
        ),
    )


# ---------------------------------------------------------------------------
# Part 4 -- Unit Economics business-model families
# Source: ANCHOR_DESIGN.md Part 4. SaaS anchors are the only FROZEN numeric
# thresholds; all others require real evidence to CLEAR a bar, never a
# number, per the frozen spec's own explicit scoping.
# ---------------------------------------------------------------------------

class UnitEconomicsFamily(str, Enum):
    SAAS_SUBSCRIPTION = "saas_subscription"
    MARKETPLACE = "marketplace"
    INSURANCE = "insurance"
    HARDWARE = "hardware"
    COMMERCE_DTC = "commerce_dtc"
    DEEPTECH_PARTNERSHIP = "deeptech_partnership"


def score_unit_economics_saas(
    gross_margin_pct: float | None,
    cac_payback_months: float | None,
    ltv_cac_ratio: float | None,
) -> AnchorScore:
    """FROZEN SaaS-family anchors only: margin>80%=excellent, payback<12mo=excellent,
    LTV:CAC>3x=strong. Never applied to any other family."""
    if gross_margin_pct is None and cac_payback_months is None and ltv_cac_ratio is None:
        return AnchorScore(AnchorResult.INSUFFICIENT_EVIDENCE, rationale="No SaaS unit-economics figures disclosed.")

    signals = []
    if gross_margin_pct is not None:
        signals.append(9.0 if gross_margin_pct > 80 else (6.5 if gross_margin_pct > 60 else 4.0))
    if cac_payback_months is not None:
        signals.append(9.0 if cac_payback_months < 12 else (6.5 if cac_payback_months < 18 else 3.5))
    if ltv_cac_ratio is not None:
        signals.append(7.5 if ltv_cac_ratio > 3 else (5.5 if ltv_cac_ratio > 2 else 3.0))

    score = round(sum(signals) / len(signals), 1)
    return AnchorScore(
        AnchorResult.SCORED, score=score, confidence="Medium-High", band="SaaS-family FROZEN anchor",
        rationale=f"SaaS anchors applied to {len(signals)} disclosed figure(s): margin={gross_margin_pct}, "
                  f"CAC payback={cac_payback_months}mo, LTV:CAC={ltv_cac_ratio}.",
    )


def score_unit_economics_non_saas(
    family: UnitEconomicsFamily,
    has_primary_metric: bool,
    has_supporting_signal: bool,
    is_generic_industry_commentary: bool = False,
) -> AnchorScore:
    """
    Non-SaaS families: NO numeric threshold is implemented (none is FROZEN
    or even FROZEN AS PROVISIONAL for any of these 5 families -- Part 11).
    This function implements only the WITHHOLDING logic that IS frozen:
    a lone primary metric with no supporting signal is insufficient
    (marketplace take-rate-alone, commerce/DTC thesis-not-outcome -- both
    FROZEN); generic industry-wide commentary never counts as company-specific
    evidence (validated against Shyp and DoorDash). Never returns SCORED with
    an invented threshold.
    """
    if is_generic_industry_commentary:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale=f"{family.value}: evidence is generic industry-wide commentary, not company-specific "
                      f"-- fails the company-specificity bar (Shyp/DoorDash precedent).",
        )
    if not has_primary_metric:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale=f"{family.value}: no primary metric evidence for this family.",
        )
    if not has_supporting_signal:
        return AnchorScore(
            AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
            rationale=f"{family.value}: a primary metric alone, with no supporting cost/sustainability "
                      f"signal, is insufficient by design (marketplace take-rate-alone / commerce-DTC "
                      f"thesis-not-outcome withholding rules, both FROZEN).",
        )
    return AnchorScore(
        AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
        rationale=f"{family.value}: primary metric and a supporting signal both present, but this "
                  f"family's numeric threshold is CALIBRATION_REQUIRED with no anchor of any kind "
                  f"(Part 11) -- real evidence exists, no number is invented for it here.",
    )


def score_unit_economics_from_structured_facts(structured_facts: dict) -> AnchorScore:
    """
    Family-detection + routing dispatcher for Unit Economics (Blocker 4 fix,
    post-implementation review). structured_facts["families"] is a list of
    per-family fact blocks -- usually one, but more than one when the
    evidence genuinely spans multiple business-model families (e.g. a
    fintech with both a SaaS software layer and an insurance-underwriting
    layer); per the requirement, a company is never arbitrarily forced into
    a single family when the methodology permits more than one relevant
    unit. Each family is scored ONLY through its own anchor function --
    score_unit_economics_saas() for "saas_subscription", never applied to
    any other family; score_unit_economics_non_saas() for every other
    family, which by Part 4's explicit scoping can only ever withhold
    (CALIBRATION_ANCHOR_REQUIRED / INSUFFICIENT_EVIDENCE), never SCORE. This
    means SaaS is the only family that can ever produce a numeric result --
    so when multiple families are present, the SaaS reading (if it scores)
    is used and every other family actually considered is still named in
    the rationale so nothing is silently dropped; there is no cross-family
    blending formula to invent, since no anchor for one exists.
    """
    families = structured_facts.get("families")
    if not families:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale="No business-model family was extracted for Unit Economics.",
        )

    per_family_results: list[tuple[str, AnchorScore]] = []
    for entry in families:
        family_value = entry.get("business_model_family") if isinstance(entry, dict) else None
        try:
            family = UnitEconomicsFamily(family_value)
        except ValueError:
            per_family_results.append((
                str(family_value),
                AnchorScore(
                    AnchorResult.INSUFFICIENT_EVIDENCE,
                    rationale=f"Unrecognized business_model_family '{family_value}'.",
                ),
            ))
            continue

        if family == UnitEconomicsFamily.SAAS_SUBSCRIPTION:
            result = score_unit_economics_saas(
                gross_margin_pct=entry.get("gross_margin_pct"),
                cac_payback_months=entry.get("cac_payback_months"),
                ltv_cac_ratio=entry.get("ltv_cac_ratio"),
            )
        else:
            result = score_unit_economics_non_saas(
                family=family,
                has_primary_metric=bool(entry.get("has_primary_metric", False)),
                has_supporting_signal=bool(entry.get("has_supporting_signal", False)),
                is_generic_industry_commentary=bool(entry.get("is_generic_industry_commentary", False)),
            )
        per_family_results.append((family.value, result))

    scored = [(name, r) for name, r in per_family_results if r.result == AnchorResult.SCORED]
    if scored:
        # Only the SaaS family can ever land here (non-SaaS families never
        # SCORE by design) -- take the first for determinism (Part 12).
        name, result = scored[0]
        other_names = [n for n, _ in per_family_results if n != name]
        extra = f" (other family evidence also considered: {', '.join(other_names)})" if other_names else ""
        return AnchorScore(
            AnchorResult.SCORED, score=result.score, confidence=result.confidence, band=result.band,
            rationale=f"[{name}]{extra} {result.rationale}",
        )

    # No family produced a numeric score -- report withheld, naming every
    # family actually considered so mixed-model evidence is never silently
    # collapsed into a single, unlabeled outcome.
    calibration_required = [(n, r) for n, r in per_family_results if r.result == AnchorResult.CALIBRATION_ANCHOR_REQUIRED]
    if calibration_required:
        names = ", ".join(n for n, _ in calibration_required)
        details = " | ".join(f"[{n}] {r.rationale}" for n, r in calibration_required)
        return AnchorScore(
            AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
            rationale=f"Evidence clears the withholding bar for {names}, but no FROZEN numeric anchor "
                      f"exists for that family (Part 4 scoping). {details}",
        )

    names = ", ".join(n for n, _ in per_family_results) or "none"
    details = " | ".join(f"[{n}] {r.rationale}" for n, r in per_family_results)
    return AnchorScore(
        AnchorResult.INSUFFICIENT_EVIDENCE,
        rationale=f"No considered family ({names}) cleared the evidence bar. {details}",
    )


# ---------------------------------------------------------------------------
# Part 5/6 -- Burn Efficiency / Runway qualitative bands
# Source: ANCHOR_DESIGN.md Parts 5-6. Band architecture FROZEN; exact
# within-band placement FROZEN AS PROVISIONAL (single-analyst judgment,
# reconfirmed but not independently cross-validated).
# ---------------------------------------------------------------------------

class QualitativeBand(str, Enum):
    CLEARLY_POOR = "clearly_poor"
    WEAK = "weak"
    CREDIBLE = "credible"
    STRONG = "strong"
    EXCEPTIONAL = "exceptional"


_BAND_MIDPOINT = {
    QualitativeBand.CLEARLY_POOR: 1.5,
    QualitativeBand.WEAK: 3.5,
    QualitativeBand.CREDIBLE: 5.0,
    QualitativeBand.STRONG: 6.5,
    QualitativeBand.EXCEPTIONAL: 9.0,
}


def score_burn_efficiency_qualitative(
    documented_crisis_requiring_emergency_financing_or_cuts: bool,
    explicit_nonhedged_spend_growing_faster_than_value: bool,
    explicit_signal_spend_matched_to_milestones: bool,
    disclosed_spend_control_or_efficiency_improvement: bool,
    disclosed_burn_multiple_below_1x_or_profitable_claim: bool,
    is_vague_or_hedged_narrative: bool = False,
) -> AnchorScore:
    """
    FROZEN 5-tier qualitative band architecture. Reconfirmed unchanged
    against Tesla (Clearly Poor) and Quibi (Weak) in the calibration rerun.
    Explicitly rejects vague/hedged narratives regardless of direction
    (validated symmetrically against Ginkgo/Jawbone/Meetup [vague negative]
    and Peloton [vague positive] in the freeze sprint).
    """
    if is_vague_or_hedged_narrative:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale="Evidence is vague/hedged (self-described as ambiguous, or a general narrative "
                      "with no direct, company-specific, non-hedged claim) -- does not clear the bar "
                      "for any qualitative band, regardless of whether it leans positive or negative.",
        )
    if documented_crisis_requiring_emergency_financing_or_cuts:
        band = QualitativeBand.CLEARLY_POOR
    elif explicit_nonhedged_spend_growing_faster_than_value:
        band = QualitativeBand.WEAK
    elif disclosed_burn_multiple_below_1x_or_profitable_claim:
        band = QualitativeBand.EXCEPTIONAL
    elif disclosed_spend_control_or_efficiency_improvement:
        band = QualitativeBand.STRONG
    elif explicit_signal_spend_matched_to_milestones:
        band = QualitativeBand.CREDIBLE
    else:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale="No qualifying evidence pattern found for any Burn Efficiency band.",
        )
    return AnchorScore(
        AnchorResult.SCORED, score=_BAND_MIDPOINT[band], confidence="Medium", band=band.value,
        rationale=f"Qualitative Burn Efficiency band: {band.value} (FROZEN architecture; exact "
                  f"within-band placement FROZEN AS PROVISIONAL).",
    )


def score_runway_qualitative(
    near_insolvency_unresolved_at_snapshot: bool,
    near_insolvency_just_addressed_by_fresh_capital: bool,
    direct_nonhedged_financing_inadequacy_claim: bool,
    direct_claim_financing_adequate_unremarkable: bool,
    committed_undrawn_credit_facility_disclosed: bool,
    quantified_reserves_relative_to_disclosed_burn_or_spend_plan: bool,
    is_large_raise_in_isolation_only: bool = False,
) -> AnchorScore:
    """
    FROZEN 6-tier qualitative band architecture. Explicitly rejects "large
    raise in isolation" as evidence of financial health (validated against
    Beepi, Jawbone, Quibi -- none qualified from raise size alone).
    """
    if is_large_raise_in_isolation_only:
        return AnchorScore(
            AnchorResult.INSUFFICIENT_EVIDENCE,
            rationale="Fundraising amount alone never implies financial health, by explicit design "
                      "(Beepi/Jawbone/Quibi precedent) -- withheld.",
        )
    if near_insolvency_unresolved_at_snapshot:
        return AnchorScore(AnchorResult.SCORED, score=1.0, confidence="High", band="clearly_poor_unresolved",
                            rationale="Documented near-insolvency, still unresolved as of the snapshot.")
    if near_insolvency_just_addressed_by_fresh_capital:
        return AnchorScore(AnchorResult.SCORED, score=2.0, confidence="Medium-High", band="clearly_poor_addressed",
                            rationale="Documented near-insolvency and emergency financing that closed at/near the "
                                      "snapshot; fragility demonstrated, resilience unproven (Tesla precedent).")
    if direct_nonhedged_financing_inadequacy_claim:
        return AnchorScore(AnchorResult.SCORED, score=3.5, confidence="Medium", band="weak",
                            rationale="Direct, non-hedged claim of financing inadequacy.")
    if quantified_reserves_relative_to_disclosed_burn_or_spend_plan:
        return AnchorScore(AnchorResult.SCORED, score=9.0, confidence="Medium", band="exceptional",
                            rationale="Quantified cash reserves explicitly disclosed as large relative to a "
                                      "known burn rate or spend plan (not a raise viewed in isolation).")
    if committed_undrawn_credit_facility_disclosed:
        return AnchorScore(AnchorResult.SCORED, score=7.0, confidence="Medium", band="strong",
                            rationale="Concrete, credible, committed access to capital beyond ordinary equity, "
                                      "not yet drawn (Stripe precedent).")
    if direct_claim_financing_adequate_unremarkable:
        return AnchorScore(AnchorResult.SCORED, score=5.0, confidence="Medium", band="credible",
                            rationale="Explicit, direct claim that financing position is adequate-but-unremarkable.")
    return AnchorScore(
        AnchorResult.INSUFFICIENT_EVIDENCE,
        rationale="No qualifying evidence pattern found for any Runway band. Absence of public cash data "
                  "is never itself grounds to infer distress.",
    )


# ---------------------------------------------------------------------------
# Retention -- FROZEN anchors, the best-anchored dimension in the methodology
# (spec Part 7): NRR>130%=9-10, GRR>90%=strong, logo churn<1.5%/mo=strong.
# ---------------------------------------------------------------------------

def score_retention(
    nrr_pct: float | None = None,
    grr_pct: float | None = None,
    monthly_logo_churn_pct: float | None = None,
) -> AnchorScore:
    if nrr_pct is None and grr_pct is None and monthly_logo_churn_pct is None:
        return AnchorScore(AnchorResult.INSUFFICIENT_EVIDENCE, rationale="No retention figures disclosed.")

    signals = []
    if nrr_pct is not None:
        signals.append(9.5 if nrr_pct > 130 else (7.0 if nrr_pct > 110 else (5.0 if nrr_pct >= 100 else 3.0)))
    if grr_pct is not None:
        signals.append(8.0 if grr_pct > 90 else (5.5 if grr_pct > 80 else 3.0))
    if monthly_logo_churn_pct is not None:
        signals.append(8.0 if monthly_logo_churn_pct < 1.5 else (5.0 if monthly_logo_churn_pct < 3.0 else 2.5))

    score = round(sum(signals) / len(signals), 1)
    return AnchorScore(
        AnchorResult.SCORED, score=score, confidence="Medium-High", band="FROZEN anchor",
        rationale=f"FROZEN Retention anchors applied to {len(signals)} disclosed figure(s): "
                  f"NRR={nrr_pct}, GRR={grr_pct}, monthly logo churn={monthly_logo_churn_pct}.",
    )


# ---------------------------------------------------------------------------
# Part 8 -- Customer Demand lifecycle resolver
# ---------------------------------------------------------------------------

class CustomerDemandLifecycleState(str, Enum):
    EXPECTED = "expected"
    EXPECTED_UNTIL_SUPERSEDED = "expected_until_superseded"
    NOT_APPLICABLE = "not_applicable"


def score_from_structured_facts(dimension_name: str, structured_facts: dict) -> AnchorScore:
    """
    Single entry point for the 5 Deterministic dimensions. Customer Growth
    has its OWN contract (score_customer_growth() -- achieved multiple, no
    required window) distinct from Revenue Growth and Growth Velocity
    (score_growth_metric() -- annualized, scale-tiered CAGR); this split is
    the Blocker 2 fix (post-implementation review) for the defect where all
    three previously routed through one shared engine and could never
    legitimately diverge. Retention has its own FROZEN anchors; Unit
    Economics has its own family-based anchors. Called from
    app/ai/analyze_pillar.py after the evidence-extraction stage returns a
    dimension's (LLM-extracted, Python-scored) structured_facts. Never
    called for any other dimension.
    """
    if dimension_name == "Customer Growth":
        try:
            window_years = structured_facts.get("window_years")
            return score_customer_growth(
                start_value=float(structured_facts["start_value"]),
                end_value=float(structured_facts["end_value"]),
                window_years=float(window_years) if window_years is not None else None,
                business_model_family=structured_facts.get("business_model_family", "default"),
                metric_confirmed_actual=bool(structured_facts.get("metric_confirmed_actual", True)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            return AnchorScore(
                AnchorResult.INSUFFICIENT_EVIDENCE,
                rationale=f"structured_facts present but malformed/incomplete ({exc}) -- withheld rather "
                          f"than guessing at a missing field.",
            )
    if dimension_name in ("Revenue Growth", "Growth Velocity"):
        try:
            return score_growth_metric(
                start_value=float(structured_facts["start_value"]),
                end_value=float(structured_facts["end_value"]),
                window_years=float(structured_facts["window_years"]),
                business_model_family=structured_facts.get("business_model_family", "default"),
                metric_confirmed_actual=bool(structured_facts.get("metric_confirmed_actual", True)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            return AnchorScore(
                AnchorResult.INSUFFICIENT_EVIDENCE,
                rationale=f"structured_facts present but malformed/incomplete ({exc}) -- withheld rather "
                          f"than guessing at a missing field.",
            )
    if dimension_name == "Retention":
        try:
            return score_retention(
                nrr_pct=structured_facts.get("nrr_pct"),
                grr_pct=structured_facts.get("grr_pct"),
                monthly_logo_churn_pct=structured_facts.get("monthly_logo_churn_pct"),
            )
        except (TypeError, ValueError) as exc:
            return AnchorScore(
                AnchorResult.INSUFFICIENT_EVIDENCE,
                rationale=f"structured_facts present but malformed ({exc}) -- withheld.",
            )
    if dimension_name == "Unit Economics":
        try:
            return score_unit_economics_from_structured_facts(structured_facts)
        except (TypeError, AttributeError, ValueError) as exc:
            return AnchorScore(
                AnchorResult.INSUFFICIENT_EVIDENCE,
                rationale=f"structured_facts present but malformed ({exc}) -- withheld rather than "
                          f"guessing at a missing/misshapen family entry.",
            )
    return AnchorScore(
        AnchorResult.CALIBRATION_ANCHOR_REQUIRED,
        rationale=f"'{dimension_name}' has no structured_facts-driven anchor implemented.",
    )


def resolve_customer_demand_applicability(
    financing_round_label: str,
    has_disclosed_customer_or_revenue_data: bool,
    is_single_market_or_pre_scale: bool,
    realized_traction_evidence_exists: bool,
) -> CustomerDemandLifecycleState:
    """
    Implements Part 8's maturity-based (not label-based) lifecycle rule,
    including the two-part 'genuinely early despite the label' test
    validated against Instacart, Warby Parker, and Ginkgo Bioworks in the
    targeted PASS A rerun: (1) no disclosed customer/revenue data AND
    (2) single-market/pre-scale => evaluate under the Seed rule even if the
    round label says otherwise.
    """
    label = financing_round_label.strip().lower()
    is_pre_seed = "pre-seed" in label or "pre seed" in label
    is_seed = label == "seed" or ("seed" in label and not is_pre_seed)

    genuinely_early_despite_label = (
        not has_disclosed_customer_or_revenue_data and is_single_market_or_pre_scale
    )

    if is_pre_seed:
        return CustomerDemandLifecycleState.EXPECTED

    if is_seed or genuinely_early_despite_label:
        if realized_traction_evidence_exists:
            return CustomerDemandLifecycleState.NOT_APPLICABLE
        return CustomerDemandLifecycleState.EXPECTED_UNTIL_SUPERSEDED

    # Series A+ by label, and genuinely mature by evidence.
    return CustomerDemandLifecycleState.NOT_APPLICABLE
