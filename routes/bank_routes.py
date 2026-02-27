from flask import Blueprint, jsonify

bank_bp = Blueprint("bank", __name__)

@bank_bp.route("/bank/transaction/<txn_id>", methods=["GET"])
def get_bank_transaction(txn_id):
    # Mock bank responses
    mock_transactions = {
        "TXN1001": "SUCCESS",
        "TXN1002": "FAILED",
        "TXN1003": "PENDING"
    }

    status = mock_transactions.get(txn_id, "FAILED")

    return jsonify({
        "transaction_id": txn_id,
        "bank_status": status
    })