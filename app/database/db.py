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
            structured_analysis TEXT              
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
        structured_analysis 
):
    connection = get_connection()
    cursor = connection.cursor()

    created_at = datetime.now().isoformat()
    structured_analysis_json = json.dumps(structured_analysis)

    cursor.execute("""
        INSERT INTO analyses (
            company_text,
            summary,
            risk_analysis,
            competitor_analysis,
            memo,
            created_at,
            structured_analysis
         )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,(
        company_text,
        summary,
        risk_analysis,
        competitor_analysis,
        memo,
        created_at,
        structured_analysis_json
    ))
    
    connection.commit()
    connection.close()


def get_analyses():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM analyses
    """)

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]

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
    
    return dict(row)

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