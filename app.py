from flask import Flask, render_template, jsonify
import bunq_client
import agents # Import agents if you need analysis results
import os
from dotenv import load_dotenv

# Load environment variables (needed for bunq_client initialization)
load_dotenv()

app = Flask(__name__)

# --- Simple In-Memory Cache ---
# Stores analysis results keyed by transaction ID
# WARNING: This cache is lost on app restart and not suitable for multi-process production.
analysis_cache = {}
# ---------------------------

# Initialize bunq context (handle potential errors)
try:
    print("Initializing bunq context for Flask app...")
    bunq_client.initialize_bunq_context()
    print("bunq context initialized successfully.")
except Exception as e:
    print(f"WARNING: Failed to initialize bunq context in Flask app: {e}")
    # The app can still run, but bunq features will fail.
    # You might want stricter error handling depending on your needs.

@app.route('/')
def index():
    """Renders the home page."""
    return render_template('index.html', title='bunq AI Agent')

@app.route('/transactions')
def get_transactions():
    """Fetches, classifies, analyzes (with caching), and displays recent transactions."""
    global analysis_cache # Allow modification of the global cache
    try:
        # Fetch transactions (adjust lookback_days as needed)
        transactions_raw = bunq_client.get_all_transactions(lookback_days=7)
        transactions_raw.sort(key=lambda x: getattr(x, 'created', '1970-01-01T00:00:00Z'), reverse=True)
        historical_transactions = transactions_raw

        transactions_display = []
        for tx in transactions_raw:
            tx_id = getattr(tx, 'id_', None)
            if not tx_id:
                print("Skipping transaction with no ID")
                continue # Cannot cache without an ID

            # --- Check Cache --- 
            if tx_id in analysis_cache:
                print(f"Cache HIT for Tx ID {tx_id}")
                cached_data = analysis_cache[tx_id]
                classification = cached_data['classification']
                analysis_action = cached_data['analysis_action']
                analysis_details = cached_data['analysis_details']
            else:
                print(f"Cache MISS for Tx ID {tx_id}. Analyzing...")
                # --- Run Analysis (if not cached) ---
                analysis_action = "none"
                analysis_details = {}
                classification = "Unknown"
                try:
                    # Step 1: Classify Transaction
                    classification = agents.classify_transaction(tx)
                    if not classification:
                        classification = "Unknown"
                        print(f"Warning: Classification failed for Tx ID {tx_id}")

                    # Step 2: Call Appropriate Agent based on Classification
                    if classification == "Subscription":
                        action, details = agents.analyze_subscription_transaction(tx, historical_transactions)
                    elif classification == "Online Purchase":
                        action, details = agents.analyze_online_purchase(tx, historical_transactions)
                    elif classification == "Offline Purchase":
                        action, details = agents.analyze_offline_purchase(tx, historical_transactions)
                    else: # Includes "Unknown"
                        print(f"Skipping detailed analysis for Tx ID {tx_id} (Classification: {classification})")
                        action = "none"
                        details = {"text": f"Type: {classification}"}

                    analysis_action = action
                    analysis_details = details
                    print(f"Analyzed Tx ID {tx_id}: Classification={classification}, Action={action}, Details={details.get('text', 'N/A')}")

                    # --- Store in Cache --- 
                    analysis_cache[tx_id] = {
                        'classification': classification,
                        'analysis_action': analysis_action,
                        'analysis_details': analysis_details
                    }

                except Exception as analysis_error:
                    print(f"Error during classification/analysis for transaction {tx_id}: {analysis_error}")
                    analysis_action = "error"
                    # Store error state in cache to avoid retrying constantly
                    analysis_cache[tx_id] = {
                        'classification': classification, # Store classification attempt
                        'analysis_action': 'error',
                        'analysis_details': {'text': f"Analysis Error: {analysis_error}"}
                    }
                    # Use the error state for display
                    analysis_details = analysis_cache[tx_id]['analysis_details']
            # --- End Analysis/Cache Logic ---

            transactions_display.append({
                'id': tx_id,
                'description': getattr(tx, 'description', 'N/A'),
                'amount': getattr(getattr(tx, 'amount', None), 'value', 'N/A'),
                'currency': getattr(getattr(tx, 'amount', None), 'currency', 'N/A'),
                'counterparty': getattr(getattr(tx, 'counterparty_alias', None), 'display_name', 'N/A'),
                'created': getattr(tx, 'created', 'N/A'),
                'type': getattr(tx, 'type', 'N/A'),
                'sub_type': getattr(tx, 'sub_type', 'N/A'),
                'classification': classification,
                'analysis_action': analysis_action,
                'analysis_text': analysis_details.get('text', '')
            })

        return render_template('transactions.html', transactions=transactions_display, title='Recent Transactions & Analysis')
    except Exception as e:
        print(f"Error fetching transactions for web view: {e}")
        return render_template('error.html', error_message=f"Failed to load transactions: {e}", title='Error')

# Example route to show analysis results (if needed)
# @app.route('/analysis/<transaction_id>')
# def transaction_analysis(transaction_id):
#     # TODO: Fetch specific transaction by ID (might need new bunq_client function)
#     # TODO: Run agents.analyze_purchase(tx)
#     # TODO: Return analysis results (e.g., as JSON or render a template)
#     return jsonify({"status": "Analysis endpoint not fully implemented", "transaction_id": transaction_id})


if __name__ == '__main__':
    # Use environment variable for port or default to 5001 to avoid conflict with common ports
    port = int(os.environ.get('PORT', 5001))
    # Debug=True is helpful for development but should be False in production
    app.run(debug=False)