from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def enrich_research(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a startup research analyst helping enrich due diligence context."
            },
            {
                "role": "user",
                "content": f"""
Based on the company information below, provide additional research-style context.

Company information:
{company_text}

Return a concise research brief with these sections:

1. Company Overview
2. Likely Business Model
3. Target Customers
4. Market Context
5. Potential Competitors
6. Key Risks
7. Important Unknowns

Do not make unsupported claims sound certain.
If information is missing, clearly say what is unknown.
"""
            }
        ]
    )

    return response.choices[0].message.content