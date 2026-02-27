from flask import Blueprint, request, jsonify
from datetime import datetime

from services import llm_service
from services.verification_service import verify_transaction
from services.refund_service import trigger_refund
from models.dispute_model import insert_dispute, get_all_disputes

dispute_bp = Blueprint("dispute", __name__)


# ==================================================
# 🔹 Route 1: UI / Chat-based Dispute (LLM-assisted)
# ==================================================
@dispute_bp.route("/dispute", methods=["POST"])
def raise_dispute():
    """
    Handles natural-language user dispute submission.
    Uses LLM only for:
    - parsing user input
    - asking clarifying questions
    - explaining backend decision
    """

    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    # 1️⃣ Parse user input using LLM (UI layer only)
    parsed_input = llm_service.parse_user_input(user_message)

    # 2️⃣ Ask clarifying questions if needed
    followup_questions = llm_service.generate_followup_questions(parsed_input)
    if followup_questions:
        return jsonify({
            "status": "NEED_MORE_INFO",
            "questions": followup_questions
        }), 200

    txn_id = parsed_input.get("transaction_id")
    dispute_reason = parsed_input.get("dispute_reason")

    if not txn_id:
        return jsonify({
            "status": "NEED_MORE_INFO",
            "questions": ["Please provide the transaction ID to proceed."]
        }), 200

    # 3️⃣ Rule-based backend verification (NO AI)
    verification = verify_transaction(txn_id)

    refund_info = None
    final_status = verification["verification_result"]

    if verification["verification_result"] == "REFUND_ELIGIBLE":
        refund_info = trigger_refund(txn_id)
        final_status = "REFUND_INITIATED"

    # 4️⃣ LLM explanation for user
    explanation = llm_service.generate_explanation({
        "final_status": final_status,
        "bank_status": verification["bank_status"],
        "merchant_status": verification["merchant_status"]
    })

    # 5️⃣ Store dispute (AI used ONLY for explanation)
    dispute_record = {
        "transaction_id": txn_id,
        "merchant_status": verification["merchant_status"],
        "bank_status": verification["bank_status"],
        "dispute_reason": dispute_reason,
        "verification_result": verification["verification_result"],
        "ai_decision": None,        # intentionally None (no AI decisions)
        "confidence": None,         # not applicable
        "explanation": explanation,
        "final_status": final_status,
        "created_at": datetime.now().isoformat()
    }

    insert_dispute(dispute_record)

    return jsonify({
        "transaction_id": txn_id,
        "status": final_status,
        "explanation": explanation,
        "refund": refund_info
    }), 200


# ==================================================
# 🔹 Route 2: Direct API Dispute (Rule-based only)
# ==================================================
@dispute_bp.route("/dispute/direct", methods=["POST"])
def raise_dispute_direct():
    """
    Handles direct API-based dispute submission
    (no LLM, fully rule-based).
    """

    data = request.get_json()

    txn_id = data.get("transaction_id")
    dispute_reason = data.get("dispute_reason")

    if not txn_id:
        return jsonify({"error": "transaction_id is required"}), 400

    # 1️⃣ Rule-based verification
    verification = verify_transaction(txn_id)

    refund_info = None
    final_status = verification["verification_result"]

    if verification["verification_result"] == "REFUND_ELIGIBLE":
        refund_info = trigger_refund(txn_id)
        final_status = "REFUND_INITIATED"

    # 2️⃣ Store dispute (no AI explanation here)
    dispute_record = {
        "transaction_id": txn_id,
        "merchant_status": verification["merchant_status"],
        "bank_status": verification["bank_status"],
        "dispute_reason": dispute_reason,
        "verification_result": verification["verification_result"],
        "ai_decision": None,
        "confidence": None,
        "explanation": None,
        "final_status": final_status,
        "created_at": datetime.now().isoformat()
    }

    insert_dispute(dispute_record)

    return jsonify({
        "transaction_id": txn_id,
        "verification_result": verification["verification_result"],
        "reason_code": verification.get("reason_code"),
        "refund": refund_info
    }), 200


# ==================================================
# 🔹 Route 3: List All Disputes (Dashboard)
# ==================================================
@dispute_bp.route("/disputes", methods=["GET"])
def list_disputes():
    disputes = get_all_disputes()
    return jsonify(disputes), 200