import sqlite3
import json
from backend.database import DB_PATH
from backend.text_processing import normalize_text
from backend.chunking import chunk_text
from backend.embedding_engine import embed_chunks, compute_similarity_matrix
from backend.llm_risk_engine import analyze_clause_with_llm


# ==========================================
# Structural Drift
# ==========================================

def compute_structural_drift(modified, removed, added, total_old):
    if total_old == 0:
        return 0.0

    modified_ratio = modified / total_old
    removed_ratio = removed / total_old
    added_ratio = added / total_old

    score = (
        modified_ratio * 0.4 +
        removed_ratio * 0.3 +
        added_ratio * 0.3
    ) * 100

    return round(score, 2)


# ==========================================
# Semantic Risk Aggregation
# ==========================================

def aggregate_semantic_risk(clause_results, structural_drift):

    if not clause_results:
        return 0.0, "LOW"

    scores = [c["risk_score"] for c in clause_results]

    max_risk = max(scores)
    high_risk_count = len([s for s in scores if s >= 7])
    medium_risk_count = len([s for s in scores if 4 <= s < 7])

    base_score = (
        max_risk * 0.5 +
        high_risk_count * 0.7 +
        medium_risk_count * 0.3
    )

    structural_multiplier = 1 + (structural_drift / 200)

    final_score = base_score * structural_multiplier
    final_score = min(round(final_score, 2), 10)

    if final_score >= 7:
        level = "HIGH"
    elif final_score >= 4:
        level = "MEDIUM"
    else:
        level = "LOW"

    return final_score, level


# ==========================================
# Policy Drift Engine
# ==========================================

def compute_policy_drift(company_name, mode="baseline", return_data=False):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM companies WHERE name=?", (company_name,))
    company = cursor.fetchone()

    if not company:
        print("Company not found.")
        return

    company_id = company[0]

    cursor.execute("""
        SELECT content, timestamp FROM policy_versions
        WHERE company_id=?
        ORDER BY timestamp ASC
    """, (company_id,))

    versions = cursor.fetchall()
    conn.close()

    if len(versions) < 2:
        print("Not enough versions.")
        return

    if mode == "baseline":
        old_text, old_time = versions[0]
        new_text, new_time = versions[-1]
    else:  # incremental
        old_text, old_time = versions[-2]
        new_text, new_time = versions[-1]

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

    for row in similarity_matrix:
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

    for j in range(len(new_chunks)):
        if j not in matched_new_indices:

            result = analyze_clause_with_llm(
                old_chunks,
                new_chunks[j]
            )

            clause_results.append(result)

    semantic_score, semantic_level = aggregate_semantic_risk(
        clause_results,
        structural_drift
    )

    final_report = {
        "company": company_name,
        "mode": mode,
        "structural_drift": structural_drift,
        "semantic_score": semantic_score,
        "risk_level": semantic_level,
        "total_new_clauses": len(clause_results),
        "all_new_clauses": clause_results
    }

    if return_data:
        return final_report

    print(json.dumps(final_report, indent=2))