import re


def normalize_text(text: str) -> str:
    """
    Cleans raw policy text while preserving paragraph structure.
    """

    if not text:
        return ""

    # 1️⃣ Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2️⃣ Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # 3️⃣ Remove multiple blank lines (keep max 1)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 4️⃣ Strip leading/trailing whitespace
    text = text.strip()

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