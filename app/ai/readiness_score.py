from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_readiness_score(
    market_score,
    team_score,
    product_score,
    competition_score,
    traction_score,
    financial_score,
    overall_score
):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst. Return only valid JSON."
            },
            {
                "role": "user",
                "content": f"""
Evaluate fundraising readiness.

Scores:

Market: {market_score}
Team: {team_score}
Product: {product_score}
Competition: {competition_score}
Traction: {traction_score}
Financial: {financial_score}
Overall: {overall_score}

Return ONLY valid JSON.

Use this exact structure:

{{
  "readiness_score": 0,
  "readiness_summary": "",
  "strengths": [],
  "weaknesses": []
}}
"""
            }
        ]
    )

    content = response.choices[0].message.content
    content = content.replace("```json", "").replace("```", "").strip()

    print("\nRAW READINESS CONTENT:\n")
    print(content)
    return json.loads(content)