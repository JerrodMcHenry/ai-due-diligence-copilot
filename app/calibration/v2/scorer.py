"""
PASS A blind scorer -- SIE Methodology v2 calibration.

IMPORTANT, HONEST DISCLOSURE (read before trusting these results): the dimension-
level judgments in app/calibration/v2/pass_a/results/*.json were produced directly
by the analyst (Claude) reading the harness-stripped blind_inputs/*.json files,
NOT by an automated model API call. This repository has no wired-up mechanism for
this session to invoke the production LLM pipeline against arbitrary evidence
text, so "scoring" in PASS A means the analyst performing the same judgment a
constrained-LLM or hybrid dimension's prompt would ask of a model, using only the
permitted blind fields.

A second, more serious caveat: this analyst authored the benchmark records
themselves in earlier turns of this same conversation, including the
expected_quality_tier and future_outcome fields now stripped by blind_loader.py.
True cognitive blinding is not achievable this way -- the loader's field-stripping
is real and enforced (see test_blind_loader.py), but it cannot erase this
analyst's prior knowledge of how these specific companies were tiered or how
they turned out. Every judgment was made by working strictly from the re-read,
stripped evidence text and citing it explicitly, deliberately not consulting
memory of the tier/outcome -- but this is a good-faith discipline, not a
structural guarantee the way the loader's field-stripping is. If a stronger
blinding guarantee is required, re-running PASS A through a genuinely fresh
session/agent with no exposure to this conversation's history is the correct
fix, not a claim this document could make on its own.

Canonical states (spec Part 4): scored | not_expected_by_stage | not_applicable |
optional_unavailable | usually_private_unavailable | expected_unavailable |
conflicting | mixed. "Unavailable" states never carry a score.

anchor_status: FROZEN | CALIBRATION_ANCHOR_REQUIRED | NOT_APPLICABLE (no numeric
anchor question arises because the dimension is unscored for this company).
"""

from __future__ import annotations

METHODOLOGY_VERSION = "v2-spec-2026-08-23"
MODEL_IDENTIFIER = "claude-sonnet-5 (analyst reasoning, not an automated pipeline call -- see module docstring)"
PROMPT_VERSION = "PASS_A_manual_v1"

DIMENSIONS = [
    # (name, pillar, mode)
    ("Market Size", "Market", "Hybrid"),
    ("Market Growth", "Market", "Constrained LLM"),
    ("Market Timing", "Market", "Constrained LLM"),
    ("Competitive Intensity", "Market", "Hybrid"),
    ("Customer Demand", "Market", "Hybrid"),
    ("Founder-Market Fit", "Team", "Constrained LLM"),
    ("Technical Capability", "Team", "Hybrid"),
    ("Business Capability", "Team", "Hybrid"),
    ("Leadership", "Team", "Constrained LLM"),
    ("Execution Track Record", "Team", "Constrained LLM"),
    ("Customer Value", "Product", "Hybrid"),
    ("Differentiation", "Product", "Constrained LLM"),
    ("Usability", "Product", "Hybrid"),
    ("Defensibility", "Product", "Constrained LLM"),
    ("Adoption Potential", "Product", "Hybrid"),
    ("Go-to-Market Execution", "Execution", "Hybrid"),
    ("Product Execution", "Execution", "Hybrid"),
    ("Operational Execution", "Execution", "Hybrid"),
    ("Strategic Execution", "Execution", "Constrained LLM"),
    ("Customer Growth", "Traction", "Deterministic"),
    ("Revenue Growth", "Traction", "Deterministic"),
    ("Retention", "Traction", "Deterministic"),
    ("Engagement", "Traction", "Hybrid"),
    ("Growth Velocity", "Traction", "Deterministic"),
    ("Revenue Quality", "Financial Health", "Hybrid"),
    ("Unit Economics", "Financial Health", "Deterministic"),
    ("Burn Efficiency", "Financial Health", "Deterministic"),
    ("Runway", "Financial Health", "Deterministic"),
]

PILLAR_WEIGHTS = {
    "Market": 0.20, "Team": 0.20, "Product": 0.20,
    "Execution": 0.15, "Traction": 0.15, "Financial Health": 0.10,
}

DIM_WEIGHTS = {
    "Market": {"Market Size": .25, "Market Growth": .20, "Market Timing": .20,
               "Competitive Intensity": .15, "Customer Demand": .20},
    "Team": {"Founder-Market Fit": .25, "Technical Capability": .20, "Business Capability": .20,
             "Leadership": .20, "Execution Track Record": .15},
    "Product": {"Customer Value": .25, "Differentiation": .20, "Usability": .15,
                "Defensibility": .20, "Adoption Potential": .20},
    # SPEC GAP FOUND DURING PASS A (reported, not silently fixed): the
    # specification's Part 2 relocates Growth Velocity out of Execution
    # (5 dims -> 4) but Part 3 only re-derives Traction and Financial Health
    # weights from their investment questions, leaving Execution's four
    # remaining dimensions at their original .20 each (summing to .80, not
    # 1.0) with no explicit re-statement. This is a genuine specification
    # omission, flagged in the PASS A findings report -- NOT tuned or
    # silently redesigned here. The value below applies the spec's OWN
    # already-frozen aggregation rule ("renormalize weights to sum to 1
    # across the scored set") to this pre-existing equal-.20 relationship,
    # which mechanically yields .25 each -- this uses an existing rule on
    # an existing (if incomplete) weight set, it does not invent a new
    # weighting scheme or run a benchmark-driven re-derivation the way
    # Traction/Financial Health received.
    "Execution": {"Go-to-Market Execution": .25, "Product Execution": .25,
                  "Operational Execution": .25, "Strategic Execution": .25},
    "Traction": {"Retention": .25, "Revenue Growth": .25, "Growth Velocity": .20,
                 "Customer Growth": .15, "Engagement": .15},
    "Financial Health": {"Runway": .30, "Unit Economics": .25,
                          "Burn Efficiency": .25, "Revenue Quality": .20},
}

UNAVAILABLE_STATES = {
    "not_expected_by_stage", "not_applicable", "optional_unavailable",
    "usually_private_unavailable", "expected_unavailable",
}
