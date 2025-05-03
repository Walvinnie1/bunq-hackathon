import os
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq import ApiEnvironmentType

CONFIG_FILE_PATH = 'bunq.conf'
API_KEY = "7e29cf223d42b223207387ed5a2b1e9b4fabc67e241db6d325417a330c3665d3"
DEVICE_DESCRIPTION = "jeroen laptop"

# Check if the config file exists
if os.path.exists(CONFIG_FILE_PATH):
    # Restore the API context from file
    print(f"Restoring API context from {CONFIG_FILE_PATH}")
    api_context = ApiContext.restore(CONFIG_FILE_PATH)
else:
    # Create and save the API context (run once per device)
    print(f"Creating new API context and saving to {CONFIG_FILE_PATH}")
    api_context = ApiContext.create(ApiEnvironmentType.SANDBOX, API_KEY, DEVICE_DESCRIPTION)
    api_context.save(CONFIG_FILE_PATH)

# Load the API context into BunqContext
print("Loading API context into BunqContext")
BunqContext.load_api_context(api_context)

print("API context loaded successfully.")