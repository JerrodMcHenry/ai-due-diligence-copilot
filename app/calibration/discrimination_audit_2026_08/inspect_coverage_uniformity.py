"""
Phase 10.8A -- SPS Discrimination Audit, read-only support script.

Reproduces this audit's headline finding: three of six pillars show an
*exact*, decimal-identical evidence_coverage percentage across the
entire frozen 25-company real-company cohort from
app/calibration/validation_2026_08/raw_results_summary.json.

This script:
  - never writes to canonical startup/analyses tables (no DB import at all)
  - never invokes run_due_diligence() or any LLM call -- reads only the
    already-frozen raw_results_summary.json from Phase 10.8
  - never modifies that file or anything under validation_2026_08/
  - never touches methodology/scoring code

Run with (repo root, backend venv active):
    python -m app.calibration.discrimination_audit_2026_08.inspect_coverage_uniformity
"""

import json
from collections import Counter
from pathlib import Path

SUMMARY_PATH = (
    Path(__file__).resolve().parent.parent
    / "validation_2026_08"
    / "raw_results_summary.json"
)

PILLAR_KEYS = ["market", "team", "product", "execution", "traction", "financial_health"]


def main() -> None:
    if not SUMMARY_PATH.exists():
        print(f"No frozen results found at {SUMMARY_PATH}.")
        return

    with SUMMARY_PATH.open(encoding="utf-8") as f:
        records = json.load(f)

    completed = [r for r in records if r["status"] == "completed"]
    print(f"Inspecting {len(completed)} completed companies (read-only, no re-run).\n")

    for key in PILLAR_KEYS:
        coverages = [r["pillars"][key]["evidence_coverage"] for r in completed]
        counts = Counter(coverages)
        distinct = len(counts)
        print(f"{key:<18} distinct evidence_coverage values: {distinct}")
        for value, count in sorted(counts.items()):
            pct = 100 * count / len(completed)
            flag = "  <-- structural constant" if count == len(completed) else ""
            print(f"    {value:>6}%  x {count:>2}/{len(completed)} ({pct:.0f}%){flag}")
        print()

    print(
        "A pillar whose evidence_coverage is identical for every company\n"
        "regardless of real size/stage/quality indicates a fixed subset of\n"
        "that pillar's dimensions structurally never scoring from website-\n"
        "sourced input -- see SPS_DISCRIMINATION_AUDIT.md Sections 1 and 15\n"
        "for the dimension-level trace (Traction's Deterministic dimensions,\n"
        "Financial Health's Runway + Unit Economics, Team's Founder-Market Fit)."
    )


if __name__ == "__main__":
    main()
