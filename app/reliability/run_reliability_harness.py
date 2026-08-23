"""
Runs a frozen evidence fixture through score_frozen_evidence() N times and
reports reliability statistics against the sprint's gates.

No live research is called during the loop -- every run scores the exact
same enriched_text via analyze_pillars_from_enriched_text(). Any variance
observed is therefore attributable to LLM-call variance and/or evidence-
validator/scoring behavior, not to research or query nondeterminism.

Usage:
    python -m app.reliability.run_reliability_harness novaledger --runs 10 --label before
"""

import argparse
import json
from pathlib import Path

from app.reliability.frozen_evidence import FrozenEvidencePacket
from app.reliability.harness import score_frozen_evidence
from app.reliability.stats import compute_stats, evaluate_gates, serialize_run

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def run(name: str, n_runs: int, label: str) -> dict:
    packet = FrozenEvidencePacket.load(name)

    print(f"\nReliability harness: {name} ({label})")
    print(f"Frozen evidence captured at: {packet.captured_at}")
    print(f"Running {n_runs} scoring passes over identical enriched_text...")
    print("-" * 72)

    raw_runs = []

    for i in range(1, n_runs + 1):
        analysis = score_frozen_evidence(packet)
        run_result = serialize_run(analysis)
        raw_runs.append(run_result)

        print(
            f"Run {i:>2}/{n_runs}: overall SPS = {run_result['overall_sps']}  "
            + "  ".join(
                f"{p[:4]}={run_result['pillars'][p]['score']}"
                for p in run_result["pillars"]
            )
        )

    stats = compute_stats(raw_runs)
    gate_result = evaluate_gates(stats)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{name}_{label}.json"

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "fixture": name,
                "label": label,
                "n_runs": n_runs,
                "raw_runs": raw_runs,
                "stats": stats,
                "gates": gate_result,
            },
            f,
            indent=2,
            default=str,
        )

    print("-" * 72)
    print(f"Report saved: {report_path}")
    print()
    print(
        f"Overall SPS: min={stats['overall_sps']['min']} "
        f"max={stats['overall_sps']['max']} "
        f"range={stats['overall_sps']['range']} "
        f"stdev={stats['overall_sps']['stdev']}"
    )
    print()
    print("Gate results:")
    for g in gate_result["gates"]:
        status = "PASS" if g["passed"] else "FAIL"
        print(f"  [{status}] {g['gate']}: {g['value']}")
    print()
    print(
        "SPRINT GATE: "
        + ("ALL PASSED" if gate_result["all_passed"] else "FAILURES PRESENT")
    )

    return {
        "raw_runs": raw_runs,
        "stats": stats,
        "gates": gate_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Fixture name, e.g. novaledger")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--label", default="run")
    args = parser.parse_args()

    run(args.name, args.runs, args.label)


if __name__ == "__main__":
    main()
