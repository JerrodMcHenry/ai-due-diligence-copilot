from app.ai.analyze_pillar import analyze_pillar
from app.models.analysis import FinancialAnalysisResult


def analyze_financials(company_text: str) -> FinancialAnalysisResult:
    return analyze_pillar(
        pillar="Financial Health",
        company_text=company_text,
        result_model=FinancialAnalysisResult,
        system_message=(
            "You are a venture capital analyst evaluating startup financial health. "
            "Use all financial evidence explicitly included in the supplied company "
            "information, including company-provided metrics. A metric does not need "
            "to be independently published on the public internet to be treated as "
            "observed evidence. Return only valid JSON."
        ),
        extra_fields={
            "revenue_quality": "Assessment of revenue durability, recurrence, retention, concentration, and predictability.",
            "pricing_model": "Assessment of pricing structure, pricing power, and contract economics.",
            "unit_economics": (
                "Assessment of whether a typical unit/customer/transaction earns sufficient economic "
                "value relative to the cost to acquire and serve it. Use the evidence family that "
                "actually matches this company's business model -- SaaS/subscription (gross margin, "
                "CAC payback, LTV:CAC), marketplace (take-rate, gross-vs-net revenue, per-transaction "
                "servicing cost), insurance (loss ratio, combined ratio), hardware/manufacturing "
                "(per-unit COGS vs. price), commerce/DTC (landed cost vs. price, contribution margin), "
                "or R&D-partnership/deeptech (program fee vs. cost to deliver). Do not require or expect "
                "SaaS-shaped figures from a company in a different family."
            ),
            "burn_rate": (
                "Assessment of burn rate, burn multiple, and growth relative to spending. When a "
                "defensible burn multiple cannot be computed (capital-intensive pre-revenue hardware/"
                "biotech/deeptech, or spend driven by capex/R&D rather than revenue-generating "
                "operations), evaluate spend relative to stated milestones/output, capital intensity "
                "appropriate to the business model, and financing consumption relative to demonstrated "
                "progress instead -- but never restate Runway's 'how long until cash runs out' question "
                "here; that is Runway's exclusive domain."
            ),
            "runway": (
                "Assessment of cash runway and ability to reach the next major milestone. When an exact "
                "months-of-runway calculation is not possible, permit judgment only from strong, direct "
                "evidence of the financing position (documented near-insolvency, emergency/rescue "
                "financing, or clearly substantial cash reserves relative to known operating needs). "
                "The absence of public cash data is never itself grounds to infer distress -- do not "
                "score this dimension low merely because no cash figure was disclosed."
            ),
            "capital_efficiency": "Assessment of growth and milestone achievement relative to capital consumed.",
            "fundraising_readiness": "Assessment of readiness to raise the next financing round.",
        },
        extra_rules=[
            "Do not invent financial metrics.",
            (
                "Treat any financial metric explicitly stated in company_text as "
                "observed evidence, even when it is company-provided or normally private."
            ),
            (
                "Do not mark a metric unavailable merely because it is not independently "
                "published or externally verified."
            ),
            (
                "Use explicitly provided revenue, ARR, retention, churn, gross margin, "
                "CAC payback, LTV:CAC, burn multiple, cash, runway, funding, and use-of-funds data."
            ),
            (
                "For AtlasGrid-like input, metrics such as 141% NRR, 96% GRR, "
                "84% gross margin, 10-month CAC payback, 6.4x LTV:CAC, "
                "0.7 burn multiple, and 37 months runway must not be treated as missing "
                "when they appear in company_text."
            ),
            "If a genuinely required financial detail is absent, identify only that specific missing information.",
            (
                # SIE Methodology v2: Fundraising Readiness is unscored (narrative-only) --
                # not one of the four scored Financial Health dimensions.
                "Evaluate financial health across Revenue Quality, Unit Economics, "
                "Burn Efficiency, and Runway. Fundraising Readiness is narrative-only in v2 -- "
                "assess it for the fundraising_readiness field above, but it is not scored "
                "and does not enter Financial Health's pillar aggregation."
            ),
        ],
    )