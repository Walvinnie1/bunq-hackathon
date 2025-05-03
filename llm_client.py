# Module for interacting with LLM APIs
import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError # Import OpenAI client and specific error

# Load environment variables once when the module is loaded
load_dotenv()
# Use the same environment variable name for simplicity, but it's the Nvidia key
NVIDIA_API_KEY = os.getenv("OPENAI_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Initialize OpenAI client globally or within the function
# Global initialization can be slightly more efficient if called frequently
# if OPENAI_API_KEY:
if NVIDIA_API_KEY:
    client = OpenAI(
        # api_key=OPENAI_API_KEY
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY
    )
else:
    print("Warning: OPENAI_API_KEY (used for Nvidia API) not found in environment variables. LLM calls will fail.")
    client = None # Set client to None if key is missing

# def get_llm_response(prompt, system_prompt="You are a helpful financial assistant analyzing banking data.", model="google/gemma-2-9b-it"): # <-- Adjust model name as needed for Nvidia API
# Switch to a model known to support system roles, like Llama 3.1
def get_llm_response(prompt, system_prompt="You are a helpful financial assistant analyzing banking data.", model="meta/llama-3.1-8b-instruct"):
    """Sends a prompt to the configured LLM API (Nvidia) and returns the response content.

    Args:
        prompt: The user's prompt/query for the LLM.
        system_prompt: The system message to set the LLM's context/role.
        # model: The OpenAI model to use (e.g., "gpt-3.5-turbo", "gpt-4").
        model: The model identifier for the Nvidia API (e.g., "nvidia/gemma-3-27b-instruct").

    Returns:
        The text content of the LLM's response, or None if an error occurs.
    """
    if not client:
        # print("Error: OpenAI client is not initialized. Check OPENAI_API_KEY.")
        print("Error: Nvidia API client is not initialized. Check OPENAI_API_KEY in .env file.")
        return None

    try:
        print(f"\n--- Sending prompt to LLM ({model} via Nvidia API) ---")
        # print(f"System: {system_prompt}") # Optional: Log system prompt
        # print(f"User: {prompt[:200]}...") # Optional: Log truncated user prompt

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt}, # Restore system role
                {"role": "user", "content": prompt}
            ],
            # Add other parameters like temperature, max_tokens if needed
            temperature=0.2,
            max_tokens=1024,
            # top_p=0.7, # Optional: Can add top_p if desired
            stream=False # Keep stream=False to get the full response at once
        )

        response_content = response.choices[0].message.content
        print("--- Received LLM response ---")
        # print(response_content) # Optional: Log full response
        return response_content

    except OpenAIError as e:
        print(f"Error calling OpenAI API: {e}")
        # Consider specific handling for RateLimitError, AuthenticationError etc.
        return None
    except Exception as e:
        # Catch other potential exceptions (e.g., network issues)
        print(f"An unexpected error occurred during LLM call: {e}")
        return None

# Example usage (for testing this module directly)
# if __name__ == '__main__':
#     test_prompt = "What are common types of bank transaction fees?"
#     print(f"Testing LLM call with prompt: {test_prompt}")
#     llm_reply = get_llm_response(test_prompt)
#     if llm_reply:
#         print("\nLLM Reply:")
#         print(llm_reply)
#     else:
#         print("\nLLM call failed.") 