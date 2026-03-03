import sqlite3
from backend.database import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_companies (
    user_id TEXT,
    company_id INTEGER,
    PRIMARY KEY(user_id, company_id),
    FOREIGN KEY(company_id) REFERENCES companies(id)
)
""")

conn.commit()
conn.close()

print("User tables created successfully.")