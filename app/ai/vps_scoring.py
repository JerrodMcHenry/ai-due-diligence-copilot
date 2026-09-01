"""
Idea Lab / Venture Simulator V1 -- the Venture Potential Score (VPS)
deterministic scoring engine.

THIS IS NOT METHODOLOGY V3. VPS is architecturally separate from SIE
Methodology v2 / SPS (see app/ai/sie_v2_methodology.py, scoring.py,
scoring_methodology.py -- none of which this module imports or modifies).
VPS has NOT undergone the calibration/blind-holdout program SPS has; it is
explicitly a V1, uncalibrated, assumption-based model. It must never be
labeled, stored, or treated as SPS.

Design grounding (Phase 6 inspection of app/ai/scoring_methodology.py's
real 28 dimensions): Traction's five dimensions (Customer Growth, Revenue
Growth, Retention, Engagement, Growth Velocity) and Execution's four
(Go-to-Market/Product/Operational/Strategic Execution) all grade
DEMONSTRATED, observed history -- a pre-launch idea has none of this by
definition, so VPS does not reuse them as categories. Financial Health's
Unit Economics/Burn Efficiency require real operating data, not
projections, for the same reason. What DOES legitimately carry over is
the general shape of the methodology -- weighted categories, each
Unavailable-safe, renormalized when a category can't be scored -- applied
here as an independent, much simpler, uncalibrated model.

Every category function below reads ONLY its own namespaced slice of the
`assumptions` dict (see VentureAssumptions in app/models/idea_lab.py) --
this is what makes an irrelevant assumption change provably unable to
alter an unrelated category's score (Part 19 test 17), and what makes
identical inputs always produce identical output (Part 19 test 15): every
function here is a pure function of its inputs, no randomness, no LLM
call, no I/O.

Provenance is structural, not a per-field tag: everything under
assumptions["validation"] is a founder-REPORTED OBSERVATION (customer
interviews actually conducted, customers actually paying); every other
top-level group (market/problem_solution/founder/gtm/economics/capital)
is a MODELED ASSUMPTION by construction. See VentureAssumptions's own
docstring for why this is honest without needing a parallel per-field
metadata structure.
"""

from dataclasses import dataclass, field


VPS_LABEL = "MODELED / ASSUMPTION-BASED"

# Deliberately smaller and differently-named than SIE Methodology v2's six
# pillars -- see this module's own docstring for why Traction/Execution
# were excluded outright, and the Phase 6 design report for why Problem
# and Solution were merged into one category for V1 rather than split
# (they're highly correlated at idea stage and splitting them added
# complexity without a corresponding gain in defensibility this early).
VPS_CATEGORIES = [
    "market_potential",
    "problem_solution",
    "founder_readiness",
    "gtm_feasibility",
    "economic_potential",
    "validation",
]

VPS_CATEGORY_LABELS = {
    "market_potential": "Market Potential",
    "problem_solution": "Problem & Solution Strength",
    "founder_readiness": "Founder Readiness",
    "gtm_feasibility": "GTM Feasibility",
    "economic_potential": "Economic Potential",
    "validation": "Validation",
}

# Sums to 1.0. Validation is weighted meaningfully (not token-weighted)
# so a venture with zero real-world signal is honestly capped lower
# overall -- without being punitive: Part 4's "do not punish an idea
# simply for not already being Series A" is honored by renormalizing
# around Validation when it's Unavailable (a pure idea, see
# compute_vps() below), not by inflating it or excluding it from the
# rubric altogether.
VPS_CATEGORY_WEIGHTS = {
    "market_potential": 0.20,
    "problem_solution": 0.20,
    "founder_readiness": 0.15,
    "gtm_feasibility": 0.15,
    "economic_potential": 0.10,
    "validation": 0.20,
}


def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


@dataclass
class CategoryResult:
    key: str
    label: str
    # None means Unavailable -- not enough assumptions were provided to
    # responsibly score this category at all. Never defaulted to a
    # midpoint or to 0 -- an absent score is excluded from the weighted
    # average below and renormalized around, the same discipline
    # Methodology v2 uses for an Unavailable pillar.
    score: float | None
    basis: list[str] = field(default_factory=list)


def _score_market_potential(assumptions: dict) -> CategoryResult:
    market = assumptions.get("market") or {}
    size = market.get("estimated_market_size")
    intensity = market.get("competition_intensity")
    description = market.get("market_description")

    if size is None and intensity is None and not description:
        return CategoryResult("market_potential", VPS_CATEGORY_LABELS["market_potential"], None)

    basis = []
    score = 5.0

    size_points = {"Small": -1.5, "Medium": 0.0, "Large": 1.5, "Very Large": 2.5}
    if size in size_points:
        score += size_points[size]
        basis.append(f"Estimated market size: {size}")

    intensity_points = {"Low": 1.5, "Medium": 0.0, "High": -1.5}
    if intensity in intensity_points:
        score += intensity_points[intensity]
        basis.append(f"Assumed competitive intensity: {intensity}")

    if description and size is None and intensity is None:
        basis.append("Market description provided, but no size/competition assumption")

    return CategoryResult("market_potential", VPS_CATEGORY_LABELS["market_potential"], _clamp(score), basis)


def _score_problem_solution(assumptions: dict) -> CategoryResult:
    ps = assumptions.get("problem_solution") or {}
    problem = ps.get("problem_statement")
    solution = ps.get("solution_description")
    differentiation = ps.get("differentiation")
    target_customer = assumptions.get("target_customer")

    if not problem and not solution:
        return CategoryResult("problem_solution", VPS_CATEGORY_LABELS["problem_solution"], None)

    basis = []
    score = 5.0

    if problem and solution:
        # SIE Intelligence Reset: previously a basis note only, worth
        # zero points -- part of why this category's ceiling (7.5) fell
        # short of what a genuinely complete, well-articulated model
        # deserves. A real, if modest, completeness bonus.
        score += 0.5
        basis.append("Both a problem statement and a solution description are provided")
    elif problem:
        score -= 1.0
        basis.append("Problem stated, but no solution description yet")
    elif solution:
        score -= 1.0
        basis.append("Solution described, but the problem it solves isn't stated")

    if differentiation and len(differentiation.strip()) > 20:
        # SIE Intelligence Reset: a second tier for a genuinely
        # substantive differentiation (not just past the 20-character
        # floor) -- this dimension's own top evidence anchor. Confirmed
        # defect this fixes: the category's own mathematical ceiling
        # (7.5, unreachable past that regardless of evidence quality)
        # was one reason VPS's overall ceiling fell short of 9 even for
        # a maximally strong synthetic company across every other
        # category.
        if len(differentiation.strip()) > 80:
            score += 2.0
            basis.append("A specific, well-articulated differentiation is described")
        else:
            score += 1.5
            basis.append("A specific differentiation is described")

    if target_customer:
        score += 1.0
        basis.append("A target customer is named")

    return CategoryResult("problem_solution", VPS_CATEGORY_LABELS["problem_solution"], _clamp(score), basis)


def _score_founder_readiness(assumptions: dict) -> CategoryResult:
    founder = assumptions.get("founder") or {}
    count = founder.get("founder_count")
    years = founder.get("relevant_domain_experience_years")
    has_technical = founder.get("has_technical_cofounder")
    has_business = founder.get("has_business_cofounder")

    if count is None and years is None and has_technical is None and has_business is None:
        return CategoryResult("founder_readiness", VPS_CATEGORY_LABELS["founder_readiness"], None)

    # Starts below the neutral midpoint deliberately: absence of stated
    # founder background is not treated as average readiness, it's
    # treated as genuinely unknown-and-therefore-weaker until assumptions
    # say otherwise -- the same "don't fabricate a default" principle as
    # everywhere else, applied to the base rather than to a single field.
    basis = []
    score = 4.0

    if years is not None:
        contribution = min(max(years, 0) / 5.0, 1.0) * 3.0
        score += contribution
        basis.append(f"{years} years of stated relevant domain experience")

    if has_technical:
        score += 1.5
        basis.append("Technical cofounder present")

    if has_business:
        score += 1.5
        basis.append("Business/GTM cofounder present")

    if count is not None and count == 1 and not has_technical and not has_business:
        basis.append("Solo founder, no stated technical or business cofounder")

    return CategoryResult("founder_readiness", VPS_CATEGORY_LABELS["founder_readiness"], _clamp(score), basis)


def _score_gtm_feasibility(assumptions: dict) -> CategoryResult:
    gtm = assumptions.get("gtm") or {}
    strategy = gtm.get("primary_acquisition_strategy")
    cac = gtm.get("expected_cac")
    price_point = (assumptions.get("economics") or {}).get("price_point")

    if not strategy and cac is None:
        return CategoryResult("gtm_feasibility", VPS_CATEGORY_LABELS["gtm_feasibility"], None)

    basis = []
    score = 5.0

    if strategy:
        score += 1.0
        basis.append(f"Stated acquisition strategy: {strategy}")

    if cac is not None and price_point:
        ratio = price_point / cac if cac > 0 else 0
        if ratio > 3:
            score += 2.0
            basis.append("Assumed price point comfortably exceeds assumed CAC")
        elif ratio >= 1:
            score += 0.5
            basis.append("Assumed price point modestly exceeds assumed CAC")
        else:
            score -= 2.0
            basis.append("Assumed CAC exceeds the assumed price point")
    elif cac is not None:
        basis.append("CAC assumed, but no price point to check it against")

    return CategoryResult("gtm_feasibility", VPS_CATEGORY_LABELS["gtm_feasibility"], _clamp(score), basis)


def _score_economic_potential(assumptions: dict) -> CategoryResult:
    econ = assumptions.get("economics") or {}
    pricing_model = econ.get("pricing_model")
    price_point = econ.get("price_point")
    margin = econ.get("expected_gross_margin_pct")

    if not pricing_model and price_point is None and margin is None:
        return CategoryResult("economic_potential", VPS_CATEGORY_LABELS["economic_potential"], None)

    basis = []
    score = 5.0

    if margin is not None:
        if margin >= 70:
            score += 2.5
            basis.append(f"Assumed gross margin of {margin}%")
        elif margin >= 40:
            score += 1.0
            basis.append(f"Assumed gross margin of {margin}%")
        else:
            score -= 1.0
            basis.append(f"Assumed gross margin of {margin}% is thin for a venture-scale outcome")

    if pricing_model:
        score += 1.0
        basis.append(f"Pricing model: {pricing_model}")

    return CategoryResult("economic_potential", VPS_CATEGORY_LABELS["economic_potential"], _clamp(score), basis)


def _validation_commercial_scale(paying: float | None, revenue: float | None) -> float:
    """
    SIE Intelligence Reset. Deterministic 0-8 base from the two
    strongest, most reliably founder-reported commercial-validation
    facts: real paying customers and real reported revenue. Explicit
    evidence-anchor tiers (not a single early cap) so real dynamic
    range survives at scale -- the confirmed defect this replaces: the
    old formula capped ALL credit at 10 paying customers, making 186
    paying customers score identically to 10, and gave a single flat
    "+2" for ANY nonzero revenue, making $983K/mo indistinguishable
    from $12/year (the ApexGrid regression case's central bug).

    Tiers (paying customers / monthly revenue, either independently):
      absent            -> 0
      a few / early      -> 2.0   (1-2 customers, or <$1K/mo)
      early commercial   -> 3.0   (3-9 customers, or $1K-$10K/mo)
      solid base         -> 4.5   (10-49 customers, or $10K-$50K/mo)
      strong base        -> 5.5   (50-99 customers, or $50K-$250K/mo)
      large scale        -> 6.5   (100+ customers, or $250K+/mo) -- STRONG anchor
    Both present at "solid" tier or better adds +1.0: genuine paired
    commercial validation (people pay AND the business collects real
    money), not just the stronger signal counted once.
    """
    if not paying and not revenue:
        return 0.0

    score = 0.0

    if paying:
        if paying >= 100:
            score = max(score, 6.5)
        elif paying >= 50:
            score = max(score, 5.5)
        elif paying >= 10:
            score = max(score, 4.5)
        elif paying >= 3:
            score = max(score, 3.0)
        else:
            score = max(score, 2.0)

    if revenue:
        if revenue >= 250_000:
            score = max(score, 6.5)
        elif revenue >= 50_000:
            score = max(score, 5.5)
        elif revenue >= 10_000:
            score = max(score, 4.5)
        elif revenue >= 1_000:
            score = max(score, 3.0)
        else:
            score = max(score, 2.0)

    if paying and revenue and paying >= 10 and revenue >= 10_000:
        score += 1.0

    return min(score, 8.0)


def _validation_modifiers(
    revenue: float | None, prior_revenue: float | None, retention_pct: float | None
) -> tuple[float, list[str]]:
    """
    Growth and retention as EXPLICIT additive modifiers on top of the
    commercial-scale base above -- never a floor, never a penalty for
    being unstated (Rulebook: unknown information must not lower
    Strength). Only applies when the underlying facts are actually
    known; a declining revenue trend or weak retention are genuine
    NEGATIVE evidence and lower the score, which is different in kind
    from simply not having the fact at all.
    """
    modifier = 0.0
    basis: list[str] = []

    if revenue is not None and prior_revenue is not None and prior_revenue > 0:
        growth = (revenue - prior_revenue) / prior_revenue
        if growth >= 1.5:
            modifier += 1.5
            basis.append(f"~{growth * 100:.0f}% revenue growth over the reported period")
        elif growth >= 0.5:
            modifier += 0.75
            basis.append(f"~{growth * 100:.0f}% revenue growth over the reported period")
        elif growth < -0.15:
            modifier -= 2.0
            basis.append(f"revenue declined ~{abs(growth) * 100:.0f}% over the reported period")
        elif growth < 0:
            modifier -= 0.75
            basis.append(f"revenue declined slightly (~{abs(growth) * 100:.0f}%) over the reported period")

    if retention_pct is not None:
        if retention_pct >= 110:
            modifier += 1.0
            basis.append(f"{retention_pct:g}% retention indicates strong net expansion")
        elif retention_pct >= 95:
            modifier += 0.5
            basis.append(f"{retention_pct:g}% retention reported")
        elif retention_pct < 70:
            modifier -= 2.5
            basis.append(f"{retention_pct:g}% retention is a significant negative signal")
        elif retention_pct < 85:
            modifier -= 1.0
            basis.append(f"{retention_pct:g}% retention is a modeled weak point")

    return modifier, basis


def _score_validation(assumptions: dict) -> CategoryResult:
    """
    The one category scored from founder-REPORTED OBSERVATIONS, not
    modeled assumptions -- see this module's own docstring. A pure idea
    with none of these fields set is correctly Unavailable here
    (excluded from the weighted average, not scored as a 0-out-of-10
    failure) -- see compute_vps()'s renormalization.

    Two regimes, both earned by real signal, never assumed:
    - Pre-commercial (no paying customers, no revenue): interviews and
      waitlist signal only -- UNCHANGED from the prior formula, which
      was never the reported defect.
    - Commercial (paying customers and/or revenue reported): scaled via
      _validation_commercial_scale()'s evidence-anchor tiers, then
      adjusted by _validation_modifiers()'s growth/retention evidence --
      replaces the old formula's early hard cap, the confirmed root
      cause of the ApexGrid regression case (186 paying customers /
      $11.8M ARR / 281% growth / 128% NRR scoring ~5, indistinguishable
      from a company with 10 customers and $1 of revenue).
    """
    validation = assumptions.get("validation") or {}
    interviews = validation.get("customer_interviews")
    waitlist = validation.get("waitlist_signups")
    paying = validation.get("paying_customers")
    revenue = validation.get("monthly_revenue")
    prior_revenue = validation.get("prior_monthly_revenue")
    retention_pct = validation.get("retention_pct")

    if interviews is None and waitlist is None and paying is None and revenue is None:
        return CategoryResult("validation", VPS_CATEGORY_LABELS["validation"], None)

    basis: list[str] = []

    if paying or revenue:
        score = _validation_commercial_scale(paying, revenue)
        if paying:
            basis.append(f"{paying} paying customers reported")
        if revenue:
            basis.append(f"${revenue:,.0f}/mo in reported revenue")

        modifier, modifier_basis = _validation_modifiers(revenue, prior_revenue, retention_pct)
        score += modifier
        basis.extend(modifier_basis)
    else:
        # Pre-commercial: the original interview/waitlist formula --
        # never the reported defect, left unchanged (Part 16: don't
        # discard a working safeguard because a different part of the
        # system was broken).
        score = 0.0
        if interviews is not None:
            score += min(max(interviews, 0) / 25.0, 1.0) * 3.0
            basis.append(f"{interviews} customer interviews reported")
        if waitlist is not None:
            score += min(max(waitlist, 0) / 200.0, 1.0) * 2.0
            basis.append(f"{waitlist} waitlist signups reported")

    return CategoryResult("validation", VPS_CATEGORY_LABELS["validation"], _clamp(score), basis)


_CATEGORY_SCORERS = {
    "market_potential": _score_market_potential,
    "problem_solution": _score_problem_solution,
    "founder_readiness": _score_founder_readiness,
    "gtm_feasibility": _score_gtm_feasibility,
    "economic_potential": _score_economic_potential,
    "validation": _score_validation,
}


def compute_vps(assumptions: dict) -> dict:
    """
    Pure, deterministic function: identical assumptions always produce an
    identical result (Part 19 test 15). No randomness, no LLM call.

    Returns:
        {
            "vps": float | None,   # None only when EVERY category is
                                    # Unavailable (a venture with no
                                    # assumptions at all) -- never
                                    # fabricated as 0.
            "label": "MODELED / ASSUMPTION-BASED",
            "categories": [ {key, label, score, basis}, ... ],
        }
    """
    categories = [scorer(assumptions) for scorer in _CATEGORY_SCORERS.values()]

    scored = [c for c in categories if c.score is not None]

    if not scored:
        vps = None
    else:
        total_weight = sum(VPS_CATEGORY_WEIGHTS[c.key] for c in scored)
        weighted_sum = sum(c.score * VPS_CATEGORY_WEIGHTS[c.key] for c in scored)
        # Renormalized around whichever categories ARE scored -- the same
        # "unavailable dimensions don't silently drag the average toward
        # a fabricated number" discipline as Methodology v2's
        # finalize_pillar_score, applied independently here.
        vps = round(weighted_sum / total_weight, 1) if total_weight > 0 else None

    return {
        "vps": vps,
        "label": VPS_LABEL,
        "categories": [
            {"key": c.key, "label": c.label, "score": c.score, "basis": c.basis}
            for c in categories
        ],
    }
