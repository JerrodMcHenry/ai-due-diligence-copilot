from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_structured_analysis(company_text):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital analyst. Return only valid JSON."
            },
            {
                "role": "user",
                "content":f"""
Analyze this startup and return JSON with these exact keys:

company_name
summary
key_risks
strengths
recommendation

Startup:
{company_text}
"""
            }
        ]
    )

    content = response.choices[0].message.content
    print("\nRAW STRUCTURED CONTENT:\n")
    print(content)

    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)