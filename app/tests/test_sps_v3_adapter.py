"""
Phase 10.9, Part 31 -- backend tests for the V3 production adapter and
its integration into the canonical model / workflow.

All tests here stub app.ai.sps_v3_adapter.call_analysis_model so they run
fully offline and deterministically -- no live OpenAI call, no network,
no DATABASE_URL required. This mirrors how the rest of this test suite
already avoids live-API dependence for anything that doesn't specifically
need it (see app/tests/test_sie_v2_methodology.py's own fixtures).

Run with:
    python -m app.tests.test_sps_v3_adapter
(requires the project's .venv -- pydantic etc. are not on bare python3)
"""

import json
from unittest import mock

from app.ai import sps_v3_adapter as adapter
from app.models.startup import PillarAnalysis, SIEContext, SIEMethodologyAnalysis
from app.models.scoring import PillarScoreBreakdown, Subscore


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _observed_subscore(name: str, evidence: list[str], signals: list[str] | None = None) -> Subscore:
    return Subscore(
        name=name, score=7.0, weight=0.2, confidence="Medium",
        evidence_status="Observed", rationale="test", evidence=evidence,
        signals=signals or [],
    )


def _inferred_subscore(name: str) -> Subscore:
    return Subscore(
        name=name, score=6.0, weight=0.2, confidence="Low",
        evidence_status="Inferred", rationale="test", evidence=["a guess, not a fact"],
    )


def _pillar(subscores: list[Subscore]) -> PillarAnalysis:
    return PillarAnalysis(
        score=7.0, confidence="Medium", summary="",
        score_breakdown=PillarScoreBreakdown(subscores=subscores),
    )


CANNED_EXTRACTION = {
    "market": {
        "competitors": [
            {"verbatim_quote": "competes directly with Acme Corp", "named_competitor": "Acme Corp", "differentiator_named": True},
        ],
        "customer_demand": [
            {"verbatim_quote": "several enterprise customers have expressed strong interest", "outcome_claim": "several enterprise customers have expressed strong interest"},
        ],
    },
    "team": {
        "founder_experience": [
            {"verbatim_quote": "the CEO previously led engineering at a Fortune 500 logistics company", "founder_role": "CEO", "experience_type": "DIRECT_DOMAIN"},
        ],
        "founder_outcomes": [
            {"verbatim_quote": "the CTO's prior startup, DataFlow, was acquired by a larger firm", "prior_entity_name": "DataFlow", "outcome_type": "ACQUIRED"},
        ],
    },
    "product": {
        "capabilities": [
            {"verbatim_quote": "the platform has shipped a fully automated onboarding flow", "capability_label": "automated onboarding", "shipped": True},
        ],
    },
    "execution": {},
    "traction": {
        "contracts": [
            {"verbatim_quote": "signed a paid contract with a mid-market logistics customer", "contract_type": "PAYING", "named_customer": None, "renewal_evidence": False},
        ],
    },
}


def test_firewall_drops_ungrounded_quotes() -> None:
    """A classification whose verbatim_quote does NOT appear in the
    source text must be dropped -- the single most important invariant
    this adapter has (module docstring's stated firewall)."""
    poisoned = json.loads(json.dumps(CANNED_EXTRACTION))
    poisoned["market"]["competitors"].append({
        "verbatim_quote": "this exact sentence was never in the source text",
        "named_competitor": "FakeCorp", "differentiator_named": True,
    })

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(poisoned)):
        market = _pillar([_observed_subscore("competitive_landscape", ["competes directly with Acme Corp"])])
        team = _pillar([])
        product = _pillar([])
        execution = _pillar([])
        traction = _pillar([])

        observations = adapter.classify_evidence_for_v3(market, team, product, execution, traction, id_seed="TEST")

    named = [o.named_competitor for o in observations if hasattr(o, "named_competitor")]
    expect("Acme Corp" in named, f"Grounded competitor should survive: {named}")
    expect("FakeCorp" not in named, f"Ungrounded competitor must be dropped by the firewall, got: {named}")


def test_inferred_evidence_never_reaches_the_model() -> None:
    """Only Observed-status subscore evidence is sent to the classifier
    -- Inferred (an LLM judgment call) must never be treated as a
    verified fact for V3 purposes."""
    market = _pillar([_inferred_subscore("competitive_landscape")])
    team = _pillar([])
    product = _pillar([])
    execution = _pillar([])
    traction = _pillar([])

    text = adapter._pillar_observed_text(market)
    expect(text == "", f"Inferred-status evidence must be excluded from the text sent to the classifier, got: {text!r}")


def test_full_adapter_pipeline_produces_deterministic_assessment() -> None:
    """End-to-end: stubbed classification -> real, unmodified
    deterministic engine -> a real SPSV3Assessment. Two independent runs
    over the same canned input must produce byte-identical results
    (determinism, Phase 10.9 Part 31)."""
    context = SIEContext(company_name="Test Co", company_stage="Series A", funding_stage="Series A")

    market = _pillar([_observed_subscore("competitive_landscape", ["competes directly with Acme Corp"]),
                       _observed_subscore("customer_demand", ["several enterprise customers have expressed strong interest"])])
    team = _pillar([_observed_subscore("founder_experience", ["the CEO previously led engineering at a Fortune 500 logistics company"]),
                     _observed_subscore("founder_outcomes", ["the CTO's prior startup, DataFlow, was acquired by a larger firm"])])
    product = _pillar([_observed_subscore("capability", ["the platform has shipped a fully automated onboarding flow"])])
    execution = _pillar([])
    traction = _pillar([_observed_subscore("contracts", ["signed a paid contract with a mid-market logistics customer"])])
    financial = _pillar([])

    methodology = SIEMethodologyAnalysis(
        context=context, market=market, team=team, product=product,
        execution=execution, traction=traction, financial_health=financial,
    )

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(CANNED_EXTRACTION)):
        result_1 = adapter.compute_sps_v3_assessment(methodology, id_seed="TESTCO-1")
        result_2 = adapter.compute_sps_v3_assessment(methodology, id_seed="TESTCO-1")

    expect(result_1 is not None, "Adapter should produce a real assessment for well-formed canned input.")
    expect(result_1.engine_version == adapter.SPS_V3_ENGINE_VERSION, "engine_version must be stamped.")
    expect(result_1.scoring_version != "" and "V2" not in result_1.scoring_version.upper(), f"scoring_version must be a distinct V3 identifier, got: {result_1.scoring_version}")
    expect(result_1.assessment_state in ("sufficient", "limited", "insufficient"), f"Unexpected assessment_state: {result_1.assessment_state}")
    if result_1.assessment_state != "sufficient":
        expect(result_1.overall_score is None, f"overall_score must be None when not sufficient, got {result_1.overall_score}")
    # computed_at is a wall-clock timestamp (module docstring never
    # claims otherwise) -- excluded from the equality check; every other
    # field (the actual scoring output) must be byte-identical.
    dump_1 = result_1.model_dump(exclude={"computed_at"})
    dump_2 = result_2.model_dump(exclude={"computed_at"})
    expect(dump_1 == dump_2, f"Two runs over identical canned input must be byte-identical (determinism): {dump_1} != {dump_2}")


def test_adapter_returns_none_never_raises_on_call_failure() -> None:
    """A broken/unparseable LLM response must degrade to sps_v3=None
    (same as an analysis run before this field existed), never crash the
    surrounding /analyze request and never fabricate an INSUFFICIENT
    placeholder that looks like a real, deliberate result."""
    context = SIEContext(company_name="Test Co")
    # Must have at least one Observed subscore somewhere, or
    # classify_evidence_for_v3's own short-circuit (zero evidence -> zero
    # observations, no call at all) would make this test pass for the
    # wrong reason -- the point here is a call that IS attempted and
    # fails, not a call that's correctly never attempted.
    market = _pillar([_observed_subscore("competitive_landscape", ["some observed evidence"])])
    empty = _pillar([])
    methodology = SIEMethodologyAnalysis(
        context=context, market=market, team=empty, product=empty,
        execution=empty, traction=empty, financial_health=empty,
    )

    with mock.patch.object(adapter, "call_analysis_model", side_effect=RuntimeError("simulated provider outage")):
        result = adapter.compute_sps_v3_assessment(methodology, id_seed="TESTCO-2")

    expect(result is None, f"A call failure must degrade to None, got: {result}")


def test_missing_verbatim_quote_drops_only_that_claim() -> None:
    """SPS V3 local activation verification pass -- regression test for a
    real bug found via a live /analyze run: a claim missing verbatim_quote
    (the model omitted the field entirely, which real responses do) must
    only drop THAT claim -- every other, well-formed claim in the SAME
    pillar must still survive. Before this fix, a strict `str` field
    meant one missing quote raised a Pydantic ValidationError for the
    whole pillar, silently discarding every other claim too."""
    mixed = {
        "market": {
            "competitors": [
                {"named_competitor": "Acme Corp", "differentiator_named": True},  # no verbatim_quote at all
            ],
        },
        "team": {
            "founder_experience": [
                {"verbatim_quote": "the CEO previously led engineering at a Fortune 500 logistics company",
                 "founder_role": "CEO", "experience_type": "DIRECT_DOMAIN"},
            ],
        },
        "product": {}, "execution": {}, "traction": {},
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(mixed)):
        market = _pillar([_observed_subscore("competitive_landscape", ["competes directly with Acme Corp"])])
        team = _pillar([_observed_subscore("founder", ["the CEO previously led engineering at a Fortune 500 logistics company"])])
        empty = _pillar([])

        observations = adapter.classify_evidence_for_v3(market, team, empty, empty, empty, id_seed="TESTMISSINGQUOTE")

    expect(len(observations) == 1, f"The unquoted market claim must be dropped, but the well-formed team claim must survive: got {len(observations)} observations")
    expect(observations[0].founder_role == "CEO", f"Expected the surviving observation to be the Team founder-experience claim, got: {observations[0]}")


def test_no_evidence_short_circuits_without_calling_the_model() -> None:
    """When every pillar has zero Observed-status evidence, the adapter
    must not spend an LLM call at all -- classify_evidence_for_v3 returns
    () immediately."""
    empty = _pillar([])

    with mock.patch.object(adapter, "call_analysis_model") as mocked:
        observations = adapter.classify_evidence_for_v3(empty, empty, empty, empty, empty, id_seed="TESTCO-3")

    expect(observations == (), "No evidence anywhere should short-circuit to zero observations.")
    mocked.assert_not_called()


def test_sps_v3_is_none_by_default_on_a_fresh_model() -> None:
    """Backward compatibility: a SIEMethodologyAnalysis constructed with
    no sps_v3 argument (i.e. every historical record, and every analysis
    produced while the feature flag is off) decodes with sps_v3=None."""
    m = SIEMethodologyAnalysis()
    expect(m.sps_v3 is None, "sps_v3 must default to None.")


def main() -> None:
    tests = [
        test_firewall_drops_ungrounded_quotes,
        test_inferred_evidence_never_reaches_the_model,
        test_full_adapter_pipeline_produces_deterministic_assessment,
        test_adapter_returns_none_never_raises_on_call_failure,
        test_missing_verbatim_quote_drops_only_that_claim,
        test_no_evidence_short_circuits_without_calling_the_model,
        test_sps_v3_is_none_by_default_on_a_fresh_model,
    ]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as exc:
            failures.append((test.__name__, str(exc)))
            print(f"FAIL: {test.__name__}: {exc}")
        except Exception as exc:
            failures.append((test.__name__, repr(exc)))
            print(f"ERROR: {test.__name__}: {exc!r}")
    print(f"\n{len(tests) - len(failures)}/{len(tests)} passed.")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
