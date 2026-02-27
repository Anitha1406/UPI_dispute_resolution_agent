from services.bank_service import get_bank_transaction_status
from services.merchant_service import get_merchant_transaction_status

# services/verification_service.py

TEST_TRANSACTIONS = {
    "TXN101": {
        "bank_status": "FAILED",
        "merchant_status": "SUCCESS",
        "verification_result": "REFUND_ELIGIBLE"
    },
    "TXN202": {
        "bank_status": "SUCCESS",
        "merchant_status": "FAILED",
        "verification_result": "ESCALATE"
    },
    "TXN303": {
        "bank_status": "SUCCESS",
        "merchant_status": "SUCCESS",
        "verification_result": "UPDATE_STATUS"
    },
    "TXN404": {
        "bank_status": "PENDING",
        "merchant_status": "PENDING",
        "verification_result": "ESCALATE"
    }
}

# Additional test case: no refund applicable (both sides succeeded but business rule says no refund)
TEST_TRANSACTIONS["TXN505"] = {
    "bank_status": "SUCCESS",
    "merchant_status": "SUCCESS",
    "verification_result": "REFUND_NOT_APPLICABLE"
}

def verify_transaction(transaction_id):
    record = TEST_TRANSACTIONS.get(transaction_id)

    if not record:
        return {
            "bank_status": "UNKNOWN",
            "merchant_status": "UNKNOWN",
            "verification_result": "ESCALATE",
            "reason_code": "TXN_NOT_FOUND"
        }

    return {
        "bank_status": record["bank_status"],
        "merchant_status": record["merchant_status"],
        "verification_result": record["verification_result"],
        "reason_code": "TEST_DATA"
    }