# Module for handling actions (notifications, logging, etc.)
import datetime
import json

# Simple logging setup (can be replaced with Python's logging module for more robustness)
_LOG_FILE = 'agent_actions.log'

def _log_action(log_entry):
    """Appends a timestamped log entry to the action log file."""
    timestamp = datetime.datetime.now().isoformat()
    try:
        with open(_LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - {log_entry}\n")
    except IOError as e:
        print(f"Error writing to log file {_LOG_FILE}: {e}")

def send_notification(text, details=None):
    """Sends a notification (currently prints to console and logs).

    Args:
        text: The main notification message.
        details: Optional dictionary with additional context from the analysis.
    """
    print(f"\n--- ❗ NOTIFICATION --- ")
    print(text)
    print(f"------------------------")
    log_entry = {"action": "NOTIFICATION", "message": text}
    if details:
        # Log analysis details if provided (e.g., from agents)
        # Ensure details are serializable
        try:
            log_entry['details'] = json.loads(json.dumps(details, default=str)) # Basic serialization
        except (TypeError, json.JSONDecodeError):
            log_entry['details'] = "<details not serializable>"
            
    _log_action(json.dumps(log_entry))

def log_block_suggestion(reason, transaction_id=None, details=None):
    """Logs a suggestion to block an activity or transaction.
    
    Args:
        reason: The reason provided by the LLM for the block suggestion.
        transaction_id: The ID of the transaction, if applicable.
        details: Optional dictionary with additional context from the analysis.
    """
    print(f"\n--- ⚠️ BLOCK SUGGESTION --- ")
    print(f"Reason: {reason}")
    if transaction_id:
        print(f"Transaction ID: {transaction_id}")
    print(f"ACTION: Logged suggestion. Manual review potentially required.")
    print(f"---------------------------")
    log_entry = {
        "action": "BLOCK_SUGGESTION", 
        "reason": reason, 
        "transaction_id": transaction_id
    }
    if details:
        try:
            log_entry['details'] = json.loads(json.dumps(details, default=str))
        except (TypeError, json.JSONDecodeError):
            log_entry['details'] = "<details not serializable>"
            
    _log_action(json.dumps(log_entry))

# Example (could add more actions like format_suggestion if needed)
# def format_suggestion(text):
#    # Prepare text for display in a specific UI format
#    return f"Suggestion: {text}" 