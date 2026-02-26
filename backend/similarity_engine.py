import numpy as np


def safe_cosine_similarity(a, b):
    """
    Manually compute cosine similarity to avoid divide-by-zero issues.
    """

    # Normalize vectors
    a_norm = np.linalg.norm(a, axis=1, keepdims=True)
    b_norm = np.linalg.norm(b, axis=1, keepdims=True)

    # Avoid division by zero
    a_norm[a_norm == 0] = 1e-10
    b_norm[b_norm == 0] = 1e-10

    a_normalized = a / a_norm
    b_normalized = b / b_norm

    return np.dot(a_normalized, b_normalized.T)


def compute_similarity_matrix(old_vectors, new_vectors):
    if len(old_vectors) == 0 or len(new_vectors) == 0:
        return np.array([])

    return safe_cosine_similarity(old_vectors, new_vectors)