import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"
REQUEST_TIMEOUT = 30  # seconds


# --------------------------------------------------
# Helper: Safe JSON Extraction from LLM Output
# --------------------------------------------------
def extract_json(text):
    """
    Safely extracts JSON object from LLM output text.
    """
    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM response")

    return json.loads(text[start:end])


# --------------------------------------------------
# 1️⃣ User Input → Structured Backend Input
# --------------------------------------------------
def parse_user_input(user_message):
    """
    Converts natural language user complaint into
    structured backend-ready input.
    """

    prompt = f"""
You are a payment dispute assistant.

Extract structured information from the user complaint.

User complaint:
"{user_message}"

Return ONLY valid JSON in this format:
{{
  "transaction_id": "<transaction id or null>",
  "dispute_reason": "<short standardized reason>"
}}

IMPORTANT:
- Do not include any explanation
- Do not include markdown
- Output ONLY raw JSON

Rules:
- If transaction ID is not mentioned, return null
- Keep dispute_reason concise and generic
"""

    # quick regex extraction to catch obvious transaction IDs (fallback when LLM misses them)
    import re
    tx_match = re.search(r"\b(?:TXN|UTR|TX|TID)[\s:\-]*([A-Za-z0-9\-_]{3,})\b", user_message, re.IGNORECASE)
    tx_guess = tx_match.group(1) if tx_match else None

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        raw_text = response.json()["response"]
        parsed = extract_json(raw_text)

        # if LLM didn't pick up the transaction id but regex found one, use it
        if (not parsed.get("transaction_id")) and tx_guess:
            parsed["transaction_id"] = tx_guess

        return parsed

    except Exception:
        # Safe fallback so backend never crashes; prefer regex guess if available
        return {
            "transaction_id": tx_guess if tx_guess else None,
            "dispute_reason": "Unable to parse user input"
        }


# --------------------------------------------------
# 2️⃣ Backend Result → User-Friendly Explanation
# --------------------------------------------------
def generate_explanation(backend_result):
    """
    Converts backend rule-based decision into
    a user-friendly explanation.
    """

    prompt = f"""
You are a UPI customer support assistant.

Explain the outcome in at most 3 short sentences.

Rules:
- Be clear and factual
- No greetings, no reassurance paragraphs
- No internal system mention
- Focus only on what happened and what happens next

Backend result:
{json.dumps(backend_result, indent=2)}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=90  # longer timeout ONLY for explanation
        )

        raw_text = response.json().get("response", "").strip()

        if raw_text:
            return raw_text

        return (
            "Your refund has been initiated. "
            "Please allow some time for the amount to be credited back."
        )

    except requests.exceptions.ReadTimeout:
        # Graceful degradation for slow local LLMs
        return (
            "Your transaction has been verified and the refund process has been initiated. "
            "The amount will be credited back to your account shortly."
        )

    except Exception:
        return (
            "Your request has been received and is currently being processed. "
            "Please check back shortly for an update."
        )


# --------------------------------------------------
# 3️⃣ (Optional) Clarifying Questions for User
# --------------------------------------------------
def generate_followup_questions(parsed_input):
    """
    Ask clarifying questions ONLY if transaction_id is missing.
    """

    if parsed_input.get("transaction_id"):
        return []

    prompt = f"""
You are a customer support assistant for UPI payment disputes.

The backend REQUIRES a transaction ID to proceed.

Structured input:
{json.dumps(parsed_input, indent=2)}

Rules:
- Ask questions ONLY to obtain the transaction ID
- Do NOT ask about merchant, order number, date, or any other details
- Ask at most ONE short question

Return ONLY valid JSON:
{{
  "questions": ["question"]
}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        raw_text = response.json()["response"]
        return extract_json(raw_text).get("questions", [])

    except Exception:
        return ["Please provide the transaction ID to proceed."]

# --------------------------------------------------
# 🧪 TEST ALL RESPONSIBILITIES
# --------------------------------------------------
if __name__ == "__main__":

    print("\n--- TEST 1: User Input Parsing ---")
    user_text = "My money was deducted but I didn't receive my order"
    parsed = parse_user_input(user_text)
    print(parsed)

    print("\n--- TEST 2: Clarifying Questions ---")
    questions = generate_followup_questions(parsed)
    print(questions)

    print("\n--- TEST 3: Backend Explanation ---")
    backend_result = {
        "final_status": "AUTO_REFUND",
        "bank_status": "FAILED",
        "merchant_status": "SUCCESS"
    }
    explanation = generate_explanation(backend_result)
    print(explanation)