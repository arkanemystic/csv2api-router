# csv2api-router
Modular Python pipeline that processes CSVs or unstructured text, extracts API-relevant data, and routes it to Python functions for execution. This project leverages local LLM capabilities via Ollama for data processing and supports both batch and interactive modes with full logging and audit support.

## Features
- Process CSV files and unstructured text
- Local LLM processing using Ollama (deepseek-r1 model)
- Automated API call identification and parameter extraction
- Support for multiple blockchain APIs (Ethereum, Polygon, BSC)
- Batch and interactive processing modes
- Comprehensive logging and audit trail
- Asynchronous API execution

## Architecture
The pipeline follows a three-stage architecture:
1. **Data Extraction** (`extractor.py`): Parses input sources and extracts relevant data
2. **LLM Processing** (`processor.py`): Uses local Ollama model to identify required API calls
3. **API Routing** (`router.py`): Executes identified API calls with proper parameters

## Project Structure
```
csv2api-router
├── src
│   ├── pipeline          # Contains the core processing logic
│   │   ├── extractor.py  # Extracts data from CSVs and text
│   │   ├── processor.py  # LLM-based data processing via Ollama
│   │   └── router.py     # API call routing and execution
│   ├── utils            # Utility functions and helpers
│   │   └── logger.py    # Structured logging with audit support
│   ├── config           # Configuration settings
│   │   └── settings.py  # Project settings
│   └── main.py         # CLI entry point
├── tests               # Unit tests
│   ├── test_extractor.py
│   ├── test_processor.py
│   └── test_router.py
├── requirements.txt    # Python dependencies
└── setup.py           # Project setup configuration
```

## Prerequisites
- Python 3.9 or higher
- Ollama installed and running locally with the deepseek-r1 model
- Required Python packages (see requirements.txt)

## Installation
1. Install Ollama and the deepseek-r1 model:
```bash
# Install Ollama (if not already installed)
curl https://ollama.ai/install.sh | sh

# Pull the deepseek-r1 model
ollama pull deepseek-r1
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage
The pipeline can be run in either batch or interactive mode:

### Interactive Mode
Process a single file with detailed output:
```bash
python src/main.py -i path/to/file.csv
```

### Batch Mode
Process multiple files:
```bash
python src/main.py path/to/directory/
```

### Additional Options
- Process specific file types:
```bash
python src/main.py -p "*.txt" path/to/directory/
```

- Specify custom Ollama endpoint:
```bash
python src/main.py -i --ollama-url "http://localhost:11434" path/to/file.csv
```

## API Support
Currently supported blockchain API calls:
- Transaction: get_transaction, get_receipt
- Token: get_balance, get_transfers
- Contract: get_abi, get_events

## Logging
The pipeline maintains two types of logs:
1. Standard logs (`csv2api_YYYYMMDD.log`)
2. Audit logs in JSON format (`audit_YYYYMMDD.jsonl`)

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.