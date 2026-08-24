from typing import Literal

from pydantic import BaseModel, Field


AnalysisType = Literal[
    "public",
    "pitch_deck",
    "founder",
    "investor",
    "data_room",
]


EvidenceSourceType = Literal[
    "company_description",
    "website",
    "public_research",
    "pitch_deck",
    "founder_questionnaire",
    "founder_metrics",
    "financial_documents",
    "data_room",
    "investor_notes",
]


class AnalysisContext(BaseModel):
    analysis_type: AnalysisType = "public"

    evidence_sources: list[EvidenceSourceType] = Field(
        default_factory=lambda: ["company_description"]
    )

    missing_information: list[str] = Field(default_factory=list)

    methodology_version: str = "1.0"

    # SIE Methodology v2 addition: distinguishes "same 28-dimension
    # architecture, refined/expanded anchor set" from "different dimension
    # set entirely". Empty for analyses run before this field existed
    # (never backfilled), consistent with every other provenance field's
    # "empty means not recorded, not fabricated" convention.
    anchor_registry_version: str = ""

    # --- Provenance (SIE Scoring Reliability sprint, Phase 5) ---
    #
    # Populated only for analyses run after this field set was added.
    # Every field here defaults to "empty" (not a fabricated value), so
    # loading an older stored methodology JSONB -- which never had these
    # keys -- leaves them blank rather than pretending that analysis
    # carried provenance it never actually recorded.

    # Version of the pillar-to-overall-SPS aggregation methodology
    # (pillar weights + weighted-average/renormalization formula in
    # app/ai/scoring_methodology.py and app/ai/investment_score.py).
    # Bump this whenever those change.
    scoring_version: str = ""

    # The OpenAI model used for the six pillar-analysis calls that
    # actually determine pillar scores (see app/ai/analyze_pillar.py).
    model_identifier: str = ""

    # Identifies which version of the pillar-analysis prompt architecture
    # (build_evidence_prompt() in app/ai/evidence_extraction.py and
    # build_scoring_prompt() in app/ai/pillar_scoring.py) produced this
    # analysis, so a future prompt change can be distinguished from a
    # genuine evidence or model change when explaining a score.
    prompt_version: str = ""

    # sha256 of the raw, as-submitted company_text. Lets a later
    # investigation confirm whether two analyses actually used identical
    # input without needing to diff the full text.
    company_text_hash: str = ""

    # The web search query research_enrichment.py generated from
    # company_text for this analysis.
    search_query: str = ""

    # The full research brief text that was appended to company_text to
    # form the enriched_text sent into pillar analysis.
    research_brief_snapshot: str = ""

    # The Tavily source list (title/url) used to build the research
    # brief above.
    source_snapshot: list[dict[str, str]] = Field(default_factory=list)

    # UTC ISO timestamp of when this analysis was produced. Distinct
    # from the analyses.created_at DB column (set at save time) so the
    # methodology JSONB is self-describing even outside the database row.
    analyzed_at: str = ""