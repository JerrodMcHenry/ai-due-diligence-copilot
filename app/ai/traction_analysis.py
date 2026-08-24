from app.ai.analyze_pillar import analyze_pillar
from app.models.analysis import TractionAnalysisResult


def analyze_traction(company_text):
    return analyze_pillar(
        pillar="Traction",
        company_text=company_text,
        result_model=TractionAnalysisResult,
        system_message=(
            "You are a venture capital analyst evaluating startup traction. "
            "Return only valid JSON."
        ),
        extra_fields={
            "customer_growth": "Assessment of customer growth.",
            "revenue_growth": "Assessment of revenue growth.",
            "fundraising_signal": "Assessment of fundraising or investor validation signals.",
        },
        extra_rules=[
            "Do not invent customer counts, revenue, churn, retention, or growth rates.",
            "Only use metrics explicitly present in the startup information.",
            "If traction details are missing, say what is missing.",
            # SIE Methodology v2: "commercial validation" removed (it double-counted
            # evidence already owned by Customer Growth/Revenue Growth/Retention).
            # Growth Velocity (a Deterministic, normalized-rate dimension -- see
            # app/ai/sie_v2_anchors.py) replaces it. If the supplied text discloses a
            # real, dated, two-point customer-count or revenue series (both points
            # confirmed actuals, not a projection), extract it into the Growth
            # Velocity dimension's structured_facts field; do not estimate one from
            # a single data point.
            "Evaluate traction across customer growth, revenue growth, retention, engagement, and growth velocity.",
        ],
    )