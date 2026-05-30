from openai import OpenAI
from dotenv import load_dotenv
import os 

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_competitors(company_text):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital associate analyzing startup competition."
            },
            {
                "role": "user",
                "content": f"""
                Anlyze the competitors for this startup.

                Startup:
                {company_text}

                Include:
                - Major competitors
                - Competitive advantages
                - Competitive disadvantges 
                - Barriers to entry 
                - Competitive risks
                """
            }
        ]
    )

    return response.choices[0].message.content
