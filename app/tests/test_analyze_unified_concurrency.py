"""
Concurrency regression test for Unified Multi-Source Analyze Startup
(POST /analyze in app/api.py) and, as of Phase 10.1A, for the
/analyze-pdf event-loop-blocking FIX.

Unlike every other test in app/tests/, this one starts a REAL uvicorn
server on a local port -- proving the concurrency property requires an
actual ASGI server dispatching real concurrent connections; a FastAPI
TestClient (used by test_analyze_unified.py and elsewhere) runs
everything synchronously in-process and would not catch an event-loop-
blocking regression. run_due_diligence is monkeypatched to a slow,
deterministic stand-in so this test takes a few seconds, not minutes, and
makes no real LLM/Tavily calls.

POST /analyze is deliberately a sync `def` (see its own comment in
app/api.py) specifically to avoid blocking the event loop --
FastAPI/Starlette automatically dispatches a sync path operation to a
worker thread, which is what keeps a slow /analyze request from blocking
GET /health or GET /analytics.

Note on test_health_stays_responsive_during_a_slow_analysis below: it
deliberately sends NO Authorization header, so /analyze's RequireAuth
dependency rejects it with a fast 401 before run_due_diligence is ever
reached -- the monkeypatched sleep never actually executes on this path.
The test's assertions still hold (a fast 401 obviously doesn't block
/health either), but this specific test does not by itself exercise the
slow code path. test_analyze_pdf_health_stays_responsive_during_a_slow_
analysis below closes that gap: it presents a real, verified JWT (the
same local-RSA-keypair technique every other authenticated test file in
this project uses) specifically so the request clears RequireAuth and
the monkeypatched multi-second sleep genuinely runs during the
assertion window -- a real proof, not an incidental one, and this is
the test that would have failed against /analyze-pdf's pre-Phase-10.1A
`async def` + direct-blocking-call shape.

Run with:
    python -m app.tests.test_analyze_unified_concurrency
"""

import threading
import time

import jwt as pyjwt
import requests
import uvicorn
from cryptography.hazmat.primitives.asymmetric import rsa

from sqlalchemy import text

import app.api as api
import app.auth as auth
from app.database.db import engine

PORT = 8099
PDF_PORT = 8100
SLOW_SECONDS = 3

TEST_ISSUER = "https://test-instance.clerk.accounts.dev"
TEST_AZP = "http://localhost:3000"

_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _slow_fake_run_due_diligence(*args, **kwargs):
    time.sleep(SLOW_SECONDS)
    raise RuntimeError("intentional fake failure -- only the timing matters here")


def _fake_extract_text_from_pdf(*args, **kwargs):
    # Only run_due_diligence's timing matters for this test -- avoids
    # needing a real, pypdf-parseable PDF fixture. _read_pdf_upload_sync()
    # (the actual object of Phase 10.1A's fix) still runs for real on
    # whatever bytes the test sends.
    return "fake extracted pitch deck text"


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKSClient:
    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey(_public_key)


def _make_token() -> str:
    now = int(time.time())
    payload = {
        "sub": "zztest_concurrency_pdf_user",
        "iss": TEST_ISSUER,
        "azp": TEST_AZP,
        "iat": now,
        "exp": now + 3600,
    }
    return pyjwt.encode(payload, _private_key, algorithm="RS256")


class _patched_auth:
    def __enter__(self):
        self._orig_issuer = auth.CLERK_ISSUER
        self._orig_jwks_client = auth._jwks_client
        self._orig_resolve_parties = auth._resolve_authorized_parties

        auth.CLERK_ISSUER = TEST_ISSUER
        auth._jwks_client = lambda: _FakeJWKSClient()
        auth._resolve_authorized_parties = lambda: [TEST_AZP]
        return self

    def __exit__(self, *exc):
        auth.CLERK_ISSUER = self._orig_issuer
        auth._jwks_client = self._orig_jwks_client
        auth._resolve_authorized_parties = self._orig_resolve_parties
        return False


def test_health_stays_responsive_during_a_slow_analysis() -> None:
    original_run_due_diligence = api.run_due_diligence
    api.run_due_diligence = _slow_fake_run_due_diligence

    config = uvicorn.Config(api.app, host="127.0.0.1", port=PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)

    results: dict = {}

    try:
        thread.start()
        time.sleep(2)  # let the server finish starting before hitting it

        def call_analyze():
            try:
                requests.post(
                    f"http://127.0.0.1:{PORT}/analyze",
                    data={"company_text": "x" * 50},
                    timeout=10,
                )
            except Exception:
                pass  # expected -- the fake raises; only /health's timing matters

        def call_health():
            time.sleep(0.5)  # ensure /analyze is already in flight
            start = time.time()
            response = requests.get(f"http://127.0.0.1:{PORT}/health", timeout=8)
            results["health_status"] = response.status_code
            results["health_latency"] = time.time() - start

        analyze_thread = threading.Thread(target=call_analyze)
        health_thread = threading.Thread(target=call_health)
        analyze_thread.start()
        health_thread.start()
        analyze_thread.join()
        health_thread.join()
    finally:
        server.should_exit = True
        time.sleep(1)
        api.run_due_diligence = original_run_due_diligence

    expect(
        results.get("health_status") == 200,
        f"Expected GET /health to succeed even during a slow /analyze call, got {results}",
    )
    expect(
        results.get("health_latency", 999) < 1.5,
        "GET /health took long enough to suggest it was queued behind the slow "
        f"/analyze request rather than served concurrently: {results}",
    )


def test_analyze_pdf_health_stays_responsive_during_a_slow_analysis() -> None:
    """
    Phase 10.1A: proves /analyze-pdf no longer blocks the event loop.
    Uses a REAL verified JWT (unlike the /analyze test above) so the
    request actually clears RequireAuth and reaches the monkeypatched
    multi-second run_due_diligence() sleep -- a genuine behavioral proof,
    not merely a source-string check that the endpoint says `def` instead
    of `async def`. Before the Phase 10.1A fix, this test would have
    failed: /analyze-pdf's old `async def` + un-thread-pooled
    run_due_diligence() call would have stalled this same server's event
    loop for SLOW_SECONDS, and GET /health would have queued behind it.
    """
    original_run_due_diligence = api.run_due_diligence
    original_extract_text_from_pdf = api.extract_text_from_pdf
    api.run_due_diligence = _slow_fake_run_due_diligence
    api.extract_text_from_pdf = _fake_extract_text_from_pdf

    config = uvicorn.Config(api.app, host="127.0.0.1", port=PDF_PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)

    results: dict = {}

    try:
        with _patched_auth():
            token = _make_token()
            thread.start()
            time.sleep(2)  # let the server finish starting before hitting it

            def call_analyze_pdf():
                try:
                    requests.post(
                        f"http://127.0.0.1:{PDF_PORT}/analyze-pdf",
                        files={"file": ("deck.pdf", b"%PDF-1.4 fake content", "application/pdf")},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                except Exception:
                    pass  # expected -- the fake raises; only /health's timing matters

            def call_health():
                time.sleep(0.5)  # ensure /analyze-pdf is already in flight
                start = time.time()
                response = requests.get(f"http://127.0.0.1:{PDF_PORT}/health", timeout=8)
                results["health_status"] = response.status_code
                results["health_latency"] = time.time() - start

            analyze_thread = threading.Thread(target=call_analyze_pdf)
            health_thread = threading.Thread(target=call_health)
            analyze_thread.start()
            health_thread.start()
            analyze_thread.join()
            health_thread.join()
    finally:
        server.should_exit = True
        time.sleep(1)
        api.run_due_diligence = original_run_due_diligence
        api.extract_text_from_pdf = original_extract_text_from_pdf
        # Unlike the /analyze test above (which never authenticates
        # successfully, so get_current_user()'s get_or_create_user() is
        # never reached), this test's request DOES clear RequireAuth for
        # real -- which means it also creates a real `users` row for the
        # test subject via the same lazy-synchronization path every real
        # authenticated request uses. Clean it up, even on failure.
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM users WHERE id = 'zztest_concurrency_pdf_user'"))

    expect(
        results.get("health_status") == 200,
        f"Expected GET /health to succeed even during a slow /analyze-pdf call, got {results}",
    )
    expect(
        results.get("health_latency", 999) < 1.5,
        "GET /health took long enough to suggest it was queued behind the slow "
        f"/analyze-pdf request rather than served concurrently: {results}",
    )


TESTS = [
    test_health_stays_responsive_during_a_slow_analysis,
    test_analyze_pdf_health_stays_responsive_during_a_slow_analysis,
]


def main() -> None:
    print("\nUnified Analyze Startup concurrency test")
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
