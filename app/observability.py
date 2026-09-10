"""
Phase 40C -- Private Beta Deployment + Production Acceptance, Minimum
Viable Observability. Wires the sentry-sdk dependency that has sat unused
in requirements.txt since before this phase -- no new monitoring platform
introduced, per the phase's own explicit preference for reusing what's
already there.

Entirely opt-in: SENTRY_DSN unset (the default for local development, and
for any environment that hasn't configured one yet) means
init_observability() does nothing and capture_exception() is a no-op --
this module changes nothing about local dev, and a missing DSN never
breaks or degrades a request. There is no fallback identity, no guessed
default DSN -- exactly the same "unset means off, never a weaker guess"
discipline app/auth.py's CLERK_ISSUER and app/api.py's
CORS_ALLOWED_ORIGINS already follow.

Deliberately minimal, matching the phase's own "smallest useful
observability layer" instruction -- this is not a logging platform:

- Server-side exceptions: capture_exception() is called from each
  existing `except Exception:` block in app/api.py, right alongside its
  existing traceback.print_exc() call. It adds nothing to what already
  gets logged server-side; it only ALSO reports to Sentry when
  configured.
- Endpoint/path + timestamp: Sentry's Starlette/FastAPI auto-instrumentation
  (enabled automatically by sentry_sdk.init() when starlette/fastapi are
  importable, which they always are here) attaches the request path,
  method, and a timestamp to every event without any extra code here.
- Environment: the ENVIRONMENT env var (defaults to "development") is
  tagged on every event, so a staging failure can never be mistaken for
  a production one.
- Correlation: Sentry assigns every captured event its own event id,
  usable to look the failure up later -- no separate request-id scheme
  was built for this, since Sentry's own id already serves that purpose.

PII / sensitive-data discipline: `send_default_pii=False` is passed
explicitly (restated even though it's the SDK's own default) so a future
SDK default change can't silently start capturing more. `before_send`
additionally redacts any Authorization/Cookie header Sentry's own request
context would otherwise attach -- defense in depth, not a replacement for
send_default_pii=False. Nothing here ever passes founder financial data,
founder explanations, or full company descriptions to Sentry -- every
call site passes only the caught exception object itself; the request
body is never separately captured by anything in this module.
"""

import os

import sentry_sdk

_SENSITIVE_HEADER_NAMES = {"authorization", "cookie"}

_initialized = False


def _scrub_event(event: dict, hint: dict) -> dict:
    request = event.get("request")
    if isinstance(request, dict):
        headers = request.get("headers")
        if isinstance(headers, dict):
            for name in list(headers):
                if name.lower() in _SENSITIVE_HEADER_NAMES:
                    headers[name] = "[redacted]"
    return event


def init_observability() -> None:
    """
    Called once at API startup (app/api.py, before the app is otherwise
    configured). No-op when SENTRY_DSN is unset -- see this module's own
    docstring for why that's a deliberate fail-closed-to-nothing default,
    not a bug.
    """
    global _initialized

    dsn = os.getenv("SENTRY_DSN")

    if not dsn:
        print("Observability: SENTRY_DSN not set -- Sentry reporting is disabled.")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("ENVIRONMENT", "development"),
        # No performance tracing/profiling -- this phase's own scope is
        # "make a specific founder-reported failure diagnosable," not an
        # APM platform. Keeping this at 0 avoids sampling request bodies
        # or building a second, broader telemetry surface than asked for.
        traces_sample_rate=0.0,
        send_default_pii=False,
        before_send=_scrub_event,
    )
    _initialized = True
    print("Observability: Sentry reporting enabled.")


def capture_exception(exc: BaseException) -> None:
    """
    A no-op when Sentry isn't configured. Every call site in app/api.py
    pairs this with its own existing traceback.print_exc() -- server-side
    console logging is completely unchanged; this only ALSO reports to
    Sentry when SENTRY_DSN is set.
    """
    if not _initialized:
        return

    sentry_sdk.capture_exception(exc)
