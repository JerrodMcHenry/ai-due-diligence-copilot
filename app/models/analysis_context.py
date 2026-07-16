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