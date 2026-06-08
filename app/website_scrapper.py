import requests
from bs4 import BeautifulSoup


def extract_text_from_website(url: str) -> str:
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        timeout=10
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove junk
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    cleaned_text = " ".join(text.split())

    if not cleaned_text:
        raise ValueError("No readable content found on website.")

    return cleaned_text