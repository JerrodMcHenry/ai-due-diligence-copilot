"""
SPS V3 Real-World Acceptance Test -- Part 17 repeatability check.

Loads a company's already-saved V2.1 pillar analyses (produced by
scratch_acceptance_runner.py) and calls classify_evidence_for_v3() ONCE
to get a real, frozen tuple of canonical observations (this call is the
non-deterministic acquisition/classification step -- run once, then
frozen). Then runs evaluate_all_dimensions() + evaluate_sps() +
classify_ux_state() TWICE against that SAME frozen observations tuple
and diffs the two results field by field. This isolates deterministic
SCORING repeatability from evidence ACQUISITION variance, exactly as
Part 17 requires -- no production code is modified; this only calls
already-exported functions from an external script.
"""
import json
import sys
from dotenv import load_dotenv

load_dotenv()

from app.models.startup import PillarAnalysis
from app.ai.sps_v3_adapter import classify_evidence_for_v3
from app.ai.sps_v3_engine.evaluators import evaluate_all_dimensions
from app.ai.sps_v3_engine.aggregation import evaluate_sps, classify_ux_state
from app.ai.sps_v3_engine.registry import DEFAULT_REGISTRY
from app.ai.sps_v3_engine.evidence_bundle import EvidenceBundle
from app.ai.sps_v3_adapter import map_stage


def main():
    slug = sys.argv[1]
    json_path = f"/private/tmp/claude-501/-Users-jerrodmchenry-Desktop-ai-due-diligence-copilot-ai-due-diligence-copilot/5af9a3ea-872d-44dc-8d64-5df92be865b9/scratchpad/sps_acceptance/{slug}.json"
    with open(json_path) as f:
        data = json.load(f)

    m = data["v2_1_methodology"]
    market = PillarAnalysis(**m["market"])
    team = PillarAnalysis(**m["team"])
    product = PillarAnalysis(**m["product"])
    execution = PillarAnalysis(**m["execution"])
    traction = PillarAnalysis(**m["traction"])

    print(f">>> Calling classify_evidence_for_v3 ONCE for {slug} to freeze observations...")
    observations = classify_evidence_for_v3(market, team, product, execution, traction, id_seed=f"REPEAT-{slug}")
    print(f">>> Froze {len(observations)} observations.")

    stage = map_stage(m["context"].get("company_stage") or m["context"].get("funding_stage"))
    bundle = EvidenceBundle(company_id=f"REPEAT-{slug}", stage=stage, evidence=observations)

    def run_once():
        dims = evaluate_all_dimensions(bundle, DEFAULT_REGISTRY)
        result = evaluate_sps(dims, stage, DEFAULT_REGISTRY)
        return {
            "sps": str(result.sps),
            "coverage_pct": str(result.coverage.overall_pct),
            "confidence": result.confidence.overall.value,
            "publishable": result.publishable,
            "ux_state": classify_ux_state(result),
            "pillars": {
                p.pillar: {
                    "strength": str(p.strength),
                    "coverage_pct": str(p.completeness_pct),
                    "confidence": p.confidence.value,
                    "publishable": p.publishable,
                }
                for p in result.pillar_results
            },
            "dimension_scores": {d.dimension_id: str(d.score) for d in dims},
        }

    run1 = run_once()
    run2 = run_once()

    identical = run1 == run2
    print(f">>> REPEATABILITY for {slug}: {'IDENTICAL' if identical else 'DIFFERENT -- DEFECT'}")
    if not identical:
        print("RUN 1:", json.dumps(run1, indent=2))
        print("RUN 2:", json.dumps(run2, indent=2))

    out_path = f"/private/tmp/claude-501/-Users-jerrodmchenry-Desktop-ai-due-diligence-copilot-ai-due-diligence-copilot/5af9a3ea-872d-44dc-8d64-5df92be865b9/scratchpad/sps_acceptance/{slug}_repeatability.json"
    with open(out_path, "w") as f:
        json.dump({"identical": identical, "run1": run1, "run2": run2, "num_observations": len(observations)}, f, indent=2)
    print(f"WROTE {out_path}")


if __name__ == "__main__":
    main()
