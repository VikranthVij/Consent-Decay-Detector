import requests
import json
import re

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"


# ==========================================
# Controlled Risk Ontology
# ==========================================

ALLOWED_CATEGORIES = {
    "ai_training",
    "profiling",
    "cross_platform_sharing",
    "data_aggregation",
    "retention_expansion",
    "third_party_sharing",
    "automated_decision_making",
    "historical_data_reclassification"
}


# ==========================================
# Rule-Based Signal Extraction
# ==========================================

RULE_SIGNALS = {
    "ai_training": [
        "train",
        "machine learning",
        "artificial intelligence",
        "improve models"
    ],
    "profiling": [
        "profiling",
        "behavioral prediction",
        "automated profiling"
    ],
    "cross_platform_sharing": [
        "across products",
        "cross-platform",
        "meta company products"
    ],
    "data_aggregation": [
        "aggregate",
        "aggregation",
        "long-term data aggregation"
    ],
    "retention_expansion": [
        "retain",
        "retention",
        "store for extended period"
    ],
    "third_party_sharing": [
        "third party",
        "third-party",
        "external partners"
    ],
    "automated_decision_making": [
        "automated decision",
        "automated processing",
        "algorithmic decision"
    ],
    "historical_data_reclassification": [
        "historical data",
        "past interactions",
        "previously collected data"
    ]
}


def extract_rule_categories(text):
    text_lower = text.lower()
    categories = []

    for category, keywords in RULE_SIGNALS.items():
        for keyword in keywords:
            if keyword in text_lower:
                categories.append(category)
                break

    return categories


# ==========================================
# Safe JSON Extraction
# ==========================================

def safe_extract_json(text):

    # Remove markdown fences
    text = text.replace("```json", "").replace("```", "").strip()

    # Extract first JSON block (non-greedy)
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        return None

    json_candidate = match.group(0)

    # Remove trailing commas
    json_candidate = re.sub(r",\s*}", "}", json_candidate)
    json_candidate = re.sub(r",\s*]", "]", json_candidate)

    try:
        return json.loads(json_candidate)
    except json.JSONDecodeError:
        return None


# ==========================================
# Hybrid LLM + Rule Analysis
# ==========================================

def analyze_clause_with_llm(old_clauses, new_clause):

    # Rule-based categories
    rule_categories = extract_rule_categories(new_clause)

    prompt = f"""
You are a privacy policy risk analysis system.

Compare OLD policy clauses to NEW clause.

OLD POLICY:
{old_clauses[:10]}

NEW CLAUSE:
{new_clause}

Allowed categories:
- ai_training
- profiling
- cross_platform_sharing
- data_aggregation
- retention_expansion
- third_party_sharing
- automated_decision_making
- historical_data_reclassification

Return ONLY valid JSON:

{{
  "risk_score": number (0-10),
  "expansion": true/false,
  "categories": [list from allowed categories only],
  "reason": "short explanation"
}}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        raw_output = response.json()["response"]

        parsed = safe_extract_json(raw_output)

        if not parsed:
            raise ValueError("Invalid JSON from LLM")

        # Filter LLM categories to allowed ontology only
        llm_categories = [
            cat for cat in parsed.get("categories", [])
            if cat in ALLOWED_CATEGORIES
        ]

        # Merge rule + LLM categories
        final_categories = list(set(rule_categories + llm_categories))

        return {
            "risk_score": int(parsed.get("risk_score", 0)),
            "expansion": bool(parsed.get("expansion", False)),
            "categories": final_categories,
            "reason": parsed.get("reason", "")
        }

    except Exception as e:
        return {
            "risk_score": 0,
            "expansion": False,
            "categories": rule_categories,
            "reason": f"LLM error: {str(e)}"
        }