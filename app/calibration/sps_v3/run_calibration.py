"""
Phase 10.8I -- baseline run, P0 grid search, holdout evaluation.

Zero network/LLM calls (evidence is already frozen in
calibration_evidence.py, gathered via WebSearch earlier in this phase's
execution, not re-fetched here). Zero database writes. Pure,
deterministic evaluation over the frozen 31-company roster.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from itertools import product

from app.calibration.sps_v3.aggregation import evaluate_sps
from app.calibration.sps_v3.calibration_evidence import CALIBRATION_COMPANIES, TODAY
from app.calibration.sps_v3.evaluators import evaluate_all_dimensions
from app.calibration.sps_v3.registry import DEFAULT_REGISTRY, ParameterRegistry

# The two historical companies get their own as-of reference_date;
# every other (current-state) company uses TODAY.
_REFERENCE_DATE_OVERRIDES = {
    "CAL-030": date(2020, 1, 1),   # Mailchimp
    "CAL-031": date(2021, 6, 1),   # Fast
}


def _reference_date_for(cal_id: str) -> date:
    return _REFERENCE_DATE_OVERRIDES.get(cal_id, TODAY)


def run_one(cal_id: str, registry: ParameterRegistry) -> dict:
    builder, split, outcome = CALIBRATION_COMPANIES[cal_id]
    company = builder()
    ref_date = _reference_date_for(cal_id)
    dims = evaluate_all_dimensions(company, registry, reference_date=ref_date)
    result = evaluate_sps(dims, company.stage, registry)
    return {
        "cal_id": cal_id,
        "company_id": company.company_id,
        "split": split,
        "stage": company.stage.value,
        "reference_date": ref_date.isoformat(),
        "sps": str(result.sps) if result.sps is not None else None,
        "publishable": result.publishable,
        "withhold_reason": result.withhold_reason,
        "coverage_pct": str(result.coverage.overall_pct),
        "confidence": result.confidence.overall.value,
        "pillars": {
            p.pillar: {
                "strength": str(p.strength) if p.strength is not None else None,
                "completeness_pct": str(p.completeness_pct),
                "confidence": p.confidence.value,
                "publishable": p.publishable,
            }
            for p in result.pillar_results
        },
        "dimensions": {
            d.dimension_id: {
                "score": str(d.score) if d.score is not None else None,
                "availability": d.availability.value,
                "classification": d.classification.classification if d.classification else None,
            }
            for d in dims
        },
        "outcome_data": outcome,
    }


def run_all(registry: ParameterRegistry, ids: list[str] | None = None) -> list[dict]:
    target_ids = ids if ids is not None else list(CALIBRATION_COMPANIES.keys())
    return [run_one(cal_id, registry) for cal_id in target_ids]


def training_ids() -> list[str]:
    return [k for k, (b, split, o) in CALIBRATION_COMPANIES.items() if split == "TRAINING"]


def holdout_ids() -> list[str]:
    return [k for k, (b, split, o) in CALIBRATION_COMPANIES.items() if split == "HOLDOUT"]


def summarize(records: list[dict]) -> dict:
    published = [r for r in records if r["publishable"]]
    withheld = [r for r in records if not r["publishable"]]
    sps_values = sorted(Decimal(r["sps"]) for r in published)
    return {
        "n": len(records),
        "published": len(published),
        "withheld": len(withheld),
        "sps_min": str(sps_values[0]) if sps_values else None,
        "sps_max": str(sps_values[-1]) if sps_values else None,
        "sps_mean": str(sum(sps_values) / len(sps_values)) if sps_values else None,
        "sps_sorted": [str(v) for v in sps_values],
    }


def main() -> None:
    # --- Part 5: pre-calibration baseline (current provisional params) ---
    baseline_training = run_all(DEFAULT_REGISTRY, training_ids())
    baseline_holdout = run_all(DEFAULT_REGISTRY, holdout_ids())

    out_dir_path = "app/calibration/sps_v3/calibration_baseline.json"
    with open(out_dir_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "phase": "10.8I",
                "label": "PRE-CALIBRATION BASELINE -- immutable, never overwritten",
                "parameters_used": {k: str(v.value) for k, v in DEFAULT_REGISTRY.all().items()},
                "training": baseline_training,
                "holdout": baseline_holdout,
                "training_summary": summarize(baseline_training),
                "holdout_summary": summarize(baseline_holdout),
            },
            f, indent=2,
        )
    print(f"Baseline written to {out_dir_path}")
    print("Training summary:", summarize(baseline_training))
    print("Holdout summary:", summarize(baseline_holdout))
    for r in baseline_training + baseline_holdout:
        print(f"  {r['cal_id']:<10} {r['company_id']:<30} split={r['split']:<9} sps={r['sps']} pub={r['publishable']} cov={r['coverage_pct']}% reason={r['withhold_reason']}")


if __name__ == "__main__":
    main()
