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

    old_clean = normalize_text(old_text)
    new_clean = normalize_text(new_text)

    old_chunks = chunk_text(old_clean)
    new_chunks = chunk_text(new_clean)

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

    clause_results = []
    all_categories = set()

    for j in range(len(new_chunks)):
        if j not in matched_new_indices:
            result = analyze_clause_with_llm(old_chunks, new_chunks[j])
            clause_results.append(result)

            for cat in result.get("categories", []):
                all_categories.add(cat)

    semantic_score, semantic_level = aggregate_semantic_risk(
        clause_results,
        structural_drift
    )

    return {
        "structural_drift": structural_drift,
        "semantic_score": semantic_score,
        "risk_level": semantic_level,
        "categories": list(all_categories)
    }


# ==========================================
# Timeline Drift Engine with Category Tracking
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
    print("=" * 70)

    seen_categories = set()

    for i in range(1, len(versions)):

        old_text, old_time = versions[i - 1]
        new_text, new_time = versions[i]

        result = compare_versions(old_text, new_text)

        new_categories = set(result["categories"])
        first_introduced = new_categories - seen_categories

        seen_categories.update(new_categories)

        print(f"\n{old_time}  →  {new_time}")
        print(f"Structural Drift: {result['structural_drift']}%")
        print(f"Semantic Risk: {result['semantic_score']}/10")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Categories Detected: {result['categories']}")

        if first_introduced:
            print("⚠ First Introduction Detected:")
            for cat in first_introduced:
                print(f"   - {cat}")

    print("\n" + "=" * 70)
    print("End of Timeline Analysis")


# ==========================================
# CLI ENTRY
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python -m backend.timeline_engine <CompanyName>")
        sys.exit(1)

    compute_timeline_drift(sys.argv[1])