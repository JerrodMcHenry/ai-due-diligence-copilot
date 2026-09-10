"""
Phase 40C -- Private Beta Deployment + Production Acceptance, Minimum
Viable Observability. Verifies app/observability.py's own two functions
directly -- no real Sentry account/DSN is available in this environment,
so these tests substitute a fake in-process transport (an object with a
capture_envelope method, sentry_sdk's own supported extension point) for
the real HTTPS transport. This proves the CODE PATH is correct end to
end (an exception reaches capture_exception() reaches sentry_sdk reaches
a transport) without requiring network access or a live Sentry project.
Confirming actual delivery to a real Sentry dashboard is a live-account
verification step this test suite cannot perform and does not claim to.

Hand-rolled PASS/FAIL runner, matching every other test file in this
directory -- no pytest/jest.
"""

import os

import sentry_sdk
from sentry_sdk.transport import Transport

from app import observability


class _FakeTransport(Transport):
    """Records every envelope sentry_sdk would otherwise send over HTTPS.
    Must actually subclass sentry_sdk's own Transport ABC -- make_transport()
    (sentry_sdk/transport.py) only honors options["transport"] via an
    `isinstance(ref_transport, Transport)` check; a plain duck-typed object
    is silently ignored in favor of constructing the real HttpTransport."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.envelopes = []

    def capture_envelope(self, envelope):
        self.envelopes.append(envelope)


def _reset_sentry_state():
    sentry_sdk.get_global_scope().set_client(sentry_sdk.Client())
    observability._initialized = False


TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


@test
def test_capture_exception_is_a_no_op_when_not_initialized():
    """The exact default state of every environment until SENTRY_DSN is
    explicitly configured -- local dev, and any not-yet-configured
    deployment. Must never raise, must never attempt to reach sentry_sdk
    at all."""
    _reset_sentry_state()
    try:
        observability.capture_exception(ValueError("should be swallowed silently"))
    except Exception as e:  # pragma: no cover - the whole point of this test
        raise AssertionError(f"capture_exception raised when uninitialized: {e}")


@test
def test_init_observability_is_a_no_op_when_sentry_dsn_unset():
    """Confirms init_observability() never calls sentry_sdk.init() at all
    when SENTRY_DSN is unset -- not merely that it doesn't crash. Uses the
    module's own _initialized flag as the observable signal."""
    _reset_sentry_state()
    original = os.environ.pop("SENTRY_DSN", None)
    try:
        observability.init_observability()
        expect(
            observability._initialized is False,
            "init_observability() marked itself initialized with no SENTRY_DSN set.",
        )
    finally:
        if original is not None:
            os.environ["SENTRY_DSN"] = original


@test
def test_capture_exception_reaches_a_configured_transport():
    """The real end-to-end proof: once Sentry IS configured (a valid-shaped
    DSN, matching what a real deployment would set), an exception passed
    to capture_exception() actually produces a captured envelope -- not
    just "didn't crash." A fake transport stands in for the real HTTPS
    one so this never touches the network or requires a live account."""
    _reset_sentry_state()
    fake_transport = _FakeTransport()

    sentry_sdk.init(
        # Syntactically valid DSN shape (sentry_sdk validates this at
        # init time) -- the host is deliberately fake since `transport=`
        # below intercepts every envelope before any network I/O happens.
        dsn="https://fake_public_key@fake.ingest.example.com/1",
        transport=fake_transport,
        send_default_pii=False,
        before_send=observability._scrub_event,
    )
    observability._initialized = True

    try:
        raise RuntimeError("Phase 40C observability acceptance test failure")
    except RuntimeError as exc:
        observability.capture_exception(exc)

    sentry_sdk.flush()

    expect(
        len(fake_transport.envelopes) == 1,
        f"Expected exactly one captured envelope, got {len(fake_transport.envelopes)}.",
    )


@test
def test_scrub_event_redacts_authorization_and_cookie_headers():
    """Defense-in-depth check independent of send_default_pii=False --
    even if a request's headers ever reached an event, this must never
    let a real bearer token or session cookie through to Sentry."""
    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer super-secret-token",
                "Cookie": "session=super-secret-session",
                "Content-Type": "application/json",
            }
        }
    }

    scrubbed = observability._scrub_event(event, {})

    headers = scrubbed["request"]["headers"]
    expect(headers["Authorization"] == "[redacted]", "Authorization header was not redacted.")
    expect(headers["Cookie"] == "[redacted]", "Cookie header was not redacted.")
    expect(headers["Content-Type"] == "application/json", "Unrelated header was altered.")


@test
def test_scrub_event_tolerates_missing_request_data():
    """An event with no request context at all (many exception events
    won't have one) must pass through unchanged, never raise."""
    event = {"message": "no request context here"}
    scrubbed = observability._scrub_event(event, {})
    expect(scrubbed == event, "Event without request context was unexpectedly altered.")


def main():
    print("-" * 74)
    passed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {fn.__name__}: {e}")
    print("-" * 74)
    print(f"{passed}/{len(TESTS)} passed")
    if passed != len(TESTS):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
