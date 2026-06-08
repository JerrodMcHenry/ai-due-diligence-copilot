from pypdf import PdfReader
from io import BytesIO


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n\n"

    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("No readable text found in PDF.")

    return cleaned_text