from ai.analyze_pillar import analyze_pillar
from models.analysis import FinancialAnalysisResult


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
            "unit_economics": "Assessment of gross margin, CAC payback, LTV:CAC, and sales efficiency.",
            "burn_rate": "Assessment of burn rate, burn multiple, and growth relative to spending.",
            "runway": "Assessment of cash runway and ability to reach the next major milestone.",
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
                "Evaluate financial health across Revenue Quality, Unit Economics, "
                "Burn Efficiency, Runway, and Fundraising Readiness."
            ),
        ],
    )