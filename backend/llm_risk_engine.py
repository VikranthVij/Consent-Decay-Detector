import requests
import json
import re

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"


# -------------------------------
# Rule-Based Signal Extraction
# -------------------------------

RULE_SIGNALS = {
    "ai_training": ["train", "machine learning", "artificial intelligence"],
    "profiling": ["profiling", "behavioral prediction"],
    "cross_platform_sharing": ["across products", "cross-platform"],
    "data_aggregation": ["aggregate", "long-term data aggregation"],
    "retention_expansion": ["retain", "retention"]
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


# -------------------------------
# Safe JSON Extraction
# -------------------------------

def safe_extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return None


# -------------------------------
# Hybrid LLM + Rule Analysis
# -------------------------------

def analyze_clause_with_llm(old_clauses, new_clause):

    rule_categories = extract_rule_categories(new_clause)

    prompt = f"""
You are a privacy policy risk analysis system.

Compare OLD policy clauses to NEW clause.

OLD POLICY:
{old_clauses[:10]}

NEW CLAUSE:
{new_clause}

Return ONLY valid JSON:

{{
  "risk_score": number (0-10),
  "expansion": true/false,
  "categories": [list of risk categories],
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

        llm_categories = parsed.get("categories", [])

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