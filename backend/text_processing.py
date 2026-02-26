import re


def normalize_text(text):

    # Handle bytes from SQLite BLOB
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = "\n".join(line for line in text.split("\n") if line)

    return text


def preview_cleaning(original_text: str):
    """
    Prints before/after preview for debugging.
    """

    cleaned = normalize_text(original_text)

    print("\n" + "=" * 60)
    print("ORIGINAL (first 1000 chars)")
    print("=" * 60)
    print(original_text[:1000])

    print("\n" + "=" * 60)
    print("CLEANED (first 1000 chars)")
    print("=" * 60)
    print(cleaned[:1000])

    print("\n" + "=" * 60)
    print(f"Original Length: {len(original_text)}")
    print(f"Cleaned Length : {len(cleaned)}")
    print("=" * 60)

    return cleaned