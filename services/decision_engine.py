def final_decision(merchant_status, bank_status, ai_result):
    """
    Combines rule-based logic with AI recommendation
    to produce a safe final decision.
    """

    ai_decision = ai_result["decision"]
    confidence = ai_result["confidence"]

    # RULE 1: Bank FAILED + Merchant SUCCESS → Always refund
    if bank_status == "FAILED" and merchant_status == "SUCCESS":
        return {
            "final_decision": "AUTO_REFUND",
            "reason": "Rule-based override: Bank failure with merchant success"
        }

    # RULE 2: Bank SUCCESS + Merchant FAILED → Update merchant
    if bank_status == "SUCCESS" and merchant_status == "FAILED":
        return {
            "final_decision": "UPDATE_STATUS",
            "reason": "Rule-based override: Bank success with merchant failure"
        }

    # RULE 3: Both SUCCESS → No refund, escalate
    if bank_status == "SUCCESS" and merchant_status == "SUCCESS":
        return {
            "final_decision": "ESCALATE",
            "reason": "Payment successful at both ends"
        }

    # RULE 4: Trust AI only if confidence is high
    if confidence >= 0.80:
        return {
            "final_decision": ai_decision,
            "reason": "AI decision accepted (high confidence)"
        }

    # RULE 5: Low confidence → Escalate
    return {
        "final_decision": "ESCALATE",
        "reason": "Low AI confidence, manual review required"
    }

if __name__ == "__main__":

    ai_result = {
        "decision": "AUTO_REFUND",
        "confidence": 0.85,
        "explanation": "Mismatch detected"
    }

    result = final_decision(
        merchant_status="SUCCESS",
        bank_status="FAILED",
        ai_result=ai_result
    )

    print(result)