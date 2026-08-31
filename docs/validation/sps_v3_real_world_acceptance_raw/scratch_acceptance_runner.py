"""
SPS V3 Real-World Acceptance Test -- isolated runner.

Calls run_due_diligence() directly (no DB writes, no auth/usage-cap
layer) with SPS_ENGINE_VERSION=v3, for exactly one company, and writes
the full result (V2.1 methodology + V3 assessment) to a JSON file.

Usage: python3 scratch_acceptance_runner.py <slug> <company_text_file>
"""
import json
import sys
from dotenv import load_dotenv

load_dotenv()

from app.workflows.due_diligence_workflow import run_due_diligence


def main():
    slug = sys.argv[1]
    text_path = sys.argv[2]
    with open(text_path) as f:
        company_text = f.read()

    results = run_due_diligence(company_text, analysis_type="public", evidence_sources=["company_description"])
    sie = results["sie_analysis"]

    out = {
        "slug": slug,
        "v2_1_overall_score": sie.startup_intelligence_score,
        "v2_1_methodology": sie.model_dump(mode="json"),
        "sps_v3": sie.sps_v3.model_dump(mode="json") if sie.sps_v3 else None,
    }

    out_path = f"/private/tmp/claude-501/-Users-jerrodmchenry-Desktop-ai-due-diligence-copilot-ai-due-diligence-copilot/5af9a3ea-872d-44dc-8d64-5df92be865b9/scratchpad/sps_acceptance/{slug}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"WROTE {out_path}")


if __name__ == "__main__":
    main()
