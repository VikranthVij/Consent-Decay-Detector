import requests
import trafilatura
import json
import hashlib
import time
import sqlite3
from playwright.sync_api import sync_playwright
from backend.database import init_db, DB_PATH


def generate_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def fetch_static(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        return trafilatura.extract(response.text)
    except:
        return None


def fetch_dynamic(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0")
            page = context.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(8000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            text = page.inner_text("body")
            browser.close()
        return text
    except:
        return None


def get_company_id(conn, name, url):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM companies WHERE name=?", (name,))
    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute("INSERT INTO companies (name, url) VALUES (?, ?)", (name, url))
    conn.commit()
    return cursor.lastrowid


def get_latest_hash(conn, company_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT hash FROM policy_versions
        WHERE company_id=?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (company_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def save_new_version(conn, company_id, hash_value, content):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO policy_versions (company_id, hash, content)
        VALUES (?, ?, ?)
    """, (company_id, hash_value, content))
    conn.commit()


if __name__ == "__main__":

    init_db()

    with open("backend/registry.json") as f:
        registry = json.load(f)

    conn = sqlite3.connect(DB_PATH)

    for entry in registry:
        company = entry["company"]
        url = entry["url"]

        print(f"\nFetching {company}...")

        text = fetch_static(url)
        if not text:
            text = fetch_dynamic(url)

        if not text:
            print(f"Failed to fetch {company}")
            continue

        company_id = get_company_id(conn, company, url)
        new_hash = generate_hash(text)
        old_hash = get_latest_hash(conn, company_id)

        if old_hash == new_hash:
            print(f"No change detected for {company}")
        else:
            save_new_version(conn, company_id, new_hash, text)
            print(f"New version stored for {company}")

    conn.close()
    print("\nDone.")