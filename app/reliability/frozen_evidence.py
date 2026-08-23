"""
Frozen evidence packet: the exact inputs one research-enrichment run
produced for a company, captured once so the reliability harness can
re-score the SAME evidence repeatedly without calling live research again.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@dataclass
class FrozenEvidencePacket:
    company_name: str

    # The exact original input, byte-for-byte.
    company_text: str

    # What research_enrichment.py produced from that company_text, at
    # capture time, with temperature=0.0 (Phase 1 fix already applied).
    search_query: str
    research_brief: str
    sources: list[dict]

    # The exact enriched_text that was actually sent into
    # analyze_pillars_from_enriched_text() -- this is the frozen evidence
    # itself. Reconstructing it from the other fields must reproduce this
    # exact string; it is stored explicitly rather than only implied, so a
    # change to build_enriched_text()'s format can never silently change
    # what a previously-captured fixture replays.
    enriched_text: str

    # Captured once from generate_structured_analysis(enriched_text) at
    # fixture-capture time and reused across every repeated scoring run.
    # This only supplies SIEContext display metadata (company_name,
    # industry, business_model, stage) -- it is never fed into the six
    # pillar-analysis prompts and has no effect on pillar scores or SPS
    # (see app/ai/*_analysis.py: each pillar analyzer takes only
    # enriched_text). Freezing it too avoids introducing an unrelated,
    # unmeasured source of LLM variance into the reliability loop.
    structured_analysis: dict

    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def save(self, name: str) -> Path:
        FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
        path = FIXTURES_DIR / f"{name}.json"

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

        return path

    @classmethod
    def load(cls, name: str) -> "FrozenEvidencePacket":
        path = FIXTURES_DIR / f"{name}.json"

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)
