import sqlite3

DB_PATH = "backend/policies.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Companies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            url TEXT NOT NULL
        )
    """)

    # Policy versions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policy_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            hash TEXT,
            content TEXT,
            FOREIGN KEY(company_id) REFERENCES companies(id)
        )
    """)

    conn.commit()
    conn.close()