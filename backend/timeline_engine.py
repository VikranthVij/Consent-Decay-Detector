import sqlite3
import json
from collections import defaultdict
from backend.database import DB_PATH
from backend.text_processing import normalize_text
from backend.chunking import chunk_text
from backend.embedding_engine import embed_chunks, compute_similarity_matrix
from backend.llm_risk_engine import analyze_clause_with_llm
from backend.drift_engine import compute_structural_drift, aggregate_semantic_risk


CATEGORY_BASE_WEIGHTS = {
    "ai_training": 3,
    "profiling": 3,
    "cross_platform_sharing": 2,
    "data_aggregation": 2,
    "retention_expansion": 2,
    "third_party_sharing": 2,
    "automated_decision_making": 3,
    "historical_data_reclassification": 4,
}


def compute_category_severity(clause_results):

    category_counts = defaultdict(int)
    category_risk_sum = defaultdict(int)

    for result in clause_results:
        risk = result.get("risk_score", 0)
        categories = result.get("categories", [])

        for cat in categories:
            category_counts[cat] += 1
            category_risk_sum[cat] += risk

    severity_map = {}

    for cat, count in category_counts.items():

        base = CATEGORY_BASE_WEIGHTS.get(cat, 1)
        avg_risk = category_risk_sum[cat] / count if count else 0

        amplification = 0

        if count > 1:
            amplification += 1

        if avg_risk >= 7:
            amplification += 1

        severity = min(base + amplification, 4)
        severity_map[cat] = severity

    return severity_map


def detect_escalation(previous_map, current_map):

    escalations = {}

    for cat, current_strength in current_map.items():
        previous_strength = previous_map.get(cat, 0)

        if current_strength > previous_strength:
            escalations[cat] = {
                "previous": previous_strength,
                "current": current_strength
            }

    return escalations


def compute_timeline_drift(company_name, return_data=False):

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

    timeline_summary = []
    previous_severity_map = {}

    for i in range(1, len(versions)):

        old_text, old_time = versions[i - 1]
        new_text, new_time = versions[i]

        old_clean = normalize_text(old_text)
        new_clean = normalize_text(new_text)

        old_chunks = chunk_text(old_clean)
        new_chunks = chunk_text(new_clean)

        old_embeddings = embed_chunks(old_chunks)
        new_embeddings = embed_chunks(new_chunks)

        similarity_matrix = compute_similarity_matrix(old_embeddings, new_embeddings)

        modified = removed = added = 0
        matched_new_indices = set()

        for row in similarity_matrix:
            max_similarity = max(row)
            max_index = row.tolist().index(max_similarity)

            if max_similarity > 0.75:
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
                result = analyze_clause_with_llm(old_chunks, new_chunks[j])
                clause_results.append(result)

        semantic_score, semantic_level = aggregate_semantic_risk(
            clause_results,
            structural_drift
        )

        current_severity_map = compute_category_severity(clause_results)
        escalations = detect_escalation(previous_severity_map, current_severity_map)

        timeline_summary.append({
            "from": old_time,
            "to": new_time,
            "structural_drift": structural_drift,
            "semantic_score": semantic_score,
            "risk_level": semantic_level,
            "categories": current_severity_map,
            "escalations": escalations
        })

        previous_severity_map = current_severity_map

    if return_data:
        return timeline_summary

    print(json.dumps(timeline_summary, indent=2))