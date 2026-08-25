"""
Regression/security tests for Website / URL Ingestion (app/website_scrapper.py
and WebsiteAnalysisRequest in app/models/startup.py).

These exercise the SSRF-hardening layer directly: scheme allow-listing,
private/loopback/link-local/metadata-address rejection, DNS-rebinding-safe
IP pinning, bounded redirects with per-hop re-validation, and bounded
response size. Two cases (valid public HTTP/HTTPS URL) make a real,
outbound network call to https://example.com/ (IANA's dedicated
example-content domain -- stable, no auth, tiny response) since that's the
only way to prove the full fetch-and-pin path actually reaches a real
public site end to end; every other case is fully offline and
deterministic (private-network/scheme rejection short-circuits before any
network I/O, and the redirect/oversized-response cases fake the
connection pool rather than touching the network).

Run with:
    python -m app.tests.test_website_url_security
"""

from pydantic import ValidationError

import app.website_scrapper as ws
from app.models.startup import WebsiteAnalysisRequest
from app.website_scrapper import WebsiteFetchError, extract_text_from_website


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_rejected(url: str, message_substring: str = "") -> None:
    try:
        extract_text_from_website(url)
    except WebsiteFetchError as error:
        if message_substring:
            expect(
                message_substring.lower() in str(error).lower(),
                f"Expected rejection message to mention {message_substring!r}, "
                f"got {error!r}",
            )
        return

    raise AssertionError(f"Expected {url!r} to be rejected, but it was accepted.")


def test_valid_public_https_url_is_fetched() -> None:
    text = extract_text_from_website("https://example.com")
    expect(len(text) > 0, "Expected non-empty text from a real public HTTPS site.")


def test_valid_public_http_url_is_fetched() -> None:
    text = extract_text_from_website("http://example.com")
    expect(len(text) > 0, "Expected non-empty text from a real public HTTP site.")


def test_localhost_rejected() -> None:
    expect_rejected("http://localhost:8000/")


def test_loopback_ip_rejected() -> None:
    expect_rejected("http://127.0.0.1/", "private or internal")


def test_private_ipv4_rejected() -> None:
    for host in ("http://10.0.0.5/", "http://172.16.0.5/", "http://192.168.1.1/"):
        expect_rejected(host, "private or internal")


def test_link_local_and_metadata_rejected() -> None:
    # 169.254.169.254 is the AWS/GCP/Azure cloud metadata endpoint -- the
    # single highest-value SSRF target this guard exists to stop.
    expect_rejected("http://169.254.169.254/latest/meta-data/", "private or internal")


def test_non_http_scheme_rejected() -> None:
    for url in ("file:///etc/passwd", "ftp://example.com/", "gopher://example.com/"):
        expect_rejected(url, "http and https")


def test_malformed_url_rejected() -> None:
    expect_rejected("not a url")
    expect_rejected("http://")


def test_redirect_to_private_destination_rejected() -> None:
    """A URL that validates fine on its own but redirects to a private
    address must still be rejected -- the redirect target gets the exact
    same validation as the original URL, not a blind follow. Faked at the
    connection-pool level (not the network) so this is deterministic; the
    rejection itself is real, unmocked _resolve_validated_ip logic. Uses
    a public IP literal (8.8.8.8) as the "origin" so no real DNS lookup
    is needed to reach the fake redirect response.
    """

    class _FakeResponse:
        def __init__(self, status: int, headers: dict) -> None:
            self.status = status
            self.headers = headers

        def stream(self, chunk_size, decode_content=True):
            return iter([])

        def release_conn(self) -> None:
            pass

    class _FakeRedirectPool:
        def __init__(self, host, port, **kwargs) -> None:
            pass

        def request(self, method, path, headers=None, preload_content=None, redirect=None):
            return _FakeResponse(302, {"Location": "http://169.254.169.254/"})

        def close(self) -> None:
            pass

    original_http_pool = ws.urllib3.HTTPConnectionPool
    original_https_pool = ws.urllib3.HTTPSConnectionPool

    ws.urllib3.HTTPConnectionPool = _FakeRedirectPool
    ws.urllib3.HTTPSConnectionPool = _FakeRedirectPool

    try:
        expect_rejected("http://8.8.8.8/", "private or internal")
    finally:
        ws.urllib3.HTTPConnectionPool = original_http_pool
        ws.urllib3.HTTPSConnectionPool = original_https_pool


def test_oversized_response_rejected() -> None:
    class _FakeOversizedResponse:
        def stream(self, chunk_size, decode_content=True):
            remaining = ws.MAX_RESPONSE_BYTES + 1
            while remaining > 0:
                take = min(chunk_size, remaining)
                yield b"x" * take
                remaining -= take

    try:
        ws._read_bounded(_FakeOversizedResponse(), ws.MAX_RESPONSE_BYTES)
    except WebsiteFetchError:
        return

    raise AssertionError("Expected an oversized response to be rejected.")


def test_request_model_rejects_malformed_url() -> None:
    try:
        WebsiteAnalysisRequest(url="not a url")
    except ValidationError:
        return

    raise AssertionError(
        "Expected WebsiteAnalysisRequest to reject a URL missing http(s)://."
    )


def test_request_model_accepts_legitimate_url() -> None:
    request = WebsiteAnalysisRequest(url="https://example.com/about")
    expect(
        request.url == "https://example.com/about",
        f"Expected a legitimate URL to pass through unchanged, got {request.url!r}",
    )


TESTS = [
    test_valid_public_https_url_is_fetched,
    test_valid_public_http_url_is_fetched,
    test_localhost_rejected,
    test_loopback_ip_rejected,
    test_private_ipv4_rejected,
    test_link_local_and_metadata_rejected,
    test_non_http_scheme_rejected,
    test_malformed_url_rejected,
    test_redirect_to_private_destination_rejected,
    test_oversized_response_rejected,
    test_request_model_rejects_malformed_url,
    test_request_model_accepts_legitimate_url,
]


def main() -> None:
    print("\nWebsite / URL Ingestion security tests")
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
