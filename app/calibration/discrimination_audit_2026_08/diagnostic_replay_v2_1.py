"""
Phase 10.8B, Part 14 -- V2 vs V2.1 diagnostic replay.

Re-runs EXACTLY the six diagnostic companies from Phase 10.8A
(Rippling, Databricks, Plaid, Clubhouse, Relaw, Dome) through the NOW-
MODIFIED Methodology V2.1 pipeline, using the identical input procedure
as the frozen Phase 10.8 validation run (one real website URL each,
same evidence_sources convention, zero database writes -- same
isolation pattern as app/calibration/validation_2026_08/run_validation_cohort.py).

THIS IS NOT A BLIND VALIDATION. These six companies were used to
diagnose the V2 methodology (Phase 10.8A) and to motivate several of the
V2.1 changes below -- their results are contaminated for validation
purposes by construction. This script exists only to produce a
regression/diagnostic comparison (V2's frozen scores vs. V2.1's new
scores for the same six real companies), per Phase 10.8B Part 14's
explicit instruction. Do not cite this comparison as evidence that
V2.1 "passes" anything -- Phase 10.8C's new, independently-selected,
frozen cohort is what a real blind validation requires.

Writes to a NEW directory (diagnostic_replay_v2_1/) -- the frozen Phase
10.8 raw_results/ under validation_2026_08/ is never read for writing,
never modified, never overwritten.

Run with (repo root, backend venv active):
    python -m app.calibration.discrimination_audit_2026_08.diagnostic_replay_v2_1
"""

import json
import re
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.calibration.run_calibration import serialize_value
from app.website_scrapper import extract_text_from_website
from app.workflows.due_diligence_workflow import run_due_diligence

RUN_DIR = Path(__file__).resolve().parent
RAW_RESULTS_DIR = RUN_DIR / "diagnostic_replay_v2_1" / "raw_results"
SUMMARY_PATH = RUN_DIR / "diagnostic_replay_v2_1" / "summary.json"

FROZEN_V2_SCORES = {
    # Phase 10.8's frozen results, for the comparison table -- copied
    # from app/calibration/validation_2026_08/raw_results_summary.json,
    # never re-read/re-derived from that file at runtime, so this script
    # has zero risk of ever writing into the frozen V2 directory.
    "Rippling": 76.0,
    "Databricks": 67.7,
    "Plaid": 68.2,
    "Clubhouse": 64.9,
    "Relaw": 72.5,
    "Dome": 63.0,
}


@dataclass(frozen=True)
class DiagnosticCompany:
    name: str
    website: str


DIAGNOSTIC_COMPANIES = [
    DiagnosticCompany("Rippling", "https://www.rippling.com"),
    DiagnosticCompany("Databricks", "https://www.databricks.com"),
    DiagnosticCompany("Plaid", "https://plaid.com"),
    DiagnosticCompany("Clubhouse", "https://www.joinclubhouse.com"),
    DiagnosticCompany("Relaw", "https://www.relaw.ai"),
    DiagnosticCompany("Dome", "https://www.domeapi.io"),
]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def extract_pillar(sie_analysis, key: str) -> dict:
    pillar = getattr(sie_analysis, key)
    breakdown = pillar.score_breakdown
    return {
        "score": pillar.score,
        "confidence": pillar.confidence,
        "evidence_coverage": breakdown.evidence_coverage if breakdown else None,
    }


def run_one(company: DiagnosticCompany) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    record: dict = {
        "company": company.name,
        "website": company.website,
        "frozen_v2_sps": FROZEN_V2_SCORES.get(company.name),
        "started_at": started_at,
        "status": "failed",
    }

    try:
        website_text = extract_text_from_website(company.website)
    except Exception as error:
        record["error_stage"] = "website_extraction"
        record["error"] = str(error)
        return record

    try:
        results = run_due_diligence(
            website_text,
            analysis_type="public",
            evidence_sources=["website", "public_research"],
        )
    except Exception as error:
        record["error_stage"] = "run_due_diligence"
        record["error"] = str(error)
        record["traceback"] = traceback.format_exc()
        return record

    sie_analysis = results["sie_analysis"]

    record.update({
        "status": "completed",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "overall_score_v2_1": sie_analysis.startup_intelligence_score,
        "recommendation_v2_1": sie_analysis.startup_scorecard.recommendation,
        "company_stage_extracted": sie_analysis.context.company_stage,
        "methodology_version": sie_analysis.analysis_context.methodology_version
        if sie_analysis.analysis_context else None,
        "pillars_v2_1": {
            "market": extract_pillar(sie_analysis, "market"),
            "team": extract_pillar(sie_analysis, "team"),
            "product": extract_pillar(sie_analysis, "product"),
            "execution": extract_pillar(sie_analysis, "execution"),
            "traction": extract_pillar(sie_analysis, "traction"),
            "financial_health": extract_pillar(sie_analysis, "financial_health"),
        },
    })

    raw_path = RAW_RESULTS_DIR / f"{slugify(company.name)}.json"
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(serialize_value(results), f, indent=2, ensure_ascii=False)
    record["raw_report_path"] = str(raw_path.relative_to(RUN_DIR))

    return record


def main() -> None:
    RAW_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []
    if SUMMARY_PATH.exists():
        with SUMMARY_PATH.open(encoding="utf-8") as f:
            summary = json.load(f)
    completed_names = {row["company"] for row in summary if row.get("status") == "completed"}

    for index, company in enumerate(DIAGNOSTIC_COMPANIES, start=1):
        if company.name in completed_names:
            print(f"[{index}/{len(DIAGNOSTIC_COMPANIES)}] SKIP (already completed) {company.name}")
            continue

        print(f"[{index}/{len(DIAGNOSTIC_COMPANIES)}] Running {company.name} ({company.website}) under V2.1")
        start = time.monotonic()
        record = run_one(company)
        elapsed = time.monotonic() - start
        record["elapsed_seconds"] = round(elapsed, 1)

        status_line = (
            f"    -> {record['status']} in {elapsed:.0f}s"
            + (
                f", V2={record['frozen_v2_sps']} -> V2.1={record.get('overall_score_v2_1')}"
                if record["status"] == "completed"
                else f", error at {record.get('error_stage')}: {record.get('error')}"
            )
        )
        print(status_line)

        summary = [row for row in summary if row["company"] != company.name]
        summary.append(record)
        with SUMMARY_PATH.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    completed = sum(1 for row in summary if row["status"] == "completed")
    print(f"\nDone. {completed}/{len(DIAGNOSTIC_COMPANIES)} completed.")
    print(f"Summary written to {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
