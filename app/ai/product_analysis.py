from ai.analyze_pillar import analyze_pillar
from models.analysis import ProductAnalysisResult


def analyze_product(company_text):
    return analyze_pillar(
        pillar="Product",
        company_text=company_text,
        result_model=ProductAnalysisResult,
        system_message=(
            "You are a venture capital analyst evaluating startup product "
            "quality and defensibility. Return only valid JSON."
        ),
        extra_fields={
            "customer_value":
                "Assessment of how clearly the product solves an important customer problem.",
            "technical_defensibility":
                "Assessment of technical differentiation, proprietary technology, AI capability, integrations, or defensibility.",
            "ease_of_adoption":
                "Assessment of how easy it is for target customers to adopt and use the product.",
            "product_maturity":
                "Assessment of product completeness, reliability, roadmap maturity, and readiness for scale.",
        },
    )