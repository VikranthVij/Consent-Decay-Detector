import requests
import json

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"


def analyze_clause_with_llm(old_clauses, new_clause):
    """
    Sends clause comparison to local Ollama LLM
    Returns structured risk analysis
    """

    prompt = f"""
You are a privacy policy risk analysis system.

Compare the OLD policy clauses to the NEW clause below.

OLD POLICY:
{old_clauses[:10]}  # truncated for context

NEW CLAUSE:
{new_clause}

Determine:

1. Does the NEW clause expand company rights?
2. Does it introduce AI training, profiling, retention expansion, cross-platform sharing, or broader permissions?
3. Assign a risk score from 0 to 10.
4. Provide a short reason.

Respond ONLY in valid JSON:

{{
  "risk_score": <number>,
  "expansion": <true/false>,
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

        # Try parsing JSON safely
        try:
            result = json.loads(raw_output)
        except:
            # Fallback parsing if model adds extra text
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            result = json.loads(raw_output[start:end])

        return {
            "risk_score": int(result.get("risk_score", 0)),
            "expansion": bool(result.get("expansion", False)),
            "reason": result.get("reason", "No explanation provided.")
        }

    except Exception as e:
        return {
            "risk_score": 0,
            "expansion": False,
            "reason": f"LLM error: {str(e)}"
        }