import sqlite3

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
            memo TEXT NOT NULL               
        )
    """)
    
    connection.commit()
    connection.close()

def save_analysis(
        company_text,
        summary,
        risk_analysis,
        memo
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO analyses (
            company_text,
            summary,
            risk_analysis,
            memo
         )
        VALUES (?, ?, ?, ?)
    """,(
        company_text,
        summary,
        risk_analysis,
        memo
    ))
    
    connection.commit()
    connection.close()