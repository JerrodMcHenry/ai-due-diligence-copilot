"""
Regression tests for Unified Multi-Source Analyze Startup (POST /analyze
in app/api.py, and assemble_multi_source_text()/evidence_sources
threading in app/workflows/due_diligence_workflow.py).

Runs entirely offline, with no real database write and no real LLM/
Tavily calls: app.api's module-level run_due_diligence and save_analysis
references are monkeypatched to fast, deterministic stand-ins for every
test in this file (restored after each test, even on failure), and
extract_text_from_website is monkeypatched to avoid a real network call.
PDF extraction, in contrast, uses REAL reportlab-generated PDFs through
the real (already separately tested in test_pdf_ingestion.py)
app.pdf_extractor.extract_text_from_pdf, since that's fully local and
free to exercise for real here.

The fake run_due_diligence still calls the REAL
build_sie_methodology_analysis()/build_provenance_context()/
AnalysisContext plumbing -- only the six pillar LLM calls and Tavily
research are skipped -- so evidence_sources/analysis_type threading is
exercised for real, not just asserted on the fake's own input echo.

SIE Authentication Phase 2 added a real Clerk-JWT auth gate in front of
these same endpoints. This file is about multi-source assembly, not
auth -- auth itself has its own dedicated coverage in
test_backend_authentication.py -- so it bypasses the gate for its own
process lifetime via FastAPI's dependency_overrides, returning a fixed
fake identity instead of verifying a real token. No test below asserts
anything about who this identity is; it only exists so requests reach
the endpoint bodies under test at all.

Run with:
    python -m app.tests.test_analyze_unified
"""

from contextlib import contextmanager
from io import BytesIO

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

import app.api as api
from app.auth import AuthenticatedUser, get_current_user
from app.models.analysis import (
    ExecutionAnalysisResult,
    FinancialAnalysisResult,
    FounderAnalysisResult,
    MarketAnalysisResult,
    ProductAnalysisResult,
    TractionAnalysisResult,
)
from app.models.analysis_context import AnalysisContext
from app.workflows.due_diligence_workflow import build_sie_methodology_analysis


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


FAKE_WEBSITE_TEXT = "Acme Robotics builds autonomous inventory-scanning robots."
FAKE_PDF_TEXT = "Acme Robotics pitch deck content for extraction testing."

client = TestClient(api.app)

# See module docstring: this file tests multi-source assembly, not auth,
# so it bypasses the real Clerk verification with a fixed fake identity
# for its own process lifetime.
api.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
    user_id="test-user-analyze-unified"
)


def _make_pdf_bytes(text: str = FAKE_PDF_TEXT) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.showPage()
    c.save()
    return buf.getvalue()


@contextmanager
def patched_pipeline():
    """
    Patches app.api's module-level run_due_diligence (a call-counting,
    LLM-free fake -- see module docstring), save_analysis (a no-op stub,
    no real DB write), and extract_text_from_website (a fixed fake, no
    real network call). Restores all three on exit regardless of outcome.
    Yields the shared call_log list every fake appends an entry to.
    """
    call_log: list[dict] = []

    def fake_run_due_diligence(company_text, analysis_type="public", evidence_sources=None):
        call_log.append({
            "company_text": company_text,
            "analysis_type": analysis_type,
            "evidence_sources": evidence_sources,
        })

        sie_analysis = build_sie_methodology_analysis(
            structured_analysis={
                "company_name": "Acme Robotics",
                "industry": "Robotics",
                "business_model": "Hardware-as-a-service",
            },
            readiness=None,
            founder_analysis=FounderAnalysisResult(),
            market_analysis=MarketAnalysisResult(),
            product_analysis=ProductAnalysisResult(),
            execution_analysis=ExecutionAnalysisResult(),
            traction_analysis=TractionAnalysisResult(),
            financial_analysis=FinancialAnalysisResult(),
            analysis_type=analysis_type,
            evidence_sources=evidence_sources,
        )

        return {
            "summary": "s",
            "risk_analysis": "r",
            "competitor_analysis": "c",
            "memo": "m",
            "structured_analysis": {"company_name": "Acme Robotics"},
            "investment_score": {},
            "founder_analysis": FounderAnalysisResult(),
            "market_analysis": MarketAnalysisResult(),
            "sources": [],
            "traction_analysis": TractionAnalysisResult(),
            "market_score": None,
            "team_score": None,
            "product_score": None,
            "competition_score": None,
            "traction_score": None,
            "financial_score": None,
            "overall_score": sie_analysis.startup_intelligence_score,
            "recommendation": None,
            "readiness_score": None,
            "readiness_summary": None,
            "sie_analysis": sie_analysis,
        }

    def fake_save_analysis(**kwargs):
        call_log.append({"save_analysis_kwargs": kwargs})
        return 999

    def fake_save_score_history(**kwargs):
        # Only /analyze-startup (of the four endpoints exercised in this
        # file) calls this. fake_save_analysis returns a fake id (999)
        # that doesn't correspond to a real row, so the real
        # save_score_history would fail its analysis_id foreign key --
        # stub it too rather than touch the real DB from this file.
        call_log.append({"save_score_history_kwargs": kwargs})

    def fake_extract_text_from_website(url):
        call_log.append({"website_url_fetched": url})
        return FAKE_WEBSITE_TEXT

    original_run_due_diligence = api.run_due_diligence
    original_save_analysis = api.save_analysis
    original_save_score_history = api.save_score_history
    original_extract_text_from_website = api.extract_text_from_website

    api.run_due_diligence = fake_run_due_diligence
    api.save_analysis = fake_save_analysis
    api.save_score_history = fake_save_score_history
    api.extract_text_from_website = fake_extract_text_from_website

    try:
        yield call_log
    finally:
        api.run_due_diligence = original_run_due_diligence
        api.save_analysis = original_save_analysis
        api.save_score_history = original_save_score_history
        api.extract_text_from_website = original_extract_text_from_website


def _pipeline_calls(call_log: list[dict]) -> list[dict]:
    return [entry for entry in call_log if "company_text" in entry]


def _run_and_get_call(data: dict | None = None, files: dict | None = None) -> dict:
    with patched_pipeline() as call_log:
        response = client.post("/analyze", data=data or {}, files=files or {})

    expect(
        response.status_code == 200,
        f"Expected 200, got {response.status_code}: {response.text}",
    )

    calls = _pipeline_calls(call_log)
    expect(
        len(calls) == 1,
        f"Expected exactly one canonical pipeline invocation, got {len(calls)}",
    )

    return calls[0]


# --- The seven valid source combinations -----------------------------------


def test_website_only() -> None:
    call = _run_and_get_call(data={"website_url": "https://example.com"})

    expect("=== Company Website ===" in call["company_text"], "Website section missing")
    expect(FAKE_WEBSITE_TEXT in call["company_text"], "Website text missing")
    expect("=== Pitch Deck ===" not in call["company_text"], "Pitch deck section must be omitted")
    expect(
        "=== Additional Company Information ===" not in call["company_text"],
        "User text section must be omitted",
    )
    expect(
        call["evidence_sources"] == ["website", "public_research"],
        f"Unexpected evidence_sources: {call['evidence_sources']}",
    )
    expect(call["analysis_type"] == "public", f"Expected 'public', got {call['analysis_type']!r}")


def test_pitch_deck_only() -> None:
    call = _run_and_get_call(files={"pdf": ("deck.pdf", _make_pdf_bytes(), "application/pdf")})

    expect("=== Pitch Deck ===" in call["company_text"], "Pitch deck section missing")
    expect(FAKE_PDF_TEXT in call["company_text"], "Extracted PDF text missing")
    expect("=== Company Website ===" not in call["company_text"], "Website section must be omitted")
    expect(
        "=== Additional Company Information ===" not in call["company_text"],
        "User text section must be omitted",
    )
    expect(
        call["evidence_sources"] == ["pitch_deck", "public_research"],
        f"Unexpected evidence_sources: {call['evidence_sources']}",
    )
    expect(
        call["analysis_type"] == "pitch_deck",
        f"Expected 'pitch_deck', got {call['analysis_type']!r}",
    )


def test_company_information_only() -> None:
    call = _run_and_get_call(data={"company_text": "Acme Robotics has 12 paying customers."})

    expect(
        "=== Additional Company Information ===" in call["company_text"],
        "User text section missing",
    )
    expect(
        "Acme Robotics has 12 paying customers." in call["company_text"],
        "User text content missing",
    )
    expect("=== Company Website ===" not in call["company_text"], "Website section must be omitted")
    expect("=== Pitch Deck ===" not in call["company_text"], "Pitch deck section must be omitted")
    expect(
        call["evidence_sources"] == ["company_description", "public_research"],
        f"Unexpected evidence_sources: {call['evidence_sources']}",
    )
    expect(call["analysis_type"] == "public", f"Expected 'public', got {call['analysis_type']!r}")


def test_website_and_pitch_deck() -> None:
    call = _run_and_get_call(
        data={"website_url": "https://example.com"},
        files={"pdf": ("deck.pdf", _make_pdf_bytes(), "application/pdf")},
    )

    expect("=== Company Website ===" in call["company_text"], "Website section missing")
    expect("=== Pitch Deck ===" in call["company_text"], "Pitch deck section missing")
    expect(
        "=== Additional Company Information ===" not in call["company_text"],
        "User text section must be omitted",
    )
    expect(
        call["evidence_sources"] == ["website", "pitch_deck", "public_research"],
        f"Unexpected evidence_sources: {call['evidence_sources']}",
    )
    expect(
        call["analysis_type"] == "pitch_deck",
        f"pitch_deck must win the analysis_type rule, got {call['analysis_type']!r}",
    )


def test_website_and_company_information() -> None:
    call = _run_and_get_call(
        data={
            "website_url": "https://example.com",
            "company_text": "Bootstrapped, no outside funding yet.",
        }
    )

    expect("=== Company Website ===" in call["company_text"], "Website section missing")
    expect(
        "=== Additional Company Information ===" in call["company_text"],
        "User text section missing",
    )
    expect("=== Pitch Deck ===" not in call["company_text"], "Pitch deck section must be omitted")
    expect(
        call["evidence_sources"] == ["website", "company_description", "public_research"],
        f"Unexpected evidence_sources: {call['evidence_sources']}",
    )
    expect(call["analysis_type"] == "public", f"Expected 'public', got {call['analysis_type']!r}")


def test_pitch_deck_and_company_information() -> None:
    call = _run_and_get_call(
        data={"company_text": "Raised a small pre-seed round last year."},
        files={"pdf": ("deck.pdf", _make_pdf_bytes(), "application/pdf")},
    )

    expect("=== Pitch Deck ===" in call["company_text"], "Pitch deck section missing")
    expect(
        "=== Additional Company Information ===" in call["company_text"],
        "User text section missing",
    )
    expect("=== Company Website ===" not in call["company_text"], "Website section must be omitted")
    expect(
        call["evidence_sources"] == ["pitch_deck", "company_description", "public_research"],
        f"Unexpected evidence_sources: {call['evidence_sources']}",
    )
    expect(
        call["analysis_type"] == "pitch_deck",
        f"Expected 'pitch_deck', got {call['analysis_type']!r}",
    )


def test_website_and_pitch_deck_and_company_information() -> None:
    call = _run_and_get_call(
        data={
            "website_url": "https://example.com",
            "company_text": "14 months of runway remaining.",
        },
        files={"pdf": ("deck.pdf", _make_pdf_bytes(), "application/pdf")},
    )

    expect("=== Company Website ===" in call["company_text"], "Website section missing")
    expect("=== Pitch Deck ===" in call["company_text"], "Pitch deck section missing")
    expect(
        "=== Additional Company Information ===" in call["company_text"],
        "User text section missing",
    )
    expect(
        call["evidence_sources"]
        == ["website", "pitch_deck", "company_description", "public_research"],
        f"Unexpected evidence_sources: {call['evidence_sources']}",
    )
    expect(
        call["analysis_type"] == "pitch_deck",
        f"Expected 'pitch_deck', got {call['analysis_type']!r}",
    )


# --- Rejection / failure semantics ------------------------------------------


def test_zero_sources_rejected() -> None:
    with patched_pipeline() as call_log:
        response = client.post("/analyze", data={})

    expect(response.status_code == 400, f"Expected 400, got {response.status_code}")
    expect(
        len(_pipeline_calls(call_log)) == 0,
        "Pipeline must never run for a zero-source request",
    )


def test_invalid_supplied_website_rejects_entire_request() -> None:
    """A malformed website URL must reject the whole request even though
    valid company_text was also supplied -- an explicitly supplied source
    that fails is never silently dropped in favor of what did succeed."""
    with patched_pipeline() as call_log:
        response = client.post(
            "/analyze",
            data={"website_url": "not-a-url", "company_text": "Valid company text here."},
        )

    expect(response.status_code == 400, f"Expected 400, got {response.status_code}")
    expect(
        len(_pipeline_calls(call_log)) == 0,
        "Pipeline must not run when a supplied source fails validation",
    )


def test_invalid_supplied_pdf_rejects_entire_request() -> None:
    """A non-PDF file rejects the whole request even though valid
    company_text was also supplied -- same rule as the website case."""
    with patched_pipeline() as call_log:
        response = client.post(
            "/analyze",
            data={"company_text": "Valid company text here."},
            files={"pdf": ("deck.pdf", b"not actually a pdf", "application/pdf")},
        )

    expect(response.status_code == 400, f"Expected 400, got {response.status_code}")
    expect(
        len(_pipeline_calls(call_log)) == 0,
        "Pipeline must not run when a supplied source fails validation",
    )


def test_assembled_input_size_bound() -> None:
    huge_website_text = "x" * 120_000

    with patched_pipeline() as call_log:
        api.extract_text_from_website = lambda url: huge_website_text
        response = client.post(
            "/analyze",
            data={
                "website_url": "https://example.com",
                "company_text": "y" * 40_000,
            },
        )

    expect(response.status_code == 400, f"Expected 400, got {response.status_code}")
    expect(
        "too long" in response.json()["detail"].lower(),
        f"Expected a clear too-long message, got {response.json()}",
    )
    expect(
        len(_pipeline_calls(call_log)) == 0,
        "Pipeline must not run when the assembled input exceeds the bound",
    )


# --- Backward compatibility --------------------------------------------------


def test_legacy_analyze_startup_still_works() -> None:
    with patched_pipeline() as call_log:
        response = client.post(
            "/analyze-startup",
            json={"company_text": "Acme Robotics builds autonomous robots for warehouses."},
        )

    expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
    calls = _pipeline_calls(call_log)
    expect(len(calls) == 1, "Expected exactly one pipeline call")
    expect(
        calls[0]["evidence_sources"] is None,
        "Legacy /analyze-startup must not pass evidence_sources",
    )
    expect(
        calls[0]["analysis_type"] == "public",
        "Legacy /analyze-startup must default to analysis_type='public'",
    )


def test_legacy_analyze_website_still_works() -> None:
    with patched_pipeline() as call_log:
        response = client.post("/analyze-website", json={"url": "https://example.com"})

    expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
    calls = _pipeline_calls(call_log)
    expect(len(calls) == 1, "Expected exactly one pipeline call")
    expect(
        calls[0]["evidence_sources"] is None,
        "Legacy /analyze-website must not pass evidence_sources",
    )


def test_legacy_analyze_pdf_still_works() -> None:
    with patched_pipeline() as call_log:
        response = client.post(
            "/analyze-pdf",
            files={"file": ("deck.pdf", _make_pdf_bytes(), "application/pdf")},
        )

    expect(response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}")
    calls = _pipeline_calls(call_log)
    expect(len(calls) == 1, "Expected exactly one pipeline call")
    expect(
        calls[0]["analysis_type"] == "pitch_deck",
        "Legacy /analyze-pdf must still stamp analysis_type='pitch_deck'",
    )
    expect(
        calls[0]["evidence_sources"] is None,
        "Legacy /analyze-pdf must not pass evidence_sources",
    )


def test_old_stored_analysis_context_without_evidence_sources_still_validates() -> None:
    """An AnalysisContext dict shaped like pre-this-change stored JSON (no
    evidence_sources key at all) must still construct validly and fall
    back to the pre-existing default, never error."""
    old_style = {
        "analysis_type": "public",
        "methodology_version": "v2-spec-2026-08-23",
    }
    context = AnalysisContext(**old_style)
    expect(
        context.evidence_sources == ["company_description"],
        f"Expected the pre-existing default to apply, got {context.evidence_sources!r}",
    )


TESTS = [
    test_website_only,
    test_pitch_deck_only,
    test_company_information_only,
    test_website_and_pitch_deck,
    test_website_and_company_information,
    test_pitch_deck_and_company_information,
    test_website_and_pitch_deck_and_company_information,
    test_zero_sources_rejected,
    test_invalid_supplied_website_rejects_entire_request,
    test_invalid_supplied_pdf_rejects_entire_request,
    test_assembled_input_size_bound,
    test_legacy_analyze_startup_still_works,
    test_legacy_analyze_website_still_works,
    test_legacy_analyze_pdf_still_works,
    test_old_stored_analysis_context_without_evidence_sources_still_validates,
]


def main() -> None:
    print("\nUnified Multi-Source Analyze Startup tests")
    print("-" * 72)

    failures: list[str] = []

    for test in TESTS:
        name = test.__name__

        try:
            test()
        except AssertionError as error:
            print(f"FAIL  {name}\n      {error}")
            failures.append(name)
        else:
            print(f"PASS  {name}")

    print("-" * 72)
    print(f"{len(TESTS) - len(failures)}/{len(TESTS)} passed")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
