"""
Scores a frozen evidence packet through the real six-pillar SIE scoring
system, without calling live research.

This does not change production behavior: run_due_diligence() (the
production path) still always calls enrich_research() itself and always
builds enriched_text from live results. score_frozen_evidence() below is
an additional, harness-only entry point that skips straight to
analyze_pillars_from_enriched_text() with a pre-built enriched_text -- the
same function run_due_diligence() calls internally, so both paths run
identical scoring logic.
"""

from app.reliability.frozen_evidence import FrozenEvidencePacket
from app.workflows.due_diligence_workflow import (
    analyze_pillars_from_enriched_text,
    build_sie_methodology_analysis,
)
from app.models.startup import SIEMethodologyAnalysis


def score_frozen_evidence(
    packet: FrozenEvidencePacket,
) -> SIEMethodologyAnalysis:
    """
    Run the six pillar analyses against packet.enriched_text and assemble
    the resulting SIEMethodologyAnalysis, exactly as run_due_diligence()
    would -- minus research (frozen), minus readiness (an LLM call that
    does not feed startup_intelligence_score -- see
    app/ai/investment_score.py::calculate_base_score, which reads only
    pillar scores), and minus summary/risk/memo/competitor generation
    (irrelevant to SPS and a source of unrelated API cost/variance in a
    loop that runs 10x per fixture).
    """
    pillar_results = analyze_pillars_from_enriched_text(packet.enriched_text)

    return build_sie_methodology_analysis(
        structured_analysis=packet.structured_analysis,
        readiness=None,
        founder_analysis=pillar_results["founder_analysis"],
        market_analysis=pillar_results["market_analysis"],
        product_analysis=pillar_results["product_analysis"],
        execution_analysis=pillar_results["execution_analysis"],
        traction_analysis=pillar_results["traction_analysis"],
        financial_analysis=pillar_results["financial_analysis"],
    )
