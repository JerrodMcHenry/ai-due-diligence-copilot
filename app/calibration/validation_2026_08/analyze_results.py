"""
Phase 10.11.1 -- SPS Real-Company Validation, Part 10-18.

Pure analysis over the raw results the runner already produced
(raw_results_summary.json + raw_results/*.json). Computes nothing SIE
itself doesn't already own -- no scoring, no methodology, read-only.

Run with (from repo root, backend venv active):
    python -m app.calibration.validation_2026_08.analyze_results
"""

import json
import statistics
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = RUN_DIR / "raw_results_summary.json"
ANALYSIS_OUTPUT_PATH = RUN_DIR / "analysis_output.json"

GROUP_ORDER = ["A", "B", "C"]
BUCKET_EDGES = [
    ("<40", float("-inf"), 40),
    ("40-49.9", 40, 50),
    ("50-59.9", 50, 60),
    ("60-69.9", 60, 70),
    ("70-79.9", 70, 80),
    ("80-89.9", 80, 90),
    ("90+", 90, float("inf")),
]


def bucket_counts(scores: list[float]) -> dict:
    counts = {label: 0 for label, _, _ in BUCKET_EDGES}
    for s in scores:
        for label, low, high in BUCKET_EDGES:
            if low <= s < high:
                counts[label] += 1
                break
    return counts


def describe(scores: list[float]) -> dict:
    if not scores:
        return {"count": 0}
    sorted_scores = sorted(scores)
    return {
        "count": len(scores),
        "min": min(scores),
        "max": max(scores),
        "mean": round(statistics.mean(scores), 2),
        "median": statistics.median(scores),
        "stdev": round(statistics.pstdev(scores), 2) if len(scores) > 1 else 0.0,
        "p25": round(percentile(sorted_scores, 0.25), 2),
        "p75": round(percentile(sorted_scores, 0.75), 2),
        "range": max(scores) - min(scores),
        "sorted": sorted_scores,
    }


def percentile(sorted_data: list[float], pct: float) -> float:
    if len(sorted_data) == 1:
        return sorted_data[0]
    k = (len(sorted_data) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return sorted_data[f]
    return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * (k - f)


def pairwise_dominance(group_x: list[float], group_y: list[float]) -> float | None:
    """Fraction of (x, y) pairs across the two groups where x > y."""
    if not group_x or not group_y:
        return None
    wins = 0
    total = 0
    for x in group_x:
        for y in group_y:
            total += 1
            if x > y:
                wins += 1
            elif x == y:
                wins += 0.5
    return round(wins / total, 3) if total else None


def spearman_rank_correlation(expected_ranks: list[int], actual_values: list[float]) -> float | None:
    """Plain Spearman rho, no external dependency (scipy not required)."""
    n = len(actual_values)
    if n < 2:
        return None

    def rank(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks

    rank_expected = rank(expected_ranks)
    rank_actual = rank(actual_values)

    d_squared_sum = sum((re - ra) ** 2 for re, ra in zip(rank_expected, rank_actual))
    rho = 1 - (6 * d_squared_sum) / (n * (n**2 - 1))
    return round(rho, 3)


def main() -> None:
    if not SUMMARY_PATH.exists():
        print(f"No results found at {SUMMARY_PATH} -- run the cohort first.")
        return

    with SUMMARY_PATH.open(encoding="utf-8") as f:
        all_records = json.load(f)

    completed = [r for r in all_records if r["status"] == "completed"]
    failed = [r for r in all_records if r["status"] != "completed"]

    print(f"Completed: {len(completed)} / {len(all_records)}")
    if failed:
        print("Failed companies:")
        for r in failed:
            print(f"  - {r['company']} ({r.get('error_stage')}): {r.get('error')}")

    overall_scores = [r["overall_score"] for r in completed]
    overall_stats = describe(overall_scores)
    overall_buckets = bucket_counts(overall_scores)

    print("\n=== OVERALL DISTRIBUTION ===")
    print(json.dumps(overall_stats, indent=2))
    print("Buckets:", overall_buckets)

    group_stats = {}
    group_scores = {}
    for group in GROUP_ORDER:
        scores = [r["overall_score"] for r in completed if r["expected_group"] == group]
        group_scores[group] = scores
        group_stats[group] = describe(scores)
        print(f"\n=== GROUP {group} ({len(scores)} companies) ===")
        print(json.dumps(group_stats[group], indent=2))

    print("\n=== GROUP SEPARATION ===")
    separation = {
        "median_A_vs_B": (group_stats["A"].get("median"), group_stats["B"].get("median")),
        "median_B_vs_C": (group_stats["B"].get("median"), group_stats["C"].get("median")),
        "mean_A_vs_B": (group_stats["A"].get("mean"), group_stats["B"].get("mean")),
        "mean_B_vs_C": (group_stats["B"].get("mean"), group_stats["C"].get("mean")),
        "P(A>B)": pairwise_dominance(group_scores["A"], group_scores["B"]),
        "P(A>C)": pairwise_dominance(group_scores["A"], group_scores["C"]),
        "P(B>C)": pairwise_dominance(group_scores["B"], group_scores["C"]),
    }
    print(json.dumps(separation, indent=2))

    group_rank = {"A": 3, "B": 2, "C": 1}
    expected_ranks = [group_rank[r["expected_group"]] for r in completed]
    rho = spearman_rank_correlation(expected_ranks, overall_scores)
    print(f"\nSpearman rank correlation (expected group vs SPS): {rho}")

    print("\n=== ORDERED SPS (all completed companies) ===")
    for r in sorted(completed, key=lambda r: r["overall_score"], reverse=True):
        print(f"{r['overall_score']:>5} | group {r['expected_group']} | {r['company']}")

    pillar_keys = ["market", "team", "product", "execution", "traction", "financial_health"]
    pillar_stats = {}
    for key in pillar_keys:
        scores = [r["pillars"][key]["score"] for r in completed if r["pillars"][key]["score"] is not None]
        pillar_stats[key] = describe(scores)
        pillar_stats[key]["n_unavailable"] = sum(1 for r in completed if r["pillars"][key]["score"] is None)

        by_group = {}
        for group in GROUP_ORDER:
            gscores = [
                r["pillars"][key]["score"]
                for r in completed
                if r["expected_group"] == group and r["pillars"][key]["score"] is not None
            ]
            by_group[group] = describe(gscores)
        pillar_stats[key]["by_group"] = by_group

    print("\n=== PILLAR DISCRIMINATION ===")
    for key, stats in pillar_stats.items():
        print(f"\n{key}: min={stats.get('min')} max={stats.get('max')} mean={stats.get('mean')} "
              f"median={stats.get('median')} stdev={stats.get('stdev')} unavailable={stats['n_unavailable']}")
        for group in GROUP_ORDER:
            g = stats["by_group"][group]
            print(f"    group {group}: mean={g.get('mean')} median={g.get('median')} n={g.get('count')}")

    # Evidence/confidence cross-tab
    print("\n=== EVIDENCE / CONFIDENCE ===")
    high_score_low_confidence = []
    for r in completed:
        low_conf_pillars = [k for k in pillar_keys if r["pillars"][k]["confidence"] == "Low"]
        if r["overall_score"] >= 75 and len(low_conf_pillars) >= 3:
            high_score_low_confidence.append({
                "company": r["company"],
                "overall_score": r["overall_score"],
                "low_confidence_pillars": low_conf_pillars,
            })
    print(f"Companies with SPS >= 75 AND >= 3 Low-confidence pillars: {len(high_score_low_confidence)}")
    for row in high_score_low_confidence:
        print(f"  - {row}")

    output = {
        "completed_count": len(completed),
        "failed_count": len(failed),
        "failed_companies": [{"company": r["company"], "error_stage": r.get("error_stage"), "error": r.get("error")} for r in failed],
        "overall_stats": overall_stats,
        "overall_buckets": overall_buckets,
        "group_stats": group_stats,
        "separation": separation,
        "spearman_rho": rho,
        "ordered": [
            {"company": r["company"], "expected_group": r["expected_group"], "overall_score": r["overall_score"]}
            for r in sorted(completed, key=lambda r: r["overall_score"], reverse=True)
        ],
        "pillar_stats": pillar_stats,
        "high_score_low_confidence": high_score_low_confidence,
    }

    with ANALYSIS_OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nFull analysis written to {ANALYSIS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
