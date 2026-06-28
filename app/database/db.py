import os
import json
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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
    readiness_summary
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
        
        result = connection.execute(text("""
            INSERT INTO analyses (
                company_name,
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
    search_term = f"%{query}%"

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT *
            FROM (
                SELECT DISTINCT ON (LOWER(COALESCE(company_name, summary)))
                    *
                FROM analyses
                WHERE company_text ILIKE :search_term
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
                ORDER BY
                    LOWER(COALESCE(company_name, summary)),
                    created_at DESC,
                    id DESC
            ) latest_results
            ORDER BY created_at DESC
        """), {
            "search_term": search_term
        })

        rows = result.mappings().all()

    return [parse_structured_analysis(row) for row in rows]

        
    
def parse_structured_analysis(row):
    analysis = dict(row)

    json_fields = [
        "structured_analysis",
        "investment_score",
        "founder_analysis",
        "market_analysis",
        "sources",
        "traction_analysis"
    ]

    for field in json_fields:
        if analysis.get(field):
            try:
                analysis[field] = json.loads(analysis[field])
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
    search_term = f"%{company_name.strip()}%"

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT *
            FROM analyses
            WHERE company_name ILIKE :company_name
                OR structured_analysis ILIKE :company_name
                OR summary ILIKE :company_name
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        """), {
            "company_name": search_term
        })

        row = result.mappings().first()

    if row is None:
        return None

    return parse_structured_analysis(row)
        

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
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT
                COUNT(*) AS total_startups,
                ROUND(AVG(overall_score), 2) AS average_overall_score,
                ROUND(AVG(readiness_score), 2) AS average_readiness_score,
                ROUND(AVG(market_score), 2) AS average_market_score,
                ROUND(AVG(team_score), 2) AS average_team_score,
                ROUND(AVG(product_score), 2) AS average_product_score,
                ROUND(AVG(competition_score), 2) AS average_competition_score,
                ROUND(AVG(traction_score), 2) AS average_traction_score,
                ROUND(AVG(financial_score), 2) AS average_financial_score
            FROM analyses
        """))

        analytics = dict(result.mappings().first())

        top_result = connection.execute(text("""
            SELECT
                id,
                summary,
                overall_score,
                market_score,
                team_score,
                product_score,
                traction_score,
                financial_score,
                recommendation,
                created_at
            FROM analyses
            WHERE overall_score IS NOT NULL
            ORDER BY overall_score DESC
            LIMIT 5  
        """))

        top_startups = [dict(row) for row in top_result.mappings().all()]

    analytics["top_startups"] = top_startups

    return analytics

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
            FROM analyses
            WHERE overall_score IS NOT NULL
            ORDER BY overall_score DESC
        """))

        rows = result.mappings().all()

    return [dict(row) for row in rows]


def get_top_startups(limit: int = 10):
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT DISTINCT ON (company_name)
                company_name,
                industry,
                stage,
                business_model,
                overall_score,
                readiness_score,
                created_at
            FROM score_history
            WHERE overall_score IS NOT NULL
            ORDER BY company_name, created_at DESC
        """))

        latest_rows = result.mappings().all()

    sorted_rows = sorted(
        [dict(row) for row in latest_rows],
        key=lambda row: row["overall_score"],
        reverse=True
    )

    return sorted_rows[:limit]



def get_top_improving_startups(limit: int = 10):
    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT *
            FROM score_history
            ORDER BY company_name, created_at ASC
        """))

        rows = result.mappings().all()

    companies = {}

    for row in rows:
        normalized_name = row["company_name"].lower().strip()

        if normalized_name not in companies:
            companies[normalized_name] = {
                "display_name": row["company_name"],
                "first_score": row["overall_score"],
                "latest_score": row["overall_score"]
            }
        else:
            companies[normalized_name]["latest_score"] = row["overall_score"]

    improvements = []

    for company_name, scores in companies.items():
        score_change = (
            scores["latest_score"] -
            scores["first_score"]
        )

        improvements.append({
            "company_name": scores["display_name"],
            "first_score": scores["first_score"],
            "latest_score": scores["latest_score"],
            "score_change": score_change
        })

    improvements.sort(
        key=lambda x: x["score_change"],
        reverse=True
    )

    return improvements[:limit]