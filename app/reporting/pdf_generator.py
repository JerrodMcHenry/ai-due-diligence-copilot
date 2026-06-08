from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime
import os
import json
import re


def clean_filename(text: str) -> str:
    text = text[:40]
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text)
    return text.strip("_").lower() or "analysis"

def clean_markdown(text):
    if text is None:
        return ""

    text = str(text)

    text = text.replace("### ", "")
    text = text.replace("## ", "")
    text = text.replace("# ", "")

    text = text.replace("**", "")
    text = text.replace("__", "")

    text = text.replace("\n", "<br/>")

    return text

def format_value(value):
    if isinstance(value, dict):
        return "<br/>".join([
            f"<b>{clean_markdown(key)}:</b> {clean_markdown(val)}"
            for key, val in value.items()
        ])

    if isinstance(value, list):
        return "<br/>".join([
            f"- {clean_markdown(item)}"
            for item in value
        ])

    if value is None:
        return ""

    return clean_markdown(value)




def generate_pdf_report(analysis: dict) -> str:
    os.makedirs("reports", exist_ok=True)

    source = analysis.get("company_text", "analysis")
    filename = f"{clean_filename(source)}_due_diligence_report.pdf"
    file_path = os.path.join("reports", filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=LETTER,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("AI Due Diligence Report", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Source:</b> {format_value(source)}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["BodyText"]))
    story.append(Spacer(1, 18))

    sections = [
        ("Investment Score", analysis.get("investment_score")),
        ("Executive Summary", analysis.get("summary")),
        ("Founder Analysis", analysis.get("founder_analysis")),
        ("Market Analysis", analysis.get("market_analysis")),
        ("Competitor Analysis", analysis.get("competitor_analysis")),
        ("Risk Analysis", analysis.get("risk_analysis")),
        ("Investment Memo", analysis.get("memo")),
        ("Structured Analysis", analysis.get("structured_analysis")),
    ]

    for title, value in sections:
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Paragraph(format_value(value), styles["BodyText"]))
        story.append(Spacer(1, 14))

    doc.build(story)

    return file_path

