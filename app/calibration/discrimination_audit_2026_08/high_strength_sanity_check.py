"""
V2.1 high-strength sanity check (post-Phase 10.8B, pre-10.8C).

Runs exactly the three companies recorded ex ante in
HIGH_STRENGTH_SANITY_EXANTE.md (Stripe, Canva, SpaceX) through the
UNMODIFIED, frozen production V2.1 pipeline -- same
extract_text_from_website() -> run_due_diligence() call shape as every
other calibration/validation harness in this repo, zero database writes.

This script does NOT modify methodology/scoring/anchors/confidence-caps/
research/evidence-rule/weight code in any way. It observes two existing
functions (apply_confidence_score_cap, apply_provenance_guard) by
monkeypatching the NAME each already-unmodified caller module bound at
import time, with a wrapper that calls straight through to the real,
untouched function and only additionally records what went in and what
came out -- the return value used by the real pipeline is always the
real function's own return value, unchanged. This is the same
unittest.mock.patch technique already used throughout app/tests/, applied
here for observation instead of substitution.

Run with (repo root, backend venv active):
    python -m app.calibration.discrimination_audit_2026_08.high_strength_sanity_check
"""

import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import app.ai.analyze_pillar as analyze_pillar_module
import app.ai.evidence_extraction as evidence_extraction_module
from app.ai.scoring import apply_confidence_score_cap as real_apply_confidence_score_cap
from app.ai.evidence_provenance import apply_provenance_guard as real_apply_provenance_guard
from app.calibration.run_calibration import serialize_value
from app.website_scrapper import extract_text_from_website
from app.workflows.due_diligence_workflow import run_due_diligence

RUN_DIR = Path(__file__).resolve().parent
OUT_DIR = RUN_DIR / "high_strength_sanity_check"
RAW_DIR = OUT_DIR / "raw_results"


@dataclass(frozen=True)
class SanityCompany:
    name: str
    website: str


COMPANIES = [
    SanityCompany("Stripe", "https://stripe.com"),
    SanityCompany("Canva", "https://www.canva.com"),
    SanityCompany("SpaceX", "https://www.spacex.com"),
]


# Per-call-site instrumentation state, reset before each company.
_cap_log: list[dict] = []
_provenance_log: list[dict] = []


def _instrumented_cap(subscores):
    before = {s.name: (s.score, s.confidence) for s in subscores}
    result = real_apply_confidence_score_cap(subscores)
    for sub in result:
        pre_score, confidence = before.get(sub.name, (None, None))
        activated = (
            pre_score is not None
            and sub.score is not None
            and sub.score != pre_score
        )
        _cap_log.append({
            "dimension": sub.name,
            "confidence": confidence,
            "score_before_cap": pre_score,
            "score_after_cap": sub.score,
            "cap_activated": activated,
        })
    return result


def _instrumented_provenance(dimensions, company_text):
    before = {d.dimension: (list(d.evidence), list(d.signals), d.evidence_status) for d in dimensions}
    new_dimensions, altered = real_apply_provenance_guard(dimensions, company_text)
    for dim in new_dimensions:
        pre_evidence, pre_signals, pre_status = before.get(dim.dimension, ([], [], None))
        if dim.dimension in altered:
            dropped_evidence = [e for e in pre_evidence if e not in dim.evidence]
            dropped_signals = [s for s in pre_signals if s not in dim.signals]
            _provenance_log.append({
                "dimension": dim.dimension,
                "status_before": pre_status,
                "status_after": dim.evidence_status,
                "dropped_evidence": dropped_evidence,
                "dropped_signals": dropped_signals,
            })
    return new_dimensions, altered


def extract_pillar_detail(sie_analysis, key: str) -> dict:
    pillar = getattr(sie_analysis, key)
    breakdown = pillar.score_breakdown
    subscores = []
    if breakdown:
        for sub in breakdown.subscores:
            subscores.append({
                "name": sub.name,
                "score": sub.score,
                "weight": sub.weight,
                "confidence": sub.confidence,
                "evidence_status": sub.evidence_status,
                "score_corrected": sub.score_corrected,
                "evidence_corrected": sub.evidence_corrected,
                "evidence": sub.evidence,
                "rationale": sub.rationale,
                "missing_information": sub.missing_information,
            })
    return {
        "pillar_score": pillar.score,
        "pillar_confidence": pillar.confidence,
        "evidence_coverage": breakdown.evidence_coverage if breakdown else None,
        "subscores": subscores,
    }


def run_one(company: SanityCompany) -> dict:
    global _cap_log, _provenance_log
    _cap_log = []
    _provenance_log = []

    record: dict = {"company": company.name, "website": company.website, "status": "failed"}

    try:
        website_text = extract_text_from_website(company.website)
    except Exception as error:
        record["error_stage"] = "website_extraction"
        record["error"] = str(error)
        return record

    with patch.object(
        analyze_pillar_module, "apply_confidence_score_cap", side_effect=_instrumented_cap
    ), patch.object(
        evidence_extraction_module, "apply_provenance_guard", side_effect=_instrumented_provenance
    ):
        try:
            results = run_due_diligence(
                website_text,
                analysis_type="public",
                evidence_sources=["website", "public_research"],
            )
        except Exception as error:
            record["error_stage"] = "run_due_diligence"
            record["error"] = str(error)
            return record

    sie_analysis = results["sie_analysis"]

    record.update({
        "status": "completed",
        "overall_score": sie_analysis.startup_intelligence_score,
        "recommendation": sie_analysis.startup_scorecard.recommendation,
        "company_stage_extracted": sie_analysis.context.company_stage,
        "methodology_version": (
            sie_analysis.analysis_context.methodology_version if sie_analysis.analysis_context else None
        ),
        "pillars": {
            key: extract_pillar_detail(sie_analysis, key)
            for key in ("market", "team", "product", "execution", "traction", "financial_health")
        },
        "confidence_cap_log": list(_cap_log),
        "provenance_guard_log": list(_provenance_log),
    })

    raw_path = RAW_DIR / f"{company.name.lower()}.json"
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(serialize_value(results), f, indent=2, ensure_ascii=False)
    record["raw_report_path"] = str(raw_path.relative_to(RUN_DIR))

    return record


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    summary = []

    for i, company in enumerate(COMPANIES, start=1):
        print(f"[{i}/{len(COMPANIES)}] Running {company.name} ({company.website})")
        record = run_one(company)
        status = record["status"]
        if status == "completed":
            print(f"    -> completed, SPS={record['overall_score']}, stage={record['company_stage_extracted']}")
        else:
            print(f"    -> failed at {record.get('error_stage')}: {record.get('error')}")
        summary.append(record)

    summary_path = OUT_DIR / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nDone. Summary written to {summary_path}")


if __name__ == "__main__":
    main()
