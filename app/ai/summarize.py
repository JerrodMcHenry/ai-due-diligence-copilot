from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_company(company_text):
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",

        messages= [
            {
                "role": "system",
                "content": "You are a venture capital analyst."
            },
            {
                "role": "user",
                "content": f"Summarize this startup:\n\n{company_text}"
            }
        ]
    )

    return response.choices[0].message.content