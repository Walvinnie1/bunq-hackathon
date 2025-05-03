# Module for interacting with the bunq API
import os
from dotenv import load_dotenv
# Import directly from bunq.sdk
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.exception.api_exception import ApiException
from bunq import ApiEnvironmentType
# from bunq.sdk import context 
# from bunq.sdk import exception
from bunq.sdk.model.generated import endpoint
import datetime
from dateutil.parser import isoparse # For parsing ISO date strings
# Import specific ApiObject endpoint classes
from bunq.sdk.model.generated.endpoint import MonetaryAccountBankApiObject, PaymentApiObject

# Configuration file path
_BUNQ_CONF_PATH = 'bunq.conf'

def initialize_bunq_context():
    """
    Initializes the bunq API context.

    Checks if a bunq configuration file exists. If so, it loads the context.
    If not, it creates a new context using environment variables, saves it,
    and then loads it.
    """
    load_dotenv() # Load variables from .env file

    api_key = os.getenv("BUNQ_API_KEY")
    environment_type_str = os.getenv("BUNQ_ENVIRONMENT_TYPE", "SANDBOX") # Default to SANDBOX
    device_description = os.getenv("BUNQ_DEVICE_DESCRIPTION", "bunq-ai-agent")
    permitted_ips_str = os.getenv("BUNQ_PERMITTED_IPS") # Optional, handle None

    if not api_key:
        raise ValueError("BUNQ_API_KEY not found in environment variables.")

    # Convert environment type string to ApiEnvironmentType enum
    try:
        if environment_type_str.upper() == "PRODUCTION":
            # environment_type = context.ApiEnvironmentType.PRODUCTION
            environment_type = ApiEnvironmentType.PRODUCTION # Use direct import
        else:
            # environment_type = context.ApiEnvironmentType.SANDBOX
            environment_type = ApiEnvironmentType.SANDBOX # Use direct import
    except ValueError:
        print(f"Invalid BUNQ_ENVIRONMENT_TYPE: {environment_type_str}. Defaulting to SANDBOX.")
        # environment_type = context.ApiEnvironmentType.SANDBOX
        environment_type = ApiEnvironmentType.SANDBOX # Use direct import

    permitted_ips = permitted_ips_str.split(',') if permitted_ips_str else []

    print(f"Initializing bunq context for {environment_type.name} environment...")

    try:
        if os.path.exists(_BUNQ_CONF_PATH):
            print(f"Found existing configuration file: {_BUNQ_CONF_PATH}. Loading context...")
            # Load existing context
            # api_context = context.ApiContext.restore(_BUNQ_CONF_PATH)
            api_context = ApiContext.restore(_BUNQ_CONF_PATH) # Use direct import
            print("Context restored successfully.")
        else:
            print(f"No configuration file found. Creating new context with API key...")
            # Create new context. Note: Permitted IPs are often handled during API key creation in bunq UI.
            # The SDK might use different methods depending on version/setup.
            # This example focuses on saving/loading the context.
            # The actual API key registration/device-server flow might need adjustment
            # based on the specific bunq SDK version and initial setup requirements.
            # api_context = context.ApiContext.create(
            api_context = ApiContext.create( # Use direct import
                environment_type,
                api_key,
                device_description,
                # permitted_ips # Permitted IPs might not be needed here depending on key setup
            )
            print("New context created.")
            # Save the context for future use
            api_context.save(_BUNQ_CONF_PATH)
            print(f"Context saved to: {_BUNQ_CONF_PATH}")

        # Load the API context into BunqContext for SDK calls
        # BunqContext.load_api_context(api_context)
        BunqContext.load_api_context(api_context) # Use direct import
        print("bunq API context loaded successfully.")

        # Optional: Test the connection by fetching user info
        # from bunq.sdk.model.generated import endpoint
        # user = endpoint.User.list().value[0].get_referenced_object()
        # print(f"Successfully connected as user: {user.display_name}")

    except ApiException as bunq_exception: # Use direct import
        print(f"Error initializing bunq context: {bunq_exception}")
        # Consider more specific error handling based on BunqException details
        raise # Re-raise the exception to halt execution if context fails

# Example of calling the initialization at the start (will be moved to main.py later)
# if __name__ == '__main__':
#     try:
#         initialize_bunq_context()
#         print("Initialization check complete.")
#     except Exception as e:
#         print(f"Failed to initialize: {e}")

# --- Placeholder functions for data fetching (to be implemented next) ---

def get_monetary_accounts():
    print("Placeholder: Fetching monetary accounts...")
    # TODO: Implement using endpoint.MonetaryAccount.list()
    # return []
    """Fetches all active monetary accounts (bank accounts) for the user."""
    try:
        # Use the specific ApiObject class as per documentation
        # accounts_response = endpoint.monetary_account_bank.list() # Try lowercase attribute
        accounts_response = MonetaryAccountBankApiObject.list()
        accounts = accounts_response.value
        # Access the actual account object within the response wrapper
        # active_accounts = [acc.get_referenced_object() for acc in accounts if acc.get_referenced_object().status == 'ACTIVE'] # Adjust filtering based on actual object structure
        # Assume items in 'accounts' are the actual MonetaryAccountBank objects
        active_accounts = [acc for acc in accounts if acc.status == 'ACTIVE']
        print(f"Found {len(active_accounts)} active monetary accounts.")
        return active_accounts
    except ApiException as e: # Use direct import
        print(f"Error fetching monetary accounts: {e}")
        return [] # Return empty list on error

def get_payments(account_id, count=50, older_id=None):
    print(f"Placeholder: Fetching payments for account {account_id}...")
    # TODO: Implement using endpoint.Payment.list() with pagination
    # return []
    """Fetches payments for a specific monetary account.

    Args:
        account_id: The ID of the monetary account.
        count: The number of payments to retrieve per request.
        older_id: The ID of the oldest payment seen (for pagination).

    Returns:
        A list of payment objects or None if an error occurs.
    """
    pagination_params = {"count": count}
    if older_id:
        pagination_params["older_id"] = older_id

    try:
        print(f"Fetching payments for account {account_id} with params: {pagination_params}")
        # payment_response = endpoint.Payment.list(monetary_account_id=account_id,
        #                                          params=pagination_params)
        # Use the specific ApiObject class
        payment_response = PaymentApiObject.list(monetary_account_id=account_id,
                                               params=pagination_params)
        payments = payment_response.value
        print(f"Fetched {len(payments)} payments for account {account_id}.")
        # The response object might also contain pagination info (older_url, newer_url)
        # which could be used for more robust pagination if needed.
        return payments
    except ApiException as e: # Use direct import
        print(f"Error fetching payments for account {account_id}: {e}")
        return None # Return None or empty list on error

def get_all_transactions(lookback_days=30):
    print(f"Placeholder: Fetching all transactions for the last {lookback_days} days...")
    # TODO: Implement logic using get_monetary_accounts and get_payments
    # return []
    """Fetches all transactions across all active accounts within a lookback period.

    Args:
        lookback_days: The number of days back from today to fetch transactions for.

    Returns:
        A list of all transactions within the period.
    """
    all_transactions = []
    accounts = get_monetary_accounts()

    if not accounts:
        print("No active accounts found to fetch transactions from.")
        return []

    # Calculate the start date for filtering
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)
    print(f"Fetching transactions since: {start_date.isoformat()}")

    for account in accounts:
        account_id = account.id_
        print(f"\nProcessing account ID: {account_id} ({account.description})")
        older_id = None # Initialize for pagination
        keep_fetching = True
        account_transactions = []

        while keep_fetching:
            # Fetch a batch of payments
            payments_batch = get_payments(account_id, count=200, older_id=older_id) # Fetch max count

            if payments_batch is None: # Handle error from get_payments
                print(f"Skipping account {account_id} due to error fetching payments.")
                keep_fetching = False
                continue

            if not payments_batch:
                print("No more payments found for this account in this batch.")
                keep_fetching = False # No more payments from the API for this account
                continue

            # Process the fetched batch
            last_payment_in_batch_date = None
            for payment in payments_batch:
                try:
                    # Payment objects have a 'created' field (string)
                    payment_date = isoparse(payment.created)
                    payment_date = payment_date.replace(tzinfo=datetime.timezone.utc) # Make payment_date UTC-aware
                    last_payment_in_batch_date = payment_date # Keep track of the last date seen

                    if payment_date >= start_date:
                        # Payment is within our desired time window
                        account_transactions.append(payment)
                    else:
                        # This payment is older than our lookback period.
                        # Since payments are ordered chronologically (newest first),
                        # we can stop fetching for this account.
                        print(f"Reached end of lookback period for account {account_id}.")
                        keep_fetching = False
                        break # Stop processing this batch
                except Exception as e:
                    print(f"Error processing payment {payment.id_}: {e} - Skipping.")
                    # Decide if you want to continue or stop on parsing errors

            # Prepare for the next pagination iteration if needed
            if keep_fetching and payments_batch:
                older_id = payments_batch[-1].id_ # Use the ID of the last payment for the next older_id
                print(f"Paginated - Fetched {len(payments_batch)}, oldest date in batch: {last_payment_in_batch_date}, setting older_id to {older_id}")
            else:
                 # Either keep_fetching is False or payments_batch was empty
                 older_id = None # Reset older_id if we stop fetching

        print(f"Finished fetching for account {account_id}. Total found: {len(account_transactions)}")
        all_transactions.extend(account_transactions)

    print(f"\nFinished fetching all accounts. Total transactions within lookback: {len(all_transactions)}")
    # Sort by date if needed, although likely already mostly sorted
    all_transactions.sort(key=lambda p: isoparse(p.created), reverse=True)
    return all_transactions

def get_transaction_details(transaction_id, account_id):
     print(f"Placeholder: Fetching details for transaction {transaction_id}...")
     # TODO: Implement using endpoint.Payment.get()
     # Example based on new pattern:
     # try:
     #     payment_details = PaymentApiObject.get(payment_id=transaction_id, monetary_account_id=account_id).value
     #     return payment_details
     # except ApiException as e:
     #     print(f"Error fetching details for payment {transaction_id}: {e}")
     #     return None
     pass 