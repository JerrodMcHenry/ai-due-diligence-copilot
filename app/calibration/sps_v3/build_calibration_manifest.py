"""
Phase 10.8H -- generates the machine-readable calibration manifest from
the roster designed in docs/validation/SPS_V3_CALIBRATION_DATASET.md.

This script performs NO network calls, NO LLM calls, and writes NO
canonical_evidence -- it only emits the roster/metadata structure so a
future phase can populate real evidence against a frozen schema. Every
company's `canonical_evidence` and `desired_sps`-shaped field is
deliberately absent from the schema entirely (no such field exists to
populate) -- this is a structural, not merely a documented, enforcement
of Phase 10.8H Part 17's "do not tune yet" instruction.

Run with:
    python -m app.calibration.sps_v3.build_calibration_manifest
"""

import json
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parent / "calibration_manifest.json"

# (company_id, name, split, stage_hypothesis, sector, strength_profile_hypothesis, as_of_date, outcome)
_ROSTER = [
    ("CAL-001", "Balance (YC W26)", "TRAINING", "PRE_SEED", "FINTECH_ACCOUNTING_AI", "EXCEPTIONAL_FOR_STAGE_CANDIDATE", None, None),
    ("CAL-002", "Ritivel (YC W26)", "HOLDOUT", "IDEA_PRE_SEED", "HEALTHCARE_LIFE_SCIENCES_AI", "SPARSE_EVIDENCE_CANDIDATE", None, None),
    ("CAL-003", "Vercel", "TRAINING", "SERIES_B_PLUS", "AI_DEV_TOOLS", "VERY_STRONG_EVIDENCE_RICH", None, None),
    ("CAL-004", "Modal Labs", "TRAINING", "SERIES_B_PLUS", "AI_DEV_TOOLS", "ORDINARY_SPARSE_EVIDENCE", None, None),
    ("CAL-005", "Middesk", "HOLDOUT", "SERIES_B_PLUS", "FINTECH_INFRA", "ORDINARY_SPARSE_EVIDENCE", None, None),
    ("CAL-006", "Speak", "TRAINING", "SERIES_B_PLUS", "AI_CONSUMER", "STRONG_EVIDENCE_RICH", None, None),
    ("CAL-007", "Attio", "HOLDOUT", "SERIES_B_PLUS", "B2B_SAAS_CRM", "STRONG_ORDINARY_GROWTH", None, None),
    ("CAL-008", "Clay", "HOLDOUT", "SERIES_B_PLUS", "B2B_SAAS", "STRONG_HIGH_GROWTH", None, None),
    ("CAL-009", "Harvey AI", "TRAINING", "SERIES_B_C", "AI_LEGAL_VERTICAL", "ELITE_TEAM_CANDIDATE", None, None),
    ("CAL-010", "Together AI", "TRAINING", "SERIES_B", "AI_INFRA", "CAPITAL_EFFICIENT_TO_VERIFY", None, None),
    ("CAL-011", "Whatnot", "HOLDOUT", "SERIES_D_E", "MARKETPLACE_CONSUMER", "HIGH_GROWTH_EVIDENCE_RICH", None, None),
    ("CAL-012", "Perplexity AI", "TRAINING", "SERIES_C_D", "AI_CONSUMER", "VERY_STRONG_HIGH_FUNDING_UE_SCRUTINY", None, None),
    ("CAL-013", "Glean", "TRAINING", "SERIES_D", "AI_ENTERPRISE", "STRONG_EVIDENCE_RICH", None, None),
    ("CAL-014", "Mercury", "HOLDOUT", "SERIES_B_C", "FINTECH", "STRONG_CAPITAL_EFFICIENT_TO_VERIFY", None, None),
    ("CAL-015", "Webflow", "TRAINING", "SERIES_C", "B2B_SAAS", "STRONG_ORDINARY_GROWTH", None, None),
    ("CAL-016", "Scale AI", "HOLDOUT", "SERIES_F_PLUS", "AI", "VERY_STRONG_HIGH_FUNDING", None, None),
    ("CAL-017", "Hugging Face", "TRAINING", "SERIES_D", "AI_DEV_TOOLS", "STRONG_COMMUNITY_EVIDENCE_RICH", None, None),
    ("CAL-018", "Flexport", "TRAINING", "SERIES_E_GROWTH", "LOGISTICS", "DISTRESSED_MIXED", None, None),
    ("CAL-019", "Gusto", "HOLDOUT", "GROWTH", "B2B_SAAS_HR", "ORDINARY_STRONG_MATURE", None, None),
    ("CAL-020", "Airwallex", "TRAINING", "GROWTH", "FINTECH", "STRONG_MATURE", None, None),
    ("CAL-021", "Carta", "TRAINING", "GROWTH", "B2B_SAAS", "MIXED_ORDINARY_DOCUMENTED_STRUGGLES", None, None),
    ("CAL-022", "Instacart", "HOLDOUT", "GROWTH_PUBLIC", "MARKETPLACE_CONSUMER", "ORDINARY_MATURE_PROFITABLE_SLOWER_GROWTH", None, None),
    ("CAL-023", "ZipRecruiter", "TRAINING", "GROWTH_PUBLIC", "B2B_SAAS_HR", "PROFITABLE_SLOWER_GROWTH", None, None),
    ("CAL-024", "Discord", "HOLDOUT", "GROWTH", "CONSUMER", "STRONG_HIGH_EVIDENCE_MONETIZATION_MIXED", None, None),
    ("CAL-025", "Convoy", "TRAINING", "GROWTH_DEFUNCT", "LOGISTICS", "FAILED_SHUTDOWN", None, {"outcome": "SHUT_DOWN", "outcome_date": "2023-10"}),
    ("CAL-026", "Olive AI", "TRAINING", "GROWTH_DEFUNCT", "HEALTHCARE_AI", "FAILED_WOUND_DOWN", None, {"outcome": "WOUND_DOWN", "outcome_date": "2023"}),
    ("CAL-027", "Katerra", "HOLDOUT", "GROWTH_DEFUNCT", "CONSTRUCTION_HARDWARE", "FAILED_BANKRUPT", None, {"outcome": "BANKRUPTCY", "outcome_date": "2021-06"}),
    ("CAL-028", "Quibi", "TRAINING", "GROWTH_DEFUNCT", "MEDIA_CONSUMER", "FAILED_SHUTDOWN", None, {"outcome": "SHUT_DOWN", "outcome_date": "2020-12"}),
    ("CAL-029", "Bird", "HOLDOUT", "GROWTH_DEFUNCT", "MICROMOBILITY_HARDWARE", "FAILED_BANKRUPT", None, {"outcome": "BANKRUPTCY", "outcome_date": "2023-12"}),
    ("CAL-030", "Mailchimp", "TRAINING", "GROWTH_HISTORICAL", "B2B_SAAS", "CAPITAL_EFFICIENT_HISTORICAL_SNAPSHOT", "2020-01-01", {"outcome": "ACQUIRED", "outcome_date": "2021-09", "acquirer": "Intuit", "amount_usd_approx": 12000000000}),
    ("CAL-031", "Fast (checkout startup)", "HOLDOUT", "GROWTH_HISTORICAL", "FINTECH_CHECKOUT", "HISTORICAL_FAILED_OUTCOME_SNAPSHOT", "2021-06-01", {"outcome": "SHUT_DOWN", "outcome_date": "2022-04"}),
]


def build_manifest() -> dict:
    companies = []
    for company_id, name, split, stage, sector, profile, as_of, outcome in _ROSTER:
        companies.append({
            "company_id": company_id,
            "name": name,
            "split": split,
            "stage_hypothesis": stage,
            "sector": sector,
            "strength_profile_hypothesis": profile,
            "as_of_date": as_of,
            "requires_live_reverification": True,
            "canonical_evidence": None,
            "outcome_data": outcome,
            "leakage_register_checked": True,
        })

    return {
        "manifest_version": "10.8I-v1",
        "frozen": True,
        "frozen_at_phase": "10.8I",
        "purpose": "CALIBRATION -- NOT VALIDATION",
        "phase": "10.8I",
        "notes": (
            "Roster metadata, live-reverified during Phase 10.8I (2 substitutions: "
            "Cursor->Vercel [acquired by SpaceX, closed 2026-08-14], "
            "Metronome->Attio [acquired by Stripe, Dec 2025]; 3 reserved slots filled: "
            "Balance + Ritivel from YC W26, Fast as the historical failed-outcome case). "
            "Actual canonical evidence lives in app/calibration/sps_v3/calibration_evidence.py, "
            "not in this file's canonical_evidence field (kept None here per the original "
            "10.8H schema -- see that module for the real, sourced evidence). "
            "No desired_sps field exists in this schema -- see "
            "docs/validation/SPS_V3_CALIBRATION_DATASET.md Section 20. "
            "Every company confirmed absent from "
            "docs/validation/SPS_V3_CALIBRATION_LEAKAGE_REGISTER.md's "
            "36-company register."
        ),
        "training_count": sum(1 for c in companies if c["split"] == "TRAINING"),
        "holdout_count": sum(1 for c in companies if c["split"] == "HOLDOUT"),
        "companies": companies,
    }


def main() -> None:
    manifest = build_manifest()
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(manifest['companies'])} companies "
          f"({manifest['training_count']} training / {manifest['holdout_count']} holdout) "
          f"to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
