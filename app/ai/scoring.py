from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import re

from models.scoring import Subscore, PillarScoreBreakdown

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SIE_SCORING_CONFIG = {
    "Market": [
        ("Market Size", 0.25),
        ("Market Growth", 0.20),
        ("Market Timing", 0.20),
        ("Competitive Intensity", 0.15),
        ("Customer Demand", 0.20),
    ],
    "Team": [
        ("Founder-Market Fit", 0.25),
        ("Technical Capability", 0.20),
        ("Business Capability", 0.20),
        ("Leadership", 0.20),
        ("Execution Track Record", 0.15),
    ],
    "Product": [
        ("Customer Value", 0.25),
        ("Differentiation", 0.20),
        ("Usability", 0.15),
        ("Defensibility", 0.20),
        ("Adoption Potential", 0.20),
    ],
    "Execution": [
        ("Go-to-Market Execution", 0.20),
        ("Product Execution", 0.20),
        ("Operational Execution", 0.20),
        ("Strategic Execution", 0.20),
        ("Execution Velocity", 0.20),
    ],
    "Traction": [
        ("Customer Growth", 0.20),
        ("Revenue Growth", 0.20),
        ("Retention", 0.20),
        ("Engagement", 0.20),
        ("Commercial Validation", 0.20),
    ],
    "Financial Health": [
        ("Revenue Quality", 0.20),
        ("Unit Economics", 0.20),
        ("Burn Efficiency", 0.20),
        ("Runway", 0.20),
        ("Fundraising Readiness", 0.20),
    ],
}


MARKET_SUBSCORES = SIE_SCORING_CONFIG["Market"]
TEAM_SUBSCORES = SIE_SCORING_CONFIG["Team"]
PRODUCT_SUBSCORES = SIE_SCORING_CONFIG["Product"]
EXECUTION_SUBSCORES = SIE_SCORING_CONFIG["Execution"]
TRACTION_SUBSCORES = SIE_SCORING_CONFIG["Traction"]
FINANCIAL_SUBSCORES = SIE_SCORING_CONFIG["Financial Health"]


def get_scoring_dimensions(pillar: str) -> list[tuple[str, float]]:
    return SIE_SCORING_CONFIG[pillar]


def parse_json_from_response(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in scoring response.")

    return json.loads(match.group(0))


def calculate_weighted_score(subscores: list[Subscore]) -> float | None:
    valid_scores = [
        subscore for subscore in subscores
        if subscore.score is not None
    ]

    if not valid_scores:
        return None

    total_weight = sum(
        subscore.weight
        for subscore in valid_scores
    )

    if total_weight == 0:
        return None

    weighted_score = sum(
        subscore.score * subscore.weight
        for subscore in valid_scores
    ) / total_weight

    return round(weighted_score, 1)


def create_subscores(definitions: list[tuple[str, float]]) -> list[Subscore]:
    return [
        Subscore(
            name=name,
            weight=weight,
        )
        for name, weight in definitions
    ]


def finalize_pillar_score(
    score_breakdown: PillarScoreBreakdown,
) -> PillarScoreBreakdown:
    score_breakdown.score = calculate_weighted_score(
        score_breakdown.subscores
    )

    return score_breakdown


def generate_investment_score(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a venture capital analyst scoring startup "
                    "investment opportunities. Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"""
Score this startup as an investment opportunity.

Startup:
{company_text}

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.
Do not wrap the JSON in triple backticks.

Return exactly this structure:
{{
  "market_score": 0,
  "team_score": 0,
  "product_score": 0,
  "competition_score": 0,
  "traction_score": 0,
  "financial_score": 0,
  "overall_score": 0,
  "recommendation": "string"
}}

overall_score should be 0 to 100.
market_score, team_score, product_score, competition_score, traction_score, and financial_score should be 0 to 10.
""",
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        return parse_json_from_response(content)

    except Exception:
        return {
            "market_score": 0,
            "team_score": 0,
            "product_score": 0,
            "competition_score": 0,
            "traction_score": 0,
            "financial_score": 0,
            "overall_score": 0,
            "recommendation": "Unable to parse scoring output",
        }