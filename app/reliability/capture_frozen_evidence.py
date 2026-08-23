"""
One-off capture of a frozen evidence packet.

Calls live research enrichment (Tavily + 2 OpenAI calls, now temperature=
0.0 per Phase 1) and structured-analysis extraction EXACTLY ONCE, then
freezes the result to app/reliability/fixtures/<name>.json for repeated,
research-free scoring runs via the reliability harness.

This is NOT run as part of the repeated 10x reliability loop -- it is run
once, by hand, to produce or refresh a fixture.

Usage:
    python -m app.reliability.capture_frozen_evidence novaledger \
        --company-text-file path/to/company_text.txt
"""

import argparse

from app.ai.research_enrichment import enrich_research
from app.ai.structured_analysis import generate_structured_analysis
from app.reliability.frozen_evidence import FrozenEvidencePacket
from app.workflows.due_diligence_workflow import build_enriched_text


def capture(name: str, company_text: str) -> FrozenEvidencePacket:
    research_result = enrich_research(company_text)
    research_brief = research_result["research_brief"]
    sources = research_result["sources"]
    search_query = research_result["search_query"]

    enriched_text = build_enriched_text(company_text, research_brief)
    structured_analysis = generate_structured_analysis(enriched_text)

    packet = FrozenEvidencePacket(
        company_name=structured_analysis.get("company_name") or name,
        company_text=company_text,
        search_query=search_query,
        research_brief=research_brief,
        sources=sources,
        enriched_text=enriched_text,
        structured_analysis=structured_analysis,
    )

    path = packet.save(name)
    print(f"Saved frozen evidence packet: {path}")
    return packet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Fixture name, e.g. novaledger")
    parser.add_argument(
        "--company-text-file",
        required=True,
        help="Path to a text file containing the exact company_text to freeze.",
    )
    args = parser.parse_args()

    with open(args.company_text_file, "r", encoding="utf-8") as f:
        company_text = f.read()

    capture(args.name, company_text)


if __name__ == "__main__":
    main()
