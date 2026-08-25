"""
Regression/security tests for Pitch Deck / PDF Ingestion
(app/pdf_extractor.py, and the analysis_type provenance threading in
app/workflows/due_diligence_workflow.py).

The extraction-side cases build real PDF bytes in-memory with reportlab
(already a production dependency, used by app/reporting/pdf_generator.py)
and pypdf's own writer -- no binary fixture files, no network calls, and
no LLM calls. The provenance cases exercise build_provenance_context()/
build_sie_methodology_analysis() directly with synthetic inputs, the same
no-LLM-calls approach test_stage_extraction.py already uses.

Run with:
    python -m app.tests.test_pdf_ingestion
"""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from app.models.analysis import (
    ExecutionAnalysisResult,
    FinancialAnalysisResult,
    FounderAnalysisResult,
    MarketAnalysisResult,
    ProductAnalysisResult,
    TractionAnalysisResult,
)
from app.pdf_extractor import (
    MAX_PAGES,
    MAX_PDF_BYTES,
    PdfExtractionError,
    extract_text_from_pdf,
)
from app.workflows.due_diligence_workflow import (
    build_provenance_context,
    build_sie_methodology_analysis,
)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_rejected(pdf_bytes: bytes, message_substring: str = "") -> None:
    try:
        extract_text_from_pdf(pdf_bytes)
    except PdfExtractionError as error:
        if message_substring:
            expect(
                message_substring.lower() in str(error).lower(),
                f"Expected rejection message to mention {message_substring!r}, "
                f"got {error!r}",
            )
        return

    raise AssertionError("Expected the PDF to be rejected, but it was accepted.")


def make_text_pdf(text: str = "Hello Startup World", pages: int = 1) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    for i in range(pages):
        c.drawString(100, 750, f"{text} (page {i + 1})")
        c.showPage()
    c.save()
    return buf.getvalue()


def make_blank_pdf(pages: int = 1) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    for _ in range(pages):
        c.showPage()
    c.save()
    return buf.getvalue()


def encrypt_pdf(pdf_bytes: bytes, user_password: str, owner_password: str) -> bytes:
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password=user_password, owner_password=owner_password)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_valid_text_layer_pdf_extracts() -> None:
    text = extract_text_from_pdf(make_text_pdf("Acme Robotics pitch deck"))
    expect(
        "Acme Robotics" in text,
        f"Expected extracted text to contain the source text, got {text!r}",
    )


def test_successful_multi_page_extraction() -> None:
    text = extract_text_from_pdf(make_text_pdf("Slide content", pages=5))
    expect(len(text) > 0, "Expected non-empty text from a multi-page deck.")
    expect(
        "page 1" in text and "page 5" in text,
        f"Expected text from every page to be present, got {text!r}",
    )


def test_non_pdf_renamed_pdf_rejected() -> None:
    # No PDF magic bytes at all -- e.g. a .txt or .docx file simply
    # renamed to end in .pdf before upload.
    expect_rejected(b"This is just a plain text file, not a PDF at all.")


def test_invalid_magic_bytes_rejected() -> None:
    # A real file format (zip) that is not a PDF, disguised with a .pdf
    # filename -- exercises the magic-byte check independent of the
    # "obviously not a file at all" case above.
    expect_rejected(b"PK\x03\x04" + b"\x00" * 100, "valid PDF")


def test_oversized_upload_rejected() -> None:
    expect_rejected(b"%PDF-1.4" + b"0" * (MAX_PDF_BYTES + 1), "too large")


def test_corrupt_truncated_pdf_rejected() -> None:
    # A real PDF header followed by garbage instead of a valid object
    # structure -- simulates a truncated/corrupted upload.
    expect_rejected(b"%PDF-1.4\n" + b"not a real pdf body" * 20, "corrupt")


def test_encrypted_password_protected_pdf_rejected() -> None:
    encrypted = encrypt_pdf(
        make_text_pdf("Confidential Deck"),
        user_password="realpassword",
        owner_password="ownerpassword",
    )
    expect_rejected(encrypted, "password-protected")


def test_permissions_only_encrypted_pdf_still_extracts() -> None:
    """
    A PDF encrypted with an empty user password (restricting printing/
    editing via the owner password only) is not actually
    password-protected from a reader's perspective -- it should extract
    normally, not be rejected as if it required a password.
    """
    permissions_only = encrypt_pdf(
        make_text_pdf("Owner Restricted Deck"),
        user_password="",
        owner_password="ownerpassword",
    )
    text = extract_text_from_pdf(permissions_only)
    expect(
        "Owner Restricted Deck" in text,
        f"Expected permissions-only PDF to extract normally, got {text!r}",
    )


def test_no_readable_text_pdf_rejected() -> None:
    expect_rejected(make_blank_pdf(), "no readable text")


def test_excessive_page_count_rejected() -> None:
    expect_rejected(make_text_pdf(pages=MAX_PAGES + 1), "too many pages")


def test_empty_file_rejected() -> None:
    expect_rejected(b"", "empty")


def _build_methodology_analysis(analysis_type: str | None = None):
    kwargs = {
        "structured_analysis": {
            "company_name": "DeckCo",
            "industry": "SaaS",
            "business_model": "Subscription",
        },
        "readiness": None,
        "founder_analysis": FounderAnalysisResult(),
        "market_analysis": MarketAnalysisResult(),
        "product_analysis": ProductAnalysisResult(),
        "execution_analysis": ExecutionAnalysisResult(),
        "traction_analysis": TractionAnalysisResult(),
        "financial_analysis": FinancialAnalysisResult(),
    }

    if analysis_type is not None:
        kwargs["analysis_type"] = analysis_type

    return build_sie_methodology_analysis(**kwargs)


def test_pitch_deck_analysis_type_persists_on_provenance_context() -> None:
    context = build_provenance_context(analysis_type="pitch_deck")
    expect(
        context.analysis_type == "pitch_deck",
        f"Expected analysis_type == 'pitch_deck', got {context.analysis_type!r}",
    )


def test_public_analysis_type_is_the_default() -> None:
    context = build_provenance_context()
    expect(
        context.analysis_type == "public",
        f"Expected the default analysis_type to stay 'public', got "
        f"{context.analysis_type!r}",
    )


def test_pitch_deck_analysis_type_flows_through_methodology_analysis() -> None:
    analysis = _build_methodology_analysis(analysis_type="pitch_deck")
    expect(
        analysis.analysis_context is not None
        and analysis.analysis_context.analysis_type == "pitch_deck",
        "Expected build_sie_methodology_analysis(analysis_type='pitch_deck') "
        f"to set analysis_context.analysis_type, got "
        f"{getattr(analysis.analysis_context, 'analysis_type', None)!r}",
    )


def test_public_ingestion_remains_analysis_type_public() -> None:
    """Text/website ingestion never pass analysis_type explicitly -- the
    default must stay "public" so this change is invisible to every
    existing ingestion path."""
    analysis = _build_methodology_analysis()
    expect(
        analysis.analysis_context is not None
        and analysis.analysis_context.analysis_type == "public",
        "Expected the default (no analysis_type passed) to remain "
        f"'public', got {getattr(analysis.analysis_context, 'analysis_type', None)!r}",
    )


TESTS = [
    test_valid_text_layer_pdf_extracts,
    test_successful_multi_page_extraction,
    test_non_pdf_renamed_pdf_rejected,
    test_invalid_magic_bytes_rejected,
    test_oversized_upload_rejected,
    test_corrupt_truncated_pdf_rejected,
    test_encrypted_password_protected_pdf_rejected,
    test_permissions_only_encrypted_pdf_still_extracts,
    test_no_readable_text_pdf_rejected,
    test_excessive_page_count_rejected,
    test_empty_file_rejected,
    test_pitch_deck_analysis_type_persists_on_provenance_context,
    test_public_analysis_type_is_the_default,
    test_pitch_deck_analysis_type_flows_through_methodology_analysis,
    test_public_ingestion_remains_analysis_type_public,
]


def main() -> None:
    print("\nPitch Deck / PDF Ingestion tests")
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
