# backend/policy_summary_engine.py

import sqlite3
import requests
from typing import Dict

from backend.database import DB_PATH

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


def get_latest_policy(company_name: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT pv.content
        FROM policy_versions pv
        JOIN companies c ON pv.company_id = c.id
        WHERE c.name = ?
        ORDER BY pv.timestamp DESC
        LIMIT 1
    """, (company_name,))

    row = c.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"No policy found for {company_name}")

    return row[0]


def call_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code != 200:
        raise RuntimeError("Ollama request failed")

    return response.json()["response"]


def summarize_current_policy(company_name: str) -> Dict:
    policy_text = get_latest_policy(company_name)

    prompt = f"""
You are a senior legal privacy policy analyst preparing a professional compliance report.

Analyze the following privacy policy deeply and produce a comprehensive structured summary.

Use EXACTLY these section headings:

DATA COLLECTION
DATA USAGE
DATA SHARING
DATA RETENTION
AI & PROFILING
AUTOMATED DECISIONS
USER RIGHTS
OVERALL SUMMARY

Under EACH heading:

- Write 8–12 detailed analytical bullet points
- Explain scope of data collected (types, categories, identifiers)
- Mention whether collection is automatic, manual, inferred, or third-party
- Describe purposes of processing
- Identify third-party sharing relationships
- Describe retention conditions and duration triggers
- Highlight legal basis if mentioned
- Explain potential implications or risks for users
- Be specific, not generic
- Avoid repeating the same sentence structure

Formatting Rules:
- DO NOT return JSON
- DO NOT use markdown code blocks
- Use clean readable text
- Each bullet must start with "- "
- Do not include commentary outside the structured summary

Privacy Policy Text:
\"\"\"
{policy_text[:25000]}
\"\"\"
"""

    summary_text = call_ollama(prompt)

    return {
        "formatted_summary": summary_text
    }