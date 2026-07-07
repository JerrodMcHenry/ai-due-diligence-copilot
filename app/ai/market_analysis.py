from ai.analyze_pillar import analyze_pillar
from models.analysis import MarketAnalysisResult


def analyze_market(company_text: str) -> MarketAnalysisResult:
    return analyze_pillar(
        pillar="Market",
        company_text=company_text,
        result_model=MarketAnalysisResult,
        system_message=(
            "You are a disciplined venture capital market analyst. "
            "You do not invent market size numbers. Return only valid JSON."
        ),
        extra_fields={
            "tam": "UNKNOWN or directly supported value only",
            "sam": "UNKNOWN or directly supported value only",
            "som": "UNKNOWN or directly supported value only",
            "growth_rate": "UNKNOWN or directly supported value only",
        },
        extra_rules=[
            "Do not invent TAM, SAM, SOM, market size, market share, revenue, transaction volume, customer counts, or growth rates.",
            "Do not estimate numbers unless they are explicitly stated in the provided context.",
            "For TAM, SAM, and SOM, only return values if they are explicitly stated in the provided context.",
            "Do not derive, calculate, estimate, or infer TAM, SAM, or SOM from market share, revenue, payment volume, customer count, or other metrics.",
            "If TAM, SAM, SOM, or growth_rate is not explicitly provided, return UNKNOWN.",
            "If you make a qualitative assessment, label it as an inference.",
            "Be conservative and evidence-based.",
        ],
    )