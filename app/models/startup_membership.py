"""
Phase 7.1C -- Founder Membership Authorization Foundation. Response
contract only -- see app/database/db.py's own Phase 7.1C section for the
read-only query this backs, and its own statement of the claim-history-
vs-membership distinction this whole phase exists to enforce.

Its own file for the same reason app/models/startup_claim.py is its own
file (see that module's docstring): membership -- the current
authorization truth -- is a distinct concern from the claim
request/review lifecycle those models describe.
"""

from pydantic import BaseModel


class MyStartupMembership(BaseModel):
    """GET /me/startups row shape -- one row per startup_memberships
    relationship belonging to the caller. Structurally incapable of
    naming another user's membership, since
    get_startup_memberships_for_user() only ever selects rows matching
    the caller's own user_id. role always comes from the database row
    (currently always 'member' -- see approve_startup_claim()'s own
    invariant), never from anything a client could supply."""
    startup_id: int
    canonical_name: str
    role: str
