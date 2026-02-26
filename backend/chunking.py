import re


def chunk_text(text: str) -> list:
    """
    Sentence-level chunking.
    Each sentence becomes a chunk.
    """

    if not text:
        return []

    # Split by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Clean and remove tiny fragments
    chunks = [s.strip() for s in sentences if len(s.strip()) > 20]

    return chunks