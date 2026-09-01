"""
Idea Lab / Venture Simulator V1 -- deterministic, rule-based guidance
generated from the SAME structured assumptions + computed VPS categories
vps_scoring.compute_vps() already produced.

Entirely template-driven, no LLM call, matching Part 13's directive: if a
category can't yet be defensibly scored, this flags the gap rather than
hiding an arbitrary generated sentence behind the interface. Language
throughout is restrained by construction -- these are templates, not a
model free-associating about a company's chances ("interview 20 target
customers", never "your idea will succeed").
"""

from app.ai.vps_scoring import VPS_CATEGORY_LABELS, VPS_CATEGORY_WEIGHTS

STRENGTH_THRESHOLD = 7.0
RISK_THRESHOLD = 4.0
MAX_MILESTONES = 5
MAX_PATH_TO_STRONGER = 3


def _strengths(categories: list[dict]) -> list[str]:
    lines = []

    for category in categories:
        if category["score"] is not None and category["score"] >= STRENGTH_THRESHOLD:
            basis = category["basis"][0] if category["basis"] else None
            lines.append(
                f"{category['label']} is a modeled strength"
                + (f" — {basis}." if basis else ".")
            )

    return lines


def _risks(categories: list[dict]) -> list[str]:
    lines = []

    for category in categories:
        if category["score"] is not None and category["score"] < RISK_THRESHOLD:
            basis = category["basis"][0] if category["basis"] else None
            lines.append(
                f"{category['label']} is a modeled weak point"
                + (f" — {basis}." if basis else ".")
            )

    return lines


def _key_assumptions(assumptions: dict) -> list[str]:
    """Every material MODELED input actually in use, labeled as such --
    never conflated with validation's founder-reported observations."""
    lines = []

    market = assumptions.get("market") or {}
    if market.get("estimated_market_size"):
        lines.append(f"Assumption: market size is \"{market['estimated_market_size']}\".")
    if market.get("competition_intensity"):
        lines.append(f"Assumption: competitive intensity is {market['competition_intensity']}.")

    gtm = assumptions.get("gtm") or {}
    if gtm.get("expected_cac") is not None:
        lines.append(f"Assumption: expected CAC is ${gtm['expected_cac']:,.0f}.")

    econ = assumptions.get("economics") or {}
    if econ.get("expected_gross_margin_pct") is not None:
        lines.append(f"Assumption: gross margin is {econ['expected_gross_margin_pct']}%.")
    if econ.get("price_point") is not None:
        lines.append(f"Assumption: price point is ${econ['price_point']:,.0f}.")

    capital = assumptions.get("capital") or {}
    if capital.get("monthly_burn") is not None:
        lines.append(f"Assumption: monthly burn is ${capital['monthly_burn']:,.0f}.")

    return lines


def _validation_gaps(assumptions: dict) -> list[str]:
    validation = assumptions.get("validation") or {}
    gaps = []

    if validation.get("customer_interviews") is None:
        gaps.append("No customer interviews reported yet.")
    if validation.get("waitlist_signups") is None and validation.get("paying_customers") is None:
        gaps.append("No waitlist or paying-customer signal reported yet.")
    if validation.get("monthly_revenue") is None:
        gaps.append("No revenue reported yet.")

    if not gaps:
        return []

    # Framed as expected, not as a failure -- Part 4's explicit
    # requirement not to punish an idea for being early.
    return ["This is expected at the idea stage, not a failure — validation is earned over time."] + gaps


def _has_real_traction(assumptions: dict) -> bool:
    """
    A venture has moved past "prove the problem/willingness-to-pay is
    real" once it has an actual paying customer or actual revenue --
    founder-REPORTED OBSERVATIONS (assumptions["validation"]), never a
    modeled assumption. Used only to REORDER/select among the same fixed
    template sentences below, never to change a score -- this function is
    not called anywhere in vps_scoring.py and has no effect on VPS.
    """
    validation = assumptions.get("validation") or {}
    paying = validation.get("paying_customers")
    revenue = validation.get("monthly_revenue")
    return bool((paying is not None and paying > 0) or (revenue is not None and revenue > 0))


def _next_milestones(assumptions: dict, categories_by_key: dict) -> list[str]:
    """
    Selects and orders the venture's biggest current uncertainties.

    This used to be a single fixed fall-through sequence (always ask
    about interviews first, then a first paying customer, then
    differentiation, ...) regardless of what the venture's own modeled
    state already showed. That produced genuinely confusing output for a
    venture that already has real traction -- e.g. recommending "secure a
    first paying customer" to a venture that already reported 14 of them,
    or leading with "define your differentiation" ahead of the much
    bigger open question a traction-stage venture actually faces: whether
    growth holds up beyond founder-led selling.

    Every candidate sentence below is still one of the SAME fixed
    templates as before (missionSuggestions.ts's exact-string lookup
    still matches every one) -- what changed is which ones apply and in
    what order, based on `_has_real_traction()` and each category's own
    already-computed score. Nothing here is a score, a new AI call, or a
    new recommendation engine -- it is the same deterministic, template-
    driven selection, made to actually look at the venture's current
    modeled state before picking an order.
    """
    validation = assumptions.get("validation") or {}
    interviews = validation.get("customer_interviews")
    paying = validation.get("paying_customers")
    has_traction = _has_real_traction(assumptions)

    # (priority, text) -- lower priority numbers surface first. Several
    # candidates can share a priority tier; original template order below
    # breaks ties, same as the old fixed sequence did.
    candidates: list[tuple[int, str]] = []

    if not has_traction:
        if interviews is None or interviews < 20:
            candidates.append((0, "Interview 20+ target customers to validate the problem is real."))
        if paying is None or paying == 0:
            candidates.append((1, "Secure a first paying customer to validate willingness to pay."))
    elif interviews is None or interviews < 20:
        # Still a real gap worth naming for a traction-stage venture, but
        # no longer the FIRST thing to ask -- it already has stronger
        # signal than interviews alone.
        candidates.append((4, "Interview 20+ target customers to validate the problem is real."))

    gtm = categories_by_key.get("gtm_feasibility")
    if gtm and gtm["score"] is None:
        candidates.append((1, "Define a primary customer-acquisition strategy."))
    elif has_traction and gtm and gtm["score"] is not None and gtm["score"] < STRENGTH_THRESHOLD:
        # The traction-stage question this venture actually faces: it has
        # customers, but GTM Feasibility (assumed CAC/price economics,
        # not traction itself -- see vps_scoring.py's own module
        # docstring on why VPS keeps these separate) isn't yet a modeled
        # strength. Surfaced ahead of differentiation because "can this
        # keep growing" is a bigger open question than "can I name my
        # differentiator" once customers already exist.
        candidates.append((0, "Prove customer acquisition works repeatably beyond founder-led sales or referrals."))

    problem_solution = categories_by_key.get("problem_solution")
    ps = assumptions.get("problem_solution") or {}
    if problem_solution and (problem_solution["score"] is None or not ps.get("differentiation")):
        candidates.append((2 if not has_traction else 3, "Define what specifically differentiates your solution from alternatives."))

    founder = categories_by_key.get("founder_readiness")
    if founder and founder["score"] is not None and founder["score"] < 6.0:
        candidates.append((3, "Strengthen the founding team's domain, technical, or business coverage."))

    economic = categories_by_key.get("economic_potential")
    if economic and economic["score"] is None:
        candidates.append((3, "Estimate a pricing model and expected gross margin."))

    market = categories_by_key.get("market_potential")
    market_assumptions = assumptions.get("market") or {}
    if market and market["score"] is not None and not market_assumptions.get("competition_intensity"):
        candidates.append((5, "Assess how intense competition is in your target market."))

    candidates.sort(key=lambda c: c[0])

    milestones: list[str] = []
    for _, text in candidates:
        if text not in milestones:
            milestones.append(text)

    return milestones[:MAX_MILESTONES]


# Short, deterministic "what's missing" hints for the categories most
# commonly incomplete rather than genuinely weak -- reused by
# _path_to_stronger() below. Each hint names a concrete, honest gap in
# the MODELED ASSUMPTIONS already in front of the founder; it never
# implies a point value, and it is never shown for a category that's
# already Unavailable (that's what _next_milestones() covers).
_STRENGTHEN_HINTS: dict[str, str] = {
    "market_potential": "A larger estimated market size or a lower assumed competitive intensity would strengthen this.",
    "problem_solution": "A specific, named differentiation is usually the single biggest lever here.",
    "founder_readiness": "More stated relevant domain experience, or a technical/business cofounder, would strengthen this.",
    "gtm_feasibility": "A clearly stated acquisition strategy plus a price point that comfortably beats your expected CAC would strengthen this.",
    "economic_potential": "A higher assumed gross margin, or a clearer pricing model, would strengthen this.",
    "validation": "More customer interviews, paying customers, or reported revenue would strengthen this -- earned, not assumed.",
}


def _path_to_stronger(categories: list[dict]) -> list[dict]:
    """
    Restrained "what would most plausibly strengthen the overall
    assessment" guidance -- Section 7's "Path to 8" investigation.

    Deliberately NOT a score preview: it never fabricates or previews a
    specific VPS delta. It only (a) identifies which SCORED categories
    are below STRENGTH_THRESHOLD, (b) ranks them by
    weight x headroom-to-threshold (both already-existing, unchanged
    values -- VPS_CATEGORY_WEIGHTS from vps_scoring.py and each
    category's own already-computed score), and (c) attaches one
    deterministic, template-driven hint per category. A founder who wants
    an actual number can already get one honestly through the existing
    scenario-preview machinery (What If / Recalculate) by editing real
    assumptions -- this list only points at where editing would matter
    most.
    """
    ranked = []
    for category in categories:
        score = category["score"]
        if score is None or score >= STRENGTH_THRESHOLD:
            continue

        weight = VPS_CATEGORY_WEIGHTS.get(category["key"], 0.0)
        headroom = STRENGTH_THRESHOLD - score
        ranked.append((weight * headroom, category))

    ranked.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {
            "key": category["key"],
            "label": category["label"],
            "score": category["score"],
            "hint": _STRENGTHEN_HINTS.get(category["key"], "More supporting detail here would strengthen this."),
        }
        for _, category in ranked[:MAX_PATH_TO_STRONGER]
    ]


def generate_guidance(assumptions: dict, vps_result: dict) -> dict:
    categories = vps_result["categories"]
    categories_by_key = {c["key"]: c for c in categories}

    return {
        "strengths": _strengths(categories),
        "risks": _risks(categories),
        "key_assumptions": _key_assumptions(assumptions),
        "validation_gaps": _validation_gaps(assumptions),
        "next_milestones": _next_milestones(assumptions, categories_by_key),
        "path_to_stronger": _path_to_stronger(categories),
    }
