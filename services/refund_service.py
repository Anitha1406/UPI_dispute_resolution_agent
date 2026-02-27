def trigger_refund(txn_id, amount=0):
    """
    Mock refund trigger
    """
    return {
        "transaction_id": txn_id,
        "refund_status": "REFUND_INITIATED",
        "message": "Refund has been successfully initiated"
    }