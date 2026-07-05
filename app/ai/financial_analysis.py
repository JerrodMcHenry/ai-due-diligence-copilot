from ai.analyze_pillar import analyze_pillar
from models.analysis import FinancialAnalysisResult


def analyze_financials(company_text):
    return analyze_pillar(
        pillar="Financial Health",
        company_text=company_text,
        result_model=FinancialAnalysisResult,
        system_message=(
            "You are a venture capital analyst evaluating startup financial "
            "health. Return only valid JSON."
        ),
        extra_fields={
            "revenue_quality": "Assessment of revenue quality.",
            "pricing_model": "Assessment of pricing model.",
            "unit_economics": "Assessment of unit economics.",
            "burn_rate": "Assessment of burn rate.",
            "runway": "Assessment of runway.",
            "capital_efficiency": "Assessment of capital efficiency.",
            "fundraising_readiness": "Assessment of fundraising readiness.",
        },
        extra_rules=[
            "Do not invent financial metrics.",
            "Only use revenue, burn, runway, margin, CAC, LTV, churn, or funding data if explicitly provided.",
            "If financial details are missing, say what is missing.",
            "Evaluate financial health across revenue quality, unit economics, burn efficiency, runway, and fundraising readiness.",
        ],
    )