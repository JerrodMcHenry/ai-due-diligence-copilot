from ai.analyze_pillar import analyze_pillar
from models.analysis import FounderAnalysisResult


def analyze_founders(company_text):
    return analyze_pillar(
        pillar="Team",
        company_text=company_text,
        result_model=FounderAnalysisResult,
        system_message=(
            "You are a venture capital analyst evaluating startup founding "
            "teams. Return only valid JSON."
        ),
        extra_fields={
            "founder_market_fit": "Assessment of founder-market fit.",
            "fundraising_signal": "Assessment of the team's fundraising signal.",
        },
        extra_rules=[
            "Do not invent founder credentials.",
            "If founder details are missing, say what is missing.",
            "Evaluate the team across founder-market fit, technical capability, business capability, leadership, and execution track record.",
        ],
    )