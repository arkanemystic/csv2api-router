# CSV to API Router

A Python tool that processes CSV files or unstructured text containing blockchain transaction data, leveraging both heuristics and local LLMs (Ollama/LlamaIndex) to generate appropriate API calls. Includes a command-line interface and a Streamlit web application.

## Features

-   **Smart CSV Processing**: Uses heuristics to automatically detect transaction types and extract key data like `tx_hash` and `chain` from CSVs.
-   **Natural Language Processing**: Employs local LLMs (Ollama) to understand user prompts, generate API call mapping plans, and determine user intent.
-   **Text-to-CSV Extraction**: Uses an LLM to extract structured CSV data from unstructured pasted text.
-   **CSV Analysis with LlamaIndex**: Integrates LlamaIndex with Ollama for in-depth analysis and summarization of CSV data within the Streamlit app.
-   **Multi-Chain Support**: Detects blockchain networks (Ethereum, Polygon, Optimism, Arbitrum, Base, BSC) from explorer URLs or text.
-   **Batch Processing**: Efficiently processes multiple transactions via the command-line interface.
-   **Interactive Web UI**: Provides a Streamlit application for uploading files, pasting text, providing instructions, and viewing generated API calls.
-   **Robust Error Handling**: Includes retries for certain operations and detailed logging.
-   **Structured Logging**: Comprehensive logging for auditing and debugging, including JSONL format for audit trails.

## Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/arkanemystic/csv2api-router.git](https://github.com/arkanemystic/csv2api-router.git)
    cd csv2api-router
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Ensure you have Ollama installed and running locally with a suitable model (e.g., `mistral:instruct`, `codellama:latest`).

## Usage

### Command-Line Interface (CLI) - Heuristic Processing

This mode primarily uses heuristic rules defined in `csv_cleaner.py` to process a CSV file based on column content.

Process a CSV file:
```bash
python3 -m src.main -i /path/to/your/transactions.csv
````

The script will determine the most likely API function (`tag_as_expense`, `get_transaction`, or `get_receipt`) based on the data present in the rows and generate the corresponding API call structures.

### Streamlit Web Application - LLM-Powered Processing

This mode uses LLMs for understanding natural language prompts, analyzing CSVs, and extracting data from text.

Run the Streamlit app:

```bash
streamlit run src/app.py
```

Upload a CSV file or paste unstructured text, provide natural language instructions (e.g., "Tag these as expenses", "Get receipts for these transactions"), and the app will use the LLM to generate the appropriate API calls.

### CLI - Natural Language Prompt Processing (Heuristic Parsing)

You can also use the CLI to heuristically parse simple natural language prompts into single API calls (uses basic regex, not the full LLM pipeline):

```bash
python3 src/pipeline/llm_client.py --prompt "tag transaction 0x123... as expense for office supplies"
python3 src/pipeline/llm_client.py --prompt "get transaction details for 0x456..."
python3 src/pipeline/llm_client.py --prompt "list chains"
python3 src/pipeline/llm_client.py --prompt "fill account by account_id act-123 with amount 500"
```

## CSV Format (Expected by Heuristics/CLI `main.py`)

The heuristic CLI mode (`src/main.py`) expects a CSV file potentially containing columns like:

  - `tx_link`: URL to the transaction on a blockchain explorer (used to extract `tx_hash` and `chain`).
  - Columns containing a transaction hash (`0x...`).
  - `purpose` / `expense_category`: Purpose of the transaction.
  - `amount in ETH`: Amount in ETH.
  - `amount in USD`: Amount in USD.

*Note: The Streamlit app is more flexible as the LLM can map columns based on your instructions.*

Example CSV (`sample.csv`):

```csv
Transaction Link,Amount,Purpose,Date
[https://etherscan.io/tx/0xabc123,250.00,Flight](https://etherscan.io/tx/0xabc123,250.00,Flight) to NYC,2024-05-10
[https://etherscan.io/tx/0xdef456,95.00,Hotel,2024-05-11](https://etherscan.io/tx/0xdef456,95.00,Hotel,2024-05-11)
...
```

## Supported API Functions

The tool can generate calls for the following methods based on input data and/or LLM interpretation:

1.  **`tag_as_expense`**: Tags a transaction as an expense.
      - *Params*: `tx_hash`, `chain`, `expense_category`, `amount_in_eth` (optional), `amount_in_usd` (optional)
2.  **`get_transaction`**: Fetches transaction details.
      - *Params*: `tx_hash`, `chain`
3.  **`get_receipt`**: Fetches transaction receipt.
      - *Params*: `tx_hash`, `chain`
4.  **`fill_account_by`**: (Primarily via LLM/NLP prompt) Adds funds to an account.
      - *Params*: `account_id`, `amount`
5.  **`list_chains`**: (Primarily via LLM/NLP prompt) Lists supported chains.
      - *Params*: None

*Note: `get_events`, `get_balance`, `get_transfers`, `get_abi` are defined in `router.py` but may not be fully integrated into the primary generation workflows.*

## API Call Format Example

The tool generates API calls (typically as JSON output or results) in the following format:

```json
{
  "method": "tag_as_expense",
  "params": {
    "tx_hash": "0xabc123...",
    "chain": "ETHEREUM",
    "expense_category": "Flight to NYC",
    "amount_in_eth": null,
    "amount_in_usd": 250.0
  },
  "timestamp": "2025-10-23T..."
}
```

*[Based on `api_functions.py`]*

## Project Structure

```
csv2api-router/
├── src/
│   ├── __init__.py
│   ├── app.py             # Streamlit UI application
│   ├── main.py            # Main CLI entry point (heuristic processing)
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── api_docs.py      # API documentation for LLM prompts
│   │   ├── api_functions.py # Generates final API call structures
│   │   ├── batch_caller.py  # Simple batch execution loop (used by main.py)
│   │   ├── batch_executor.py# Concurrent batch execution utility
│   │   ├── csv_cleaner.py   # Heuristic CSV cleaning and classification
│   │   ├── csv_parser.py    # Parses CSVs into structured objects
│   │   ├── extractor.py     # Heuristic data extraction (tx_hash, chain)
│   │   ├── llm_client.py    # Handles direct calls to Ollama (NLP, text-to-CSV)
│   │   ├── processor.py     # Coordinates LLM processing pipeline
│   │   ├── router.py        # Async execution of API calls (e.g., against Etherscan)
│   │   └── prompt_template.txt # (Potentially outdated template)
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py        # Structured logging setup
│   └── config/              # Configuration (currently empty)
├── dataset/                 # Sample CSV files
├── logs/                    # Log output directory
├── tests/                   # Unit tests
├── requirements.txt         # Project dependencies
├── setup.py                 # Package setup
├── ollama_test.py           # Script to test Ollama connection
└── README.md
```

*[Based on provided file structure]*

### Key Components

  - **`main.py`**: CLI entry point using heuristic processing (`csv_cleaner.py`, `batch_caller.py`).
  - **`app.py`**: Streamlit application using LLM processing (`processor.py`, `llm_client.py`, LlamaIndex).
  - **`pipeline/csv_cleaner.py`**: Handles heuristic CSV parsing, cleaning, and primary function classification for `main.py`.
  - **`pipeline/extractor.py`**: Provides reusable heuristic functions for extracting `tx_hash` and `chain`.
  - **`pipeline/processor.py`**: Manages the LLM-based pipeline for natural language understanding and mapping generation.
  - **`pipeline/llm_client.py`**: Contains functions for interacting directly with the Ollama LLM for specific tasks like text-to-CSV.
  - **`pipeline/api_functions.py`**: Defines functions that create the final, structured API call dictionaries.
  - **`utils/logger.py`**: Configures application-wide structured logging.

## Development

### Adding New API Functions (Heuristic Path - `main.py`)

1.  Add the function definition (creating the API call dict) to `src/pipeline/api_functions.py`.
2.  Add the function name to the `API_FUNCTIONS` dictionary in `src/main.py`.
3.  Update `src/pipeline/csv_cleaner.py`:
      * Add a new value to the `FunctionType` enum.
      * Modify `determine_function_type` to recognize the conditions for triggering your new function.

### Adding New API Functions (LLM Path - `app.py` / `processor.py`)

1.  Add the function definition (creating the API call dict) to `src/pipeline/api_functions.py` (if not already present).
2.  Update the `SUPPORTED_APIS` dictionary in `src/pipeline/llm_client.py` with the new method name and its required parameters.
3.  Update `API_USAGE_GUIDE` in `src/pipeline/api_docs.py` to include documentation for the LLM.
4.  Update the `PipelineProcessor.SUPPORTED_APIS` class variable in `src/pipeline/processor.py`.
5.  Consider adding specific validation logic for the new API's parameters in `PipelineProcessor.validate_api_call`.
6.  Update any relevant prompts used to guide the LLM if necessary (e.g., in `processor.py`).

### Adding New Chain Support

Update the `CHAIN_MAP` dictionary in `src/pipeline/csv_cleaner.py` and potentially the chain detection logic in `src/pipeline/extractor.py` if domains differ significantly.

## Contributing

1.  Fork the repository
2.  Create a feature branch
3.  Commit your changes
4.  Push to the branch
5.  Create a Pull Request

## License

This project is licensed under the MIT License.
