# Bunq AI Agent

This project utilizes AI agents, powered by large language models (LLMs), to analyze your bunq bank transactions. It aims to provide insights, detect potential issues like redundant subscriptions or anomalous spending patterns, and suggest appropriate actions.

## Core Features

*   **Transaction Classification (Agent 0):** Automatically categorizes incoming transactions into types like `Subscription`, `Online Purchase`, or `Offline Purchase`.
*   **Subscription Analysis (Agent 1):**
    *   Identifies the specific service for subscription transactions.
    *   Scans recent history for similar/redundant subscriptions in the same category (e.g., multiple video streaming services).
    *   Generates notifications suggesting potential cancellations or acknowledgments.
*   **Online Purchase Analysis (Agent 2):**
    *   Categorizes online purchases (e.g., Food Delivery, Shopping).
    *   Analyzes spending patterns (amount, frequency, timing) within categories based on historical data.
    *   Detects significant deviations from typical spending habits.
    *   Flags highly suspicious outliers (e.g., unusually large amounts) suggesting review or potential blocking.
*   **Offline Purchase Analysis (Agent 3):**
    *   Categorizes offline (physical card/phone) purchases.
    *   Analyzes spending patterns for awareness.
    *   Notes significant deviations or notably large transactions.
    *   Generates awareness notifications (does **not** suggest blocking).
*   **(Placeholder) Saving Recommendations (Agent 4):** A planned agent to generate saving suggestions based on spending analysis.
*   **LLM Integration:** Leverages external LLMs (configurable via `llm_client.py`) for the core analysis tasks.
*   **Bunq Integration:** Securely connects to the bunq API (Sandbox or Production) using the bunq SDK (via `bunq_client.py`).
*   **Action Logging:** Records agent findings and suggestions in `agent_actions.log`.

## How it Works (High-Level)

1.  **Fetch:** The `main.py` script initiates the `bunq_client.py` to retrieve recent transactions from the bunq API.
2.  **Classify:** Each new transaction is passed to Agent 0 (`classify_transaction` in `agents.py`) for initial categorization.
3.  **Route & Analyze:** Based on the classification, the transaction (along with relevant historical data) is routed to the corresponding specialized agent (Agent 1, 2, or 3 in `agents.py`).
4.  **LLM Prompting:** The specialized agent constructs a detailed prompt including the transaction details and historical context, then sends it to the LLM via `llm_client.py`.
5.  **Parse & Act:** The agent parses the structured JSON response from the LLM. Based on the analysis results (e.g., `suspicious`, `is_deviation`, `suggest_block`), it determines an action (`notify`, `suggest_block`, `none`).
6.  **Log:** The action and supporting details are logged using functions in `actions.py` to the console and `agent_actions.log`.

## Project Structure

```
.
├── agents.py         # Core logic for different analysis agents (LLM prompts)
├── llm_client.py     # Handles interaction with the LLM API (e.g., OpenAI)
├── bunq_client.py    # Handles interaction with the bunq API
├── main.py           # Main script orchestrating fetching, classification, and analysis
├── actions.py        # Handles logging and notification actions
├── agent_actions.log # Log file for agent findings and suggestions
├── bunq.conf         # Configuration file for the bunq API context (generated)
├── .env              # Environment variables (API Keys, etc. - **DO NOT COMMIT**)
├── .gitignore        # Specifies intentionally untracked files
├── LICENSE           # Project license
└── README.md         # This file
# Optional: venv/      # Python virtual environment directory
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv  # Use python3 or python depending on your system
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    *(Note: A `requirements.txt` file is not currently present. You'll need to install the required packages manually. Based on the imports, you likely need:)*
    ```bash
    pip install bunq-sdk python-dotenv openai # Add any other specific libraries used
    ```
    **(Highly Recommended):** Create and maintain a `requirements.txt` file for easier dependency management:
    ```bash
    pip freeze > requirements.txt
    # Then install using: pip install -r requirements.txt
    ```

4.  **Configure bunq API:**
    *   You need a bunq API key (Sandbox recommended for testing).
    *   **Important:** The `init.py` script mentioned in the previous README version seems to be missing. You will need to adapt `bunq_client.py` or create a setup script to handle the initial API context creation and saving it to `bunq.conf`. This typically involves providing your API key and device description to the bunq SDK.
    *   **Security:** Ensure `bunq.conf` is added to your `.gitignore`, especially if using a Production key.

5.  **Configure LLM API:**
    *   Create a `.env` file in the root directory.
    *   Add your LLM provider's API key (the current `llm_client.py` appears set up for OpenAI):
        ```dotenv
        # .env
        OPENAI_API_KEY='your_openai_api_key_here'
        # Add other necessary environment variables if required by llm_client.py
        ```
    *   Ensure `.env` is listed in your `.gitignore` file to prevent committing secrets.

## Usage

Execute the main script from the root directory:

```bash
python main.py
```

The script will:
1.  Load environment variables (from `.env`).
2.  Initialize the bunq client (using `bunq.conf` if configured correctly).
3.  Fetch recent transactions (lookback period configurable in `main.py`).
4.  Process transactions through the agent pipeline (classify -> analyze).
5.  Print notifications and log suggestions/errors to the console and `agent_actions.log`.

### Periodic Execution (Optional)

The `main.py` script likely contains logic (possibly commented out) for running the analysis periodically. Check the script for variables like `check_interval_seconds` or similar to enable and configure automated looping.

## Configuration

*   **bunq API Context:** Managed via `bunq_client.py` and stored in `bunq.conf`. Setup process needs verification (see Setup step 4).
*   **LLM API Key:** `.env` file.
*   **LLM Interaction:** Modify `llm_client.py` to change models, providers, or base prompt instructions.
*   **Agent Logic & Prompts:** Adjust the specific prompts and analysis logic within the agent functions in `agents.py`.
*   **Execution Parameters:** Modify settings in `main.py` (e.g., transaction lookback period, run interval).

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs, feature requests, or improvements.

## License

[MIT License] (See LICENSE file)
