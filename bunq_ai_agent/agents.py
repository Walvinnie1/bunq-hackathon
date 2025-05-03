# Implementation of different AI agents 
import json
from llm_client import get_llm_response
# We assume transaction data is fetched elsewhere and passed to these functions
# from bunq_client import get_all_transactions


def serialize_bunq_objects(obj):
    """Helper function to serialize bunq SDK objects for JSON dumping."""
    if hasattr(obj, '__dict__'):
        # Convert object attributes to dictionary
        # Handle specific types if needed (like MonetaryAccountBank)
        if hasattr(obj, 'to_dict'): # Many bunq objects have this method
            return obj.to_dict()
        # Basic fallback
        return {k: serialize_bunq_objects(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
    elif isinstance(obj, list):
        return [serialize_bunq_objects(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_bunq_objects(v) for k, v in obj.items()}
    else:
        # Basic types (int, str, float, bool, None)
        return obj

def analyze_subscriptions(transactions):
    """Analyzes a list of transactions to identify potential subscriptions using an LLM.

    Args:
        transactions: A list of bunq Payment objects.

    Returns:
        A tuple containing the action (str) and details (dict).
    """
    print(f"\n--- Starting Subscription Analysis for {len(transactions)} transactions ---")
    if not transactions:
        return "none", {"message": "No transactions provided for subscription analysis."}

    # 1. Pre-process transactions: Serialize relevant fields for the prompt
    # We need to carefully select what to send to avoid exceeding token limits
    # Sending details of recent transactions might be more useful than just a summary
    simplified_transactions = []
    for tx in transactions[:20]: # Limit the number of transactions sent to LLM
        simplified_tx = {
            "id": getattr(tx, 'id_', None),
            "description": getattr(tx, 'description', 'N/A'),
            "amount": getattr(tx.amount, 'value', 'N/A'),
            "currency": getattr(tx.amount, 'currency', 'N/A'),
            "created": getattr(tx, 'created', 'N/A'),
            "type": getattr(tx, 'type', 'N/A'), # e.g., PAYMENT, MASTERCARD
            "sub_type": getattr(tx, 'sub_type', 'N/A'), # e.g., ONCE, RECURRING
            "counterparty_alias": getattr(tx.counterparty_alias, 'display_name', 'N/A')
        }
        simplified_transactions.append(simplified_tx)

    transaction_summary = json.dumps(simplified_transactions, indent=2)

    # 2. Create prompt
    prompt = f"""
    Analyze the following recent transactions to identify potential recurring subscriptions:
    ```json
    {transaction_summary}
    ```

    Based *only* on the provided data, consider patterns in description, counterparty, and amount:
    1. List potential subscriptions (merchant name/description, amount). Infer frequency (monthly, yearly) if possible from patterns *within this data*, otherwise state 'unknown frequency'.
    2. Identify any transactions that might represent unusual or potentially unwanted subscriptions based on common service costs or vague descriptions.
    3. Suggest concise text for a user notification summarizing the findings (potential subscriptions and any flagged as unusual).

    Respond ONLY in valid JSON format with the following structure:
    {{ 
      "potential_subscriptions": [{{ "merchant": "...", "amount": "...", "currency": "...", "inferred_frequency": "..." }}], 
      "unusual_subscriptions": [{{ "merchant": "...", "amount": "...", "currency": "...", "reason": "..." }}], 
      "notification_text": "..."
    }}
    """

    # 3. Call LLM
    response_text = get_llm_response(prompt) # Use default model from llm_client

    # 4. Parse response and determine action
    if not response_text:
        print("Error: Did not receive response from LLM for subscriptions.")
        return "error", {"message": "Failed to get LLM subscription analysis."}

    try:
        # Clean the response text in case the LLM adds markdown backticks
        cleaned_response_text = response_text.strip().strip("`json\n").strip("\n```")
        analysis = json.loads(cleaned_response_text)
        
        # Basic validation of parsed structure
        if not all(k in analysis for k in ["potential_subscriptions", "unusual_subscriptions", "notification_text"]):
             raise ValueError("LLM response missing required keys.")
             
        action = "notify"
        details = {"text": analysis.get("notification_text", "Could not generate summary."), "analysis": analysis}
        print(f"Subscription Analysis Result: {json.dumps(analysis, indent=2)}")
        return action, details
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error parsing LLM response for subscriptions: {e}")
        print(f"Raw LLM Response:\n{response_text}") # Log raw response for debugging
        return "error", {"message": f"Failed to parse LLM subscription analysis: {e}"}


def analyze_purchase(transaction):
    """Analyzes a single transaction for potential fraud using an LLM.

    Args:
        transaction: A bunq Payment object.

    Returns:
        A tuple containing the action (str) and details (dict).
    """
    print(f"\n--- Starting Purchase Analysis for Transaction ID: {getattr(transaction, 'id_', 'N/A')} ---")
    
    # Serialize the single transaction
    # simplified_tx = serialize_bunq_objects(transaction)
    # More controlled serialization:
    simplified_tx = {
        "id": getattr(transaction, 'id_', None),
        "description": getattr(transaction, 'description', 'N/A'),
        "amount": getattr(transaction.amount, 'value', 'N/A'),
        "currency": getattr(transaction.amount, 'currency', 'N/A'),
        "created": getattr(transaction, 'created', 'N/A'),
        "type": getattr(transaction, 'type', 'N/A'),
        "sub_type": getattr(transaction, 'sub_type', 'N/A'),
        "counterparty_alias": getattr(transaction.counterparty_alias, 'display_name', 'N/A'),
        "merchant_country": getattr(transaction.counterparty_alias, 'country', 'N/A'), # Example: if available
         # Add other potentially relevant fields if available in your Payment object structure
         # e.g., merchant category code (MCC) if accessible
    }
    transaction_str = json.dumps(simplified_tx, indent=2)

    prompt = f"""
    Analyze this single bank transaction for potential signs of fraud:
    ```json
    {transaction_str}
    ```

    Consider factors like: unusual merchant description, high amount compared to typical small purchases (assume user usually spends moderately), transaction time (if unusual, e.g., late night), vague description, or uncommon country (if available). Assume you don't have historical user data, focus only on this transaction's details.

    Answer the following questions based ONLY on the provided transaction data:
    1. Is this transaction suspicious? (Answer strictly "Yes" or "No")
    2. Provide a brief reason for your suspicion or lack thereof.
    3. Should this transaction be flagged for manual review or potential blocking? (Answer strictly "Yes" or "No" - be conservative, only flag if strong indicators exist).
    4. If suspicious, suggest concise notification text for the user.

    Respond ONLY in valid JSON format with the following structure:
    {{ 
      "suspicious": "Yes/No", 
      "reason": "...", 
      "suggest_block": "Yes/No", 
      "notification_text": "..." 
    }}
    Ensure the response is only the JSON object, without any additional text or markdown formatting.
    """
    response_text = get_llm_response(prompt) # Use default model from llm_client

    if not response_text:
        print("Error: Did not receive response from LLM for purchase analysis.")
        return "error", {"message": "Failed to get LLM purchase analysis.", "transaction_id": simplified_tx.get('id')}

    try:
        # Clean the response text
        cleaned_response_text = response_text.strip().strip("`json\n").strip("\n```")
        analysis = json.loads(cleaned_response_text)

        # Validate response structure
        if not all(k in analysis for k in ["suspicious", "reason", "suggest_block", "notification_text"]):
             raise ValueError("LLM response missing required keys.")
        if analysis.get("suspicious") not in ["Yes", "No"] or analysis.get("suggest_block") not in ["Yes", "No"]:
             raise ValueError("Invalid Yes/No value in LLM response.")

        print(f"Purchase Analysis Result: {json.dumps(analysis, indent=2)}")
        tx_id = simplified_tx.get('id')

        if analysis.get("suggest_block") == "Yes":
            # CRITICAL: Do NOT automatically block. Log suggestion.
            print(f"LLM suggests blocking transaction ID: {tx_id}")
            action = "suggest_block"
            details = {"text": analysis.get("notification_text", "Suspicious transaction requires review."), "reason": analysis.get("reason"), "transaction_id": tx_id, "analysis": analysis}
        elif analysis.get("suspicious") == "Yes":
            action = "notify"
            details = {"text": analysis.get("notification_text", "A transaction might need your attention."), "reason": analysis.get("reason"), "transaction_id": tx_id, "analysis": analysis}
        else:
            action = "none" # Transaction deemed not suspicious
            details = {"transaction_id": tx_id}
        return action, details

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error parsing LLM response for purchase {simplified_tx.get('id')}: {e}")
        print(f"Raw LLM Response:\n{response_text}")
        return "error", {"message": f"Failed to parse LLM purchase analysis: {e}", "transaction_id": simplified_tx.get('id')}


def generate_saving_recommendations(transactions):
     """(Placeholder) Analyzes transactions to generate saving recommendations."""
     print("\n--- Generating Saving Recommendations (Placeholder) ---")
     # TODO: Implement Agent 4 logic
     # 1. Process transactions (maybe categorize, summarize spending)
     # 2. Create a suitable prompt for the LLM
     # 3. Call get_llm_response
     # 4. Parse response and format action/details
     return "none", {"message": "Savings recommendation agent not implemented yet."} 