import sqlite3
from datetime import datetime
import json

DATABASE_PATH = "app/database/due_diligence.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row 
    return connection 

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            risk_analysis TEXT NOT NULL,
            competitor_analysis TEXT,
            memo TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP ,
            structured_analysis TEXT,
            investment_score TEXT,
            founder_analysis TEXT          
        )
    """)

    try:
        cursor.execute(
            "ALTER TABLE analyses ADD COLUMN competitor_analysis TEXT"
        )
    except sqlite3.OperationalError as e:
        print("competitor_analysis migration:", e)

    try:
        cursor.execute(
            "ALTER TABLE analyses ADD COLUMN created_at TEXT"
        )
        print("created_at column added")
    except sqlite3.OperationalError as e:
        print("created_at migration:", e)

    try:
        cursor.execute(
            "ALTER TABLE analyses ADD COLUMN structured_analysis TEXT"
        )
        print("stuctured_analysis column added")

    except sqlite3.OperationalError as e:
        print("structured_analysis migration:", e)

    try:
        cursor.execute(
        "ALTER TABLE analyses ADD COLUMN investment_score TEXT"
    )
        print("investment_score column added")
    except sqlite3.OperationalError as e:
        print("investment_score migration:", e)

    try:
        cursor.execute(
            "ALTER TABLE analyses ADD COLUMN founder_analysis TEXT"
        )
    except sqlite3.OperationalError:
        pass

    cursor.execute("PRAGMA table_info(analyses)")
    columns = cursor.fetchall()
    
    for column in columns:
        print(column["name"])
    
    connection.commit()
    connection.close()

def save_analysis(
        company_text,
        summary,
        risk_analysis,
        competitor_analysis,
        memo,
        structured_analysis,
        investment_score,
        founder_analysis
):
    connection = get_connection()
    cursor = connection.cursor()

    created_at = datetime.now().isoformat()
    structured_analysis_json = json.dumps(structured_analysis)
    investment_score_json = json.dumps(investment_score)
    founder_analysis_json = json.dumps(founder_analysis)

    cursor.execute("""
        INSERT INTO analyses (
            company_text,
            summary,
            risk_analysis,
            competitor_analysis,
            memo,
            created_at,
            structured_analysis,
            investment_score,
            founder_analysis
         )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,(
        company_text,
        summary,
        risk_analysis,
        competitor_analysis,
        memo,
        created_at,
        structured_analysis_json,
        investment_score_json,
        founder_analysis_json
    ))
    
    connection.commit()
    connection.close()

def search_analyses(query: str):
    connection = get_connection()
    cursor = connection.cursor()

    search_term = f"%{query}%"

    cursor.execute(
        """
        SELECT * FROM analyses
        WHERE company_text LIKE ?
            OR summary LIKE ?
            OR risk_analysis LIKE ?
            OR competitor_analysis LIKE ?
            OR memo LIKE ?
            OR structured_analysis LIKE ?
            OR investment_score LIKE ?
            OR founder_analysis LIKE ?
        ORDER BY id DESC
""", 
(
    search_term,
    search_term,
    search_term,
    search_term,
    search_term,
    search_term
    
)
    )

    rows = cursor.fetchall()
    connection.close()

    return [parse_structured_analysis(row) for row in rows]

        
    

def parse_structured_analysis(row):
    analysis = dict(row)

    if analysis.get("structured_analysis"):
        try:
            analysis["structured_analysis"] = json.loads(
                analysis["structured_analysis"]
            )
        except json.JSONDecodeError:
            pass
        
        return analysis

def get_analyses():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM analyses
    """)

    rows = cursor.fetchall()

    connection.close()

    return [parse_structured_analysis(row) for row in rows]

def get_analysis_by_id(analysis_id):
    connection = get_connection()
    cursor = connection.cursor() 

    cursor.execute("""
        SELECT * FROM analyses
        WHERE id = ?
    """, (analysis_id,))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None
    
    return parse_structured_analysis(row)

def delete_analysis(analysis_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    connection.commit()

    deleted_count = cursor.rowcount
    connection.close()

    return deleted_count

def update_analysis(
    analysis_id: int,
    company_text: str,
    summary: str,
    risk_analysis: str,
    competitor_analysis: str,
    memo: str,
    structured_analysis: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE analyses
        SET company_text = ?,
            summary = ?,
            risk_analysis = ?,
            competitor_analysis = ?,
            memo = ?,
            structured_analysis = ?
        WHERE id = ?
        """,
        (
            company_text,
            summary,
            risk_analysis,
            competitor_analysis,
            memo,
            structured_analysis,
            analysis_id
        )
    )

    connection.commit()

    updated_count = cursor.rowcount

    connection.close()

    return updated_count