"""
Phase 10.11.1 -- SPS Real-Company Validation, Part 7/8/9.

Runs the frozen 30-company cohort (cohort.py) through the EXACT SAME
production scoring pipeline POST /analyze uses for a website-only
submission -- extract_text_from_website() then run_due_diligence(),
identical functions, identical arguments shape, identical evidence_sources
convention (see app/api.py's own analyze_unified() for the reference this
mirrors). This is the existing calibration harness's own architecture
(app/calibration/run_calibration.py: run_due_diligence() called directly,
zero database writes), reused rather than reinvented, extended only to
loop a cohort and add group-comparison analysis on top afterward.

ISOLATION (Part 8): this script calls save_analysis()/save_score_history()/
get_or_create_startup() NOWHERE -- grep this file, there is no import from
app.database.db at all. Every result is serialized straight to a JSON file
under raw_results/. Nothing here can create a canonical startup, touch
Rankings, or touch Discovery.

INPUT CONSISTENCY (Part 7): every company gets exactly one real website
URL and nothing else -- no manually written company_text, no hand-picked
supplemental context. Whatever run_due_diligence()'s own existing
research-enrichment step (Tavily, via enrich_research()) finds on its own
is the same for every company, exactly as it already works for any real
user submitting only a website.

Each company is INDEPENDENT: one company's extraction/pipeline failure is
recorded and the run continues -- Part 9's "run all companies" is not
allowed to mean "abandon the cohort because company #14 timed out."

Run with (from repo root, backend venv active):
    python -m app.calibration.validation_2026_08.run_validation_cohort
"""

import json
import re
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from app.calibration.run_calibration import serialize_value
from app.calibration.validation_2026_08.cohort import COHORT
from app.website_scrapper import extract_text_from_website
from app.workflows.due_diligence_workflow import run_due_diligence

RUN_DIR = Path(__file__).resolve().parent
RAW_RESULTS_DIR = RUN_DIR / "raw_results"
SUMMARY_PATH = RUN_DIR / "raw_results_summary.json"


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


def run_one(company) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    record: dict = {
        "company": company.name,
        "website": company.website,
        "expected_group": company.expected_group,
        "stage_hypothesis": company.stage_hypothesis,
        "started_at": started_at,
        "status": "failed",
    }

    try:
        website_text = extract_text_from_website(company.website)
    except Exception as error:
        record["error_stage"] = "website_extraction"
        record["error"] = str(error)
        return record

    record["website_text_length"] = len(website_text)

    # Mirrors app/api.py::analyze_unified()'s own evidence_sources
    # convention exactly for a website-only submission: ["website",
    # "public_research"] -- public_research is always present because
    # enrich_research() always runs inside run_due_diligence() itself.
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
        "overall_score": sie_analysis.startup_intelligence_score,
        "recommendation": sie_analysis.startup_scorecard.recommendation,
        "company_stage_extracted": sie_analysis.context.company_stage,
        "industry_extracted": sie_analysis.context.industry,
        "methodology_version": sie_analysis.analysis_context.methodology_version
        if sie_analysis.analysis_context else None,
        "scoring_version": sie_analysis.analysis_context.scoring_version
        if sie_analysis.analysis_context else None,
        "pillars": {
            "market": extract_pillar(sie_analysis, "market"),
            "team": extract_pillar(sie_analysis, "team"),
            "product": extract_pillar(sie_analysis, "product"),
            "execution": extract_pillar(sie_analysis, "execution"),
            "traction": extract_pillar(sie_analysis, "traction"),
            "financial_health": extract_pillar(sie_analysis, "financial_health"),
        },
    })

    # Full raw serialized result, same convention as
    # app/calibration/run_calibration.py::save_report() -- kept per
    # company for later re-inspection (Part 16 outlier investigation).
    raw_path = RAW_RESULTS_DIR / f"{slugify(company.name)}.json"
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(serialize_value(results), f, indent=2, ensure_ascii=False)

    record["raw_report_path"] = str(raw_path.relative_to(RUN_DIR))

    return record


def main() -> None:
    RAW_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []

    # Resume support: if this script is re-run after a partial failure,
    # don't re-spend paid API calls on companies already completed.
    if SUMMARY_PATH.exists():
        with SUMMARY_PATH.open(encoding="utf-8") as f:
            summary = json.load(f)
    completed_names = {row["company"] for row in summary if row.get("status") == "completed"}

    for index, company in enumerate(COHORT, start=1):
        if company.name in completed_names:
            print(f"[{index}/{len(COHORT)}] SKIP (already completed) {company.name}")
            continue

        print(f"[{index}/{len(COHORT)}] Running {company.name} ({company.website}) -- expected group {company.expected_group}")
        start = time.monotonic()

        record = run_one(company)

        elapsed = time.monotonic() - start
        record["elapsed_seconds"] = round(elapsed, 1)

        status_line = (
            f"    -> {record['status']} in {elapsed:.0f}s"
            + (f", SPS={record.get('overall_score')}" if record["status"] == "completed" else f", error at {record.get('error_stage')}: {record.get('error')}")
        )
        print(status_line)

        # Replace any prior (failed) record for this company, then persist
        # immediately after every single company -- a crash partway
        # through the cohort must not lose already-completed results.
        summary = [row for row in summary if row["company"] != company.name]
        summary.append(record)
        with SUMMARY_PATH.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    completed = sum(1 for row in summary if row["status"] == "completed")
    failed = sum(1 for row in summary if row["status"] == "failed")
    print(f"\nDone. {completed}/{len(COHORT)} completed, {failed}/{len(COHORT)} failed.")
    print(f"Summary written to {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
