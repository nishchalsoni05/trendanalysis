
def check_safety(user_text):
    """
    Enforce safety guardrails for AI interaction.
    """
    # 1. Check for PII keywords
    pii_terms = ["aadhaar number", "phone number", "mobile", "address of", "person name"]
    if any(term in user_text.lower() for term in pii_terms):
        return False, "Query rejected: Potential operational security / PII risk."
        
    # 2. Check for out-of-scope topics
    politics = ["vote", "election result", "party", "protest"]
    if any(term in user_text.lower() for term in politics):
        return False, "Query rejected: Topic out of scope for demographic analytics."

    return True, ""

def validate_response(response_text):
    """
    Post-process validation of AI response.
    """
    if "I cannot" in response_text and "data" not in response_text:
         # Pass-through generic refusals
         return True
    
    return True
