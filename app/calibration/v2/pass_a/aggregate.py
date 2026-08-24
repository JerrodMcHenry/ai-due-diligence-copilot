"""
PASS A aggregation: dimension -> pillar -> SPS, using ONLY the canonical
missing-evidence and aggregation rules from SIE_Methodology_v2_Specification.md
(Parts 4 and 9). No below-average missing-evidence defaults. No tuning.

Run with:
    .venv/bin/python3 -m app.calibration.v2.pass_a.aggregate
"""

import json
from pathlib import Path

from app.calibration.v2.scorer import DIM_WEIGHTS, PILLAR_WEIGHTS, UNAVAILABLE_STATES

RESULTS_DIR = Path(__file__).resolve().parent / "results"
OUT_PATH = Path(__file__).resolve().parent / "aggregate_results.json"


def aggregate_pillar(dimensions: list[dict], pillar: str) -> dict:
    pillar_dims = [d for d in dimensions if d["pillar"] == pillar]
    scored = [d for d in pillar_dims if d["evidence_status"] not in UNAVAILABLE_STATES
              and d["score"] is not None]
    unavailable = [d for d in pillar_dims if d["evidence_status"] in UNAVAILABLE_STATES]
    na = [d for d in pillar_dims if d["evidence_status"] == "not_applicable"]
    calib_blocked = [d for d in pillar_dims if d["score"] is None
                      and d["evidence_status"] not in UNAVAILABLE_STATES]

    weights = DIM_WEIGHTS[pillar]
    total_w = sum(weights[d["dimension"]] for d in scored)

    if not scored or total_w == 0:
        return {
            "pillar": pillar,
            "scoreable_dimensions": [],
            "unavailable_dimensions": [d["dimension"] for d in unavailable],
            "na_dimensions": [d["dimension"] for d in na],
            "calibration_blocked_dimensions": [d["dimension"] for d in calib_blocked],
            "pillar_score": None,
            "pillar_score_suppressed_reason": "No dimension in this pillar produced a defensible score for this company.",
            "coverage_pct": round(100 * len(scored) / max(1, len(pillar_dims) - len(na)), 1),
        }

    weighted_sum = sum(d["score"] * weights[d["dimension"]] for d in scored)
    pillar_score = weighted_sum / total_w

    confidences = [d["confidence"] for d in scored if d["confidence"]]
    high = confidences.count("High")
    low = sum(1 for c in confidences if c and c.startswith("Low"))
    in_scope = len(pillar_dims) - len(na)
    coverage = len(scored) / in_scope if in_scope else 0.0

    if coverage >= 0.6 and high >= len(confidences) * 0.5 and low == 0:
        pillar_conf = "High"
    elif low > len(confidences) * 0.5 or coverage < 0.3:
        pillar_conf = "Low"
    else:
        pillar_conf = "Medium"

    return {
        "pillar": pillar,
        "scoreable_dimensions": [d["dimension"] for d in scored],
        "unavailable_dimensions": [d["dimension"] for d in unavailable],
        "na_dimensions": [d["dimension"] for d in na],
        "calibration_blocked_dimensions": [d["dimension"] for d in calib_blocked],
        "pillar_score": round(pillar_score, 2),
        "pillar_confidence": pillar_conf,
        "coverage_pct": round(100 * coverage, 1),
    }


def aggregate_company(result: dict) -> dict:
    dims = result["dimensions"]
    pillars = {p: aggregate_pillar(dims, p) for p in PILLAR_WEIGHTS}

    scored_pillars = {p: r for p, r in pillars.items() if r.get("pillar_score") is not None}
    total_w = sum(PILLAR_WEIGHTS[p] for p in scored_pillars)

    overall_coverage_scored = sum(len(r["scoreable_dimensions"]) for r in pillars.values())
    overall_coverage_in_scope = sum(
        len(r["scoreable_dimensions"]) + len(r["unavailable_dimensions"]) + len(r.get("calibration_blocked_dimensions", []))
        for r in pillars.values()
    )
    overall_coverage_pct = round(
        100 * overall_coverage_scored / max(1, overall_coverage_in_scope), 1
    )

    if not scored_pillars or total_w == 0:
        sps = None
        sps_reason = "No pillar produced a defensible score."
    else:
        sps_raw = sum(r["pillar_score"] * PILLAR_WEIGHTS[p] for p, r in scored_pillars.items()) / total_w
        sps = round(sps_raw * 10, 1)  # pillar scores are 0-10; SPS displayed 0-100
        sps_reason = None

    diligence_flag_count = sum(
        1 for d in dims
        if d["evidence_status"] == "expected_unavailable"
        or (d["score"] is None and d["evidence_status"] not in UNAVAILABLE_STATES)
    )

    return {
        "company_name": result["company_name"],
        "filename": result["filename"],
        "pillars": pillars,
        "sps": sps,
        "sps_suppressed_reason": sps_reason,
        "overall_coverage_pct": overall_coverage_pct,
        "diligence_flag_count": diligence_flag_count,
        "pillars_unavailable_entirely": [p for p in PILLAR_WEIGHTS if p not in scored_pillars],
    }


def main() -> None:
    files = sorted(RESULTS_DIR.glob("*.json"))
    all_results = []
    for f in files:
        with open(f) as fh:
            result = json.load(fh)
        all_results.append(aggregate_company(result))

    with open(OUT_PATH, "w") as fh:
        json.dump(all_results, fh, indent=2)

    print(f"Aggregated {len(all_results)} companies -> {OUT_PATH}")
    for r in all_results:
        sps_str = f"SPS={r['sps']}" if r["sps"] is not None else f"SPS=SUPPRESSED ({r['sps_suppressed_reason']})"
        print(f"  {r['company_name']:20s} {sps_str:35s} coverage={r['overall_coverage_pct']}% flags={r['diligence_flag_count']}")


if __name__ == "__main__":
    main()
