from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_founders(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst evaluating startup founding teams."
            },
            {
                "role": "user",
                "content": f"""
Analyze the founding team for this startup.

Startup:
{company_text}

Return ONLY valid JSON with these fields:
{{
  "founder_strengths": "string",
  "domain_expertise": "string",
  "execution_risk": "string",
  "fundraising_signal": "string",
  "overall_assessment": "string"
}}
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "founder_strengths": "Unable to parse founder analysis",
            "domain_expertise": "Unable to parse founder analysis",
            "execution_risk": "Unable to parse founder analysis",
            "fundraising_signal": "Unable to parse founder analysis",
            "overall_assessment": "Unable to parse founder analysis"
        }