import requests
import json

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"


def analyze_clause_with_llm(old_clauses, new_clause):

    old_context = "\n".join(old_clauses[:10])

    prompt = f"""
You are a privacy policy risk analysis system.

Compare OLD and NEW clauses.

OLD:
{old_context}

NEW:
{new_clause}

Determine:

1. Does the NEW clause expand company rights?
2. Assign risk score (0-10).
3. Identify categories if present:
   - ai_training
   - profiling
   - retention_expansion
   - cross_platform_sharing
   - data_aggregation
4. Provide short explanation.

Respond ONLY as valid JSON:

{{
  "risk_score": <number>,
  "expansion": <true/false>,
  "categories": ["ai_training", "profiling", ...],
  "reason": "<short explanation>"
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

        try:
            result = json.loads(raw_output)
        except:
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            result = json.loads(raw_output[start:end])

        return {
            "risk_score": int(result.get("risk_score", 0)),
            "expansion": bool(result.get("expansion", False)),
            "categories": result.get("categories", []),
            "reason": result.get("reason", "No explanation provided.")
        }

    except Exception as e:
        return {
            "risk_score": 0,
            "expansion": False,
            "categories": [],
            "reason": f"LLM error: {str(e)}"
        }