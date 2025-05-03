# Bunq AI Agent

This project analyzes bunq bank transactions using AI (specifically, large language models) to provide insights, detect potential issues like unwanted subscriptions or suspicious activity, and potentially offer saving recommendations (future feature).

## Features (Current & Planned)

*   **Transaction Fetching:** Connects to the bunq API (Sandbox or Production) to retrieve recent transactions.
*   **Subscription Analysis:** Identifies recurring payments that might be subscriptions using an LLM.
*   **Suspicious Activity Detection:** Analyzes individual transactions for characteristics that might indicate fraud or error, using an LLM.
*   **Notification System:** Logs findings and potential issues (currently prints to console and logs to `bunq_ai_agent/agent_actions.log`).
*   **(Planned)** Saving Recommendations: Analyze spending patterns to suggest saving opportunities.

## Project Structure

```
.
├── bunq_ai_agent/        # Main application code
│   ├── main.py           # Main script orchestrating the process
│   ├── agents.py         # Contains different analysis agents (LLM logic)
│   ├── llm_client.py     # Handles interaction with the LLM API (e.g., OpenAI)
│   ├── bunq_client.py    # Handles interaction with the bunq API
│   ├── actions.py        # Handles logging and notification actions
│   ├── agent_actions.log # Log file for agent findings
│   └── ...               # Other supporting files/folders (__pycache__, venv)
├── bunq.conf             # Configuration file for the bunq API context
├── init.py               # Script to initialize the bunq API context (run once or if config changes)
├── .env                  # Environment variables (API Keys, etc. - **DO NOT COMMIT**)
├── .gitignore            # Specifies intentionally untracked files
├── LICENSE               # Project license
└── README.md             # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv bunq_ai_agent/venv
    source bunq_ai_agent/venv/bin/activate  # On Windows use `bunq_ai_agent\venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    *(Note: A `requirements.txt` file is not currently present. You'll need to install the required packages manually. Based on the imports, you likely need:*
    ```bash
    pip install bunq-sdk python-dotenv openai # Add any other specific libraries used
    ```
    *(It's recommended to create a `requirements.txt` file)*

4.  **Configure bunq API:**
    *   Obtain your bunq API key (Sandbox or Production).
    *   Edit the `init.py` script, replacing the placeholder `API_KEY` and `DEVICE_DESCRIPTION` with your actual key and a description for this API access.
    *   Run the initialization script **once** to create the `bunq.conf` file:
        ```bash
        python init.py
        ```
        This will save your API context. You should not need to run this again unless your API key changes or the `bunq.conf` file is lost. **Important:** Ensure `bunq.conf` is added to your `.gitignore` if you are using a Production key to avoid committing sensitive information.

5.  **Configure LLM API:**
    *   Create a `.env` file in the root directory.
    *   Add your LLM provider's API key (e.g., OpenAI):
        ```dotenv
        # .env
        OPENAI_API_KEY='your_openai_api_key_here'
        # Add other necessary environment variables if required by llm_client.py
        ```
    *   Ensure `.env` is listed in your `.gitignore` file.

## Usage

To run the analysis once, execute the main script from the root directory:

```bash
python bunq_ai_agent/main.py
```

The script will:
1.  Load environment variables (from `.env`).
2.  Initialize the bunq context (using `bunq.conf`).
3.  Fetch recent transactions (default lookback is 7 days, configurable in `main.py`).
4.  Analyze transactions using the defined agents (`agents.py`).
5.  Print notifications and log suggestions/errors to the console and `bunq_ai_agent/agent_actions.log`.

### Periodic Execution (Optional)

The `main.py` script contains commented-out code for running the analysis periodically. You can uncomment and modify the `check_interval_seconds` and `lookback_interval_days` variables to run the script automatically in a loop.

## Configuration

*   **bunq API:** `init.py` (for initial setup), `bunq.conf` (stores context).
*   **LLM API:** `.env` file (for API keys).
*   **Analysis Behavior:** Modify parameters within `bunq_ai_agent/main.py` (e.g., `lookback_days`) and potentially within the agent functions in `bunq_ai_agent/agents.py` or prompts in `bunq_ai_agent/llm_client.py`.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

[Specify License Type - e.g., MIT License] (See LICENSE file)
