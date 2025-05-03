# Implementation of different AI agents 
import json
import datetime # Needed for potential date manipulation in prompts if required
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

def simplify_transaction_for_prompt(tx):
     """Creates a simplified dictionary from a bunq transaction object for LLM prompts."""
     # Extract relevant fields safely using getattr
     amount_obj = getattr(tx, 'amount', None)
     counterparty_alias_obj = getattr(tx, 'counterparty_alias', None)

     return {
        "id": getattr(tx, 'id_', None),
        "description": getattr(tx, 'description', 'N/A'),
        "amount": getattr(amount_obj, 'value', 'N/A') if amount_obj else 'N/A',
        "currency": getattr(amount_obj, 'currency', 'N/A') if amount_obj else 'N/A',
        "created": getattr(tx, 'created', 'N/A'),
        "type": getattr(tx, 'type', 'N/A'), # e.g., PAYMENT, MASTERCARD
        "sub_type": getattr(tx, 'sub_type', 'N/A'), # e.g., ONCE, RECURRING
        "counterparty_display_name": getattr(counterparty_alias_obj, 'display_name', 'N/A') if counterparty_alias_obj else 'N/A',
        "counterparty_iban": getattr(counterparty_alias_obj, 'iban', 'N/A') if counterparty_alias_obj else 'N/A', # Add IBAN if useful
        # Add other fields as needed, e.g., 'merchant_country'
     }

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

# --- Agent 0: Transaction Classifier ---
def classify_transaction(transaction):
    """Classifies a single transaction using an LLM.

    Args:
        transaction: A bunq Payment object.

    Returns:
        A string classification ("Subscription", "Online Purchase", "Offline Purchase", "Unknown")
        or None if an error occurs.
    """
    print(f"\n--- Agent 0: Classifying Transaction ID: {getattr(transaction, 'id_', 'N/A')} ---")

    simplified_tx = simplify_transaction_for_prompt(transaction)
    transaction_json = json.dumps(simplified_tx, indent=2)

    prompt = f"""
You are an AI assistant specializing in classifying bank transactions. Your task is to analyze the details of a single new transaction and determine its most likely type.

**Transaction Details:**
```json
{transaction_json}
```

Instructions:

Analyze the provided transaction details, paying close attention to the merchant name/description, transaction type code (if available), and amount consistency (though you only have one transaction here, common subscription names are key).

Determine if the transaction is most likely:

*   **Subscription:** Recurring payment for a service (e.g., Netflix, Spotify, Gym Membership, Software). Often identifiable by merchant name. Direct debits can be subscriptions but aren't always.
*   **Online Purchase:** A one-off or infrequent purchase made via the internet (e.g., Amazon, food delivery app, online store, iDEAL payment). May have transaction types like 'IDEAL' or come from known e-commerce merchants.
*   **Offline Purchase:** A purchase made physically using a card or phone (e.g., Point-of-Sale terminal, supermarket, restaurant). Often associated with 'MASTERCARD', 'MAESTRO', 'VISA' types at physical vendors, but can overlap with online. Use merchant description context if available.

Provide your classification in JSON format.

Output Format (JSON):
{{
  "classified_type": "Subscription | Online Purchase | Offline Purchase"
}}
    """

    response_text = get_llm_response(prompt)

    if not response_text:
        print("Error: Did not receive response from LLM for classification.")
        return None

    try:
        cleaned_response_text = response_text.strip().strip("`json\n").strip("\n```")
        analysis = json.loads(cleaned_response_text)

        classified_type = analysis.get("classified_type")
        if classified_type in ["Subscription", "Online Purchase", "Offline Purchase"]:
            print(f"Transaction classified as: {classified_type}")
            return classified_type
        else:
            print(f"Warning: LLM returned unexpected classification: {classified_type}. Treating as Unknown.")
            return "Unknown"
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error parsing LLM response for classification: {e}")
        print(f"Raw LLM Response:\n{response_text}")
        return None

# --- Agent 1: Subscription Analyzer ---
def analyze_subscription_transaction(current_transaction, historical_transactions, time_frame_months=3):
    """Analyzes a new subscription, checks history for similar ones.

    Args:
        current_transaction: The bunq Payment object classified as Subscription.
        historical_transactions: A list of recent bunq Payment objects.
        time_frame_months: The lookback period in months for history.

    Returns:
        A tuple containing the action (str) and details (dict).
    """
    current_tx_id = getattr(current_transaction, 'id_', 'N/A')
    print(f"\n--- Agent 1: Analyzing Subscription Transaction ID: {current_tx_id} ---")

    simplified_current_tx = simplify_transaction_for_prompt(current_transaction)
    current_transaction_json = json.dumps(simplified_current_tx, indent=2)

    # Prepare historical data (limit size for prompt)
    simplified_history = [simplify_transaction_for_prompt(tx) for tx in historical_transactions if getattr(tx, 'id_', None) != current_tx_id]
    # Limit history size further if needed based on token limits
    MAX_HISTORY_ITEMS = 50
    historical_transactions_json = json.dumps(simplified_history[:MAX_HISTORY_ITEMS], indent=2)


    prompt = f"""
You are an AI financial assistant specializing in subscription management. You have received a transaction classified as a 'Subscription' and recent transaction history. Your task is to identify the specific service, check for similar potentially redundant subscriptions, and generate a helpful notification.

**Current Subscription Transaction:**
```json
{current_transaction_json}
```

**Recent Transaction History (Last {time_frame_months} Months):**
```json
{historical_transactions_json}
```

Instructions:

1.  **Identify Service:** Determine the specific service name for the Current Subscription Transaction (e.g., "Spotify", "Netflix", "Basic-Fit Gym").
2.  **Identify Category:** Determine the category of this service (e.g., "Music Streaming", "Video Streaming", "Fitness", "Software").
3.  **Scan History for Similar Services:** Analyze the Recent Transaction History to find other recurring payments within the **same category**. Look for different merchants offering comparable services (e.g., if the current is Spotify, look for Apple Music, YouTube Music, Deezer). List their names/descriptions.
4.  **Generate Suggestion:**
    *   If one or more similar/redundant subscriptions are found in the history: Generate a `notification_text` suggesting the user might have overlapping services and could consider cancelling one. Mention the current service and the similar ones found. Set `suggestion_type` to "Consider Cancellation".
    *   If no similar subscriptions are found: Generate a simple `notification_text` acknowledging the new subscription payment. Set `suggestion_type` to "Acknowledgment".

Provide your analysis and the notification text in JSON format ONLY.

Output Format (JSON):
{{
  "identified_service": "string",
  "service_category": "string",
  "similar_services_found": ["string"],
  "suggestion_type": "Consider Cancellation | Acknowledgment",
  "notification_text": "string"
}}
    """

    response_text = get_llm_response(prompt)

    if not response_text:
        print("Error: Did not receive response from LLM for subscription analysis.")
        return "error", {"message": "Failed to get LLM subscription analysis.", "transaction_id": current_tx_id}

    try:
        cleaned_response_text = response_text.strip().strip("`json\n").strip("\n```")
        analysis = json.loads(cleaned_response_text)

        # Basic validation
        required_keys = ["identified_service", "service_category", "similar_services_found", "suggestion_type", "notification_text"]
        if not all(k in analysis for k in required_keys):
             raise ValueError("LLM response missing required keys for subscription analysis.")

        action = "notify" # Always notify for subscriptions in this flow
        details = {"text": analysis.get("notification_text", "Subscription processed."), "analysis": analysis, "transaction_id": current_tx_id}
        print(f"Subscription Analysis Result: {json.dumps(analysis, indent=2)}")
        return action, details
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error parsing LLM response for subscription {current_tx_id}: {e}")
        print(f"Raw LLM Response:\n{response_text}")
        return "error", {"message": f"Failed to parse LLM subscription analysis: {e}", "transaction_id": current_tx_id}


# --- Agent 2: Online Purchase Analyzer ---
def analyze_online_purchase(current_transaction, historical_transactions, time_frame_months=3):
    """Analyzes an online purchase against historical spending patterns.

     Args:
        current_transaction: The bunq Payment object classified as Online Purchase.
        historical_transactions: A list of recent bunq Payment objects.
        time_frame_months: The lookback period in months for history.

    Returns:
        A tuple containing the action (str) and details (dict).
    """
    current_tx_id = getattr(current_transaction, 'id_', 'N/A')
    print(f"\n--- Agent 2: Analyzing Online Purchase Transaction ID: {current_tx_id} ---")

    simplified_current_tx = simplify_transaction_for_prompt(current_transaction)
    current_transaction_json = json.dumps(simplified_current_tx, indent=2)

    # Prepare historical data
    simplified_history = [simplify_transaction_for_prompt(tx) for tx in historical_transactions if getattr(tx, 'id_', None) != current_tx_id]
    MAX_HISTORY_ITEMS = 100 # Allow more history for pattern analysis
    historical_transactions_json = json.dumps(simplified_history[:MAX_HISTORY_ITEMS], indent=2)

    prompt = f"""
You are an AI financial assistant analyzing online spending patterns and detecting potential fraud. You have received a transaction classified as an 'Online Purchase' and historical transaction data. Your tasks are to categorize the purchase, analyze spending patterns within that category, flag highly anomalous outliers, and suggest an appropriate action (notify or flag for block).

**Current Online Purchase Transaction:**
```json
{current_transaction_json}
```

**Relevant Transaction History (Last {time_frame_months} Months):**
```json
{historical_transactions_json}
```

Instructions:

1.  **Categorize Purchase:** Determine the spending category for the Current Online Purchase Transaction (e.g., "Food Delivery", "Online Clothing Shopping", "Electronics", "Software/Apps", "Travel Booking", "Other").
2.  **Analyze Spending Pattern for Wisdom:**
    *   Filter the Relevant Transaction History to find other transactions likely in the **same category**.
    *   Analyze the typical spending amount, frequency, and **timing** (e.g., day of week/month) within this category based on the history. Provide a brief summary in `typical_spending_info`.
    *   Compare the Current Online Purchase Transaction to this pattern. Set `is_deviation` (boolean) and provide a `deviation_reason` (string or null) if it deviates significantly (e.g., "Amount much higher than usual for [Category]", "Purchase timing unusual based on history for [Category]"). The goal is to highlight potentially unwise spending relative to established habits.
3.  **Detect Highly Suspicious Outliers:** Independently, assess if the Current Online Purchase Transaction amount/context is extremely anomalous and potentially fraudulent (e.g., a 5-figure sum for 'Online Game Store'). Set `is_highly_suspicious_outlier` (boolean).
4.  **Determine Action and Generate Notification:**
    *   If `is_highly_suspicious_outlier` is true: Set `action_suggestion` to "Flag for Block". Generate concise `notification_text` explaining why (e.g., "Security Alert: Unusually large online purchase of [Amount] at [Merchant] detected. Review immediately.").
    *   Else if `is_deviation` is true: Set `action_suggestion` to "Notify". Generate `notification_text` offering insight into the spending pattern deviation (e.g., "Spending Insight: This purchase of €[Amount] for [Category] differs from your usual pattern (Reason: [Deviation Reason]).").
    *   Else: Set `action_suggestion` to "None". Set `notification_text` to null.

Provide your analysis and the suggested action/notification in JSON format ONLY.

Output Format (JSON):
{{
  "purchase_category": "string",
  "pattern_analysis": {{
    "typical_spending_info": "string",
    "is_deviation": boolean,
    "deviation_reason": "string | null"
  }},
  "is_highly_suspicious_outlier": boolean,
  "action_suggestion": "Flag for Block | Notify | None",
  "notification_text": "string | null"
}}
    """

    response_text = get_llm_response(prompt) # Use default model

    if not response_text:
        print("Error: Did not receive response from LLM for online purchase analysis.")
        return "error", {"message": "Failed to get LLM online purchase analysis.", "transaction_id": current_tx_id}

    try:
        cleaned_response_text = response_text.strip().strip("`json\n").strip("\n```")
        analysis = json.loads(cleaned_response_text)

        # Basic validation
        required_keys = ["purchase_category", "pattern_analysis", "is_highly_suspicious_outlier", "action_suggestion", "notification_text"]
        if not all(k in analysis for k in required_keys) or not isinstance(analysis.get("pattern_analysis"), dict):
             raise ValueError("LLM response missing required keys for online purchase analysis.")
        if analysis.get("action_suggestion") not in ["Flag for Block", "Notify", "None"]:
             raise ValueError("Invalid action_suggestion value in online purchase analysis.")

        suggested_action = analysis.get("action_suggestion")
        action = "none" # Default action
        if suggested_action == "Flag for Block":
            action = "suggest_block" # Map LLM suggestion to our internal action name
        elif suggested_action == "Notify":
            action = "notify"

        details = {"text": analysis.get("notification_text"), "analysis": analysis, "transaction_id": current_tx_id}
        print(f"Online Purchase Analysis Result: {json.dumps(analysis, indent=2)}")
        return action, details

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error parsing LLM response for online purchase {current_tx_id}: {e}")
        print(f"Raw LLM Response:\n{response_text}")
        return "error", {"message": f"Failed to parse LLM online purchase analysis: {e}", "transaction_id": current_tx_id}

# --- Agent 3: Offline Purchase Analyzer ---
def analyze_offline_purchase(current_transaction, historical_transactions, time_frame_months=3):
    """Analyzes an offline purchase against historical spending patterns (Notification only).

     Args:
        current_transaction: The bunq Payment object classified as Offline Purchase.
        historical_transactions: A list of recent bunq Payment objects.
        time_frame_months: The lookback period in months for history.

    Returns:
        A tuple containing the action (str, "notify" or "none") and details (dict).
    """
    current_tx_id = getattr(current_transaction, 'id_', 'N/A')
    print(f"\n--- Agent 3: Analyzing Offline Purchase Transaction ID: {current_tx_id} ---")

    simplified_current_tx = simplify_transaction_for_prompt(current_transaction)
    current_transaction_json = json.dumps(simplified_current_tx, indent=2)

    # Prepare historical data
    simplified_history = [simplify_transaction_for_prompt(tx) for tx in historical_transactions if getattr(tx, 'id_', None) != current_tx_id]
    MAX_HISTORY_ITEMS = 100
    historical_transactions_json = json.dumps(simplified_history[:MAX_HISTORY_ITEMS], indent=2)

    prompt = f"""
You are an AI financial assistant analyzing offline spending patterns. You have received a transaction classified as an 'Offline Purchase' (made with a physical card/phone) and historical transaction data. Your tasks are to categorize the purchase, analyze spending patterns within that category, note any significant deviations or outliers, and suggest an appropriate notification. **Crucially, you should NEVER suggest blocking an offline purchase.**

**Current Offline Purchase Transaction:**
```json
{current_transaction_json}
```

**Relevant Transaction History (Last {time_frame_months} Months):**
```json
{historical_transactions_json}
```

Instructions:

1.  **Categorize Purchase:** Determine the spending category (e.g., "Groceries", "Dining Out", "Transportation", "Shopping", "Entertainment", "Other").
2.  **Analyze Spending Pattern for Awareness:**
    *   Filter history for the same category.
    *   Analyze typical amount, frequency, **timing**. Summarize in `typical_spending_info`.
    *   Compare current transaction. Set `is_deviation` (boolean) and `deviation_reason` (string or null) if it deviates significantly (e.g., "Amount higher than typical grocery spend", "Dining out amount unusual for a weekday based on history").
3.  **Note Notable Outliers:** Assess if the amount/context is notably large/unusual for the category/merchant, even if not a pattern deviation. Set `is_notable_outlier` (boolean).
4.  **Determine Action (Notification Only) and Generate Notification:**
    *   If `is_deviation` is true OR `is_notable_outlier` is true: Set `action_suggestion` to "Notify". Generate `notification_text` offering awareness about the spending (e.g., "Spending Awareness: This offline purchase of €[Amount] for [Category] at [Merchant] was noted as [Reason: deviation_reason or 'notable outlier'.").
    *   Else: Set `action_suggestion` to "None". Set `notification_text` to null.
    *   **Constraint:** `action_suggestion` MUST be "Notify" or "None".

Provide your analysis and the suggested action/notification in JSON format ONLY.

Output Format (JSON):
{{
  "purchase_category": "string",
  "pattern_analysis": {{
    "typical_spending_info": "string",
    "is_deviation": boolean,
    "deviation_reason": "string | null"
  }},
  "is_notable_outlier": boolean,
  "action_suggestion": "Notify | None",
  "notification_text": "string | null"
}}
    """

    response_text = get_llm_response(prompt) # Use default model

    if not response_text:
        print("Error: Did not receive response from LLM for offline purchase analysis.")
        return "error", {"message": "Failed to get LLM offline purchase analysis.", "transaction_id": current_tx_id}

    try:
        cleaned_response_text = response_text.strip().strip("`json\n").strip("\n```")
        analysis = json.loads(cleaned_response_text)

        # Basic validation
        required_keys = ["purchase_category", "pattern_analysis", "is_notable_outlier", "action_suggestion", "notification_text"]
        if not all(k in analysis for k in required_keys) or not isinstance(analysis.get("pattern_analysis"), dict):
             raise ValueError("LLM response missing required keys for offline purchase analysis.")
        # Enforce constraint
        if analysis.get("action_suggestion") not in ["Notify", "None"]:
             print(f"Warning: LLM suggested invalid action '{analysis.get('action_suggestion')}' for offline purchase. Forcing to 'Notify'.")
             analysis["action_suggestion"] = "Notify" # Force to Notify if invalid, or could force to None

        suggested_action = analysis.get("action_suggestion")
        action = "none" # Default action
        if suggested_action == "Notify":
            action = "notify"

        details = {"text": analysis.get("notification_text"), "analysis": analysis, "transaction_id": current_tx_id}
        print(f"Offline Purchase Analysis Result: {json.dumps(analysis, indent=2)}")
        return action, details

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error parsing LLM response for offline purchase {current_tx_id}: {e}")
        print(f"Raw LLM Response:\n{response_text}")
        return "error", {"message": f"Failed to parse LLM offline purchase analysis: {e}", "transaction_id": current_tx_id}

# --- Agent 4: Saving Recommendations (Placeholder) ---
def generate_saving_recommendations(transactions):
     """(Placeholder) Analyzes transactions to generate saving recommendations."""
     print("\n--- Generating Saving Recommendations (Placeholder) ---")
     # TODO: Implement Agent 4 logic
     return "none", {"message": "Savings recommendation agent not implemented yet."}

# --- Deprecated/Removed ---
# (Old analyze_purchase and analyze_subscriptions logic can be removed if fully replaced) 