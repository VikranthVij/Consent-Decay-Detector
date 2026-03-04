import sqlite3
from datetime import datetime, timedelta

from backend.database import DB_PATH
from backend.crawler import crawl_all


def check_and_run_crawler():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT last_run FROM crawl_metadata WHERE id = 1")
    row = cursor.fetchone()

    now = datetime.utcnow()

    if row:
        last_run = datetime.fromisoformat(row[0])
        diff = now - last_run
    else:
        diff = timedelta(hours=999)

    if diff >= timedelta(hours=12):
        print("⏳ Last crawl >12h. Running crawler...")

        crawl_all()

        cursor.execute("""
        INSERT OR REPLACE INTO crawl_metadata (id, last_run)
        VALUES (1, ?)
        """, (now.isoformat(),))

        conn.commit()

    else:
        print("✅ Crawl recently executed. Skipping.")

    conn.close()