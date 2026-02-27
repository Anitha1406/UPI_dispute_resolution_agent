import requests

def get_bank_transaction_status(txn_id):
    """
    Calls the mock bank API to fetch transaction status
    """
    url = f"http://127.0.0.1:5000/bank/transaction/{txn_id}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get("bank_status")
    return None