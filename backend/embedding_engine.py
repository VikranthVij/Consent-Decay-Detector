from sentence_transformers import SentenceTransformer
import numpy as np

# Load once globally
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks):
    """
    Convert list of text chunks into embedding vectors
    """
    embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings


def compute_similarity_matrix(old_embeddings, new_embeddings):

    # Remove any zero vectors
    old_embeddings = np.nan_to_num(old_embeddings)
    new_embeddings = np.nan_to_num(new_embeddings)

    similarity_matrix = np.dot(old_embeddings, new_embeddings.T)

    # Clamp values between -1 and 1
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)

    return similarity_matrix