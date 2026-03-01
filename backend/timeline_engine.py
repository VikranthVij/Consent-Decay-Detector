import sqlite3
from backend.database import DB_PATH
from backend.text_processing import normalize_text
from backend.chunking import chunk_text
from backend.embedding_engine import embed_chunks, compute_similarity_matrix
from backend.llm_risk_engine import analyze_clause_with_llm


# ==============================
# Structural Drift (FIXED)
# ==============================

def compute_structural_drift(modified, removed, added, total_old, total_new):
    if total_old == 0 and total_new == 0:
        return 0.0

    max_possible = max(total_old, total_new)

    drift = (
        (modified * 0.4) +
        (removed * 0.3) +
        (added * 0.3)
    ) / max_possible * 100

    return round(min(drift, 100), 2)


# ==============================
# Escalation Intensity
# ==============================

def compute_escalation_intensity(previous_categories, current_categories):
    intensity = 0

    for category, current_value in current_categories.items():
        prev_value = previous_categories.get(category, 0)
        if current_value > prev_value:
            intensity += (current_value - prev_value)

    return min(round(intensity, 2), 10)


# ==============================
# Irreversibility Detection (FIXED)
# ==============================

IRREVERSIBLE_CATEGORIES = {
    "ai_training",
    "historical_data_reclassification",
    "profiling",
    "cross_platform_sharing",
    "automated_decision_making"
}


def is_irreversible(previous_categories, current_categories):
    """
    Irreversible only if NEW irreversible category appears
    """
    for cat in current_categories.keys():
        if (
            cat in IRREVERSIBLE_CATEGORIES and
            cat not in previous_categories
        ):
            return True
    return False


# ==============================
# Timeline Drift + CDI
# ==============================

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

    if len(versions) < 2:
        print("Not enough versions.")
        return

    timeline_results = []
    cumulative_cdi = 0
    previous_categories = {}

    print(f"\nTimeline Drift Analysis for {company_name}")
    print("=" * 75)

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

        unchanged = modified = removed = 0
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

        added = len(new_chunks) - len(matched_new_indices)

        # 🔥 Fixed Structural Drift
        structural_drift = compute_structural_drift(
            modified,
            removed,
            added,
            len(old_chunks),
            len(new_chunks)
        )

        clause_results = []
        category_severity = {}

        for j in range(len(new_chunks)):
            if j not in matched_new_indices:
                result = analyze_clause_with_llm(old_chunks, new_chunks[j])
                clause_results.append(result)

                for cat in result.get("categories", []):
                    category_severity[cat] = max(
                        category_severity.get(cat, 0),
                        result.get("risk_score", 0) // 2
                    )

        # ⚠ DO NOT TOUCH SEMANTIC RISK
        semantic_score = (
            sum([c["risk_score"] for c in clause_results]) / len(clause_results)
            if clause_results else 0
        )

        escalation_intensity = compute_escalation_intensity(
            previous_categories,
            category_severity
        )

        irreversible = is_irreversible(previous_categories, category_severity)

        # ==========================================
        # Improved Delta Risk Balance
        # ==========================================

        delta_risk = (
            0.25 * structural_drift +   # reduced structural weight
            0.5 * semantic_score +     # semantic unchanged
            0.25 * escalation_intensity  # slightly increased escalation
        )

        if irreversible:
            delta_risk *= 1.25

        delta_risk = round(delta_risk, 2)

        cumulative_cdi = min(round(cumulative_cdi + delta_risk, 2), 100)

        previous_categories = category_severity.copy()

        print(f"\n{old_time} → {new_time}")
        print(f"Structural Drift: {structural_drift}%")
        print(f"Semantic Risk: {round(semantic_score,2)}/10")
        print(f"Escalation Intensity: {escalation_intensity}")
        if irreversible:
            print("Irreversible Expansion Detected: YES")
        print(f"Consent Decay Index (CDI): {cumulative_cdi}/100")

        timeline_results.append({
            "from": old_time,
            "to": new_time,
            "structural_drift": structural_drift,
            "semantic_score": round(semantic_score, 2),
            "escalation_intensity": escalation_intensity,
            "irreversible": irreversible,
            "cdi": cumulative_cdi
        })

    print("\n" + "=" * 75)

    if return_data:
        return timeline_results