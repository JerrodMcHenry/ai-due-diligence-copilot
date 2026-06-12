from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def extract_search_query(company_text: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages= [
            {
                "role": "system",
                "content": "Extract the best web search query for researching this startup"
            },
            {
                "role": "user",
                "content": f"""
Create one concise web search query to research this company. 

Company information:
{company_text}

Return only the search query. No quotes. No explination.
"""
            }
        ]
    )
    return response.choices[0].message.content.strip()


def search_web(query: str) -> str:
    results = tavily_client.search(
        query=query,
        search_depth="basic",
        max_results=5,
        include_answer=True
    )
    research_text = ""

    if results.get("answer"):
        research_text += f"Tavily Answer:\n{results['answer']}\n\n"

    for item in results.get("results", []):
        title = item.get("title", "")
        url = item.get("url", "")
        content = item.get("content", "")

        research_text +=  f"Title: {title}\nURL: {url}\nContent: {content}\n\n"

    return research_text.strip()



def enrich_research(company_text):
    search_query = extract_search_query(company_text)
    web_research = search_web(search_query)
    
    
    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a startup research analyst helping enrich due diligence context using web research evidence."
            },
            {
                "role": "user",
                "content": f"""


Company information:
{company_text}

Web research:
{web_research}

Create a due diligence brief using ONLY the provided information.

Rules:

- Only state information as a fact if it is supported by the web research.
- Clearly seperate facts from assumptions.
- If information cannot be verified, state UNKNOWN. 
- Do not invent funding amounts. 
- Do not invent TAM, SAM, SOM, market size, market share, growth rates, or revenue figures. 
- Do not make unsupported claims sound certain. 

Return these sections: 

1. Company Overview
2. Verified Facts
3. Reasonable Assumptions
4. Business Model 
5. Target Customers
6. Competitors
7. Key Risks
8. Important Unknowns
9. Sources

For the Sources section, include any URLs referenced in the web research. 
"""
            }
        ]
    )

    return response.choices[0].message.content