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
from decimal import Decimal
from unittest import mock

from app.ai import sps_v3_adapter as adapter
from app.ai.sps_v3_engine.evaluators import evaluate_all_dimensions
from app.ai.sps_v3_engine.evidence_bundle import EvidenceBundle
from app.ai.sps_v3_engine.registry import DEFAULT_REGISTRY
from app.ai.sps_v3_engine.types import AvailabilityStatus, Stage
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
    only affect THAT claim -- every other, well-formed claim in the SAME
    pillar must still survive. Before the original fix, a strict `str`
    field meant one missing quote raised a Pydantic ValidationError for
    the whole pillar, silently discarding every other claim too. Since
    the Adapter Hardening phase's Fix #3, a missing quote no longer
    means automatic drop -- see the two tests immediately below, which
    split "missing quote" into its two now-distinct outcomes."""
    mixed = {
        "market": {
            "competitors": [
                {"named_competitor": "Zenith Freight", "differentiator_named": True},  # no verbatim_quote
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
        # Market's own source text never mentions "Zenith Freight" at all
        # (unlike the recoverable-anchor test below) -- so tier-1 anchor
        # recovery cannot find it, and the correction retry's own mocked
        # response (the same `mixed` payload, not a valid array) parses
        # to zero recovered items -- the competitor claim is genuinely
        # unrecoverable and must be dropped.
        market = _pillar([_observed_subscore("competitive_landscape", ["the market has several established players"])])
        team = _pillar([_observed_subscore("founder", ["the CEO previously led engineering at a Fortune 500 logistics company"])])
        empty = _pillar([])

        observations = adapter.classify_evidence_for_v3(market, team, empty, empty, empty, id_seed="TESTMISSINGQUOTE")

    expect(len(observations) == 1, f"The unrecoverable market claim must be dropped, but the well-formed team claim must survive: got {len(observations)} observations")
    expect(observations[0].founder_role == "CEO", f"Expected the surviving observation to be the Team founder-experience claim, got: {observations[0]}")


def test_missing_quote_recoverable_via_anchor_is_deterministically_recovered() -> None:
    """Fix #3, tier 1 (CASE A -- recoverable): a claim that omits
    verbatim_quote but whose own proper-noun anchor (named_competitor)
    genuinely, literally appears in the pillar's source text must be
    recovered -- with NO extra LLM call -- using the real sentence
    containing that anchor, and marked as recovered (LOW
    extraction_confidence, an explicit source_reference) so it stays
    distinguishable from a claim the classifier grounded on the first
    try."""
    extraction = {
        "market": {
            "competitors": [
                {"named_competitor": "Acme Corp", "differentiator_named": True},  # no verbatim_quote
            ],
        },
        "team": {}, "product": {}, "execution": {}, "traction": {},
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)) as mocked:
        market = _pillar([_observed_subscore("competitive_landscape", ["The company competes directly with Acme Corp in the mid-market segment."])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(market, empty, empty, empty, empty, id_seed="TESTANCHOR")

    expect(len(observations) == 1, f"The anchor-recoverable claim must survive, got {len(observations)} observations")
    obs = observations[0]
    expect(obs.named_competitor == "Acme Corp", f"Expected the recovered competitor, got: {obs}")
    expect(obs.source_excerpt == "The company competes directly with Acme Corp in the mid-market segment.",
           f"Recovered quote must be the real, literal sentence from source text, got: {obs.source_excerpt!r}")
    expect(obs.extraction_confidence.value == "LOW", f"A recovered observation must carry LOW extraction_confidence, got: {obs.extraction_confidence}")
    expect(obs.source_reference == "recovered_by_grounding_repair", f"A recovered observation must carry the recovery marker, got: {obs.source_reference!r}")
    # Tier 1 recovery needs zero extra LLM calls -- the correction retry
    # (tier 2) must never fire when tier 1 already succeeded.
    expect(mocked.call_count == 1, f"Anchor recovery must not trigger a second (correction-retry) call, got {mocked.call_count} calls")


def test_missing_quote_with_no_safe_anchor_is_not_accepted_by_tier_one() -> None:
    """Fix #3, tier 1 (CASE B -- unrecoverable at tier 1): a claim
    missing verbatim_quote whose anchor field is empty (no proper noun
    to search for at all -- e.g. a capability claim) must NOT be
    accepted by tier 1, and must fall through to the bounded tier-2
    correction retry rather than being silently trusted."""
    extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {
            "capabilities": [
                {"capability_label": "automated onboarding flow", "shipped": True},  # no verbatim_quote
            ],
        },
    }
    calls = {"n": 0}

    def _side_effect(system, user, temperature):
        calls["n"] += 1
        if calls["n"] == 1:
            return json.dumps(extraction)
        # Correction retry: no source sentence actually supports this
        # claim -- the model correctly returns null.
        return json.dumps([{"index": 0, "quote": None}])

    with mock.patch.object(adapter, "call_analysis_model", side_effect=_side_effect) as mocked:
        product = _pillar([_observed_subscore("capability", ["the platform supports single sign-on."])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, empty, product, empty, empty, id_seed="TESTNOANCHOR")

    expect(observations == (), f"A claim with no safe anchor and no correction-retry match must be dropped, got: {observations}")
    expect(mocked.call_count == 2, f"Tier 2 (the single bounded correction retry) must still be attempted, got {mocked.call_count} calls")


def test_no_evidence_short_circuits_without_calling_the_model() -> None:
    """When every pillar has zero Observed-status evidence, the adapter
    must not spend an LLM call at all -- classify_evidence_for_v3 returns
    () immediately."""
    empty = _pillar([])

    with mock.patch.object(adapter, "call_analysis_model") as mocked:
        observations = adapter.classify_evidence_for_v3(empty, empty, empty, empty, empty, id_seed="TESTCO-3")

    expect(observations == (), "No evidence anywhere should short-circuit to zero observations.")
    mocked.assert_not_called()


def _dimension(results, dimension_id: str):
    for r in results:
        if r.dimension_id == dimension_id:
            return r
    raise AssertionError(f"No DimensionResult for {dimension_id!r} in {[r.dimension_id for r in results]}")


# ---------------------------------------------------------------------
# Fix #1 -- capability classification leakage
# ---------------------------------------------------------------------

def test_capability_filter_rejects_financial_and_operational_boilerplate() -> None:
    """funding != technical capability, runway != technical capability,
    gross margin != product execution, customer growth != product
    execution, ARR != product execution. Every quote below is grounded
    (present verbatim in source text) so ONLY the content-shape guard
    (Fix #1) is under test here -- deliberately original, non-test-suite
    wording (never the literal sentences the acceptance test found for
    any real company), to prove the guard generalizes over term
    FAMILIES rather than memorizing specific phrases."""
    boilerplate_claims = [
        ("the company disclosed a $50M funding round in March", "Funding round disclosure"),
        ("the company reported fourteen months of runway remaining", "Runway disclosure"),
        ("gross margin improved to sixty-two percent this quarter", "Margin improvement"),
        ("customer growth accelerated three times year over year", "Customer growth"),
        ("the company's ARR crossed ten million dollars this year", "ARR milestone"),
    ]
    extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {
            "capabilities": [
                {"verbatim_quote": quote, "capability_label": label, "shipped": True}
                for quote, label in boilerplate_claims
            ],
        },
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
        product = _pillar([_observed_subscore("capability", [q for q, _ in boilerplate_claims])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, empty, product, empty, empty, id_seed="TESTBOILER")

    expect(observations == (), f"All five financial/operational boilerplate claims must be rejected as capabilities, got: {observations}")


def test_capability_filter_accepts_legitimate_shipped_capability_and_release() -> None:
    """A real shipped technical/product capability and a real product
    release must still pass -- the guard must not become a blanket
    rejection of the whole capabilities category."""
    legit_claims = [
        ("the team shipped a real-time inventory sync engine that updates every 30 seconds", "real-time inventory sync engine"),
        ("the company launched a new mobile app with offline support", "mobile app with offline support"),
    ]
    extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {
            "capabilities": [
                {"verbatim_quote": quote, "capability_label": label, "shipped": True}
                for quote, label in legit_claims
            ],
        },
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
        product = _pillar([_observed_subscore("capability", [q for q, _ in legit_claims])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, empty, product, empty, empty, id_seed="TESTLEGIT")

    expect(len(observations) == 2, f"Both legitimate shipped-capability claims must survive, got: {observations}")
    labels = {o.capability_label for o in observations}
    expect(labels == {label for _, label in legit_claims}, f"Unexpected surviving labels: {labels}")


def test_boilerplate_does_not_create_technical_capability_or_product_execution_but_legit_does() -> None:
    """Pipeline-level confirmation, at the deterministic-dimension level:
    a company whose ONLY 'capability'-shaped evidence is financial/
    operational boilerplate must leave technical_capability (Team) and
    product_execution (Execution) UNAVAILABLE_NO_EVIDENCE -- never
    SCORABLE from that evidence -- while a company with a real shipped
    capability DOES make product_execution SCORABLE."""
    boiler_extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {
            "capabilities": [
                {"verbatim_quote": "the company reported healthy operating cadence and strong margins",
                 "capability_label": "Strong operating performance", "shipped": True},
            ],
        },
    }
    legit_extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {
            "capabilities": [
                {"verbatim_quote": "the platform shipped a new automated fraud-detection pipeline",
                 "capability_label": "automated fraud-detection pipeline", "shipped": True},
            ],
        },
    }

    def run(extraction) -> tuple:
        with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
            product = _pillar([_observed_subscore("capability", [extraction["product"]["capabilities"][0]["verbatim_quote"]])])
            empty = _pillar([])
            observations = adapter.classify_evidence_for_v3(empty, empty, product, empty, empty, id_seed="TESTDIM")
        bundle = EvidenceBundle(company_id="TESTDIM", stage=Stage.SEED, evidence=observations)
        return evaluate_all_dimensions(bundle, DEFAULT_REGISTRY)

    boiler_results = run(boiler_extraction)
    legit_results = run(legit_extraction)

    boiler_prodex = _dimension(boiler_results, "product_execution")
    expect(boiler_prodex.availability == AvailabilityStatus.UNAVAILABLE_NO_EVIDENCE,
           f"Boilerplate-only evidence must leave product_execution unavailable, got: {boiler_prodex.availability}")
    expect(boiler_prodex.score is None, f"Boilerplate-only product_execution must have no score, got: {boiler_prodex.score}")

    legit_prodex = _dimension(legit_results, "product_execution")
    expect(legit_prodex.availability == AvailabilityStatus.SCORABLE,
           f"A real shipped capability must make product_execution scorable, got: {legit_prodex.availability}")
    expect(legit_prodex.score is not None, "A real shipped capability must produce a real product_execution score.")


# ---------------------------------------------------------------------
# Fix #2 -- negative evidence extraction
# ---------------------------------------------------------------------

def test_capability_filter_term_matching_does_not_collide_on_substrings() -> None:
    """Regression test for a real bug this phase found: the technical
    term "engine" must never match inside the unrelated word
    "engineering" (which would let a pure hiring-plan/headcount claim
    slip past the boilerplate guard just because it mentions
    "engineering teams"). Word-boundary matching must isolate whole
    words, not just prefixes."""
    with_engineering_but_no_real_engine = "Hiring plan disclosed to double engineering and sales teams over next 12 months."
    expect(
        adapter._is_financial_operational_boilerplate(with_engineering_but_no_real_engine),
        f"'engineering' must not be mistaken for the technical term 'engine': {with_engineering_but_no_real_engine!r}",
    )
    real_engine_claim = "the team shipped a real-time fraud-detection engine that processes transactions quickly."
    expect(
        not adapter._is_financial_operational_boilerplate(real_engine_claim),
        f"A genuine standalone 'engine' claim must still pass: {real_engine_claim!r}",
    )


def test_negative_signal_grounded_adverse_fact_becomes_observation() -> None:
    """A grounded, affirmative adverse fact, mapped to a valid dimension
    for its own pillar, must become a NegativeSignalObservation."""
    extraction = {
        "market": {}, "product": {}, "execution": {}, "traction": {},
        "team": {
            "negative_signals": [
                {"verbatim_quote": "the company laid off 40% of its staff in early 2024",
                 "signal_type": "workforce_reduction", "severity": "SEVERE",
                 "affected_dimension": "execution_track_record_team"},
            ],
        },
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
        team = _pillar([_observed_subscore("execution_history", ["the company laid off 40% of its staff in early 2024"])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, team, empty, empty, empty, id_seed="TESTNEG")

    expect(len(observations) == 1, f"Expected exactly one negative-signal observation, got: {observations}")
    obs = observations[0]
    expect(obs.signal_type == "workforce_reduction", f"Unexpected signal_type: {obs.signal_type}")
    expect(obs.severity == "SEVERE", f"Unexpected severity: {obs.severity}")
    expect(obs.affected_dimension == "execution_track_record_team", f"Unexpected affected_dimension: {obs.affected_dimension}")


def test_negative_signal_without_grounded_support_is_dropped() -> None:
    """A negative-signal claim the model asserts but that has NO real
    support in the actual Observed source text -- whether because the
    underlying information is simply missing, the model expressed
    uncertainty, or it fabricated the claim outright -- must be dropped.
    The adapter does not (and cannot generically) distinguish those
    three REASONS a claim lacks support; it enforces one uniform rule:
    every negative signal must be grounded in real text, exactly like
    every positive claim, via the SAME firewall."""
    extraction = {
        "market": {}, "product": {}, "execution": {}, "traction": {},
        "team": {
            "negative_signals": [
                {"verbatim_quote": "the company may be facing unspecified headwinds",
                 "signal_type": "unspecified_concern", "severity": "MODERATE",
                 "affected_dimension": "execution_track_record_team"},
            ],
        },
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
        # Team's real Observed text never contains that sentence at all.
        team = _pillar([_observed_subscore("execution_history", ["the founding team has two prior startups"])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, team, empty, empty, empty, id_seed="TESTNEGDROP")

    expect(observations == (), f"An ungrounded negative-signal claim must be dropped, got: {observations}")


def test_negative_signal_dimension_must_belong_to_its_own_pillar() -> None:
    """affected_dimension is validated against the REAL dimension
    vocabulary for the claim's OWN pillar (read-only from the frozen
    engine's DIMENSION_PILLARS) -- a valid dimension for a DIFFERENT
    pillar, or an outright invalid dimension id, must be dropped, never
    guessed or cross-assigned."""
    extraction = {
        "product": {}, "execution": {}, "traction": {},
        "market": {
            "negative_signals": [
                {"verbatim_quote": "the company lost its largest publicly-named customer to a competitor",
                 "signal_type": "customer_loss", "severity": "MODERATE",
                 "affected_dimension": "market_size"},  # valid Market dimension -> accepted
                {"verbatim_quote": "the company disclosed severe cash constraints in its public filing",
                 "signal_type": "cash_constraint", "severity": "SEVERE",
                 "affected_dimension": "capital_efficiency"},  # a Financial Health dimension, wrong pillar -> dropped
                {"verbatim_quote": "the company faces an entirely fabricated made-up problem",
                 "signal_type": "bogus", "severity": "SEVERE",
                 "affected_dimension": "not_a_real_dimension"},  # not a real dimension at all -> dropped
            ],
        },
        "team": {},
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
        market = _pillar([_observed_subscore("competitive_landscape", [
            "the company lost its largest publicly-named customer to a competitor",
            "the company disclosed severe cash constraints in its public filing",
            "the company faces an entirely fabricated made-up problem",
        ])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(market, empty, empty, empty, empty, id_seed="TESTNEGDIM")

    expect(len(observations) == 1, f"Only the valid-for-its-pillar dimension should survive, got: {observations}")
    expect(observations[0].affected_dimension == "market_size", f"Unexpected surviving dimension: {observations[0].affected_dimension}")


def test_negative_signal_reaches_engine_and_lowers_relevant_strength() -> None:
    """End-to-end confirmation at the deterministic-dimension level: a
    NegativeSignalObservation the adapter produces must reach
    evaluate_all_dimensions and pull the SPECIFIC affected dimension's
    Strength down to the negative band -- never diluted, never
    generalized to an unrelated dimension."""
    extraction = {
        "market": {}, "product": {}, "execution": {}, "traction": {},
        "team": {
            "negative_signals": [
                {"verbatim_quote": "the company laid off 40% of its staff in early 2024",
                 "signal_type": "workforce_reduction", "severity": "SEVERE",
                 "affected_dimension": "execution_track_record_team"},
            ],
        },
    }

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
        team = _pillar([_observed_subscore("execution_history", ["the company laid off 40% of its staff in early 2024"])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, team, empty, empty, empty, id_seed="TESTNEGENGINE")

    # classify_evidence_for_v3 returns a single flat tuple mixing
    # positive and negative typed observations -- the engine's
    # evaluators only ever read company.negative_signals (a field
    # separate from company.evidence), so the split below mirrors
    # exactly what compute_sps_v3_assessment itself must do (see its
    # own fix in sps_v3_adapter.py).
    from app.ai.sps_v3_engine.types import NegativeSignalObservation as _Neg
    positive = tuple(o for o in observations if not isinstance(o, _Neg))
    negative = tuple(o for o in observations if isinstance(o, _Neg))
    bundle = EvidenceBundle(company_id="TESTNEGENGINE", stage=Stage.SEED, evidence=positive, negative_signals=negative)
    results = evaluate_all_dimensions(bundle, DEFAULT_REGISTRY)
    etr = _dimension(results, "execution_track_record_team")
    expect(etr.classification is not None and etr.classification.classification == "NEGATIVE_SIGNAL_PRESENT",
           f"Expected NEGATIVE_SIGNAL_PRESENT classification, got: {etr.classification}")
    expect(etr.score == DEFAULT_REGISTRY.value("band.negative_signal"),
           f"Negative evidence must pull the score to the registry's negative band, got: {etr.score}")


def test_compute_sps_v3_assessment_routes_negative_signals_correctly() -> None:
    """Production-entry-point confirmation: compute_sps_v3_assessment
    itself (not just the lower-level evaluate_all_dimensions call) must
    correctly split classify_evidence_for_v3's flat output into
    EvidenceBundle.evidence vs .negative_signals -- this is the exact
    integration bug this phase found and fixed (negative observations
    were being placed into .evidence, where no evaluator ever looks for
    them, so they never reached the engine despite being extracted)."""
    extraction = {
        "market": {}, "product": {}, "execution": {}, "traction": {},
        "team": {
            "negative_signals": [
                {"verbatim_quote": "the company laid off 40% of its staff in early 2024",
                 "signal_type": "workforce_reduction", "severity": "SEVERE",
                 "affected_dimension": "execution_track_record_team"},
            ],
        },
    }
    context = SIEContext(company_name="Negative Signal Co", company_stage="Seed", funding_stage="Seed")
    team = _pillar([_observed_subscore("execution_history", ["the company laid off 40% of its staff in early 2024"])])
    empty = _pillar([])
    methodology = SIEMethodologyAnalysis(
        context=context, market=empty, team=team, product=empty,
        execution=empty, traction=empty, financial_health=empty,
    )

    with mock.patch.object(adapter, "call_analysis_model", return_value=json.dumps(extraction)):
        result = adapter.compute_sps_v3_assessment(methodology, id_seed="TESTNEGROUTE")

    expect(result is not None, "Expected a real assessment.")
    team_result = result.pillars.get("Team")
    expect(team_result is not None, f"Expected a Team pillar result, got pillars={list(result.pillars)}")
    expect(team_result.strength is not None and team_result.strength <= 3.0,
           f"A severe negative signal on execution_track_record_team must pull Team strength down into the negative band, got: {team_result.strength}")


# ---------------------------------------------------------------------
# Fix #3, tier 2 -- bounded correction retry
# ---------------------------------------------------------------------

def test_correction_retry_accepts_exact_quote_rejects_paraphrase_fabrication_and_unsupported() -> None:
    """One batched correction call covering four unresolved claims:
    (1) an EXACT verbatim quote -> accepted; (2) a paraphrase of the
    real sentence -> rejected (not an exact substring); (3) a fabricated
    number never present in source -> rejected; (4) a quote describing
    an entirely unsupported fact -> rejected. Proves the same firewall
    is re-applied per-item, independent of the other items in the same
    batch."""
    source_sentence = "The team shipped a real-time fraud-detection engine last quarter."
    extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {
            "capabilities": [
                {"capability_label": "fraud-detection engine (exact)", "shipped": True},
                {"capability_label": "fraud-detection engine (paraphrase)", "shipped": True},
                {"capability_label": "fraud-detection engine (fabricated number)", "shipped": True},
                {"capability_label": "fraud-detection engine (unsupported)", "shipped": True},
            ],
        },
    }
    correction_response = [
        {"index": 0, "quote": source_sentence},
        {"index": 1, "quote": "They built a system to detect fraud in real time."},
        {"index": 2, "quote": "The team shipped a fraud-detection engine that processes 50,000 events per second."},
        {"index": 3, "quote": "The company also expanded into three new international markets."},
    ]
    calls = {"n": 0}

    def _side_effect(system, user, temperature):
        calls["n"] += 1
        if calls["n"] == 1:
            return json.dumps(extraction)
        return json.dumps(correction_response)

    with mock.patch.object(adapter, "call_analysis_model", side_effect=_side_effect) as mocked:
        product = _pillar([_observed_subscore("capability", [source_sentence])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, empty, product, empty, empty, id_seed="TESTRETRY")

    expect(len(observations) == 1, f"Only the exact-quote claim should be recovered, got: {observations}")
    expect(observations[0].source_excerpt == source_sentence, f"Unexpected recovered quote: {observations[0].source_excerpt!r}")
    expect(observations[0].capability_label == "fraud-detection engine (exact)", f"Unexpected recovered claim: {observations[0]}")
    expect(mocked.call_count == 2, f"Exactly one primary call + one correction retry, got {mocked.call_count}")


def test_correction_retry_malformed_response_fails_closed() -> None:
    """A correction-retry response that isn't valid JSON (or isn't a
    list) must degrade to zero recovered claims, never crash the whole
    analysis and never fabricate a fallback quote."""
    extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {"capabilities": [{"capability_label": "some capability", "shipped": True}]},
    }
    calls = {"n": 0}

    def _side_effect(system, user, temperature):
        calls["n"] += 1
        if calls["n"] == 1:
            return json.dumps(extraction)
        return "not valid json at all {{{"

    with mock.patch.object(adapter, "call_analysis_model", side_effect=_side_effect):
        product = _pillar([_observed_subscore("capability", ["the platform shipped something"])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, empty, product, empty, empty, id_seed="TESTMALFORMED")

    expect(observations == (), f"A malformed correction response must fail closed to zero recovered claims, got: {observations}")


def test_correction_retry_call_failure_fails_closed_without_losing_other_claims() -> None:
    """If the correction-retry LLM call itself raises, the whole
    analysis must NOT crash and must NOT lose claims that were already
    grounded elsewhere -- only the pending (unresolved) claims fail to
    recover."""
    extraction = {
        "market": {
            "competitors": [
                {"verbatim_quote": "the company competes with Beta Rivals in enterprise sales", "named_competitor": "Beta Rivals", "differentiator_named": False},
            ],
        },
        "team": {}, "execution": {}, "traction": {},
        "product": {"capabilities": [{"capability_label": "unresolved capability claim", "shipped": True}]},
    }
    calls = {"n": 0}

    def _side_effect(system, user, temperature):
        calls["n"] += 1
        if calls["n"] == 1:
            return json.dumps(extraction)
        raise RuntimeError("simulated correction-retry outage")

    with mock.patch.object(adapter, "call_analysis_model", side_effect=_side_effect):
        market = _pillar([_observed_subscore("competitive_landscape", ["the company competes with Beta Rivals in enterprise sales"])])
        product = _pillar([_observed_subscore("capability", ["the platform has an unresolved capability"])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(market, empty, product, empty, empty, id_seed="TESTRETRYFAIL")

    expect(len(observations) == 1, f"The already-grounded competitor claim must survive a correction-retry failure, got: {observations}")
    expect(observations[0].named_competitor == "Beta Rivals", f"Unexpected surviving observation: {observations[0]}")


def test_correction_retry_is_bounded_to_a_single_non_recursive_call() -> None:
    """However many claims remain unresolved after the correction retry,
    the adapter must never issue a second correction attempt -- the
    total call count for one classify_evidence_for_v3 invocation is
    always at most 2 (one primary + one bounded retry), regardless of
    how many pending items existed or how many the retry failed to
    resolve."""
    extraction = {
        "market": {}, "team": {}, "execution": {}, "traction": {},
        "product": {
            "capabilities": [
                {"capability_label": f"unresolved capability {i}", "shipped": True} for i in range(5)
            ],
        },
    }
    calls = {"n": 0}

    def _side_effect(system, user, temperature):
        calls["n"] += 1
        if calls["n"] == 1:
            return json.dumps(extraction)
        # Retry resolves nothing -- every item stays null.
        return json.dumps([{"index": i, "quote": None} for i in range(5)])

    with mock.patch.object(adapter, "call_analysis_model", side_effect=_side_effect) as mocked:
        product = _pillar([_observed_subscore("capability", ["the platform has several unresolved capabilities"])])
        empty = _pillar([])
        observations = adapter.classify_evidence_for_v3(empty, empty, product, empty, empty, id_seed="TESTBOUNDED")

    expect(observations == (), "None of the unresolved claims should be recovered.")
    expect(mocked.call_count == 2, f"Must be bounded to exactly one primary + one retry call even with zero recoveries, got {mocked.call_count}")


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
        test_missing_quote_recoverable_via_anchor_is_deterministically_recovered,
        test_missing_quote_with_no_safe_anchor_is_not_accepted_by_tier_one,
        test_capability_filter_rejects_financial_and_operational_boilerplate,
        test_capability_filter_accepts_legitimate_shipped_capability_and_release,
        test_boilerplate_does_not_create_technical_capability_or_product_execution_but_legit_does,
        test_capability_filter_term_matching_does_not_collide_on_substrings,
        test_negative_signal_grounded_adverse_fact_becomes_observation,
        test_negative_signal_without_grounded_support_is_dropped,
        test_negative_signal_dimension_must_belong_to_its_own_pillar,
        test_negative_signal_reaches_engine_and_lowers_relevant_strength,
        test_compute_sps_v3_assessment_routes_negative_signals_correctly,
        test_correction_retry_accepts_exact_quote_rejects_paraphrase_fabrication_and_unsupported,
        test_correction_retry_malformed_response_fails_closed,
        test_correction_retry_call_failure_fails_closed_without_losing_other_claims,
        test_correction_retry_is_bounded_to_a_single_non_recursive_call,
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
