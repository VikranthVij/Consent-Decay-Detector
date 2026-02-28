import sqlite3
import sys
import json

from backend.database import DB_PATH
from backend.drift_engine import compute_structural_drift, aggregate_semantic_risk
from backend.text_processing import normalize_text
from backend.chunking import chunk_text
from backend.embedding_engine import embed_chunks, compute_similarity_matrix
from backend.llm_risk_engine import analyze_clause_with_llm


# ==========================================
# Compare Two Policy Versions
# ==========================================

def compare_versions(old_text, new_text):

    # Normalize
    old_clean = normalize_text(old_text)
    new_clean = normalize_text(new_text)

    # Chunk
    old_chunks = chunk_text(old_clean)
    new_chunks = chunk_text(new_clean)

    # Embeddings
    old_embeddings = embed_chunks(old_chunks)
    new_embeddings = embed_chunks(new_chunks)

    similarity_matrix = compute_similarity_matrix(old_embeddings, new_embeddings)

    unchanged = 0
    modified = 0
    removed = 0
    added = 0

    matched_new_indices = set()

    for i, row in enumerate(similarity_matrix):
        max_similarity = max(row)
        max_index = row.tolist().index(max_similarity)

        if max_similarity > 0.95:
            unchanged += 1
            matched_new_indices.add(max_index)
        elif max_similarity > 0.75:
            modified += 1
            matched_new_indices.add(max_index)
        else:
            removed += 1

    for j in range(len(new_chunks)):
        if j not in matched_new_indices:
            added += 1

    structural_drift = compute_structural_drift(
        modified, removed, added, len(old_chunks)
    )

    # Semantic Risk Analysis
    clause_results = []

    for j in range(len(new_chunks)):
        if j not in matched_new_indices:
            result = analyze_clause_with_llm(old_chunks, new_chunks[j])
            clause_results.append(result)

    semantic_score, semantic_level = aggregate_semantic_risk(
        clause_results,
        structural_drift
    )

    return {
        "structural_drift": structural_drift,
        "semantic_score": semantic_score,
        "risk_level": semantic_level,
        "total_new_clauses": len(clause_results)
    }


# ==========================================
# Timeline Drift Engine
# ==========================================

def compute_timeline_drift(company_name):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM companies WHERE name=?", (company_name,))
    company = cursor.fetchone()

    if not company:
        print("Company not found.")
        return

    company_id = company[0]

    cursor.execute("""
        SELECT content, timestamp
        FROM policy_versions
        WHERE company_id=?
        ORDER BY timestamp ASC
    """, (company_id,))

    versions = cursor.fetchall()
    conn.close()

    if len(versions) < 2:
        print("Not enough versions to compute timeline drift.")
        return

    print(f"\nTimeline Drift Analysis for {company_name}")
    print("=" * 60)

    timeline_results = []

    for i in range(1, len(versions)):

        old_text, old_time = versions[i - 1]
        new_text, new_time = versions[i]

        print(f"\nComparing:")
        print(f"{old_time}  →  {new_time}")

        result = compare_versions(old_text, new_text)

        print(f"Structural Drift: {result['structural_drift']}%")
        print(f"Semantic Risk: {result['semantic_score']}/10")
        print(f"Risk Level: {result['risk_level']}")
        print(f"New Clauses: {result['total_new_clauses']}")

        timeline_results.append({
            "from": old_time,
            "to": new_time,
            **result
        })

    print("\n" + "=" * 60)
    print("Timeline Summary (JSON)")
    print("=" * 60)
    print(json.dumps(timeline_results, indent=2))


# ==========================================
# CLI ENTRY POINT
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python -m backend.timeline_engine <CompanyName>")
        sys.exit(1)

    company_name = sys.argv[1]
    compute_timeline_drift(company_name)