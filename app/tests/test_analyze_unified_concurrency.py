"""
Concurrency regression test for Unified Multi-Source Analyze Startup
(POST /analyze in app/api.py) and, as of Phase 10.1B, for the same-user
concurrency lock in app/database/db.py's analysis_runs section.

Unlike every other test in app/tests/, this one starts a REAL uvicorn
server on a local port -- proving the concurrency property requires an
actual ASGI server dispatching real concurrent connections; a FastAPI
TestClient (used by test_analyze_unified.py and elsewhere) runs
everything synchronously in-process and would not catch a real race
condition or an event-loop-blocking regression. run_due_diligence is
monkeypatched to a slow, deterministic stand-in so these tests take a
few seconds, not minutes, and make no real LLM/Tavily calls.

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
slow code path.
test_second_concurrent_analysis_from_same_user_is_rejected_before_pipeline
below closes that gap: it presents real, verified JWTs (the same
local-RSA-keypair technique every other authenticated test file in this
project uses) specifically so the requests clear RequireAuth and the
monkeypatched multi-second sleep genuinely runs during the assertion
window -- a real proof, not an incidental one, and it is what actually
exercises the analysis_runs partial-unique-index race under genuine
concurrent load (a sequential TestClient-based test cannot: correctness
here specifically depends on what happens when two real threads hit the
database at nearly the same instant).

Phase 10.1A's own /analyze-pdf event-loop-blocking test was removed from
this file along with the /analyze-pdf route itself in Phase 10.1B (zero
frontend consumers) -- see test_analysis_usage_protection.py for the
tests proving that route (and /analyze-startup, /analyze-website) no
longer exist.

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
CONCURRENCY_LOCK_PORT = 8100
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


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKSClient:
    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey(_public_key)


def _make_token(sub: str) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
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


def test_second_concurrent_analysis_from_same_user_is_rejected_before_pipeline() -> None:
    """
    Phase 10.1B: proves the analysis_runs partial-unique-index
    concurrency lock (app/database/db.py) is genuinely race-safe under
    real concurrent load, not just correct when called sequentially.

    Fires three real, simultaneous HTTP requests against one real running
    server: two from the SAME user (USER_A_ID) and one from a DIFFERENT
    user (USER_B_ID). run_due_diligence is monkeypatched to sleep
    SLOW_SECONDS then raise -- slow enough that all three requests are
    genuinely in flight at once, and call-counted so this test can prove
    exactly how many of the three ever reached it.

    Expected outcome: exactly ONE of USER_A_ID's two requests reaches the
    (slow, failing) pipeline -- getting the same 502 the other endpoints'
    tests already expect from a failing pipeline -- and the OTHER gets
    409 immediately, without ever calling run_due_diligence at all.
    USER_B_ID's request is unaffected by USER_A_ID's lock and also
    reaches the pipeline. Total pipeline invocations across all three
    requests: exactly 2, never 3 -- the one hard number that proves the
    database-level lock, not application-level timing, is what's actually
    preventing the duplicate run.
    """
    call_count_lock = threading.Lock()
    call_count = {"value": 0}

    def counting_slow_fake_run_due_diligence(*args, **kwargs):
        with call_count_lock:
            call_count["value"] += 1
        time.sleep(SLOW_SECONDS)
        raise RuntimeError("intentional fake failure -- only call count/status matter here")

    original_run_due_diligence = api.run_due_diligence
    api.run_due_diligence = counting_slow_fake_run_due_diligence

    config = uvicorn.Config(api.app, host="127.0.0.1", port=CONCURRENCY_LOCK_PORT, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)

    USER_A_ID = "zztest_concurrency_lock_user_a"
    USER_B_ID = "zztest_concurrency_lock_user_b"
    results: dict = {}

    try:
        with _patched_auth():
            token_a = _make_token(USER_A_ID)
            token_b = _make_token(USER_B_ID)
            thread.start()
            time.sleep(2)  # let the server finish starting before hitting it

            def call_analyze(key: str, token: str, company_text: str):
                try:
                    response = requests.post(
                        f"http://127.0.0.1:{CONCURRENCY_LOCK_PORT}/analyze",
                        data={"company_text": company_text},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                    results[key] = response.status_code
                except Exception as error:
                    results[key] = f"error: {error}"

            thread_a1 = threading.Thread(target=call_analyze, args=("user_a_first", token_a, "User A's first submission"))
            thread_a2 = threading.Thread(target=call_analyze, args=("user_a_second", token_a, "User A's second submission"))
            thread_b1 = threading.Thread(target=call_analyze, args=("user_b_first", token_b, "User B's submission"))

            thread_a1.start()
            thread_a2.start()
            thread_b1.start()
            thread_a1.join()
            thread_a2.join()
            thread_b1.join()
    finally:
        server.should_exit = True
        time.sleep(1)
        api.run_due_diligence = original_run_due_diligence
        # Both requesting users authenticate for real, so both get real
        # `users` rows (get_or_create_user(), via get_current_user()) and
        # real analysis_runs rows -- clean up both, even on failure.
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM analysis_runs WHERE user_id = ANY(:ids)"), {"ids": [USER_A_ID, USER_B_ID]})
            connection.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": [USER_A_ID, USER_B_ID]})

    user_a_statuses = sorted([results.get("user_a_first"), results.get("user_a_second")])
    expect(
        user_a_statuses == [409, 502],
        f"Expected User A's two concurrent requests to be exactly one 409 and one 502, got {results}",
    )
    expect(
        results.get("user_b_first") == 502,
        f"Expected User B's request to reach the pipeline unaffected by User A's lock, got {results}",
    )
    expect(
        call_count["value"] == 2,
        f"Expected run_due_diligence to be called exactly twice (once per user, never for the rejected duplicate), got {call_count['value']}",
    )


TESTS = [
    test_health_stays_responsive_during_a_slow_analysis,
    test_second_concurrent_analysis_from_same_user_is_rejected_before_pipeline,
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
