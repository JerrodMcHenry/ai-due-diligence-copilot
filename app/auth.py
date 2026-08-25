"""
SIE Authentication Phase 2: FastAPI backend enforcement of Clerk-issued
identity. This is the real security boundary -- Phase 1's Next.js
proxy.ts/page-level auth.protect() is UX only, and is explicitly
documented as such there; a request that skips the frontend entirely and
calls this backend directly is only stopped here.

Verifies a Clerk session JWT (RS256, asymmetric -- no shared secret, no
custom crypto) against Clerk's own public JWKS, using PyJWT's built-in
PyJWKClient for key discovery/caching. This module never issues, stores,
or trusts a session on its own; it only verifies what Clerk already
signed.

Centralized on purpose: every endpoint that requires a signed-in user
depends on get_current_user() below rather than re-implementing any part
of this -- see app/api.py's four analyze endpoints for the only call
sites.
"""

import os
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, Request
from jwt import PyJWKClient

from app.database.db import get_or_create_user

# Env-driven, mirrors the existing CORS_ALLOWED_ORIGINS pattern in
# app/api.py. This is the Clerk instance's Frontend API URL (e.g.
# https://your-app.clerk.accounts.dev in dev, https://clerk.yourdomain.com
# in production) -- used both to validate the JWT `iss` claim and to
# derive the public JWKS discovery URL. Unlike CORS, there is no safe
# generic local-dev default here: "which Clerk instance" is not something
# a fallback value can guess correctly, so an unset CLERK_ISSUER fails
# every authenticated request closed (a clean 401), never open.
CLERK_ISSUER = os.getenv("CLERK_ISSUER", "").rstrip("/")

# Optional, comma-separated, mirrors CORS_ALLOWED_ORIGINS's own pattern --
# validates the JWT `azp` (authorized party) claim, i.e. which frontend
# origin actually requested this token, against known origins. Unset
# falls back to the same local-dev origins CORS already trusts by
# default, so local development needs no extra configuration.
_LOCAL_DEV_AUTHORIZED_PARTIES = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def _resolve_authorized_parties() -> list[str]:
    raw = os.getenv("CLERK_AUTHORIZED_PARTIES", "")
    parties = [p.strip() for p in raw.split(",") if p.strip()]
    return parties or _LOCAL_DEV_AUTHORIZED_PARTIES


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    """
    One cached PyJWKClient for the process -- PyJWKClient itself caches
    fetched signing keys internally, so this only avoids re-constructing
    the client (and losing that cache) on every single request. Raises
    if CLERK_ISSUER is unset; get_current_user() below always checks that
    first and returns a clean 401 rather than letting this propagate.
    """
    return PyJWKClient(f"{CLERK_ISSUER}/.well-known/jwks.json")


class AuthenticatedUser:
    """
    The authenticated identity, derived exclusively from a verified
    Clerk JWT -- never from anything a client supplied directly (a
    request body, a query param, a header the client controls the
    content of). user_id (the JWT `sub` claim) is Clerk's canonical
    external identity and the only field every caller can rely on.

    email is populated only when the verified token actually carries an
    `email` claim -- Clerk's default session token does not include one
    (only `sub`/`iss`/`azp`/`exp`/`nbf`/`iat`/`sid`/`jti` and a few
    plan/feature claims; email requires a custom JWT template, not
    configured here). It is never fabricated or guessed, and it is never
    used as a security identifier -- only user_id is.
    """

    __slots__ = ("user_id", "email")

    def __init__(self, user_id: str, email: str | None = None):
        self.user_id = user_id
        self.email = email


_INVALID_TOKEN_DETAIL = "Invalid or expired authentication token."
_AUTH_REQUIRED_DETAIL = "Authentication required."


def _extract_bearer_token(authorization_header: str | None) -> str:
    if not authorization_header:
        raise HTTPException(status_code=401, detail=_AUTH_REQUIRED_DETAIL)

    parts = authorization_header.split(" ", 1)

    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail=_AUTH_REQUIRED_DETAIL)

    return parts[1].strip()


def get_current_user(request: Request) -> AuthenticatedUser:
    """
    FastAPI dependency: verifies a Clerk-issued session JWT from the
    Authorization header and returns the authenticated identity, having
    already ensured a corresponding `users` row exists (see
    get_or_create_user()'s own docstring for why that's idempotent and
    ownership-free).

    Fails closed with a clean, generic 401 on every failure mode --
    missing header, malformed bearer token, invalid signature, expired
    token, wrong issuer, wrong authorized party, or any other
    verification error. The specific reason is logged server-side only
    (never in the HTTPException detail), so a real misconfiguration is
    still diagnosable without ever leaking token contents, JWKS/crypto
    internals, or stack traces to the client.
    """
    token = _extract_bearer_token(request.headers.get("authorization"))

    if not CLERK_ISSUER:
        print(
            "Clerk auth rejected: CLERK_ISSUER is not configured -- "
            "every authenticated request fails closed until it is set."
        )
        raise HTTPException(status_code=401, detail=_AUTH_REQUIRED_DETAIL)

    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=CLERK_ISSUER,
            options={"require": ["exp", "iat", "sub"]},
        )
    except Exception as e:
        # Deliberately broad: PyJWT raises distinct exception types for
        # an expired token, a bad signature, a wrong issuer, malformed
        # JSON, an unreachable JWKS endpoint, etc. -- all of them are the
        # same 401 to the client, and the same "log the real reason
        # server-side" here.
        print(f"Clerk token verification failed: {e}")
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)

    # azp (authorized party) validation: Clerk's own documented rule is
    # to skip this check entirely when a token has no azp claim at all
    # (not every token carries one), and otherwise require it to match a
    # known frontend origin -- exactly mirroring how CORS_ALLOWED_ORIGINS
    # already validates "which frontend is allowed to talk to this
    # backend" elsewhere in this file.
    azp = payload.get("azp")
    if azp is not None and azp not in _resolve_authorized_parties():
        print(f"Clerk token verification failed: azp {azp!r} is not an authorized party.")
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)

    user_id = payload.get("sub")
    if not user_id:
        print("Clerk token verification failed: no sub claim present.")
        raise HTTPException(status_code=401, detail=_INVALID_TOKEN_DETAIL)

    email = payload.get("email")  # almost always absent -- see AuthenticatedUser's docstring

    get_or_create_user(user_id, email)

    return AuthenticatedUser(user_id=user_id, email=email)


# Convenience alias for endpoint signatures -- `current_user: AuthenticatedUser
# = Depends(RequireAuth)` reads slightly cleaner than repeating
# `Depends(get_current_user)` at every call site, while still being the
# exact same dependency (no wrapping, no behavior difference).
RequireAuth = Depends(get_current_user)
