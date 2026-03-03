import requests
import trafilatura
import json
import hashlib
import sqlite3
from playwright.sync_api import sync_playwright
from backend.database import init_db, DB_PATH


# ==============================
# Utility
# ==============================

def generate_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ==============================
# Static Fetch (Improved Headers)
# ==============================

def fetch_static(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml"
        }

        response = requests.get(url, headers=headers, timeout=30)

        print("Static Status Code:", response.status_code)

        if response.status_code != 200:
            return None

        extracted = trafilatura.extract(response.text)
        return extracted

    except Exception as e:
        print("Static fetch error:", e)
        return None


# ==============================
# Dynamic Fetch (Stronger)
# ==============================

def fetch_dynamic(url):
    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False,
                slow_mo=100,
                args=["--disable-blink-features=AutomationControlled"]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True
            )

            page = context.new_page()

            print("Opening:", url)

            page.goto(url, timeout=90000, wait_until="domcontentloaded")

            # Small wait for content rendering
            page.wait_for_timeout(5000)

            html = page.content()

            browser.close()

        extracted = trafilatura.extract(html)
        return extracted

    except Exception as e:
        print("Dynamic fetch error:", e)
        return None

# ==============================
# Database Helpers
# ==============================

def get_company_id(conn, name, url):
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM companies WHERE name=?", (name,))
    result = cursor.fetchone()

    if result:
        return result[0]

    cursor.execute(
        "INSERT INTO companies (name, url) VALUES (?, ?)",
        (name, url)
    )
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

# ==============================
# Crawl Single Company
# ==============================

def crawl_company(company_name):
    init_db()

    with open("backend/registry.json") as f:
        registry = json.load(f)

    entry = next((e for e in registry if e["company"] == company_name), None)

    if not entry:
        return {"error": "Company not found in registry"}

    url = entry["url"]

    conn = sqlite3.connect(DB_PATH)

    print(f"\nFetching {company_name}...")

    text = fetch_static(url)

    if not text:
        print("Static failed. Trying dynamic...")
        text = fetch_dynamic(url)

    if not text:
        conn.close()
        return {
            "status": "failed",
            "message": "Unable to fetch policy"
        }

    company_id = get_company_id(conn, company_name, url)
    new_hash = generate_hash(text)
    old_hash = get_latest_hash(conn, company_id)

    if old_hash == new_hash:
        conn.close()
        return {
            "status": "no_change",
            "message": "No change detected"
        }

    save_new_version(conn, company_id, new_hash, text)
    conn.close()

    return {
        "status": "updated",
        "message": "New policy version stored"
    }


# ==============================
# Crawl All Companies
# ==============================

def crawl_all():
    init_db()

    with open("backend/registry.json") as f:
        registry = json.load(f)

    results = []

    conn = sqlite3.connect(DB_PATH)

    for entry in registry:
        company = entry["company"]
        url = entry["url"]

        print(f"\nFetching {company}...")

        text = fetch_static(url)

        if not text:
            print("Static failed. Trying dynamic...")
            text = fetch_dynamic(url)

        if not text:
            results.append({
                "company": company,
                "status": "failed"
            })
            continue

        company_id = get_company_id(conn, company, url)
        new_hash = generate_hash(text)
        old_hash = get_latest_hash(conn, company_id)

        if old_hash == new_hash:
            results.append({
                "company": company,
                "status": "no_change"
            })
        else:
            save_new_version(conn, company_id, new_hash, text)
            results.append({
                "company": company,
                "status": "updated"
            })

    conn.close()
    return results


# ==============================
# Script Mode (Keep Working)
# ==============================

if __name__ == "__main__":
    result = crawl_all()
    print("\nDone.")
    print(result)