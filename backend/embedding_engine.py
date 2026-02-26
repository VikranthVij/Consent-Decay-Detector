from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once globally
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(chunks):
    if not chunks:
        return np.array([])

    embeddings = model.encode(chunks)

    # Convert to numpy array
    embeddings = np.array(embeddings)

    # Replace NaN or inf
    embeddings = np.nan_to_num(embeddings)

    return embeddings