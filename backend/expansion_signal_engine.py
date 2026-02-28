# ======================================
# Rule-Based Expansion Signal Extraction
# ======================================

EXPANSION_CATEGORIES = {
    "ai_training": [
        "machine learning",
        "artificial intelligence",
        "train models",
        "improve models",
        "predictive models",
        "model training",
    ],
    "profiling": [
        "profiling",
        "behavioral prediction",
        "automated decision",
    ],
    "retention_expansion": [
        "retain",
        "long-term storage",
        "data retention",
    ],
    "cross_platform_sharing": [
        "across products",
        "meta company products",
        "cross-platform",
    ],
    "data_aggregation": [
        "aggregation",
        "cross-platform analysis",
        "combined data",
    ],
}


def extract_expansion_signals(clause_text: str):
    clause_lower = clause_text.lower()
    detected_categories = []

    for category, keywords in EXPANSION_CATEGORIES.items():
        for keyword in keywords:
            if keyword in clause_lower:
                detected_categories.append(category)
                break

    return detected_categories