import os
import json
import hashlib
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

# P0 Product Trust Cleanup: reuse the single source of truth for "what
# counts as the current canonical methodology" rather than hardcoding the
# version string a second time here. sie_v2_methodology.py has no
# project-internal imports of its own, so this does not introduce a
# circular import or any real import cost.
from app.ai.sie_v2_methodology import METHODOLOGY_VERSION



load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Phase 10.1A -- Critical Security/Runtime Hardening: pool_pre_ping=True
# issues a cheap "SELECT 1"-style liveness check before handing out a
# pooled connection, transparently discarding and replacing one a
# managed Postgres provider has silently closed server-side (e.g. after
# an idle timeout) instead of letting the caller's next real query fail
# with a raw OperationalError. Pool size/overflow/recycle are left at
# SQLAlchemy's defaults -- nothing in this codebase holds a connection
# open for the duration of an LLM call (every DB interaction is a short
# engine.begin() block), so the default pool is sufficient for expected
# beta load and there is no evidence of an actual sizing problem to fix.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)



def create_tables():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS analyses (
                id SERIAL PRIMARY KEY,
                company_text TEXT NOT NULL,
                summary TEXT NOT NULL,
                risk_analysis TEXT NOT NULL,
                competitor_analysis TEXT,
                memo TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                structured_analysis TEXT,
                investment_score TEXT,
                founder_analysis TEXT,
                market_analysis TEXT,
                sources TEXT,
                traction_analysis TEXT
            )
        """))

    print("PostgreSQL tables created successfully.")


def add_analysis_columns():
    columns = [
        "sources TEXT",
        "traction_analysis TEXT",
    ]

    for column in columns:
            column_name = column.split()[0]

            try:
                with engine.begin() as connection:
                    connection.execute(text(
                        f"ALTER TABLE analyses ADD COLUMN {column}"
                ))
                print(f"{column_name} column added")
            except Exception as e:
                print(f"{column_name} migration skipped", e)


def add_scoring_columns():
    columns = [
        "market_score INTEGER",
        "team_score INTEGER",
        "product_score INTEGER",
        "competition_score INTEGER",
        "traction_score INTEGER",
        "financial_score INTEGER",
        "overall_score INTEGER",
        "recommendation TEXT",

    ]

    for column in columns:
            column_name = column.split()[0]

            try:
                with engine.begin() as connection:
                    connection.execute(text(
                    f"ALTER TABLE analyses ADD COLUMN {column}"
                ))
                print(f"{column_name} column added")
            except Exception as e:
                print(f"{column_name} migration skipped", e)

def add_benchmarking_columns():
    columns = [
        "industry TEXT",
        "stage TEXT",
        "business_model TEXT"

    ]

    for column in columns:
        column_name = column.split()[0]

        try:
            with engine.begin() as connection:
                connection.execute(text(
                    f"ALTER TABLE analyses ADD COLUMN {column}"
                ))
                print(f"{column_name} column added")
        except Exception as e:
            print(f"{column_name} migration skipped", e)

def add_company_name_column():
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE analyses ADD COLUMN company_name TEXT
            """))
            print("company_name column added")
    except Exception as e:
        print("company_name migration skipped", e)


def add_readiness_columns():
    columns = [
        "readiness_score INTEGER",
        "readiness_summary TEXT"
    ]

    for column in columns:
        column_name = column.split()[0]

        try:
            with engine.begin() as connection:
                connection.execute(text(
                    f"ALTER TABLE analyses ADD COLUMN {column}"
                ))
            print(f"{column_name} column added")

        except Exception as e:
            print(f"{column_name} migration skipped", e)


def create_score_history_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS score_history (
                id SERIAL PRIMARY KEY,
                analysis_id INTEGER REFERENCES analyses(id) ON DELETE CASCADE,
                company_name TEXT,
                industry TEXT,
                stage TEXT,
                business_model TEXT,
                market_score INTEGER,
                team_score INTEGER,
                product_score INTEGER,
                competition_score INTEGER,
                traction_score INTEGER,
                financial_score INTEGER,
                overall_score INTEGER,
                readiness_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("score_history table created successfully.")


# ---------------------------------------------------------------------------
# SIE Accounts & Ownership -- Canonical Startup Entity (first implementation
# slice; see the accompanying architecture design). This introduces a real
# `startups` row as the stable identity every canonical query (get_rankings,
# search_analyses, get_startup_by_name, get_sps_history,
# get_top_improving_startups) has always re-derived ad hoc via
# LOWER(TRIM(company_name)) grouping, instead of storing it anywhere.
#
# Foundation only in this slice: create_users_table() /
# create_startup_memberships_table() / create_saved_startups_table() exist
# so the schema is in place, but nothing populates them yet -- no
# authentication, no ownership assignment, no Saved Startups behavior.
# Every startup created by backfill_startup_ids() below is unowned by
# construction (it never touches startup_memberships), per the explicit
# product decision that analysis and ownership are separate concepts and
# analyzing a startup must never grant membership.
#
# None of the existing canonical read queries are migrated to use
# startup_id in this slice -- they are left completely untouched so this
# migration's correctness can be verified independently of any product
# behavior change (see the test suite and the stabilization report this
# slice produces).
# ---------------------------------------------------------------------------

def create_startups_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS startups (
                id SERIAL PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("startups table created successfully.")


def add_startup_id_column():
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE analyses ADD COLUMN startup_id INTEGER REFERENCES startups(id)"
            ))
        print("startup_id column added")
    except Exception as e:
        print("startup_id migration skipped", e)


def create_users_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("users table created successfully.")


def get_or_create_user(user_id: str, email: str | None = None) -> None:
    """
    SIE Authentication Phase 2 -- lazy users-table synchronization. Called
    by app/auth.py's get_current_user() dependency on every successfully
    authenticated request. Idempotent: ON CONFLICT DO NOTHING, so a
    user's first authenticated request creates their row and every
    request after that is a safe no-op -- never a duplicate, never an
    error, no explicit "does this user already exist" check needed first.

    Deliberately does not update email on conflict: Clerk is the actual
    identity source of truth (see the SIE Accounts & Ownership
    architecture design) -- this table exists only so
    startup_memberships/saved_startups have a stable local foreign-key
    target, not to mirror a Clerk profile. Whatever email was present (or
    not) on a user's first authenticated request is what's stored;
    keeping it in sync with Clerk on every change is explicitly out of
    scope here (no webhook infrastructure, per that design).

    This function creates ONLY a users row. It never touches
    startup_memberships or saved_startups -- authentication means "this
    user exists," never "this user owns a startup."
    """
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO users (id, email)
            VALUES (:id, :email)
            ON CONFLICT (id) DO NOTHING
        """), {"id": user_id, "email": email})


def create_startup_memberships_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS startup_memberships (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                startup_id INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
                role TEXT NOT NULL DEFAULT 'owner',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT startup_memberships_user_startup_key UNIQUE (user_id, startup_id)
            )
        """))

    print("startup_memberships table created successfully.")


# ---------------------------------------------------------------------------
# Phase 7.1A -- Startup Claim & Membership backend lifecycle.
#
# CORE INVARIANT, stated once here as the single source of truth: the
# ONLY code path in this entire application allowed to INSERT INTO
# startup_memberships is approve_startup_claim() below, and it only ever
# does so for a claim that was, at the instant of that same transaction,
# genuinely status='pending'. Submitting a claim, viewing a claim,
# rejecting a claim, and cancelling a claim all create ZERO membership
# rows -- this is enforced by construction (those functions simply never
# contain an INSERT INTO startup_memberships statement), not by a runtime
# check. Analyzing a startup, saving a startup, and creating a modeled
# venture have never touched this table and still don't -- see
# get_or_create_startup()'s, save_startup_for_user()'s, and
# create_modeled_venture()'s own docstrings.
#
# role is ALWAYS 'member' on approval, regardless of claim order. Phase
# 7.1's original design considered auto-assigning 'owner' to the first
# approved claimant; that was explicitly corrected before implementation
# -- approval order is not proof of superior ownership authority. Owner
# elevation is deferred to a future, intentionally-designed member-
# administration feature. startup_memberships.role's column/default are
# unchanged; every INSERT below simply specifies role='member' explicitly.
# ---------------------------------------------------------------------------

class StartupClaimError(Exception):
    """Base class for clean, application-level claim failures -- never a
    raw IntegrityError/psycopg2 exception surfacing to app/api.py."""


class StartupNotFoundError(StartupClaimError):
    pass


class DuplicatePendingClaimError(StartupClaimError):
    pass


class AlreadyMemberError(StartupClaimError):
    """Raised when the claimant already has an approved membership for
    this startup -- Part 3's 'an existing membership should prevent
    unnecessary duplicate claiming'."""


def create_startup_claims_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS startup_claims (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                startup_id INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
                verification_method TEXT NOT NULL DEFAULT 'manual_review',
                justification TEXT,
                contact_email TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewed_by TEXT REFERENCES users(id),
                rejection_reason TEXT
            )
        """))

    with engine.begin() as connection:
        # Partial unique index: at most one PENDING claim per
        # (user_id, startup_id) -- a rejected or cancelled prior claim
        # does NOT count toward this, so resubmission is always possible
        # (Part 6/9's explicit "rejected claim can be resubmitted").
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS startup_claims_one_pending_per_user_startup
            ON startup_claims (user_id, startup_id)
            WHERE status = 'pending'
        """))

    print("startup_claims table created successfully.")


def create_startup_claim(
    user_id: str,
    startup_id: int,
    justification: str,
    contact_email: str | None,
) -> int:
    """
    Creates exactly one pending startup_claims row. Never touches
    startup_memberships -- see this section's own module-level comment.

    Raises:
        StartupNotFoundError -- startup_id doesn't exist.
        AlreadyMemberError -- the caller already has an approved
            membership for this startup; a new claim would be redundant.
        DuplicatePendingClaimError -- the caller already has a pending
            claim for this startup (checked explicitly, then re-checked
            via the partial unique index itself as a race-safe fallback
            if two concurrent requests both pass the initial check).
    """
    with engine.begin() as connection:
        startup_exists = connection.execute(
            text("SELECT 1 FROM startups WHERE id = :startup_id"),
            {"startup_id": startup_id},
        ).scalar()

        if startup_exists is None:
            raise StartupNotFoundError(f"Startup {startup_id} does not exist")

        already_member = connection.execute(text("""
            SELECT 1 FROM startup_memberships
            WHERE user_id = :user_id AND startup_id = :startup_id
        """), {"user_id": user_id, "startup_id": startup_id}).scalar()

        if already_member is not None:
            raise AlreadyMemberError(
                f"User {user_id} is already a member of startup {startup_id}"
            )

        already_pending = connection.execute(text("""
            SELECT 1 FROM startup_claims
            WHERE user_id = :user_id AND startup_id = :startup_id AND status = 'pending'
        """), {"user_id": user_id, "startup_id": startup_id}).scalar()

        if already_pending is not None:
            raise DuplicatePendingClaimError(
                f"User {user_id} already has a pending claim for startup {startup_id}"
            )

        try:
            result = connection.execute(text("""
                INSERT INTO startup_claims (
                    user_id, startup_id, status, verification_method,
                    justification, contact_email
                )
                VALUES (
                    :user_id, :startup_id, 'pending', 'manual_review',
                    :justification, :contact_email
                )
                RETURNING id
            """), {
                "user_id": user_id,
                "startup_id": startup_id,
                "justification": justification,
                "contact_email": contact_email,
            })
        except IntegrityError as error:
            # Race-safe fallback: two concurrent requests could both pass
            # the already_pending check above before either commits: the
            # partial unique index itself is the final authority.
            raise DuplicatePendingClaimError(
                f"User {user_id} already has a pending claim for startup {startup_id}"
            ) from error

        return result.scalar()


def list_startup_claims_for_user(user_id: str):
    """Only the caller's OWN claims -- see GET /me/startup-claims in
    app/api.py. Deliberately excludes justification/contact_email (not
    part of Part 4's required field list for this endpoint) and every
    other user's data by construction (the WHERE clause is the only
    thing that can ever match a row)."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                sc.id AS id,
                sc.startup_id AS startup_id,
                s.canonical_name AS canonical_name,
                sc.status AS status,
                sc.verification_method AS verification_method,
                sc.submitted_at AS submitted_at,
                sc.reviewed_at AS reviewed_at,
                sc.rejection_reason AS rejection_reason
            FROM startup_claims sc
            JOIN startups s ON s.id = sc.startup_id
            WHERE sc.user_id = :user_id
            ORDER BY sc.submitted_at DESC
        """), {"user_id": user_id})

        return [dict(row) for row in result.mappings().all()]


def get_startup_claim_status_for_user(user_id: str, startup_id: int):
    """
    Smallest useful helper for Phase 7.1B's future 'Claim this startup'
    control: the caller's own most recent claim for this one startup, or
    None if they've never claimed it. Never reveals whether anyone ELSE
    has claimed or been approved for this startup -- scoped to user_id in
    the SQL itself, same discipline as every other per-user query in this
    file.
    """
    with engine.begin() as connection:
        row = connection.execute(text("""
            SELECT id, status, submitted_at, reviewed_at, rejection_reason
            FROM startup_claims
            WHERE user_id = :user_id AND startup_id = :startup_id
            ORDER BY submitted_at DESC
            LIMIT 1
        """), {"user_id": user_id, "startup_id": startup_id}).mappings().first()

        return dict(row) if row is not None else None


def list_pending_startup_claims_for_admin():
    """
    Admin-only READ -- authorization (RequireAdmin) is enforced entirely
    at the API layer in app/api.py, matching this file's existing
    convention that DB functions implement queries, not access control
    (e.g. get_saved_startups_for_user() doesn't re-check auth either; the
    endpoint does). This function has no per-user filter by design --
    an admin legitimately needs to see every pending claim.

    existing_member_count gives the reviewer context (Part 4/6: "already
    has a member" is information for the human, never a submission
    blocker) without a second round trip.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                sc.id AS id,
                sc.startup_id AS startup_id,
                s.canonical_name AS canonical_name,
                sc.user_id AS user_id,
                u.email AS user_email,
                sc.contact_email AS contact_email,
                sc.justification AS justification,
                sc.submitted_at AS submitted_at,
                (
                    SELECT COUNT(*) FROM startup_memberships sm
                    WHERE sm.startup_id = sc.startup_id
                ) AS existing_member_count
            FROM startup_claims sc
            JOIN startups s ON s.id = sc.startup_id
            JOIN users u ON u.id = sc.user_id
            WHERE sc.status = 'pending'
            ORDER BY sc.submitted_at ASC
        """))

        return [dict(row) for row in result.mappings().all()]


def approve_startup_claim(claim_id: int, admin_user_id: str):
    """
    THE ONLY function in this entire codebase that may INSERT INTO
    startup_memberships. Fully atomic in one transaction:

    1. SELECT ... FOR UPDATE locks this specific claim row for the
       duration of the transaction -- a concurrent second approval
       attempt on the SAME claim_id blocks here until this transaction
       commits or rolls back, then re-reads status and correctly finds
       it's no longer 'pending' (Part 9's "approval race cannot create
       duplicate memberships").
    2. If the claim doesn't exist or isn't currently pending (already
       approved/rejected/cancelled, or a concurrent approval already won
       the race), this returns None and writes NOTHING -- not an error,
       just "nothing to do".
    3. Otherwise: insert the membership (role ALWAYS 'member' -- see this
       section's own module-level comment), with ON CONFLICT DO NOTHING
       as a second, independent layer of duplicate protection (the
       existing UNIQUE(user_id, startup_id) constraint on
       startup_memberships), then mark the claim approved with
       reviewed_at/reviewed_by.

    Because both writes happen inside the same engine.begin() block, a
    failure in either one rolls back both -- an approved claim can never
    exist without its membership, and a failed claim-status update can
    never leave an unauthorized membership behind.
    """
    with engine.begin() as connection:
        claim = connection.execute(text("""
            SELECT id, user_id, startup_id, status
            FROM startup_claims
            WHERE id = :claim_id
            FOR UPDATE
        """), {"claim_id": claim_id}).mappings().first()

        if claim is None or claim["status"] != "pending":
            return None

        connection.execute(text("""
            INSERT INTO startup_memberships (user_id, startup_id, role)
            VALUES (:user_id, :startup_id, 'member')
            ON CONFLICT (user_id, startup_id) DO NOTHING
        """), {"user_id": claim["user_id"], "startup_id": claim["startup_id"]})

        connection.execute(text("""
            UPDATE startup_claims
            SET status = 'approved',
                reviewed_at = CURRENT_TIMESTAMP,
                reviewed_by = :admin_user_id
            WHERE id = :claim_id
        """), {"claim_id": claim_id, "admin_user_id": admin_user_id})

        return {
            "claim_id": claim_id,
            "user_id": claim["user_id"],
            "startup_id": claim["startup_id"],
        }


def reject_startup_claim(claim_id: int, admin_user_id: str, rejection_reason: str) -> bool:
    """Only a currently-pending claim transitions to rejected -- the
    WHERE status = 'pending' guard makes this a safe no-op (0 rows
    affected) against an already-decided or concurrently-decided claim.
    Creates zero startup_memberships rows, always."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE startup_claims
            SET status = 'rejected',
                reviewed_at = CURRENT_TIMESTAMP,
                reviewed_by = :admin_user_id,
                rejection_reason = :rejection_reason
            WHERE id = :claim_id AND status = 'pending'
        """), {
            "claim_id": claim_id,
            "admin_user_id": admin_user_id,
            "rejection_reason": rejection_reason,
        })

        return result.rowcount > 0


def cancel_startup_claim(user_id: str, claim_id: int) -> bool:
    """Claimant-only (WHERE user_id = :user_id), own-claim-only, and only
    a currently-pending claim can be cancelled. Zero membership effect."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE startup_claims
            SET status = 'cancelled'
            WHERE id = :claim_id AND user_id = :user_id AND status = 'pending'
        """), {"claim_id": claim_id, "user_id": user_id})

        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Phase 7.1C -- Founder Membership Authorization Foundation. Purely
# additive reads: no new table, no new INSERT path. startup_memberships
# remains write-once via approve_startup_claim() above -- that function's
# own module-level comment is still the single source of truth for "the
# only place this table is ever written."
#
# The distinction these two functions exist to enforce, ahead of Phase
# 7.2 Founder Workspace: an approved startup_claims row is historical
# evidence that approval happened once; a live startup_memberships row is
# the ONLY current authorization truth. Neither function below ever
# consults startup_claims, saved_startups, or modeled_ventures -- so if a
# membership-removal path is ever added in the future, these functions
# correctly stop authorizing access the instant the row is gone, even
# though the original claim would still read 'approved' forever (claims
# are an immutable historical record; see approve_startup_claim()'s own
# docstring -- it never rewrites a claim once decided).
# ---------------------------------------------------------------------------

def get_startup_memberships_for_user(user_id: str):
    """
    Every canonical startup this user currently has authorized access to
    -- one row per startup_memberships relationship belonging to them,
    derived from that table alone. A user with memberships at several
    startups gets one row each (no assumption anywhere that a user
    belongs to at most one startup); a startup with several members
    likewise has one independent row per member here, scoped by user_id
    in the WHERE clause the same way get_saved_startups_for_user() and
    list_startup_claims_for_user() are scoped.

    Deliberately does not join in SPS/industry/stage/or any other
    intelligence field -- see this section's own module-level comment.
    A future founder surface that needs current intelligence per startup
    should join out to canonical analyses via startup_id at read time,
    the same "join, don't copy" principle get_saved_startups_for_user()
    already applies.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                sm.id AS membership_id,
                sm.startup_id AS startup_id,
                s.canonical_name AS canonical_name,
                sm.role AS role,
                sm.created_at AS created_at
            FROM startup_memberships sm
            JOIN startups s ON s.id = sm.startup_id
            WHERE sm.user_id = :user_id
            ORDER BY sm.created_at ASC
        """), {"user_id": user_id})

        return [dict(row) for row in result.mappings().all()]


def user_has_startup_membership(user_id: str, startup_id: int) -> bool:
    """
    The single question every founder-only authorization check reduces
    to: does a live startup_memberships row exist for this exact
    (user_id, startup_id) pair? No claim history, no client-supplied
    role, no other table is ever consulted here -- see RequireStartupMember
    in app/auth.py, the intended caller for Phase 7.2's founder-only
    routes.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT 1 FROM startup_memberships
            WHERE user_id = :user_id AND startup_id = :startup_id
        """), {"user_id": user_id, "startup_id": startup_id})

        return result.first() is not None


# ---------------------------------------------------------------------------
# Phase 7.2 -- Founder Workspace V1. One read-only function, no new table,
# no new write path. Authorization for who may call this is entirely the
# caller's job (RequireStartupMember in app/auth.py) -- this function
# itself trusts startup_id unconditionally, same division of
# responsibility list_pending_startup_claims_for_admin() already
# documents for RequireAdmin.
# ---------------------------------------------------------------------------

def get_founder_startup_workspace(startup_id: int):
    """
    Everything Founder Workspace V1's default view needs for one startup,
    in one read: the canonical identity (from startups itself, so this
    resolves even for a startup with zero analyses yet), its latest
    canonical intelligence, and its full SPS history.

    Deliberately resolves the latest analysis by the real startup_id FK
    (analyses.startup_id) rather than by company_name string-matching --
    a stricter, more correct key than get_startup_by_name() uses, made
    possible here because the caller always already has a real startup_id
    (from startup_memberships, via RequireStartupMember) rather than a
    URL-provided name. Uses the exact same "methodology IS NOT NULL"
    filter as get_startup_by_name() (no additional methodology_version
    gate), so this always reports the same current SPS as the public
    Startup Profile for the same startup -- the two are never allowed to
    disagree about "what is this company's current intelligence".

    methodology/created_at are None when no canonical analysis exists yet
    for this startup -- never fabricated to a placeholder score. Returns
    None only if startup_id itself doesn't resolve to a real startups
    row, which should never happen once RequireStartupMember has already
    passed (a membership row can't exist for a startup_id that isn't
    real, per the FK), but is still checked so this function is safe to
    call on its own.
    """
    with engine.begin() as connection:
        startup_row = connection.execute(text("""
            SELECT id, canonical_name FROM startups WHERE id = :startup_id
        """), {"startup_id": startup_id}).mappings().first()

        if startup_row is None:
            return None

        analysis_row = connection.execute(text("""
            SELECT id, created_at, methodology
            FROM analyses
            WHERE startup_id = :startup_id
              AND methodology IS NOT NULL
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """), {"startup_id": startup_id}).mappings().first()

        history_rows = connection.execute(text("""
            SELECT
                id,
                created_at,
                methodology->>'startup_intelligence_score' AS sps
            FROM analyses
            WHERE startup_id = :startup_id
              AND methodology IS NOT NULL
            ORDER BY created_at ASC, id ASC
        """), {"startup_id": startup_id}).mappings().all()

    methodology = None
    created_at = None

    if analysis_row is not None:
        created_at = analysis_row["created_at"]
        methodology = analysis_row["methodology"]

        if isinstance(methodology, str):
            methodology = json.loads(methodology)

    return {
        "startup_id": startup_row["id"],
        "canonical_name": startup_row["canonical_name"],
        "created_at": created_at,
        "methodology": methodology,
        "sps_history": [
            {
                "analysis_id": row["id"],
                "created_at": row["created_at"],
                "startup_intelligence_score": (
                    float(row["sps"]) if row["sps"] is not None else None
                ),
            }
            for row in history_rows
        ],
    }


FOUNDER_ACTION_STATUSES = ("todo", "in_progress", "completed", "dismissed")
FOUNDER_ACTION_SOURCES = ("sie_recommendation", "founder_created")
FOUNDER_ACTION_PILLARS = (
    "market", "team", "product", "execution", "traction", "financial_health",
)


class FounderActionError(Exception):
    """Base class for clean, application-level founder-action failures --
    never a raw IntegrityError/psycopg2 exception surfacing to app/api.py.
    Mirrors StartupClaimError's own role for the claims section above."""


class FounderActionNotFoundError(FounderActionError):
    pass


# ---------------------------------------------------------------------------
# Phase 7.3 -- Founder Progress & Improvement V1. founder_actions is a
# dedicated, purely additive table -- it is NEVER read by, written by, or
# joined into anything in the scoring/methodology path (analyses,
# startup_intelligence_score, PillarAnalysis, VPS, calibration). It holds
# workflow state ONLY: what a founder intends to do or has done, never
# evidence and never a score. See this section's own tests
# (test_founder_actions.py) for the code-level audit proving that
# no function here ever writes analyses.methodology, any *_score column,
# or startup_memberships.
#
# Shared per-startup, not per-member (explicit product decision, Part 11):
# every list/update function below is scoped by startup_id alone --
# created_by_user_id is recorded for provenance/attribution only, never
# used to filter what a member can see or move between statuses. Any
# verified member of a startup sees and can act on the same plan.
# ---------------------------------------------------------------------------

def create_founder_actions_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS founder_actions (
                id SERIAL PRIMARY KEY,
                startup_id INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
                created_by_user_id TEXT NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                description TEXT,
                related_pillar TEXT,
                status TEXT NOT NULL DEFAULT 'todo'
                    CHECK (status IN ('todo', 'in_progress', 'completed', 'dismissed')),
                -- Phase 8 added 'fundraising_gap' alongside the original
                -- two values (see
                -- add_fundraising_gap_source_to_founder_actions() below
                -- for the matching migration on a database that already
                -- has this table) -- backward compatible, existing rows
                -- are untouched either way.
                source TEXT NOT NULL
                    CHECK (source IN ('sie_recommendation', 'founder_created', 'fundraising_gap')),
                -- Dedup key for non-founder-authored actions (see
                -- create_founder_action()'s own docstring) -- always NULL
                -- for founder_created, so the partial unique index below
                -- never constrains founder-authored text at all.
                source_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """))

        # Scoped to (startup_id, source_ref), not globally -- the exact
        # same recommendation/gap text for a DIFFERENT startup is a
        # distinct, legitimate row; only a second copy of the SAME
        # recommendation/gap for the SAME startup is blocked.
        # WHERE source <> 'founder_created' covers both
        # 'sie_recommendation' and Phase 8's 'fundraising_gap' (and any
        # future non-founder-authored source) with one predicate, while
        # founder_created rows (whose source_ref is always NULL) are
        # never constrained by it at all -- see create_founder_action()'s
        # own docstring for why founder-authored text is deliberately
        # never deduplicated.
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS founder_actions_dedup_sie_recommendation
            ON founder_actions (startup_id, source_ref)
            WHERE source <> 'founder_created'
        """))

    print("founder_actions table created successfully.")


def add_fundraising_gap_source_to_founder_actions():
    """
    Phase 8 migration for a database where founder_actions already
    exists from Phase 7.3/CREATE TABLE IF NOT EXISTS never re-runs the
    body above. Idempotent: DROP ... IF EXISTS + CREATE, safe to call on
    every startup. Widens the CHECK constraint to allow 'fundraising_gap'
    and widens the dedup index's predicate to match (see
    create_founder_actions_table()'s own comment for why
    `source <> 'founder_created'` is the correct predicate for both).
    Never touches existing rows.
    """
    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE founder_actions DROP CONSTRAINT IF EXISTS founder_actions_source_check
        """))
        connection.execute(text("""
            ALTER TABLE founder_actions ADD CONSTRAINT founder_actions_source_check
            CHECK (source IN ('sie_recommendation', 'founder_created', 'fundraising_gap'))
        """))
        connection.execute(text("""
            DROP INDEX IF EXISTS founder_actions_dedup_sie_recommendation
        """))
        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS founder_actions_dedup_sie_recommendation
            ON founder_actions (startup_id, source_ref)
            WHERE source <> 'founder_created'
        """))

    print("founder_actions.source migrated to include fundraising_gap.")


def list_founder_actions_for_startup(startup_id: int):
    """Every action for this startup, regardless of who created it or its
    current status -- the frontend groups by status client-side (Next Up
    / In Progress / Completed / dismissed items simply omitted from the
    default view). Authorization (RequireStartupMember) is enforced
    entirely at the API layer, matching this file's existing convention
    (e.g. list_pending_startup_claims_for_admin()'s own docstring)."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                id, startup_id, created_by_user_id, title, description,
                related_pillar, status, source, source_ref,
                created_at, updated_at, completed_at
            FROM founder_actions
            WHERE startup_id = :startup_id
            ORDER BY created_at ASC
        """), {"startup_id": startup_id})

        return [dict(row) for row in result.mappings().all()]


def create_founder_action(
    startup_id: int,
    created_by_user_id: str,
    title: str,
    description: str | None,
    related_pillar: str | None,
    source: str,
):
    """
    Creates one founder_actions row, OR -- for a non-founder-authored
    action (source='sie_recommendation' or, since Phase 8,
    'fundraising_gap') whose exact title already exists for this startup
    -- returns the existing row untouched instead of erroring or
    creating a duplicate. This is the "Add to Plan" idempotency guarantee
    (Part 13/Phase 8 Part 16): clicking it twice on the same suggested
    recommendation or fundraising gap is a safe no-op, never a second
    row, never a 409 the frontend has to explain.

    source_ref (the dedup key) is derived HERE from title, never accepted
    from the caller -- there is no client-supplied identity field to
    spoof or collide. founder_created rows always get source_ref=None,
    so two founder-authored actions with coincidentally identical text
    are both kept -- see this function's own module-level comment for why
    that's deliberate (founder text is not deduplicated).

    Existing-row lookup on conflict is a second, separate SELECT rather
    than relying on RETURNING (which is empty on an ON CONFLICT DO
    NOTHING no-op) -- both happen inside the same transaction, so this
    is still atomic with respect to a concurrent identical insert.
    """
    source_ref = title.strip() if source != "founder_created" else None

    with engine.begin() as connection:
        result = connection.execute(text("""
            INSERT INTO founder_actions (
                startup_id, created_by_user_id, title, description,
                related_pillar, status, source, source_ref
            )
            VALUES (
                :startup_id, :created_by_user_id, :title, :description,
                :related_pillar, 'todo', :source, :source_ref
            )
            ON CONFLICT (startup_id, source_ref)
                WHERE source <> 'founder_created'
                DO NOTHING
            RETURNING
                id, startup_id, created_by_user_id, title, description,
                related_pillar, status, source, source_ref,
                created_at, updated_at, completed_at
        """), {
            "startup_id": startup_id,
            "created_by_user_id": created_by_user_id,
            "title": title,
            "description": description,
            "related_pillar": related_pillar,
            "source": source,
            "source_ref": source_ref,
        })

        row = result.mappings().first()

        if row is not None:
            return dict(row)

        # Conflict: an sie_recommendation with this exact title already
        # exists for this startup -- return it as-is (see this function's
        # own docstring; never revives a dismissed one, never duplicates).
        existing = connection.execute(text("""
            SELECT
                id, startup_id, created_by_user_id, title, description,
                related_pillar, status, source, source_ref,
                created_at, updated_at, completed_at
            FROM founder_actions
            WHERE startup_id = :startup_id AND source_ref = :source_ref
        """), {"startup_id": startup_id, "source_ref": source_ref}).mappings().first()

        return dict(existing)


def update_founder_action_status(startup_id: int, action_id: int, new_status: str):
    """
    Returns the updated row, or None if this action_id doesn't exist for
    this exact startup_id (never revealing whether it exists for a
    DIFFERENT startup -- the WHERE clause is what makes a cross-startup
    update structurally impossible, not a check performed after the
    fact, same discipline as update_modeled_venture_for_user()'s own
    user_id-scoped WHERE clause).

    completed_at is set to NOW() only on a transition INTO 'completed',
    and cleared back to NULL on any transition AWAY from it (the
    "reopen" case) -- never touched for a lateral move between the other
    three statuses. updated_at always advances.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE founder_actions
            SET status = :new_status,
                updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE
                    WHEN :new_status = 'completed' THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
            WHERE id = :action_id AND startup_id = :startup_id
            RETURNING
                id, startup_id, created_by_user_id, title, description,
                related_pillar, status, source, source_ref,
                created_at, updated_at, completed_at
        """), {"new_status": new_status, "action_id": action_id, "startup_id": startup_id})

        row = result.mappings().first()
        return dict(row) if row is not None else None


FOUNDER_UPDATE_TYPES = (
    "customer", "revenue", "product", "team", "fundraising",
    "partnership", "validation", "operations", "other",
)
MILESTONE_STATUSES = ("planned", "in_progress", "achieved", "cancelled")

FOUNDER_UPDATE_COLUMNS = """
    id, startup_id, created_by_user_id, update_type, title, description,
    related_pillar, metric_name, metric_value, metric_unit,
    occurred_at, created_at, updated_at
"""

MILESTONE_COLUMNS = """
    id, startup_id, created_by_user_id, title, description,
    related_pillar, status, target_date, completed_at,
    created_at, updated_at
"""

# ---------------------------------------------------------------------------
# Phase 7.4 -- Founder Evidence + Milestones V1. Two dedicated, purely
# additive tables -- founder_updates and startup_milestones -- neither
# ever read by, written by, or joined into anything in the scoring/
# methodology path (analyses, startup_intelligence_score, PillarAnalysis,
# VPS, calibration). Both hold FOUNDER-REPORTED operational record only,
# same "workflow state, never evidence, never a score" boundary
# founder_actions established in Phase 7.3 -- see this section's own
# tests (test_founder_updates.py, test_startup_milestones.py) for the
# code-level audit.
#
# Distinct from app/models/evidence.py's Evidence model on purpose: that
# Evidence is CANONICAL pillar-analysis evidence (LLM-extracted, embedded
# in PillarAnalysis.evidence, assessed against Public/Inferred/Private
# rules) -- a completely different epistemic standard from "a founder
# typed a sentence into a form." founder_updates rows are never inserted
# into methodology.evidence, and no function in this file ever performs
# that conversion. A founder update becomes part of canonical evidence
# only if the founder separately, deliberately re-analyzes and mentions
# it in what they submit -- exactly like any other self-reported fact
# fed into the existing pipeline, no different or more privileged than
# before this phase existed.
#
# Shared per-startup, not per-member (same Part 11 decision Phase 7.3
# made for founder_actions): every function below is scoped by
# startup_id alone -- created_by_user_id is attribution only.
# ---------------------------------------------------------------------------

def create_founder_updates_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS founder_updates (
                id SERIAL PRIMARY KEY,
                startup_id INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
                created_by_user_id TEXT NOT NULL REFERENCES users(id),
                update_type TEXT NOT NULL CHECK (update_type IN (
                    'customer', 'revenue', 'product', 'team', 'fundraising',
                    'partnership', 'validation', 'operations', 'other'
                )),
                title TEXT NOT NULL,
                description TEXT,
                related_pillar TEXT,
                -- Optional structured metric (Part 9) -- deliberately just
                -- three plain nullable columns, no metrics platform, no
                -- separate metrics table, no charting. All three are
                -- either all present or all absent; enforced at the API
                -- layer (CreateFounderUpdateRequest), not here, matching
                -- this file's existing convention that DB functions
                -- implement writes, not validation.
                metric_name TEXT,
                metric_value NUMERIC,
                metric_unit TEXT,
                occurred_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("founder_updates table created successfully.")


def list_founder_updates_for_startup(startup_id: int):
    """Every update for this startup, regardless of who recorded it --
    newest-first by occurred_at (the founder-chosen "when did this
    happen" date, not necessarily when the row was inserted), which is
    what a Recent Updates timeline actually wants. Authorization
    (RequireStartupMember) is enforced entirely at the API layer, same
    convention as list_founder_actions_for_startup()."""
    with engine.begin() as connection:
        result = connection.execute(text(f"""
            SELECT {FOUNDER_UPDATE_COLUMNS}
            FROM founder_updates
            WHERE startup_id = :startup_id
            ORDER BY occurred_at DESC, created_at DESC
        """), {"startup_id": startup_id})

        return [dict(row) for row in result.mappings().all()]


def create_founder_update(
    startup_id: int,
    created_by_user_id: str,
    update_type: str,
    title: str,
    description: str | None,
    related_pillar: str | None,
    occurred_at,
    metric_name: str | None = None,
    metric_value: float | None = None,
    metric_unit: str | None = None,
):
    """No deduplication of any kind -- unlike founder_actions' SIE-
    recommendation dedup, every founder update is a genuinely distinct
    reported event even if the text happens to repeat (a founder may
    legitimately report "Signed a new customer" multiple times)."""
    with engine.begin() as connection:
        result = connection.execute(text(f"""
            INSERT INTO founder_updates (
                startup_id, created_by_user_id, update_type, title,
                description, related_pillar, metric_name, metric_value,
                metric_unit, occurred_at
            )
            VALUES (
                :startup_id, :created_by_user_id, :update_type, :title,
                :description, :related_pillar, :metric_name, :metric_value,
                :metric_unit, :occurred_at
            )
            RETURNING {FOUNDER_UPDATE_COLUMNS}
        """), {
            "startup_id": startup_id,
            "created_by_user_id": created_by_user_id,
            "update_type": update_type,
            "title": title,
            "description": description,
            "related_pillar": related_pillar,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_unit": metric_unit,
            "occurred_at": occurred_at,
        })

        return dict(result.mappings().first())


def update_founder_update(
    startup_id: int,
    update_id: int,
    update_type: str,
    title: str,
    description: str | None,
    related_pillar: str | None,
    occurred_at,
    metric_name: str | None = None,
    metric_value: float | None = None,
    metric_unit: str | None = None,
):
    """Full-field correction, not a partial patch -- same shape as
    update_modeled_venture_for_user()'s own precedent (every editable
    field is supplied on every call, avoiding the ambiguity of "field
    absent" vs. "field explicitly cleared"). Returns None if this
    update_id doesn't exist for this exact startup_id -- same
    non-leaking, WHERE-clause-scoped discipline as
    update_founder_action_status()."""
    with engine.begin() as connection:
        result = connection.execute(text(f"""
            UPDATE founder_updates
            SET update_type = :update_type,
                title = :title,
                description = :description,
                related_pillar = :related_pillar,
                metric_name = :metric_name,
                metric_value = :metric_value,
                metric_unit = :metric_unit,
                occurred_at = :occurred_at,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :update_id AND startup_id = :startup_id
            RETURNING {FOUNDER_UPDATE_COLUMNS}
        """), {
            "update_type": update_type,
            "title": title,
            "description": description,
            "related_pillar": related_pillar,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_unit": metric_unit,
            "occurred_at": occurred_at,
            "update_id": update_id,
            "startup_id": startup_id,
        })

        row = result.mappings().first()
        return dict(row) if row is not None else None


def create_startup_milestones_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS startup_milestones (
                id SERIAL PRIMARY KEY,
                startup_id INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
                created_by_user_id TEXT NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                description TEXT,
                related_pillar TEXT,
                status TEXT NOT NULL DEFAULT 'planned'
                    CHECK (status IN ('planned', 'in_progress', 'achieved', 'cancelled')),
                target_date DATE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("startup_milestones table created successfully.")


def list_startup_milestones_for_startup(startup_id: int):
    with engine.begin() as connection:
        result = connection.execute(text(f"""
            SELECT {MILESTONE_COLUMNS}
            FROM startup_milestones
            WHERE startup_id = :startup_id
            ORDER BY created_at ASC
        """), {"startup_id": startup_id})

        return [dict(row) for row in result.mappings().all()]


def create_startup_milestone(
    startup_id: int,
    created_by_user_id: str,
    title: str,
    description: str | None,
    related_pillar: str | None,
    target_date,
):
    """New milestones always start 'planned' -- no other status is ever
    accepted at creation time, matching create_founder_action()'s own
    "status always starts at the initial value" discipline."""
    with engine.begin() as connection:
        result = connection.execute(text(f"""
            INSERT INTO startup_milestones (
                startup_id, created_by_user_id, title, description,
                related_pillar, status, target_date
            )
            VALUES (
                :startup_id, :created_by_user_id, :title, :description,
                :related_pillar, 'planned', :target_date
            )
            RETURNING {MILESTONE_COLUMNS}
        """), {
            "startup_id": startup_id,
            "created_by_user_id": created_by_user_id,
            "title": title,
            "description": description,
            "related_pillar": related_pillar,
            "target_date": target_date,
        })

        return dict(result.mappings().first())


def update_startup_milestone_status(startup_id: int, milestone_id: int, new_status: str):
    """Same completed_at discipline as update_founder_action_status():
    set to NOW() only on a transition INTO 'achieved', cleared back to
    NULL on any transition away from it (the "reopen" case). Marking a
    milestone 'achieved' or 'cancelled' never touches analyses,
    methodology, or any *_score column -- see this section's own
    module-level comment and test_startup_milestones.py's static audit."""
    with engine.begin() as connection:
        result = connection.execute(text(f"""
            UPDATE startup_milestones
            SET status = :new_status,
                updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE
                    WHEN :new_status = 'achieved' THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
            WHERE id = :milestone_id AND startup_id = :startup_id
            RETURNING {MILESTONE_COLUMNS}
        """), {"new_status": new_status, "milestone_id": milestone_id, "startup_id": startup_id})

        row = result.mappings().first()
        return dict(row) if row is not None else None


def create_saved_startups_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS saved_startups (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                startup_id INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT saved_startups_user_startup_key UNIQUE (user_id, startup_id)
            )
        """))

    print("saved_startups table created successfully.")


# ---------------------------------------------------------------------------
# Saved Startups / Watchlist -- Phase 1. saved_startups is a pure
# relationship table (user_id, startup_id) -- see create_saved_startups_table()
# above. These four functions are the ONLY code that reads or writes it.
#
# Deliberately does NOT copy SPS, company_name, industry, stage, or any
# other intelligence field into saved_startups at save time -- a saved
# startup points at startups.id only, and get_saved_startups_for_user()
# below joins out to the LATEST canonical (methodology_version-matching)
# analysis for that startup_id every time it's called, so a user's
# watchlist always reflects current intelligence, never a stale snapshot
# frozen at save time. This is the same "join out to current state, don't
# copy" principle get_rankings()/search_analyses() already use for
# "latest analysis per startup" -- applied here across a relationship
# table instead of within analyses itself.
#
# None of these functions ever touch startup_memberships. Saving a
# startup is a bookmark, not a claim of ownership -- see the SIE Accounts
# & Ownership architecture design and get_or_create_user()'s own
# docstring for the same principle applied to authentication.
# ---------------------------------------------------------------------------

def save_startup_for_user(user_id: str, startup_id: int) -> bool:
    """
    Idempotent: ON CONFLICT (user_id, startup_id) DO NOTHING means saving
    an already-saved startup is a safe no-op, never a duplicate row and
    never an error. Returns True if a new row was created, False if the
    startup was already saved (both are success outcomes to the caller;
    see app/api.py's save endpoint).

    Raises ValueError for a startup_id that doesn't exist in startups --
    saved_startups.startup_id has a real FK constraint, so this always
    fails cleanly (never a half-written row) on an invalid id; the FK
    violation is caught here and translated into a clean, callable-facing
    error rather than leaking a raw IntegrityError/psycopg2 exception up
    to app/api.py.
    """
    try:
        with engine.begin() as connection:
            result = connection.execute(text("""
                INSERT INTO saved_startups (user_id, startup_id)
                VALUES (:user_id, :startup_id)
                ON CONFLICT (user_id, startup_id) DO NOTHING
            """), {"user_id": user_id, "startup_id": startup_id})

            return result.rowcount > 0
    except IntegrityError as error:
        raise ValueError(f"Startup {startup_id} does not exist") from error


def unsave_startup_for_user(user_id: str, startup_id: int) -> bool:
    """
    Idempotent: deleting a row that isn't there deletes zero rows, not an
    error -- unsaving an already-unsaved (or never-saved) startup is
    always safe. Returns True if a row was actually removed, False if
    there was nothing to remove.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            DELETE FROM saved_startups
            WHERE user_id = :user_id AND startup_id = :startup_id
        """), {"user_id": user_id, "startup_id": startup_id})

        return result.rowcount > 0


def is_startup_saved_by_user(user_id: str, startup_id: int) -> bool:
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT 1 FROM saved_startups
            WHERE user_id = :user_id AND startup_id = :startup_id
        """), {"user_id": user_id, "startup_id": startup_id})

        return result.first() is not None


def get_saved_startups_for_user(user_id: str):
    """
    One row per startup this user has saved, most-recently-saved first.
    Each row's intelligence fields (industry, stage, overall_score,
    latest_analysis_at) come from a LEFT JOIN LATERAL that independently
    resolves that startup's own latest canonical (methodology_version ==
    current) analysis via analyses.startup_id -- the real FK written by
    get_or_create_startup()/save_analysis(), not a re-derivation via
    company_name normalization the way get_rankings() still does (see
    that function's own docstring for why it hasn't been migrated to the
    FK) -- so this always reflects current intelligence, never a snapshot
    from whenever the startup was saved.

    LEFT (not INNER) JOIN LATERAL deliberately: a startup a user saved
    can, in principle, currently have zero canonical analyses (e.g. its
    only analysis predates Methodology v2, or predates the write path and
    was never backfilled with a matching canonical row). That startup
    still appears in the list -- with null intelligence fields -- rather
    than silently vanishing from a list the user explicitly built. No
    field here is ever fabricated to fill the gap.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                ss.startup_id AS startup_id,
                ss.created_at AS saved_at,
                startups.canonical_name AS company_name,
                latest.industry AS industry,
                latest.stage AS stage,
                latest.overall_score AS overall_score,
                latest.created_at AS latest_analysis_at
            FROM saved_startups ss
            JOIN startups ON startups.id = ss.startup_id
            LEFT JOIN LATERAL (
                SELECT
                    industry,
                    stage,
                    (methodology->>'startup_intelligence_score')::float AS overall_score,
                    created_at
                FROM analyses
                WHERE analyses.startup_id = ss.startup_id
                  AND methodology IS NOT NULL
                  AND methodology->'analysis_context'->>'methodology_version' = :methodology_version
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            ) latest ON true
            WHERE ss.user_id = :user_id
            ORDER BY ss.created_at DESC
        """), {
            "user_id": user_id,
            "methodology_version": METHODOLOGY_VERSION,
        })

        rows = result.mappings().all()

    return [dict(row) for row in rows]


def backfill_startup_ids():
    """
    One-time (but safely re-runnable) data migration: creates exactly one
    startups row per LOWER(TRIM(company_name)) identity already implicitly
    used as "startup identity" by every canonical read query in this file
    -- the EXACT same normalization rule those queries already use, not a
    new or improved one, so this migration cannot silently redefine what
    "the same startup" means. Rows with no company_name (NULL, or blank
    after trim) are skipped entirely and get no startup_id, exactly as
    those same canonical queries already exclude them from grouping (see
    search_analyses()/get_rankings()'s own "company_name IS NOT NULL AND
    TRIM(company_name) <> ''" filters) -- they are never merged into one
    fake shared identity.

    canonical_name is taken from the most recent matching analysis
    (ORDER BY created_at DESC, id DESC), the same "latest wins" tie-break
    get_rankings()/get_startup_by_name() already use for "which row
    represents this startup right now".

    Idempotent: the UNIQUE constraint on startups.normalized_name makes
    the insert step a safe no-op for identities already present (ON
    CONFLICT DO NOTHING); the update step only ever touches
    analyses.startup_id IS NULL rows, so re-running this after some rows
    are already backfilled changes nothing further and is always safe to
    call at every startup alongside the other migrations.

    Creates ONLY startups rows and analyses.startup_id values -- never
    touches startup_memberships or saved_startups. Every startup created
    here is unowned by construction; no ownership is fabricated for
    historical analyses.
    """
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO startups (canonical_name, normalized_name)
            SELECT DISTINCT ON (LOWER(TRIM(company_name)))
                company_name,
                LOWER(TRIM(company_name))
            FROM analyses
            WHERE company_name IS NOT NULL
              AND TRIM(company_name) <> ''
            ORDER BY LOWER(TRIM(company_name)), created_at DESC, id DESC
            ON CONFLICT (normalized_name) DO NOTHING
        """))

        result = connection.execute(text("""
            UPDATE analyses
            SET startup_id = startups.id
            FROM startups
            WHERE analyses.startup_id IS NULL
              AND analyses.company_name IS NOT NULL
              AND TRIM(analyses.company_name) <> ''
              AND LOWER(TRIM(analyses.company_name)) = startups.normalized_name
        """))

    print(f"startup backfill complete: {result.rowcount} analyses linked to startups")


def save_score_history(
    analysis_id,
    company_name,
    industry,
    stage,
    business_model,
    market_score,
    team_score,
    product_score,
    competition_score,
    traction_score,
    financial_score,
    overall_score,
    readiness_score
):
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO score_history (
                analysis_id,
                company_name,
                industry,
                stage,
                business_model,
                market_score,
                team_score,
                product_score,
                competition_score,
                traction_score,
                financial_score,
                overall_score,
                readiness_score
            )
            VALUES (
                :analysis_id,
                :company_name,
                :industry,
                :stage,
                :business_model,
                :market_score,
                :team_score,
                :product_score,
                :competition_score,
                :traction_score,
                :financial_score,
                :overall_score,
                :readiness_score
            )
        """), {
            "analysis_id": analysis_id,
            "company_name": company_name,
            "industry": industry,
            "stage": stage,
            "business_model": business_model,
            "market_score": market_score,
            "team_score": team_score,
            "product_score": product_score,
            "competition_score": competition_score,
            "traction_score": traction_score,
            "financial_score": financial_score,
            "overall_score": overall_score,
            "readiness_score": readiness_score,
        })

    print("Score history saved successfully.")


def get_score_history(company_name: str):
    search_term = f"%{company_name}%"

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                id,
                analysis_id,
                company_name,
                industry,
                stage,
                business_model,
                market_score,
                team_score,
                product_score,
                competition_score,
                traction_score,
                financial_score,
                overall_score,
                readiness_score,
                created_at
            FROM score_history
            WHERE company_name ILIKE :search_term
            ORDER BY created_at ASC
        """), {
            "search_term": search_term
        })

        rows = result.mappings().all()

    return [dict(row) for row in rows]


def get_startup_trends(company_name: str):
    history = get_score_history(company_name)

    if len(history) == 0:
        return {
            "error": "No history found"
        }

    first = history[0]
    latest = history[-1]

    score_change = latest["overall_score"] - first["overall_score"]
    readiness_change = (
        latest["readiness_score"] -
        first["readiness_score"]
    )

    if score_change > 0:
        trend = "Improving"
    elif score_change < 0:
        trend = "Declining"
    else:
        trend = "Stable"

    return {
        "company_name": company_name,
        "first_score": first["overall_score"],
        "latest_score": latest["overall_score"],
        "score_change": score_change,
        "first_readiness": first["readiness_score"],
        "latest_readiness": latest["readiness_score"],
        "readiness_change": readiness_change,
        "trend": trend,
        "total_analyses": len(history)
    }


def get_or_create_startup(company_name, connection=None):
    """
    SIE Accounts & Ownership -- canonical Startup write path. Resolves
    company_name to its canonical startups.id, creating exactly one new
    startups row the first time this identity is ever seen.

    Uses the EXACT same normalization rule as backfill_startup_ids() and
    every canonical read query in this file (LOWER(TRIM(company_name)))
    -- not a new or improved one, so a new analysis can never resolve to
    a different notion of "the same startup" than the migration already
    established.

    Concurrency-safe: relies on the UNIQUE constraint on
    startups.normalized_name via INSERT ... ON CONFLICT DO NOTHING,
    followed by a SELECT for the (now certainly present) row's id. This
    is correct regardless of which of two concurrent callers' INSERT
    actually wins the race -- Postgres serializes concurrent inserts
    against the same unique key (the loser waits briefly rather than
    racing incorrectly), so by the time the SELECT below runs, the
    winning row is guaranteed visible in this transaction.

    Never modifies an existing startup's canonical_name: ON CONFLICT DO
    NOTHING never updates the existing row, so a later analysis that
    happens to use different casing/whitespace for an already-known
    company reuses the existing row exactly as first stored -- only the
    very first analysis for a given normalized identity sets
    canonical_name.

    Creates ONLY a startups row -- never touches startup_memberships or
    saved_startups, and never associates a user. Ownership is a
    completely separate concept from analysis (see the SIE Accounts &
    Ownership architecture design); this function's only job is identity
    resolution.

    Pass an existing SQLAlchemy Connection (already inside a transaction,
    e.g. save_analysis()'s own) via `connection` to keep Startup
    resolution and the Analysis insert atomic -- if that transaction
    later rolls back for any reason, a Startup created here rolls back
    with it, so a failed analysis write can never leave behind an orphan
    Startup. If no connection is passed, this opens and commits its own
    short transaction (useful for standalone/test callers).

    Returns None for a null/empty company_name -- exactly matching the
    existing exclusion already used everywhere else (search_analyses(),
    get_rankings(), backfill_startup_ids()) -- a nameless analysis is
    never merged into a fake shared identity, and gets no startup_id.
    """
    normalized_name = company_name.strip().lower() if company_name else ""

    if not normalized_name:
        return None

    def _resolve(conn):
        conn.execute(text("""
            INSERT INTO startups (canonical_name, normalized_name)
            VALUES (:canonical_name, :normalized_name)
            ON CONFLICT (normalized_name) DO NOTHING
        """), {
            "canonical_name": company_name.strip(),
            "normalized_name": normalized_name,
        })

        return conn.execute(text("""
            SELECT id FROM startups WHERE normalized_name = :normalized_name
        """), {"normalized_name": normalized_name}).scalar()

    if connection is not None:
        return _resolve(connection)

    with engine.begin() as new_connection:
        return _resolve(new_connection)


def save_analysis(
    company_text,
    summary,
    risk_analysis,
    competitor_analysis,
    memo,
    structured_analysis,
    investment_score,
    founder_analysis,
    market_analysis,
    sources,
    traction_analysis,
    market_score,
    team_score,
    product_score,
    competition_score,
    traction_score,
    financial_score,
    overall_score,
    recommendation,
    readiness_score,
    readiness_summary,
    methodology,
    startup_id=None,
):
    """
    Phase 7.2.1 -- Deterministic Founder Re-analysis: startup_id is an
    OPTIONAL authoritative override, meant only for a caller that has
    ALREADY verified the current user is a real member of that exact
    startup (POST /analyze's own use of require_startup_member() before
    ever calling this function) -- save_analysis() itself does not check
    authorization, matching this file's existing convention that DB
    functions implement queries/writes, not access control.

    When startup_id is None (every existing caller, and /analyze's own
    normal/public path): behavior is completely unchanged --
    get_or_create_startup() resolves identity from the extracted
    company_name exactly as before.

    When startup_id is supplied: get_or_create_startup() is never
    called, so this analysis can never spawn a second startups row no
    matter what company name this particular analysis happened to
    extract ("Linear" vs "Linear Inc." vs "Linear App" all resolve to the
    SAME startup_id here, deterministically, because none of them are
    ever consulted for identity). The given id is looked up (never
    blindly trusted) inside this same transaction; a nonexistent id
    raises ValueError and nothing is written -- same
    "raise ValueError for a startup_id that doesn't exist" contract
    save_startup_for_user() already uses, so callers already know this
    shape.

    Per the Phase 7.2.1 design decision on identity vs. display: the
    row's `company_name` column (the field other canonical read paths
    key off, e.g. search_analyses()'s DISTINCT ON) is set to the
    startup's EXISTING canonical_name, not whatever this analysis
    happened to extract -- this is what actually prevents identity
    drift. The LLM-extracted name is NOT discarded, though: it still
    lives in `methodology`/`structured_analysis` (the JSONB blobs) via
    the analysis_context/company_name this function already receives one
    layer up, in `structured_analysis` -- callers may still show it,
    it simply never overrides canonical_name here.
    """
    company_name = None
    industry = None
    stage = None
    business_model = None

    if isinstance(structured_analysis, dict):
        company_name = structured_analysis.get("company_name")
        industry = structured_analysis.get("industry")
        stage = structured_analysis.get("stage")
        business_model = structured_analysis.get("business_model")

    created_at = datetime.now().isoformat()

    with engine.begin() as connection:
        if startup_id is not None:
            # Authoritative path (Phase 7.2.1): identity is already
            # decided by the caller's verified startup_id -- resolve the
            # real row directly, never via get_or_create_startup()'s
            # name-matching. The FK constraint on analyses.startup_id
            # would itself reject a nonexistent id, but failing here with
            # a clean ValueError (inside this same transaction, before
            # any INSERT is attempted) is the same "clean application
            # error, never a raw IntegrityError" discipline
            # save_startup_for_user() already established.
            startup_row = connection.execute(text("""
                SELECT id, canonical_name FROM startups WHERE id = :startup_id
            """), {"startup_id": startup_id}).mappings().first()

            if startup_row is None:
                raise ValueError(f"Startup {startup_id} does not exist")

            resolved_startup_id = startup_row["id"]
            # Overrides the extracted company_name for the DB column
            # only -- see this function's own docstring for why this is
            # the one thing that actually needs to stay pinned to the
            # canonical identity, while methodology/structured_analysis
            # (untouched below) may still carry whatever this analysis
            # extracted.
            company_name = startup_row["canonical_name"]
        else:
            # SIE Accounts & Ownership -- canonical Startup write path,
            # centralized here so every existing and future
            # save_analysis() caller gets it automatically (no
            # per-endpoint duplication). Resolved inside this same
            # transaction/connection so Startup resolution and the
            # Analysis insert commit or roll back together -- a failed
            # Analysis insert can never leave behind an orphan Startup.
            # See get_or_create_startup()'s own docstring for the
            # normalization/concurrency/ownership guarantees.
            resolved_startup_id = get_or_create_startup(company_name, connection=connection)

        result = connection.execute(text("""
            INSERT INTO analyses (
                company_name,
                startup_id,
                company_text,
                summary,
                risk_analysis,
                competitor_analysis,
                memo,
                created_at,
                structured_analysis,
                investment_score,
                founder_analysis,
                market_analysis,
                sources,
                traction_analysis,
                methodology,
                market_score,
                team_score,
                product_score,
                competition_score,
                traction_score,
                financial_score,
                overall_score,
                recommendation,
                readiness_score,
                readiness_summary,
                industry,
                stage,
                business_model
            )
            VALUES (
                :company_name,
                :startup_id,
                :company_text,
                :summary,
                :risk_analysis,
                :competitor_analysis,
                :memo,
                :created_at,
                :structured_analysis,
                :investment_score,
                :founder_analysis,
                :market_analysis,
                :sources,
                :traction_analysis,
                CAST(:methodology AS JSONB),
                :market_score,
                :team_score,
                :product_score,
                :competition_score,
                :traction_score,
                :financial_score,
                :overall_score,
                :recommendation,
                :readiness_score,
                :readiness_summary,
                :industry,
                :stage,
                :business_model

            )
            RETURNING id
        """), {
            "company_name": company_name,
            "startup_id": resolved_startup_id,
            "company_text": company_text,
            "summary": summary,
            "risk_analysis": risk_analysis,
            "competitor_analysis": competitor_analysis,
            "memo": memo,
            "created_at": created_at,
            "structured_analysis": json.dumps(structured_analysis),
            "investment_score": json.dumps(investment_score),
            "founder_analysis": json.dumps(founder_analysis),
            "market_analysis": json.dumps(market_analysis),
            "sources": json.dumps(sources),
            "traction_analysis": json.dumps(traction_analysis),
            "methodology": json.dumps(methodology),
            "market_score": market_score,
            "team_score": team_score,
            "product_score": product_score,
            "competition_score": competition_score,
            "traction_score": traction_score,
            "financial_score": financial_score,
            "overall_score": overall_score,
            "recommendation": recommendation,
            "readiness_score": readiness_score,
            "readiness_summary": readiness_summary,
            "industry": industry,
            "stage": stage,
            "business_model": business_model
        })
        analysis_id = result.scalar()
    return analysis_id

        

def search_analyses(query: str):
    """
    P0 Product Trust Cleanup: search results must represent unique
    startups backed by their latest CANONICAL Methodology v2 analysis --
    the same "methodology IS NOT NULL and methodology_version matches the
    current constant" rule as get_rankings(), so a legacy (pre-v2 or
    methodology-null) analysis can never surface as a current canonical
    startup. Search still matches broadly across the same text columns as
    before (company_text, summary, risk_analysis, etc.) -- only the
    candidate pool (canonical rows only) and the returned score's source
    (methodology.startup_intelligence_score, not the legacy overall_score
    column) have changed; the match behavior and result shape the frontend
    consumes (company_name, summary, overall_score) are unchanged.
    """
    search_term = f"%{query}%"

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                company_name,
                summary,
                overall_score
            FROM (
                SELECT DISTINCT ON (LOWER(TRIM(company_name)))
                    company_name,
                    summary,
                    (methodology->>'startup_intelligence_score')::float AS overall_score,
                    created_at
                FROM analyses
                WHERE
                    methodology IS NOT NULL
                    AND methodology->'analysis_context'->>'methodology_version' = :methodology_version
                    AND company_name IS NOT NULL
                    AND TRIM(company_name) <> ''
                    AND (
                        company_text ILIKE :search_term
                        OR company_name ILIKE :search_term
                        OR summary ILIKE :search_term
                        OR risk_analysis ILIKE :search_term
                        OR competitor_analysis ILIKE :search_term
                        OR memo ILIKE :search_term
                        OR structured_analysis ILIKE :search_term
                        OR investment_score ILIKE :search_term
                        OR founder_analysis ILIKE :search_term
                        OR market_analysis ILIKE :search_term
                        OR sources ILIKE :search_term
                        OR traction_analysis ILIKE :search_term
                    )
                ORDER BY
                    LOWER(TRIM(company_name)),
                    created_at DESC,
                    id DESC
            ) latest_canonical_results
            ORDER BY created_at DESC
        """), {
            "search_term": search_term,
            "methodology_version": METHODOLOGY_VERSION,
        })

        rows = result.mappings().all()

    return [dict(row) for row in rows]

        
    
def parse_structured_analysis(row):
    analysis = dict(row)

    json_fields = [
        "structured_analysis",
        "investment_score",
        "founder_analysis",
        "market_analysis",
        "sources",
        "traction_analysis"
        "methodology",
    ]

    for field in json_fields:

        value = analysis.get(field)

    if isinstance(value, str):
        try:
            analysis[field] = json.loads(value)
        except json.JSONDecodeError:
            pass

    return analysis

def get_analyses():
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT * FROM analyses
            ORDER BY id DESC
        """))

        rows = result.mappings().all()

    return [parse_structured_analysis(row) for row in rows]

def get_analysis_by_id(analysis_id):
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT * FROM analyses
            WHERE id = :analysis_id
        """), {
            "analysis_id": analysis_id
        })

        row = result.mappings().first()

    if row is None:
        return None

    return parse_structured_analysis(row)


def get_startup_by_name(company_name: str):
    """
    Note: the `id` field returned here is analyses.id (the specific
    analysis row), not startups.id -- that naming predates the canonical
    Startup entity and is left alone since existing consumers
    (SPS History, etc.) already depend on it meaning "this analysis".

    Saved Startups (Watchlist Phase 1) added `startup_id` (analyses.
    startup_id, the canonical Startup FK -- see get_or_create_startup())
    alongside it, additively, so the frontend Save control has something
    stable to save without repurposing `id` or requiring a second request.
    A NULL startup_id here (only possible for pre-write-path historical
    rows that predate both the backfill and this column) means the
    frontend has nothing valid to save and hides the control rather than
    guessing.
    """
    normalized_company_name = company_name.strip()

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                id,
                startup_id,
                created_at,
                methodology
            FROM analyses
            WHERE LOWER(TRIM(company_name)) =
                  LOWER(TRIM(:company_name))
              AND methodology IS NOT NULL
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """), {
            "company_name": normalized_company_name
        })

        row = result.mappings().first()

    if row is None:
        return None

    startup = dict(row)

    if isinstance(startup["methodology"], str):
        startup["methodology"] = json.loads(
            startup["methodology"]
        )

    return startup


def get_sps_history(company_name: str):
    """
    Canonical SPS history for a company, sourced from the methodology
    JSONB rather than the legacy score_history table.

    score_history stores overall_score as INTEGER (lossy vs. the real
    float score) and, for every company analyzed before canonical
    methodology persistence existed, spans multiple incompatible
    revisions of the scoring algorithm. Filtering to
    methodology IS NOT NULL here naturally excludes all of that
    pre-canonical data, at the cost of most companies currently having
    zero or one point until more analyses are run under the current
    methodology.
    """
    normalized_company_name = company_name.strip()

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                id,
                created_at,
                methodology->>'startup_intelligence_score' AS sps
            FROM analyses
            WHERE LOWER(TRIM(company_name)) =
                  LOWER(TRIM(:company_name))
              AND methodology IS NOT NULL
            ORDER BY created_at ASC, id ASC
        """), {
            "company_name": normalized_company_name
        })

        rows = result.mappings().all()

    return [
        {
            "analysis_id": row["id"],
            "created_at": row["created_at"],
            "startup_intelligence_score": (
                float(row["sps"]) if row["sps"] is not None else None
            ),
        }
        for row in rows
    ]


def delete_analysis(analysis_id: int):
    with engine.begin() as connection:
        result = connection.execute(text("""
            DELETE FROM analyses
            WHERE id = :analysis_id
        """), {
            "analysis_id": analysis_id
        })

        deleted_count = result.rowcount

    return deleted_count



def update_analysis(
    analysis_id: int,
    company_text: str,
    summary: str,
    risk_analysis: str,
    competitor_analysis: str,
    memo: str,
    structured_analysis: dict,
    investment_score: str,
    founder_analysis: str,
    market_analysis: str,
    sources: str,
    traction_analysis: str
):
    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE analyses
            SET company_text = :company_text,
                summary = :summary,
                risk_analysis = :risk_analysis,
                competitor_analysis = :competitor_analysis,
                memo = :memo,
                structured_analysis = :structured_analysis,
                investment_score = :investment_score,
                founder_analysis = :founder_analysis,
                market_analysis = :market_analysis,
                sources = :sources,
                traction_analysis = :traction_analysis
            WHERE id = :analysis_id
        """), {
            "analysis_id": analysis_id,
            "company_text": company_text,
            "summary": summary,
            "risk_analysis": risk_analysis,
            "competitor_analysis": competitor_analysis,
            "memo": memo,
            "structured_analysis": json.dumps(structured_analysis),
            "investment_score": json.dumps(investment_score),
            "founder_analysis": json.dumps(founder_analysis),
            "market_analysis": json.dumps(market_analysis),
            "sources": json.dumps(sources),
            "traction_analysis": json.dumps(traction_analysis),
        })

        updated_count = result.rowcount

    return updated_count

def get_analytics():
    """
    Canonical Dashboard MVP: sourced from the exact same canonical
    population get_rankings() computes (latest Methodology v2 analysis per
    normalized startup) -- not COUNT(*)/AVG(...) over the full `analyses`
    table, which is still >90% legacy, pre-v2 rows. "Tracked startups" and
    "average score" now honestly mean "canonical startups" and "average
    canonical SPS."

    Per-pillar legacy averages (market/team/product/competition/traction/
    financial) and average_readiness_score are dropped entirely rather than
    carried forward unused: nothing in the frontend consumes them, they
    were sourced from the same legacy columns, and readiness_score
    specifically has no defined numeric scale at all (see the P0 Product
    Trust Cleanup report) -- inventing a "canonical" version of either
    would mean fabricating a metric, not just re-sourcing one. The
    redundant top_startups sub-list is dropped too: get_top_startups()
    already serves that, from the same canonical population, independently.
    """
    rankings = get_rankings()

    scores = [
        row["overall_score"]
        for row in rankings
        if row["overall_score"] is not None
    ]

    return {
        "total_startups": len(rankings),
        "average_overall_score": (
            round(sum(scores) / len(scores), 2) if scores else None
        ),
    }


def get_sps_v3_analytics():
    """
    Phase 10.9, Part 23. Deliberately separate from get_analytics() above
    rather than folded into it -- V3 is an additive, feature-flagged,
    parallel assessment (see app/ai/sps_v3_adapter.py), not a replacement
    for the canonical V2.1 population get_analytics() describes, so
    mixing the two into one response would misrepresent what's actually
    being counted.

    "Latest analysis per startup that HAS an sps_v3 at all" -- the same
    ROW_NUMBER()-per-startup shape get_rankings() uses, scoped to rows
    where methodology->'sps_v3' is present, so re-analyzing a startup
    under V3 doesn't double count its history. average_overall_score
    only ever averages SUFFICIENT rows' real numbers -- assessment_state
    'limited'/'insufficient' rows are counted in their own bucket, never
    contributing a null (or a fabricated 0) to that average (Phase 10.9
    Part 23's explicit "never treat null as zero").
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                methodology->'sps_v3'->>'assessment_state' AS assessment_state,
                (methodology->'sps_v3'->>'overall_score')::float AS overall_score
            FROM (
                SELECT
                    methodology,
                    ROW_NUMBER() OVER (
                        PARTITION BY startup_id
                        ORDER BY created_at DESC, id DESC
                    ) AS row_number
                FROM analyses
                WHERE methodology IS NOT NULL
                  AND methodology->'sps_v3' IS NOT NULL
                  AND startup_id IS NOT NULL
            ) ranked
            WHERE row_number = 1
        """))

        rows = result.mappings().all()

    counts = {"sufficient": 0, "limited": 0, "insufficient": 0}
    sufficient_scores = []

    for row in rows:
        state = row["assessment_state"]
        if state in counts:
            counts[state] += 1
        if state == "sufficient" and row["overall_score"] is not None:
            sufficient_scores.append(row["overall_score"])

    return {
        "total_v3_assessed": len(rows),
        "sufficient": counts["sufficient"],
        "limited": counts["limited"],
        "insufficient": counts["insufficient"],
        "average_sufficient_overall_score": (
            round(sum(sufficient_scores) / len(sufficient_scores), 2)
            if sufficient_scores else None
        ),
    }


def get_industry_analytics():
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                COALESCE(industry, 'Unknown') AS industry,
                COALESCE(stage, 'Unknown') AS stage,
                COALESCE(business_model, 'Unknown') AS business_model,
                COUNT(*) AS total_startups,
                ROUND(AVG(overall_score), 2) AS average_overall_score,
                ROUND(AVG(market_score), 2) AS average_market_score,
                ROUND(AVG(team_score), 2) AS average_team_score,
                ROUND(AVG(product_score), 2) AS average_product_score,
                ROUND(AVG(competition_score), 2) AS average_competition_score,
                ROUND(AVG(traction_score), 2) AS average_traction_score,
                ROUND(AVG(financial_score), 2) AS average_financial_score
            FROM analyses
            GROUP BY
                COALESCE(industry, 'Unknown'),
                COALESCE(stage, 'Unknown'),
                COALESCE(business_model, 'Unknown')
            ORDER BY total_startups DESC
        """))

        rows = result.mappings().all()

    return [dict(row) for row in rows]



def get_rankings():
    """
    P0 Product Trust Cleanup: rankings must reflect ONLY canonical
    Methodology v2 analyses -- never the legacy flattened score columns,
    and never an analysis whose methodology JSON predates the current v2
    dimension set (e.g. a stored blob stamped methodology_version "1.0",
    which `methodology IS NOT NULL` alone does not exclude).

    Every column below is read from the methodology JSONB, not the legacy
    analyses.overall_score/market_score/etc. columns -- those columns are
    left exactly as they were (still written at analysis time for
    historical/legacy consumers) but are no longer this query's source of
    truth. The response SHAPE is unchanged (same keys as before) so the
    frontend RankingsTable requires no changes.

    "One row per startup, latest canonical analysis" is still enforced via
    the same ROW_NUMBER()-over-normalized-company_name pattern as before,
    now scoped to canonical rows only.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                id,
                company_name,
                industry,
                stage,
                business_model,
                overall_score,
                market_score,
                team_score,
                product_score,
                competition_score,
                traction_score,
                financial_score,
                recommendation,
                created_at
            FROM (
                SELECT
                    id,
                    company_name,
                    industry,
                    stage,
                    business_model,
                    (methodology->>'startup_intelligence_score')::float AS overall_score,
                    (methodology->'market'->>'score')::float AS market_score,
                    (methodology->'team'->>'score')::float AS team_score,
                    (methodology->'product'->>'score')::float AS product_score,
                    (methodology->'execution'->>'score')::float AS competition_score,
                    (methodology->'traction'->>'score')::float AS traction_score,
                    (methodology->'financial_health'->>'score')::float AS financial_score,
                    methodology->'startup_scorecard'->>'recommendation' AS recommendation,
                    created_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY LOWER(TRIM(company_name))
                        ORDER BY created_at DESC, id DESC
                    ) AS row_number
                FROM analyses
                WHERE
                    methodology IS NOT NULL
                    AND methodology->'analysis_context'->>'methodology_version' = :methodology_version
                    AND methodology->>'startup_intelligence_score' IS NOT NULL
                    AND company_name IS NOT NULL
                    AND TRIM(company_name) <> ''
            ) ranked_analyses
            WHERE row_number = 1
            ORDER BY overall_score DESC NULLS LAST, company_name ASC
        """), {
            "methodology_version": METHODOLOGY_VERSION,
        })

        rows = result.mappings().all()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Startup Discovery V1. One centralized query, reused by both the count and
# the page of results, so "which startups match these filters" can never
# disagree between the two.
#
# Same canonical population as get_rankings() -- methodology IS NOT NULL,
# methodology_version == the current constant, startup_intelligence_score
# present, company_name present -- and the same "exactly one row per
# startup, latest analysis wins" rule. The one deliberate difference:
# get_rankings() still partitions by LOWER(TRIM(company_name)) (its own
# docstring explains why it hasn't been migrated off that); this partitions
# by analyses.startup_id, the real FK written by get_or_create_startup()/
# save_analysis() -- the same choice already made for
# get_saved_startups_for_user() in Saved Startups Phase 1, for the same
# reason (a real identity, not a re-derived string match). On the current
# canonical population these two grouping rules produce the identical
# result set (verified: both currently resolve to the same 6 startups) --
# this is a stricter implementation of the same semantics, not a new
# definition of "current startup."
#
# Every filter is optional and additive (AND'd together). A pillar-minimum
# filter (min_market, etc.) compares against a JSONB-derived score that is
# NULL for any startup whose pillar was Unavailable -- SQL's own NULL
# semantics (`NULL >= x` is never TRUE) mean an unavailable pillar can
# never satisfy a minimum, with no special-case code required. Nothing
# here invents or defaults a missing score.
# ---------------------------------------------------------------------------

DEFAULT_DISCOVERY_LIMIT = 24
MAX_DISCOVERY_LIMIT = 100

_DISCOVERY_SORT_COLUMNS = {
    "sps_desc": "overall_score DESC NULLS LAST, company_name ASC",
    "sps_asc": "overall_score ASC NULLS LAST, company_name ASC",
    "newest": "created_at DESC, company_name ASC",
    "name_asc": "company_name ASC",
}


def _build_discovery_filters(
    query: str | None,
    industry: str | None,
    stage: str | None,
    business_model: str | None,
    min_sps: float | None,
    max_sps: float | None,
    min_market: float | None,
    min_team: float | None,
    min_product: float | None,
    min_execution: float | None,
    min_traction: float | None,
    min_financial_health: float | None,
) -> tuple[str, dict]:
    """
    Shared by discover_startups() and count_discover_startups() below, so
    the count shown to a user and the rows they actually get always agree
    about which startups qualify. Every value is bound as a SQLAlchemy
    parameter (:name) -- no filter value is ever interpolated into the SQL
    string itself, including the free-text `query`.
    """
    clauses: list[str] = []
    params: dict = {}

    if query:
        clauses.append("company_name ILIKE :query")
        params["query"] = f"%{query}%"

    if industry:
        clauses.append("industry = :industry")
        params["industry"] = industry

    if stage:
        clauses.append("stage = :stage")
        params["stage"] = stage

    if business_model:
        clauses.append("business_model = :business_model")
        params["business_model"] = business_model

    if min_sps is not None:
        clauses.append("overall_score >= :min_sps")
        params["min_sps"] = min_sps

    if max_sps is not None:
        clauses.append("overall_score <= :max_sps")
        params["max_sps"] = max_sps

    if min_market is not None:
        clauses.append("market_score >= :min_market")
        params["min_market"] = min_market

    if min_team is not None:
        clauses.append("team_score >= :min_team")
        params["min_team"] = min_team

    if min_product is not None:
        clauses.append("product_score >= :min_product")
        params["min_product"] = min_product

    if min_execution is not None:
        clauses.append("execution_score >= :min_execution")
        params["min_execution"] = min_execution

    if min_traction is not None:
        clauses.append("traction_score >= :min_traction")
        params["min_traction"] = min_traction

    if min_financial_health is not None:
        clauses.append("financial_score >= :min_financial_health")
        params["min_financial_health"] = min_financial_health

    where_sql = ""
    if clauses:
        where_sql = " AND " + " AND ".join(clauses)

    return where_sql, params


_DISCOVERY_BASE_CTE = """
    WITH latest_per_startup AS (
        SELECT
            startup_id,
            company_name,
            industry,
            stage,
            business_model,
            overall_score,
            market_score,
            team_score,
            product_score,
            execution_score,
            traction_score,
            financial_score,
            created_at
        FROM (
            SELECT
                a.startup_id AS startup_id,
                a.company_name AS company_name,
                a.industry AS industry,
                a.stage AS stage,
                a.business_model AS business_model,
                (a.methodology->>'startup_intelligence_score')::float AS overall_score,
                (a.methodology->'market'->>'score')::float AS market_score,
                (a.methodology->'team'->>'score')::float AS team_score,
                (a.methodology->'product'->>'score')::float AS product_score,
                (a.methodology->'execution'->>'score')::float AS execution_score,
                (a.methodology->'traction'->>'score')::float AS traction_score,
                (a.methodology->'financial_health'->>'score')::float AS financial_score,
                a.created_at AS created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY a.startup_id
                    ORDER BY a.created_at DESC, a.id DESC
                ) AS row_number
            FROM analyses a
            WHERE
                a.startup_id IS NOT NULL
                AND a.methodology IS NOT NULL
                AND a.methodology->'analysis_context'->>'methodology_version' = :methodology_version
                AND a.methodology->>'startup_intelligence_score' IS NOT NULL
                AND a.company_name IS NOT NULL
                AND TRIM(a.company_name) <> ''
        ) ranked
        WHERE row_number = 1
    )
"""


def discover_startups(
    query: str | None = None,
    industry: str | None = None,
    stage: str | None = None,
    business_model: str | None = None,
    min_sps: float | None = None,
    max_sps: float | None = None,
    min_market: float | None = None,
    min_team: float | None = None,
    min_product: float | None = None,
    min_execution: float | None = None,
    min_traction: float | None = None,
    min_financial_health: float | None = None,
    sort: str = "sps_desc",
    limit: int = DEFAULT_DISCOVERY_LIMIT,
    offset: int = 0,
):
    where_sql, params = _build_discovery_filters(
        query, industry, stage, business_model,
        min_sps, max_sps,
        min_market, min_team, min_product, min_execution, min_traction, min_financial_health,
    )

    params["methodology_version"] = METHODOLOGY_VERSION
    # Defensive bounds even though app/api.py's Query(...) validation
    # already enforces these -- this function is also called directly by
    # tests and is safe to call with untrusted values on its own.
    params["limit"] = max(1, min(limit, MAX_DISCOVERY_LIMIT))
    params["offset"] = max(0, offset)

    order_sql = _DISCOVERY_SORT_COLUMNS.get(sort, _DISCOVERY_SORT_COLUMNS["sps_desc"])

    sql = _DISCOVERY_BASE_CTE + f"""
        SELECT * FROM latest_per_startup
        WHERE 1=1{where_sql}
        ORDER BY {order_sql}
        LIMIT :limit OFFSET :offset
    """

    with engine.begin() as connection:
        result = connection.execute(text(sql), params)
        rows = result.mappings().all()

    return [dict(row) for row in rows]


def count_discover_startups(
    query: str | None = None,
    industry: str | None = None,
    stage: str | None = None,
    business_model: str | None = None,
    min_sps: float | None = None,
    max_sps: float | None = None,
    min_market: float | None = None,
    min_team: float | None = None,
    min_product: float | None = None,
    min_execution: float | None = None,
    min_traction: float | None = None,
    min_financial_health: float | None = None,
) -> int:
    where_sql, params = _build_discovery_filters(
        query, industry, stage, business_model,
        min_sps, max_sps,
        min_market, min_team, min_product, min_execution, min_traction, min_financial_health,
    )

    params["methodology_version"] = METHODOLOGY_VERSION

    sql = _DISCOVERY_BASE_CTE + f"""
        SELECT COUNT(*) FROM latest_per_startup
        WHERE 1=1{where_sql}
    """

    with engine.begin() as connection:
        return connection.execute(text(sql), params).scalar()


def get_discovery_filter_options():
    """
    Startup Discovery V1, Part 4: filter option lists are derived from the
    REAL canonical population, never hardcoded -- so the UI can never offer
    an industry/stage/business model that currently returns zero results,
    and automatically grows as more canonical analyses are added. Sourced
    from the exact same canonical population discover_startups() itself
    queries (same methodology_version/startup_id gate), via the shared CTE.
    """
    sql = _DISCOVERY_BASE_CTE + """
        SELECT
            ARRAY_AGG(DISTINCT industry) FILTER (WHERE industry IS NOT NULL AND TRIM(industry) <> '') AS industries,
            ARRAY_AGG(DISTINCT stage) FILTER (WHERE stage IS NOT NULL AND TRIM(stage) <> '') AS stages,
            ARRAY_AGG(DISTINCT business_model) FILTER (WHERE business_model IS NOT NULL AND TRIM(business_model) <> '') AS business_models
        FROM latest_per_startup
    """

    with engine.begin() as connection:
        row = connection.execute(
            text(sql), {"methodology_version": METHODOLOGY_VERSION}
        ).mappings().first()

    return {
        "industries": sorted(row["industries"] or []),
        "stages": sorted(row["stages"] or []),
        "business_models": sorted(row["business_models"] or []),
    }


MIN_COMPARISON_STARTUPS = 2
MAX_COMPARISON_STARTUPS = 4


def get_startups_for_comparison(startup_ids: list[int]):
    """
    Compare Startups V1. Resolves each of the given canonical startups.id
    values to its own latest canonical (methodology_version-matching)
    analysis -- the same startup_id-keyed "latest per startup" semantics
    as discover_startups()/get_saved_startups_for_user(), not a new or
    competing definition of "current startup".

    Unlike discover_startups()'s flat DiscoveryResult shape, this returns
    the FULL methodology JSONB per startup -- Compare needs pillar
    strengths/weaknesses/subscores, which the flat Discovery shape never
    carried. app/api.py's /compare endpoint slims this down to the fields
    the frontend actually needs (see ComparisonStartup); this function's
    job is only canonical resolution.

    Deduplicates startup_ids (preserving first-occurrence order) and
    returns results in that SAME order -- callers that need to know which
    of their requested ids didn't resolve (invalid id, or a real startup
    with no canonical analysis yet) compare their own input against the
    returned rows' startup_ids; this function never raises for a
    partially-unresolvable list, since "some ids didn't resolve" is a
    normal, cleanly-representable outcome, not an error.
    """
    deduped_ids = list(dict.fromkeys(startup_ids))

    if not deduped_ids:
        return []

    with engine.begin() as connection:
        result = connection.execute(text("""
            WITH latest_per_startup AS (
                SELECT
                    a.startup_id AS startup_id,
                    a.id AS analysis_id,
                    a.company_name AS company_name,
                    a.created_at AS created_at,
                    a.methodology AS methodology,
                    ROW_NUMBER() OVER (
                        PARTITION BY a.startup_id
                        ORDER BY a.created_at DESC, a.id DESC
                    ) AS row_number
                FROM analyses a
                WHERE
                    a.startup_id = ANY(:startup_ids)
                    AND a.methodology IS NOT NULL
                    AND a.methodology->'analysis_context'->>'methodology_version' = :methodology_version
            )
            SELECT startup_id, analysis_id, company_name, created_at, methodology
            FROM latest_per_startup
            WHERE row_number = 1
        """), {
            "startup_ids": deduped_ids,
            "methodology_version": METHODOLOGY_VERSION,
        })

        rows = {row["startup_id"]: dict(row) for row in result.mappings().all()}

    ordered_results = []

    for startup_id in deduped_ids:
        row = rows.get(startup_id)

        if row is None:
            continue

        if isinstance(row["methodology"], str):
            row["methodology"] = json.loads(row["methodology"])

        ordered_results.append(row)

    return ordered_results


# ---------------------------------------------------------------------------
# Investor Workspace V1 (Phase 9). No new table: saved_startups remains the
# sole watchlist relationship (see save_startup_for_user()/
# get_saved_startups_for_user() above), and this function's only job is
# resolving each of a user's saved startups to its two most recent
# canonical (methodology_version-matching) analyses -- "latest" and
# "previous" -- so app/ai/investor_workspace.py can deterministically diff
# them. Same ROW_NUMBER()-per-startup_id pattern as
# get_startups_for_comparison() just above, generalized from "top 1" to
# "top 2" and batched across every saved startup_id in one query rather
# than one query per startup.
# ---------------------------------------------------------------------------

def get_watchlist_startups_for_user(user_id: str):
    """
    One entry per startup this user has saved (most-recently-saved first),
    each carrying its own `latest` and `previous` canonical analysis
    (id/created_at/methodology), independently resolved by startup_id --
    not by re-deriving identity from company_name the way get_rankings()
    still does. Either or both of `latest`/`previous` is None, never a
    fabricated stand-in:

    - `latest` is None when the startup has zero canonical analyses yet
      (e.g. only pre-Methodology-v2 history, or never analyzed at all).
      The startup still appears in the list -- a user's own saved list is
      never silently trimmed by the state of canonical intelligence.
    - `previous` is None when the startup has exactly one canonical
      analysis. This is the "no historical comparison yet" case Part 13.B
      calls out; callers must represent it as "unknown", never as a zero
      delta.

    Ownership is enforced entirely in SQL via `WHERE ss.user_id =
    :user_id` -- there is no path through this function for one user's
    watchlist to include another user's saved_startups row.
    """
    with engine.begin() as connection:
        saved_rows = connection.execute(text("""
            SELECT
                ss.startup_id AS startup_id,
                ss.created_at AS saved_at,
                startups.canonical_name AS company_name
            FROM saved_startups ss
            JOIN startups ON startups.id = ss.startup_id
            WHERE ss.user_id = :user_id
            ORDER BY ss.created_at DESC
        """), {"user_id": user_id}).mappings().all()

        startup_ids = [row["startup_id"] for row in saved_rows]

        history_by_startup: dict[int, list[dict]] = {}

        if startup_ids:
            history_rows = connection.execute(text("""
                SELECT startup_id, analysis_id, created_at, methodology, row_number
                FROM (
                    SELECT
                        a.startup_id AS startup_id,
                        a.id AS analysis_id,
                        a.created_at AS created_at,
                        a.methodology AS methodology,
                        ROW_NUMBER() OVER (
                            PARTITION BY a.startup_id
                            ORDER BY a.created_at DESC, a.id DESC
                        ) AS row_number
                    FROM analyses a
                    WHERE
                        a.startup_id = ANY(:startup_ids)
                        AND a.methodology IS NOT NULL
                        AND a.methodology->'analysis_context'->>'methodology_version' = :methodology_version
                ) ranked
                WHERE row_number <= 2
            """), {
                "startup_ids": startup_ids,
                "methodology_version": METHODOLOGY_VERSION,
            }).mappings().all()

            for row in history_rows:
                methodology = row["methodology"]
                if isinstance(methodology, str):
                    methodology = json.loads(methodology)

                entry = {
                    "analysis_id": row["analysis_id"],
                    "created_at": row["created_at"],
                    "methodology": methodology,
                }

                history_by_startup.setdefault(row["startup_id"], [None, None])
                history_by_startup[row["startup_id"]][row["row_number"] - 1] = entry

    results = []

    for row in saved_rows:
        latest, previous = history_by_startup.get(row["startup_id"], [None, None])
        results.append({
            "startup_id": row["startup_id"],
            "company_name": row["company_name"],
            "saved_at": row["saved_at"],
            "latest": latest,
            "previous": previous,
        })

    return results


# ---------------------------------------------------------------------------
# Idea Lab / Venture Simulator V1. modeled_ventures is a completely
# separate persistence concept from startups/analyses -- see the Phase 6
# design report for the full reasoning. Structurally:
#
# - No column here references startups or analyses. Creating, editing, or
#   deleting a modeled venture can never touch canonical intelligence,
#   because there is no foreign key path to it at all.
# - Every read/write function below takes user_id as a REQUIRED filter,
#   not an optional one -- the same "ownership scoped in the SQL itself,
#   not just checked in Python after the fact" discipline already used
#   for saved_startups (see save_startup_for_user()'s own docstring).
#   A mismatched owner gets a clean "not found" (None / 0 rows), never a
#   leaked row and never a different error shape that would let a caller
#   distinguish "doesn't exist" from "belongs to someone else".
# - model_result (the computed VPS) is stored as its own JSONB column,
#   entirely separate from analyses.methodology -- a modeled venture can
#   never be mistaken for a canonical analysis by any query that reads
#   analyses, because it was never inserted into analyses at all.
# ---------------------------------------------------------------------------

def create_modeled_ventures_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS modeled_ventures (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                industry TEXT,
                business_model TEXT,
                target_customer TEXT,
                stage TEXT,
                assumptions JSONB NOT NULL DEFAULT '{}'::jsonb,
                model_result JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("modeled_ventures table created successfully.")


def create_modeled_venture(
    user_id: str,
    name: str,
    description: str | None,
    industry: str | None,
    business_model: str | None,
    target_customer: str | None,
    stage: str | None,
    assumptions: dict,
    model_result: dict | None,
) -> int:
    with engine.begin() as connection:
        result = connection.execute(text("""
            INSERT INTO modeled_ventures (
                user_id, name, description, industry, business_model,
                target_customer, stage, assumptions, model_result
            )
            VALUES (
                :user_id, :name, :description, :industry, :business_model,
                :target_customer, :stage, :assumptions, :model_result
            )
            RETURNING id
        """), {
            "user_id": user_id,
            "name": name,
            "description": description,
            "industry": industry,
            "business_model": business_model,
            "target_customer": target_customer,
            "stage": stage,
            "assumptions": json.dumps(assumptions),
            "model_result": json.dumps(model_result) if model_result is not None else None,
        })

        return result.scalar()


def _parse_venture_row(row: dict) -> dict:
    venture = dict(row)

    if isinstance(venture.get("assumptions"), str):
        venture["assumptions"] = json.loads(venture["assumptions"])

    if isinstance(venture.get("model_result"), str):
        venture["model_result"] = json.loads(venture["model_result"])

    return venture


def list_modeled_ventures_for_user(user_id: str):
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT id, user_id, name, description, industry, business_model,
                   target_customer, stage, assumptions, model_result,
                   created_at, updated_at
            FROM modeled_ventures
            WHERE user_id = :user_id
            ORDER BY updated_at DESC
        """), {"user_id": user_id})

        rows = result.mappings().all()

    return [_parse_venture_row(dict(row)) for row in rows]


def get_modeled_venture_for_user(user_id: str, venture_id: int):
    """
    Returns None both when the venture doesn't exist AND when it belongs
    to a different user -- the caller (app/api.py) maps both to the same
    404, so a request can never distinguish "wrong id" from "someone
    else's venture" (the same non-leaking shape already used for Saved
    Startups' invalid-startup-id handling).
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT id, user_id, name, description, industry, business_model,
                   target_customer, stage, assumptions, model_result,
                   created_at, updated_at
            FROM modeled_ventures
            WHERE id = :venture_id AND user_id = :user_id
        """), {"venture_id": venture_id, "user_id": user_id})

        row = result.mappings().first()

    if row is None:
        return None

    return _parse_venture_row(dict(row))


def update_modeled_venture_for_user(
    user_id: str,
    venture_id: int,
    name: str,
    description: str | None,
    industry: str | None,
    business_model: str | None,
    target_customer: str | None,
    stage: str | None,
    assumptions: dict,
    model_result: dict | None,
) -> bool:
    """Returns True if a row was actually updated -- False means either the
    venture doesn't exist or belongs to a different user; the WHERE
    clause's user_id filter is what makes cross-user writes structurally
    impossible, not a Python-level check performed after the fact."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE modeled_ventures
            SET name = :name,
                description = :description,
                industry = :industry,
                business_model = :business_model,
                target_customer = :target_customer,
                stage = :stage,
                assumptions = :assumptions,
                model_result = :model_result,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :venture_id AND user_id = :user_id
        """), {
            "venture_id": venture_id,
            "user_id": user_id,
            "name": name,
            "description": description,
            "industry": industry,
            "business_model": business_model,
            "target_customer": target_customer,
            "stage": stage,
            "assumptions": json.dumps(assumptions),
            "model_result": json.dumps(model_result) if model_result is not None else None,
        })

        return result.rowcount > 0


def delete_modeled_venture_for_user(user_id: str, venture_id: int) -> bool:
    with engine.begin() as connection:
        result = connection.execute(text("""
            DELETE FROM modeled_ventures
            WHERE id = :venture_id AND user_id = :user_id
        """), {"venture_id": venture_id, "user_id": user_id})

        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Phase 10.7 -- Founder Missions V1. venture_missions belongs to
# modeled_ventures, structurally as separate from founder_actions/
# startups/analyses as modeled_ventures itself already is from those same
# tables (see create_modeled_ventures_table()'s own docstring -- the same
# reasoning applies here one level down). The FK is to modeled_ventures(id)
# ONLY; there is no column here, and no query anywhere in this module,
# that could resolve a mission to a startup_id, analysis_id, or
# founder_action.
#
# Deliberately modeled on founder_actions' own table/function shape
# (title, description, a related-category label, status, source +
# source_ref for the exact same "Add to Plan is idempotent" dedup
# discipline -- see create_founder_action()'s own docstring, reused here
# verbatim in create_venture_mission()) rather than a new pattern --
# Part 1's own instruction to inspect founder_actions "only as a
# reference," not to reuse it directly (no shared table, no shared FK, no
# shared endpoint).
#
# THE VPS FIREWALL (Part 9) is structural, not a convention someone has to
# remember: no function in this section ever touches modeled_ventures.
# assumptions or modeled_ventures.model_result, and no function in
# app/api.py's mission endpoints ever calls compute_vps()/
# update_modeled_venture_for_user(). A mission's status has no code path
# to a score.
#
# learning_summary/learning_recorded_at live directly on this table
# (Part 11's Option A) -- a mission has at most one current reflection in
# V1, so a second table would be unused complexity today. resource_ref is
# a nullable, unused-in-V1 column (Part 18): a future Founder Playbook
# feature can populate it without a schema change, but nothing reads or
# writes it in this phase.
def create_venture_missions_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS venture_missions (
                id SERIAL PRIMARY KEY,
                venture_id INTEGER NOT NULL REFERENCES modeled_ventures(id) ON DELETE CASCADE,
                created_by_user_id TEXT NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                description TEXT,
                mission_type TEXT NOT NULL DEFAULT 'other'
                    CHECK (mission_type IN (
                        'customer_discovery', 'validation', 'pricing', 'gtm',
                        'product', 'founder', 'economics', 'other'
                    )),
                related_category TEXT,
                source TEXT NOT NULL
                    CHECK (source IN ('vps_guidance', 'founder_created')),
                -- Dedup key for vps_guidance-sourced missions only -- see
                -- create_venture_mission()'s own docstring. Always NULL
                -- for founder_created, so the partial unique index below
                -- never constrains founder-authored missions.
                source_ref TEXT,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'completed', 'dismissed')),
                learning_summary TEXT,
                learning_recorded_at TIMESTAMP,
                -- Part 18: nullable, future Founder Playbook hook. Unused
                -- (never read, never written) in this phase.
                resource_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """))

        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS venture_missions_dedup_vps_guidance
            ON venture_missions (venture_id, source_ref)
            WHERE source <> 'founder_created'
        """))

    print("venture_missions table created successfully.")


def add_pitch_deck_coach_mission_source():
    """
    Phase 11 -- Pitch Deck Coach V2, Part 13. Same migration shape as
    add_fundraising_gap_source_to_founder_actions() (Phase 8): widens the
    CHECK constraint to allow a third source value, 'pitch_deck_coach',
    for a mission a founder explicitly created from a deck review's
    top_fixes card ("Make this a mission"). Deliberately its own source
    value, not reused 'vps_guidance' or 'founder_created': provenance
    should say where a mission actually came from, and this codebase's
    own established pattern (founder_actions' 'sie_recommendation' /
    'founder_created' / 'fundraising_gap' trio) is exactly this --
    distinct source per real origin. Dedup behavior is intentionally the
    SAME as vps_guidance (source <> 'founder_created' already covers any
    non-founder_created value, this one included) -- clicking "Make this
    a mission" twice for the identical fix title on the same venture
    must not create two rows. Never touches existing rows.
    """
    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE venture_missions DROP CONSTRAINT IF EXISTS venture_missions_source_check
        """))
        connection.execute(text("""
            ALTER TABLE venture_missions ADD CONSTRAINT venture_missions_source_check
            CHECK (source IN ('vps_guidance', 'founder_created', 'pitch_deck_coach'))
        """))

    print("venture_missions.source migrated to include pitch_deck_coach.")


def _mission_ownership_join_clause() -> str:
    # Ownership is enforced by this JOIN's predicate, not by a Python
    # check performed after a row is fetched -- the same discipline
    # get_modeled_venture_for_user() already uses one table up. A mission
    # belonging to a venture some OTHER user owns can never be selected,
    # updated, or returned by any function below; there is no code path
    # where the WHERE clause is satisfied but the row belongs to the
    # wrong user.
    return "JOIN modeled_ventures v ON v.id = vm.venture_id"


def list_venture_missions_for_owner(user_id: str, venture_id: int):
    with engine.begin() as connection:
        result = connection.execute(text(f"""
            SELECT vm.id, vm.venture_id, vm.created_by_user_id, vm.title,
                   vm.description, vm.mission_type, vm.related_category,
                   vm.source, vm.source_ref, vm.status, vm.learning_summary,
                   vm.learning_recorded_at, vm.resource_ref, vm.created_at,
                   vm.updated_at, vm.completed_at
            FROM venture_missions vm
            {_mission_ownership_join_clause()}
            WHERE vm.venture_id = :venture_id AND v.user_id = :user_id
            ORDER BY vm.created_at ASC
        """), {"venture_id": venture_id, "user_id": user_id})

        return [dict(row) for row in result.mappings().all()]


def create_venture_mission(
    venture_id: int,
    user_id: str,
    title: str,
    description: str | None,
    mission_type: str,
    related_category: str | None,
    source: str,
    resource_ref: str | None = None,
):
    """
    Creates one venture_missions row, OR -- for a vps_guidance/
    pitch_deck_coach-sourced mission whose exact title already exists for
    this venture -- returns the existing row untouched. Verbatim the same
    idempotency contract as create_founder_action() (see that function's
    own docstring for the full reasoning); source_ref is derived HERE
    from title, never accepted from the caller, and founder_created
    missions are never deduplicated.

    resource_ref (Phase 11, Part 14): the first real use of the column
    Phase 10.7 reserved as "future Founder Playbook hook" -- a playbook
    slug (e.g. "go-to-market") the caller resolved BEFORE calling this
    (via lib/playbooks/resourceMap.ts on the frontend), never computed
    here. None for every existing caller (vps_guidance suggestions,
    founder-authored missions) -- this function's signature default
    keeps their behavior byte-identical.

    Ownership is enforced by the caller (app/api.py) verifying
    get_modeled_venture_for_user(user_id, venture_id) is not None BEFORE
    this runs -- this function itself does not re-check ownership because
    venture_id here is only ever a value the caller already confirmed
    belongs to user_id, same as create_founder_action() trusts an
    already-verified startup_id.
    """
    source_ref = title.strip() if source != "founder_created" else None

    with engine.begin() as connection:
        result = connection.execute(text("""
            INSERT INTO venture_missions (
                venture_id, created_by_user_id, title, description,
                mission_type, related_category, source, source_ref,
                resource_ref, status
            )
            VALUES (
                :venture_id, :created_by_user_id, :title, :description,
                :mission_type, :related_category, :source, :source_ref,
                :resource_ref, 'active'
            )
            ON CONFLICT (venture_id, source_ref)
                WHERE source <> 'founder_created'
                DO NOTHING
            RETURNING
                id, venture_id, created_by_user_id, title, description,
                mission_type, related_category, source, source_ref, status,
                learning_summary, learning_recorded_at, resource_ref,
                created_at, updated_at, completed_at
        """), {
            "venture_id": venture_id,
            "created_by_user_id": user_id,
            "title": title,
            "description": description,
            "mission_type": mission_type,
            "related_category": related_category,
            "source": source,
            "source_ref": source_ref,
            "resource_ref": resource_ref,
        })

        row = result.mappings().first()

        if row is not None:
            return dict(row)

        existing = connection.execute(text("""
            SELECT id, venture_id, created_by_user_id, title, description,
                   mission_type, related_category, source, source_ref, status,
                   learning_summary, learning_recorded_at, resource_ref,
                   created_at, updated_at, completed_at
            FROM venture_missions
            WHERE venture_id = :venture_id AND source_ref = :source_ref
        """), {"venture_id": venture_id, "source_ref": source_ref}).mappings().first()

        return dict(existing)


def update_venture_mission_status_for_owner(
    user_id: str, venture_id: int, mission_id: int, new_status: str
):
    """
    Returns the updated row, or None if this mission_id doesn't exist for
    this venture_id/user_id combination -- never revealing whether the
    mission exists for a different user's venture (the JOIN's WHERE
    clause is what makes that structurally impossible, not a Python check
    after the fact).

    completed_at is set the first time status becomes 'completed' and is
    NEVER cleared afterward (dismissing a previously-completed mission,
    while unusual, doesn't erase the historical fact that it was once
    completed) -- CASE WHEN only sets it forward, never back to NULL.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE venture_missions vm
            SET status = :new_status,
                updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE
                    WHEN :new_status = 'completed' THEN CURRENT_TIMESTAMP
                    ELSE vm.completed_at
                END
            FROM modeled_ventures v
            WHERE vm.venture_id = v.id
              AND vm.id = :mission_id
              AND vm.venture_id = :venture_id
              AND v.user_id = :user_id
            RETURNING vm.id, vm.venture_id, vm.created_by_user_id, vm.title,
                      vm.description, vm.mission_type, vm.related_category,
                      vm.source, vm.source_ref, vm.status, vm.learning_summary,
                      vm.learning_recorded_at, vm.resource_ref, vm.created_at,
                      vm.updated_at, vm.completed_at
        """), {
            "mission_id": mission_id,
            "venture_id": venture_id,
            "user_id": user_id,
            "new_status": new_status,
        })

        row = result.mappings().first()
        return dict(row) if row is not None else None


def record_venture_mission_learning_for_owner(
    user_id: str, venture_id: int, mission_id: int, learning_summary: str
):
    """Same ownership-scoped UPDATE...FROM...WHERE shape as
    update_venture_mission_status_for_owner() -- see that function's own
    docstring. Recording a reflection never touches `status`; a founder
    can reflect without completing, or complete without reflecting."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            UPDATE venture_missions vm
            SET learning_summary = :learning_summary,
                learning_recorded_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            FROM modeled_ventures v
            WHERE vm.venture_id = v.id
              AND vm.id = :mission_id
              AND vm.venture_id = :venture_id
              AND v.user_id = :user_id
            RETURNING vm.id, vm.venture_id, vm.created_by_user_id, vm.title,
                      vm.description, vm.mission_type, vm.related_category,
                      vm.source, vm.source_ref, vm.status, vm.learning_summary,
                      vm.learning_recorded_at, vm.resource_ref, vm.created_at,
                      vm.updated_at, vm.completed_at
        """), {
            "mission_id": mission_id,
            "venture_id": venture_id,
            "user_id": user_id,
            "learning_summary": learning_summary,
        })

        row = result.mappings().first()
        return dict(row) if row is not None else None


# ---------------------------------------------------------------------------
# Phase 10.8 -- Pitch Deck Coach V1. pitch_deck_reviews has no FK to
# startups/analyses/modeled_ventures -- only to users(id), the same "clean
# private entity" shape modeled_ventures and venture_missions already
# established (see create_modeled_ventures_table()'s and
# create_venture_missions_table()'s own docstrings). A pitch deck review
# is a coaching artifact, never a Startup/Analysis: nothing in this
# section, or anywhere that reads from this table, has a path into
# Rankings, Discovery, Compare, or SPS History.
#
# `review` is one JSONB blob holding the full sanitized coaching payload
# app/ai/pitch_deck_coaching.py::generate_pitch_deck_review() returns
# (story/sections/top_fixes/strengths/open_questions/prep_questions) --
# deliberately not split across columns, the same reasoning
# modeled_ventures.model_result already uses for VPSResult: this is a
# single cohesive artifact always read and written as a whole, never
# queried by its internal fields.
#
# Deck text is intentionally NOT persisted here -- only readiness_label,
# deck_filename, page_count, and the review JSONB. The founder's raw deck
# content only ever needs to exist in memory for the one request that
# reviews it; storing it again would be a second copy of potentially
# sensitive material with no product use for this phase.
# ---------------------------------------------------------------------------

def create_pitch_deck_reviews_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS pitch_deck_reviews (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                deck_filename TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                readiness_label TEXT NOT NULL,
                review JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

    print("pitch_deck_reviews table created successfully.")


def create_pitch_deck_review(
    user_id: str,
    deck_filename: str,
    page_count: int,
    readiness_label: str,
    review: dict,
) -> int:
    with engine.begin() as connection:
        result = connection.execute(text("""
            INSERT INTO pitch_deck_reviews (
                user_id, deck_filename, page_count, readiness_label, review
            )
            VALUES (
                :user_id, :deck_filename, :page_count, :readiness_label, :review
            )
            RETURNING id
        """), {
            "user_id": user_id,
            "deck_filename": deck_filename,
            "page_count": page_count,
            "readiness_label": readiness_label,
            "review": json.dumps(review),
        })

        return result.scalar()


def _parse_pitch_deck_review_row(row: dict) -> dict:
    parsed = dict(row)

    if isinstance(parsed.get("review"), str):
        parsed["review"] = json.loads(parsed["review"])

    return parsed


def list_pitch_deck_reviews_for_user(user_id: str):
    """Part 17: reviews naturally coexist -- every POST creates a new row,
    nothing here overwrites a prior review. Summary shape only (no
    `review` JSONB) -- matches list_modeled_ventures_for_user()'s own
    light-list convention; app/api.py projects this into
    PitchDeckReviewSummary."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT id, user_id, deck_filename, page_count, readiness_label, created_at
            FROM pitch_deck_reviews
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """), {"user_id": user_id})

        return [dict(row) for row in result.mappings().all()]


def count_recent_pitch_deck_reviews(user_id: str, window_hours: int) -> int:
    """Minimal cost-control check (Part 24's own "preserve Phase 10.1
    hardening" posture, scoped down for this phase): counts every review
    row created in the rolling window, regardless of outcome. Pitch Deck
    Coach makes exactly one LLM call per review (see
    generate_pitch_deck_review()), a materially smaller cost surface than
    the six-pillar canonical pipeline analysis_runs guards -- so this
    reuses that module's proportionate, count-based approach rather than
    its full concurrency-lock/fingerprint/dedup machinery, which this
    phase's own test list (Part 25) does not call for."""
    with engine.begin() as connection:
        return connection.execute(text("""
            SELECT count(*) FROM pitch_deck_reviews
            WHERE user_id = :user_id
              AND created_at > CURRENT_TIMESTAMP - make_interval(hours => :window_hours)
        """), {"user_id": user_id, "window_hours": window_hours}).scalar()


def get_pitch_deck_review_for_user(user_id: str, review_id: int):
    """Returns None both when the review doesn't exist AND when it
    belongs to a different user -- same non-leaking 404 shape as
    get_modeled_venture_for_user()."""
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT id, user_id, deck_filename, page_count, readiness_label, review, created_at
            FROM pitch_deck_reviews
            WHERE id = :review_id AND user_id = :user_id
        """), {"review_id": review_id, "user_id": user_id})

        row = result.mappings().first()

    if row is None:
        return None

    return _parse_pitch_deck_review_row(dict(row))


def get_top_startups(limit: int = 10):
    """
    Canonical Dashboard MVP: Top Startups reuses get_rankings() directly --
    the exact same canonical population, "latest analysis per startup"
    logic, and SPS-descending order -- rather than a second, parallel
    query against the legacy score_history table. Top Startups and
    Rankings can now never disagree about which analyses are eligible or
    which one is "latest" for a given company, because they're the same
    query.
    """
    return get_rankings()[:limit]


def get_top_improving_startups(limit: int = 10):
    """
    Canonical Dashboard MVP: sourced ONLY from canonical Methodology v2
    analyses (methodology IS NOT NULL AND methodology_version matches the
    current constant) -- never the legacy score_history table, which mixes
    incompatible scoring eras and has no methodology-version concept at
    all. A startup needs at least 2 canonical analyses before an
    "improvement" can be honestly computed; a startup with only one
    canonical analysis is excluded, not compared against itself or against
    a legacy score. Returns [] -- not a partial/fake leaderboard -- if
    fewer than one startup currently qualifies; the frontend's existing
    empty state already renders that truthfully.

    Final MVP Stabilization: also requires score_change > 0. Without this,
    a company whose SPS actually declined between analyses could still
    surface here (as the least-bad entry) under the label "Fastest
    improving startups" -- a real, honest-labeling defect found during
    the Core MVP acceptance walkthrough, not a hypothetical: with only one
    repeat-analyzed company in the dataset and a negative score_change,
    that company was the sole (misleading) entry. A company that hasn't
    actually improved now falls out of this list entirely and the
    zero-results empty state (see above) takes over, rather than the list
    quietly including a decline.
    """
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                company_name,
                (methodology->>'startup_intelligence_score')::float AS sps,
                created_at
            FROM analyses
            WHERE
                methodology IS NOT NULL
                AND methodology->'analysis_context'->>'methodology_version' = :methodology_version
                AND methodology->>'startup_intelligence_score' IS NOT NULL
                AND company_name IS NOT NULL
                AND TRIM(company_name) <> ''
            ORDER BY LOWER(TRIM(company_name)), created_at ASC, id ASC
        """), {
            "methodology_version": METHODOLOGY_VERSION,
        })

        rows = result.mappings().all()

    companies = {}

    for row in rows:
        normalized_name = row["company_name"].lower().strip()

        if normalized_name not in companies:
            companies[normalized_name] = {
                "display_name": row["company_name"],
                "first_score": row["sps"],
                "latest_score": row["sps"],
                "canonical_analysis_count": 1,
            }
        else:
            companies[normalized_name]["latest_score"] = row["sps"]
            companies[normalized_name]["display_name"] = row["company_name"]
            companies[normalized_name]["canonical_analysis_count"] += 1

    improvements = [
        {
            "company_name": data["display_name"],
            "first_score": data["first_score"],
            "latest_score": data["latest_score"],
            "score_change": round(data["latest_score"] - data["first_score"], 2),
        }
        for data in companies.values()
        if data["canonical_analysis_count"] >= 2
        and data["latest_score"] > data["first_score"]
    ]

    improvements.sort(
        key=lambda x: x["score_change"],
        reverse=True
    )

    return improvements[:limit]

# ---------------------------------------------------------------------------
# Phase 10.1B -- AI Cost + Analysis Abuse Protection. analysis_runs is a
# new, additive, purely operational table: one row per REAL attempt to
# run the expensive pipeline (POST /analyze reaching the usage-protection
# gate), never a second scoring or intelligence concept. It has no FK
# from any canonical table and nothing here ever reads back into
# Methodology v2/SPS/VPS/Fundraising Readiness/Investor Workspace -- it
# exists purely to answer three operational questions: "does this user
# already have a run in flight," "how many attempts has this user made
# recently," and "did this user just submit the exact same thing."
#
# Durability requirement (Part 3): the concurrency lock below MUST survive
# multiple worker processes and process restarts, not just be correct
# within one Python process. It is enforced by
# analysis_runs_one_active_per_user, a PARTIAL UNIQUE INDEX on
# (user_id) WHERE status = 'running' -- the database itself guarantees at
# most one 'running' row per user_id can ever exist, regardless of how
# many processes/threads race to insert one. This is the same
# "correctness lives in a real constraint, not a check-then-act race" the
# codebase already established at create_startup_memberships_table()'s
# UNIQUE(user_id, startup_id) and approve_startup_claim()'s
# SELECT ... FOR UPDATE.
# ---------------------------------------------------------------------------

# Centralized, named policy constants (Part 4: "keep the policy
# centralized/configurable rather than scattering magic numbers") --
# every number a beta-usage decision depends on lives here, nowhere else.

# How many analysis attempts (any status -- 'running', 'completed', or
# 'failed' all count, matching Part 4.C's "completed/started analyses")
# a single user may make in the rolling window below. This is a small
# closed beta with a bounded, personally-invited user population (see the
# Phase 10.1 audit) -- 20/day is generous enough not to interfere with a
# real founder testing their own startup repeatedly or an investor
# exploring several companies in one sitting, while still bounding the
# realistic worst case (a careless script, a stuck retry loop, a shared
# account) to a small, predictable number of paid LLM/Tavily calls.
DAILY_ANALYSIS_CAP = 20
USAGE_WINDOW_HOURS = 24

# How long a 'running' row is trusted before it's treated as abandoned
# (Part 5: "stale running records caused by process termination"). Reuses
# the frontend's own existing ANALYZE_TIMEOUT_MS (10 minutes --
# dashboard/lib/api/analyze.ts) as the exact same "this should have
# finished by now" ceiling, rather than inventing a second number for the
# same real-world fact: a genuine analysis that hasn't finished in 10
# minutes is already considered hung/timed-out from the client's own
# point of view.
STALE_RUN_THRESHOLD_MINUTES = 10

# How long a SUCCESSFUL (status='completed') run's fingerprint blocks an
# identical resubmission from the same user (Part 4.B: "shortly after a
# successful submission"). Deliberately short -- long enough to catch an
# accidental double-click/duplicate-tab submission of the exact same
# input, short enough that a user who genuinely wants to re-run the same
# public company text again later is never meaningfully blocked. Never
# applied to a failed run (a user must always be able to immediately
# retry after a failure -- see AnalyzeStartupForm.tsx's own existing "Your
# input hasn't been lost -- you can try again" copy) and never applied to
# a founder-targeted re-analysis (startup_id is not None) -- Phase 7.2.1's
# whole point is that re-analyzing the SAME startup again soon after a
# previous run is a legitimate, expected workflow, not a duplicate.
DUPLICATE_COOLDOWN_MINUTES = 5


def create_analysis_runs_table():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                startup_id INTEGER REFERENCES startups(id),
                fingerprint TEXT,
                status TEXT NOT NULL DEFAULT 'running'
                    CHECK (status IN ('running', 'completed', 'failed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """))

        connection.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS analysis_runs_one_active_per_user
            ON analysis_runs (user_id)
            WHERE status = 'running'
        """))

    print("analysis_runs table created successfully.")


def compute_analysis_fingerprint(company_text: str | None, website_url: str | None, pdf_bytes: bytes | None) -> str:
    """
    A deterministic fingerprint of the RAW inputs a caller submitted --
    computed from what the client actually sent, before any extraction,
    so the duplicate-cooldown check (has_recent_duplicate_completed_run()
    below) can run before website fetch/PDF parsing, not after (Part 5).
    Plain sha256 over a delimited, order-fixed concatenation -- no
    external library, no secret, nothing sensitive derived from it that
    isn't already fully known to the caller who submitted it.
    """
    normalized_text = (company_text or "").strip()
    normalized_url = (website_url or "").strip().lower()
    pdf_digest = hashlib.sha256(pdf_bytes).hexdigest() if pdf_bytes else ""

    combined = f"{normalized_text}\x00{normalized_url}\x00{pdf_digest}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def count_recent_analysis_runs(user_id: str) -> int:
    """Part 4.C usage-cap check -- counts every attempt (any status) in
    the rolling USAGE_WINDOW_HOURS window, regardless of how it ended."""
    with engine.begin() as connection:
        return connection.execute(text("""
            SELECT count(*) FROM analysis_runs
            WHERE user_id = :user_id
              AND created_at > CURRENT_TIMESTAMP - make_interval(hours => :window_hours)
        """), {"user_id": user_id, "window_hours": USAGE_WINDOW_HOURS}).scalar()


def has_recent_duplicate_completed_run(user_id: str, fingerprint: str) -> bool:
    """
    Part 4.B rapid-accidental-duplicate check. Only ever called by the
    caller for a NON-founder-targeted request (startup_id is None) --
    see this module's own DUPLICATE_COOLDOWN_MINUTES docstring for why
    founder-targeted re-analysis and failed runs are both deliberately
    excluded from this check entirely (the exclusion is enforced by what
    the caller passes in / calls this at all, not by a parameter here).
    """
    with engine.begin() as connection:
        row = connection.execute(text("""
            SELECT 1 FROM analysis_runs
            WHERE user_id = :user_id
              AND fingerprint = :fingerprint
              AND status = 'completed'
              AND startup_id IS NULL
              AND created_at > CURRENT_TIMESTAMP - make_interval(mins => :cooldown_minutes)
            LIMIT 1
        """), {"user_id": user_id, "fingerprint": fingerprint, "cooldown_minutes": DUPLICATE_COOLDOWN_MINUTES}).first()
        return row is not None


def begin_analysis_run(user_id: str, startup_id: int | None, fingerprint: str) -> int | None:
    """
    Part 4.A concurrency lock. First expires any of THIS user's stale
    'running' rows (a crash/restart mid-pipeline is the only way one can
    outlive STALE_RUN_THRESHOLD_MINUTES, since a real run always
    transitions to 'completed'/'failed' via finish_analysis_run() in a
    try/finally -- see that function's own docstring), in its own
    transaction, then attempts the actual INSERT in a second, separate
    transaction so a unique-violation there cleanly aborts only that one
    statement.

    Returns the new row's id on success. Returns None if the user already
    has a genuinely active (non-stale) 'running' row -- the caller must
    treat None as "reject with 409," never retry-insert itself; the
    partial unique index (see create_analysis_runs_table()) is what
    actually guarantees correctness under real concurrent requests, this
    pre-expiry step is only what keeps a long-dead crash from permanently
    locking the user out.
    """
    with engine.begin() as connection:
        connection.execute(text("""
            UPDATE analysis_runs
            SET status = 'failed', completed_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
              AND status = 'running'
              AND created_at < CURRENT_TIMESTAMP - make_interval(mins => :threshold)
        """), {"user_id": user_id, "threshold": STALE_RUN_THRESHOLD_MINUTES})

    try:
        with engine.begin() as connection:
            result = connection.execute(text("""
                INSERT INTO analysis_runs (user_id, startup_id, fingerprint, status)
                VALUES (:user_id, :startup_id, :fingerprint, 'running')
                RETURNING id
            """), {"user_id": user_id, "startup_id": startup_id, "fingerprint": fingerprint})
            return result.scalar()
    except IntegrityError:
        return None


def finish_analysis_run(run_id: int, status: str) -> None:
    """
    Releases the concurrency lock (Part 5: "do not leave the user
    permanently locked because a previous request crashed") by
    transitioning a 'running' row to its real terminal status. Called
    from a `finally` block around the entire post-gate request body in
    POST /analyze, so this runs whether the request ultimately succeeded,
    failed validation, failed extraction, failed the pipeline, or failed
    to persist -- every one of those paths still frees the user to submit
    again immediately.
    """
    with engine.begin() as connection:
        connection.execute(text("""
            UPDATE analysis_runs
            SET status = :status, completed_at = CURRENT_TIMESTAMP
            WHERE id = :run_id
        """), {"run_id": run_id, "status": status})


def add_methodology_column():
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE analyses
                ADD COLUMN methodology JSONB
            """))

        print("methodology column added")

    except Exception as error:
        print("methodology migration skipped", error)