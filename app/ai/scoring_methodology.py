from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringDimension:
    name: str
    weight: float
    question: str
    strong_signals: list[str]
    weak_signals: list[str]


SCORING_METHODOLOGY = {
    "Market": [
        ScoringDimension(
            name="Market Size",
            weight=0.25,
            question="How large is the addressable market if the company executes successfully?",
            strong_signals=[
                "Large enterprise market",
                "Large SMB market",
                "Global opportunity",
                "Multiple customer segments",
            ],
            weak_signals=[
                "Small niche",
                "Single local market",
                "Limited expansion potential",
            ],
        ),
        ScoringDimension(
            name="Market Growth",
            weight=0.20,
            question="Is the underlying market growing rapidly?",
            strong_signals=[
                "Growing industry",
                "AI adoption",
                "Digital transformation",
                "Regulatory tailwinds",
            ],
            weak_signals=[
                "Declining market",
                "Shrinking demand",
            ],
        ),
        ScoringDimension(
            name="Market Timing",
            weight=0.20,
            question="Is this the right time for this solution?",
            strong_signals=[
                "Technology inflection point",
                "Customer demand",
                "Regulatory changes",
            ],
            weak_signals=[
                "Premature market",
                "Late commodity market",
            ],
        ),
        ScoringDimension(
            name="Competitive Intensity",
            weight=0.15,
            question="Can the company realistically compete?",
            strong_signals=[
                "Clear differentiation",
                "Switching costs",
                "Unique positioning",
            ],
            weak_signals=[
                "Commodity product",
                "Many identical competitors",
            ],
        ),
        ScoringDimension(
            name="Customer Demand",
            weight=0.20,
            question="Is there evidence customers genuinely want this product?",
            strong_signals=[
                "Paying customers",
                "Retention",
                "Customer growth",
                "Case studies",
            ],
            weak_signals=[
                "No validation",
                "No customer evidence",
            ],
        ),
    ],
}