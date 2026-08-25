import os
import json
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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

engine = create_engine(DATABASE_URL)



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
):
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
        # SIE Accounts & Ownership -- canonical Startup write path,
        # centralized here so every existing and future save_analysis()
        # caller gets it automatically (no per-endpoint duplication).
        # Resolved inside this same transaction/connection so Startup
        # resolution and the Analysis insert commit or roll back
        # together -- a failed Analysis insert can never leave behind an
        # orphan Startup. See get_or_create_startup()'s own docstring for
        # the normalization/concurrency/ownership guarantees.
        startup_id = get_or_create_startup(company_name, connection=connection)

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
            "startup_id": startup_id,
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
    normalized_company_name = company_name.strip()

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                id,
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