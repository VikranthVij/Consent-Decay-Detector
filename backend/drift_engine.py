import numpy as np
from backend.versioning import get_earliest_and_latest
from backend.text_processing import normalize_text
from backend.chunking import chunk_text
from backend.embedding_engine import generate_embeddings
from backend.similarity_engine import compute_similarity_matrix


# Similarity thresholds
SIMILARITY_SAME = 0.85
SIMILARITY_MODIFIED = 0.60


def classify_drift(old_chunks, new_chunks, similarity_matrix):
    """
    Classify clauses into:
    - unchanged
    - modified
    - removed
    - added
    """

    unchanged = 0
    modified = 0
    removed = 0

    matched_new_indices = set()

    for i in range(len(old_chunks)):

        if similarity_matrix.size == 0:
            removed += 1
            continue

        row = similarity_matrix[i]
        max_sim = np.max(row)
        max_index = np.argmax(row)

        if max_sim >= SIMILARITY_SAME:
            unchanged += 1
            matched_new_indices.add(max_index)

        elif SIMILARITY_MODIFIED <= max_sim < SIMILARITY_SAME:
            modified += 1
            matched_new_indices.add(max_index)

        else:
            removed += 1

    # New clauses that were never matched
    added = len(new_chunks) - len(matched_new_indices)

    return unchanged, modified, removed, added


def compute_drift_score(modified, removed, added, total_old):
    """
    Structural Drift Score (percentage of clauses changed)
    """

    if total_old == 0:
        return 0.0

    total_changes = modified + removed + added
    structural_drift = (total_changes / total_old) * 100

    return round(structural_drift, 2)


def compute_policy_drift(company_name: str):
    """
    Full drift detection pipeline
    """

    versions = get_earliest_and_latest(company_name)

    if not versions or not versions[0] or not versions[1]:
        print("Not enough versions to compare.")
        return

    old_text = versions[0]
    new_text = versions[1]

    # 1️⃣ Normalize
    old_clean = normalize_text(old_text)
    new_clean = normalize_text(new_text)

    # 2️⃣ Sentence-level chunking
    old_chunks = chunk_text(old_clean)
    new_chunks = chunk_text(new_clean)

    print(f"\nOld Chunks: {len(old_chunks)}")
    print(f"New Chunks: {len(new_chunks)}")

    if len(old_chunks) == 0 or len(new_chunks) == 0:
        print("Chunking failed — no clauses detected.")
        return

    # 3️⃣ Generate embeddings
    old_vectors = generate_embeddings(old_chunks)
    new_vectors = generate_embeddings(new_chunks)

    # 4️⃣ Compute similarity matrix
    similarity_matrix = compute_similarity_matrix(old_vectors, new_vectors)

    # 5️⃣ Classify structural changes
    unchanged, modified, removed, added = classify_drift(
        old_chunks, new_chunks, similarity_matrix
    )

    # 6️⃣ Compute structural drift percentage
    drift_percentage = compute_drift_score(
        modified, removed, added, len(old_chunks)
    )

    # 7️⃣ Print formatted report
    print("\n--- Policy Drift Report ---")
    print(f"Total Clauses (Old): {len(old_chunks)}")
    print(f"Total Clauses (New): {len(new_chunks)}")

    print(f"\nUnchanged Clauses : {unchanged}")
    print(f"Modified Clauses  : {modified}")
    print(f"Removed Clauses   : {removed}")
    print(f"Added Clauses     : {added}")

    print(f"\nStructural Drift  : {drift_percentage}%")

    return {
        "unchanged": unchanged,
        "modified": modified,
        "removed": removed,
        "added": added,
        "structural_drift_percentage": drift_percentage
    }


if __name__ == "__main__":
    compute_policy_drift("WhatsApp")