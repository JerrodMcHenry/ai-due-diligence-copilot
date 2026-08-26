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

from app.ai.vps_scoring import VPS_CATEGORY_LABELS

STRENGTH_THRESHOLD = 7.0
RISK_THRESHOLD = 4.0
MAX_MILESTONES = 5


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


def _next_milestones(assumptions: dict, categories_by_key: dict) -> list[str]:
    milestones = []

    validation = assumptions.get("validation") or {}
    interviews = validation.get("customer_interviews")
    if interviews is None or interviews < 20:
        milestones.append("Interview 20+ target customers to validate the problem is real.")

    paying = validation.get("paying_customers")
    if paying is None or paying == 0:
        milestones.append("Secure a first paying customer to validate willingness to pay.")

    problem_solution = categories_by_key.get("problem_solution")
    ps = assumptions.get("problem_solution") or {}
    if problem_solution and (problem_solution["score"] is None or not ps.get("differentiation")):
        milestones.append("Define what specifically differentiates your solution from alternatives.")

    founder = categories_by_key.get("founder_readiness")
    if founder and founder["score"] is not None and founder["score"] < 6.0:
        milestones.append("Strengthen the founding team's domain, technical, or business coverage.")

    gtm = categories_by_key.get("gtm_feasibility")
    if gtm and gtm["score"] is None:
        milestones.append("Define a primary customer-acquisition strategy.")

    economic = categories_by_key.get("economic_potential")
    if economic and economic["score"] is None:
        milestones.append("Estimate a pricing model and expected gross margin.")

    market = categories_by_key.get("market_potential")
    market_assumptions = assumptions.get("market") or {}
    if market and market["score"] is not None and not market_assumptions.get("competition_intensity"):
        milestones.append("Assess how intense competition is in your target market.")

    return milestones[:MAX_MILESTONES]


def generate_guidance(assumptions: dict, vps_result: dict) -> dict:
    categories = vps_result["categories"]
    categories_by_key = {c["key"]: c for c in categories}

    return {
        "strengths": _strengths(categories),
        "risks": _risks(categories),
        "key_assumptions": _key_assumptions(assumptions),
        "validation_gaps": _validation_gaps(assumptions),
        "next_milestones": _next_milestones(assumptions, categories_by_key),
    }
