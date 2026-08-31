"""
SPS V3 Real-World Acceptance Test -- deep dimension-level dump.

Re-derives the full dimension-level trace (canonical observations with
source quotes, per-dimension DimensionResult with classification/
rule_trace/cited_evidence_ids) for a company already run by
scratch_acceptance_runner.py, by calling the SAME production
classify_evidence_for_v3() on the SAME already-acquired V2.1 pillar
evidence (no new research). This does not modify production code; it
only calls already-exported functions from an external script to
capture more detail than the production adapter's summary-only return
value exposes, for acceptance-test inspection purposes.
"""
import json
import sys
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

from app.models.startup import PillarAnalysis
from app.ai.sps_v3_adapter import classify_evidence_for_v3, map_stage
from app.ai.sps_v3_engine.evaluators import evaluate_all_dimensions, DIMENSION_PILLARS
from app.ai.sps_v3_engine.aggregation import evaluate_sps, classify_ux_state
from app.ai.sps_v3_engine.registry import DEFAULT_REGISTRY
from app.ai.sps_v3_engine.evidence_bundle import EvidenceBundle


def _default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "value"):
        return obj.value
    return str(obj)


def main():
    slug = sys.argv[1]
    base = "/private/tmp/claude-501/-Users-jerrodmchenry-Desktop-ai-due-diligence-copilot-ai-due-diligence-copilot/5af9a3ea-872d-44dc-8d64-5df92be865b9/scratchpad/sps_acceptance"
    with open(f"{base}/{slug}.json") as f:
        data = json.load(f)

    m = data["v2_1_methodology"]
    market = PillarAnalysis(**m["market"])
    team = PillarAnalysis(**m["team"])
    product = PillarAnalysis(**m["product"])
    execution = PillarAnalysis(**m["execution"])
    traction = PillarAnalysis(**m["traction"])

    observations = classify_evidence_for_v3(market, team, product, execution, traction, id_seed=f"DEEP-{slug}")

    stage = map_stage(m["context"].get("company_stage") or m["context"].get("funding_stage"))
    bundle = EvidenceBundle(company_id=f"DEEP-{slug}", stage=stage, evidence=observations)

    dims = evaluate_all_dimensions(bundle, DEFAULT_REGISTRY)
    result = evaluate_sps(dims, stage, DEFAULT_REGISTRY)
    ux_state = classify_ux_state(result)

    out = {
        "slug": slug,
        "stage": stage.value,
        "num_observations": len(observations),
        "observations": [
            {
                "type": type(o).__name__,
                "observation_id": o.observation_id,
                "source_excerpt": o.source_excerpt,
                "provenance_grade": o.provenance_grade.value,
                **{k: (v.value if hasattr(v, "value") else v) for k, v in o.__dict__.items()
                   if k not in ("observation_id", "source_excerpt", "provenance_status", "provenance_grade",
                                "direct_or_derived", "extraction_confidence", "source_reference", "source_date",
                                "derivation", "as_of_date", "origin_id", "source_independence")},
            }
            for o in observations
        ],
        "dimensions": [
            {
                "dimension_id": d.dimension_id,
                "pillar": d.pillar,
                "weight": str(d.weight),
                "score": (str(d.score) if d.score is not None else None),
                "availability": d.availability.value,
                "confidence": d.confidence.value,
                "classification": d.classification.classification if d.classification else None,
                "classification_reason": d.classification.reason if d.classification else None,
                "supporting_evidence_ids": list(d.classification.supporting_evidence_ids) if d.classification else [],
                "negative_evidence_ids": list(d.classification.negative_evidence_ids) if d.classification else [],
                "rule_id": d.rule_trace.rule_id if d.rule_trace else None,
                "rule_reason": d.rule_trace.reason if d.rule_trace else None,
                "cited_evidence_ids": list(d.cited_evidence_ids),
            }
            for d in dims
        ],
        "sps_result": {
            "sps": str(result.sps) if result.sps is not None else None,
            "publishable": result.publishable,
            "withhold_reason": result.withhold_reason,
            "coverage_pct": str(result.coverage.overall_pct),
            "per_pillar_coverage": {k: str(v) for k, v in result.coverage.per_pillar_pct.items()},
            "confidence": result.confidence.overall.value,
            "per_pillar_confidence": {k: v.value for k, v in result.confidence.per_pillar.items()},
            "ux_state": ux_state,
            "pillar_results": [
                {
                    "pillar": p.pillar,
                    "strength": str(p.strength) if p.strength is not None else None,
                    "completeness_pct": str(p.completeness_pct),
                    "confidence": p.confidence.value,
                    "publishable": p.publishable,
                    "withhold_reason": p.withhold_reason,
                }
                for p in result.pillar_results
            ],
        },
    }

    out_path = f"{base}/{slug}_deep.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=_default)
    print(f"WROTE {out_path}")


if __name__ == "__main__":
    main()
