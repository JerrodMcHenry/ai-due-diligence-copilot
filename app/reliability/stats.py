"""
Serialization and variance/flip-rate statistics for the reliability
harness. No LLM calls here -- pure computation over already-collected
run results.
"""

import statistics
from typing import Any

from app.models.startup import SIEMethodologyAnalysis

PILLAR_NAMES = [
    "market",
    "team",
    "product",
    "execution",
    "traction",
    "financial_health",
]


def serialize_run(analysis: SIEMethodologyAnalysis) -> dict[str, Any]:
    """
    Reduce one scoring run to the fields the reliability gates care
    about, plus (Evidence/Scoring Separation sprint, Phase 6) enough
    per-subscore detail to distinguish evidence drift, classification
    drift, reasoning drift, and numeric-score drift in later analysis:
    the evidence list, extracted signals, rationale, and whether either
    stage required a scoped correction for that dimension.

    Purely additive over the prior shape (score/evidence_status/
    confidence) -- old reports remain readable by compute_stats() below,
    since it only reads the fields that existed before.
    """
    pillars: dict[str, Any] = {}

    for pillar_name in PILLAR_NAMES:
        pillar = getattr(analysis, pillar_name)
        breakdown = pillar.score_breakdown

        subscores = {
            subscore.name: {
                "score": subscore.score,
                "evidence_status": subscore.evidence_status,
                "confidence": subscore.confidence,
                "evidence": list(subscore.evidence),
                "signals": list(subscore.signals),
                "rationale": subscore.rationale,
                "evidence_corrected": subscore.evidence_corrected,
                "score_corrected": subscore.score_corrected,
            }
            for subscore in breakdown.subscores
        }

        pillars[pillar_name] = {
            "score": pillar.score,
            "confidence": pillar.confidence,
            "evidence_coverage": breakdown.evidence_coverage,
            "subscores": subscores,
        }

    return {
        "overall_sps": analysis.startup_intelligence_score,
        "pillars": pillars,
    }


def _range_stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "max": None, "range": None, "stdev": None}

    return {
        "min": min(values),
        "max": max(values),
        "range": round(max(values) - min(values), 4),
        "stdev": (
            round(statistics.pstdev(values), 4)
            if len(values) > 1
            else 0.0
        ),
    }


def compute_stats(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """
    runs: list of serialize_run() outputs, one per repeated scoring run
    of the SAME frozen evidence.
    """
    n = len(runs)

    overall_sps_values = [r["overall_sps"] for r in runs]
    overall_sps_stats = _range_stats(overall_sps_values)

    pillar_stats: dict[str, Any] = {}
    pillar_confidence_flips = 0
    null_pillar_flips = 0

    subscore_stats: dict[str, Any] = {}
    evidence_status_flips = 0
    subscore_confidence_flips = 0
    evidence_content_flips = 0
    signal_content_flips = 0
    total_subscores_seen = 0
    evidence_correction_events = 0
    score_correction_events = 0
    total_subscore_runs = 0

    for pillar_name in PILLAR_NAMES:
        scores = [
            r["pillars"][pillar_name]["score"]
            for r in runs
            if r["pillars"][pillar_name]["score"] is not None
        ]
        is_none_states = {
            r["pillars"][pillar_name]["score"] is None for r in runs
        }
        confidences = {
            r["pillars"][pillar_name]["confidence"] for r in runs
        }

        pillar_flips_null = len(is_none_states) > 1
        pillar_flips_confidence = len(confidences) > 1

        if pillar_flips_null:
            null_pillar_flips += 1
        if pillar_flips_confidence:
            pillar_confidence_flips += 1

        pillar_stats[pillar_name] = {
            **_range_stats(scores),
            "scored_in_n_of_n_runs": f"{len(scores)}/{n}",
            "confidence_values_seen": sorted(confidences),
            "confidence_flipped": pillar_flips_confidence,
            "null_status_flipped": pillar_flips_null,
        }

        # Subscore-level stats, keyed by "pillar/name".
        subscore_names = sorted(
            {
                name
                for r in runs
                for name in r["pillars"][pillar_name]["subscores"]
            }
        )

        for name in subscore_names:
            key = f"{pillar_name}/{name}"
            total_subscores_seen += 1

            entries = [
                r["pillars"][pillar_name]["subscores"].get(name)
                for r in runs
            ]
            entries = [e for e in entries if e is not None]

            scores_ = [e["score"] for e in entries if e["score"] is not None]
            statuses = {e["evidence_status"] for e in entries}
            confidences_ = {e["confidence"] for e in entries}

            status_flipped = len(statuses) > 1
            confidence_flipped = len(confidences_) > 1

            if status_flipped:
                evidence_status_flips += 1
            if confidence_flipped:
                subscore_confidence_flips += 1

            # Evidence-content / extracted-fact drift (Phase 6): did the
            # actual evidence quotes or extracted signals change across
            # runs, independent of whether evidence_status or score
            # changed? Order-independent (a set), since which fact gets
            # listed first is not meaningful drift.
            evidence_sets = {
                frozenset(e.get("evidence", [])) for e in entries
            }
            signal_sets = {
                frozenset(e.get("signals", [])) for e in entries
            }

            evidence_flipped = len(evidence_sets) > 1
            signal_flipped = len(signal_sets) > 1

            if evidence_flipped:
                evidence_content_flips += 1
            if signal_flipped:
                signal_content_flips += 1

            evidence_corrected_count = sum(
                1 for e in entries if e.get("evidence_corrected")
            )
            score_corrected_count = sum(
                1 for e in entries if e.get("score_corrected")
            )
            evidence_correction_events += evidence_corrected_count
            score_correction_events += score_corrected_count
            total_subscore_runs += len(entries)

            subscore_stats[key] = {
                **_range_stats(scores_),
                "evidence_status_values_seen": sorted(statuses),
                "evidence_status_flipped": status_flipped,
                "confidence_values_seen": sorted(confidences_),
                "confidence_flipped": confidence_flipped,
                "evidence_content_flipped": evidence_flipped,
                "signal_content_flipped": signal_flipped,
                "evidence_corrections": f"{evidence_corrected_count}/{len(entries)}",
                "score_corrections": f"{score_corrected_count}/{len(entries)}",
            }

    return {
        "n_runs": n,
        "overall_sps": overall_sps_stats,
        "pillars": pillar_stats,
        "subscores": subscore_stats,
        "flip_rates": {
            "evidence_status_flip_rate": round(
                evidence_status_flips / total_subscores_seen, 4
            ) if total_subscores_seen else 0.0,
            "evidence_status_flips": evidence_status_flips,
            "subscore_count": total_subscores_seen,
            "pillar_confidence_flip_rate": round(
                pillar_confidence_flips / len(PILLAR_NAMES), 4
            ),
            "pillar_confidence_flips": pillar_confidence_flips,
            "subscore_confidence_flip_rate": round(
                subscore_confidence_flips / total_subscores_seen, 4
            ) if total_subscores_seen else 0.0,
            "subscore_confidence_flips": subscore_confidence_flips,
            "null_pillar_flip_rate": round(
                null_pillar_flips / len(PILLAR_NAMES), 4
            ),
            "null_pillar_flips": null_pillar_flips,
            "evidence_content_flip_rate": round(
                evidence_content_flips / total_subscores_seen, 4
            ) if total_subscores_seen else 0.0,
            "evidence_content_flips": evidence_content_flips,
            "extracted_fact_flip_rate": round(
                signal_content_flips / total_subscores_seen, 4
            ) if total_subscores_seen else 0.0,
            "extracted_fact_flips": signal_content_flips,
            "evidence_correction_frequency": round(
                evidence_correction_events / total_subscore_runs, 4
            ) if total_subscore_runs else 0.0,
            "evidence_correction_events": evidence_correction_events,
            "score_correction_frequency": round(
                score_correction_events / total_subscore_runs, 4
            ) if total_subscore_runs else 0.0,
            "score_correction_events": score_correction_events,
        },
    }


# Initial reliability gates (Scoring Reliability sprint, Phase 3).
GATES = {
    "overall_sps_range_max": 1.0,
    "overall_sps_range_target": 0.5,
    "pillar_score_range_max": 0.2,
    "evidence_status_flip_rate_max": 0.0,
    "pillar_confidence_flip_rate_max": 0.0,
    "null_pillar_flip_rate_max": 0.0,
}


def evaluate_gates(stats: dict[str, Any]) -> dict[str, Any]:
    results = []

    sps_range = stats["overall_sps"]["range"]
    results.append({
        "gate": "Overall SPS range <= 1.0",
        "value": sps_range,
        "passed": sps_range is not None and sps_range <= GATES["overall_sps_range_max"],
        "meets_target_0.5": sps_range is not None and sps_range <= GATES["overall_sps_range_target"],
    })

    worst_pillar_range = 0.0
    worst_pillar_name = None
    for name, s in stats["pillars"].items():
        if s["range"] is not None and s["range"] > worst_pillar_range:
            worst_pillar_range = s["range"]
            worst_pillar_name = name

    results.append({
        "gate": "Pillar score range <= 0.2 (worst pillar)",
        "value": worst_pillar_range,
        "worst_pillar": worst_pillar_name,
        "passed": worst_pillar_range <= GATES["pillar_score_range_max"],
    })

    fr = stats["flip_rates"]

    results.append({
        "gate": "Evidence-status flip rate == 0%",
        "value": fr["evidence_status_flip_rate"],
        "passed": fr["evidence_status_flip_rate"] <= GATES["evidence_status_flip_rate_max"],
    })

    results.append({
        "gate": "Pillar confidence flip rate == 0",
        "value": fr["pillar_confidence_flip_rate"],
        "passed": fr["pillar_confidence_flip_rate"] <= GATES["pillar_confidence_flip_rate_max"],
    })

    results.append({
        "gate": "Null/Unavailable pillar flip rate == 0",
        "value": fr["null_pillar_flip_rate"],
        "passed": fr["null_pillar_flip_rate"] <= GATES["null_pillar_flip_rate_max"],
    })

    return {
        "gates": results,
        "all_passed": all(r["passed"] for r in results),
    }
