# Risk categories with weights
RISK_KEYWORDS = {
    "ai_training": {
        "keywords": ["ai", "machine learning", "train models"],
        "weight": 3,
    },
    "third_party_sharing": {
        "keywords": ["third party", "third-party", "partners", "affiliates", "share with"],
        "weight": 2,
    },
    "biometric_data": {
        "keywords": ["biometric", "facial recognition", "voiceprint"],
        "weight": 4,
    },
    "retention_extension": {
        "keywords": ["retain indefinitely", "no retention limit", "longer retention"],
        "weight": 2,
    },
    "data_sale": {
        "keywords": ["sell data", "sale of data"],
        "weight": 5,
    },
}


def analyze_risk(added_clauses, modified_clauses):
    risk_score = 0
    flagged_clauses = []

    all_changed = added_clauses + modified_clauses

    for clause in all_changed:
        clause_lower = clause.lower()

        # Normalize hyphenated words
        clause_normalized = clause_lower.replace("-", " ")

        clause_flagged = False

        for category, data in RISK_KEYWORDS.items():
            for keyword in data["keywords"]:
                keyword_normalized = keyword.lower().replace("-", " ")

                if keyword_normalized in clause_normalized:
                    risk_score += data["weight"]
                    clause_flagged = True
                    break

        if clause_flagged:
            flagged_clauses.append(clause)

    # Risk level thresholds
    if risk_score == 0:
        risk_level = "LOW"
    elif risk_score <= 3:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    return risk_level, flagged_clauses