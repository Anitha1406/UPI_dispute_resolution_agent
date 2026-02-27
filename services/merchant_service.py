def get_merchant_transaction_status(txn_id):
    """
    Mock merchant transaction lookup
    """

    mock_merchant_transactions = {
        "TXN1001": "SUCCESS",
        "TXN1002": "SUCCESS",   # Bank FAILED, Merchant SUCCESS (refund case)
        "TXN1003": "PENDING"
    }

    return mock_merchant_transactions.get(txn_id, "FAILED")