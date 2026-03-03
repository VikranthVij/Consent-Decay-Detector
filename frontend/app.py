import sys
import os

# Add project root to Python path FIRST
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlite3
import json
from flask import Flask, render_template, jsonify, request

from backend.database import DB_PATH, init_db
from backend.policy_summary_engine import summarize_current_policy
from backend.text_processing import normalize_text
from backend.chunking import chunk_text
from backend.embedding_engine import embed_chunks, compute_similarity_matrix
from backend.drift_engine import compute_policy_drift
from backend.timeline_engine import compute_timeline_drift
from backend.expansion_signal_engine import extract_expansion_signals

app = Flask(__name__)


# ==========================================
# Pages
# ==========================================

@app.route("/")
def index():
    return render_template("index.html")


# ==========================================
# API Endpoints
# ==========================================

@app.route("/api/companies")
def api_companies():
    """List tracked companies (optionally filtered by user)."""
    user_id = request.args.get("user_id")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if user_id:
        cursor.execute("""
            SELECT c.id, c.name, c.url, COUNT(pv.id) as version_count,
                   MIN(pv.timestamp) as first_seen,
                   MAX(pv.timestamp) as last_seen
            FROM companies c
            JOIN user_companies uc ON c.id = uc.company_id
            LEFT JOIN policy_versions pv ON c.id = pv.company_id
            WHERE uc.user_id = ?
            GROUP BY c.id
            ORDER BY c.name
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT c.id, c.name, c.url, COUNT(pv.id) as version_count,
                   MIN(pv.timestamp) as first_seen,
                   MAX(pv.timestamp) as last_seen
            FROM companies c
            LEFT JOIN policy_versions pv ON c.id = pv.company_id
            GROUP BY c.id
            ORDER BY c.name
        """)

    companies = []
    for row in cursor.fetchall():
        companies.append({
            "id": row[0],
            "name": row[1],
            "url": row[2],
            "version_count": row[3],
            "first_seen": row[4],
            "last_seen": row[5],
        })

    conn.close()
    return jsonify(companies)


@app.route("/api/company/<name>/versions")
def api_versions(name):
    """Get all stored versions for a company."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM companies WHERE name=?", (name,))
    company = cursor.fetchone()
    if not company:
        conn.close()
        return jsonify({"error": "Company not found"}), 404

    cursor.execute("""
        SELECT id, timestamp, hash, LENGTH(content) as content_length
        FROM policy_versions
        WHERE company_id=?
        ORDER BY timestamp DESC
    """, (company[0],))

    versions = []
    for row in cursor.fetchall():
        versions.append({
            "id": row[0],
            "timestamp": row[1],
            "hash": row[2],
            "content_length": row[3],
        })

    conn.close()
    return jsonify(versions)


@app.route("/api/company/<name>/version/<int:version_id>")
def api_version_content(name, version_id):
    """Get content of a specific version."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pv.content, pv.timestamp, pv.hash
        FROM policy_versions pv
        JOIN companies c ON pv.company_id = c.id
        WHERE c.name=? AND pv.id=?
    """, (name, version_id))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({"error": "Version not found"}), 404

    content = result[0]
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")

    return jsonify({
        "content": content,
        "timestamp": result[1],
        "hash": result[2],
    })


@app.route("/api/company/<name>/drift")
def api_drift(name):
    """Run baseline and incremental drift analysis."""
    try:
        baseline = compute_policy_drift(name, mode="baseline", return_data=True)
        incremental = compute_policy_drift(name, mode="incremental", return_data=True)

        return jsonify({
            "baseline": baseline,
            "incremental": incremental,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/company/<name>/timeline")
def api_timeline(name):
    """Run timeline drift analysis."""
    try:
        timeline = compute_timeline_drift(name, return_data=True)
        return jsonify({"timeline": timeline})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/company/<name>/quick-stats")
def api_quick_stats(name):
    """Get quick structural stats without LLM (fast)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM companies WHERE name=?", (name,))
    company = cursor.fetchone()
    if not company:
        conn.close()
        return jsonify({"error": "Company not found"}), 404

    company_id = company[0]

    cursor.execute("""
        SELECT content, timestamp FROM policy_versions
        WHERE company_id=?
        ORDER BY timestamp ASC
    """, (company_id,))

    versions = cursor.fetchall()
    conn.close()

    if len(versions) < 2:
        return jsonify({"error": "Not enough versions for comparison"}), 400

    old_text, old_time = versions[0]
    new_text, new_time = versions[-1]

    old_clean = normalize_text(old_text)
    new_clean = normalize_text(new_text)

    old_chunks = chunk_text(old_clean)
    new_chunks = chunk_text(new_clean)

    old_embeddings = embed_chunks(old_chunks)
    new_embeddings = embed_chunks(new_chunks)

    sim_matrix = compute_similarity_matrix(old_embeddings, new_embeddings)

    unchanged = modified = removed = 0
    matched_new = set()

    for row in sim_matrix:
        max_sim = max(row)
        max_idx = row.tolist().index(max_sim)

        if max_sim > 0.95:
            unchanged += 1
            matched_new.add(max_idx)
        elif max_sim > 0.75:
            modified += 1
            matched_new.add(max_idx)
        else:
            removed += 1

    added = len(new_chunks) - len(matched_new)

    # Collect new clauses and their expansion signals
    new_clauses = []
    all_signals = {}
    for j in range(len(new_chunks)):
        if j not in matched_new:
            signals = extract_expansion_signals(new_chunks[j])
            new_clauses.append({
                "text": new_chunks[j],
                "expansion_signals": signals,
            })
            for s in signals:
                all_signals[s] = all_signals.get(s, 0) + 1

    total_old = len(old_chunks)
    structural_drift = 0.0
    if total_old > 0:
        structural_drift = round(
            ((modified * 0.4 + removed * 0.3 + added * 0.3) / total_old) * 100, 2
        )

    return jsonify({
        "company": name,
        "old_version_date": old_time,
        "new_version_date": new_time,
        "total_old_chunks": total_old,
        "total_new_chunks": len(new_chunks),
        "unchanged": unchanged,
        "modified": modified,
        "removed": removed,
        "added": added,
        "structural_drift": structural_drift,
        "new_clauses": new_clauses,
        "expansion_signals_summary": all_signals,
    })


@app.route("/api/analyze-text", methods=["POST"])
def api_analyze_text():
    """Analyze pasted policy text for expansion signals."""
    data = request.get_json()
    text = data.get("text", "")

    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    cleaned = normalize_text(text)
    chunks = chunk_text(cleaned)

    results = []
    signal_summary = {}

    for chunk in chunks:
        signals = extract_expansion_signals(chunk)
        if signals:
            results.append({
                "text": chunk,
                "expansion_signals": signals,
            })
            for s in signals:
                signal_summary[s] = signal_summary.get(s, 0) + 1

    return jsonify({
        "total_chunks": len(chunks),
        "flagged_chunks": len(results),
        "flagged_clauses": results,
        "signal_summary": signal_summary,
    })

@app.route("/api/company/<name>/summary")
def api_policy_summary(name):
    try:
        summary = summarize_current_policy(name)
        return jsonify({
            "company": name,
            "summary": summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/registry")
def api_registry():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM companies ORDER BY name")
    companies = [row[0] for row in cursor.fetchall()]

    conn.close()
    return jsonify({"companies": companies})

@app.route("/api/user/<user_id>/companies", methods=["POST"])

def api_set_user_companies(user_id):
    data = request.get_json()
    selected = data.get("companies", [])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure user exists
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))

    # Clear old selections
    cursor.execute("DELETE FROM user_companies WHERE user_id = ?", (user_id,))

    for company_name in selected:
        cursor.execute("SELECT id FROM companies WHERE name=?", (company_name,))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                INSERT INTO user_companies (user_id, company_id)
                VALUES (?, ?)
            """, (user_id, row[0]))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/api/user/<user_id>/companies", methods=["GET"])
def api_get_user_companies(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.name
        FROM companies c
        JOIN user_companies uc ON c.id = uc.company_id
        WHERE uc.user_id = ?
    """, (user_id,))

    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    return jsonify({"companies": companies})

@app.route("/api/company/<name>/crawl", methods=["POST"])
def api_manual_crawl(name):
    try:
        from backend.crawler import crawl_company
        result = crawl_company(name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# Run
# ==========================================

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001, threaded=True)
