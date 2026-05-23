from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_investment_memo(company_text):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a venture capital associate writing concise investment memos."
            },
            {
                "role": "user",
                "content": f"""
                Create a concise investment memo for this startup.

                Starup:
                {company_text}

                Include:
                - Company overview
                - Problem
                - Solution
                - Market opportunity 
                - Competative landscape
                - Key risks
                - Recommendation
                """
            }
        ]
    )

    return response.choices[0].message.content