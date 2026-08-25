"""
Pitch Deck / PDF Ingestion: extracts the text content of an uploaded PDF so
it can enter the SAME canonical SIE pipeline (run_due_diligence) that
company_text/website input already goes through -- this module only
produces plain text, it never touches scoring, evidence, or persistence.

Hardened against the resource/malformed-input risks a PDF upload endpoint
faces:

1. A byte-size cap, checked before any parsing is attempted.
2. Magic-byte validation (the "%PDF-" header) in addition to the
   filename's .pdf suffix (checked by the caller) -- a renamed non-PDF
   file is rejected up front rather than failing deep inside the parser.
3. A page-count cap, checked as soon as pypdf can report it, before the
   (potentially expensive) per-page text-extraction loop runs.
4. Encrypted/password-protected PDFs are detected and given a clear,
   actionable message instead of falling through to a generic error --
   an empty-password decrypt is attempted first, since many PDFs are
   "encrypted" only to restrict printing/editing and open with no
   password at all.
5. Corrupt/malformed PDFs are caught both where pypdf opens the file and
   where it reads each page, and turned into the same clean,
   safe-to-display error every other rejection here uses.

Everything stays in memory (BytesIO) -- no temporary files are written
anywhere in this module, same as before hardening.
"""

from io import BytesIO

from pypdf import PasswordType, PdfReader

MAX_PDF_BYTES = 15 * 1024 * 1024  # 15 MB -- generous for a slide deck's images
MAX_PAGES = 200  # generous for any real pitch deck; guards pathological files
PDF_MAGIC_BYTES = b"%PDF-"
# The PDF spec allows the header to appear anywhere in the first 1024
# bytes (some generators prepend junk before it) -- checking that whole
# window instead of only byte 0 avoids false-rejecting a few real-world
# PDFs while still refusing anything that isn't a PDF at all.
_MAGIC_BYTES_SEARCH_WINDOW = 1024


class PdfExtractionError(ValueError):
    """
    A deliberate, safe-to-display failure validating or extracting a PDF
    -- every message raised as this (or plain ValueError, its parent)
    anywhere in this module is written to be shown to the end user as-is,
    the same contract app/website_scrapper.py's WebsiteFetchError follows.
    """


def validate_pdf_size(pdf_bytes: bytes) -> None:
    if len(pdf_bytes) == 0:
        raise PdfExtractionError("The uploaded file is empty.")

    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise PdfExtractionError(
            f"That PDF is too large to analyze (max "
            f"{MAX_PDF_BYTES // (1024 * 1024)} MB)."
        )


def _validate_magic_bytes(pdf_bytes: bytes) -> None:
    if PDF_MAGIC_BYTES not in pdf_bytes[:_MAGIC_BYTES_SEARCH_WINDOW]:
        raise PdfExtractionError(
            "That file doesn't look like a valid PDF. Please upload a PDF file."
        )


def _open_reader(pdf_bytes: bytes) -> PdfReader:
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception:
        # pypdf raises several distinct exception types for a
        # malformed/corrupt/truncated PDF, not just one -- deliberately
        # broad so all of them collapse to the same safe message.
        raise PdfExtractionError(
            "That PDF appears to be corrupted or malformed and could not be read."
        )

    if reader.is_encrypted:
        # Many "encrypted" PDFs only restrict printing/editing and
        # actually open with no password at all -- try that before
        # treating it as genuinely password-protected. Note:
        # PdfReader.is_encrypted reflects whether the file HAS an
        # encryption dictionary at all and stays True even after a
        # successful decrypt() -- the decrypt() return value (a
        # PasswordType) is the only reliable signal of whether it
        # actually unlocked, not is_encrypted checked again afterward.
        try:
            decrypt_result = reader.decrypt("")
        except Exception:
            decrypt_result = PasswordType.NOT_DECRYPTED

        if decrypt_result == PasswordType.NOT_DECRYPTED:
            raise PdfExtractionError(
                "That PDF is password-protected. Please upload an "
                "unprotected PDF."
            )

    return reader


def _validate_page_count(reader: PdfReader) -> None:
    try:
        page_count = len(reader.pages)
    except Exception:
        raise PdfExtractionError(
            "That PDF appears to be corrupted or malformed and could not be read."
        )

    if page_count == 0:
        raise PdfExtractionError("That PDF has no pages.")

    if page_count > MAX_PAGES:
        raise PdfExtractionError(
            f"That PDF has too many pages to analyze (max {MAX_PAGES})."
        )


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    validate_pdf_size(pdf_bytes)
    _validate_magic_bytes(pdf_bytes)

    reader = _open_reader(pdf_bytes)
    _validate_page_count(reader)

    text = ""

    for page in reader.pages:
        try:
            page_text = page.extract_text()
        except Exception:
            # One unreadable page shouldn't sink an otherwise-readable
            # deck -- skip it and keep going, the same tolerance the loop
            # already had for a page that simply returns no text.
            continue

        if page_text:
            text += page_text + "\n\n"

    cleaned_text = text.strip()

    if not cleaned_text:
        raise PdfExtractionError("No readable text found in PDF.")

    return cleaned_text
