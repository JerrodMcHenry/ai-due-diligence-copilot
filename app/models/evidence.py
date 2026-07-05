from pydantic import BaseModel
from typing import Literal


class Evidence(BaseModel):
    statement: str

    source: str | None = None

    source_type: Literal[
        "Pitch Deck",
        "Website",
        "Research",
        "User Input",
        "Financial Statement",
        "Unknown",
    ] = "Unknown"

    confidence: Literal[
        "Low",
        "Medium",
        "High",
    ] = "Medium"

    verified: bool = False