# Main orchestration script
import time
import os
from dotenv import load_dotenv

# Import our modules
import bunq_client
import llm_client # Although not called directly, ensures OpenAI client might be initialized
import agents
import actions

# --- Initialization --- 
print("Loading environment variables...")
load_dotenv()

# Initialize bunq context (this might take a moment the first time)
try:
    print("Initializing bunq context...")
    bunq_client.initialize_bunq_context()
    print("bunq context initialized successfully.")
except Exception as e:
    print(f"FATAL: Failed to initialize bunq context: {e}")
    # Exit if we can't connect to bunq
    exit(1) 
# --- End Initialization ---

def process_recent_transactions(lookback_days=1):
    """Fetches recent transactions, analyzes them, and performs actions."""
    print(f"\n=== Starting Transaction Processing Cycle (Lookback: {lookback_days} days) ===")
    
    # Fetch transactions using the bunq_client
    print("Fetching recent transactions...")
    try:
        transactions = bunq_client.get_all_transactions(lookback_days=lookback_days)
    except Exception as e:
        print(f"Error fetching transactions from bunq: {e}")
        transactions = [] # Continue or handle error as needed

    # --- Using Dummy Data (Keep for easy testing, remove/comment for real use) ---
    # print("\n*** WARNING: Using dummy transaction data for testing! ***")
    # transactions = [
    #     type('obj', (object,), {'id_': "tx123", 'amount': type('obj', (object,), {'value': '-10.99', 'currency': 'EUR'})(), 'description': "Netflix", 'created': "2023-10-26T10:00:00Z", 'type': "MASTERCARD", 'sub_type': "RECURRING", 'counterparty_alias': type('obj', (object,), {'display_name': 'Netflix Inc.', 'country': 'US'})()})(),
    #     type('obj', (object,), {'id_': "tx456", 'amount': type('obj', (object,), {'value': '-85.50', 'currency': 'EUR'})(), 'description': "Unknown POS DE", 'created': "2023-10-27T15:30:00Z", 'type': "MAESTRO", 'sub_type': "ONCE", 'counterparty_alias': type('obj', (object,), {'display_name': 'REWE Markt', 'country': 'DE'})()})(),
    #     type('obj', (object,), {'id_': "tx789", 'amount': type('obj', (object,), {'value': '1500.00', 'currency': 'EUR'})(), 'description': "Salary", 'created': "2023-10-25T09:00:00Z", 'type': "DIRECT_DEBIT", 'sub_type': "ONCE", 'counterparty_alias': type('obj', (object,), {'display_name': 'My Employer Ltd.', 'country': 'NL'})()})(),
    #     type('obj', (object,), {'id_': "txABC", 'amount': type('obj', (object,), {'value': '-49.99', 'currency': 'EUR'})(), 'description': "Vague Service Fee", 'created': "2023-10-28T02:15:00Z", 'type': "PAYMENT", 'sub_type': "ONCE", 'counterparty_alias': type('obj', (object,), {'display_name': 'ServiceCo.', 'country': 'IE'})()})()
    # ]
    # --- End Dummy Data ---
    
    if not transactions:
        print("No new transactions found within the lookback period.")
        # No need to run agents if there's no data
        print("=== Finished Transaction Processing Cycle ===")
        return

    print(f"Processing {len(transactions)} transactions...")
    processed_transaction_ids = set() # Keep track if processing multiple times

    for tx in transactions:
        tx_id = getattr(tx, 'id_', None)
        if not tx_id or tx_id in processed_transaction_ids:
             continue # Skip if no ID or already processed in this run
             
        processed_transaction_ids.add(tx_id)
        print(f"\n--- Analyzing Transaction {tx_id} ---")
        
        # Agent 2/3: Analyze individual purchases for potential fraud/suspicion
        try:
            # TODO: Add logic to differentiate online/offline if possible from data
            # For now, analyze_purchase handles any payment transaction
            action, details = agents.analyze_purchase(tx)

            if action == "notify":
                actions.send_notification(text=details.get("text", "Notification for transaction."), details=details)
            elif action == "suggest_block":
                actions.log_block_suggestion(
                    reason=details.get("reason", "Block suggested by LLM."), 
                    transaction_id=details.get("transaction_id"),
                    details=details
                )
            elif action == "error":
                print(f"Error processing transaction {tx_id}: {details.get('message')}")
                # Log error details if needed
                actions._log_action(f"ERROR_ANALYSIS: Transaction {tx_id} - {details.get('message')}")
            # No action needed for action == "none"

        except Exception as e:
            print(f"Unexpected error during purchase analysis for {tx_id}: {e}")
            actions._log_action(f"ERROR_UNEXPECTED_AGENT: Transaction {tx_id} - {e}")

        # Add a small delay to avoid hitting rate limits (LLM or bunq)
        # Adjust based on actual API limits and usage patterns
        print("Sleeping briefly...")
        time.sleep(2) 

    # Agent 1: Analyze subscriptions (can use the same transactions list)
    print("\n--- Analyzing recent transactions for subscriptions... ---")
    try:
        action, details = agents.analyze_subscriptions(transactions)
        if action == "notify":
            actions.send_notification(text=details.get("text", "Subscription analysis summary."), details=details)
        elif action == "error":
            print(f"Error analyzing subscriptions: {details.get('message')}")
            actions._log_action(f"ERROR_SUBSCRIPTIONS: {details.get('message')}")
    except Exception as e:
        print(f"Unexpected error during subscription analysis: {e}")
        actions._log_action(f"ERROR_UNEXPECTED_AGENT: Subscriptions - {e}")

    # Agent 4: Saving recommendations (placeholder)
    # print("\n--- Generating saving recommendations... ---")
    # try:
    #     # Maybe fetch longer history for better recommendations
    #     # all_history = bunq_client.get_all_transactions(lookback_days=90) 
    #     action, details = agents.generate_saving_recommendations(transactions) # Pass recent for now
    #     if action == "notify": # Assuming Agent 4 also uses notify
    #         actions.send_notification(text=details.get("text", "Savings recommendations."), details=details)
    #     elif action == "error":
    #         print(f"Error generating savings recommendations: {details.get('message')}")
    # except Exception as e:
    #     print(f"Unexpected error during saving recommendation generation: {e}")

    print("\n=== Finished Transaction Processing Cycle ===")


if __name__ == "__main__":
    # --- Option A: Run once --- 
    print("Running the transaction processing once.")
    process_recent_transactions(lookback_days=7) # Look back 7 days on manual run

    # --- Option B: Run periodically (Simple Loop) --- 
    # print("Starting periodic processing loop...")
    # check_interval_seconds = 3600 # Check every hour
    # lookback_interval_days = 1 # Check transactions from the last day
    # while True:
    #     process_recent_transactions(lookback_days=lookback_interval_days)
    #     print(f"\nWaiting for {check_interval_seconds // 60} minutes before next check...")
    #     time.sleep(check_interval_seconds)

    # --- Option C: Event-driven --- 
    # This would require setting up a web server (like Flask or FastAPI)
    # to listen for bunq callbacks (webhooks). Implementation not included here.
    # print("Setup for event-driven (webhook) processing not implemented in this script.") 