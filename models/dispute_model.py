import sqlite3
from datetime import datetime

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "dispute.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_dispute_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disputes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT,
    merchant_status TEXT,
    bank_status TEXT,
    dispute_reason TEXT,

    verification_result TEXT,   -- NEW (rule-based outcome)

    ai_decision TEXT,            -- for future LLM use
    confidence REAL,             -- for future LLM use
    explanation TEXT,            -- LLM-generated, nullable

    final_status TEXT,
    created_at TEXT
);
    """)

    conn.commit()
    conn.close()

def insert_dispute(data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO disputes (
    transaction_id,
    merchant_status,
    bank_status,
    dispute_reason,
    verification_result,
    ai_decision,
    confidence,
    explanation,
    final_status,
    created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("transaction_id"),
        data.get("merchant_status"),
        data.get("bank_status"),
        data.get("dispute_reason"),
        data.get("verification_result"),
        data.get("ai_decision"),
        data.get("confidence"),
        data.get("explanation"),
        data.get("final_status"),
        data.get("created_at")
    ))

    conn.commit()
    conn.close()
def get_dispute_by_transaction_id(txn_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM disputes WHERE transaction_id = ?",
        (txn_id,)
    )

    row = cursor.fetchone()
    conn.close()
    return row


def get_all_disputes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM disputes")
    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]
    results = []

    for row in rows:
        results.append(dict(zip(columns, row)))

    conn.close()
    return results

if __name__ == "__main__":
    create_dispute_table()
    print("Disputes table created successfully")