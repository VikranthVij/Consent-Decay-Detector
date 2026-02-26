import sqlite3
from backend.database import DB_PATH


def get_earliest_and_latest(company_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get company id
    cursor.execute("SELECT id FROM companies WHERE name=?", (company_name,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None, None

    company_id = result[0]

    # Earliest version
    cursor.execute("""
        SELECT content, timestamp
        FROM policy_versions
        WHERE company_id=?
        ORDER BY timestamp ASC
        LIMIT 1
    """, (company_id,))
    earliest = cursor.fetchone()

    # Latest version
    cursor.execute("""
        SELECT content, timestamp
        FROM policy_versions
        WHERE company_id=?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (company_id,))
    latest = cursor.fetchone()

    conn.close()

    return earliest[0], latest[0]