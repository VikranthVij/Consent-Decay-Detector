import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing")

client = genai.Client(api_key=api_key)

MODEL = "gemini-2.0-flash"

def analyze_clause_with_llm(old_clauses, new_clause):

    old_context = "\n".join(old_clauses[:10])

    prompt = f"""
Compare OLD and NEW privacy policy clauses.

OLD:
{old_context}

NEW:
{new_clause}

Respond ONLY as valid JSON:

{{
  "risk_score": 0-10,
  "expansion": true/false,
  "reason": "short explanation"
}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,   # ✅ SIMPLE STRING
        )

        text = response.text.strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        data = json.loads(text[start:end])

        return {
            "risk_score": int(data.get("risk_score", 0)),
            "expansion": bool(data.get("expansion", False)),
            "reason": data.get("reason", ""),
        }

    except Exception as e:
        return {
            "risk_score": 0,
            "expansion": False,
            "reason": f"Gemini error: {str(e)}",
        }