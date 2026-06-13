from openai import OpenAI
from dotenv import load_dotenv
import os 
import json 

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_traction(company_text):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst evaluating startup traction."
            },
            {
                "role": "user",
                "content": f"""
Analyze evidence of traction for this startup. 

Startup:

{company_text}

Return ONLY valid JSON:

{{
    "custoner_signals": "string",
    "growth_signals": "string",
    "partnership_signals": "string",
    "fundraising_signals": "string",
    "adoption_risk": "string",
    "overall_traction": "string"
}}

Rules:

- Do not invent customers. 
- Do not invent revenue. 
- Do not invent fundraising. 
- If evidence is unavilable, say UNKNOWN.
- Be evidence-based.
"""
            }
        ]
    )

    content = response.choices[0].message.content

    try: 
        return json.loads(content)
    
    except json.JSONDecodeError:

        return {
            "customer_signals": "UNKOWN", 
            "growth_signals": "UNKOOWN", 
            "partership_signals": "UNKNOWN",
            "fundraising_signals": "UNKNOWN",
            "adoption_risk": "Unable to parse", 
            "overall_traction": "Unable to parse"
        }
