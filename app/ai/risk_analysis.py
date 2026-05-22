from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_risks(company_text):
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",

        messages=[
            {
                "role": "system",
                "content": "You are a venture capital risk analyst"
            },
            
            {
                "role": "user",
                "content": f"""
                Analyze the risks of this startup.

                Startup:
                {company_text}

                Focus on:
                - competition
                - scalability
                - market risk
                - customer adoption risk 
                - operational risk
                """

            }
        ]
    )

    return response.choices[0].message.content