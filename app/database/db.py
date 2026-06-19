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
    recommendation
):
    
    industry = None
    stage = None
    business_model = None

    if isinstance(structured_analysis, dict):
        industry = structured_analysis.get("industry")
        stage = structured_analysis.get("stage")
        business_model = structured_analysis.get("business_model")
    
    created_at = datetime.now().isoformat()

    with engine.begin() as connection:
        
        connection.execute(text("""
            INSERT INTO analyses (
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
                industry,
                stage,
                business_model
            )
            VALUES (
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
                :industry,
                :stage,
                :business_model
            )
        """), {
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
            "industry": industry,
            "stage": stage,
            "business_model": business_model
        })

def search_analyses(query: str):
    search_term = f"%{query}%"

    with engine.begin() as connection:
        result = connection.execute(text("""
            SELECT * FROM analyses
            WHERE company_text ILIKE :search_term
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
            ORDER BY id DESC
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