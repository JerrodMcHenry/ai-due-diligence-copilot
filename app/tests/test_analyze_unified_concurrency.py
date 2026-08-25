"""
Concurrency regression test for Unified Multi-Source Analyze Startup
(POST /analyze in app/api.py).

Unlike every other test in app/tests/, this one starts a REAL uvicorn
server on a local port -- proving the concurrency property requires an
actual ASGI server dispatching real concurrent connections; a FastAPI
TestClient (used by test_analyze_unified.py and elsewhere) runs
everything synchronously in-process and would not catch an event-loop-
blocking regression. run_due_diligence is monkeypatched to a slow,
deterministic stand-in so this test takes a few seconds, not minutes, and
makes no real LLM/Tavily calls.

Confirms the fix for the known /analyze-pdf bug (documented in the Pitch
Deck / PDF Ingestion completion report): declaring a FastAPI path
operation `async def` while doing fully synchronous, blocking work inside
it blocks the entire event loop, starving every other concurrent request
for the duration. POST /analyze is deliberately a sync `def` (see its own
comment in app/api.py) specifically to avoid this -- FastAPI/Starlette
automatically dispatches a sync path operation to a worker thread, which
is what keeps a slow /analyze request from blocking GET /health or
GET /analytics. This test is what proves that choice actually works, not
just that it looks right -- and (via the positive-control comment below)
was verified during implementation to actually fail against
/analyze-pdf's real async-with-blocking-internals shape.

Run with:
    python -m app.tests.test_analyze_unified_concurrency
"""

import threading
import time

import requests
import uvicorn

import app.api as api

PORT = 8099
SLOW_SECONDS = 3


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _slow_fake_run_due_diligence(*args, **kwargs):
    time.sleep(SLOW_SECONDS)
    raise RuntimeError("intentional fake failure -- only the timing matters here")


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


TESTS = [
    test_health_stays_responsive_during_a_slow_analysis,
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
